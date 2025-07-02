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
    """Submit tool outputs with retries and exponential backoff.
    
    Returns:
        The submission result on success, None on permanent failure.
    """
    tool_outputs_list = list(tool_outputs) if not isinstance(tool_outputs, list) else tool_outputs
    tool_count = len(tool_outputs_list)
    
    logger.info(
        "Submitting %d tool outputs for run_id=%s, thread_id=%s", 
        tool_count, 
        run_id, 
        thread_id
    )
    
    for attempt in range(retries):
        try:
            result = await client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run_id,
                tool_outputs=tool_outputs_list,
            )
            logger.info(
                "Successfully submitted %d tool outputs for run_id=%s (attempt %d/%d)", 
                tool_count, 
                run_id, 
                attempt + 1, 
                retries
            )
            return result
        except Exception as err:  # noqa: BLE001
            wait_time = backoff ** attempt
            logger.error(
                "Tool output submission failed (attempt %d/%d) for run_id=%s: %s. "
                "Waiting %d seconds before retry.",
                attempt + 1,
                retries,
                run_id,
                err,
                wait_time if attempt < retries - 1 else 0,
            )
            if attempt == retries - 1:
                logger.error(
                    "Permanent failure: Unable to submit %d tool outputs after %d attempts for run_id=%s",
                    tool_count,
                    retries,
                    run_id,
                )
                return None
            await asyncio.sleep(wait_time)
    return None


async def cancel_run_safely(client: Any, thread_id: str, run_id: str) -> bool:
    """Safely cancel a run, returning True if successful or already in terminal state."""
    try:
        # First check if run is already in a terminal state
        run_status = await retrieve_run(client, thread_id, run_id)
        if run_status and run_status.status in ["completed", "failed", "cancelled", "expired"]:
            logger.info("Run %s already in terminal state: %s", run_id, run_status.status)
            return True
            
        # Attempt to cancel the run
        await client.beta.threads.runs.cancel(thread_id=thread_id, run_id=run_id)
        logger.info("Successfully cancelled run_id=%s, thread_id=%s", run_id, thread_id)
        return True
        
    except Exception as err:  # noqa: BLE001
        logger.error("Failed to cancel run_id=%s, thread_id=%s: %s", run_id, thread_id, err)
        return False
