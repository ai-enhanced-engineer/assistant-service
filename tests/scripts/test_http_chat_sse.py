"""Unit tests for SSE handling in HTTP chat client."""

import json

# Import the function we're testing
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from httpx_sse import ServerSentEvent

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.conversation.http_chat import process_sse_with_httpx_sse


class MockSSEResponse:
    """Mock SSE response for testing."""

    def __init__(self, events):
        self.events = events
        self.index = 0

    async def aiter_sse(self):
        """Async iterator for SSE events."""
        for event in self.events:
            yield event


@pytest.mark.asyncio
async def test_process_message_delta_events():
    """Test processing of message delta events."""
    # Create mock SSE events
    events = [
        ServerSentEvent(
            event="thread.message.delta",
            data=json.dumps({"data": {"delta": {"content": [{"type": "text", "text": {"value": "Hello"}}]}}}),
        ),
        ServerSentEvent(
            event="thread.message.delta",
            data=json.dumps({"data": {"delta": {"content": [{"type": "text", "text": {"value": " world!"}}]}}}),
        ),
        ServerSentEvent(event="thread.run.completed", data=json.dumps({"status": "completed"})),
    ]

    mock_client = AsyncMock()

    # Mock the aconnect_sse context manager
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_aconnect_sse(*args, **kwargs):
        yield MockSSEResponse(events)

    with patch("scripts.conversation.http_chat.aconnect_sse", mock_aconnect_sse):
        result = await process_sse_with_httpx_sse(
            mock_client, "http://test.com/chat", {"thread_id": "test", "message": "test"}
        )

    assert result == "Hello world!"


@pytest.mark.asyncio
async def test_process_metadata_event():
    """Test processing of metadata events."""
    printed_output = []

    def mock_print(*args, **kwargs):
        printed_output.append(args[0] if args else "")

    events = [
        ServerSentEvent(
            event="thread.message.delta",
            data=json.dumps({"data": {"delta": {"content": [{"type": "text", "text": {"value": "Response"}}]}}}),
        ),
        ServerSentEvent(
            event="metadata",
            data=json.dumps({"correlation_id": "test-123", "elapsed_time_seconds": 2.5, "event_count": 5}),
        ),
        ServerSentEvent(event="thread.run.completed", data=json.dumps({"status": "completed"})),
    ]

    mock_client = AsyncMock()

    # Mock the aconnect_sse context manager
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_aconnect_sse(*args, **kwargs):
        yield MockSSEResponse(events)

    with patch("scripts.conversation.http_chat.aconnect_sse", mock_aconnect_sse):
        with patch("builtins.print", side_effect=mock_print):
            await process_sse_with_httpx_sse(
                mock_client, "http://test.com/chat", {"thread_id": "test", "message": "test"}
            )

    # Check that timing info was printed
    assert any("[Completed in 2.50s]" in output for output in printed_output)


@pytest.mark.asyncio
async def test_process_error_event():
    """Test processing of error events."""
    printed_output = []

    def mock_print(*args, **kwargs):
        printed_output.append(args[0] if args else "")

    events = [
        ServerSentEvent(event="thread.run.created", data=json.dumps({"id": "run_123"})),
        ServerSentEvent(
            event="error",
            data=json.dumps(
                {"error": "Something went wrong", "error_type": "RuntimeError", "correlation_id": "test-123"}
            ),
        ),
    ]

    mock_client = AsyncMock()

    # Mock the aconnect_sse context manager
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_aconnect_sse(*args, **kwargs):
        yield MockSSEResponse(events)

    with patch("scripts.conversation.http_chat.aconnect_sse", mock_aconnect_sse):
        with patch("builtins.print", side_effect=mock_print):
            await process_sse_with_httpx_sse(
                mock_client, "http://test.com/chat", {"thread_id": "test", "message": "test"}
            )

    # Check that error was printed
    assert any("[Error: Something went wrong]" in output for output in printed_output)


@pytest.mark.asyncio
async def test_handle_run_failed_event():
    """Test handling of run failed events."""
    printed_output = []

    def mock_print(*args, **kwargs):
        printed_output.append(args[0] if args else "")

    events = [
        ServerSentEvent(event="thread.run.failed", data=json.dumps({"error": {"message": "Assistant run failed"}}))
    ]

    mock_client = AsyncMock()

    # Mock the aconnect_sse context manager
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_aconnect_sse(*args, **kwargs):
        yield MockSSEResponse(events)

    with patch("scripts.conversation.http_chat.aconnect_sse", mock_aconnect_sse):
        with patch("builtins.print", side_effect=mock_print):
            await process_sse_with_httpx_sse(
                mock_client, "http://test.com/chat", {"thread_id": "test", "message": "test"}
            )

    # Check that error was printed
    assert any("[Error: Run failed]" in output for output in printed_output)


@pytest.mark.asyncio
async def test_handle_json_decode_error():
    """Test handling of JSON decode errors."""
    events = [
        ServerSentEvent(event="thread.message.delta", data="invalid json"),
        ServerSentEvent(event="thread.run.completed", data=json.dumps({"status": "completed"})),
    ]

    mock_client = AsyncMock()

    # Mock the aconnect_sse context manager
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_aconnect_sse(*args, **kwargs):
        yield MockSSEResponse(events)

    with patch("scripts.conversation.http_chat.aconnect_sse", mock_aconnect_sse):
        # Should not raise, just log error and continue
        result = await process_sse_with_httpx_sse(
            mock_client, "http://test.com/chat", {"thread_id": "test", "message": "test"}
        )

    # Should return empty string since no valid content was processed
    assert result == ""


@pytest.mark.asyncio
async def test_process_mixed_content_types():
    """Test processing of mixed content types in delta events."""
    events = [
        ServerSentEvent(
            event="thread.message.delta",
            data=json.dumps(
                {
                    "data": {
                        "delta": {
                            "content": [
                                {"type": "text", "text": {"value": "Text content"}},
                                {"type": "image", "image": {"url": "http://example.com/image.png"}},
                                {"type": "text", "text": {"value": " more text"}},
                            ]
                        }
                    }
                }
            ),
        ),
        ServerSentEvent(event="thread.run.completed", data=json.dumps({"status": "completed"})),
    ]

    mock_client = AsyncMock()

    # Mock the aconnect_sse context manager
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_aconnect_sse(*args, **kwargs):
        yield MockSSEResponse(events)

    with patch("scripts.conversation.http_chat.aconnect_sse", mock_aconnect_sse):
        result = await process_sse_with_httpx_sse(
            mock_client, "http://test.com/chat", {"thread_id": "test", "message": "test"}
        )

    # Should only include text content
    assert result == "Text content more text"
