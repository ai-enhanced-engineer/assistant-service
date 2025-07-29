from unittest.mock import AsyncMock

import pytest

from assistant_service.entities import EngineAssistantConfig
from assistant_service.processors.openai_orchestrator import OpenAIOrchestrator


@pytest.mark.asyncio
async def test_retrieve_run_returns_none_on_error():
    """Test that _retrieve_run returns None on error."""
    mock_client = AsyncMock()
    mock_client.beta.threads.runs.retrieve.side_effect = RuntimeError("boom")

    config = EngineAssistantConfig(
        assistant_id="test-assistant", assistant_name="Test Assistant", initial_message="Hello"
    )
    orchestrator = OpenAIOrchestrator(mock_client, config)

    result = await orchestrator._retrieve_run("t", "r")
    assert result is None
    mock_client.beta.threads.runs.retrieve.assert_called_once_with(thread_id="t", run_id="r")


@pytest.mark.asyncio
async def test_list_run_steps_returns_none_on_error():
    """Test that _list_run_steps returns None on error."""
    mock_client = AsyncMock()
    mock_client.beta.threads.runs.steps.list.side_effect = RuntimeError("boom")

    config = EngineAssistantConfig(
        assistant_id="test-assistant", assistant_name="Test Assistant", initial_message="Hello"
    )
    orchestrator = OpenAIOrchestrator(mock_client, config)

    result = await orchestrator._list_run_steps("t", "r")
    assert result is None
    mock_client.beta.threads.runs.steps.list.assert_called_once_with(thread_id="t", run_id="r", order="asc")


@pytest.mark.asyncio
async def test_submit_tool_outputs_retries():
    """Test that _submit_tool_outputs_with_backoff retries on failure."""
    mock_client = AsyncMock()
    # First call fails, second succeeds
    mock_client.beta.threads.runs.submit_tool_outputs.side_effect = [RuntimeError("fail"), "ok"]

    config = EngineAssistantConfig(
        assistant_id="test-assistant", assistant_name="Test Assistant", initial_message="Hello"
    )
    orchestrator = OpenAIOrchestrator(mock_client, config)

    result = await orchestrator._submit_tool_outputs_with_backoff("t", "r", [])
    assert result == "ok"
    assert mock_client.beta.threads.runs.submit_tool_outputs.call_count == 2


@pytest.mark.asyncio
async def test_submit_tool_outputs_returns_none_after_retries():
    """Test that _submit_tool_outputs_with_backoff returns None after all retries fail."""
    mock_client = AsyncMock()
    mock_client.beta.threads.runs.submit_tool_outputs.side_effect = RuntimeError("fail")

    config = EngineAssistantConfig(
        assistant_id="test-assistant", assistant_name="Test Assistant", initial_message="Hello"
    )
    orchestrator = OpenAIOrchestrator(mock_client, config)

    result = await orchestrator._submit_tool_outputs_with_backoff("t", "r", [], retries=2)
    assert result is None
    assert mock_client.beta.threads.runs.submit_tool_outputs.call_count == 2


@pytest.mark.asyncio
async def test_cancel_run_safely_success():
    """Test successful run cancellation."""
    mock_client = AsyncMock()
    mock_run = AsyncMock()
    mock_run.status = "in_progress"
    mock_client.beta.threads.runs.retrieve.return_value = mock_run
    mock_client.beta.threads.runs.cancel.return_value = None

    config = EngineAssistantConfig(
        assistant_id="test-assistant", assistant_name="Test Assistant", initial_message="Hello"
    )
    orchestrator = OpenAIOrchestrator(mock_client, config)

    result = await orchestrator._cancel_run_safely("thread_123", "run_456")
    assert result is True
    mock_client.beta.threads.runs.cancel.assert_called_once_with(thread_id="thread_123", run_id="run_456")


@pytest.mark.asyncio
async def test_cancel_run_safely_already_terminal():
    """Test canceling run that's already in terminal state."""
    mock_client = AsyncMock()
    mock_run = AsyncMock()
    mock_run.status = "completed"
    mock_client.beta.threads.runs.retrieve.return_value = mock_run

    config = EngineAssistantConfig(
        assistant_id="test-assistant", assistant_name="Test Assistant", initial_message="Hello"
    )
    orchestrator = OpenAIOrchestrator(mock_client, config)

    result = await orchestrator._cancel_run_safely("thread_123", "run_456")
    assert result is True
    # Should not attempt to cancel
    mock_client.beta.threads.runs.cancel.assert_not_called()


@pytest.mark.asyncio
async def test_cancel_run_safely_failure():
    """Test failed run cancellation."""
    mock_client = AsyncMock()
    mock_run = AsyncMock()
    mock_run.status = "in_progress"
    mock_client.beta.threads.runs.retrieve.return_value = mock_run
    mock_client.beta.threads.runs.cancel.side_effect = Exception("Cancel failed")

    config = EngineAssistantConfig(
        assistant_id="test-assistant", assistant_name="Test Assistant", initial_message="Hello"
    )
    orchestrator = OpenAIOrchestrator(mock_client, config)

    result = await orchestrator._cancel_run_safely("thread_123", "run_456")
    assert result is False
