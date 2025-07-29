"""Tests for correlation ID and enhanced error context functionality."""

import types
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from assistant_service.structured_logging import (
    CorrelationContext,
    generate_correlation_id,
    get_correlation_id,
    get_or_create_correlation_id,
    set_correlation_id,
)


def test_generate_correlation_id():
    """Test correlation ID generation produces valid UUIDs."""
    correlation_id = generate_correlation_id()
    # Should be a valid UUID
    UUID(correlation_id)  # Will raise ValueError if invalid
    assert len(correlation_id) == 36  # Standard UUID length


def test_correlation_context_manager():
    """Test correlation context manager sets and resets context."""
    # Initially no correlation ID
    assert get_correlation_id() is None

    with CorrelationContext() as correlation_id:
        # Should have a correlation ID in context
        assert get_correlation_id() == correlation_id
        assert correlation_id is not None
        UUID(correlation_id)  # Should be valid UUID

    # Should be reset after context
    assert get_correlation_id() is None


def test_correlation_context_with_custom_id():
    """Test correlation context manager with custom ID."""
    custom_id = "custom-test-id"

    with CorrelationContext(custom_id) as correlation_id:
        assert correlation_id == custom_id
        assert get_correlation_id() == custom_id

    assert get_correlation_id() is None


def test_get_or_create_correlation_id():
    """Test get_or_create_correlation_id creates when none exists."""
    # Initially no correlation ID
    assert get_correlation_id() is None

    # Should create a new one
    correlation_id = get_or_create_correlation_id()
    assert correlation_id is not None
    assert get_correlation_id() == correlation_id

    # Should return same one on subsequent calls
    same_id = get_or_create_correlation_id()
    assert same_id == correlation_id


def test_set_and_get_correlation_id():
    """Test manual setting and getting of correlation ID."""
    test_id = "test-correlation-id"

    set_correlation_id(test_id)
    assert get_correlation_id() == test_id


@pytest.mark.asyncio
async def test_api_endpoints_include_correlation_ids(monkeypatch):
    """Test that API endpoints include correlation IDs in responses and logs."""
    from assistant_service import repositories as repos
    from assistant_service.entities import EngineAssistantConfig

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
    import assistant_service.server.main as main_module

    monkeypatch.setattr(main_module, "GCPSecretRepository", DummySecretRepo)
    monkeypatch.setattr(main_module, "GCPConfigRepository", DummyConfigRepo)

    from assistant_service.server.main import AssistantEngineAPI

    # Mock client
    class DummyThreads:
        async def create(self):
            return types.SimpleNamespace(id="thread123")

    class DummyBeta:
        def __init__(self):
            self.threads = DummyThreads()

    class DummyClient:
        def __init__(self) -> None:
            self.beta = DummyBeta()
            self.aclose = AsyncMock()
            self.close = AsyncMock()

    api = AssistantEngineAPI()
    api.client = DummyClient()  # type: ignore[assignment]

    # Initialize components that would normally be initialized in lifespan
    from assistant_service.core.run_processor import RunProcessor
    from assistant_service.server.endpoints import APIEndpoints

    api.run_processor = RunProcessor(api.client, api.engine_config, api.tool_executor)  # type: ignore[arg-type]
    api.api_endpoints = APIEndpoints(api.client, api.engine_config, api.run_processor)  # type: ignore[arg-type]

    with TestClient(api.app) as client:
        # Test start endpoint includes correlation_id
        resp = client.get("/start")
        assert resp.status_code == 200
        data = resp.json()
        assert "correlation_id" in data
        assert "thread_id" in data
        assert data["thread_id"] == "thread123"

        # Correlation ID should be a valid UUID
        UUID(data["correlation_id"])


@pytest.mark.asyncio
async def test_error_responses_include_correlation_ids(monkeypatch):
    """Test that error responses include correlation IDs for debugging."""
    from assistant_service import repositories as repos
    from assistant_service.entities import EngineAssistantConfig

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
    import assistant_service.server.main as main_module

    monkeypatch.setattr(main_module, "GCPSecretRepository", DummySecretRepo)
    monkeypatch.setattr(main_module, "GCPConfigRepository", DummyConfigRepo)

    from openai import OpenAIError

    from assistant_service.server.main import AssistantEngineAPI

    # Mock client that raises error
    class DummyThreads:
        async def create(self):
            raise OpenAIError("Test OpenAI error")

    class DummyBeta:
        def __init__(self):
            self.threads = DummyThreads()

    class DummyClient:
        def __init__(self) -> None:
            self.beta = DummyBeta()
            self.aclose = AsyncMock()
            self.close = AsyncMock()

    api = AssistantEngineAPI()
    api.client = DummyClient()  # type: ignore[assignment]

    # Initialize components that would normally be initialized in lifespan
    from assistant_service.core.run_processor import RunProcessor
    from assistant_service.server.endpoints import APIEndpoints

    api.run_processor = RunProcessor(api.client, api.engine_config, api.tool_executor)  # type: ignore[arg-type]
    api.api_endpoints = APIEndpoints(api.client, api.engine_config, api.run_processor)  # type: ignore[arg-type]

    with TestClient(api.app) as client:
        # Test error response includes correlation_id
        resp = client.get("/start")
        assert resp.status_code == 502
        error_detail = resp.json()["detail"]
        assert "correlation_id:" in error_detail
        # Extract correlation ID from error message
        correlation_part = error_detail.split("correlation_id: ")[1].rstrip(")")
        assert len(correlation_part) == 8  # Should be first 8 characters


@pytest.mark.asyncio
async def test_chat_endpoint_validation_with_correlation_id(monkeypatch):
    """Test chat endpoint validation includes correlation ID in error."""
    from assistant_service import repositories as repos
    from assistant_service.entities import EngineAssistantConfig

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
    import assistant_service.server.main as main_module

    monkeypatch.setattr(main_module, "GCPSecretRepository", DummySecretRepo)
    monkeypatch.setattr(main_module, "GCPConfigRepository", DummyConfigRepo)

    from assistant_service.server.main import AssistantEngineAPI

    api = AssistantEngineAPI()
    api.client = AsyncMock()

    # Initialize components that would normally be initialized in lifespan
    from assistant_service.core.run_processor import RunProcessor
    from assistant_service.server.endpoints import APIEndpoints

    api.run_processor = RunProcessor(api.client, api.engine_config, api.tool_executor)  # type: ignore[arg-type]
    api.api_endpoints = APIEndpoints(api.client, api.engine_config, api.run_processor)  # type: ignore[arg-type]

    with TestClient(api.app) as client:
        # Test missing thread_id includes correlation_id
        resp = client.post("/chat", json={"message": "hello"})
        assert resp.status_code == 422  # Pydantic validation error first

        # Test empty thread_id includes correlation_id
        resp = client.post("/chat", json={"thread_id": "", "message": "hello"})
        assert resp.status_code == 400
        error_detail = resp.json()["detail"]
        assert "correlation_id:" in error_detail
