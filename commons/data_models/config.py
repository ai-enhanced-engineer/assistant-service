from typing import Optional

from pydantic import BaseModel, Field
from pydantic.v1 import BaseSettings


class BaseConfig(BaseSettings):
    project_id: str = Field(..., env="PROJECT_ID")
    bucket_id: str = Field(..., env="BUCKET_ID")
    client_id: str = Field(..., env="CLIENT_ID")


class AssistantConfig(BaseModel):
    assistant_id: str
    function_names: Optional[list[str]] = Field(default=None)
