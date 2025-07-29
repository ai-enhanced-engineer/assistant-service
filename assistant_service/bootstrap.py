from assistant_service.entities import EngineAssistantConfig
from assistant_service.repositories import (
    BaseConfigRepository,
    BaseSecretRepository,
    GCPConfigRepository,
    GCPSecretRepository,
    LocalConfigRepository,
    LocalSecretRepository,
)
from assistant_service.service_config import ServiceConfig
from assistant_service.structured_logging import get_logger

logger = get_logger("BOOTSTRAP")


def get_secret_repository(config: ServiceConfig) -> BaseSecretRepository:
    """Factory function to create the appropriate secret repository based on config."""
    if config.is_development:
        logger.info("Using local secret repository for development")
        return LocalSecretRepository()
    else:
        logger.info("Using GCP secret repository for production")
        return GCPSecretRepository(
            project_id=config.project_id,
            client_id=config.client_id,
        )


def get_config_repository(config: ServiceConfig) -> BaseConfigRepository:
    """Factory function to create the appropriate config repository based on config."""
    if config.is_development:
        logger.info("Using local config repository for development")
        return LocalConfigRepository()
    else:
        logger.info("Using GCP config repository for production")
        return GCPConfigRepository(
            client_id=config.client_id,
            project_id=config.project_id,
            bucket_name=config.bucket_id,
        )


def get_engine_config(
    secret_repository: BaseSecretRepository, config_repository: BaseConfigRepository
) -> EngineAssistantConfig:
    config = config_repository.read_config()
    if not isinstance(config, EngineAssistantConfig):
        raise TypeError("Config repository returned invalid type")
    config.openai_apikey = secret_repository.access_secret("openai-api-key")
    return config
