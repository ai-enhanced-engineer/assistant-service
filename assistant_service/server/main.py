"""Main application module for the Assistant Engine.

This module bootstraps the FastAPI application with all necessary components.
"""

import json
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional

from fastapi import FastAPI, Request, WebSocket
from openai import AsyncOpenAI, OpenAIError
from sse_starlette.sse import EventSourceResponse

from ..bootstrap import (
    get_assistant_config,
    get_config_repository,
    get_openai_client,
    get_orchestrator,
    get_secret_repository,
    get_stream_handler,
)
from ..entities import SSE_STREAM_EVENTS, ServiceConfig
from ..entities.schemas import ChatRequest, ChatResponse, StartResponse
from ..structured_logging import CorrelationContext, configure_structlog, get_logger, get_or_create_correlation_id
from .error_handlers import ErrorHandler

# Use new structured logger
logger = get_logger("MAIN")


def create_lifespan(api_instance: "AssistantEngineAPI") -> Any:
    """Create a lifespan context manager for the API instance."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        """Manage application startup and shutdown."""
        logger.info("Application starting up...")
        yield
        logger.info("Application shutting down...")
        await api_instance.client.close()

    return lifespan


class AssistantEngineAPI:
    """Main API class for the assistant engine."""

    def __init__(self, service_config: Optional[ServiceConfig] = None) -> None:
        """Initialize the assistant engine with configuration.

        Args:
            service_config: Optional service configuration. If not provided, will be loaded from environment.
        """
        # Load service configuration
        self.service_config = service_config or ServiceConfig()

        # Set up repositories using factory functions
        secret_repository = get_secret_repository(self.service_config)
        config_repository = get_config_repository(self.service_config)

        self.assistant_config = get_assistant_config(secret_repository, config_repository)

        # Create components using factory functions
        self.client: AsyncOpenAI = get_openai_client(self.service_config)
        self.orchestrator = get_orchestrator(self.client, self.service_config, self.assistant_config)
        self.stream_handler = get_stream_handler(self.orchestrator, self.service_config)

        # Log configuration (without sensitive data)
        logger.info(
            "Booting with config",
            assistant_id=self.assistant_config.assistant_id,
            assistant_name=self.assistant_config.assistant_name,
            initial_message=self.assistant_config.initial_message,
            code_interpreter=self.assistant_config.code_interpreter,
            file_search=self.assistant_config.file_search,
            function_names=self.assistant_config.function_names,
            openai_apikey="sk" if self.service_config.openai_api_key else None,
            orchestrator_type=self.service_config.orchestrator_type,
            stream_handler_type=self.service_config.stream_handler_type,
            tool_executor_type=self.service_config.tool_executor_type,
            message_parser_type=self.service_config.message_parser_type,
        )

        # Create FastAPI app
        self.app = FastAPI(title="Assistant Engine", lifespan=create_lifespan(self))

        # Routes will be added after components are initialized
        self._setup_routes()

    async def _format_sse_events(self, thread_id: str, human_query: str) -> AsyncGenerator[dict[str, Any], None]:
        """Format OpenAI streaming events as SSE events with enhanced features."""
        import time

        correlation_id = get_or_create_correlation_id()
        start_time = time.time()
        event_count = 0
        last_heartbeat = time.time()
        heartbeat_interval = 15  # Send heartbeat every 15 seconds

        try:
            async for event in self.orchestrator.process_run_stream(thread_id, human_query):
                # Send heartbeat if needed
                current_time = time.time()
                if current_time - last_heartbeat > heartbeat_interval:
                    yield {
                        "comment": "keepalive",
                        "retry": 5000,  # Retry after 5 seconds if connection lost
                    }
                    last_heartbeat = current_time

                # Pass through relevant events to the client
                if event.event in SSE_STREAM_EVENTS:
                    event_count += 1
                    yield {
                        "event": event.event,
                        "data": event.model_dump_json(),
                        "id": f"{correlation_id}_{event.event}_{event_count}",
                        "retry": 5000,  # Retry after 5 seconds if connection lost
                    }

                    # Add metadata for completion events
                    if event.event == "thread.run.completed":
                        elapsed_time = time.time() - start_time
                        yield {
                            "event": "metadata",
                            "data": json.dumps(
                                {
                                    "correlation_id": correlation_id,
                                    "elapsed_time_seconds": round(elapsed_time, 3),
                                    "event_count": event_count,
                                    "thread_id": thread_id,
                                }
                            ),
                            "id": f"{correlation_id}_metadata",
                        }

        except Exception as e:
            # Send error event to client
            logger.error(
                "Error in SSE stream",
                error=str(e),
                error_type=type(e).__name__,
                thread_id=thread_id,
                correlation_id=correlation_id,
            )
            yield {
                "event": "error",
                "data": json.dumps(
                    {
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "correlation_id": correlation_id,
                    }
                ),
                "id": f"{correlation_id}_error",
            }

    def _setup_routes(self) -> None:
        """Set up routes after components are initialized."""

        @self.app.get("/")
        async def root() -> dict[str, str]:
            return {"message": "Assistant Engine is running"}

        @self.app.get("/start")
        async def start() -> StartResponse:
            """Start a new conversation and return the thread information."""
            with CorrelationContext() as correlation_id:
                try:
                    thread = await self.client.beta.threads.create()
                    logger.info("New thread created successfully", thread_id=thread.id, correlation_id=correlation_id)
                    return StartResponse(
                        thread_id=thread.id,
                        initial_message=self.assistant_config.initial_message,
                        correlation_id=correlation_id,
                    )
                except OpenAIError as err:
                    raise ErrorHandler.handle_openai_error(err, "start thread", correlation_id)
                except Exception as err:  # noqa: BLE001
                    raise ErrorHandler.handle_unexpected_error(err, "starting thread", correlation_id)

        @self.app.post("/chat", response_model=ChatResponse)
        async def chat(request: ChatRequest, http_request: Request) -> ChatResponse | EventSourceResponse:
            """Process a user message and return assistant responses.

            Supports both regular JSON responses and Server-Sent Events streaming
            based on the Accept header.
            """
            with CorrelationContext() as correlation_id:
                if not request.thread_id:
                    raise ErrorHandler.handle_validation_error("Missing thread_id", correlation_id)

                # Check if client wants streaming response
                accept_header = http_request.headers.get("accept", "")
                if "text/event-stream" in accept_header:
                    logger.info(
                        "Processing streaming chat request",
                        thread_id=request.thread_id,
                        correlation_id=correlation_id,
                        message_length=len(request.message),
                    )

                    # Return SSE streaming response
                    return EventSourceResponse(
                        self._format_sse_events(request.thread_id, request.message),
                        headers={
                            "X-Correlation-ID": correlation_id,
                            "Cache-Control": "no-cache, no-transform",
                            "X-Accel-Buffering": "no",  # Disable nginx buffering
                            "Connection": "keep-alive",
                            "X-Content-Type-Options": "nosniff",
                        },
                    )
                else:
                    # Regular non-streaming response
                    responses = await self.orchestrator.process_run(request.thread_id, request.message)
                    logger.debug(
                        "Chat processing completed", thread_id=request.thread_id, response_count=len(responses)
                    )
                    return ChatResponse(responses=responses)

        @self.app.websocket("/ws/chat")
        async def ws_chat(websocket: WebSocket) -> None:
            """Handle WebSocket chat connections for real-time streaming."""
            await self.stream_handler.handle_connection(websocket)


def get_app() -> FastAPI:
    """Return a fully configured FastAPI application."""
    # Configure structured logging
    configure_structlog()

    # Create and return a new API instance
    api_instance = AssistantEngineAPI()
    return api_instance.app


# Public API exports
__all__ = ["get_app", "AssistantEngineAPI"]
