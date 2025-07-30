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
        extra="ignore",  # Ignore extra environment variables
        populate_by_name=True,  # Allow both field names and validation aliases
    )

    # Environment configuration
    environment: Literal["development", "production"] = Field(
        default="development",
        description="The environment the service is running in",
        validation_alias="ENVIRONMENT",
    )

    # GCP configuration
    project_id: str = Field(
        default="",
        description="GCP project ID",
        validation_alias="PROJECT_ID",
    )
    bucket_id: str = Field(
        default="",
        description="GCS bucket ID for configuration storage",
        validation_alias="BUCKET_ID",
    )

    # OpenAI configuration
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key",
        validation_alias="OPENAI_API_KEY",
    )

    # Component type configurations for dependency injection
    orchestrator_type: Literal["openai"] = Field(
        default="openai",
        description="Type of orchestrator to use. Currently supported: 'openai'",
        validation_alias="ORCHESTRATOR_TYPE",
    )
    stream_handler_type: Literal["websocket"] = Field(
        default="websocket",
        description="Type of stream handler to use. Currently supported: 'websocket'",
        validation_alias="STREAM_HANDLER_TYPE",
    )
    tool_executor_type: Literal["default"] = Field(
        default="default",
        description="Type of tool executor to use. Currently supported: 'default'",
        validation_alias="TOOL_EXECUTOR_TYPE",
    )
    message_parser_type: Literal["default"] = Field(
        default="default",
        description="Type of message parser to use. Currently supported: 'default'",
        validation_alias="MESSAGE_PARSER_TYPE",
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production" and bool(self.project_id) and bool(self.bucket_id)

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return not self.is_production


class AssistantConfig(BaseModel):
    """Configuration for an OpenAI assistant instance."""

    assistant_id: str = Field(default="", description="Assistant ID (empty during registration)")
    assistant_name: str
    initial_message: str
    code_interpreter: bool = Field(default=False)
    file_search: bool = Field(default=False, description="Enable file search (vector store) capability")
    function_names: list[str] = Field(default_factory=list)
