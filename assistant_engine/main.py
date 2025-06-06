import json

import chainlit as cl
from config import build_engine_config
from functions import TOOL_MAP
from openai import AsyncOpenAI
from processors import ThreadMessageProcessor, ToolProcessor

from botbrew_commons.data_models import BaseConfig
from botbrew_commons.repositories import GCPConfigRepository, GCPSecretRepository

from .bb_logging import get_logger

logger = get_logger("MAIN")

base_config = BaseConfig()  # Loads variables from the environment
secret_repository = GCPSecretRepository(project_id=base_config.project_id, client_id=base_config.client_id)
config_repository = GCPConfigRepository(
    client_id=base_config.client_id, project_id=base_config.project_id, bucket_name=base_config.bucket_id
)
engine_config = build_engine_config(secret_repository, config_repository)
logger.info(f"Booting with config: {engine_config}")

client = AsyncOpenAI(api_key=engine_config.openai_apikey)


@cl.on_chat_start
async def start_chat():
    thread = await client.beta.threads.create()
    logger.info(f"### Starting chat with thread:: {thread.id} ###")
    cl.user_session.set("thread", thread)
    await cl.Message(
        author=engine_config.assistant_name,
        content=engine_config.initial_message,
        disable_feedback=True,
    ).send()


class DictToObject:
    def __init__(self, dictionary):
        for key, value in dictionary.items():
            if isinstance(value, dict):
                setattr(self, key, DictToObject(value))
            else:
                setattr(self, key, value)

    def __str__(self):
        return "\n".join(f"{key}: {value}" for key, value in self.__dict__.items())


@cl.step(name="Assistant", type="run", root=True)
async def run(thread_id: str, human_query: str):
    # Add the message to the thread
    init_message = await client.beta.threads.messages.create(thread_id=thread_id, role="user", content=human_query)
    logger.info(f"### Received user message with content:{init_message.content} ###")

    # Create the run stream
    stream = await client.beta.threads.runs.create(
        thread_id=thread_id, assistant_id=engine_config.assistant_id, stream=True
    )

    thread_processor = ThreadMessageProcessor()
    tool_processor = ToolProcessor()

    run_id = None

    async for event in stream:
        logger.info(f"## Stream event received: {event.event} ##")

        if event.event == "thread.run.created":
            run_id = event.data.id
            logger.info(f"Created run: {run_id}")
            continue

        if event.event.startswith("thread.message"):
            thread_message = await client.beta.threads.messages.retrieve(message_id=event.data.id, thread_id=thread_id)
            processed_message = await thread_processor.process(thread_message)
            if thread_processor.send_message:
                await processed_message.send()
            else:
                await processed_message.update()
            continue

        if event.event.startswith("thread.run.step") and run_id:
            run_step = await client.beta.threads.runs.steps.retrieve(
                thread_id=thread_id, run_id=run_id, step_id=event.data.id
            )
            step_details = run_step.step_details
            logger.info(f"Step details {step_details}")

            if step_details.type == "message_creation":
                thread_message = await client.beta.threads.messages.retrieve(
                    message_id=step_details.message_creation.message_id,
                    thread_id=thread_id,
                )
                processed_message = await thread_processor.process(thread_message)
                if thread_processor.send_message:
                    await processed_message.send()
                else:
                    await processed_message.update()

            if step_details.type == "tool_calls":
                for tool_call in step_details.tool_calls:
                    if isinstance(tool_call, dict):
                        tool_call = DictToObject(tool_call)

                    if tool_call.type == "retrieval":
                        logger.info("# Using RETRIEVAL #")
                        cl_step = await tool_processor.process_tool_call(
                            step=run_step,
                            tool_call=tool_call,
                            name=tool_call.type,
                            t_input="Retrieving information",
                            t_output="Retrieved information",
                        )

                        if tool_processor.update:
                            await cl_step.update()
                        else:
                            await cl_step.send()

                    elif tool_call.type == "function":
                        logger.info("# Using FUNCTION #")
                        logger.info(tool_call)
                        function_name = tool_call.function.name
                        logger.info(function_name)  # TODO: Validate that function name is in TOOL_MAP
                        function_args = json.loads(tool_call.function.arguments)
                        function_output = TOOL_MAP[function_name](**json.loads(tool_call.function.arguments))

                        cl_step = await tool_processor.process_tool_call(
                            step=run_step,
                            tool_call=tool_call,
                            name=function_name,
                            t_input=function_args,
                            t_output=function_output,
                            show_input="json",
                        )

                        if tool_processor.update:
                            await cl_step.update()
                        else:
                            await cl_step.send()
            continue

        if event.event == "thread.run.requires_action" and run_id:
            logger.info(
                f"Submitting tool outputs for thread: {thread_id}, run: {run_id}, "
                f"outputs: {tool_processor.tool_outputs}"
            )
            await client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run_id,
                tool_outputs=tool_processor.tool_outputs.values(),
            )
            continue


@cl.on_message
async def on_message(message_from_ui: cl.Message):
    thread = cl.user_session.get("thread")  # type: Thread
    await run(thread_id=thread.id, human_query=message_from_ui.content)
