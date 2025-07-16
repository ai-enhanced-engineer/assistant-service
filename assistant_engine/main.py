"""HTTP API layer for interacting with the OpenAI assistant."""

import inspect
import json
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket
from openai import AsyncOpenAI, OpenAIError
from pydantic import BaseModel

from botbrew_commons.data_models import BaseConfig
from botbrew_commons.repositories import GCPConfigRepository, GCPSecretRepository

from .bb_logging import get_logger, log_with_context
from .config import build_engine_config
from .correlation import CorrelationContext, get_or_create_correlation_id
from .functions import TOOL_MAP
from .openai_helpers import cancel_run_safely, submit_tool_outputs_with_backoff

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

    def _validate_function_args(self, func: callable, args: dict[str, Any], func_name: str) -> None:
        """Validate that required function parameters are provided."""
        sig = inspect.signature(func)

        # Check for missing required parameters
        for param_name, param in sig.parameters.items():
            if param.default is inspect.Parameter.empty and param_name not in args:
                raise TypeError(f"Missing required parameter '{param_name}'")

        # Check for unexpected parameters
        unexpected_params = set(args.keys()) - set(sig.parameters.keys())
        if unexpected_params:
            logger.warning("Function '%s' received unexpected parameters: %s", func_name, unexpected_params)

    @asynccontextmanager
    async def lifespan(self, _app: FastAPI) -> AsyncGenerator[None, None]:
        logger.info("Application starting up...")
        if self.client is None:
            self.client = AsyncOpenAI(api_key=self.engine_config.openai_apikey)
        try:
            yield
        finally:
            logger.info("Application shutting down...")
            if self.client is not None:
                await self.client.aclose()

    def register_routes(self) -> None:
        self.app.add_api_route("/start", self.start_endpoint, methods=["GET"])
        self.app.add_api_route(
            "/chat",
            self.chat_endpoint,
            methods=["POST"],
            response_model=ChatResponse,
        )
        self.app.add_api_websocket_route("/stream", self.stream_endpoint)

    async def _iterate_run_events(self, thread_id: str, human_query: str) -> AsyncGenerator[Any, None]:
        """Yield events while managing tool calls and submissions."""
        correlation_id = get_or_create_correlation_id()
        
        try:
            await self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=human_query,
            )
            log_with_context(
                logger, logging.INFO, 
                "Message created successfully", 
                thread_id=thread_id, 
                correlation_id=correlation_id
            )
        except OpenAIError as err:
            log_with_context(
                logger, logging.ERROR, 
                f"OpenAI message creation failed: {err}", 
                thread_id=thread_id, 
                correlation_id=correlation_id,
                error_type="OpenAIError"
            )
            raise HTTPException(
                status_code=502, 
                detail=f"Failed to create message (correlation_id: {correlation_id[:8]})"
            ) from err
        except Exception as err:  # noqa: BLE001
            log_with_context(
                logger, logging.ERROR, 
                f"Unexpected error creating message: {err}", 
                thread_id=thread_id, 
                correlation_id=correlation_id,
                error_type=type(err).__name__
            )
            raise HTTPException(
                status_code=500, 
                detail=f"Internal server error (correlation_id: {correlation_id[:8]})"
            ) from err

        try:
            event_stream = await self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.engine_config.assistant_id,
                stream=True,
            )
            log_with_context(
                logger, logging.INFO, 
                "Run stream created successfully", 
                thread_id=thread_id, 
                correlation_id=correlation_id,
                assistant_id=self.engine_config.assistant_id
            )
        except OpenAIError as err:
            log_with_context(
                logger, logging.ERROR, 
                f"OpenAI run creation failed: {err}", 
                thread_id=thread_id, 
                correlation_id=correlation_id,
                error_type="OpenAIError",
                assistant_id=self.engine_config.assistant_id
            )
            raise HTTPException(
                status_code=502, 
                detail=f"Failed to create run (correlation_id: {correlation_id[:8]})"
            ) from err
        except Exception as err:  # noqa: BLE001
            log_with_context(
                logger, logging.ERROR, 
                f"Unexpected error creating run: {err}", 
                thread_id=thread_id, 
                correlation_id=correlation_id,
                error_type=type(err).__name__,
                assistant_id=self.engine_config.assistant_id
            )
            raise HTTPException(
                status_code=500, 
                detail=f"Internal server error (correlation_id: {correlation_id[:8]})"
            ) from err

        tool_outputs: dict[str, dict[str, Any]] = {}
        run_id = None

        async for event in event_stream:
            yield event

            if event.event == "thread.run.created":
                run_id = event.data.id

            if event.event == "thread.run.step.completed":
                step_details = event.data.step_details

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

                            # Validate function exists in TOOL_MAP
                            if name not in TOOL_MAP:
                                log_with_context(
                                    logger, logging.ERROR, 
                                    f"Unknown function '{name}' not found in TOOL_MAP", 
                                    thread_id=thread_id, 
                                    run_id=run_id,
                                    tool_call_id=tool_call.id,
                                    function_name=name
                                )
                                tool_outputs[tool_call.id] = {
                                    "tool_call_id": tool_call.id,
                                    "output": f"Error: Function '{name}' not available (correlation_id: {correlation_id[:8]})",
                                }
                                continue

                            try:
                                # Validate function arguments
                                func = TOOL_MAP[name]
                                self._validate_function_args(func, args, name)

                                # Execute function with validated arguments
                                log_with_context(
                                    logger, logging.DEBUG, 
                                    f"Executing function '{name}' with args: {args}", 
                                    thread_id=thread_id, 
                                    run_id=run_id,
                                    tool_call_id=tool_call.id,
                                    function_name=name
                                )
                                output = func(**args)
                                tool_outputs[tool_call.id] = {
                                    "tool_call_id": tool_call.id,
                                    "output": output,
                                }
                                log_with_context(
                                    logger, logging.INFO, 
                                    f"Function '{name}' executed successfully", 
                                    thread_id=thread_id, 
                                    run_id=run_id,
                                    tool_call_id=tool_call.id,
                                    function_name=name
                                )
                            except TypeError as err:
                                log_with_context(
                                    logger, logging.ERROR, 
                                    f"Invalid arguments for function '{name}': {err}", 
                                    thread_id=thread_id, 
                                    run_id=run_id,
                                    tool_call_id=tool_call.id,
                                    function_name=name,
                                    error_type="TypeError"
                                )
                                tool_outputs[tool_call.id] = {
                                    "tool_call_id": tool_call.id,
                                    "output": f"Error: Invalid arguments for function '{name}': {err} (correlation_id: {correlation_id[:8]})",
                                }
                            except Exception as err:  # noqa: BLE001
                                log_with_context(
                                    logger, logging.ERROR, 
                                    f"Function '{name}' execution failed: {err}", 
                                    thread_id=thread_id, 
                                    run_id=run_id,
                                    tool_call_id=tool_call.id,
                                    function_name=name,
                                    error_type=type(err).__name__
                                )
                                tool_outputs[tool_call.id] = {
                                    "tool_call_id": tool_call.id,
                                    "output": f"Error: Function '{name}' execution failed: {err} (correlation_id: {correlation_id[:8]})",
                                }

            if (
                event.event == "thread.run.requires_action"
                and event.data.required_action.type == "submit_tool_outputs"
                and run_id
            ):
                submission_result = await submit_tool_outputs_with_backoff(
                    self.client,
                    thread_id=thread_id,
                    run_id=run_id,
                    tool_outputs=tool_outputs.values(),
                )
                
                if submission_result is None:
                    logger.error(
                        "Tool output submission failed permanently for run_id=%s, thread_id=%s. "
                        "Attempting to cancel run to prevent hanging state.",
                        run_id,
                        thread_id,
                    )
                    cancel_success = await cancel_run_safely(self.client, thread_id, run_id)
                    if not cancel_success:
                        logger.error(
                            "Critical error: Unable to submit tool outputs or cancel run_id=%s. "
                            "Run may be in an inconsistent state.",
                            run_id,
                        )
                    # Break the event loop to prevent infinite waiting
                    break

            if event.event in [
                "thread.run.completed",
                "thread.run.failed",
                "thread.run.cancelled",
                "thread.run.expired",
            ]:
                break

    async def _process_run(self, thread_id: str, human_query: str) -> list[str]:
        """Run the assistant for the provided query and return responses."""
        correlation_id = get_or_create_correlation_id()
        messages: list[str] = []

        log_with_context(
            logger, logging.INFO, 
            "Starting run processing", 
            thread_id=thread_id, 
            correlation_id=correlation_id
        )

        async for event in self._iterate_run_events(thread_id, human_query):
            if event.event == "thread.run.step.completed" and event.data.step_details.type == "message_creation":
                step_details = event.data.step_details
                message_id = step_details.message_creation.message_id
                
                try:
                    thread_message = await self.client.beta.threads.messages.retrieve(
                        message_id=message_id,
                        thread_id=thread_id,
                    )
                    log_with_context(
                        logger, logging.DEBUG, 
                        "Message retrieved successfully", 
                        thread_id=thread_id, 
                        correlation_id=correlation_id,
                        message_id=message_id
                    )
                except OpenAIError as err:
                    log_with_context(
                        logger, logging.ERROR, 
                        f"OpenAI message retrieval failed: {err}", 
                        thread_id=thread_id, 
                        correlation_id=correlation_id,
                        message_id=message_id,
                        error_type="OpenAIError"
                    )
                    raise HTTPException(
                        status_code=502, 
                        detail=f"Failed to retrieve message (correlation_id: {correlation_id[:8]})"
                    ) from err
                except Exception as err:  # noqa: BLE001
                    log_with_context(
                        logger, logging.ERROR, 
                        f"Unexpected error retrieving message: {err}", 
                        thread_id=thread_id, 
                        correlation_id=correlation_id,
                        message_id=message_id,
                        error_type=type(err).__name__
                    )
                    raise HTTPException(
                        status_code=500, 
                        detail=f"Internal server error (correlation_id: {correlation_id[:8]})"
                    ) from err
                    
                for content in thread_message.content:
                    if hasattr(content, "text"):
                        messages.append(content.text.value)

        log_with_context(
            logger, logging.INFO, 
            f"Run processing completed with {len(messages)} messages", 
            thread_id=thread_id, 
            correlation_id=correlation_id,
            message_count=len(messages)
        )
        return messages

    async def _process_run_stream(self, thread_id: str, human_query: str) -> AsyncGenerator[Any, None]:
        """Yield events from the assistant run as they arrive."""
        async for event in self._iterate_run_events(thread_id, human_query):
            yield event

    async def start_endpoint(self) -> dict[str, str]:
        """Start a new conversation and return the thread information."""
        with CorrelationContext() as correlation_id:
            try:
                thread = await self.client.beta.threads.create()
                log_with_context(
                    logger, logging.INFO, 
                    "New thread created successfully", 
                    thread_id=thread.id, 
                    correlation_id=correlation_id
                )
            except OpenAIError as err:
                log_with_context(
                    logger, logging.ERROR, 
                    f"OpenAI thread creation failed: {err}", 
                    correlation_id=correlation_id,
                    error_type="OpenAIError"
                )
                raise HTTPException(
                    status_code=502, 
                    detail=f"Failed to start thread (correlation_id: {correlation_id[:8]})"
                ) from err
            except Exception as err:  # noqa: BLE001
                log_with_context(
                    logger, logging.ERROR, 
                    f"Unexpected error starting thread: {err}", 
                    correlation_id=correlation_id,
                    error_type=type(err).__name__
                )
                raise HTTPException(
                    status_code=500, 
                    detail=f"Internal server error (correlation_id: {correlation_id[:8]})"
                ) from err
                
            return {
                "thread_id": thread.id, 
                "initial_message": self.engine_config.initial_message,
                "correlation_id": correlation_id
            }

    async def chat_endpoint(self, request: ChatRequest) -> ChatResponse:
        """Process a user message and return assistant responses."""
        with CorrelationContext() as correlation_id:
            if not request.thread_id:
                log_with_context(
                    logger, logging.ERROR, 
                    "Missing thread_id in chat request", 
                    correlation_id=correlation_id
                )
                raise HTTPException(
                    status_code=400, 
                    detail=f"Missing thread_id (correlation_id: {correlation_id[:8]})"
                )
                
            log_with_context(
                logger, logging.INFO, 
                "Processing chat request", 
                thread_id=request.thread_id, 
                correlation_id=correlation_id,
                message_length=len(request.message)
            )
            
            responses = await self._process_run(request.thread_id, request.message)
            return ChatResponse(responses=responses)

    async def stream_endpoint(self, websocket: WebSocket) -> None:
        """Forward run events directly through a WebSocket connection."""
        with CorrelationContext() as correlation_id:
            await websocket.accept()
            
            try:
                data = await websocket.receive_json()
                thread_id = data.get("thread_id")
                message = data.get("message")
                
                if not thread_id or not message:
                    error_msg = f"Missing thread_id or message (correlation_id: {correlation_id[:8]})"
                    log_with_context(
                        logger, logging.ERROR, 
                        "WebSocket request missing required fields", 
                        correlation_id=correlation_id,
                        has_thread_id=bool(thread_id),
                        has_message=bool(message)
                    )
                    await websocket.send_json({"error": error_msg})
                    await websocket.close()
                    return

                log_with_context(
                    logger, logging.INFO, 
                    "Starting WebSocket stream", 
                    thread_id=thread_id, 
                    correlation_id=correlation_id,
                    message_length=len(message)
                )

                async for event in self._process_run_stream(thread_id, message):
                    await websocket.send_text(event.model_dump_json())

                log_with_context(
                    logger, logging.INFO, 
                    "WebSocket stream completed", 
                    thread_id=thread_id, 
                    correlation_id=correlation_id
                )
                
            except Exception as err:  # noqa: BLE001
                log_with_context(
                    logger, logging.ERROR, 
                    f"WebSocket stream error: {err}", 
                    correlation_id=correlation_id,
                    error_type=type(err).__name__
                )
                await websocket.send_json({
                    "error": f"Stream error (correlation_id: {correlation_id[:8]})"
                })
            finally:
                await websocket.close()


def get_app() -> FastAPI:
    """Return a fully configured FastAPI application."""

    api = AssistantEngineAPI()
    return api.app


api = AssistantEngineAPI()
app = api.app


async def process_run(thread_id: str, human_query: str) -> list[str]:
    """Proxy to the API instance for backward compatibility."""

    return await api._process_run(thread_id, human_query)


async def process_run_stream(thread_id: str, human_query: str) -> AsyncGenerator[Any, None]:
    """Proxy streaming run for backward compatibility."""

    async for event in api._process_run_stream(thread_id, human_query):
        yield event


if __name__ == "__main__":  # pragma: no cover - manual run
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
