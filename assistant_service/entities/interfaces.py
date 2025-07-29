"""Abstract base classes defining interfaces for assistant service components."""

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Optional

from fastapi import WebSocket
from openai.types.beta.threads.message import Message

from .message_data import MessageData


class IOrchestrator(ABC):
    """Interface for OpenAI orchestration."""

    @abstractmethod
    async def process_run(self, thread_id: str, message: str) -> list[str]:
        """Process a single run and return responses.

        Args:
            thread_id: The thread ID for the conversation
            message: The user's message

        Returns:
            List of assistant responses
        """
        pass

    @abstractmethod
    def process_run_stream(self, thread_id: str, message: str) -> AsyncGenerator[Any, None]:
        """Process a run with streaming responses.

        Args:
            thread_id: The thread ID for the conversation
            message: The user's message

        Yields:
            Stream events from the assistant
        """
        pass


class IStreamHandler(ABC):
    """Interface for stream handling."""

    @abstractmethod
    async def handle_connection(self, websocket: WebSocket) -> None:
        """Handle a WebSocket connection for streaming.

        Args:
            websocket: The WebSocket connection to handle
        """
        pass


class IToolExecutor(ABC):
    """Interface for tool execution."""

    @abstractmethod
    def execute_tool(self, tool_name: str, tool_args: str | dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool and return the result.

        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments as JSON string or dict
            context: Execution context (thread_id, run_id, etc.)

        Returns:
            Dict with tool_call_id and output
        """
        pass


class IMessageParser(ABC):
    """Interface for message parsing."""

    @abstractmethod
    async def process(self, message: Message) -> Optional[MessageData]:
        """Process a thread message.

        Args:
            message: The OpenAI message to process

        Returns:
            Parsed message data or None if no content
        """
        pass
