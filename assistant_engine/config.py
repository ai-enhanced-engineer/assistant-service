from botbrew_commons.data_models import EngineAssistantConfig
from botbrew_commons.repositories import BaseConfigRepository, BaseSecretRepository


def build_engine_config(
    secret_repository: BaseSecretRepository, config_repository: BaseConfigRepository
) -> EngineAssistantConfig:
    assistant_config = config_repository.read_config()
    assistant_config.openai_apikey = secret_repository.access_secret("openai-api-key")
    return assistant_config
