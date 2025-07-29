"""Tool execution logic for the assistant service."""

import inspect
import json
from typing import Any, Callable, Optional

from ..structured_logging import get_logger
from ..tools import TOOL_MAP

logger = get_logger("TOOL_EXECUTOR")


class ToolExecutor:
    """Handles tool execution and validation."""

    def __init__(self, tool_map: Optional[dict[str, Callable[..., Any]]] = None):
        """Initialize with tool registry."""
        self.tool_map = tool_map or TOOL_MAP

    def validate_function_args(self, func: Callable[..., Any], args: dict[str, Any], name: str) -> None:
        """Validate function arguments against the function signature."""
        sig = inspect.signature(func)

        # Check for required parameters
        required_params = {param.name for param in sig.parameters.values() if param.default is inspect.Parameter.empty}
        missing_params = required_params - set(args.keys())
        if missing_params:
            missing_str = ", ".join(sorted(missing_params))
            raise TypeError(f"Missing required arguments: {missing_str}")

        # Check for unexpected parameters
        valid_params = set(sig.parameters.keys())
        unexpected_params = set(args.keys()) - valid_params
        if unexpected_params:
            logger.warning(
                "Function received unexpected parameters", function_name=name, unexpected_params=unexpected_params
            )

    def execute_tool(self, tool_name: str, tool_args: str | dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool and return the result.

        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments as JSON string or dict
            context: Execution context (thread_id, run_id, etc.)

        Returns:
            Dict with tool_call_id and output
        """
        tool_call_id = context.get("tool_call_id", "unknown")

        # Parse arguments if string
        if isinstance(tool_args, str):
            try:
                args = json.loads(tool_args or "{}")
            except json.JSONDecodeError as e:
                logger.error(
                    "Invalid JSON in tool arguments",
                    function_name=tool_name,
                    tool_call_id=tool_call_id,
                    error=str(e),
                    **context,
                )
                return {"tool_call_id": tool_call_id, "output": f"Error: Invalid JSON arguments: {e}"}
        else:
            args = tool_args

        # Check if tool exists
        if tool_name not in self.tool_map:
            logger.error("Unknown function not found in TOOL_MAP", function_name=tool_name, **context)
            correlation_id = context.get("correlation_id", "unknown")
            return {
                "tool_call_id": tool_call_id,
                "output": f"Error: Function '{tool_name}' not available (correlation_id: {correlation_id[:8]})",
            }

        # Validate and execute
        func = self.tool_map[tool_name]
        try:
            self.validate_function_args(func, args, tool_name)

            logger.debug("Executing function with args", function_name=tool_name, args=args, **context)

            output = func(**args)

            logger.info("Function executed successfully", function_name=tool_name, **context)

            return {"tool_call_id": tool_call_id, "output": output}

        except TypeError as err:
            logger.error(
                "Invalid arguments for function",
                function_name=tool_name,
                error_type="TypeError",
                error=str(err),
                **context,
            )
            correlation_id = context.get("correlation_id", "unknown")
            return {
                "tool_call_id": tool_call_id,
                "output": f"Error: Invalid arguments for function '{tool_name}': {err} (correlation_id: {correlation_id[:8]})",
            }

        except Exception as err:  # noqa: BLE001
            logger.error(
                "Function execution failed",
                function_name=tool_name,
                error_type=type(err).__name__,
                error=str(err),
                **context,
            )
            correlation_id = context.get("correlation_id", "unknown")
            return {
                "tool_call_id": tool_call_id,
                "output": f"Error: Function '{tool_name}' execution failed: {err} (correlation_id: {correlation_id[:8]})",
            }
