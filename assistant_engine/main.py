"""HTTP API layer for interacting with the OpenAI assistant."""

import json
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, List, Optional

from fastapi import FastAPI, HTTPException
from openai import AsyncOpenAI
from pydantic import BaseModel

from botbrew_commons.data_models import BaseConfig
from botbrew_commons.repositories import GCPConfigRepository, GCPSecretRepository

from .bb_logging import get_logger
from .config import build_engine_config
from .functions import TOOL_MAP
from .openai_helpers import submit_tool_outputs_with_backoff

logger = get_logger("MAIN")


class ChatRequest(BaseModel):
    """Schema for chat messages."""

    thread_id: str
    message: str


class ChatResponse(BaseModel):
    """Wrapper for chat responses."""

    responses: List[str]


def _dict_to_object(data: Any) -> Any:
    """Convert nested dictionaries to simple objects."""
    if isinstance(data, dict):
        return type("Obj", (), {k: _dict_to_object(v) for k, v in data.items()})()
    return data


class AssistantEngineAPI:
    """Encapsulates the FastAPI server and OpenAI client."""

    def __init__(self) -> None:
        base_config = BaseConfig()
        secret_repository = GCPSecretRepository(project_id=base_config.project_id, client_id=base_config.client_id)
        config_repository = GCPConfigRepository(
            client_id=base_config.client_id,
            project_id=base_config.project_id,
            bucket_name=base_config.bucket_id,
        )

        self.engine_config = build_engine_config(secret_repository, config_repository)
        logger.info("Booting with config: %s", self.engine_config)

        self.client: Optional[AsyncOpenAI] = None

        self.app = FastAPI(lifespan=self.lifespan)
        self.register_routes()

    @asynccontextmanager
    async def lifespan(self, _app: FastAPI) -> AsyncGenerator[None, None]:
        logger.info("Application starting up...")
        created_client = False
        if self.client is None:
            global client
            if client is None:
                self.client = AsyncOpenAI(api_key=self.engine_config.openai_apikey)
                client = self.client
                created_client = True
            else:
                self.client = client
        try:
            yield
        finally:
            logger.info("Application shutting down...")
            if created_client:
                await self.client.aclose()

    def register_routes(self) -> None:
        self.app.add_api_route("/start", self.start_endpoint, methods=["GET"])
        self.app.add_api_route("/chat", self.chat_endpoint, methods=["POST"], response_model=ChatResponse)

    async def _process_run(self, thread_id: str, human_query: str) -> list[str]:
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

    async def start_endpoint(self) -> dict[str, str]:
        """Start a new conversation and return the thread information."""
        thread = await client.beta.threads.create()
        logger.info("Starting new thread: %s", thread.id)
        return {"thread_id": thread.id, "initial_message": engine_config.initial_message}

    async def chat_endpoint(self, request: ChatRequest) -> ChatResponse:
        """Process a user message and return assistant responses."""
        if not request.thread_id:
            raise HTTPException(status_code=400, detail="Missing thread_id")
        responses = await process_run(request.thread_id, request.message)
        return ChatResponse(responses=responses)


def get_app() -> FastAPI:
    """Return a fully configured FastAPI application."""

    api = AssistantEngineAPI()
    return api.app


api = AssistantEngineAPI()
app = api.app
client = api.client
engine_config = api.engine_config


async def process_run(thread_id: str, human_query: str) -> list[str]:
    """Proxy to the API instance for backward compatibility."""

    return await api._process_run(thread_id, human_query)


if __name__ == "__main__":  # pragma: no cover - manual run
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
