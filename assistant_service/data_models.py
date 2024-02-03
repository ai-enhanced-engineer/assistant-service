from pydantic import BaseModel


class BBConfig(BaseModel):
    assistant_id: str
