from typing import Dict, List
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


class ChatRequest(BaseModel):
    thread_id: str
    message: str


threads: Dict[str, List[str]] = {}


@app.get("/start")
async def start_conversation():
    thread_id = str(uuid4())
    threads[thread_id] = []
    return {"thread_id": thread_id}


@app.post("/chat")
async def chat(request: ChatRequest):
    if request.thread_id not in threads:
        raise HTTPException(status_code=404, detail="Unknown thread")
    threads[request.thread_id].append(request.message)
    response = f"You said: {request.message}"
    threads[request.thread_id].append(response)
    return {"response": response}
