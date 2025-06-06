import json
from typing import Any, List

from fastapi import FastAPI, HTTPException
from openai import AsyncOpenAI
from pydantic import BaseModel

from botbrew_commons.data_models import BaseConfig
from botbrew_commons.repositories import GCPConfigRepository, GCPSecretRepository

from .bb_logging import get_logger
from .config import build_engine_config
from .functions import TOOL_MAP
from .openai_helpers import (
    submit_tool_outputs_with_backoff,
)

logger = get_logger("MAIN")

# Load configuration from the environment and repositories
base_config = BaseConfig()
secret_repository = GCPSecretRepository(project_id=base_config.project_id, client_id=base_config.client_id)
config_repository = GCPConfigRepository(
    client_id=base_config.client_id,
    project_id=base_config.project_id,
    bucket_name=base_config.bucket_id,
)
engine_config = build_engine_config(secret_repository, config_repository)
logger.info(f"Booting with config: {engine_config}")

client = AsyncOpenAI(api_key=engine_config.openai_apikey)

app = FastAPI()


class ChatRequest(BaseModel):
    thread_id: str
    message: str


class ChatResponse(BaseModel):
    responses: List[str]


def _dict_to_object(data: Any) -> Any:
    """Convert nested dictionaries to simple objects."""
    if isinstance(data, dict):
        return type("Obj", (), {k: _dict_to_object(v) for k, v in data.items()})()
    return data


async def process_run(thread_id: str, human_query: str) -> list[str]:
    """Run the assistant for the provided query and return responses."""
    await client.beta.threads.messages.create(thread_id=thread_id, role="user", content=human_query)

    event_stream = await client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=engine_config.assistant_id,
        stream=True,
    )

    messages: list[str] = []
    tool_outputs: dict[str, dict[str, Any]] = {}
    run_id = None

    async for event in event_stream:
        if event.event == "thread.run.created":
            run_id = event.data.id

        if event.event == "thread.run.step.completed":
            step_details = event.data.step_details

            if step_details.type == "message_creation":
                thread_message = await client.beta.threads.messages.retrieve(
                    message_id=step_details.message_creation.message_id,
                    thread_id=thread_id,
                )
                for content in thread_message.content:
                    if hasattr(content, "text"):
                        messages.append(content.text.value)

            if step_details.type == "tool_calls":
                for tool_call in step_details.tool_calls:
                    tool_call = _dict_to_object(tool_call)
                    if tool_call.type == "retrieval":
                        tool_outputs[tool_call.id] = {
                            "tool_call_id": tool_call.id,
                            "output": "retrieval",
                        }
                    elif tool_call.type == "function":
                        name = tool_call.function.name
                        args = json.loads(tool_call.function.arguments or "{}")
                        if name not in TOOL_MAP:
                            logger.error("Unknown function %s", name)
                            continue
                        output = TOOL_MAP[name](**args)
                        tool_outputs[tool_call.id] = {
                            "tool_call_id": tool_call.id,
                            "output": output,
                        }

        if (
            event.event == "thread.run.requires_action"
            and event.data.required_action.type == "submit_tool_outputs"
            and run_id
        ):
            await submit_tool_outputs_with_backoff(
                client,
                thread_id=thread_id,
                run_id=run_id,
                tool_outputs=tool_outputs.values(),
            )

        if event.event in [
            "thread.run.completed",
            "thread.run.failed",
            "thread.run.cancelled",
            "thread.run.expired",
        ]:
            break

    return messages


@app.get("/start")
async def start() -> dict[str, str]:
    """Start a new conversation and return the thread information."""
    thread = await client.beta.threads.create()
    logger.info("Starting new thread: %s", thread.id)
    return {"thread_id": thread.id, "initial_message": engine_config.initial_message}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Process a user message and return assistant responses."""
    if not request.thread_id:
        raise HTTPException(status_code=400, detail="Missing thread_id")
    responses = await process_run(request.thread_id, request.message)
    return ChatResponse(responses=responses)
