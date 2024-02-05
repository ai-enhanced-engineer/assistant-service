import abc
import logging

from google.cloud import secretmanager

logger = logging.getLogger(__name__)


class BaseSecretRepository(abc.ABC):
    @abc.abstractmethod
    def access_secret(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def write_secret(self) -> None:
        raise NotImplementedError


class GCPSecretRepository(BaseSecretRepository):
    def __init__(self, client_id: str, project_id: str):
        self._client = secretmanager.SecretManagerServiceClient()
        self._project_id = project_id
        self._secret_id = client_id + "-openai"

    def access_secret(self) -> str:
        path = self._client.secret_version_path(
            project=self._project_id, secret=self._secret_id, secret_version="latest"
        )
        response = self._client.access_secret_version(name=path)
        logger.info(f"Retrieved secret at: {path}")
        secret = response.payload.data.decode("UTF-8")
        return secret

    def write_secret(self) -> None:
        pass
