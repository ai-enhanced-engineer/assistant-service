import logging

import chainlit as cl
from openai.types.beta.threads import (
    MessageContentText,
    ThreadMessage,
)

all = ["ThreadMessageProcessor"]

logger = logging.getLogger(__name__)


class ThreadMessageProcessor:
    """Process thread message."""

    def __init__(self):
        self._message_references: dict[str, cl.Message] = {}
        self.send_message = True

    async def process(self, thread_message: ThreadMessage) -> cl.Message:
        """Process the message thread."""
        logger.info(
            f"Processing thread message: {thread_message.id} with content: {thread_message.content}"
        )
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
