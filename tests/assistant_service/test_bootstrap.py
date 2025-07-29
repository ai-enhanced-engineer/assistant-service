from assistant_service.bootstrap import get_config_repository, get_engine_config, get_secret_repository
from assistant_service.repositories import (
    LocalConfigRepository,
    LocalSecretRepository,
)
from assistant_service.service_config import ServiceConfig


def test__get_engine_config(monkeypatch):
    with monkeypatch.context() as mp:
        mp.setenv("PROJECT_ID", "test-project")
        mp.setenv("CLIENT_ID", "test-client")
        mp.setenv("BUCKET_ID", "test-bucket")
        mp.setenv("ASSISTANT_ID", "test-assistant-id")
        mp.setenv("OPENAI_API_KEY", "test-api-key")

        local_secrets = LocalSecretRepository()  # No arguments
        local_config = LocalConfigRepository()  # No arguments

        engine_config = get_engine_config(local_secrets, local_config)

        # LocalConfigRepository always uses ASSISTANT_ID env var or default
        assert engine_config.assistant_id == "test-assistant-id"
        assert engine_config.assistant_name == "Development Assistant"
        assert engine_config.initial_message == "Hello! I'm your development assistant. How can I help you today?"
        assert engine_config.openai_apikey == "test-api-key"


def test__get_secret_repository_development():
    """Test that development config returns LocalSecretRepository."""
    config = ServiceConfig(environment="development")
    repo = get_secret_repository(config)
    assert isinstance(repo, LocalSecretRepository)


def test__get_secret_repository_production(monkeypatch):
    """Test that production config returns GCPSecretRepository."""

    # Patch the GCPSecretRepository to avoid actual GCP calls
    class MockGCPSecretRepository:
        def __init__(self, project_id, client_id):
            self.project_id = project_id
            self.client_id = client_id

    monkeypatch.setattr("assistant_service.bootstrap.GCPSecretRepository", MockGCPSecretRepository)

    config = ServiceConfig(
        environment="production", project_id="test-project", bucket_id="test-bucket", client_id="test-client"
    )
    repo = get_secret_repository(config)
    assert isinstance(repo, MockGCPSecretRepository)
    assert repo.project_id == "test-project"
    assert repo.client_id == "test-client"


def test__get_config_repository_development():
    """Test that development config returns LocalConfigRepository."""
    config = ServiceConfig(environment="development")
    repo = get_config_repository(config)
    assert isinstance(repo, LocalConfigRepository)


def test__get_config_repository_production(monkeypatch):
    """Test that production config returns GCPConfigRepository."""

    # Patch the GCPConfigRepository to avoid actual GCP calls
    class MockGCPConfigRepository:
        def __init__(self, client_id, project_id, bucket_name):
            self.client_id = client_id
            self.project_id = project_id
            self.bucket_name = bucket_name

    monkeypatch.setattr("assistant_service.bootstrap.GCPConfigRepository", MockGCPConfigRepository)

    config = ServiceConfig(
        environment="production", project_id="test-project", bucket_id="test-bucket", client_id="test-client"
    )
    repo = get_config_repository(config)
    assert isinstance(repo, MockGCPConfigRepository)
    assert repo.project_id == "test-project"
    assert repo.bucket_name == "test-bucket"
    assert repo.client_id == "test-client"
