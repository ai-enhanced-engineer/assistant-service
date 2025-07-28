"""Local implementations of repositories for testing."""

from typing import Any, Optional

from .base import BaseConfigRepository, BaseSecretRepository


class LocalSecretRepository(BaseSecretRepository):
    """Local implementation of secret repository for testing."""
    
    def __init__(self, client_id: str, project_id: str):
        self._project_id = project_id
        self._client_id = client_id
        self._secret: Optional[str] = None

    def write_secret(self, secret_suffix: str) -> None:
        self._secret = self._project_id + "/" + self._client_id + "-" + secret_suffix

    def access_secret(self, secret_suffix: str) -> str:
        print(secret_suffix)  # Silence warning
        if self._secret is None:
            raise ValueError("No secret has been written yet")
        return self._secret


class LocalConfigRepository(BaseConfigRepository):
    """Local implementation of config repository for testing."""
    
    def __init__(self) -> None:
        self._config: Optional[Any] = None

    def write_config(self, config: Any) -> None:
        self._config = config

    def read_config(self) -> Any:
        return self._config