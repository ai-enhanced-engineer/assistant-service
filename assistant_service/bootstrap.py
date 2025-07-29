from assistant_service.entities import EngineAssistantConfig
from assistant_service.repositories import BaseConfigRepository, BaseSecretRepository


def get_engine_config(
    secret_repository: BaseSecretRepository, config_repository: BaseConfigRepository
) -> EngineAssistantConfig:
    config = config_repository.read_config()
    if not isinstance(config, EngineAssistantConfig):
        raise TypeError("Config repository returned invalid type")
    config.openai_apikey = secret_repository.access_secret("openai-api-key")
    return config
