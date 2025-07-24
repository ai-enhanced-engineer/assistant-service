import abc
import json
from typing import Optional

from google.cloud import storage  # type: ignore[attr-defined]

from botbrew_commons.data_models import EngineAssistantConfig


class BaseConfigRepository(abc.ABC):
    @abc.abstractmethod
    def write_config(self, config: EngineAssistantConfig) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def read_config(self) -> EngineAssistantConfig:
        raise NotImplementedError


class LocalConfigRepository(BaseConfigRepository):
    def __init__(self) -> None:
        self._config: Optional[EngineAssistantConfig] = None

    def write_config(self, config: EngineAssistantConfig) -> None:
        self._config = config

    def read_config(self) -> EngineAssistantConfig:
        return self._config


class GCPConfigRepository(BaseConfigRepository):
    # Todo: Generalize this to a file repository.
    def __init__(self, client_id: str, project_id: str, bucket_name: str):
        client = storage.Client(project=project_id)
        self._blob = client.bucket(bucket_name).blob("configs/" + client_id)

    def write_config(self, config: EngineAssistantConfig) -> None:
        with self._blob.open("w") as f:
            f.write(json.dumps(config.dict()))

    def read_config(self) -> EngineAssistantConfig:
        with self._blob.open("r") as f:
            return EngineAssistantConfig(**json.loads(f.read()))
