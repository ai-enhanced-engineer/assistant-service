import abc
import json

import BBConfig
from google.cloud import storage


class BBConfigRepository(abc.ABC):
    @abc.abstractmethod
    def write_config(self, config: BBConfig) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def read_config(self, config_name: str) -> BBConfig:
        raise NotImplementedError


class LocalConfigRepository(BBConfigRepository):
    def write_config(self, config: BBConfig) -> None:
        with open("local-config.json", "w") as f:
            json.dump(config.dict(), f)

    def read_config(self, config_name: str) -> BBConfig:
        with open(config_name) as f:
            return json.load(f)


class GCPConfigRepository(BBConfigRepository):
    def __init__(self, client_id: str, bucket_name: str):
        client = storage.Client()
        self.client_id = client_id
        self.bucket = client.bucket(bucket_name)

    def write_config(self, config: BBConfig) -> None:
        blob = self.bucket.blob(config)

        with blob.open("w") as f:
            f.write(config.dict())

    def read_config(self, config_name: str):
        blob = self.bucket.blob(config_name)

        with blob.open("r") as f:
            print(f.read())
