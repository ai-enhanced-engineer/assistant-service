"""Comprehensive unit tests for the OpenAI Orchestrator."""

import types
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException
from openai import OpenAIError

from ai_assistant_service.services.openai_orchestrator import OpenAIOrchestrator


@pytest.fixture
def mock_client():
    """Create a mock OpenAI client."""
    client = AsyncMock()
    client.beta = AsyncMock()
    client.beta.threads = AsyncMock()
    client.beta.threads.messages = AsyncMock()
    client.beta.threads.runs = AsyncMock()
    client.beta.threads.runs.steps = AsyncMock()
    return client


@pytest.fixture
def mock_tool_executor():
    """Create a mock tool executor."""
    tool_executor = Mock()
    tool_executor.execute_tool = Mock(return_value={"tool_call_id": "test_call", "output": "test_output"})
    return tool_executor


@pytest.fixture
def orchestrator(mock_client, test_engine_config, mock_tool_executor):
    """Create a Run processor instance."""
    return OpenAIOrchestrator(mock_client, test_engine_config, mock_tool_executor)


class TestCreateMessage:
    """Test cases for create_message method."""

    @pytest.mark.asyncio
    async def test_create_message_success(self, orchestrator, mock_client):
        """Test successful message creation."""
        mock_client.beta.threads.messages.create.return_value = None

        await orchestrator.create_message("thread123", "Hello world")

        mock_client.beta.threads.messages.create.assert_called_once_with(
            thread_id="thread123", role="user", content="Hello world"
        )

    @pytest.mark.asyncio
    async def test_create_message_openai_error(self, orchestrator, mock_client):
        """Test message creation with OpenAI error."""
        mock_client.beta.threads.messages.create.side_effect = OpenAIError("API error")

        with pytest.raises(HTTPException) as exc_info:
            await orchestrator.create_message("thread123", "Hello world")

        assert exc_info.value.status_code == 502
        assert "Failed to create message" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_message_unexpected_error(self, orchestrator, mock_client):
        """Test message creation with unexpected error."""
        mock_client.beta.threads.messages.create.side_effect = RuntimeError("Unexpected")

        with pytest.raises(HTTPException) as exc_info:
            await orchestrator.create_message("thread123", "Hello world")

        assert exc_info.value.status_code == 500
        assert "Internal server error" in exc_info.value.detail


class TestCreateRunStream:
    """Test cases for create_run_stream method."""

    @pytest.mark.asyncio
    async def test_create_run_stream_success(self, orchestrator, mock_client, test_engine_config):
        """Test successful run stream creation."""
        mock_stream = AsyncMock()
        mock_client.beta.threads.runs.create.return_value = mock_stream

        result = await orchestrator.create_run_stream("thread123")

        assert result == mock_stream
        mock_client.beta.threads.runs.create.assert_called_once_with(
            thread_id="thread123", assistant_id=test_engine_config.assistant_id, stream=True
        )

    @pytest.mark.asyncio
    async def test_create_run_stream_openai_error(self, orchestrator, mock_client):
        """Test run stream creation with OpenAI error."""
        mock_client.beta.threads.runs.create.side_effect = OpenAIError("API error")

        with pytest.raises(HTTPException) as exc_info:
            await orchestrator.create_run_stream("thread123")

        assert exc_info.value.status_code == 502
        assert "Failed to create run" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_run_stream_unexpected_error(self, orchestrator, mock_client):
        """Test run stream creation with unexpected error."""
        mock_client.beta.threads.runs.create.side_effect = RuntimeError("Unexpected")

        with pytest.raises(HTTPException) as exc_info:
            await orchestrator.create_run_stream("thread123")

        assert exc_info.value.status_code == 500
        assert "Internal server error" in exc_info.value.detail


class TestProcessToolCalls:
    """Test cases for process_tool_calls method."""

    @pytest.mark.asyncio
    async def test_process_tool_calls_function_type(self, orchestrator):
        """Test processing function type tool calls."""
        # Mock the tool executor
        orchestrator.tool_executor.execute_tool = Mock(return_value={"tool_call_id": "call1", "output": "result"})

        tool_call = types.SimpleNamespace(
            id="call1",
            type="function",
            function=types.SimpleNamespace(name="test_func", arguments='{"param": "value"}'),
        )

        context = {"thread_id": "thread123", "run_id": "run123"}
        result = await orchestrator.process_tool_calls([tool_call], context)

        assert result == {"call1": {"tool_call_id": "call1", "output": "result"}}
        orchestrator.tool_executor.execute_tool.assert_called_once_with(
            tool_name="test_func",
            tool_args='{"param": "value"}',
            context={"thread_id": "thread123", "run_id": "run123", "tool_call_id": "call1"},
        )

    @pytest.mark.asyncio
    async def test_process_tool_calls_code_interpreter_type(self, orchestrator):
        """Test processing code_interpreter type tool calls."""
        tool_call = types.SimpleNamespace(id="call2", type="code_interpreter")

        context = {"thread_id": "thread123", "run_id": "run123"}
        result = await orchestrator.process_tool_calls([tool_call], context)

        assert result == {"call2": {"tool_call_id": "call2", "output": "code_interpreter"}}

    @pytest.mark.asyncio
    async def test_process_tool_calls_retrieval_type(self, orchestrator):
        """Test processing retrieval type tool calls."""
        tool_call = types.SimpleNamespace(id="call3", type="retrieval")

        context = {"thread_id": "thread123", "run_id": "run123"}
        result = await orchestrator.process_tool_calls([tool_call], context)

        assert result == {"call3": {"tool_call_id": "call3", "output": "retrieval"}}

    @pytest.mark.asyncio
    async def test_process_tool_calls_multiple_types(self, orchestrator):
        """Test processing multiple tool calls of different types."""
        orchestrator.tool_executor.execute_tool = Mock(return_value={"tool_call_id": "call1", "output": "func_result"})

        tool_calls = [
            types.SimpleNamespace(
                id="call1",
                type="function",
                function=types.SimpleNamespace(name="func1", arguments="{}"),
            ),
            types.SimpleNamespace(id="call2", type="code_interpreter"),
            types.SimpleNamespace(id="call3", type="retrieval"),
        ]

        context = {"thread_id": "thread123", "run_id": "run123"}
        result = await orchestrator.process_tool_calls(tool_calls, context)

        assert len(result) == 3
        assert result["call1"]["output"] == "func_result"
        assert result["call2"]["output"] == "code_interpreter"
        assert result["call3"]["output"] == "retrieval"


class TestIterateRunEvents:
    """Test cases for iterate_run_events method."""

    @pytest.mark.asyncio
    async def test_iterate_run_events_complete_flow(self, orchestrator, mock_client):
        """Test complete flow of iterating run events."""
        # Mock message creation
        mock_client.beta.threads.messages.create.return_value = None

        # Mock stream events
        async def mock_event_stream():
            yield types.SimpleNamespace(event="thread.run.created", data=types.SimpleNamespace(id="run123"))
            yield types.SimpleNamespace(
                event="thread.run.step.completed",
                data=types.SimpleNamespace(
                    step_details=types.SimpleNamespace(
                        type="message_creation",
                        message_creation=types.SimpleNamespace(message_id="msg123"),
                    )
                ),
            )
            yield types.SimpleNamespace(event="thread.run.completed", data=types.SimpleNamespace())

        mock_client.beta.threads.runs.create.return_value = mock_event_stream()

        events = []
        async for event in orchestrator.iterate_run_events("thread123", "Hello"):
            events.append(event)

        assert len(events) == 3
        assert events[0].event == "thread.run.created"
        assert events[1].event == "thread.run.step.completed"
        assert events[2].event == "thread.run.completed"

    @pytest.mark.asyncio
    async def test_iterate_run_events_tool_submission_failure(self, orchestrator, mock_client):
        """Test error recovery when tool output submission fails."""
        # Mock message creation
        mock_client.beta.threads.messages.create.return_value = None

        # Mock the private methods
        orchestrator._submit_tool_outputs_with_backoff = AsyncMock(return_value=None)
        orchestrator._cancel_run_safely = AsyncMock(return_value=True)

        # Mock tool executor
        orchestrator.tool_executor.execute_tool = Mock(return_value={"tool_call_id": "call1", "output": "result"})

        # Mock stream events
        async def mock_event_stream():
            yield types.SimpleNamespace(event="thread.run.created", data=types.SimpleNamespace(id="run123"))
            yield types.SimpleNamespace(
                event="thread.run.step.completed",
                data=types.SimpleNamespace(
                    step_details=types.SimpleNamespace(
                        type="tool_calls",
                        tool_calls=[
                            types.SimpleNamespace(
                                id="call1",
                                type="function",
                                function=types.SimpleNamespace(name="func", arguments="{}"),
                            )
                        ],
                    )
                ),
            )
            yield types.SimpleNamespace(
                event="thread.run.requires_action",
                data=types.SimpleNamespace(
                    id="run123",
                    required_action=types.SimpleNamespace(
                        type="submit_tool_outputs",
                        submit_tool_outputs=types.SimpleNamespace(tool_calls=[]),
                    ),
                ),
            )

        mock_client.beta.threads.runs.create.return_value = mock_event_stream()

        events = []
        async for event in orchestrator.iterate_run_events("thread123", "Hello"):
            events.append(event)

        # Verify submission was attempted and cancellation was called
        orchestrator._submit_tool_outputs_with_backoff.assert_called_once()
        orchestrator._cancel_run_safely.assert_called_once_with("thread123", "run123")


class TestProcessRun:
    """Test cases for process_run method."""

    @pytest.mark.asyncio
    async def test_process_run_success(self, orchestrator, mock_client):
        """Test successful run processing."""
        # Mock message creation
        mock_client.beta.threads.messages.create.return_value = None

        # Mock message retrieval
        mock_message = types.SimpleNamespace(
            content=[types.SimpleNamespace(text=types.SimpleNamespace(value="Assistant response"))]
        )
        mock_client.beta.threads.messages.retrieve.return_value = mock_message

        # Mock stream events
        async def mock_event_stream():
            yield types.SimpleNamespace(event="thread.run.created", data=types.SimpleNamespace(id="run123"))
            yield types.SimpleNamespace(
                event="thread.run.step.completed",
                data=types.SimpleNamespace(
                    step_details=types.SimpleNamespace(
                        type="message_creation",
                        message_creation=types.SimpleNamespace(message_id="msg123"),
                    )
                ),
            )

        mock_client.beta.threads.runs.create.return_value = mock_event_stream()

        result = await orchestrator.process_run("thread123", "Hello")

        assert result == ["Assistant response"]
        mock_client.beta.threads.messages.retrieve.assert_called_once_with(thread_id="thread123", message_id="msg123")

    @pytest.mark.asyncio
    async def test_process_run_message_retrieval_error(self, orchestrator, mock_client):
        """Test run processing with message retrieval error."""
        # Mock message creation
        mock_client.beta.threads.messages.create.return_value = None

        # Mock message retrieval error
        mock_client.beta.threads.messages.retrieve.side_effect = OpenAIError("Retrieval failed")

        # Mock stream events
        async def mock_event_stream():
            yield types.SimpleNamespace(event="thread.run.created", data=types.SimpleNamespace(id="run123"))
            yield types.SimpleNamespace(
                event="thread.run.step.completed",
                data=types.SimpleNamespace(
                    step_details=types.SimpleNamespace(
                        type="message_creation",
                        message_creation=types.SimpleNamespace(message_id="msg123"),
                    )
                ),
            )

        mock_client.beta.threads.runs.create.return_value = mock_event_stream()

        with pytest.raises(HTTPException) as exc_info:
            await orchestrator.process_run("thread123", "Hello")

        assert exc_info.value.status_code == 502
        assert "Failed to retrieve message" in exc_info.value.detail


class TestProcessRunStream:
    """Test cases for process_run_stream method."""

    @pytest.mark.asyncio
    async def test_process_run_stream_yields_events(self, orchestrator, mock_client):
        """Test that process_run_stream yields all events."""
        # Mock message creation
        mock_client.beta.threads.messages.create.return_value = None

        # Mock stream events
        async def mock_event_stream():
            yield types.SimpleNamespace(event="event1", data=types.SimpleNamespace())
            yield types.SimpleNamespace(event="event2", data=types.SimpleNamespace())
            yield types.SimpleNamespace(event="event3", data=types.SimpleNamespace())

        mock_client.beta.threads.runs.create.return_value = mock_event_stream()

        events = []
        async for event in orchestrator.process_run_stream("thread123", "Hello"):
            events.append(event)

        assert len(events) == 3
        assert [e.event for e in events] == ["event1", "event2", "event3"]
