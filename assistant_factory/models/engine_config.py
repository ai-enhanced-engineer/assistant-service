"""Configuration model for persisting assistant configuration."""

from typing import Optional

from pydantic import BaseModel, Field


class EngineAssistantConfig(BaseModel):
    """Configuration for an OpenAI assistant to be used by the engine.
    
    This is a duplicate of the engine's model to avoid cross-application dependencies.
    """
    
    assistant_id: str
    assistant_name: str
    initial_message: str
    code_interpreter: bool = Field(default=False)
    retrieval: bool = Field(default=False)
    function_names: list[str] = Field(default_factory=list)
    # Secrets are not included here as they're managed separately
    openai_apikey: Optional[str] = Field(default=None)