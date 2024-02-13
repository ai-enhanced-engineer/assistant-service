import asyncio

from assistant_factory.client_spec.leogv.assistants import ClientAssistantConfig
from assistant_factory.create_assistant import create_assistant, upload_files_for_retrieval
from assistant_factory.tool_builder import ToolBuilder
from botbrew_commons.data_models import EngineAssistantConfig
from botbrew_commons.repositories import GCPConfigRepository

BUCKET_ID = "botbrewers"
PROJECT_ID = "botbrewers"


def build_tools(assistant_config: ClientAssistantConfig):
    # Define tools to be used
    tool_builder = ToolBuilder(code_interpreter=True, retrieval=True, functions=assistant_config.functions)
    return tool_builder.build_tools()


def upload_files(assistant_config: ClientAssistantConfig, retrieval: bool):
    # RETRIEVAL: Upload necessary files
    file_id = None
    if retrieval:
        file_id = asyncio.run(upload_files_for_retrieval(path_to_file=assistant_config.file_paths[0]))
    return file_id


def create_new_assistant(assistant_config: ClientAssistantConfig, fileid: str, a_tools: list[dict]):
    assistant_name = f"{assistant_config.client_id}-{assistant_config.assistant_name}"
    assistant = asyncio.run(
        create_assistant(
            name=assistant_name,
            instructions=assistant_config.instructions,
            a_tools=a_tools,
            model=assistant_config.model,
            file_ids=[fileid],
        )
    )

    print(f"Created assistant with is: {assistant.id}")

    return assistant.id


def persist_config(assistant_config: ClientAssistantConfig, assistant_id: str):
    assistant_config = EngineAssistantConfig(
        assistant_id=assistant_id,
        initial_messages=assistant_config.initial_messages,
        code_interpreter=assistant_config.code_interpreter,
        retrieval=assistant_config.retrieval,
        function_names=[function["name"] for function in assistant_config.functions],
    )

    config_repo = GCPConfigRepository(
        client_id=personal_assistant.client_id, project_id=PROJECT_ID, bucket_name=BUCKET_ID
    )
    config_repo.write_config(assistant_config)


if __name__ == "__main__":
    # import client specific assistant configuration
    from assistant_factory.client_spec.leogv.assistants import personal_assistant

    tools = build_tools(personal_assistant)
    file_id = upload_files(personal_assistant, personal_assistant.retrieval)
    a_id = create_new_assistant(personal_assistant, file_id, tools)
    persist_config(personal_assistant, a_id)
