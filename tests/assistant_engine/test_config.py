from assistant_engine.config import build_engine_config
from assistant_engine.models import EngineAssistantConfig
from assistant_engine.repositories import LocalConfigRepository, LocalSecretRepository


def test__build_engine_config(monkeypatch):
    with monkeypatch.context() as mp:
        mp.setenv("PROJECT_ID", "test-project")
        mp.setenv("CLIENT_ID", "test-client")
        mp.setenv("BUCKET_ID", "test-bucket")

        # Change this
        mp.setenv("ASSISTANT_ID", "test-assistant-id")

        local_secrets = LocalSecretRepository("test-client", "test-project")
        local_secrets.write_secret("test-secret")

        local_config = LocalConfigRepository()
        local_config.write_config(
            EngineAssistantConfig(
                assistant_id="test-assistant-id",
                assistant_name="name",
                initial_message="hi",
            )
        )

        engine_config = build_engine_config(local_secrets, local_config)
        assert engine_config.assistant_id == "test-assistant-id"
        assert engine_config.openai_apikey == "test-project/test-client-test-secret"
        assert engine_config.assistant_id == "test-assistant-id"
