import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from openai.types.beta import Assistant


def _get_client() -> AsyncOpenAI:
    """Create an AsyncOpenAI client using env configuration."""
    load_dotenv()
    api_key = os.environ.get("OPENAI_API_KEY")
    return AsyncOpenAI(api_key=api_key)


async def create_assistant(name: str, instructions: str, a_tools: list[dict], model: str, file_ids: list) -> Assistant:
    print("Creating assistant!")
    client = _get_client()
    return await client.beta.assistants.create(
        name=name,
        instructions=instructions,
        tools=a_tools,
        model=model,
        file_ids=file_ids,
    )


async def upload_files_for_retrieval(path_to_file: str):
    # Todo: Make this upload a list of files
    client = _get_client()
    file = await client.files.create(file=open(path_to_file, "rb"), purpose="assistants")
    return file.id
