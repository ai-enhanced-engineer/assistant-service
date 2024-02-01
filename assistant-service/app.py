import logging
import os

import chainlit as cl
from openai import AsyncOpenAI
from openai.types.beta.threads import (
    MessageContentText,
    ThreadMessage,
)

logger = logging.getLogger("Assistant")
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

API_KEY = os.environ.get("OPENAI_API_KEY")
ASSISTANT_ID = os.environ.get("ASSISTANT_ID")

client = AsyncOpenAI(api_key=API_KEY)


async def process_thread_message(
    message_references: dict[str, cl.Message], thread_message: ThreadMessage
):
    for idx, content_message in enumerate(thread_message.content):
        message_id = thread_message.id + str(idx)
        if isinstance(content_message, MessageContentText):
            if message_id in message_references:
                msg = message_references[message_id]
                msg.content = content_message.text.value
                await msg.update()
            else:
                message_references[message_id] = cl.Message(
                    author=thread_message.role, content=content_message.text.value
                )
                await message_references[message_id].send()
        else:
            print("unknown message type", type(content_message))


@cl.on_chat_start
async def start_chat():
    thread = await client.beta.threads.create()
    logger.info(f"Created thread: {thread.id}")
    cl.user_session.set("thread", thread)
    await cl.Message(
        author="assistant",
        content="Ask me some meditation questions!",
        disable_feedback=True,
    ).send()


@cl.step(name="Assistant", type="run", root=True)
async def run(thread_id: str, human_query: str):
    # Add the message to the thread
    init_message = await client.beta.threads.messages.create(
        thread_id=thread_id, role="user", content=human_query
    )
    logging.info(f"Created message: {init_message.id}, content:{init_message.content}")

    # Create the run
    run = await client.beta.threads.runs.create(
        thread_id=thread_id, assistant_id=ASSISTANT_ID
    )
    logging.info(f"Created run: {run.id}")

    message_references = {}  # type: dict[str, cl.Message]
    # While to periodically check for updates
    while True:
        run = await client.beta.threads.runs.retrieve(
            thread_id=thread_id, run_id=run.id
        )
        logging.info(f"Retrieved run: {run.id}")

        # Fetch the run steps
        run_steps = await client.beta.threads.runs.steps.list(
            thread_id=thread_id, run_id=run.id, order="asc"
        )

        for step in run_steps.data:
            logging.info(f"Step: {step.step_details}")
            # Fetch step details
            run_step = await client.beta.threads.runs.steps.retrieve(
                thread_id=thread_id, run_id=run.id, step_id=step.id
            )
            step_details = run_step.step_details
            # Update step content in the Chainlit UI
            if step_details.type == "message_creation":
                thread_message = await client.beta.threads.messages.retrieve(
                    message_id=step_details.message_creation.message_id,
                    thread_id=thread_id,
                )
                await process_thread_message(message_references, thread_message)

        await cl.sleep(2)  # Refresh every 2 seconds
        if run.status in ["cancelled", "failed", "completed", "expired"]:
            break


@cl.on_message
async def on_message(message_from_ui: cl.Message):
    thread = cl.user_session.get("thread")  # type: Thread
    await run(thread_id=thread.id, human_query=message_from_ui.content)
