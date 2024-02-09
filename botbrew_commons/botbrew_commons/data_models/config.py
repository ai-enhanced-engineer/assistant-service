from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class BaseConfig(BaseSettings):
    project_id: str = Field(json_schema_extra={"environ": True})
    bucket_id: str = Field(json_schema_extra={"environ": True})
    client_id: str = Field(json_schema_extra={"environ": True})


class AssistantConfig(BaseModel):
    assistant_id: str
    function_names: Optional[list[str]] = Field(default=None)
