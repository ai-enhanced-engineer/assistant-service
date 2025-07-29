"""Configuration models for the assistant engine."""

from typing import Literal, Optional

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
    client_id: str = Field(
        default="",
        description="Client ID for multi-tenant support",
        validation_alias="CLIENT_ID",
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production" and bool(self.project_id) and bool(self.bucket_id)

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return not self.is_production


class EngineAssistantConfig(BaseModel):
    """Configuration for an OpenAI assistant instance."""

    assistant_id: str
    assistant_name: str
    initial_message: str
    code_interpreter: bool = Field(default=False)
    retrieval: bool = Field(default=False)
    function_names: list[str] = Field(default_factory=list)
    # Secrets
    openai_apikey: Optional[str] = Field(default=None)
