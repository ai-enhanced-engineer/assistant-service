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

# Component type registries for better error messages and future extensibility
SUPPORTED_ORCHESTRATORS = {"openai"}
SUPPORTED_STREAM_HANDLERS = {"websocket"}
SUPPORTED_TOOL_EXECUTORS = {"default"}
SUPPORTED_MESSAGE_PARSERS = {"default"}


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

    if orchestrator_type not in SUPPORTED_ORCHESTRATORS:
        available = ", ".join(sorted(SUPPORTED_ORCHESTRATORS))
        raise ValueError(f"Unknown orchestrator type '{orchestrator_type}'. Available types: {available}")

    if orchestrator_type == "openai":
        logger.info("Creating OpenAI orchestrator")
        tool_executor = get_tool_executor(config)
        return OpenAIOrchestrator(client, config, tool_executor)
    
    # This should not be reachable due to SUPPORTED_ORCHESTRATORS check above
    raise ValueError(f"Orchestrator type '{orchestrator_type}' is supported but not implemented")


def get_stream_handler(orchestrator: "IOrchestrator", stream_handler_type: str = "websocket") -> "IStreamHandler":
    """Create stream handler with configurable type selection for future extensibility."""
    # Import here to avoid circular dependencies
    from assistant_service.services.stream_handler import StreamHandler

    if stream_handler_type not in SUPPORTED_STREAM_HANDLERS:
        available = ", ".join(sorted(SUPPORTED_STREAM_HANDLERS))
        raise ValueError(f"Unknown stream handler type '{stream_handler_type}'. Available types: {available}")

    if stream_handler_type == "websocket":
        logger.info("Creating WebSocket stream handler")
        return StreamHandler(orchestrator)
    
    # This should not be reachable due to SUPPORTED_STREAM_HANDLERS check above
    raise ValueError(f"Stream handler type '{stream_handler_type}' is supported but not implemented")


def get_tool_executor(config: Optional[EngineAssistantConfig] = None) -> "IToolExecutor":
    """Create tool executor with configurable type selection for future extensibility."""
    # Import here to avoid circular dependencies
    from assistant_service.services.tool_executor import ToolExecutor

    tool_executor_type = getattr(config, "tool_executor_type", "default") if config else "default"

    if tool_executor_type not in SUPPORTED_TOOL_EXECUTORS:
        available = ", ".join(sorted(SUPPORTED_TOOL_EXECUTORS))
        raise ValueError(f"Unknown tool executor type '{tool_executor_type}'. Available types: {available}")

    if tool_executor_type == "default":
        logger.info("Creating default tool executor")
        return ToolExecutor()
    
    # This should not be reachable due to SUPPORTED_TOOL_EXECUTORS check above
    raise ValueError(f"Tool executor type '{tool_executor_type}' is supported but not implemented")


def get_message_parser(message_parser_type: str = "default") -> "IMessageParser":
    """Create message parser with configurable type selection for future extensibility."""
    # Import here to avoid circular dependencies
    from assistant_service.services.message_parser import MessageParser

    if message_parser_type not in SUPPORTED_MESSAGE_PARSERS:
        available = ", ".join(sorted(SUPPORTED_MESSAGE_PARSERS))
        raise ValueError(f"Unknown message parser type '{message_parser_type}'. Available types: {available}")

    if message_parser_type == "default":
        logger.info("Creating default message parser")
        return MessageParser()
    
    # This should not be reachable due to SUPPORTED_MESSAGE_PARSERS check above
    raise ValueError(f"Message parser type '{message_parser_type}' is supported but not implemented")
