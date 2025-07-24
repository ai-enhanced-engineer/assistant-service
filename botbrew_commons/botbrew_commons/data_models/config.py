from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class BaseConfig(BaseSettings):
    project_id: str = Field(json_schema_extra={"environ": True})
    bucket_id: str = Field(json_schema_extra={"environ": True})
    client_id: str = Field(json_schema_extra={"environ": True})


class EngineAssistantConfig(BaseModel):
    assistant_id: str
    assistant_name: str
    initial_message: str
    code_interpreter: bool = Field(default=False)
    retrieval: bool = Field(default=False)
    function_names: list[str] = Field(default_factory=list)
    # Secrets
    openai_apikey: Optional[str] = Field(default=None)
