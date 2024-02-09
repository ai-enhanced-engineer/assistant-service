import asyncio
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from openai.types.beta import Assistant

from assistant_factory.tool_builder import ToolBuilder
from commons.data_models.config import AssistantConfig, BaseConfig
from commons.repositories.configs import GCPConfigRepository

load_dotenv()

INSTRUCTIONS = """You are Leopoldo's personal assistant. Your mission is to provide information on Leo's background
based on the knowledge base defined in the attached document.

You are a personal math tutor. Write and run code to answer math questions.
Enclose math expressions in $$ (this is helpful to display latex). Example:
```
Given a formula below $$ s = ut + \frac{1}{2}at^{2} $$ Calculate the value of $s$ when $u = 10\frac{m}{s}$ and $a = 2\
frac{m}{s^{2}}$ at $t = 1s$
```

You can also answer weather questions!
"""

api_key = os.environ.get("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=api_key)


# tool_map = {
#     "get_current_weather": get_current_weather,
#     "get_n_day_weather_forecast": get_n_day_weather_forecast,
# }


async def create_assistant(name: str, instructions: str, a_tools: list[dict], model: str, file_ids: list) -> Assistant:
    print("Creating assistant!")
    return await client.beta.assistants.create(
        name=name,
        instructions=instructions,
        tools=a_tools,
        model=model,
        file_ids=file_ids,
    )


async def upload_files_for_retrieval(path_to_file: str):
    # file = await client.files.create(file=open(path_to_file, "rb"), purpose="assistants")
    # return file.id
    return path_to_file


if __name__ == "__main__":
    from assistant_factory.client_functions import n_day_weather_forecast_dict, weather_search_dict

    base_config = BaseConfig()  # Loads variables from the environment

    # Define tools to be used
    tool_builder = ToolBuilder(
        code_interpreter=True, retrieval=True, functions=[weather_search_dict, n_day_weather_forecast_dict]
    )
    tools = tool_builder.build_tools()
    # RETRIEVAL: Upload necessary files
    file_id = None
    if tool_builder.retrieval:
        file_id = asyncio.run(upload_files_for_retrieval(path_to_file="Resume_LGV_Oct_2023.pdf"))

    assistant = asyncio.run(
        create_assistant(
            name="Leo's personal assistant",
            instructions=INSTRUCTIONS,
            a_tools=tools,
            model="gpt-4-1106-preview",
            file_ids=[file_id],
        )
    )

    print(f"Created assistant with is: {assistant.id}")

    assistant_config = AssistantConfig(assistant_id=assistant.id)
    config_repo = GCPConfigRepository(base_config.client_id, base_config.bucket_id)
    config_repo.write_config(assistant_config)
