"""Factory functions for creating and configuring application components with dependency injection."""

from typing import TYPE_CHECKING, Optional

from openai import AsyncOpenAI

from assistant_service.entities import (
    EngineAssistantConfig,
    ServiceConfig,
)

if TYPE_CHECKING:
    from assistant_service.services.message_parser import IMessageParser
    from assistant_service.services.openai_orchestrator import IOrchestrator
    from assistant_service.services.stream_handler import IStreamHandler
    from assistant_service.services.tool_executor import IToolExecutor
from assistant_service.repositories import (
    BaseConfigRepository,
    BaseSecretRepository,
    GCPConfigRepository,
    GCPSecretRepository,
    LocalConfigRepository,
    LocalSecretRepository,
)
from assistant_service.structured_logging import get_logger

logger = get_logger("BOOTSTRAP")


def get_secret_repository(config: ServiceConfig) -> BaseSecretRepository:
    """Create development or production secret repository based on environment."""
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
    """Create development or production config repository based on environment."""
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


def get_openai_client(config: EngineAssistantConfig) -> AsyncOpenAI:
    logger.info("Creating OpenAI client")
    return AsyncOpenAI(api_key=config.openai_apikey)


def get_orchestrator(client: AsyncOpenAI, config: EngineAssistantConfig) -> "IOrchestrator":
    """Create orchestrator with configurable type selection for future extensibility."""
    # Import here to avoid circular dependencies
    from assistant_service.services.openai_orchestrator import OpenAIOrchestrator

    orchestrator_type = getattr(config, "orchestrator_type", "openai")

    if orchestrator_type == "openai":
        logger.info("Creating OpenAI orchestrator")
        tool_executor = get_tool_executor(config)
        return OpenAIOrchestrator(client, config, tool_executor)
    else:
        raise ValueError(f"Unknown orchestrator type: {orchestrator_type}")


def get_stream_handler(orchestrator: "IOrchestrator") -> "IStreamHandler":
    # Import here to avoid circular dependencies
    from assistant_service.services.stream_handler import StreamHandler

    logger.info("Creating WebSocket stream handler")
    return StreamHandler(orchestrator)


def get_tool_executor(config: Optional[EngineAssistantConfig] = None) -> "IToolExecutor":
    # Import here to avoid circular dependencies
    from assistant_service.services.tool_executor import ToolExecutor

    logger.info("Creating tool executor")
    # In the future, config could specify different tool maps
    return ToolExecutor()


def get_message_parser() -> "IMessageParser":
    # Import here to avoid circular dependencies
    from assistant_service.services.message_parser import MessageParser

    logger.info("Creating message parser")
    return MessageParser()
