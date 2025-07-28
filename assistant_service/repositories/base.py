"""Abstract base classes for repository implementations."""

import abc
from typing import Any


class BaseSecretRepository(abc.ABC):
    """Abstract base class for secret repository implementations."""

    @abc.abstractmethod
    def write_secret(self, secret_suffix: str) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def access_secret(self, secret_suffix: str) -> str:
        raise NotImplementedError


class BaseConfigRepository(abc.ABC):
    """Abstract base class for configuration repository implementations."""

    @abc.abstractmethod
    def write_config(self, config: Any) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def read_config(self) -> Any:
        raise NotImplementedError
