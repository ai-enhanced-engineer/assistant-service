"""Tests for enhanced SSE stream handler with new features."""

import asyncio
import json
import time
from typing import Any, AsyncGenerator
from unittest.mock import MagicMock, patch

import pytest

from ai_assistant_service.entities.config import ServiceConfig
from ai_assistant_service.entities.headers import SSE_HEARTBEAT_COMMENT
from ai_assistant_service.services.openai_orchestrator import IOrchestrator
from ai_assistant_service.services.sse_stream_handler import SSEStreamHandler


class MockOrchestrator(IOrchestrator):
    """Mock orchestrator for testing."""

    def __init__(self, events: list[Any]):
        self.events = events

    async def process_run(self, thread_id: str, human_query: str) -> list[str]:
        """Not used in SSE handler tests."""
        return []

    async def process_run_stream(self, thread_id: str, human_query: str) -> AsyncGenerator[Any, None]:
        """Generate test events."""
        for event in self.events:
            yield event


@pytest.fixture
def service_config():
    """Create service config for testing."""
    return ServiceConfig(
        project_id="test-project",
        bucket_id="test-bucket",
        openai_api_key="test-key",
        sse_heartbeat_interval=15.0,
        sse_max_connection_duration=3600.0,
        sse_retry_interval=5000,
        sse_max_connections_per_client=10,
    )


@pytest.fixture
def mock_correlation_id():
    """Mock correlation ID for consistent testing."""
    with patch("ai_assistant_service.services.sse_stream_handler.get_or_create_correlation_id") as mock:
        mock.return_value = "test-correlation-id"
        yield mock


@pytest.mark.asyncio
async def test_sse_handler_filters_events(mock_correlation_id, service_config):
    """Test that SSE handler only passes through events in SSE_STREAM_EVENTS."""
    # Create mock events - some in SSE_STREAM_EVENTS, some not
    mock_event_in_set = MagicMock()
    mock_event_in_set.event = "thread.run.created"
    mock_event_in_set.model_dump_json.return_value = '{"event": "thread.run.created"}'
    mock_event_in_set.model_dump.return_value = {"event": "thread.run.created"}

    mock_event_not_in_set = MagicMock()
    mock_event_not_in_set.event = "not.in.set"
    mock_event_not_in_set.model_dump_json.return_value = '{"event": "not.in.set"}'
    mock_event_not_in_set.model_dump.return_value = {"event": "not.in.set"}

    events = [mock_event_in_set, mock_event_not_in_set, mock_event_in_set]
    orchestrator = MockOrchestrator(events)
    handler = SSEStreamHandler(orchestrator, service_config)

    formatted_events = []
    async for event in handler.format_events("thread-123", "test query", "127.0.0.1"):
        formatted_events.append(event)

    # Should only have 2 events (the ones in SSE_STREAM_EVENTS)
    assert len(formatted_events) == 2
    assert all(event.get("event") == "thread.run.created" for event in formatted_events)
    # Check that correlation IDs are truncated (8 characters from "test-cor")
    assert formatted_events[0]["id"] == "test-cor_thread.run.created_1"
    assert formatted_events[1]["id"] == "test-cor_thread.run.created_2"


@pytest.mark.asyncio
async def test_sse_handler_adds_metadata_on_completion(mock_correlation_id, service_config):
    """Test that metadata event is added when thread.run.completed is received."""
    mock_event = MagicMock()
    mock_event.event = "thread.run.completed"
    mock_event.model_dump_json.return_value = '{"event": "thread.run.completed"}'
    mock_event.model_dump.return_value = {"event": "thread.run.completed"}

    orchestrator = MockOrchestrator([mock_event])
    handler = SSEStreamHandler(orchestrator, service_config)

    formatted_events = []
    async for event in handler.format_events("thread-123", "test query", "127.0.0.1"):
        formatted_events.append(event)

    assert len(formatted_events) == 2
    # First event should be the run completed event
    assert formatted_events[0]["event"] == "thread.run.completed"
    # Second event should be metadata
    assert formatted_events[1]["event"] == "metadata"

    metadata = json.loads(formatted_events[1]["data"])
    assert metadata["correlation_id"] == "test-cor"  # Truncated
    assert metadata["thread_id"] == "thread-123"
    assert metadata["event_count"] == 1
    assert "elapsed_time_seconds" in metadata
    assert "timestamp" in metadata


@pytest.mark.asyncio
async def test_sse_handler_heartbeat_mechanism(mock_correlation_id, service_config):
    """Test that heartbeats are sent when no events come for a while."""

    # Create a slow event generator
    async def slow_events():
        mock_event = MagicMock()
        mock_event.event = "thread.run.created"
        mock_event.model_dump_json.return_value = '{"event": "thread.run.created"}'
        mock_event.model_dump.return_value = {"event": "thread.run.created"}
        yield mock_event
        # Sleep longer than heartbeat interval
        await asyncio.sleep(0.1)  # Simulating delay
        yield mock_event

    orchestrator = MagicMock()
    orchestrator.process_run_stream = MagicMock(return_value=slow_events())

    # Use short heartbeat interval for testing
    service_config.sse_heartbeat_interval = 0.05
    handler = SSEStreamHandler(orchestrator, service_config)

    formatted_events = []
    start_time = time.time()

    async for event in handler.format_events("thread-123", "test query", "127.0.0.1"):
        formatted_events.append(event)
        # Stop after we get at least one heartbeat
        if any(e.get("comment") == SSE_HEARTBEAT_COMMENT for e in formatted_events):
            break
        # Safety timeout
        if time.time() - start_time > 1:
            break

    # Should have at least one heartbeat
    heartbeats = [e for e in formatted_events if e.get("comment") == SSE_HEARTBEAT_COMMENT]
    assert len(heartbeats) >= 1
    assert heartbeats[0]["retry"] == service_config.sse_retry_interval


@pytest.mark.asyncio
async def test_sse_handler_error_handling(mock_correlation_id, service_config):
    """Test that errors are properly formatted as SSE error events."""

    # Create an orchestrator that raises an exception
    async def error_stream(thread_id: str, human_query: str):
        mock_event = MagicMock()
        mock_event.event = "thread.run.created"
        mock_event.model_dump_json.return_value = '{"event": "thread.run.created"}'
        mock_event.model_dump.return_value = {"event": "thread.run.created"}
        yield mock_event
        raise RuntimeError("Test error")

    orchestrator = MagicMock()
    orchestrator.process_run_stream = error_stream

    handler = SSEStreamHandler(orchestrator, service_config)

    formatted_events = []
    async for event in handler.format_events("thread-123", "test query", "127.0.0.1"):
        formatted_events.append(event)

    # Should have the successful event and an error event
    assert len(formatted_events) == 2
    assert formatted_events[0]["event"] == "thread.run.created"
    assert formatted_events[1]["event"] == "error"

    error_data = json.loads(formatted_events[1]["data"])
    assert error_data["error"] == "Test error"
    assert error_data["error_type"] == "RuntimeError"
    assert error_data["correlation_id"] == "test-cor"  # Truncated
    assert "timestamp" in error_data


@pytest.mark.asyncio
async def test_sse_handler_event_formatting(mock_correlation_id, service_config):
    """Test that events are properly formatted with all required fields."""
    mock_event = MagicMock()
    mock_event.event = "thread.message.delta"
    mock_event.model_dump_json.return_value = '{"event": "thread.message.delta", "data": "test"}'
    mock_event.model_dump.return_value = {"event": "thread.message.delta", "data": "test"}

    orchestrator = MockOrchestrator([mock_event])
    handler = SSEStreamHandler(orchestrator, service_config)

    formatted_events = []
    async for event in handler.format_events("thread-123", "test query", "127.0.0.1"):
        formatted_events.append(event)

    assert len(formatted_events) == 1
    event = formatted_events[0]

    # Check all required SSE fields
    assert event["event"] == "thread.message.delta"
    # Note: Using cached event data, not the raw model_dump_json
    assert '"event": "thread.message.delta"' in event["data"]
    assert event["id"] == "test-cor_thread.message.delta_1"
    assert event["retry"] == service_config.sse_retry_interval


@pytest.mark.asyncio
async def test_sse_handler_multiple_events(mock_correlation_id, service_config):
    """Test handling multiple events in sequence."""
    events = []
    for i, event_type in enumerate(["thread.run.created", "thread.message.created", "thread.run.completed"]):
        mock_event = MagicMock()
        mock_event.event = event_type
        event_data = {"event": event_type, "index": i}
        mock_event.model_dump_json.return_value = json.dumps(event_data)
        mock_event.model_dump.return_value = event_data
        events.append(mock_event)

    orchestrator = MockOrchestrator(events)
    handler = SSEStreamHandler(orchestrator, service_config)

    formatted_events = []
    async for event in handler.format_events("thread-123", "test query", "127.0.0.1"):
        formatted_events.append(event)

    # Should have 4 events (3 regular + 1 metadata for completion)
    assert len(formatted_events) == 4

    # Check event sequence
    assert formatted_events[0]["event"] == "thread.run.created"
    assert formatted_events[1]["event"] == "thread.message.created"
    assert formatted_events[2]["event"] == "thread.run.completed"
    assert formatted_events[3]["event"] == "metadata"

    # Check event IDs are properly numbered with truncated correlation ID
    assert formatted_events[0]["id"] == "test-cor_thread.run.created_1"
    assert formatted_events[1]["id"] == "test-cor_thread.message.created_2"
    assert formatted_events[2]["id"] == "test-cor_thread.run.completed_3"


@pytest.mark.asyncio
async def test_sse_handler_empty_stream(mock_correlation_id, service_config):
    """Test handling of empty event stream."""
    orchestrator = MockOrchestrator([])
    handler = SSEStreamHandler(orchestrator, service_config)

    formatted_events = []
    async for event in handler.format_events("thread-123", "test query", "127.0.0.1"):
        formatted_events.append(event)

    assert len(formatted_events) == 0


def test_sse_handler_initialization(service_config):
    """Test SSE handler initialization with configuration."""
    orchestrator = MagicMock()
    handler = SSEStreamHandler(orchestrator, service_config)

    assert handler.orchestrator == orchestrator
    assert handler.config == service_config
    assert handler.heartbeat_interval == service_config.sse_heartbeat_interval
    assert handler.max_connection_duration == service_config.sse_max_connection_duration
    assert handler.retry_interval == service_config.sse_retry_interval
    assert handler.max_connections_per_client == service_config.sse_max_connections_per_client
    assert handler.active_connections == 0


@pytest.mark.asyncio
async def test_sse_handler_rate_limiting(mock_correlation_id, service_config):
    """Test rate limiting functionality."""

    # Create mock event that keeps connection alive briefly
    mock_event = MagicMock()
    mock_event.event = "thread.run.created"
    mock_event.model_dump_json.return_value = '{"event": "thread.run.created"}'
    mock_event.model_dump.return_value = {"event": "thread.run.created"}

    # Create orchestrator that yields event with small delay
    async def slow_stream(thread_id: str, human_query: str) -> AsyncGenerator[Any, None]:
        yield mock_event
        await asyncio.sleep(0.01)  # Keep connection alive

    orchestrator = MagicMock()
    orchestrator.process_run_stream = slow_stream

    # Set very low connection limit for testing
    service_config.sse_max_connections_per_client = 1
    handler = SSEStreamHandler(orchestrator, service_config)

    # Start first connection concurrently
    async def first_connection():
        formatted_events = []
        async for event in handler.format_events("thread-123", "test query", "127.0.0.1"):
            formatted_events.append(event)
        return formatted_events

    # Start second connection concurrently
    async def second_connection():
        # Small delay to let first connection establish
        await asyncio.sleep(0.005)
        formatted_events = []
        async for event in handler.format_events("thread-123", "test query", "127.0.0.1"):
            formatted_events.append(event)
            break  # Only get first event (rate limit error)
        return formatted_events

    # Run both connections concurrently
    first_events, second_events = await asyncio.gather(first_connection(), second_connection())

    # First connection should succeed and get the event
    assert len(first_events) == 1
    assert first_events[0]["event"] == "thread.run.created"

    # Second connection should be rate limited
    assert len(second_events) == 1
    assert second_events[0]["event"] == "error"
    error_data = json.loads(second_events[0]["data"])
    assert error_data["error"] == "Rate limit exceeded"
    assert error_data["error_type"] == "RateLimitError"


@pytest.mark.asyncio
async def test_sse_handler_connection_timeout(mock_correlation_id, service_config):
    """Test connection timeout functionality."""

    # Create orchestrator that yields events slowly
    async def slow_events():
        while True:
            mock_event = MagicMock()
            mock_event.event = "thread.run.created"
            mock_event.model_dump_json.return_value = '{"event": "thread.run.created"}'
            mock_event.model_dump.return_value = {"event": "thread.run.created"}
            yield mock_event
            await asyncio.sleep(0.1)

    orchestrator = MagicMock()
    orchestrator.process_run_stream = MagicMock(return_value=slow_events())

    # Set very short connection timeout for testing
    service_config.sse_max_connection_duration = 0.05
    handler = SSEStreamHandler(orchestrator, service_config)

    formatted_events = []
    timeout_reached = False

    async for event in handler.format_events("thread-123", "test query", "127.0.0.1"):
        formatted_events.append(event)
        if event.get("event") == "error" and "timeout" in event.get("id", ""):
            timeout_reached = True
            break
        # Safety limit
        if len(formatted_events) > 10:
            break

    assert timeout_reached
    timeout_event = [e for e in formatted_events if e.get("event") == "error" and "timeout" in e.get("id", "")]
    assert len(timeout_event) == 1

    error_data = json.loads(timeout_event[0]["data"])
    assert error_data["error"] == "Connection timeout reached"
    assert error_data["error_type"] == "ConnectionTimeoutError"


@pytest.mark.asyncio
async def test_sse_handler_correlation_id_truncation(mock_correlation_id, service_config):
    """Test that correlation IDs are properly truncated for security."""
    mock_event = MagicMock()
    mock_event.event = "thread.run.created"
    mock_event.model_dump_json.return_value = '{"event": "thread.run.created"}'
    mock_event.model_dump.return_value = {"event": "thread.run.created"}

    orchestrator = MockOrchestrator([mock_event])
    handler = SSEStreamHandler(orchestrator, service_config)

    formatted_events = []
    async for event in handler.format_events("thread-123", "test query", "127.0.0.1"):
        formatted_events.append(event)

    assert len(formatted_events) == 1
    # Full correlation ID is "test-correlation-id", truncated should be "test-cor" (8 chars)
    assert "test-cor" in formatted_events[0]["id"]
    assert "test-correlation-id" not in formatted_events[0]["id"]


@pytest.mark.asyncio
async def test_sse_handler_event_serialization_caching(mock_correlation_id, service_config):
    """Test that event serialization is cached for performance."""
    # Create identical events that should hit the cache
    mock_event1 = MagicMock()
    mock_event1.event = "thread.run.created"
    event_data = {"event": "thread.run.created", "data": "identical"}
    mock_event1.model_dump_json.return_value = json.dumps(event_data)
    mock_event1.model_dump.return_value = event_data

    mock_event2 = MagicMock()
    mock_event2.event = "thread.run.created"
    mock_event2.model_dump_json.return_value = json.dumps(event_data)
    mock_event2.model_dump.return_value = event_data

    orchestrator = MockOrchestrator([mock_event1, mock_event2])
    handler = SSEStreamHandler(orchestrator, service_config)

    formatted_events = []
    async for event in handler.format_events("thread-123", "test query", "127.0.0.1"):
        formatted_events.append(event)

    assert len(formatted_events) == 2
    # Both events should have the same serialized data (from cache)
    assert formatted_events[0]["data"] == formatted_events[1]["data"]
    # But different event IDs
    assert formatted_events[0]["id"] != formatted_events[1]["id"]
