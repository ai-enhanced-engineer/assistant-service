"""API endpoints for the assistant service."""

import json
from typing import TYPE_CHECKING, Any

from fastapi import HTTPException, WebSocket
from openai import OpenAIError

from ..structured_logging import CorrelationContext, get_logger
from .error_handlers import ErrorHandler, WebSocketErrorHandler
from .schemas import ChatRequest, ChatResponse, StartResponse

if TYPE_CHECKING:
    from openai import AsyncOpenAI

    from ..entities import EngineAssistantConfig
    from ..processors.run_processor import RunProcessor

logger = get_logger("API_ENDPOINTS")


class APIEndpoints:
    """HTTP and WebSocket endpoint handlers."""

    def __init__(self, client: "AsyncOpenAI", config: "EngineAssistantConfig", run_processor: "RunProcessor"):
        """Initialize with dependencies."""
        self.client = client
        self.config = config
        self.run_processor = run_processor

    async def root(self) -> dict[str, str]:
        """Root endpoint."""
        return {"message": "Assistant Engine is running"}

    async def start_endpoint(self) -> StartResponse:
        """Start a new conversation and return the thread information."""
        with CorrelationContext() as correlation_id:
            try:
                thread = await self.client.beta.threads.create()
                logger.info("New thread created successfully", thread_id=thread.id, correlation_id=correlation_id)
                return StartResponse(
                    thread_id=thread.id,
                    initial_message=self.config.initial_message,
                    correlation_id=correlation_id,
                )
            except OpenAIError as err:
                raise ErrorHandler.handle_openai_error(err, "start thread", correlation_id)
            except Exception as err:  # noqa: BLE001
                raise ErrorHandler.handle_unexpected_error(err, "starting thread", correlation_id)

    async def chat_endpoint(self, request: ChatRequest) -> ChatResponse:
        """Process a user message and return assistant responses."""
        with CorrelationContext() as correlation_id:
            if not request.thread_id:
                raise ErrorHandler.handle_validation_error("Missing thread_id", correlation_id)

            responses = await self.run_processor.process_run(request.thread_id, request.message)
            logger.debug("Chat processing completed", thread_id=request.thread_id, response_count=len(responses))
            return ChatResponse(responses=responses)

    async def stream_endpoint(self, websocket: WebSocket) -> None:
        """Forward run events through WebSocket with robust error handling."""
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
