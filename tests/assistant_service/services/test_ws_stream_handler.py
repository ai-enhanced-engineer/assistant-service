"""Comprehensive unit tests for the WebSocketStreamHandler."""

import json
import types
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.websockets import WebSocketDisconnect
from openai import OpenAIError


class TestHandleConnection:
    """Test cases for handle_connection method."""

    @pytest.mark.asyncio
    async def test_handle_connection_accept_failure(self, websocket_handler, mock_websocket):
        """Test handling connection when accept fails."""
        mock_websocket.accept.side_effect = Exception("Accept failed")

        await websocket_handler.handle_connection(mock_websocket)

        mock_websocket.accept.assert_called_once()
        # Should not close since accept failed
        mock_websocket.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_connection_client_disconnect(self, websocket_handler, mock_websocket, mock_orchestrator):
        """Test handling client disconnect during message loop."""
        mock_websocket.receive_json.side_effect = WebSocketDisconnect()

        await websocket_handler.handle_connection(mock_websocket)

        mock_websocket.accept.assert_called_once()
        mock_websocket.close.assert_called_once()
        # Should not process any runs
        mock_orchestrator.process_run_stream.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_connection_critical_error(self, websocket_handler, mock_websocket):
        """Test handling critical error during connection."""
        # First call succeeds, second call raises error
        mock_websocket.receive_json.side_effect = [
            {"thread_id": "thread123", "message": "Hello"},
            Exception("Critical error"),
        ]

        # Mock run processor to return empty stream
        async def empty_stream(*args):
            # This must actually yield to be an async generator
            if False:  # Never reached but makes it a generator
                yield

        websocket_handler.orchestrator.process_run_stream = empty_stream

        await websocket_handler.handle_connection(mock_websocket)

        mock_websocket.accept.assert_called_once()
        mock_websocket.close.assert_called_once()


class TestReceiveRequest:
    """Test cases for _receive_request method."""

    @pytest.mark.asyncio
    async def test_receive_request_success(self, websocket_handler, mock_websocket):
        """Test successful request reception."""
        mock_websocket.receive_json.return_value = {"thread_id": "thread123", "message": "Hello"}

        result = await websocket_handler._receive_request(mock_websocket, 123)

        assert result == {"thread_id": "thread123", "message": "Hello"}
        mock_websocket.receive_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_receive_request_json_decode_error(self, websocket_handler, mock_websocket):
        """Test handling JSON decode error."""

        # Mock receive_json to raise JSONDecodeError
        mock_websocket.receive_json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        with patch("assistant_service.services.ws_stream_handler.WebSocketErrorHandler") as mock_error_handler:
            mock_error_handler.send_error = AsyncMock()

            result = await websocket_handler._receive_request(mock_websocket, 123)

            assert result is None
            mock_error_handler.send_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_receive_request_websocket_disconnect(self, websocket_handler, mock_websocket):
        """Test handling WebSocket disconnect."""
        mock_websocket.receive_json.side_effect = WebSocketDisconnect()

        result = await websocket_handler._receive_request(mock_websocket, 123)

        assert result is None
        mock_websocket.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_receive_request_unexpected_error(self, websocket_handler, mock_websocket):
        """Test handling unexpected error during receive."""
        mock_websocket.receive_json.side_effect = RuntimeError("Unexpected error")

        with patch("assistant_service.services.ws_stream_handler.WebSocketErrorHandler") as mock_error_handler:
            mock_error_handler.is_disconnect_error.return_value = False
            mock_error_handler.send_error = AsyncMock()

            result = await websocket_handler._receive_request(mock_websocket, 123)

            assert result is None
            mock_error_handler.send_error.assert_called_once()


class TestProcessStream:
    """Test cases for _process_stream method."""

    @pytest.mark.asyncio
    async def test_process_stream_success(self, websocket_handler, mock_websocket):
        """Test successful stream processing."""
        # Mock events from run processor
        event1 = types.SimpleNamespace(model_dump_json=lambda: '{"event": "test1"}')
        event2 = types.SimpleNamespace(model_dump_json=lambda: '{"event": "test2"}')

        # Create async generator that yields events
        async def mock_process_run_stream(thread_id, message):
            yield event1
            yield event2

        # Patch the method directly
        with patch.object(websocket_handler.orchestrator, "process_run_stream", mock_process_run_stream):
            await websocket_handler._process_stream(mock_websocket, 123, "thread123", "Hello", "corr123")

        assert mock_websocket.send_text.call_count == 2
        mock_websocket.send_text.assert_any_call('{"event": "test1"}')
        mock_websocket.send_text.assert_any_call('{"event": "test2"}')

    @pytest.mark.asyncio
    async def test_process_stream_openai_error(self, websocket_handler, mock_websocket):
        """Test handling OpenAI error during stream."""

        # Create an async generator that raises OpenAI error
        async def mock_process_run_stream(thread_id, message):
            raise OpenAIError("API error")
            yield  # This won't be reached but satisfies the generator requirement

        with patch("assistant_service.services.ws_stream_handler.WebSocketErrorHandler") as mock_error_handler:
            mock_error_handler.send_error = AsyncMock()

            # Patch the method directly
            with patch.object(websocket_handler.orchestrator, "process_run_stream", mock_process_run_stream):
                await websocket_handler._process_stream(mock_websocket, 123, "thread123", "Hello", "corr123")

            mock_error_handler.send_error.assert_called_once()
            args = mock_error_handler.send_error.call_args[0]
            # Should send specific OpenAI error message
            assert args[1].startswith("OpenAI service error")

    @pytest.mark.asyncio
    async def test_process_stream_send_error(self, websocket_handler, mock_websocket):
        """Test handling send error during stream."""
        # Mock events
        event1 = types.SimpleNamespace(model_dump_json=lambda: '{"event": "test1"}')
        event2 = types.SimpleNamespace(model_dump_json=lambda: '{"event": "test2"}')

        # Create async generator that yields events
        async def mock_process_run_stream(thread_id, message):
            yield event1
            yield event2

        # First send succeeds, second fails
        mock_websocket.send_text.side_effect = [None, RuntimeError("Send failed")]

        with patch("assistant_service.services.ws_stream_handler.WebSocketErrorHandler") as mock_error_handler:
            mock_error_handler.is_disconnect_error.return_value = False
            mock_error_handler.send_error = AsyncMock()

            # Patch the method directly
            with patch.object(websocket_handler.orchestrator, "process_run_stream", mock_process_run_stream):
                await websocket_handler._process_stream(mock_websocket, 123, "thread123", "Hello", "corr123")

            mock_error_handler.send_error.assert_called_once()
            args = mock_error_handler.send_error.call_args[0]
            assert "Failed to send event" in args[1]

    @pytest.mark.asyncio
    async def test_process_stream_client_disconnect_during_stream(self, websocket_handler, mock_websocket):
        """Test handling client disconnect during stream."""
        # Mock events
        event1 = types.SimpleNamespace(model_dump_json=lambda: '{"event": "test1"}')

        # Create async generator that yields events
        async def mock_process_run_stream(thread_id, message):
            yield event1

        # Simulate disconnect on first send
        mock_websocket.send_text.side_effect = WebSocketDisconnect()

        with patch("assistant_service.services.ws_stream_handler.WebSocketErrorHandler") as mock_error_handler:
            mock_error_handler.is_disconnect_error.return_value = True

            # Patch the method directly
            with patch.object(websocket_handler.orchestrator, "process_run_stream", mock_process_run_stream):
                await websocket_handler._process_stream(mock_websocket, 123, "thread123", "Hello", "corr123")

            # Should not send error on disconnect
            mock_error_handler.send_error.assert_not_called()


class TestHandleMessageLoop:
    """Test cases for _handle_message_loop method."""

    @pytest.mark.asyncio
    async def test_handle_message_loop_missing_fields(self, websocket_handler, mock_websocket):
        """Test handling request with missing required fields."""
        # Missing thread_id
        mock_websocket.receive_json.side_effect = [
            {"message": "Hello"},  # Missing thread_id
            WebSocketDisconnect(),  # End the loop
        ]

        with patch("assistant_service.services.ws_stream_handler.WebSocketErrorHandler") as mock_error_handler:
            mock_error_handler.send_error = AsyncMock()

            await websocket_handler._handle_message_loop(mock_websocket, 123)

            mock_error_handler.send_error.assert_called_once()
            args = mock_error_handler.send_error.call_args[0]
            assert "Missing thread_id or message" in args[1]

    @pytest.mark.asyncio
    async def test_handle_message_loop_valid_request(self, websocket_handler, mock_websocket, mock_orchestrator):
        """Test handling valid request in message loop."""
        mock_websocket.receive_json.side_effect = [
            {"thread_id": "thread123", "message": "Hello"},
            WebSocketDisconnect(),  # End the loop
        ]

        # Mock empty stream - create proper async generator
        async def empty_stream():
            return
            yield  # Never reached but makes it a generator

        # Set up the mock to return the generator when called
        mock_orchestrator.process_run_stream.return_value = empty_stream()

        await websocket_handler._handle_message_loop(mock_websocket, 123)

        mock_orchestrator.process_run_stream.assert_called_once_with("thread123", "Hello")

    @pytest.mark.asyncio
    async def test_handle_message_loop_multiple_messages(self, websocket_handler, mock_websocket, mock_orchestrator):
        """Test handling multiple messages in the loop."""
        mock_websocket.receive_json.side_effect = [
            {"thread_id": "thread1", "message": "Hello"},
            {"thread_id": "thread2", "message": "World"},
            WebSocketDisconnect(),  # End the loop
        ]

        # Mock empty stream - create proper async generator
        async def empty_stream():
            return
            yield  # Never reached but makes it a generator

        # Set up the mock to return the generator when called
        mock_orchestrator.process_run_stream.return_value = empty_stream()

        await websocket_handler._handle_message_loop(mock_websocket, 123)

        assert mock_orchestrator.process_run_stream.call_count == 2
        mock_orchestrator.process_run_stream.assert_any_call("thread1", "Hello")
        mock_orchestrator.process_run_stream.assert_any_call("thread2", "World")
