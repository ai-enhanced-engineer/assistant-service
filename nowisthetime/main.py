import logging
import os
from time import sleep

import openai
import utilities
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from packaging import version
from pydantic import BaseModel

logger = logging.getLogger(__name__)
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

# Check OpenAI version is correct
required_version = version.parse("1.1.1")
current_version = version.parse(openai.__version__)
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
if current_version < required_version:
    raise ValueError(
        f"Error: OpenAI version {openai.__version__}" " is less than the required version 1.1.1"
    )
else:
    logger.info("OpenAI version is compatible.")

app = FastAPI()

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Create new assistant or load existing
assistant_id = utilities.create_assistant(client)


class ChatRequest(BaseModel):
    thread_id: str
    message: str


@app.get("/")
async def root():
    return {"status": "healthy"}


@app.get("/start")
async def start_conversation():
    logger.info("Starting a new conversation...")
    thread = client.beta.threads.create()
    logger.info(f"New thread created with ID: {thread.id}")
    return {"thread_id": thread.id}


@app.post("/chat")
async def chat(chat_request: ChatRequest):
    thread_id = chat_request.thread_id
    user_input = chat_request.message

    if not thread_id:
        logger.error("Error: Missing thread_id")
        raise HTTPException(status_code=400, detail="Missing thread_id")

    logger.info(f"Received message: {user_input} for thread ID: {thread_id}")

    # Add the user's message to the thread
    client.beta.threads.messages.create(thread_id=thread_id, role="user", content=user_input)

    # Run the Assistant
    run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant_id)

    # Wait for the run to be completed
    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        logger.info(f"Run status: {run_status.status}")
        if run_status.status == "completed":
            break
        sleep(1)  # Wait for a second before checking again

    # Retrieve and return the latest message from the assistant
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    response = messages.data[0].content[0].text.value

    logger.info(f"Assistant response: {response}")
    return JSONResponse(content={"response": response})


# Run server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
