"""Local implementations of repositories for testing."""

import os
from typing import Any

from assistant_service.entities import AssistantConfig

from .base import BaseConfigRepository, BaseSecretRepository


class LocalSecretRepository(BaseSecretRepository):
    """Local implementation of secret repository for development."""

    def __init__(self) -> None:
        pass

    def write_secret(self, secret_suffix: str) -> None:
        pass

    def access_secret(self, secret_suffix: str) -> str:
        """Return local secret."""
        return f"local-{secret_suffix}"


class LocalConfigRepository(BaseConfigRepository):
    """Local implementation of config repository for development."""

    def __init__(self) -> None:
        pass

    def write_config(self, config: Any) -> None:
        pass

    def read_config(self) -> AssistantConfig:
        """Return default development configuration."""
        assistant_id = os.getenv("ASSISTANT_ID", "asst_dev_default")

        return AssistantConfig(
            assistant_id=assistant_id,
            assistant_name="Development Assistant",
            initial_message="Hello! I'm your development assistant. How can I help you today?",
            code_interpreter=True,
            file_search=False,
            function_names=[],
        )
