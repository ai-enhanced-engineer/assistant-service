import asyncio
import logging
from typing import Any, Iterable, Optional

from .bb_logging import get_logger, log_with_context
from .correlation import get_or_create_correlation_id

logger = get_logger("OPENAI_HELPERS")


async def retrieve_run(client: Any, thread_id: str, run_id: str) -> Optional[Any]:
    """Safely retrieve a run, logging errors."""
    correlation_id = get_or_create_correlation_id()
    try:
        result = await client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        log_with_context(
            logger, logging.DEBUG, 
            "Run retrieved successfully", 
            thread_id=thread_id, 
            run_id=run_id,
            correlation_id=correlation_id
        )
        return result
    except Exception as err:  # noqa: BLE001
        log_with_context(
            logger, logging.ERROR, 
            f"Failed to retrieve run: {err}", 
            thread_id=thread_id, 
            run_id=run_id,
            correlation_id=correlation_id,
            error_type=type(err).__name__
        )
        return None


async def list_run_steps(client: Any, thread_id: str, run_id: str) -> Optional[Any]:
    """Safely list run steps, logging errors."""
    correlation_id = get_or_create_correlation_id()
    try:
        result = await client.beta.threads.runs.steps.list(thread_id=thread_id, run_id=run_id, order="asc")
        log_with_context(
            logger, logging.DEBUG, 
            "Run steps listed successfully", 
            thread_id=thread_id, 
            run_id=run_id,
            correlation_id=correlation_id,
            step_count=len(result.data) if hasattr(result, 'data') else 'unknown'
        )
        return result
    except Exception as err:  # noqa: BLE001
        log_with_context(
            logger, logging.ERROR, 
            f"Failed to list run steps: {err}", 
            thread_id=thread_id, 
            run_id=run_id,
            correlation_id=correlation_id,
            error_type=type(err).__name__
        )
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
    correlation_id = get_or_create_correlation_id()
    tool_outputs_list = list(tool_outputs) if not isinstance(tool_outputs, list) else tool_outputs
    tool_count = len(tool_outputs_list)
    
    log_with_context(
        logger, logging.INFO, 
        f"Submitting {tool_count} tool outputs", 
        thread_id=thread_id, 
        run_id=run_id,
        correlation_id=correlation_id,
        tool_count=tool_count
    )
    
    for attempt in range(retries):
        try:
            result = await client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run_id,
                tool_outputs=tool_outputs_list,
            )
            log_with_context(
                logger, logging.INFO, 
                f"Successfully submitted {tool_count} tool outputs", 
                thread_id=thread_id, 
                run_id=run_id,
                correlation_id=correlation_id,
                tool_count=tool_count,
                attempt=attempt + 1,
                max_retries=retries
            )
            return result
        except Exception as err:  # noqa: BLE001
            wait_time = backoff ** attempt
            log_with_context(
                logger, logging.ERROR, 
                f"Tool output submission failed: {err}", 
                thread_id=thread_id, 
                run_id=run_id,
                correlation_id=correlation_id,
                tool_count=tool_count,
                attempt=attempt + 1,
                max_retries=retries,
                error_type=type(err).__name__,
                wait_time=wait_time if attempt < retries - 1 else 0
            )
            if attempt == retries - 1:
                log_with_context(
                    logger, logging.ERROR, 
                    f"Permanent failure: Unable to submit {tool_count} tool outputs after {retries} attempts", 
                    thread_id=thread_id, 
                    run_id=run_id,
                    correlation_id=correlation_id,
                    tool_count=tool_count,
                    max_retries=retries
                )
                return None
            await asyncio.sleep(wait_time)
    return None


async def cancel_run_safely(client: Any, thread_id: str, run_id: str) -> bool:
    """Safely cancel a run, returning True if successful or already in terminal state."""
    correlation_id = get_or_create_correlation_id()
    try:
        # First check if run is already in a terminal state
        run_status = await retrieve_run(client, thread_id, run_id)
        if run_status and run_status.status in ["completed", "failed", "cancelled", "expired"]:
            log_with_context(
                logger, logging.INFO, 
                f"Run already in terminal state: {run_status.status}", 
                thread_id=thread_id, 
                run_id=run_id,
                correlation_id=correlation_id,
                status=run_status.status
            )
            return True
            
        # Attempt to cancel the run
        await client.beta.threads.runs.cancel(thread_id=thread_id, run_id=run_id)
        log_with_context(
            logger, logging.INFO, 
            "Successfully cancelled run", 
            thread_id=thread_id, 
            run_id=run_id,
            correlation_id=correlation_id
        )
        return True
        
    except Exception as err:  # noqa: BLE001
        log_with_context(
            logger, logging.ERROR, 
            f"Failed to cancel run: {err}", 
            thread_id=thread_id, 
            run_id=run_id,
            correlation_id=correlation_id,
            error_type=type(err).__name__
        )
        return False
