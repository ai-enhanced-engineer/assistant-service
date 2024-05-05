from typing import Optional

from pydantic import BaseModel


class ClientAssistantConfig(BaseModel):
    client_id: str
    assistant_name: str = "Assistant"
    instructions: str
    initial_message: str = "Ask me some questions"
    model: str
    # Tools
    code_interpreter: Optional[bool] = False
    functions: Optional[list[dict]] = None
    retrieval: Optional[bool] = False
    file_paths: Optional[list[str]] = None
