from assistant_factory.client_spec.leogv.functions import n_day_weather_forecast_dict, weather_search_dict
from assistant_factory.client_spec.leogv.instructions import PERSONAL_ASSISTANT
from assistant_factory.config import ClientAssistantConfig

personal_assistant = ClientAssistantConfig(
    client_id="leogv",
    assistant_name="personal-assistant",
    instructions=PERSONAL_ASSISTANT,
    initial_message="Hello! I'm Leopoldo's personal assistant I can answer any question regarding Leo's professional "
    "life. I'm happy to help!",
    model="gpt-4-1106-preview",
    functions=[weather_search_dict, n_day_weather_forecast_dict],
    retrieval=True,
    file_paths=["Resume_LGV_Oct_2023.pdf"],
)
