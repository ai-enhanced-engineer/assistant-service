"""Run processing logic for the assistant service."""

from typing import Any, AsyncGenerator, Optional

from openai import AsyncOpenAI, OpenAIError

from ..entities import EngineAssistantConfig
from ..providers.openai_helpers import cancel_run_safely, submit_tool_outputs_with_backoff
from ..server.error_handlers import ErrorHandler
from ..structured_logging import get_logger, get_or_create_correlation_id
from .tool_executor import ToolExecutor

logger = get_logger("RUN_PROCESSOR")


class RunProcessor:
    """Handles OpenAI run processing and event streaming."""

    def __init__(
        self, client: AsyncOpenAI, config: EngineAssistantConfig, tool_executor: Optional[ToolExecutor] = None
    ):
        """Initialize with OpenAI client and configuration."""
        self.client = client
        self.config = config
        self.tool_executor = tool_executor or ToolExecutor()

    async def create_message(self, thread_id: str, content: str) -> None:
        """Create a message in the thread."""
        correlation_id = get_or_create_correlation_id()

        try:
            await self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=content,
            )
            logger.info("Message created successfully", thread_id=thread_id, correlation_id=correlation_id)
        except OpenAIError as err:
            raise ErrorHandler.handle_openai_error(err, "create message", correlation_id, thread_id=thread_id)
        except Exception as err:  # noqa: BLE001
            raise ErrorHandler.handle_unexpected_error(err, "creating message", correlation_id, thread_id=thread_id)

    async def create_run_stream(self, thread_id: str) -> Any:
        """Create a streaming run for the thread."""
        correlation_id = get_or_create_correlation_id()

        try:
            event_stream = await self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.config.assistant_id,
                stream=True,
            )
            logger.info(
                "Run stream created successfully",
                thread_id=thread_id,
                correlation_id=correlation_id,
                assistant_id=self.config.assistant_id,
            )
            return event_stream
        except OpenAIError as err:
            raise ErrorHandler.handle_openai_error(
                err, "create run", correlation_id, thread_id=thread_id, assistant_id=self.config.assistant_id
            )
        except Exception as err:  # noqa: BLE001
            raise ErrorHandler.handle_unexpected_error(
                err, "creating run", correlation_id, thread_id=thread_id, assistant_id=self.config.assistant_id
            )

    async def process_tool_calls(self, tool_calls: Any, context: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """Process tool calls and return outputs."""
        tool_outputs = {}

        for tool_call in tool_calls:
            if tool_call.type == "function":
                result = self.tool_executor.execute_tool(
                    tool_name=tool_call.function.name,
                    tool_args=tool_call.function.arguments,
                    context={**context, "tool_call_id": tool_call.id},
                )
                tool_outputs[tool_call.id] = result
            elif tool_call.type == "code_interpreter":
                tool_outputs[tool_call.id] = {
                    "tool_call_id": tool_call.id,
                    "output": "code_interpreter",
                }
            elif tool_call.type == "retrieval":
                tool_outputs[tool_call.id] = {
                    "tool_call_id": tool_call.id,
                    "output": "retrieval",
                }

        return tool_outputs

    async def iterate_run_events(self, thread_id: str, human_query: str) -> AsyncGenerator[Any, None]:
        """Process a run and yield streaming events."""
        correlation_id = get_or_create_correlation_id()
        logger.info("Starting run processing", thread_id=thread_id, correlation_id=correlation_id)

        # Create message
        await self.create_message(thread_id, human_query)

        # Create streaming run
        event_stream = await self.create_run_stream(thread_id)

        tool_outputs: dict[str, dict[str, Any]] = {}
        run_id = None

        async for event in event_stream:
            yield event

            if event.event == "thread.run.created":
                run_id = event.data.id

            # Handle tool calls from step completed events
            if (
                event.event == "thread.run.step.completed"
                and hasattr(event.data, "step_details")
                and event.data.step_details.type == "tool_calls"
            ):
                context = {"thread_id": thread_id, "run_id": run_id, "correlation_id": correlation_id}

                step_outputs = await self.process_tool_calls(event.data.step_details.tool_calls, context)
                tool_outputs.update(step_outputs)

            # Handle required actions
            if event.event == "thread.run.requires_action":
                if event.data.required_action and event.data.required_action.type == "submit_tool_outputs":
                    # Check for any non-function tools
                    submit_tool_outputs = getattr(event.data.required_action, "submit_tool_outputs", None)
                    if submit_tool_outputs and hasattr(submit_tool_outputs, "tool_calls"):
                        context = {"thread_id": thread_id, "run_id": run_id, "correlation_id": correlation_id}

                        # Process only non-function tools
                        non_function_outputs = await self.process_tool_calls(
                            [tc for tc in submit_tool_outputs.tool_calls if tc.type != "function"], context
                        )
                        tool_outputs.update(non_function_outputs)

            # Submit tool outputs when required
            if (
                event.event == "thread.run.requires_action"
                and event.data.required_action
                and event.data.required_action.type == "submit_tool_outputs"
                and tool_outputs
                and run_id
            ):
                submission_result = await submit_tool_outputs_with_backoff(
                    self.client, thread_id, run_id, list(tool_outputs.values())
                )

                if submission_result is None:
                    logger.error(
                        "Tool output submission failed permanently for run_id=%s, thread_id=%s. "
                        "Attempting to cancel run to prevent hanging state.",
                        run_id,
                        thread_id,
                    )
                    await cancel_run_safely(self.client, thread_id, run_id)

                tool_outputs.clear()

    async def process_run(self, thread_id: str, human_query: str) -> list[str]:
        """Process a run and return the final messages."""
        correlation_id = get_or_create_correlation_id()

        logger.info(
            "Processing chat request",
            thread_id=thread_id,
            correlation_id=correlation_id,
            message_length=len(human_query),
        )

        messages: list[str] = []

        async for event in self.iterate_run_events(thread_id, human_query):
            if event.event == "thread.run.step.completed" and event.data.step_details.type == "message_creation":
                message_id = event.data.step_details.message_creation.message_id
                try:
                    thread_message = await self.client.beta.threads.messages.retrieve(
                        thread_id=thread_id, message_id=message_id
                    )
                    logger.debug(
                        "Message retrieved successfully",
                        thread_id=thread_id,
                        correlation_id=correlation_id,
                        message_id=message_id,
                    )

                    for content in thread_message.content:
                        if hasattr(content, "text"):
                            messages.append(content.text.value)

                except OpenAIError as err:
                    raise ErrorHandler.handle_openai_error(
                        err, "retrieve message", correlation_id, thread_id=thread_id, message_id=message_id
                    )
                except Exception as err:  # noqa: BLE001
                    raise ErrorHandler.handle_unexpected_error(
                        err, "retrieving message", correlation_id, thread_id=thread_id, message_id=message_id
                    )

        logger.info(
            "Run processing completed", thread_id=thread_id, correlation_id=correlation_id, message_count=len(messages)
        )
        return messages

    async def process_run_stream(self, thread_id: str, human_query: str) -> AsyncGenerator[Any, None]:
        """Yield events from the assistant run as they arrive."""
        async for event in self.iterate_run_events(thread_id, human_query):
            yield event
