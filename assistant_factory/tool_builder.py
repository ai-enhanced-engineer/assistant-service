from typing import Type, Union

from langchain_core.utils.function_calling import convert_to_openai_function
from pydantic import BaseModel


class CodeInterpreter(BaseModel):
    type: str = "code_interpreter"


class Retrieval(BaseModel):
    type: str = "retrieval"


class Function(BaseModel):
    type: str = "function"
    function: dict


class ToolBuilder:
    def __init__(
        self,
        code_interpreter: bool = False,
        retrieval: bool = False,
        functions: Union[list[dict] | list[Type[BaseModel]]] = None,
    ):
        self.code_interpreter = code_interpreter
        self.retrieval = retrieval
        self.functions = functions

    def build_tools(self) -> list[dict]:
        final_tools = []
        if self.code_interpreter:
            final_tools.append(CodeInterpreter().model_dump())
        if self.retrieval:
            final_tools.append(Retrieval().model_dump())
        if self.functions:
            for function_raw in self.functions:
                if isinstance(function_raw, dict):
                    function_model = Function(function=function_raw)
                else:
                    function_model = Function(function=convert_to_openai_function(function_raw))

                final_tools.append(function_model.model_dump())

        return final_tools
