"""Configuration models for assistant registration."""

from typing import Any, Optional

from pydantic import Field

from ai_assistant_service.entities.config import AssistantConfig


class AssistantRegistrationConfig(AssistantConfig):
    """Configuration for registering a new OpenAI assistant.

    Extends AssistantConfig with registration-specific fields.
    The assistant_id will be populated after successful registration.
    """

    # Registration-specific fields only
    instructions: str = Field(description="System instructions for the assistant")
    model: str = Field(default="gpt-4-turbo-preview", description="OpenAI model to use")
    functions_module: Optional[str] = Field(default=None, description="Python module containing functions")
    function_definitions: list[dict[str, Any]] = Field(
        default_factory=list, description="Raw OpenAI function definitions"
    )

    # Vector store support
    vector_store_name: Optional[str] = Field(default=None, description="Name for the vector store")
    vector_store_file_paths: list[str] = Field(default_factory=list, description="Files to upload to vector store")

    def to_assistant_config(self, assistant_id: str) -> AssistantConfig:
        """Convert registration config to runtime AssistantConfig.

        Args:
            assistant_id: The ID assigned by OpenAI after registration

        Returns:
            AssistantConfig ready for use with the service
        """
        return AssistantConfig(
            assistant_id=assistant_id,
            assistant_name=self.assistant_name,
            initial_message=self.initial_message,
            code_interpreter=self.code_interpreter,
            file_search=bool(self.vector_store_file_paths),  # Enable if files are provided
            function_names=self.function_names,
        )

    def to_json_schema(self) -> dict[str, Any]:
        """Generate JSON schema for configuration files.

        Returns:
            JSON schema dict that can be used for validation
        """
        return self.model_json_schema()
