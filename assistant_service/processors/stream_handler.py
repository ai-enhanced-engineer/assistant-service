"""Stream handling logic for WebSocket connections in the assistant service."""

import json
from typing import Any

from fastapi import WebSocket as FastAPIWebSocket
from openai import OpenAIError

from ..server.error_handlers import WebSocketErrorHandler
from ..structured_logging import CorrelationContext, get_logger
from .openai_orchestrator import OpenAIOrchestrator

logger = get_logger("STREAM_HANDLER")


class StreamHandler:
    """Handles WebSocket connections and message streaming."""

    def __init__(self, orchestrator: OpenAIOrchestrator):
        """Initialize with an OpenAI orchestrator.

        Args:
            orchestrator: The OpenAI orchestrator to use for processing runs
        """
        self.orchestrator = orchestrator

    async def handle_connection(self, websocket: FastAPIWebSocket) -> None:
        """Handle a WebSocket connection from accept to close.

        Args:
            websocket: The WebSocket connection to handle
        """
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
            await self._handle_message_loop(websocket, connection_id)
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

    async def _handle_message_loop(self, websocket: FastAPIWebSocket, connection_id: int) -> None:
        """Handle the WebSocket message processing loop.

        Args:
            websocket: The WebSocket connection
            connection_id: Unique identifier for the connection
        """
        while True:
            with CorrelationContext() as correlation_id:
                try:
                    # Receive request
                    data = await self._receive_request(websocket, connection_id)
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
                    await self._process_stream(websocket, connection_id, thread_id, message, correlation_id)

                except Exception as err:  # noqa: BLE001
                    logger.error(
                        "Error in message processing loop",
                        connection_id=connection_id,
                        error_type=type(err).__name__,
                        error=str(err),
                    )
                    continue

    async def _receive_request(self, websocket: FastAPIWebSocket, connection_id: int) -> dict[str, Any] | None:
        """Receive and parse a WebSocket request.

        Args:
            websocket: The WebSocket connection
            connection_id: Unique identifier for the connection

        Returns:
            The parsed request data or None if client disconnected
        """
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

    async def _process_stream(
        self, websocket: FastAPIWebSocket, connection_id: int, thread_id: str, message: str, correlation_id: str
    ) -> None:
        """Process and stream events to WebSocket client.

        Args:
            websocket: The WebSocket connection
            connection_id: Unique identifier for the connection
            thread_id: The thread ID for the conversation
            message: The user message to process
            correlation_id: The correlation ID for request tracking
        """
        try:
            async for event in self.orchestrator.process_run_stream(thread_id, message):
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
