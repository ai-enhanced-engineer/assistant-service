"""Message data entity for thread messages."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class MessageData:
    """Represents a single message extracted from a thread.

    Attributes:
        author: Role of the message sender.
        content: Textual content of the message.
        id: Unique identifier for the message content block.
    """

    author: Optional[str] = None
    content: Optional[str] = None
    id: Optional[str] = None
