import abc
import logging

from google.cloud import secretmanager

logger = logging.getLogger(__name__)


class BaseSecretRepository(abc.ABC):

    @abc.abstractmethod
    def write_secret(self, secret: str) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def access_secret(self) -> str:
        raise NotImplementedError


class LocalSecretRepository(BaseSecretRepository):

    def __init__(self, client_id: str, project_id: str):
        self._project_id = project_id
        self._secret_id = client_id + "-openai"
        self._secret = None

    def write_secret(self, secret: str) -> None:
        self._secret = self._project_id + "/" + self._secret_id + "/" + secret

    def access_secret(self) -> str:
        return self._secret


class GCPSecretRepository(BaseSecretRepository):
    def __init__(self, client_id: str, project_id: str):
        self._client = secretmanager.SecretManagerServiceClient()
        self._project_id = project_id
        self._secret_id = client_id + "-openai"

    def write_secret(self, secret: str) -> None:
        pass

    def access_secret(self) -> str:
        path = self._client.secret_version_path(
            project=self._project_id, secret=self._secret_id, secret_version="latest"
        )
        response = self._client.access_secret_version(name=path)
        logger.info(f"Retrieved secret at: {path}")
        secret = response.payload.data.decode("UTF-8")
        return secret
