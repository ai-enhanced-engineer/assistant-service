import abc
import json

from google.cloud import storage

from botbrew_commons.data_models import AssistantConfig


class BaseConfigRepository(abc.ABC):
    @abc.abstractmethod
    def write_config(self, config: AssistantConfig) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def read_config(self) -> AssistantConfig:
        raise NotImplementedError


class LocalConfigRepository(BaseConfigRepository):
    def __init__(self):
        self._config = None

    def write_config(self, config: AssistantConfig) -> None:
        self._config = config

    def read_config(self) -> AssistantConfig:
        return self._config


class GCPConfigRepository(BaseConfigRepository):
    def __init__(self, client_id: str, bucket_name: str):
        client = storage.Client()
        self._blob = client.bucket(bucket_name).blob("configs/" + client_id)

    def write_config(self, config: AssistantConfig) -> None:
        with self._blob.open("w") as f:
            f.write(json.dumps(config.dict()))

    def read_config(self) -> AssistantConfig:
        with self._blob.open("r") as f:
            return AssistantConfig(**json.loads(f.read()))
