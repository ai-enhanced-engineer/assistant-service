from assistant_service.config import build_engine_config
from assistant_service.repositories import LocalConfigRepository, LocalSecretRepository


def test__build_engine_config(monkeypatch):
    with monkeypatch.context() as mp:
        mp.setenv("PROJECT_ID", "test-project")
        mp.setenv("CLIENT_ID", "test-client")
        mp.setenv("BUCKET_ID", "test-bucket")
        mp.setenv("ASSISTANT_ID", "test-assistant-id")
        mp.setenv("OPENAI_API_KEY", "test-api-key")

        local_secrets = LocalSecretRepository()  # No arguments
        local_config = LocalConfigRepository()  # No arguments

        engine_config = build_engine_config(local_secrets, local_config)

        # LocalConfigRepository always uses ASSISTANT_ID env var or default
        assert engine_config.assistant_id == "test-assistant-id"
        assert engine_config.assistant_name == "Development Assistant"
        assert engine_config.initial_message == "Hello! I'm your development assistant. How can I help you today?"
        assert engine_config.openai_apikey == "test-api-key"
