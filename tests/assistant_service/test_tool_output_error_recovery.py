"""Tests for tool output error recovery functionality."""

import types
from unittest.mock import AsyncMock, patch

import pytest

from assistant_service.openai_helpers import cancel_run_safely, submit_tool_outputs_with_backoff


@pytest.mark.asyncio
async def test_submit_tool_outputs_success():
    """Test successful tool output submission."""
    mock_client = AsyncMock()
    mock_client.beta.threads.runs.submit_tool_outputs.return_value = "success"

    tool_outputs = [{"tool_call_id": "123", "output": "result"}]

    result = await submit_tool_outputs_with_backoff(mock_client, "thread_123", "run_456", tool_outputs)

    assert result == "success"
    mock_client.beta.threads.runs.submit_tool_outputs.assert_called_once_with(
        thread_id="thread_123", run_id="run_456", tool_outputs=tool_outputs
    )


@pytest.mark.asyncio
async def test_submit_tool_outputs_retry_then_success():
    """Test tool output submission with retry logic."""
    mock_client = AsyncMock()
    # First call fails, second succeeds
    mock_client.beta.threads.runs.submit_tool_outputs.side_effect = [Exception("Network error"), "success"]

    tool_outputs = [{"tool_call_id": "123", "output": "result"}]

    result = await submit_tool_outputs_with_backoff(mock_client, "thread_123", "run_456", tool_outputs, retries=2)

    assert result == "success"
    assert mock_client.beta.threads.runs.submit_tool_outputs.call_count == 2


@pytest.mark.asyncio
async def test_submit_tool_outputs_permanent_failure():
    """Test tool output submission permanent failure."""
    mock_client = AsyncMock()
    mock_client.beta.threads.runs.submit_tool_outputs.side_effect = Exception("Permanent error")

    tool_outputs = [{"tool_call_id": "123", "output": "result"}]

    result = await submit_tool_outputs_with_backoff(mock_client, "thread_123", "run_456", tool_outputs, retries=2)

    assert result is None
    assert mock_client.beta.threads.runs.submit_tool_outputs.call_count == 2


@pytest.mark.asyncio
async def test_cancel_run_safely_success():
    """Test successful run cancellation."""
    mock_client = AsyncMock()

    # Mock run status as in_progress
    mock_run = types.SimpleNamespace(status="in_progress")
    mock_client.beta.threads.runs.retrieve.return_value = mock_run
    mock_client.beta.threads.runs.cancel.return_value = None

    result = await cancel_run_safely(mock_client, "thread_123", "run_456")

    assert result is True
    mock_client.beta.threads.runs.cancel.assert_called_once_with(thread_id="thread_123", run_id="run_456")


@pytest.mark.asyncio
async def test_cancel_run_safely_already_terminal():
    """Test canceling run that's already in terminal state."""
    mock_client = AsyncMock()

    # Mock run status as completed
    mock_run = types.SimpleNamespace(status="completed")
    mock_client.beta.threads.runs.retrieve.return_value = mock_run

    result = await cancel_run_safely(mock_client, "thread_123", "run_456")

    assert result is True
    # Should not attempt to cancel
    mock_client.beta.threads.runs.cancel.assert_not_called()


@pytest.mark.asyncio
async def test_cancel_run_safely_failure():
    """Test failed run cancellation."""
    mock_client = AsyncMock()

    # Mock run status as in_progress
    mock_run = types.SimpleNamespace(status="in_progress")
    mock_client.beta.threads.runs.retrieve.return_value = mock_run
    mock_client.beta.threads.runs.cancel.side_effect = Exception("Cancel failed")

    result = await cancel_run_safely(mock_client, "thread_123", "run_456")

    assert result is False


@pytest.mark.asyncio
async def test_iterate_run_events_tool_output_submission_failure(monkeypatch):
    """Test error recovery when tool output submission fails."""
    from assistant_service import repositories as repos
    from assistant_service.models import EngineAssistantConfig

    # Mock repositories
    monkeypatch.setenv("PROJECT_ID", "p")
    monkeypatch.setenv("BUCKET_ID", "b")
    monkeypatch.setenv("CLIENT_ID", "c")
    monkeypatch.setenv("ASSISTANT_ID", "a")

    class DummySecretRepo:
        def __init__(self, project_id: str, client_id: str):
            pass

        def access_secret(self, _):
            return "sk"

    class DummyConfigRepo:
        def __init__(self, client_id: str, project_id: str, bucket_name: str):
            pass

        def read_config(self):
            return EngineAssistantConfig(assistant_id="a", assistant_name="name", initial_message="hi")

    monkeypatch.setattr(repos, "GCPSecretRepository", DummySecretRepo)
    monkeypatch.setattr(repos, "GCPConfigRepository", DummyConfigRepo)

    # Also patch in the main module where they're imported
    import assistant_service.main as main_module

    monkeypatch.setattr(main_module, "GCPSecretRepository", DummySecretRepo)
    monkeypatch.setattr(main_module, "GCPConfigRepository", DummyConfigRepo)

    from assistant_service.main import AssistantEngineAPI

    api = AssistantEngineAPI()
    mock_client = AsyncMock()
    api.client = mock_client

    # Mock failed tool output submission
    with patch("assistant_service.main.submit_tool_outputs_with_backoff", return_value=None):
        with patch("assistant_service.main.cancel_run_safely", return_value=True) as mock_cancel:
            # Create mock events
            async def mock_events():
                # Run created event (to set run_id)
                yield types.SimpleNamespace(event="thread.run.created", data=types.SimpleNamespace(id="run_123"))

                # Tool call event
                tool_call = types.SimpleNamespace(
                    id="tool_123",
                    type="function",
                    function=types.SimpleNamespace(name="test_func", arguments='{"param": "value"}'),
                )
                step_details = types.SimpleNamespace(type="tool_calls", tool_calls=[tool_call])
                yield types.SimpleNamespace(
                    event="thread.run.step.completed", data=types.SimpleNamespace(step_details=step_details)
                )

                # Requires action event
                required_action = types.SimpleNamespace(type="submit_tool_outputs")
                yield types.SimpleNamespace(
                    event="thread.run.requires_action", data=types.SimpleNamespace(required_action=required_action)
                )

            # Mock event stream creation
            mock_client.beta.threads.messages.create.return_value = None
            mock_client.beta.threads.runs.create.return_value = mock_events()

            # Mock TOOL_MAP with test function
            with patch("assistant_service.main.TOOL_MAP", {"test_func": lambda param: "result"}):
                events = []
                try:
                    async for event in api._iterate_run_events("thread_123", "test message"):
                        events.append(event)
                        # The function should break itself when error recovery triggers
                except StopAsyncIteration:
                    pass

                # Verify cancellation was called
                mock_cancel.assert_called_once_with(mock_client, "thread_123", "run_123")
