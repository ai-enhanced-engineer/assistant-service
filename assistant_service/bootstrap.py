"""Factory functions for creating and configuring application components with dependency injection."""

from typing import TYPE_CHECKING

from openai import AsyncOpenAI

from assistant_service.entities import (
    AssistantConfig,
    ServiceConfig,
)

if TYPE_CHECKING:
    from assistant_service.services.message_parser import IMessageParser
    from assistant_service.services.openai_orchestrator import IOrchestrator
    from assistant_service.services.sse_stream_handler import ISSEStreamHandler
    from assistant_service.services.tool_executor import IToolExecutor
    from assistant_service.services.ws_stream_handler import IWebSocketStreamHandler
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
SUPPORTED_SSE_STREAM_HANDLERS = {"default"}
SUPPORTED_TOOL_EXECUTORS = {"default"}
SUPPORTED_MESSAGE_PARSERS = {"default"}


def get_secret_repository(config: ServiceConfig) -> BaseSecretRepository:
    """Create development or production secret repository based on environment."""
    if config.environment == "development":
        logger.info("Using local secret repository for development")
        return LocalSecretRepository()
    else:
        logger.info("Using GCP secret repository for production")
        return GCPSecretRepository(
            project_id=config.project_id,
        )


def get_config_repository(config: ServiceConfig) -> BaseConfigRepository:
    """Create development or production config repository based on environment."""
    if config.environment == "development":
        logger.info("Using local config repository for development")
        return LocalConfigRepository()
    else:
        logger.info("Using GCP config repository for production")
        return GCPConfigRepository(
            project_id=config.project_id,
            bucket_name=config.bucket_id,
        )


def get_assistant_config(
    secret_repository: BaseSecretRepository, config_repository: BaseConfigRepository
) -> AssistantConfig:
    config = config_repository.read_config()
    if not isinstance(config, AssistantConfig):
        raise TypeError("Config repository returned invalid type")
    return config


def get_openai_client(service_config: ServiceConfig) -> AsyncOpenAI:
    logger.info("Creating OpenAI client")
    return AsyncOpenAI(api_key=service_config.openai_api_key)


def get_orchestrator(
    client: AsyncOpenAI, service_config: ServiceConfig, assistant_config: AssistantConfig
) -> "IOrchestrator":
    """Create orchestrator with configurable type selection for future extensibility."""
    # Import here to avoid circular dependencies
    from assistant_service.services.openai_orchestrator import OpenAIOrchestrator

    orchestrator_type = service_config.orchestrator_type

    if orchestrator_type not in SUPPORTED_ORCHESTRATORS:
        available = ", ".join(sorted(SUPPORTED_ORCHESTRATORS))
        raise ValueError(f"Unknown orchestrator type '{orchestrator_type}'. Available types: {available}")

    if orchestrator_type == "openai":
        logger.info("Creating OpenAI orchestrator")
        tool_executor = get_tool_executor(service_config)
        return OpenAIOrchestrator(client, assistant_config, tool_executor)

    # This should not be reachable due to SUPPORTED_ORCHESTRATORS check above
    raise ValueError(f"Orchestrator type '{orchestrator_type}' is supported but not implemented")


def get_websocket_stream_handler(
    orchestrator: "IOrchestrator", service_config: ServiceConfig
) -> "IWebSocketStreamHandler":
    """Create WebSocket stream handler with configurable type selection for future extensibility."""
    # Import here to avoid circular dependencies
    from assistant_service.services.ws_stream_handler import WebSocketStreamHandler

    stream_handler_type = service_config.stream_handler_type

    if stream_handler_type not in SUPPORTED_STREAM_HANDLERS:
        available = ", ".join(sorted(SUPPORTED_STREAM_HANDLERS))
        raise ValueError(f"Unknown stream handler type '{stream_handler_type}'. Available types: {available}")

    if stream_handler_type == "websocket":
        logger.info("Creating WebSocket stream handler")
        return WebSocketStreamHandler(orchestrator)

    # This should not be reachable due to SUPPORTED_STREAM_HANDLERS check above
    raise ValueError(f"Stream handler type '{stream_handler_type}' is supported but not implemented")


def get_sse_stream_handler(orchestrator: "IOrchestrator") -> "ISSEStreamHandler":
    """Create SSE stream handler for formatting Server-Sent Events."""
    # Import here to avoid circular dependencies
    from assistant_service.services.sse_stream_handler import SSEStreamHandler

    logger.info("Creating SSE stream handler")
    return SSEStreamHandler(orchestrator)


def get_tool_executor(service_config: ServiceConfig) -> "IToolExecutor":
    """Create tool executor with configurable type selection for future extensibility."""
    # Import here to avoid circular dependencies
    from assistant_service.services.tool_executor import ToolExecutor

    tool_executor_type = service_config.tool_executor_type

    if tool_executor_type not in SUPPORTED_TOOL_EXECUTORS:
        available = ", ".join(sorted(SUPPORTED_TOOL_EXECUTORS))
        raise ValueError(f"Unknown tool executor type '{tool_executor_type}'. Available types: {available}")

    if tool_executor_type == "default":
        logger.info("Creating default tool executor")
        return ToolExecutor()

    # This should not be reachable due to SUPPORTED_TOOL_EXECUTORS check above
    raise ValueError(f"Tool executor type '{tool_executor_type}' is supported but not implemented")


def get_message_parser(service_config: ServiceConfig) -> "IMessageParser":
    """Create message parser with configurable type selection for future extensibility."""
    # Import here to avoid circular dependencies
    from assistant_service.services.message_parser import MessageParser

    message_parser_type = service_config.message_parser_type

    if message_parser_type not in SUPPORTED_MESSAGE_PARSERS:
        available = ", ".join(sorted(SUPPORTED_MESSAGE_PARSERS))
        raise ValueError(f"Unknown message parser type '{message_parser_type}'. Available types: {available}")

    if message_parser_type == "default":
        logger.info("Creating default message parser")
        return MessageParser()

    # This should not be reachable due to SUPPORTED_MESSAGE_PARSERS check above
    raise ValueError(f"Message parser type '{message_parser_type}' is supported but not implemented")
