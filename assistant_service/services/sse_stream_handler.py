"""SSE (Server-Sent Events) stream handling logic with enhanced features for the assistant service."""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from threading import Lock
from typing import TYPE_CHECKING, Any, AsyncGenerator

from ..entities import ERROR_EVENT, METADATA_EVENT, RUN_COMPLETED_EVENT, SSE_STREAM_EVENTS
from ..entities.config import ServiceConfig
from ..entities.headers import SSE_CORRELATION_ID_LENGTH, SSE_HEARTBEAT_COMMENT
from ..structured_logging import get_logger, get_or_create_correlation_id

if TYPE_CHECKING:
    from .openai_orchestrator import IOrchestrator

logger = get_logger("SSE_STREAM_HANDLER")

# Global rate limiting tracker (thread-safe)
_connection_tracker = defaultdict(int)
_connection_lock = Lock()

# Event serialization cache for performance
_event_cache: dict[str, str] = {}
_cache_lock = Lock()


class ISSEStreamHandler(ABC):
    """Interface for SSE stream handling."""

    @abstractmethod
    def format_events(self, thread_id: str, human_query: str, client_ip: str = "unknown") -> AsyncGenerator[dict[str, Any], None]:
        """Format OpenAI streaming events as SSE events.

        Args:
            thread_id: The thread ID for the conversation
            human_query: The user's query message
            client_ip: Client IP address for rate limiting

        Yields:
            SSE-formatted event dictionaries
        """
        pass


class SSEStreamHandler(ISSEStreamHandler):
    """Enhanced SSE handler with resource management, performance optimizations, and security features."""

    def __init__(self, orchestrator: "IOrchestrator", config: ServiceConfig):
        """Initialize enhanced SSE stream handler.

        Args:
            orchestrator: The orchestrator to get events from
            config: Service configuration with SSE settings
        """
        self.orchestrator = orchestrator
        self.config = config
        self.heartbeat_interval = config.sse_heartbeat_interval
        self.max_connection_duration = config.sse_max_connection_duration
        self.retry_interval = config.sse_retry_interval
        self.max_connections_per_client = config.sse_max_connections_per_client
        self.active_connections = 0

    def _truncate_correlation_id(self, correlation_id: str) -> str:
        """Truncate correlation ID for security to prevent internal state exposure.
        
        Args:
            correlation_id: Full correlation ID
            
        Returns:
            Truncated correlation ID for client-facing use
        """
        return correlation_id[:SSE_CORRELATION_ID_LENGTH]

    def _check_rate_limit(self, client_ip: str) -> bool:
        """Check if client IP has exceeded connection limit.
        
        Args:
            client_ip: Client IP address
            
        Returns:
            True if within rate limit, False if exceeded
        """
        with _connection_lock:
            current_connections = _connection_tracker[client_ip]
            if current_connections >= self.max_connections_per_client:
                logger.warning(
                    "Rate limit exceeded for client",
                    client_ip=client_ip,
                    current_connections=current_connections,
                    max_allowed=self.max_connections_per_client,
                )
                return False
            _connection_tracker[client_ip] += 1
            return True

    def _release_connection(self, client_ip: str) -> None:
        """Release connection count for client IP.
        
        Args:
            client_ip: Client IP address
        """
        with _connection_lock:
            if _connection_tracker[client_ip] > 0:
                _connection_tracker[client_ip] -= 1
                if _connection_tracker[client_ip] == 0:
                    del _connection_tracker[client_ip]

    def _get_cached_event(self, event_key: str, event_data: dict) -> str:
        """Get cached serialized event data for performance.
        
        Args:
            event_key: Cache key for the event
            event_data: Event data to serialize
            
        Returns:
            Serialized event data (cached or newly serialized)
        """
        with _cache_lock:
            if event_key not in _event_cache:
                _event_cache[event_key] = json.dumps(event_data)
                # Keep cache size reasonable
                if len(_event_cache) > 1000:
                    # Remove oldest 10% of entries
                    to_remove = list(_event_cache.keys())[:100]
                    for key in to_remove:
                        del _event_cache[key]
            return _event_cache[event_key]

    async def format_events(self, thread_id: str, human_query: str, client_ip: str = "unknown") -> AsyncGenerator[dict[str, Any], None]:
        """Format OpenAI streaming events as SSE events with enhanced features.

        Features:
        - Connection timeout to prevent memory leaks
        - Rate limiting per client IP
        - Heartbeat mechanism with configurable intervals
        - Event filtering based on SSE_STREAM_EVENTS
        - Metadata events with timing information
        - Error handling with truncated correlation IDs
        - Event serialization caching for performance

        Args:
            thread_id: The thread ID for the conversation
            human_query: The user's query message
            client_ip: Client IP address for rate limiting

        Yields:
            SSE-formatted event dictionaries with proper formatting for EventSourceResponse
        """
        # Rate limiting check
        if not self._check_rate_limit(client_ip):
            yield {
                "event": ERROR_EVENT,
                "data": self._get_cached_event(
                    "rate_limit_error",
                    {
                        "error": "Rate limit exceeded",
                        "error_type": "RateLimitError",
                        "max_connections": self.max_connections_per_client,
                    }
                ),
                "id": "rate_limit_error",
                "retry": self.retry_interval,
            }
            return

        correlation_id = get_or_create_correlation_id()
        truncated_id = self._truncate_correlation_id(correlation_id)
        start_time = time.time()
        event_count = 0
        last_heartbeat = start_time

        try:
            self.active_connections += 1
            logger.info(
                "SSE connection established",
                client_ip=client_ip,
                thread_id=thread_id,
                correlation_id=correlation_id,
                active_connections=self.active_connections,
            )

            async for event in self.orchestrator.process_run_stream(thread_id, human_query):
                current_time = time.time()
                
                # Connection timeout check
                if current_time - start_time > self.max_connection_duration:
                    logger.info(
                        "SSE connection timeout reached",
                        client_ip=client_ip,
                        thread_id=thread_id,
                        correlation_id=correlation_id,
                        duration=current_time - start_time,
                    )
                    yield {
                        "event": ERROR_EVENT,
                        "data": self._get_cached_event(
                            "connection_timeout",
                            {
                                "error": "Connection timeout reached",
                                "error_type": "ConnectionTimeoutError",
                                "max_duration": self.max_connection_duration,
                                "timestamp": current_time,
                            }
                        ),
                        "id": f"{truncated_id}_timeout_{int(current_time)}",
                        "retry": self.retry_interval,
                    }
                    break

                # Send heartbeat if needed
                if current_time - last_heartbeat > self.heartbeat_interval:
                    yield {
                        "comment": SSE_HEARTBEAT_COMMENT,
                        "retry": self.retry_interval,
                    }
                    last_heartbeat = current_time

                # Pass through relevant events to the client
                if event.event in SSE_STREAM_EVENTS:
                    event_count += 1
                    
                    # Use caching for event serialization
                    cache_key = f"{event.event}_{hash(str(event.model_dump()))}"
                    
                    yield {
                        "event": event.event,
                        "data": self._get_cached_event(cache_key, event.model_dump()),
                        "id": f"{truncated_id}_{event.event}_{event_count}",
                        "retry": self.retry_interval,
                    }

                    # Add metadata for completion events
                    if event.event == RUN_COMPLETED_EVENT:
                        elapsed_time = current_time - start_time
                        metadata = {
                            "correlation_id": truncated_id,
                            "elapsed_time_seconds": round(elapsed_time, 3),
                            "event_count": event_count,
                            "thread_id": thread_id,
                            "timestamp": current_time,
                        }
                        yield {
                            "event": METADATA_EVENT,
                            "data": self._get_cached_event(f"metadata_{thread_id}", metadata),
                            "id": f"{truncated_id}_metadata",
                            "retry": self.retry_interval,
                        }

        except Exception as e:
            # Send standardized error event to client
            current_time = time.time()
            logger.error(
                "Error in SSE stream",
                error=str(e),
                error_type=type(e).__name__,
                thread_id=thread_id,
                correlation_id=correlation_id,
                client_ip=client_ip,
            )
            error_data = {
                "error": str(e),
                "error_type": type(e).__name__,
                "correlation_id": truncated_id,
                "timestamp": current_time,
            }
            yield {
                "event": ERROR_EVENT,
                "data": self._get_cached_event(f"error_{type(e).__name__}", error_data),
                "id": f"{truncated_id}_error_{int(current_time)}",
                "retry": self.retry_interval,
            }

        finally:
            # Explicit connection cleanup
            self._release_connection(client_ip)
            self.active_connections = max(0, self.active_connections - 1)
            
            elapsed_time = time.time() - start_time
            logger.info(
                "SSE connection closed",
                client_ip=client_ip,
                thread_id=thread_id,
                correlation_id=correlation_id,
                duration=round(elapsed_time, 3),
                event_count=event_count,
                active_connections=self.active_connections,
            )