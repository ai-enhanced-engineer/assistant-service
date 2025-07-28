"""Configuration models for the assistant engine."""

from typing import Optional

from pydantic import BaseModel, Field


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