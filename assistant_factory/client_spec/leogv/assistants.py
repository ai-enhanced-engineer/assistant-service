from typing import Optional

from pydantic import BaseModel

from assistant_factory.client_spec.leogv.functions import n_day_weather_forecast_dict, weather_search_dict
from assistant_factory.client_spec.leogv.instructions import PERSONAL_ASSISTANT


class ClientAssistantConfig(BaseModel):
    client_id: str
    assistant_name: str
    instructions: str
    model: str
    # Tools
    code_interpreter: Optional[bool]
    functions: Optional[list[dict]]
    retrieval: Optional[bool]
    file_paths: Optional[list[str]]


personal_assistant = ClientAssistantConfig(
    client_id="leogv",
    assistant_name="Personal assistant",
    instructions=PERSONAL_ASSISTANT,
    model="gpt-4-1106-preview",
    code_interpreter=True,
    functions=[weather_search_dict, n_day_weather_forecast_dict],
    retrieval=True,
    file_paths=["Resume_LGV_Oct_2023.pdf"],
)
