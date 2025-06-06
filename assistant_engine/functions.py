"""
This file is an empty placeholder that is replaced by specific client implementations if the function calling feature
was activated for a specific assistant. The variable TOOL_MAP bellow is a key value map where the name of the function
is used as a string key and the value is a programmatic reference to the function to be invoked. See examples in:
'assistant_factory/client_spec/{CLIENT_ID}/functions.py'
"""

from types import FunctionType

TOOL_MAP: dict[str:FunctionType] = {}
