from pydantic import Field
from pydantic.v1 import BaseSettings


class BaseConfig(BaseSettings):
    project_id: str = Field(..., env="PROJECT_ID")
    client_id: str = Field(..., env="CLIENT_ID")
