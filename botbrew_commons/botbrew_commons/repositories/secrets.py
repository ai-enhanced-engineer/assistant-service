import abc
import logging

from google.cloud import secretmanager

logger = logging.getLogger(__name__)


class BaseSecretRepository(abc.ABC):
    @abc.abstractmethod
    def write_secret(self, secret_suffix: str) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def access_secret(self, secret_suffix: str) -> str:
        raise NotImplementedError


class LocalSecretRepository(BaseSecretRepository):
    def __init__(self, client_id: str, project_id: str):
        self._project_id = project_id
        self._client_id = client_id
        self._secret = None

    def write_secret(self, secret_suffix: str) -> None:
        self._secret = self._project_id + "/" + self._client_id + "-" + secret_suffix

    def access_secret(self, secret_suffix: str) -> str:
        print(secret_suffix)  # Silence warning
        return self._secret


class GCPSecretRepository(BaseSecretRepository):
    def __init__(self, client_id: str, project_id: str):
        self._client = secretmanager.SecretManagerServiceClient()
        self._project_id = project_id
        self._client_id = client_id

    def write_secret(self, secret_suffix: str) -> None:
        pass

    def access_secret(self, secret_suffix: str) -> str:
        path = self._client.secret_version_path(
            project=self._project_id, secret=self.build_secret_name(secret_suffix), secret_version="latest"
        )
        logger.info(f"Retrieved secret at: {path}")

        response = self._client.access_secret_version(name=path)
        secret = response.payload.data.decode("UTF-8")
        return secret

    def build_secret_name(self, secret_suffix: str):
        return self._client_id + "-" + secret_suffix
