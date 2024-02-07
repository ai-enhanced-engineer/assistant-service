import os

from pydantic import BaseModel

from commons.repositories.secrets import BaseSecretRepository


class AssistantEngineConfig(BaseModel):
    assistant_id: str
    openai_apikey: str


def build_engine_config(secret_repository: BaseSecretRepository):
    return AssistantEngineConfig(
        assistant_id=os.environ["ASSISTANT_ID"], openai_apikey=secret_repository.access_secret()
    )
