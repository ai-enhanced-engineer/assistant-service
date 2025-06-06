# ruff: noqa: E402
import sys
import types

import pytest
from openai.types.beta.threads import Message, TextContentBlock
from openai.types.beta.threads.text import Text

sys.modules.setdefault("chainlit", types.ModuleType("chainlit"))
sys.modules["chainlit"].Message = object
sys.modules["chainlit"].Step = object
sys.modules["chainlit"].context = types.SimpleNamespace(current_step=types.SimpleNamespace(id="parent"))
from assistant_engine.processors import ThreadMessageProcessor


@pytest.mark.asyncio
async def test__processor_updates_message_if_already_in_message_references():
    processor = ThreadMessageProcessor()

    thread_message = Message(
        id="12340",
        content=[TextContentBlock(text=Text(annotations=[], value="test message"), type="text")],
        created_at=1234,
        file_ids=[],
        object="thread.message",
        role="user",
        thread_id="thread_123",
        status="completed",
    )

    msg_returned_once = await processor.process(thread_message=thread_message)
    # First time this message is seen, so we should send the message to the UI for the first time.
    assert processor.send_message is True
    # Save message id to make sure it is preserved and use it below to assert.
    msg_returned_once_id = msg_returned_once.id

    msg_returned_twice = await processor.process(thread_message=thread_message)
    # The message has already been seen, so we should update it instead of sending it.
    assert processor.send_message is False
    # Verify hat it is the same message
    assert msg_returned_once_id == msg_returned_twice.id


@pytest.mark.asyncio
async def test__processor_returns_none_when_content_empty():
    processor = ThreadMessageProcessor()

    thread_message = Message(
        id="empty01",
        content=[],
        created_at=1234,
        file_ids=[],
        object="thread.message",
        role="assistant",
        thread_id="thread_123",
        status="completed",
    )

    result = await processor.process(thread_message=thread_message)

    assert result is None
