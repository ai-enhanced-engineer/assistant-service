"""Shared test fixtures for the entire test suite."""

import types
from unittest.mock import AsyncMock

import pytest

from assistant_service import repositories as repos
from assistant_service.entities import EngineAssistantConfig, ServiceConfig


class DummySecretRepository:
    """Mock secret repository for testing."""

    def __init__(self, project_id: str = "", client_id: str = ""):
        self.project_id = project_id
        self.client_id = client_id

    def write_secret(self, _):
        """No-op write for testing."""
        pass

    def access_secret(self, name: str) -> str:
        """Return test secret based on name."""
        if name == "openai-api-key":
            import os

            return os.environ.get("OPENAI_API_KEY", "test-key")
        return f"local-{name}"


class DummyConfigRepository:
    """Mock config repository for testing."""

    def __init__(self, client_id: str = "", project_id: str = "", bucket_name: str = ""):
        self.client_id = client_id
        self.project_id = project_id
        self.bucket_name = bucket_name

    def write_config(self, _config):
        """No-op write for testing."""
        pass

    def read_config(self):
        """Return default test config."""
        return EngineAssistantConfig(
            assistant_id="test-assistant",
            assistant_name="Development Assistant",
            initial_message="Hello! I'm your development assistant. How can I help you today?",
        )


class DummyThreads:
    """Mock OpenAI threads API."""

    async def create(self):
        """Return mock thread."""
        return types.SimpleNamespace(id="thread123")


class DummyBeta:
    """Mock OpenAI beta API."""

    def __init__(self):
        self.threads = DummyThreads()


class DummyClient:
    """Mock OpenAI client for testing."""

    def __init__(self, api_key=None) -> None:
        self.beta = DummyBeta()
        self.aclose = AsyncMock()
        self.close = AsyncMock()


@pytest.fixture
def dummy_secret_repo():
    """Provide a dummy secret repository."""
    return DummySecretRepository()


@pytest.fixture
def dummy_config_repo():
    """Provide a dummy config repository."""
    return DummyConfigRepository()


@pytest.fixture
def dummy_client():
    """Provide a dummy OpenAI client."""
    return DummyClient()


@pytest.fixture
def test_service_config():
    """Provide a test service configuration."""
    return ServiceConfig(
        environment="development",
        project_id="test-project",
        bucket_id="test-bucket",
        client_id="test-client",
    )


@pytest.fixture
def test_engine_config():
    """Provide a test engine configuration."""
    return EngineAssistantConfig(
        assistant_id="test-assistant",
        assistant_name="Test Assistant",
        initial_message="Hello",
        code_interpreter=False,
        retrieval=False,
        function_names=["test_func"],
    )


@pytest.fixture
def mock_repositories(monkeypatch):
    """Mock both GCP repository classes."""
    monkeypatch.setattr(repos, "GCPSecretRepository", DummySecretRepository)
    monkeypatch.setattr(repos, "GCPConfigRepository", DummyConfigRepository)


@pytest.fixture
def mock_openai_client(monkeypatch, dummy_client):
    """Mock the OpenAI client factory."""
    import assistant_service.bootstrap

    monkeypatch.setattr(assistant_service.bootstrap, "get_openai_client", lambda config: dummy_client)
    return dummy_client
