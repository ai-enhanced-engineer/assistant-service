"""Unit tests for SSE streaming enhancements."""

import asyncio
import json
from typing import Any, AsyncGenerator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from assistant_service.entities import HEADER_CORRELATION_ID, SSE_RESPONSE_HEADERS
from assistant_service.entities.headers import SSE_HEARTBEAT_COMMENT
from assistant_service.server.main import AssistantEngineAPI


class MockEvent:
    """Mock event for testing."""

    def __init__(self, event_type: str, data: dict):
        self.event = event_type
        self._data = data

    def model_dump_json(self) -> str:
        return json.dumps(self._data)
        
    def model_dump(self) -> dict:
        return self._data


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator."""
    orchestrator = MagicMock()
    return orchestrator


@pytest.fixture
def api_with_mocks(mock_orchestrator, monkeypatch):
    """Create API instance with mocked dependencies."""
    # Set required environment variables
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("PROJECT_ID", "test-project")
    monkeypatch.setenv("BUCKET_ID", "test-bucket")

    # Create API instance
    api = AssistantEngineAPI()

    # Replace orchestrator with mock
    api.orchestrator = mock_orchestrator
    # Replace SSE stream handler's orchestrator with mock
    api.sse_stream_handler.orchestrator = mock_orchestrator

    return api


@pytest.mark.asyncio
async def test_sse_event_formatting_with_retry(api_with_mocks):
    """Test that SSE events include retry field."""
    api = api_with_mocks

    # Create mock event stream
    async def mock_stream(thread_id: str, message: str) -> AsyncGenerator[Any, None]:
        yield MockEvent("thread.run.created", {"id": "run_123"})
        yield MockEvent("thread.message.delta", {"delta": {"content": [{"type": "text", "text": {"value": "Hello"}}]}})
        yield MockEvent("thread.run.completed", {"status": "completed"})

    api.orchestrator.process_run_stream = mock_stream

    events = []
    async for event in api.sse_stream_handler.format_events("test_thread", "test_message", "127.0.0.1"):
        events.append(event)

    # Check that events have retry field
    assert len(events) == 4  # 3 events + 1 metadata
    for event in events[:-1]:  # All except metadata
        assert event.get("retry") == api.sse_stream_handler.retry_interval
        assert "event" in event
        assert "data" in event
        assert "id" in event


@pytest.mark.asyncio
async def test_sse_error_handling(api_with_mocks):
    """Test that errors are properly formatted as SSE events."""
    api = api_with_mocks

    # Create stream that raises error
    async def error_stream(thread_id: str, message: str) -> AsyncGenerator[Any, None]:
        yield MockEvent("thread.run.created", {"id": "run_123"})
        raise ValueError("Test error")

    api.orchestrator.process_run_stream = error_stream

    events = []
    async for event in api.sse_stream_handler.format_events("test_thread", "test_message", "127.0.0.1"):
        events.append(event)

    # Should have initial event and error event
    assert len(events) == 2
    assert events[0]["event"] == "thread.run.created"
    assert events[1]["event"] == "error"

    error_data = json.loads(events[1]["data"])
    assert error_data["error"] == "Test error"
    assert error_data["error_type"] == "ValueError"
    assert "correlation_id" in error_data
    assert "timestamp" in error_data


@pytest.mark.asyncio
async def test_sse_metadata_event(api_with_mocks):
    """Test that metadata event is sent after completion."""
    api = api_with_mocks

    # Create mock event stream
    async def mock_stream(thread_id: str, message: str) -> AsyncGenerator[Any, None]:
        yield MockEvent("thread.run.created", {"id": "run_123"})
        yield MockEvent("thread.message.delta", {"delta": {"content": [{"type": "text", "text": {"value": "Hello"}}]}})
        yield MockEvent("thread.run.completed", {"status": "completed"})

    api.orchestrator.process_run_stream = mock_stream

    events = []
    async for event in api.sse_stream_handler.format_events("test_thread", "test_message", "127.0.0.1"):
        events.append(event)

    # Find metadata event
    metadata_events = [e for e in events if e.get("event") == "metadata"]
    assert len(metadata_events) == 1

    metadata = json.loads(metadata_events[0]["data"])
    assert "correlation_id" in metadata
    assert "elapsed_time_seconds" in metadata
    assert "timestamp" in metadata
    assert metadata["event_count"] == 3
    assert metadata["thread_id"] == "test_thread"


@pytest.mark.asyncio
async def test_sse_heartbeat_mechanism(api_with_mocks):
    """Test that heartbeat comments are sent during long streams."""
    api = api_with_mocks

    # Create slow stream to trigger heartbeat
    async def slow_stream(thread_id: str, message: str) -> AsyncGenerator[Any, None]:
        yield MockEvent("thread.run.created", {"id": "run_123"})
        # This would trigger heartbeat in real scenario, but we'll mock time
        yield MockEvent("thread.run.completed", {"status": "completed"})

    api.orchestrator.process_run_stream = slow_stream

    events = []
    # Mock time to simulate heartbeat interval
    with patch("time.time") as mock_time:
        # Start time
        mock_time.return_value = 0

        event_generator = api.sse_stream_handler.format_events("test_thread", "test_message", "127.0.0.1")

        # First event
        event = await event_generator.__anext__()
        events.append(event)

        # Advance time to trigger heartbeat
        mock_time.return_value = 20  # More than default 15 seconds

        # Next event should include heartbeat
        async for event in event_generator:
            events.append(event)

    # Check for heartbeat comment
    heartbeat_events = [e for e in events if e.get("comment") == SSE_HEARTBEAT_COMMENT]
    assert len(heartbeat_events) >= 1
    assert heartbeat_events[0]["retry"] == api.sse_stream_handler.retry_interval


@pytest.mark.asyncio
async def test_sse_event_id_format(api_with_mocks):
    """Test that event IDs include truncated correlation ID and counter."""
    api = api_with_mocks

    # Create mock event stream
    async def mock_stream(thread_id: str, message: str) -> AsyncGenerator[Any, None]:
        yield MockEvent("thread.run.created", {"id": "run_123"})
        yield MockEvent("thread.message.delta", {"delta": {"content": [{"type": "text", "text": {"value": "Hello"}}]}})
        yield MockEvent("thread.run.completed", {"status": "completed"})

    api.orchestrator.process_run_stream = mock_stream

    events = []
    correlation_id = None

    with patch("assistant_service.services.sse_stream_handler.get_or_create_correlation_id") as mock_corr_id:
        mock_corr_id.return_value = "test-correlation-123"

        async for event in api.sse_stream_handler.format_events("test_thread", "test_message", "127.0.0.1"):
            events.append(event)
            if not correlation_id and "id" in event:
                # Extract correlation ID from first event
                correlation_id = event["id"].split("_")[0]

    # Verify event ID format uses truncated correlation ID (8 characters)
    truncated_id = "test-cor"  # First 8 characters of "test-correlation-123"
    assert events[0]["id"] == f"{truncated_id}_thread.run.created_1"
    assert events[1]["id"] == f"{truncated_id}_thread.message.delta_2"
    assert events[2]["id"] == f"{truncated_id}_thread.run.completed_3"


@pytest.mark.asyncio
async def test_sse_response_headers(api_with_mocks):
    """Test that SSE responses include proper headers."""
    api = api_with_mocks

    # Create mock event stream
    async def mock_stream(thread_id: str, message: str) -> AsyncGenerator[Any, None]:
        yield MockEvent("thread.run.created", {"id": "run_123"})
        yield MockEvent("thread.run.completed", {"status": "completed"})

    api.orchestrator.process_run_stream = mock_stream

    # Use TestClient to test the actual endpoint
    with TestClient(api.app) as client:
        # Need to use the streaming interface
        with client.stream(
            "POST",
            "/chat",
            json={"thread_id": "test_thread", "message": "Hello"},
            headers={"Accept": "text/event-stream"},
        ) as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

            # Verify all SSE response headers are present
            for header_name, expected_value in SSE_RESPONSE_HEADERS.items():
                assert response.headers[header_name.lower()] == expected_value.lower()

            # Verify correlation ID header is present
            assert HEADER_CORRELATION_ID.lower() in response.headers


@pytest.mark.asyncio
async def test_sse_handles_non_sse_events(api_with_mocks):
    """Test that non-SSE events are filtered out."""
    api = api_with_mocks

    # Create stream with mixed events
    async def mock_stream(thread_id: str, message: str) -> AsyncGenerator[Any, None]:
        yield MockEvent("thread.run.created", {"id": "run_123"})
        yield MockEvent("some.internal.event", {"internal": "data"})  # Should be filtered
        yield MockEvent("thread.run.completed", {"status": "completed"})

    api.orchestrator.process_run_stream = mock_stream

    events = []
    async for event in api.sse_stream_handler.format_events("test_thread", "test_message", "127.0.0.1"):
        if "event" in event:  # Skip heartbeats
            events.append(event)

    # Should only have SSE events and metadata
    event_types = [e["event"] for e in events]
    assert "some.internal.event" not in event_types
    assert "thread.run.created" in event_types
    assert "thread.run.completed" in event_types
    assert "metadata" in event_types


@pytest.mark.asyncio
async def test_sse_empty_stream(api_with_mocks):
    """Test handling of empty event stream."""
    api = api_with_mocks

    # Create empty stream
    async def empty_stream(thread_id: str, message: str) -> AsyncGenerator[Any, None]:
        return
        yield  # Make it a generator

    api.orchestrator.process_run_stream = empty_stream

    events = []
    async for event in api.sse_stream_handler.format_events("test_thread", "test_message", "127.0.0.1"):
        events.append(event)

    # Should have no events
    assert len(events) == 0


@pytest.mark.asyncio
async def test_sse_rate_limiting_integration(api_with_mocks):
    """Test rate limiting in SSE handler integration."""
    api = api_with_mocks

    # Set low connection limit for testing
    api.sse_stream_handler.max_connections_per_client = 1
    
    # Create mock event stream that doesn't immediately complete
    async def mock_stream(thread_id: str, message: str) -> AsyncGenerator[Any, None]:
        yield MockEvent("thread.run.created", {"id": "run_123"})
        # Add a small delay to keep connection alive
        await asyncio.sleep(0.01)

    api.orchestrator.process_run_stream = mock_stream

    # Start first connection concurrently
    async def first_connection():
        events = []
        async for event in api.sse_stream_handler.format_events("test_thread", "test_message", "127.0.0.1"):
            events.append(event)
        return events

    # Start second connection concurrently  
    async def second_connection():
        # Small delay to let first connection establish
        await asyncio.sleep(0.005)
        events = []
        async for event in api.sse_stream_handler.format_events("test_thread", "test_message", "127.0.0.1"):
            events.append(event)
            break  # Only need first event (should be rate limit error)
        return events

    # Run both connections concurrently
    first_events, second_events = await asyncio.gather(first_connection(), second_connection())
    
    # First connection should work normally
    assert len(first_events) == 1
    assert first_events[0]["event"] == "thread.run.created"

    # Second connection should be rate limited
    assert len(second_events) == 1
    assert second_events[0]["event"] == "error"
    error_data = json.loads(second_events[0]["data"])
    assert error_data["error"] == "Rate limit exceeded"


@pytest.mark.asyncio
async def test_sse_connection_timeout_integration(api_with_mocks):
    """Test connection timeout in SSE handler integration."""
    api = api_with_mocks

    # Set very short timeout for testing
    api.sse_stream_handler.max_connection_duration = 0.01
    
    # Create slow stream
    async def slow_stream(thread_id: str, message: str) -> AsyncGenerator[Any, None]:
        import asyncio
        yield MockEvent("thread.run.created", {"id": "run_123"})
        await asyncio.sleep(0.05)  # Longer than timeout
        yield MockEvent("thread.run.completed", {"status": "completed"})

    api.orchestrator.process_run_stream = slow_stream

    events = []
    async for event in api.sse_stream_handler.format_events("test_thread", "test_message", "127.0.0.1"):
        events.append(event)
        if event.get("event") == "error" and "timeout" in event.get("id", ""):
            break

    # Should have initial event and timeout error
    timeout_events = [e for e in events if e.get("event") == "error" and "timeout" in e.get("id", "")]
    assert len(timeout_events) == 1
    
    error_data = json.loads(timeout_events[0]["data"])
    assert error_data["error"] == "Connection timeout reached"
    assert error_data["error_type"] == "ConnectionTimeoutError"