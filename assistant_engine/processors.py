import logging
from datetime import datetime
from typing import Any, Union

import chainlit as cl
from openai.types.beta.threads import (
    MessageContentText,
    ThreadMessage,
)
from openai.types.beta.threads.runs import RunStep
from openai.types.beta.threads.runs.tool_calls_step_details import ToolCall

logger = logging.getLogger(__name__)


class ToolProcessor:
    def __init__(self):
        self.step_references: dict[str, cl.Step] = {}
        self.update = False

    async def process_tool_call(
        self,
        step: RunStep,
        tool_call: ToolCall,
        name: str,
        t_input: Any,
        t_output: Any,
        show_input: Union[bool, str] = None,
    ):
        logger.info(f"DEBUG: Step references: {self.step_references}")
        cl_step = None
        if tool_call.id not in self.step_references:
            cl_step = cl.Step(
                name=name,
                type="tool",
                parent_id=cl.context.current_step.id,
                show_input=show_input,
            )
            self.step_references[tool_call.id] = cl_step

        else:
            self.update = True
            cl_step = self.step_references[tool_call.id]

        if step.created_at:
            cl_step.start = datetime.fromtimestamp(step.created_at).isoformat()
        if step.completed_at:
            cl_step.end = datetime.fromtimestamp(step.completed_at).isoformat()

        cl_step.input = t_input
        cl_step.output = t_output

        return cl_step


class ThreadMessageProcessor:
    """Process thread message."""

    def __init__(self):
        self._message_references: dict[str, cl.Message] = {}
        self.send_message = True

    async def process(self, thread_message: ThreadMessage) -> cl.Message:
        """Process the message thread."""
        logger.info(f"Processing thread message: {thread_message.id} with content: {thread_message.content}")
        for idx, content_message in enumerate(thread_message.content):
            message_id = thread_message.id + str(idx)
            if isinstance(content_message, MessageContentText):
                if message_id in self._message_references:
                    msg = self._message_references[message_id]
                    msg.content = content_message.text.value
                    self.send_message = False
                    return msg
                else:
                    self._message_references[message_id] = cl.Message(
                        author=thread_message.role, content=content_message.text.value
                    )
                    return self._message_references[message_id]
            else:
                logger.warning("unknown message type", type(content_message))
