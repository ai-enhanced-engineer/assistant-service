"""Tests for tool output error recovery functionality."""

import types
from unittest.mock import AsyncMock, Mock, patch

import pytest

from assistant_service.entities import AssistantConfig
from assistant_service.services.openai_orchestrator import OpenAIOrchestrator


def create_mock_tool_executor():
    """Create a mock tool executor for testing."""
    tool_executor = Mock()
    tool_executor.execute_tool = Mock(return_value={"tool_call_id": "test_call", "output": "test_output"})
    return tool_executor


@pytest.mark.asyncio
async def test_submit_tool_outputs_success():
    """Test successful tool output submission."""
    mock_client = AsyncMock()
    mock_client.beta.threads.runs.submit_tool_outputs.return_value = "success"

    tool_outputs = [{"tool_call_id": "123", "output": "result"}]

    config = AssistantConfig(assistant_id="test-assistant", assistant_name="Test Assistant", initial_message="Hello")
    orchestrator = OpenAIOrchestrator(mock_client, config, create_mock_tool_executor())

    result = await orchestrator._submit_tool_outputs_with_backoff("thread_123", "run_456", tool_outputs)

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

    config = AssistantConfig(assistant_id="test-assistant", assistant_name="Test Assistant", initial_message="Hello")
    orchestrator = OpenAIOrchestrator(mock_client, config, create_mock_tool_executor())

    result = await orchestrator._submit_tool_outputs_with_backoff("thread_123", "run_456", tool_outputs, retries=2)

    assert result == "success"
    assert mock_client.beta.threads.runs.submit_tool_outputs.call_count == 2


@pytest.mark.asyncio
async def test_submit_tool_outputs_permanent_failure():
    """Test tool output submission permanent failure."""
    mock_client = AsyncMock()
    mock_client.beta.threads.runs.submit_tool_outputs.side_effect = Exception("Permanent error")

    tool_outputs = [{"tool_call_id": "123", "output": "result"}]

    config = AssistantConfig(assistant_id="test-assistant", assistant_name="Test Assistant", initial_message="Hello")
    orchestrator = OpenAIOrchestrator(mock_client, config, create_mock_tool_executor())

    result = await orchestrator._submit_tool_outputs_with_backoff("thread_123", "run_456", tool_outputs, retries=2)

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

    config = AssistantConfig(assistant_id="test-assistant", assistant_name="Test Assistant", initial_message="Hello")
    orchestrator = OpenAIOrchestrator(mock_client, config, create_mock_tool_executor())

    result = await orchestrator._cancel_run_safely("thread_123", "run_456")

    assert result is True
    mock_client.beta.threads.runs.cancel.assert_called_once_with(thread_id="thread_123", run_id="run_456")


@pytest.mark.asyncio
async def test_cancel_run_safely_already_terminal():
    """Test canceling run that's already in terminal state."""
    mock_client = AsyncMock()

    # Mock run status as completed
    mock_run = types.SimpleNamespace(status="completed")
    mock_client.beta.threads.runs.retrieve.return_value = mock_run

    config = AssistantConfig(assistant_id="test-assistant", assistant_name="Test Assistant", initial_message="Hello")
    orchestrator = OpenAIOrchestrator(mock_client, config, create_mock_tool_executor())

    result = await orchestrator._cancel_run_safely("thread_123", "run_456")

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

    config = AssistantConfig(assistant_id="test-assistant", assistant_name="Test Assistant", initial_message="Hello")
    orchestrator = OpenAIOrchestrator(mock_client, config, create_mock_tool_executor())

    result = await orchestrator._cancel_run_safely("thread_123", "run_456")

    assert result is False


@pytest.mark.asyncio
async def test_iterate_run_events_tool_output_submission_failure(monkeypatch):
    """Test error recovery when tool output submission fails."""
    from assistant_service import repositories as repos
    from assistant_service.entities import AssistantConfig

    # Mock repositories
    monkeypatch.setenv("PROJECT_ID", "p")
    monkeypatch.setenv("BUCKET_ID", "b")
    monkeypatch.setenv("ASSISTANT_ID", "a")

    class DummySecretRepo:
        def __init__(self, project_id: str):
            pass

        def access_secret(self, _):
            return "sk"

    class DummyConfigRepo:
        def __init__(self, project_id: str, bucket_name: str):
            pass

        def read_config(self):
            return AssistantConfig(assistant_id="a", assistant_name="name", initial_message="hi")

    monkeypatch.setattr(repos, "GCPSecretRepository", DummySecretRepo)
    monkeypatch.setattr(repos, "GCPConfigRepository", DummyConfigRepo)

    from assistant_service.entities import ServiceConfig
    from assistant_service.server.main import AssistantEngineAPI

    # Create a test service config
    test_config = ServiceConfig(
        environment="development",
        project_id="p",
        bucket_id="b",
    )

    # Monkeypatch the client
    import openai

    monkeypatch.setattr(openai, "AsyncOpenAI", lambda api_key=None: AsyncMock())

    api = AssistantEngineAPI(service_config=test_config)
    mock_client = api.client

    # Mock failed tool output submission - use AsyncMock to properly return None
    mock_submit = AsyncMock(return_value=None)
    mock_cancel = AsyncMock(return_value=True)

    # Create a mock for the private methods on the run_processor instance
    with patch.object(api.orchestrator, "_submit_tool_outputs_with_backoff", mock_submit):
        with patch.object(api.orchestrator, "_cancel_run_safely", mock_cancel):
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

                # Requires action event - with proper structure
                required_action = types.SimpleNamespace(
                    type="submit_tool_outputs",
                    submit_tool_outputs=types.SimpleNamespace(tool_calls=[]),  # Empty since we already processed them
                )
                yield types.SimpleNamespace(
                    event="thread.run.requires_action",
                    data=types.SimpleNamespace(id="run_123", required_action=required_action),
                )

            # Mock event stream creation
            mock_client.beta = AsyncMock()
            mock_client.beta.threads = AsyncMock()
            mock_client.beta.threads.messages = AsyncMock()
            mock_client.beta.threads.runs = AsyncMock()
            mock_client.beta.threads.messages.create = AsyncMock(return_value=None)
            mock_client.beta.threads.runs.create = AsyncMock(return_value=mock_events())

            # Mock TOOL_MAP with test function by patching the tool_map on the instance
            test_tool_map = {"test_func": lambda param: "result"}
            original_tool_map = api.orchestrator.tool_executor.tool_map
            api.orchestrator.tool_executor.tool_map = test_tool_map

            try:
                events = []
                try:
                    async for event in api.orchestrator.iterate_run_events("thread_123", "test message"):
                        events.append(event)
                        # The function should break itself when error recovery triggers
                except StopAsyncIteration:
                    pass

                # Verify cancellation was called
                mock_cancel.assert_called_once_with("thread_123", "run_123")
            finally:
                # Restore original tool map
                api.orchestrator.tool_executor.tool_map = original_tool_map
