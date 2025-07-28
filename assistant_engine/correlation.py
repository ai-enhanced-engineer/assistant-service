"""Correlation ID utilities for request tracing and error context."""

import uuid
from contextvars import ContextVar, Token
from typing import Any, Optional

# Context variable to store correlation ID across async calls
_correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return str(uuid.uuid4())


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID for the current context."""
    _correlation_id.set(correlation_id)


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID."""
    return _correlation_id.get()


def get_or_create_correlation_id() -> str:
    """Get existing correlation ID or create a new one."""
    correlation_id = get_correlation_id()
    if correlation_id is None:
        correlation_id = generate_correlation_id()
        set_correlation_id(correlation_id)
    return correlation_id


class CorrelationContext:
    """Context manager for correlation IDs."""
    
    def __init__(self, correlation_id: Optional[str] = None):
        self.correlation_id = correlation_id or generate_correlation_id()
        self.token: Optional[Token[Optional[str]]] = None
    
    def __enter__(self) -> str:
        self.token = _correlation_id.set(self.correlation_id)
        return self.correlation_id
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.token is not None:
            _correlation_id.reset(self.token)