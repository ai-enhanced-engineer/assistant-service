from assistant_service.bootstrap import get_assistant_config, get_config_repository, get_secret_repository
from assistant_service.entities import ServiceConfig
from assistant_service.repositories import (
    LocalConfigRepository,
    LocalSecretRepository,
)


def test__get_assistant_config(monkeypatch):
    with monkeypatch.context() as mp:
        mp.setenv("PROJECT_ID", "test-project")
        mp.setenv("CLIENT_ID", "test-client")
        mp.setenv("BUCKET_ID", "test-bucket")
        mp.setenv("ASSISTANT_ID", "test-assistant-id")
        mp.setenv("OPENAI_API_KEY", "test-api-key")

        local_secrets = LocalSecretRepository()  # No arguments
        local_config = LocalConfigRepository()  # No arguments

        assistant_config = get_assistant_config(local_secrets, local_config)

        # LocalConfigRepository always uses ASSISTANT_ID env var or default
        assert assistant_config.assistant_id == "test-assistant-id"
        assert assistant_config.assistant_name == "Development Assistant"
        assert assistant_config.initial_message == "Hello! I'm your development assistant. How can I help you today?"
        # openai_apikey is no longer part of AssistantConfig, moved to ServiceConfig


def test__get_secret_repository_development():
    """Test that development config returns LocalSecretRepository."""
    config = ServiceConfig(
        environment="development",
        project_id="test-project",
        bucket_id="test-bucket",
        openai_api_key="test-key",
    )
    repo = get_secret_repository(config)
    assert isinstance(repo, LocalSecretRepository)


def test__get_secret_repository_production(monkeypatch):
    """Test that production config returns GCPSecretRepository."""

    # Patch the GCPSecretRepository to avoid actual GCP calls
    class MockGCPSecretRepository:
        def __init__(self, project_id):
            self.project_id = project_id

    monkeypatch.setattr("assistant_service.bootstrap.GCPSecretRepository", MockGCPSecretRepository)

    config = ServiceConfig(
        environment="production",
        project_id="test-project",
        bucket_id="test-bucket",
        openai_api_key="test-key",
    )
    repo = get_secret_repository(config)
    assert isinstance(repo, MockGCPSecretRepository)
    assert repo.project_id == "test-project"


def test__get_config_repository_development():
    """Test that development config returns LocalConfigRepository."""
    config = ServiceConfig(
        environment="development",
        project_id="test-project",
        bucket_id="test-bucket",
        openai_api_key="test-key",
    )
    repo = get_config_repository(config)
    assert isinstance(repo, LocalConfigRepository)


def test__get_config_repository_production(monkeypatch):
    """Test that production config returns GCPConfigRepository."""

    # Patch the GCPConfigRepository to avoid actual GCP calls
    class MockGCPConfigRepository:
        def __init__(self, project_id, bucket_name):
            self.project_id = project_id
            self.bucket_name = bucket_name

    monkeypatch.setattr("assistant_service.bootstrap.GCPConfigRepository", MockGCPConfigRepository)

    config = ServiceConfig(
        environment="production",
        project_id="test-project",
        bucket_id="test-bucket",
        openai_api_key="test-key",
    )
    repo = get_config_repository(config)
    assert isinstance(repo, MockGCPConfigRepository)
    assert repo.project_id == "test-project"
    assert repo.bucket_name == "test-bucket"
