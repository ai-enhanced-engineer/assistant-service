"""Main application module for the Assistant Engine.

This module provides the FastAPI application with REST and WebSocket endpoints for
interacting with OpenAI assistants.
"""

import json
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional

from fastapi import FastAPI, HTTPException, WebSocket
from openai import AsyncOpenAI, OpenAIError
from pydantic import BaseModel

from botbrew_commons.repositories import GCPConfigRepository, GCPSecretRepository

from .config import build_engine_config
from .correlation import CorrelationContext, get_or_create_correlation_id
from .functions import TOOL_MAP
from .openai_helpers import cancel_run_safely, submit_tool_outputs_with_backoff
from .structured_logging import configure_structlog, get_logger

# Use new structured logger
logger = get_logger("MAIN")


class ChatRequest(BaseModel):
    """Schema for chat messages."""

    thread_id: str
    message: str


class ChatResponse(BaseModel):
    """Schema for chat responses."""

    responses: list[str]


def create_lifespan(api_instance: "AssistantEngineAPI") -> Any:
    """Create a lifespan context manager for the API instance."""
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        """Manage application startup and shutdown."""
        logger.info("Application starting up...")
        created_client = False
        if api_instance.client is None:
            api_instance.client = AsyncOpenAI(api_key=api_instance.engine_config.openai_apikey)
            created_client = True
        yield
        logger.info("Application shutting down...")
        if created_client and api_instance.client:
            await api_instance.client.close()
    return lifespan


class AssistantEngineAPI:
    """Main API class for the assistant engine."""

    def __init__(self) -> None:
        """Initialize the assistant engine with configuration."""
        # Set up repositories
        project_id = os.getenv("PROJECT_ID", "")
        bucket_id = os.getenv("BUCKET_ID", "")
        client_id = os.getenv("CLIENT_ID", "")
        
        secret_repository = GCPSecretRepository(project_id=project_id, client_id=client_id)
        config_repository = GCPConfigRepository(
            client_id=client_id, project_id=project_id, bucket_name=bucket_id
        )
        
        self.engine_config = build_engine_config(secret_repository, config_repository)
        self.client: Optional[AsyncOpenAI] = None

        # Log configuration (without sensitive data)
        logger.info(
            "Booting with config",
            assistant_id=self.engine_config.assistant_id,
            assistant_name=self.engine_config.assistant_name,
            initial_message=self.engine_config.initial_message,
            code_interpreter=self.engine_config.code_interpreter,
            retrieval=self.engine_config.retrieval,
            function_names=self.engine_config.function_names,
            openai_apikey="sk" if self.engine_config.openai_apikey else None,
        )

        # Create FastAPI app
        self.app = FastAPI(title="Assistant Engine", lifespan=create_lifespan(self))

        # Add routes
        self.app.get("/")(self.root)
        self.app.get("/start")(self.start_endpoint)
        self.app.post("/chat", response_model=ChatResponse)(self.chat_endpoint)
        self.app.websocket("/stream")(self.stream_endpoint)

    async def root(self) -> dict[str, str]:
        """Root endpoint."""
        return {"message": "Assistant Engine is running"}

    def _validate_function_args(self, func: Any, args: dict[str, Any], name: str) -> None:
        """Validate function arguments against the function signature."""
        import inspect

        sig = inspect.signature(func)
        
        # Check for required parameters
        required_params = {
            param.name for param in sig.parameters.values()
            if param.default is inspect.Parameter.empty
        }
        missing_params = required_params - set(args.keys())
        if missing_params:
            missing_str = ", ".join(sorted(missing_params))
            raise TypeError(f"Missing required arguments: {missing_str}")
        
        # Check for unexpected parameters
        valid_params = set(sig.parameters.keys())
        unexpected_params = set(args.keys()) - valid_params
        if unexpected_params:
            logger.warning(
                "Function received unexpected parameters",
                function_name=name,
                unexpected_params=unexpected_params
            )

    async def _iterate_run_events(self, thread_id: str, human_query: str) -> AsyncGenerator[Any, None]:
        """Process a run and return streaming events."""
        correlation_id = get_or_create_correlation_id()
        
        logger.info(
            "Starting run processing", 
            thread_id=thread_id, 
            correlation_id=correlation_id
        )

        try:
            assert self.client is not None, "Client not initialized"
            await self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=human_query,
            )
            logger.info(
                "Message created successfully", 
                thread_id=thread_id, 
                correlation_id=correlation_id
            )
        except OpenAIError as err:
            logger.error(
                "OpenAI message creation failed", 
                thread_id=thread_id, 
                correlation_id=correlation_id,
                error_type="OpenAIError",
                error=str(err)
            )
            raise HTTPException(
                status_code=502, 
                detail=f"Failed to create message (correlation_id: {correlation_id[:8]})"
            ) from err
        except Exception as err:  # noqa: BLE001
            logger.error(
                "Unexpected error creating message", 
                thread_id=thread_id, 
                correlation_id=correlation_id,
                error_type=type(err).__name__,
                error=str(err)
            )
            raise HTTPException(
                status_code=500, 
                detail=f"Internal server error (correlation_id: {correlation_id[:8]})"
            ) from err

        try:
            assert self.client is not None, "Client not initialized"
            event_stream = await self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.engine_config.assistant_id,
                stream=True,
            )
            logger.info(
                "Run stream created successfully", 
                thread_id=thread_id, 
                correlation_id=correlation_id,
                assistant_id=self.engine_config.assistant_id
            )
        except OpenAIError as err:
            logger.error(
                "OpenAI run creation failed", 
                thread_id=thread_id, 
                correlation_id=correlation_id,
                error_type="OpenAIError",
                assistant_id=self.engine_config.assistant_id,
                error=str(err)
            )
            raise HTTPException(
                status_code=502, 
                detail=f"Failed to create run (correlation_id: {correlation_id[:8]})"
            ) from err
        except Exception as err:  # noqa: BLE001
            logger.error(
                "Unexpected error creating run", 
                thread_id=thread_id, 
                correlation_id=correlation_id,
                error_type=type(err).__name__,
                assistant_id=self.engine_config.assistant_id,
                error=str(err)
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

            # Handle tool calls from step completed events
            if (event.event == "thread.run.step.completed" 
                and hasattr(event.data, 'step_details') 
                and event.data.step_details.type == "tool_calls"):
                step_tool_calls = event.data.step_details.tool_calls
                for tool_call in step_tool_calls:
                    if tool_call.type == "function":
                        name = tool_call.function.name
                        args = json.loads(tool_call.function.arguments or "{}")

                        # Validate function exists in TOOL_MAP
                        if name not in TOOL_MAP:
                            logger.error(
                                "Unknown function not found in TOOL_MAP", 
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
                            logger.debug(
                                "Executing function with args", 
                                thread_id=thread_id, 
                                run_id=run_id,
                                tool_call_id=tool_call.id,
                                function_name=name,
                                args=args
                            )
                            output = func(**args)
                            tool_outputs[tool_call.id] = {
                                "tool_call_id": tool_call.id,
                                "output": output,
                            }
                            logger.info(
                                "Function executed successfully", 
                                thread_id=thread_id, 
                                run_id=run_id,
                                tool_call_id=tool_call.id,
                                function_name=name
                            )
                                      
                        except TypeError as err:
                            logger.error(
                                "Invalid arguments for function", 
                                thread_id=thread_id, 
                                run_id=run_id,
                                tool_call_id=tool_call.id,
                                function_name=name,
                                error_type="TypeError",
                                error=str(err)
                            )
                            tool_outputs[tool_call.id] = {
                                "tool_call_id": tool_call.id,
                                "output": f"Error: Invalid arguments for function '{name}': {err} (correlation_id: {correlation_id[:8]})",
                            }
                        except Exception as err:  # noqa: BLE001
                            logger.error(
                                "Function execution failed", 
                                thread_id=thread_id, 
                                run_id=run_id,
                                tool_call_id=tool_call.id,
                                function_name=name,
                                error_type=type(err).__name__,
                                error=str(err)
                            )
                            tool_outputs[tool_call.id] = {
                                "tool_call_id": tool_call.id,
                                "output": f"Error: Function '{name}' execution failed: {err} (correlation_id: {correlation_id[:8]})",
                            }

            # Note: Function calls are now handled in step.completed events above
            # This section only handles non-function tool types if they come from required_action
            if event.event == "thread.run.requires_action":
                if event.data.required_action and event.data.required_action.type == "submit_tool_outputs":
                    # Handle the case where submit_tool_outputs might not exist or be a SimpleNamespace
                    submit_tool_outputs = getattr(event.data.required_action, 'submit_tool_outputs', None)
                    if submit_tool_outputs and hasattr(submit_tool_outputs, 'tool_calls'):
                        tool_calls = submit_tool_outputs.tool_calls
                        # Only handle code_interpreter and retrieval tools here (functions are handled in step events)
                        for tool_call in tool_calls:
                            if tool_call.type == "code_interpreter":
                                tool_outputs[tool_call.id] = {
                                    "tool_call_id": tool_call.id,
                                    "output": "code_interpreter",
                                }
                            elif tool_call.type == "retrieval":
                                tool_outputs[tool_call.id] = {
                                    "tool_call_id": tool_call.id,
                                    "output": "retrieval",
                                }
                    else:
                        # If submit_tool_outputs is not available, we should have collected tool_calls from step events
                        logger.debug(
                            "submit_tool_outputs not found in required_action, relying on step event tool outputs",
                            thread_id=thread_id,
                            run_id=run_id,
                            correlation_id=correlation_id
                        )

            if (
                event.event == "thread.run.requires_action"
                and event.data.required_action
                and event.data.required_action.type == "submit_tool_outputs"
                and tool_outputs
                and run_id
            ):
                # Submit all tool outputs at once with robust error handling
                submission_result = await submit_tool_outputs_with_backoff(
                    self.client, thread_id, run_id, list(tool_outputs.values())
                )
                
                if submission_result is None:
                    # Tool output submission failed permanently
                    logger.error(
                        "Tool output submission failed permanently for run_id=%s, thread_id=%s. "
                        "Attempting to cancel run to prevent hanging state.",
                        run_id, thread_id
                    )
                    # Attempt to cancel the run to prevent it from hanging
                    await cancel_run_safely(self.client, thread_id, run_id)
                    # Don't raise an exception here - let the run complete naturally
                
                # Clear tool outputs for next batch
                tool_outputs.clear()

    async def _process_run(self, thread_id: str, human_query: str) -> list[str]:
        """Process a run and return the final messages."""
        correlation_id = get_or_create_correlation_id()
        
        logger.info(
            "Processing chat request", 
            thread_id=thread_id, 
            correlation_id=correlation_id,
            message_length=len(human_query)
        )

        messages: list[str] = []

        async for event in self._iterate_run_events(thread_id, human_query):
            if (
                event.event == "thread.run.step.completed"
                and event.data.step_details.type == "message_creation"
            ):
                message_id = event.data.step_details.message_creation.message_id
                try:
                    assert self.client is not None, "Client not initialized"
                    thread_message = await self.client.beta.threads.messages.retrieve(
                        thread_id=thread_id, message_id=message_id
                    )
                    logger.debug(
                        "Message retrieved successfully", 
                        thread_id=thread_id, 
                        correlation_id=correlation_id,
                        message_id=message_id
                    )
                except OpenAIError as err:
                    logger.error(
                        "OpenAI message retrieval failed", 
                        thread_id=thread_id, 
                        correlation_id=correlation_id,
                        message_id=message_id,
                        error_type="OpenAIError",
                        error=str(err)
                    )
                    raise HTTPException(
                        status_code=502, 
                        detail=f"Failed to retrieve message (correlation_id: {correlation_id[:8]})"
                    ) from err
                except Exception as err:  # noqa: BLE001
                    logger.error(
                        "Unexpected error retrieving message", 
                        thread_id=thread_id, 
                        correlation_id=correlation_id,
                        message_id=message_id,
                        error_type=type(err).__name__,
                        error=str(err)
                    )
                    raise HTTPException(
                        status_code=500, 
                        detail=f"Internal server error (correlation_id: {correlation_id[:8]})"
                    ) from err
                    
                for content in thread_message.content:
                    if hasattr(content, "text"):
                        messages.append(content.text.value)

        logger.info(
            "Run processing completed", 
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
                assert self.client is not None, "Client not initialized"
                thread = await self.client.beta.threads.create()
                logger.info(
                    "New thread created successfully", 
                    thread_id=thread.id, 
                    correlation_id=correlation_id
                )
                return {
                    "thread_id": thread.id, 
                    "initial_message": self.engine_config.initial_message,
                    "correlation_id": correlation_id
                }
            except OpenAIError as err:
                logger.error(
                    "OpenAI thread creation failed", 
                    correlation_id=correlation_id,
                    error_type="OpenAIError",
                    error=str(err)
                )
                raise HTTPException(
                    status_code=502, 
                    detail=f"Failed to start thread (correlation_id: {correlation_id[:8]})"
                ) from err
            except Exception as err:  # noqa: BLE001
                logger.error(
                    "Unexpected error starting thread", 
                    correlation_id=correlation_id,
                    error_type=type(err).__name__,
                    error=str(err)
                )
                raise HTTPException(
                    status_code=500, 
                    detail=f"Internal server error (correlation_id: {correlation_id[:8]})"
                ) from err

    async def chat_endpoint(self, request: ChatRequest) -> ChatResponse:
        """Process a user message and return assistant responses."""
        with CorrelationContext() as correlation_id:
            if not request.thread_id:
                logger.error(
                    "Missing thread_id in chat request", 
                    correlation_id=correlation_id
                )
                raise HTTPException(
                    status_code=400, 
                    detail=f"Missing thread_id (correlation_id: {correlation_id[:8]})"
                )
                
            responses = await self._process_run(request.thread_id, request.message)
            logger.debug("Chat processing completed", 
                        thread_id=request.thread_id, response_count=len(responses))
            return ChatResponse(responses=responses)

    async def stream_endpoint(self, websocket: WebSocket) -> None:
        """Forward run events directly through a WebSocket connection with robust error handling."""
        with CorrelationContext() as correlation_id:
            connection_id = id(websocket)
            
            try:
                await websocket.accept()
                logger.info("WebSocket connection accepted", connection_id=connection_id)
            except Exception as err:  # noqa: BLE001
                logger.error("WebSocket accept failed", 
                            connection_id=connection_id, error_type=type(err).__name__, error=str(err))
                return
            
            try:
                # Receive and validate request data
                try:
                    data = await websocket.receive_json()
                except json.JSONDecodeError as err:
                    logger.warning("WebSocket JSON parsing error",
                                 connection_id=connection_id, error_type="JSONDecodeError", error=str(err))
                    await self._send_websocket_error(websocket, "JSON parsing error", "invalid_json")
                    return
                except Exception as err:  # noqa: BLE001
                    logger.error("WebSocket receive error",
                               connection_id=connection_id, error_type=type(err).__name__, error=str(err))
                    await self._send_websocket_error(websocket, "Failed to receive request", "receive_error")
                    return
                
                # Validate request fields
                thread_id = data.get("thread_id")
                message = data.get("message")
                
                if not thread_id or not message:
                    logger.warning("WebSocket request missing required fields",
                                 connection_id=connection_id, has_thread_id=bool(thread_id), 
                                 has_message=bool(message))
                    await self._send_websocket_error(websocket, "Missing thread_id or message", "missing_fields")
                    return

                logger.info(
                    "Starting WebSocket stream", 
                    thread_id=thread_id, 
                    correlation_id=correlation_id,
                    message_length=len(message)
                )

                # Stream events with error handling
                try:
                    async for event in self._process_run_stream(thread_id, message):
                        try:
                            await websocket.send_text(event.model_dump_json())
                        except Exception as err:  # noqa: BLE001
                            if self._is_websocket_disconnect(err):
                                logger.info("WebSocket client disconnected during stream",
                                          connection_id=connection_id, thread_id=thread_id)
                                return
                            else:
                                logger.error("WebSocket send error",
                                           connection_id=connection_id, thread_id=thread_id, 
                                           error_type=type(err).__name__, error=str(err))
                                await self._send_websocket_error(websocket, "Failed to send event", "send_error")
                                return
                                
                    logger.info(
                        "WebSocket stream completed", 
                        thread_id=thread_id, 
                        correlation_id=correlation_id
                    )
                               
                except OpenAIError as err:
                    logger.error("OpenAI error during WebSocket stream",
                               connection_id=connection_id, thread_id=thread_id, error_type="OpenAIError", error=str(err))
                    await self._send_websocket_error(websocket, f"OpenAI service error: {err}", "openai_error")
                    return
                except Exception as err:  # noqa: BLE001
                    logger.error(
                        "Unexpected error during WebSocket stream", 
                        thread_id=thread_id, 
                        correlation_id=correlation_id,
                        error_type=type(err).__name__,
                        error=str(err)
                    )
                    await websocket.send_json({
                        "error": f"Stream error (correlation_id: {correlation_id[:8]})"
                    })
                
            except Exception as err:  # noqa: BLE001
                logger.error("Critical WebSocket error", 
                            connection_id=connection_id, error_type=type(err).__name__, error=str(err))
                # Don't attempt to send error message as connection state is unknown
            finally:
                await websocket.close()
                
    async def _send_websocket_error(self, websocket: WebSocket, message: str, error_code: str) -> None:
        """Send error message to WebSocket client with proper error handling."""
        try:
            await websocket.send_json({
                "error": message,
                "error_code": error_code,
                "timestamp": json.dumps({"timestamp": "now"})  # Simple timestamp placeholder
            })
        except Exception as err:  # noqa: BLE001
            logger.debug("Failed to send WebSocket error message", 
                        error_message=message, error_code=error_code, 
                        error_type=type(err).__name__, error=str(err))
            
    def _is_websocket_disconnect(self, error: Exception) -> bool:
        """Check if error indicates WebSocket disconnect."""
        error_name = type(error).__name__
        error_message = str(error).lower()
        
        # Check for common WebSocket disconnect patterns
        disconnect_patterns = [
            "websocketdisconnect",
            "connection closed",
            "connection lost",
            "broken pipe",
            "connection reset"
        ]
        
        return (error_name == "WebSocketDisconnect" or 
                any(pattern in error_message for pattern in disconnect_patterns))


def get_app() -> FastAPI:
    """Return a fully configured FastAPI application."""
    # Configure structured logging
    configure_structlog()
    
    # Use the singleton pattern to avoid re-initialization
    api_instance = _ensure_api_initialized()
    return api_instance.app


# Create a singleton instance for backward compatibility
# Note: Instantiation is deferred to avoid initialization errors during imports
api: Optional[AssistantEngineAPI] = None
app: Optional[FastAPI] = None


def _ensure_api_initialized() -> AssistantEngineAPI:
    """Ensure the API singleton is initialized."""
    global api, app
    if api is None:
        api = AssistantEngineAPI()
        app = api.app
    return api


async def process_run(thread_id: str, human_query: str) -> list[str]:
    """Proxy to the API instance for backward compatibility."""
    api_instance = _ensure_api_initialized()
    return await api_instance._process_run(thread_id, human_query)


async def process_run_stream(thread_id: str, human_query: str) -> AsyncGenerator[Any, None]:
    """Proxy streaming run for backward compatibility."""
    api_instance = _ensure_api_initialized()
    async for event in api_instance._process_run_stream(thread_id, human_query):
        yield event


# Export TOOL_MAP for tests
__all__ = ["get_app", "AssistantEngineAPI", "TOOL_MAP", "process_run", "process_run_stream"]