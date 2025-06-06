from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Union

from openai.types.beta.threads import TextContentBlock
from openai.types.beta.threads.message import Message
from openai.types.beta.threads.runs import RunStep, ToolCall

from .bb_logging import get_logger

logger = get_logger("PROCESSORS")


@dataclass
class StepData:
    name: Optional[str] = None
    type: Optional[str] = None
    parent_id: Optional[str] = None
    show_input: Optional[Union[bool, str]] = None
    start: Optional[str] = None
    end: Optional[str] = None
    input: Any = None
    output: Any = None


@dataclass
class MessageData:
    author: Optional[str] = None
    content: Optional[str] = None
    id: Optional[str] = None


class ToolProcessor:
    def __init__(self):
        self.step_references: dict[str, StepData] = {}
        self.update = False
        self.tool_outputs: dict = {}

    async def process_tool_call(
        self,
        step: RunStep,
        tool_call: ToolCall,
        name: str,
        t_input: Any,
        t_output: Any,
        show_input: Union[bool, str] = None,
    ):
        step_data = None
        if tool_call.id not in self.step_references:
            step_data = StepData(
                name=name,
                type="tool",
                show_input=show_input,
            )
            self.step_references[tool_call.id] = step_data

        else:
            self.update = True
            step_data = self.step_references[tool_call.id]

        if step.created_at:
            step_data.start = datetime.fromtimestamp(step.created_at).isoformat()
        if step.completed_at:
            step_data.end = datetime.fromtimestamp(step.completed_at).isoformat()

        step_data.input = t_input
        step_data.output = t_output

        self.tool_outputs[tool_call.id] = {"output": t_output, "tool_call_id": tool_call.id}
        return step_data


class ThreadMessageProcessor:
    """Process thread message."""

    def __init__(self):
        self._message_references: dict[str, MessageData] = {}
        self.send_message = True

    async def process(self, thread_message: Message) -> MessageData | None:
        """Process the message thread."""
        logger.info(f"### {thread_message.content} ###")

        if not thread_message.content:
            logger.info("Received thread message with no content. Skipping message creation")
            return None

        if thread_message.content[0].text != "":
            log_message = f"Processing thread message: {thread_message.id} with content: {thread_message.content}"
        else:
            log_message = "Message has not been generated yet..."

        logger.info(log_message)

        for idx, content_message in enumerate(thread_message.content):
            message_id = thread_message.id + str(idx)
            if isinstance(content_message, TextContentBlock):
                if message_id in self._message_references:
                    msg = self._message_references[message_id]
                    msg.content = content_message.text.value
                    self.send_message = False
                    return msg
                else:
                    self._message_references[message_id] = MessageData(
                        author=thread_message.role,
                        content=content_message.text.value,
                        id=message_id,
                    )
                    return self._message_references[message_id]
            else:
                logger.warning("unknown message type", type(content_message))
