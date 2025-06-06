import asyncio
from typing import Any, Iterable, Optional

from .bb_logging import get_logger

logger = get_logger("OPENAI_HELPERS")


async def retrieve_run(client: Any, thread_id: str, run_id: str) -> Optional[Any]:
    """Safely retrieve a run, logging errors."""
    try:
        return await client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
    except Exception as err:  # noqa: BLE001
        logger.error("Failed to retrieve run: %s", err)
        return None


async def list_run_steps(client: Any, thread_id: str, run_id: str) -> Optional[Any]:
    """Safely list run steps, logging errors."""
    try:
        return await client.beta.threads.runs.steps.list(thread_id=thread_id, run_id=run_id, order="asc")
    except Exception as err:  # noqa: BLE001
        logger.error("Failed to list run steps: %s", err)
        return None


async def submit_tool_outputs_with_backoff(
    client: Any,
    thread_id: str,
    run_id: str,
    tool_outputs: Iterable[Any],
    retries: int = 3,
    backoff: int = 2,
) -> Optional[Any]:
    """Submit tool outputs with retries and exponential backoff."""
    for attempt in range(retries):
        try:
            return await client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run_id,
                tool_outputs=tool_outputs,
            )
        except Exception as err:  # noqa: BLE001
            logger.error("Failed to submit tool outputs: %s", err)
            if attempt == retries - 1:
                return None
            await asyncio.sleep(backoff**attempt)
    return None
