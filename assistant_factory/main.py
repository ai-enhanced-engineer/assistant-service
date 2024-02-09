import asyncio

from assistant_factory.client_spec.leogv.assistants import personal_assistant
from assistant_factory.create_assistant import create_assistant, upload_files_for_retrieval
from assistant_factory.tool_builder import ToolBuilder
from botbrew_commons.data_models import EngineAssistantConfig
from botbrew_commons.repositories import GCPConfigRepository

BUCKET_ID = "botbrewers"
PROJECT_ID = "botbrewers"

if __name__ == "__main__":
    # Define tools to be used
    tool_builder = ToolBuilder(code_interpreter=True, retrieval=True, functions=personal_assistant.functions)
    tools = tool_builder.build_tools()
    # RETRIEVAL: Upload necessary files
    file_id = None
    if tool_builder.retrieval:
        file_id = asyncio.run(upload_files_for_retrieval(path_to_file=personal_assistant.file_paths[0]))

    assistant = asyncio.run(
        create_assistant(
            name=personal_assistant.assistant_name,
            instructions=personal_assistant.instructions,
            a_tools=tools,
            model=personal_assistant.model,
            file_ids=[file_id],
        )
    )

    print(f"Created assistant with is: {assistant.id}")

    assistant_config = EngineAssistantConfig(
        assistant_id=assistant.id,
        code_interpreter=personal_assistant.code_interpreter,
        retrieval=personal_assistant.retrieval,
        function_names=[function["name"] for function in personal_assistant.functions],
    )

    config_repo = GCPConfigRepository(
        client_id=personal_assistant.client_id, project_id=PROJECT_ID, bucket_name=BUCKET_ID
    )
    config_repo.write_config(assistant_config)
