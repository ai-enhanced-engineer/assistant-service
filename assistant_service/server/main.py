"""FastAPI application entrypoint for the OpenAI Assistant service.

Provides HTTP and WebSocket endpoints for conversational AI interactions with support
for both synchronous JSON responses and asynchronous Server-Sent Events streaming."""

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
    get_sse_stream_handler,
    get_websocket_stream_handler,
)
from ..entities import HEADER_CORRELATION_ID, SSE_RESPONSE_HEADERS, ServiceConfig
from ..entities.schemas import ChatRequest, ChatResponse, StartResponse
from ..structured_logging import CorrelationContext, configure_structlog, get_logger
from .error_handlers import ErrorHandler

logger = get_logger("MAIN")


def create_lifespan(api_instance: "AssistantEngineAPI") -> Any:
    """Create FastAPI lifespan manager for graceful startup/shutdown handling."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        logger.info("Application starting up...")
        yield
        logger.info("Application shutting down...")
        await api_instance.client.close()

    return lifespan


class AssistantEngineAPI:
    """Core API orchestrator that manages OpenAI Assistant integration and request routing."""

    def __init__(self, service_config: Optional[ServiceConfig] = None) -> None:
        self.service_config = service_config or ServiceConfig()

        # Repository layer switches between local (dev) and GCP (production)
        secret_repository = get_secret_repository(self.service_config)
        config_repository = get_config_repository(self.service_config)

        self.assistant_config = get_assistant_config(secret_repository, config_repository)

        self.client: AsyncOpenAI = get_openai_client(self.service_config)
        self.orchestrator = get_orchestrator(self.client, self.service_config, self.assistant_config)

        # Separate handlers for WebSocket (bidirectional) vs SSE (server-push) streaming
        self.websocket_stream_handler = get_websocket_stream_handler(self.orchestrator, self.service_config)
        self.sse_stream_handler = get_sse_stream_handler(self.orchestrator)

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

        self.app = FastAPI(title="Assistant Engine", lifespan=create_lifespan(self))
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Register all API endpoints including health check, thread creation, and chat interfaces."""

        @self.app.get("/")
        async def root() -> dict[str, str]:
            return {"message": "Assistant Engine is running"}

        @self.app.get("/start")
        async def start() -> StartResponse:
            """Create a new OpenAI thread for conversation tracking."""
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
            """Process user messages with support for both synchronous and streaming responses.

            Response format is determined by the Accept header:
            - application/json: Returns complete response after processing
            - text/event-stream: Streams response chunks as they're generated
            """
            with CorrelationContext() as correlation_id:
                if not request.thread_id:
                    raise ErrorHandler.handle_validation_error("Missing thread_id", correlation_id)

                # Response format determined by Accept header
                accept_header = http_request.headers.get("accept", "")
                if "text/event-stream" in accept_header:
                    logger.info(
                        "Processing streaming chat request",
                        thread_id=request.thread_id,
                        correlation_id=correlation_id,
                        message_length=len(request.message),
                    )

                    headers = {
                        HEADER_CORRELATION_ID: correlation_id,
                        **SSE_RESPONSE_HEADERS,
                    }

                    return EventSourceResponse(
                        self.sse_stream_handler.format_events(request.thread_id, request.message),
                        headers=headers,
                    )
                else:
                    responses = await self.orchestrator.process_run(request.thread_id, request.message)
                    logger.debug(
                        "Chat processing completed", thread_id=request.thread_id, response_count=len(responses)
                    )
                    return ChatResponse(responses=responses)

        @self.app.websocket("/ws/chat")
        async def ws_chat(websocket: WebSocket) -> None:
            """WebSocket endpoint for bidirectional real-time chat with event streaming."""
            await self.websocket_stream_handler.handle_connection(websocket)


def get_app() -> FastAPI:
    """Factory function for creating the FastAPI application instance."""
    configure_structlog()
    api_instance = AssistantEngineAPI()
    return api_instance.app


__all__ = ["get_app", "AssistantEngineAPI"]
