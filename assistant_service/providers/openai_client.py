"""OpenAI client wrapper and factory."""

from typing import Optional

from openai import AsyncOpenAI

from ..entities import EngineAssistantConfig
from ..structured_logging import get_logger

logger = get_logger("OPENAI_CLIENT")


class OpenAIClientFactory:
    """Factory for creating and managing OpenAI client instances."""

    @staticmethod
    def create_client(api_key: Optional[str] = None) -> AsyncOpenAI:
        """Create a new AsyncOpenAI client instance.

        Args:
            api_key: Optional API key. If not provided, uses environment variable.

        Returns:
            Configured AsyncOpenAI client
        """
        client = AsyncOpenAI(api_key=api_key)
        logger.debug("OpenAI client created")
        return client

    @staticmethod
    def create_from_config(config: EngineAssistantConfig) -> AsyncOpenAI:
        """Create client from engine configuration.

        Args:
            config: Engine configuration with API key

        Returns:
            Configured AsyncOpenAI client
        """
        return OpenAIClientFactory.create_client(config.openai_apikey)
