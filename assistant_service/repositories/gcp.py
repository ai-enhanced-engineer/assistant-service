"""Google Cloud Platform implementations of repositories."""

import json
from typing import Any

from google.cloud import (  # type: ignore[attr-defined]
    secretmanager,
    storage,
)

from .base import BaseConfigRepository, BaseSecretRepository


class GCPSecretRepository(BaseSecretRepository):
    """GCP Secret Manager implementation."""

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

        response = self._client.access_secret_version(name=path)
        secret = response.payload.data.decode("UTF-8")
        return secret

    def build_secret_name(self, secret_suffix: str) -> str:
        return self._client_id + "-" + secret_suffix


class GCPConfigRepository(BaseConfigRepository):
    """GCP Storage implementation for configuration management."""

    def __init__(self, client_id: str, project_id: str, bucket_name: str):
        client = storage.Client(project=project_id)
        self._blob = client.bucket(bucket_name).blob("configs/" + client_id)

    def write_config(self, config: Any) -> None:
        with self._blob.open("w") as f:
            f.write(json.dumps(config.dict()))

    def read_config(self) -> Any:
        # Importing here to avoid circular import
        from assistant_service.models import EngineAssistantConfig

        with self._blob.open("r") as f:
            return EngineAssistantConfig(**json.loads(f.read()))
