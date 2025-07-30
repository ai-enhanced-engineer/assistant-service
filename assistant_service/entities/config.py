"""Configuration models for the assistant engine."""

from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceConfig(BaseSettings):
    """Service configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        populate_by_name=True,
    )

    environment: Literal["development", "production"] = Field(
        default="development",
        description="Environment mode",
        validation_alias="ENVIRONMENT",
    )
    project_id: str = Field(
        description="GCP project ID",
        validation_alias="PROJECT_ID",
    )
    bucket_id: str = Field(
        description="GCS bucket ID",
        validation_alias="BUCKET_ID",
    )
    openai_api_key: str = Field(
        description="OpenAI API key",
        validation_alias="OPENAI_API_KEY",
    )
    orchestrator_type: Literal["openai"] = Field(
        default="openai",
        description="Orchestrator type",
        validation_alias="ORCHESTRATOR_TYPE",
    )
    stream_handler_type: Literal["websocket"] = Field(
        default="websocket",
        description="Stream handler type",
        validation_alias="STREAM_HANDLER_TYPE",
    )
    tool_executor_type: Literal["default"] = Field(
        default="default",
        description="Tool executor type",
        validation_alias="TOOL_EXECUTOR_TYPE",
    )
    message_parser_type: Literal["default"] = Field(
        default="default",
        description="Message parser type",
        validation_alias="MESSAGE_PARSER_TYPE",
    )


class AssistantConfig(BaseModel):
    """Configuration for an OpenAI assistant instance."""

    assistant_id: str = Field(
        default="",
        description="Assistant ID",
    )
    assistant_name: str = Field(
        description="Assistant name",
    )
    initial_message: str = Field(
        description="Initial greeting message",
    )
    code_interpreter: bool = Field(
        default=False,
        description="Enable code interpreter",
    )
    file_search: bool = Field(
        default=False,
        description="Enable file search",
    )
    function_names: list[str] = Field(
        default_factory=list,
        description="List of enabled functions",
    )
