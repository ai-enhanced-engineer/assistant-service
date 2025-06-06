import os
from typing import Optional

from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAIError
from openai.types.beta import Assistant

load_dotenv()

_client: Optional[AsyncOpenAI] = None


def get_client() -> AsyncOpenAI:
    """Return a cached ``AsyncOpenAI`` client.

    The client is only created when first needed to avoid errors at import time
    if the ``OPENAI_API_KEY`` environment variable is not set.
    """

    global _client
    if _client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key is None:
            raise OpenAIError("OpenAI API key not configured. Set the OPENAI_API_KEY environment variable.")
        _client = AsyncOpenAI(api_key=api_key)
    return _client


async def create_assistant(name: str, instructions: str, a_tools: list[dict], model: str, file_ids: list) -> Assistant:
    """Create a new assistant using the OpenAI API."""

    print("Creating assistant!")
    client = get_client()
    return await client.beta.assistants.create(
        name=name,
        instructions=instructions,
        tools=a_tools,
        model=model,
        file_ids=file_ids,
    )


async def upload_files_for_retrieval(path_to_file: str):
    """Upload a file for retrieval."""

    client = get_client()
    file = await client.files.create(file=open(path_to_file, "rb"), purpose="assistants")
    return file.id
