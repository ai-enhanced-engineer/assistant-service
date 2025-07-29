"""Main application module for the Assistant Engine.

This module bootstraps the FastAPI application with all necessary components.
"""

import json
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional

from fastapi import FastAPI, HTTPException, WebSocket
from openai import AsyncOpenAI, OpenAIError

from ..bootstrap import get_config_repository, get_engine_config, get_secret_repository
from ..processors.run_processor import RunProcessor
from ..processors.tool_executor import ToolExecutor
from ..providers.openai_client import OpenAIClientFactory
from ..service_config import ServiceConfig
from ..structured_logging import CorrelationContext, configure_structlog, get_logger
from .error_handlers import ErrorHandler, WebSocketErrorHandler
from .schemas import ChatRequest, ChatResponse, StartResponse

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

        self.engine_config = get_engine_config(secret_repository, config_repository)

        # Create client immediately
        self.client: AsyncOpenAI = OpenAIClientFactory.create_from_config(self.engine_config)

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

        # Initialize all components
        self.tool_executor = ToolExecutor()
        self.run_processor = RunProcessor(self.client, self.engine_config, self.tool_executor)

        # Create FastAPI app
        self.app = FastAPI(title="Assistant Engine", lifespan=create_lifespan(self))

        # Routes will be added after components are initialized
        self._setup_routes()

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
                        initial_message=self.engine_config.initial_message,
                        correlation_id=correlation_id,
                    )
                except OpenAIError as err:
                    raise ErrorHandler.handle_openai_error(err, "start thread", correlation_id)
                except Exception as err:  # noqa: BLE001
                    raise ErrorHandler.handle_unexpected_error(err, "starting thread", correlation_id)

        @self.app.post("/chat", response_model=ChatResponse)
        async def chat(request: ChatRequest) -> ChatResponse:
            """Process a user message and return assistant responses."""
            with CorrelationContext() as correlation_id:
                if not request.thread_id:
                    raise ErrorHandler.handle_validation_error("Missing thread_id", correlation_id)

                responses = await self.run_processor.process_run(request.thread_id, request.message)
                logger.debug("Chat processing completed", thread_id=request.thread_id, response_count=len(responses))
                return ChatResponse(responses=responses)

        @self.app.websocket("/stream")
        async def stream(websocket: WebSocket) -> None:
            """Forward run events through WebSocket with robust error handling."""
            await self._handle_websocket_stream(websocket)

    async def _handle_websocket_stream(self, websocket: WebSocket) -> None:
        """Handle WebSocket connection and message processing."""
        connection_id = id(websocket)

        # Accept connection
        try:
            await websocket.accept()
            logger.info("WebSocket connection accepted", connection_id=connection_id)
        except Exception as err:  # noqa: BLE001
            logger.error(
                "WebSocket accept failed",
                connection_id=connection_id,
                error_type=type(err).__name__,
                error=str(err),
            )
            return

        try:
            await self._handle_websocket_messages(websocket, connection_id)
        except Exception as err:  # noqa: BLE001
            logger.error(
                "Critical WebSocket error",
                connection_id=connection_id,
                error_type=type(err).__name__,
                error=str(err),
            )
        finally:
            logger.info("WebSocket connection closing", connection_id=connection_id)
            await websocket.close()

    async def _handle_websocket_messages(self, websocket: WebSocket, connection_id: int) -> None:
        """Handle WebSocket message loop."""
        while True:
            with CorrelationContext() as correlation_id:
                try:
                    # Receive request
                    data = await self._receive_websocket_request(websocket, connection_id)
                    if data is None:
                        return  # Client disconnected

                    # Validate request
                    thread_id = data.get("thread_id")
                    message = data.get("message")

                    if not thread_id or not message:
                        logger.warning(
                            "WebSocket request missing required fields",
                            connection_id=connection_id,
                            has_thread_id=bool(thread_id),
                            has_message=bool(message),
                        )
                        await WebSocketErrorHandler.send_error(
                            websocket, "Missing thread_id or message", "missing_fields"
                        )
                        continue

                    logger.info(
                        "Starting WebSocket stream",
                        thread_id=thread_id,
                        correlation_id=correlation_id,
                        message_length=len(message),
                    )

                    # Process stream
                    await self._process_websocket_stream(websocket, connection_id, thread_id, message, correlation_id)

                except Exception as err:  # noqa: BLE001
                    logger.error(
                        "Error in message processing loop",
                        connection_id=connection_id,
                        error_type=type(err).__name__,
                        error=str(err),
                    )
                    continue

    async def _receive_websocket_request(self, websocket: WebSocket, connection_id: int) -> dict[str, Any] | None:
        """Receive and parse WebSocket request."""
        try:
            data = await websocket.receive_json()
            return data  # type: ignore[no-any-return]
        except json.JSONDecodeError as err:
            logger.warning(
                "WebSocket JSON parsing error",
                connection_id=connection_id,
                error_type="JSONDecodeError",
                error=str(err),
            )
            await WebSocketErrorHandler.send_error(websocket, "JSON parsing error", "invalid_json")
            return None
        except Exception as err:  # noqa: BLE001
            if WebSocketErrorHandler.is_disconnect_error(err):
                logger.info("WebSocket client disconnected", connection_id=connection_id)
                return None
            logger.error(
                "WebSocket receive error",
                connection_id=connection_id,
                error_type=type(err).__name__,
                error=str(err),
            )
            await WebSocketErrorHandler.send_error(websocket, "Failed to receive request", "receive_error")
            return None

    async def _process_websocket_stream(
        self, websocket: WebSocket, connection_id: int, thread_id: str, message: str, correlation_id: str
    ) -> None:
        """Process and stream events to WebSocket client."""
        try:
            async for event in self.run_processor.process_run_stream(thread_id, message):
                try:
                    await websocket.send_text(event.model_dump_json())
                except Exception as err:  # noqa: BLE001
                    if WebSocketErrorHandler.is_disconnect_error(err):
                        logger.info(
                            "WebSocket client disconnected during stream",
                            connection_id=connection_id,
                            thread_id=thread_id,
                        )
                        return
                    else:
                        logger.error(
                            "WebSocket send error",
                            connection_id=connection_id,
                            thread_id=thread_id,
                            error_type=type(err).__name__,
                            error=str(err),
                        )
                        await WebSocketErrorHandler.send_error(websocket, "Failed to send event", "send_error")
                        break

            logger.info("WebSocket stream completed", thread_id=thread_id, correlation_id=correlation_id)

        except OpenAIError as err:
            logger.error(
                "OpenAI error during WebSocket stream",
                connection_id=connection_id,
                thread_id=thread_id,
                error_type="OpenAIError",
                error=str(err),
            )
            await WebSocketErrorHandler.send_error(websocket, f"OpenAI service error: {err}", "openai_error")
        except HTTPException:
            # Let HTTP exceptions propagate for proper error responses
            raise
        except Exception as err:  # noqa: BLE001
            logger.error(
                "Unexpected error during WebSocket stream",
                thread_id=thread_id,
                correlation_id=correlation_id,
                error_type=type(err).__name__,
                error=str(err),
            )
            await WebSocketErrorHandler.send_error(
                websocket, f"Stream error (correlation_id: {correlation_id[:8]})", "stream_error"
            )


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
    return await api_instance.run_processor.process_run(thread_id, human_query)


async def process_run_stream(thread_id: str, human_query: str) -> AsyncGenerator[Any, None]:
    """Proxy streaming run for backward compatibility."""
    api_instance = _ensure_api_initialized()
    async for event in api_instance.run_processor.process_run_stream(thread_id, human_query):
        yield event


# Export for backward compatibility
__all__ = ["get_app", "AssistantEngineAPI", "process_run", "process_run_stream"]
