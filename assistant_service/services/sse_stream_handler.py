"""SSE (Server-Sent Events) stream handling logic for the assistant service."""

import json
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, AsyncGenerator

from ..entities import SSE_STREAM_EVENTS
from ..structured_logging import get_logger, get_or_create_correlation_id

if TYPE_CHECKING:
    from .openai_orchestrator import IOrchestrator

logger = get_logger("SSE_STREAM_HANDLER")


class ISSEStreamHandler(ABC):
    """Interface for SSE stream handling."""

    @abstractmethod
    def format_events(self, thread_id: str, human_query: str) -> AsyncGenerator[dict[str, Any], None]:
        """Format OpenAI streaming events as SSE events.

        Args:
            thread_id: The thread ID for the conversation
            human_query: The user's query message

        Yields:
            SSE-formatted event dictionaries
        """
        pass


class SSEStreamHandler(ISSEStreamHandler):
    """Handles SSE formatting for OpenAI Assistant streaming events."""

    def __init__(self, orchestrator: "IOrchestrator"):
        """Initialize SSE stream handler.

        Args:
            orchestrator: The orchestrator to get events from
        """
        self.orchestrator = orchestrator
        self.heartbeat_interval = 15  # Send heartbeat every 15 seconds

    async def format_events(self, thread_id: str, human_query: str) -> AsyncGenerator[dict[str, Any], None]:
        """Format OpenAI streaming events as SSE events with enhanced features.

        Features:
        - Heartbeat mechanism to keep connections alive
        - Event filtering based on SSE_STREAM_EVENTS
        - Metadata events with timing information
        - Error handling with correlation IDs

        Args:
            thread_id: The thread ID for the conversation
            human_query: The user's query message

        Yields:
            SSE-formatted event dictionaries with proper formatting for EventSourceResponse
        """
        correlation_id = get_or_create_correlation_id()
        start_time = time.time()
        event_count = 0
        last_heartbeat = time.time()

        try:
            async for event in self.orchestrator.process_run_stream(thread_id, human_query):
                # Send heartbeat if needed
                current_time = time.time()
                if current_time - last_heartbeat > self.heartbeat_interval:
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
