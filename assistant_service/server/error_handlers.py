"""Centralized error handling for the assistant service."""

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException, WebSocket
from openai import OpenAIError

from ..structured_logging import get_logger

logger = get_logger("ERROR_HANDLERS")


class ErrorHandler:
    """Centralized error handling utilities."""

    @staticmethod
    def handle_openai_error(err: OpenAIError, operation: str, correlation_id: str, **context: Any) -> HTTPException:
        """Convert OpenAI errors to HTTP exceptions with consistent logging."""
        logger.error(
            f"OpenAI {operation} failed",
            correlation_id=correlation_id,
            error_type="OpenAIError",
            error=str(err),
            **context,
        )
        return HTTPException(status_code=502, detail=f"Failed to {operation} (correlation_id: {correlation_id[:8]})")

    @staticmethod
    def handle_unexpected_error(err: Exception, operation: str, correlation_id: str, **context: Any) -> HTTPException:
        """Convert unexpected errors to HTTP exceptions with consistent logging."""
        logger.error(
            f"Unexpected error during {operation}",
            correlation_id=correlation_id,
            error_type=type(err).__name__,
            error=str(err),
            **context,
        )
        return HTTPException(status_code=500, detail=f"Internal server error (correlation_id: {correlation_id[:8]})")

    @staticmethod
    def handle_validation_error(message: str, correlation_id: str, **context: Any) -> HTTPException:
        """Handle validation errors with consistent logging."""
        logger.error(message, correlation_id=correlation_id, **context)
        return HTTPException(status_code=400, detail=f"{message} (correlation_id: {correlation_id[:8]})")


class WebSocketErrorHandler:
    """Error handling specific to WebSocket connections."""

    @staticmethod
    async def send_error(
        websocket: WebSocket, message: str, error_code: str, connection_id: Optional[int] = None
    ) -> None:
        """Send error message to WebSocket client with proper error handling."""
        try:
            await websocket.send_json(
                {
                    "error": message,
                    "error_code": error_code,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        except Exception as err:  # noqa: BLE001
            logger.debug(
                "Failed to send WebSocket error message",
                error_message=message,
                error_code=error_code,
                error_type=type(err).__name__,
                error=str(err),
                connection_id=connection_id,
            )

    @staticmethod
    def is_disconnect_error(error: Exception) -> bool:
        """Check if error indicates WebSocket disconnect."""
        error_name = type(error).__name__
        error_message = str(error).lower()

        disconnect_patterns = [
            "websocketdisconnect",
            "connection closed",
            "connection lost",
            "broken pipe",
            "connection reset",
        ]

        return error_name == "WebSocketDisconnect" or any(pattern in error_message for pattern in disconnect_patterns)
