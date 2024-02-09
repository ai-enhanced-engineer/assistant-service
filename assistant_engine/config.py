from pydantic import BaseModel

from botbrew_commons.repositories import BaseConfigRepository, BaseSecretRepository


class AssistantEngineConfig(BaseModel):
    assistant_id: str
    openai_apikey: str


def build_engine_config(secret_repository: BaseSecretRepository, config_repository: BaseConfigRepository):
    assistant_config = config_repository.read_config()
    openai_api_key = secret_repository.access_secret("openai-api-key")
    return AssistantEngineConfig(assistant_id=assistant_config.assistant_id, openai_apikey=openai_api_key)
