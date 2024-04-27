from types import FunctionType

weather_search_dict = {
    "name": "get_current_weather",
    "description": "Get the current weather",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city and state, e.g. San Francisco, CA",
            },
            "format": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "The temperature unit to use. Infer this from the users location.",
            },
        },
        "required": ["location", "format"],
    },
}

n_day_weather_forecast_dict = {
    "name": "get_n_day_weather_forecast",
    "description": "Get an N-day weather forecast",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city and state, e.g. San Francisco, CA",
            },
            "format": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "The temperature unit to use. Infer this from the users location.",
            },
            "num_days": {
                "type": "integer",
                "description": "The number of days to forecast",
            },
        },
        "required": ["location", "format", "num_days"],
    },
}


def get_current_weather(location: str, format: str):
    # return dummy weather
    return "The current weather in {} is {} degrees {}".format(location, 20, format)


def get_n_day_weather_forecast(location: str, format: str, num_days: int):
    # return dummy weather
    return "The weather forecast for the next {} days in {} is {} degrees {}".format(num_days, location, 20, format)


TOOL_MAP: dict[str:FunctionType] = {
    "get_current_weather": get_current_weather,
    "get_n_day_weather_forecast": get_n_day_weather_forecast,
}
