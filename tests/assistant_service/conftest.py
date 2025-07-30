"""Assistant service specific test fixtures."""

from unittest.mock import AsyncMock

import pytest

from assistant_service.server.main import AssistantEngineAPI


@pytest.fixture
def api(monkeypatch, mock_repositories, dummy_client, test_service_config):
    """Create an API instance with all dependencies mocked."""
    # Set required environment variable
    monkeypatch.setenv("ASSISTANT_ID", "test-assistant")

    # Mock the OpenAI client creation before any imports
    def mock_get_openai_client(config):
        return dummy_client

    # Patch in the main module where it's imported
    import assistant_service.server.main

    monkeypatch.setattr(assistant_service.server.main, "get_openai_client", mock_get_openai_client)

    # Create the API instance
    api = AssistantEngineAPI(service_config=test_service_config)

    return api, dummy_client


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket for testing."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.close = AsyncMock()
    ws.receive_json = AsyncMock()
    ws.send_text = AsyncMock()
    ws.send_json = AsyncMock()

    # Mock the client_state attribute with a value indicating connected state
    # WebSocket states: CONNECTING=0, CONNECTED=1, DISCONNECTING=2, DISCONNECTED=3
    ws.client_state = AsyncMock()
    ws.client_state.value = 1  # CONNECTED state

    return ws


@pytest.fixture
def mock_orchestrator():
    """Create a mock OpenAI orchestrator."""
    orchestrator = AsyncMock()
    orchestrator.process_run = AsyncMock()
    orchestrator.process_run_stream = AsyncMock()
    return orchestrator


@pytest.fixture
def websocket_handler(mock_orchestrator):
    """Create a WebSocketStreamHandler instance."""
    from assistant_service.services.ws_stream_handler import WebSocketStreamHandler

    return WebSocketStreamHandler(mock_orchestrator)
