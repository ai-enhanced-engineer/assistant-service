from assistant_engine.config import build_engine_config
from botbrew_commons.commons.data_models.config import AssistantConfig, BaseConfig
from botbrew_commons.commons.repositories import LocalConfigRepository, LocalSecretRepository


def test__build_engine_config(monkeypatch):
    with monkeypatch.context() as mp:
        mp.setenv("PROJECT_ID", "test-project")
        mp.setenv("CLIENT_ID", "test-client")
        mp.setenv("BUCKET_ID", "test-bucket")

        # Change this
        mp.setenv("ASSISTANT_ID", "test-assistant-id")

        base_config = BaseConfig()
        local_secrets = LocalSecretRepository(base_config.client_id, base_config.project_id)
        local_secrets.write_secret("test-secret")

        local_config = LocalConfigRepository()
        local_config.write_config(AssistantConfig(assistant_id="test-assistant-id"))

        engine_config = build_engine_config(local_secrets, local_config)
        assert engine_config.assistant_id == "test-assistant-id"
        assert engine_config.openai_apikey == "test-project/test-client-test-secret"
        assert engine_config.assistant_id == "test-assistant-id"
