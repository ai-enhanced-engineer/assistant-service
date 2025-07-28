from langchain_core.utils.function_calling import convert_to_openai_function
from pydantic import BaseModel

from assistant_factory.tool_builder import ToolBuilder


def test__tool_builder_respects_openai_format_for_all_tools():
    test_tools_all = [
        {"type": "code_interpreter"},
        {"type": "retrieval"},
        {
            "type": "function",
            "function": {
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
            },
        },
        {
            "type": "function",
            "function": {
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
            },
        },
    ]

    weather_search = {
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

    n_day_weather_forecast = {
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

    tool_builder = ToolBuilder(
        code_interpreter=True, retrieval=True, functions=[weather_search, n_day_weather_forecast]
    )
    final_tools = tool_builder.build_tools()
    assert test_tools_all == final_tools


def test__tool_builder_does_not_add_functions_if_not_passed():
    test_tools_no_functions = [{"type": "code_interpreter"}, {"type": "retrieval"}]
    tool_builder = ToolBuilder(code_interpreter=True, retrieval=True)
    final_tools = tool_builder.build_tools()
    print(final_tools)
    assert test_tools_no_functions == final_tools


def test__tool_builder_does_not_add_code_interpreter_if_not_passed():
    test_tools_all = [
        {"type": "retrieval"},
        {
            "type": "function",
            "function": {
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
            },
        },
    ]

    weather_search = {
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

    tool_builder = ToolBuilder(retrieval=True, functions=[weather_search])
    final_tools = tool_builder.build_tools()
    assert test_tools_all == final_tools


class Multiply(BaseModel):
    x: int
    y: int


def test__tool_builder_handles_mixed_function_input_first_model():
    weather_search = {
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

    expected_tools = [
        {"type": "retrieval"},
        {"type": "function", "function": convert_to_openai_function(Multiply)},
        {"type": "function", "function": weather_search},
    ]

    tool_builder = ToolBuilder(retrieval=True, functions=[Multiply, weather_search])
    assert tool_builder.build_tools() == expected_tools


def test__tool_builder_handles_mixed_function_input_first_dict():
    weather_search = {
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

    expected_tools = [
        {"type": "retrieval"},
        {"type": "function", "function": weather_search},
        {"type": "function", "function": convert_to_openai_function(Multiply)},
    ]

    tool_builder = ToolBuilder(retrieval=True, functions=[weather_search, Multiply])
    assert tool_builder.build_tools() == expected_tools
