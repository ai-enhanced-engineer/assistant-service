from assistant_service.config import build_engine_config
from commons.data_models.config import BaseConfig
from commons.repositories.secrets import LocalSecretRepository


def test__build_engine_config(monkeypatch):
    with monkeypatch.context() as mp:
        mp.setenv("PROJECT_ID", "test-project")
        mp.setenv("CLIENT_ID", "test-client")

        # Change this
        mp.setenv("ASSISTANT_ID", "test-assistant-id")

        base_config = BaseConfig()
        local_secrets = LocalSecretRepository(base_config.client_id, base_config.project_id)
        local_secrets.write_secret("test-secret")

        engine_config = build_engine_config(local_secrets)
        assert engine_config.assistant_id == "test-assistant-id"
        assert engine_config.openai_apikey == "test-project/test-client/test-secret"
