"""Tests for SSE stream handler."""

import asyncio
import json
import time
from typing import Any, AsyncGenerator
from unittest.mock import MagicMock, patch

import pytest

from assistant_service.services.openai_orchestrator import IOrchestrator
from assistant_service.services.sse_stream_handler import SSEStreamHandler


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
def mock_correlation_id():
    """Mock correlation ID for consistent testing."""
    with patch("assistant_service.services.sse_stream_handler.get_or_create_correlation_id") as mock:
        mock.return_value = "test-correlation-id"
        yield mock


@pytest.mark.asyncio
async def test_sse_handler_filters_events(mock_correlation_id):
    """Test that SSE handler only passes through events in SSE_STREAM_EVENTS."""
    # Create mock events - some in SSE_STREAM_EVENTS, some not
    mock_event_in_set = MagicMock()
    mock_event_in_set.event = "thread.run.created"
    mock_event_in_set.model_dump_json.return_value = '{"event": "thread.run.created"}'

    mock_event_not_in_set = MagicMock()
    mock_event_not_in_set.event = "not.in.set"
    mock_event_not_in_set.model_dump_json.return_value = '{"event": "not.in.set"}'

    events = [mock_event_in_set, mock_event_not_in_set, mock_event_in_set]
    orchestrator = MockOrchestrator(events)
    handler = SSEStreamHandler(orchestrator)

    formatted_events = []
    async for event in handler.format_events("thread-123", "test query"):
        formatted_events.append(event)

    # Should only have 2 events (the ones in SSE_STREAM_EVENTS)
    assert len(formatted_events) == 2
    assert all(event.get("event") == "thread.run.created" for event in formatted_events)
    assert formatted_events[0]["id"] == "test-correlation-id_thread.run.created_1"
    assert formatted_events[1]["id"] == "test-correlation-id_thread.run.created_2"


@pytest.mark.asyncio
async def test_sse_handler_adds_metadata_on_completion(mock_correlation_id):
    """Test that metadata event is added when thread.run.completed is received."""
    mock_event = MagicMock()
    mock_event.event = "thread.run.completed"
    mock_event.model_dump_json.return_value = '{"event": "thread.run.completed"}'

    orchestrator = MockOrchestrator([mock_event])
    handler = SSEStreamHandler(orchestrator)

    formatted_events = []
    async for event in handler.format_events("thread-123", "test query"):
        formatted_events.append(event)

    assert len(formatted_events) == 2
    # First event should be the run completed event
    assert formatted_events[0]["event"] == "thread.run.completed"
    # Second event should be metadata
    assert formatted_events[1]["event"] == "metadata"

    metadata = json.loads(formatted_events[1]["data"])
    assert metadata["correlation_id"] == "test-correlation-id"
    assert metadata["thread_id"] == "thread-123"
    assert metadata["event_count"] == 1
    assert "elapsed_time_seconds" in metadata


@pytest.mark.asyncio
async def test_sse_handler_heartbeat_mechanism(mock_correlation_id):
    """Test that heartbeats are sent when no events come for a while."""

    # Create a slow event generator
    async def slow_events():
        mock_event = MagicMock()
        mock_event.event = "thread.run.created"
        mock_event.model_dump_json.return_value = '{"event": "thread.run.created"}'
        yield mock_event
        # Sleep longer than heartbeat interval
        await asyncio.sleep(0.1)  # Simulating delay
        yield mock_event

    orchestrator = MagicMock()
    orchestrator.process_run_stream = MagicMock(return_value=slow_events())

    handler = SSEStreamHandler(orchestrator)
    handler.heartbeat_interval = 0.05  # Set very short for testing

    formatted_events = []
    start_time = time.time()

    async for event in handler.format_events("thread-123", "test query"):
        formatted_events.append(event)
        # Stop after we get at least one heartbeat
        if any(e.get("comment") == "keepalive" for e in formatted_events):
            break
        # Safety timeout
        if time.time() - start_time > 1:
            break

    # Should have at least one heartbeat
    heartbeats = [e for e in formatted_events if e.get("comment") == "keepalive"]
    assert len(heartbeats) >= 1
    assert heartbeats[0]["retry"] == 5000


@pytest.mark.asyncio
async def test_sse_handler_error_handling(mock_correlation_id):
    """Test that errors are properly formatted as SSE error events."""

    # Create an orchestrator that raises an exception
    async def error_stream(thread_id: str, human_query: str):
        mock_event = MagicMock()
        mock_event.event = "thread.run.created"
        mock_event.model_dump_json.return_value = '{"event": "thread.run.created"}'
        yield mock_event
        raise RuntimeError("Test error")

    orchestrator = MagicMock()
    orchestrator.process_run_stream = error_stream

    handler = SSEStreamHandler(orchestrator)

    formatted_events = []
    async for event in handler.format_events("thread-123", "test query"):
        formatted_events.append(event)

    # Should have the successful event and an error event
    assert len(formatted_events) == 2
    assert formatted_events[0]["event"] == "thread.run.created"
    assert formatted_events[1]["event"] == "error"

    error_data = json.loads(formatted_events[1]["data"])
    assert error_data["error"] == "Test error"
    assert error_data["error_type"] == "RuntimeError"
    assert error_data["correlation_id"] == "test-correlation-id"


@pytest.mark.asyncio
async def test_sse_handler_event_formatting(mock_correlation_id):
    """Test that events are properly formatted with all required fields."""
    mock_event = MagicMock()
    mock_event.event = "thread.message.delta"
    mock_event.model_dump_json.return_value = '{"event": "thread.message.delta", "data": "test"}'

    orchestrator = MockOrchestrator([mock_event])
    handler = SSEStreamHandler(orchestrator)

    formatted_events = []
    async for event in handler.format_events("thread-123", "test query"):
        formatted_events.append(event)

    assert len(formatted_events) == 1
    event = formatted_events[0]

    # Check all required SSE fields
    assert event["event"] == "thread.message.delta"
    assert event["data"] == '{"event": "thread.message.delta", "data": "test"}'
    assert event["id"] == "test-correlation-id_thread.message.delta_1"
    assert event["retry"] == 5000


@pytest.mark.asyncio
async def test_sse_handler_multiple_events(mock_correlation_id):
    """Test handling multiple events in sequence."""
    events = []
    for i, event_type in enumerate(["thread.run.created", "thread.message.created", "thread.run.completed"]):
        mock_event = MagicMock()
        mock_event.event = event_type
        mock_event.model_dump_json.return_value = json.dumps({"event": event_type, "index": i})
        events.append(mock_event)

    orchestrator = MockOrchestrator(events)
    handler = SSEStreamHandler(orchestrator)

    formatted_events = []
    async for event in handler.format_events("thread-123", "test query"):
        formatted_events.append(event)

    # Should have 4 events (3 regular + 1 metadata for completion)
    assert len(formatted_events) == 4

    # Check event sequence
    assert formatted_events[0]["event"] == "thread.run.created"
    assert formatted_events[1]["event"] == "thread.message.created"
    assert formatted_events[2]["event"] == "thread.run.completed"
    assert formatted_events[3]["event"] == "metadata"

    # Check event IDs are properly numbered
    assert formatted_events[0]["id"] == "test-correlation-id_thread.run.created_1"
    assert formatted_events[1]["id"] == "test-correlation-id_thread.message.created_2"
    assert formatted_events[2]["id"] == "test-correlation-id_thread.run.completed_3"


@pytest.mark.asyncio
async def test_sse_handler_empty_stream(mock_correlation_id):
    """Test handling of empty event stream."""
    orchestrator = MockOrchestrator([])
    handler = SSEStreamHandler(orchestrator)

    formatted_events = []
    async for event in handler.format_events("thread-123", "test query"):
        formatted_events.append(event)

    assert len(formatted_events) == 0


def test_sse_handler_initialization():
    """Test SSE handler initialization."""
    orchestrator = MagicMock()
    handler = SSEStreamHandler(orchestrator)

    assert handler.orchestrator == orchestrator
    assert handler.heartbeat_interval == 15  # Default value
