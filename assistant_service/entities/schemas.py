"""Request and response schemas for the API endpoints."""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Schema for chat messages."""

    thread_id: str
    message: str


class ChatResponse(BaseModel):
    """Schema for chat responses."""

    responses: list[str]


class StartResponse(BaseModel):
    """Schema for start endpoint response."""

    thread_id: str
    initial_message: str
    correlation_id: str


class WebSocketRequest(BaseModel):
    """Schema for WebSocket requests."""

    thread_id: str
    message: str


class WebSocketError(BaseModel):
    """Schema for WebSocket error messages."""

    error: str
    error_code: str
    timestamp: str
