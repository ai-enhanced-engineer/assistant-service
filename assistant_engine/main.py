import asyncio
import inspect
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
    list_run_steps,
    retrieve_run,
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


def handle_function_tool_call(tool_call: Any) -> Any | None:
    """Return the output of a tool call if valid."""
    function_name = tool_call.function.name
    if function_name not in TOOL_MAP:
        logger.error("Unknown function %s", function_name)
        return None

    function_args = json.loads(tool_call.function.arguments or "{}")
    function = TOOL_MAP[function_name]
    required_params = [
        p.name
        for p in inspect.signature(function).parameters.values()
        if p.default is inspect.Parameter.empty
        and p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
    ]
    missing = [param for param in required_params if param not in function_args]
    if missing:
        logger.error("Missing required parameters %s for function %s", missing, function_name)
        return None

    return function(**function_args)


async def process_run(thread_id: str, human_query: str) -> list[str]:
    """Run the assistant for the provided query and return responses."""
    await client.beta.threads.messages.create(thread_id=thread_id, role="user", content=human_query)
    run = await client.beta.threads.runs.create(thread_id=thread_id, assistant_id=engine_config.assistant_id)

    messages: list[str] = []
    tool_outputs: dict[str, dict[str, Any]] = {}

    while True:
        run = await retrieve_run(client, thread_id=thread_id, run_id=run.id)
        if not run:
            break

        run_steps = await list_run_steps(client, thread_id=thread_id, run_id=run.id)
        if not run_steps:
            break

        for step in run_steps.data:
            run_step = await client.beta.threads.runs.steps.retrieve(
                thread_id=thread_id, run_id=run.id, step_id=step.id
            )
            step_details = run_step.step_details

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
                        output = handle_function_tool_call(tool_call)
                        if output is not None:
                            tool_outputs[tool_call.id] = {
                                "tool_call_id": tool_call.id,
                                "output": output,
                            }

        if run.status == "requires_action" and run.required_action.type == "submit_tool_outputs":
            await submit_tool_outputs_with_backoff(
                client,
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs=tool_outputs.values(),
            )

        if run.status in ["cancelled", "failed", "completed", "expired"]:
            break

        await asyncio.sleep(2)

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
