import logging

import chainlit as cl
from openai.types.beta.threads import (
    MessageContentText,
    ThreadMessage,
)

logger = logging.getLogger(__name__)


class ThreadProcessor:
    def __init__(self):
        self._message_references: dict[str, cl.Message] = {}

    async def process(self, thread_message: ThreadMessage):
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
                    await msg.update()
                else:
                    self._message_references[message_id] = cl.Message(
                        author=thread_message.role, content=content_message.text.value
                    )
                    await self._message_references[message_id].send()
            else:
                logger.warning("unknown message type", type(content_message))
