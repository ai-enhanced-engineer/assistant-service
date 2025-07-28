"""GCP Storage writer for assistant configurations."""

import json

from google.cloud import storage  # type: ignore[attr-defined]

from assistant_factory.models import EngineAssistantConfig


class GCPConfigWriter:
    """Writes assistant configurations to GCP Storage.
    
    This is a minimal implementation that only supports writing configs,
    as that's all the factory needs.
    """
    
    def __init__(self, client_id: str, project_id: str, bucket_name: str):
        client = storage.Client(project=project_id)
        self._blob = client.bucket(bucket_name).blob("configs/" + client_id)

    def write_config(self, config: EngineAssistantConfig) -> None:
        """Write configuration to GCP Storage."""
        with self._blob.open("w") as f:
            f.write(json.dumps(config.dict()))