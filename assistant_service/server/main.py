"""Main application module for the Assistant Engine.

This module bootstraps the FastAPI application with all necessary components.
"""

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional

from fastapi import FastAPI, WebSocket
from openai import AsyncOpenAI, OpenAIError

from ..bootstrap import (
    get_config_repository,
    get_engine_config,
    get_openai_client,
    get_orchestrator,
    get_secret_repository,
    get_stream_handler,
)
from ..entities import ServiceConfig
from ..entities.schemas import ChatRequest, ChatResponse, StartResponse
from ..structured_logging import CorrelationContext, configure_structlog, get_logger
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

        self.engine_config = get_engine_config(secret_repository, config_repository)

        # Create components using factory functions
        self.client: AsyncOpenAI = get_openai_client(self.engine_config)
        self.orchestrator = get_orchestrator(self.client, self.engine_config)
        self.stream_handler = get_stream_handler(self.orchestrator, self.engine_config.stream_handler_type)

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
            orchestrator_type=self.engine_config.orchestrator_type,
            stream_handler_type=self.engine_config.stream_handler_type,
            tool_executor_type=self.engine_config.tool_executor_type,
            message_parser_type=self.engine_config.message_parser_type,
        )

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

                responses = await self.orchestrator.process_run(request.thread_id, request.message)
                logger.debug("Chat processing completed", thread_id=request.thread_id, response_count=len(responses))
                return ChatResponse(responses=responses)

        @self.app.websocket("/stream")
        async def stream(websocket: WebSocket) -> None:
            """Forward run events through WebSocket with robust error handling."""
            await self.stream_handler.handle_connection(websocket)


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
    return await api_instance.orchestrator.process_run(thread_id, human_query)


async def process_run_stream(thread_id: str, human_query: str) -> AsyncGenerator[Any, None]:
    """Proxy streaming run for backward compatibility."""
    api_instance = _ensure_api_initialized()
    async for event in api_instance.orchestrator.process_run_stream(thread_id, human_query):
        yield event


# Export for backward compatibility
__all__ = ["get_app", "AssistantEngineAPI", "process_run", "process_run_stream"]
