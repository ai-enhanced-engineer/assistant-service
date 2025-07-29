"""Step data entity for tracking run steps."""

from dataclasses import dataclass
from typing import Any, Optional, Union


@dataclass
class StepData:
    """Information collected about a single run step.

    Attributes:
        name: The name of the step or tool.
        type: The type of step being executed.
        parent_id: Identifier for any parent step.
        show_input: Whether to display the input when presenting the step.
        start: ISO formatted creation time.
        end: ISO formatted completion time.
        input: Input payload provided to the step.
        output: Output returned from the step.
    """

    name: Optional[str] = None
    type: Optional[str] = None
    parent_id: Optional[str] = None
    show_input: Optional[Union[bool, str]] = None
    start: Optional[str] = None
    end: Optional[str] = None
    input: Any = None
    output: Any = None
