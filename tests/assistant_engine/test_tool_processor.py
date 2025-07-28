import types
from datetime import datetime

import pytest

from assistant_engine.processors import ToolProcessor


@pytest.mark.asyncio
async def test_process_tool_call_creates_and_updates() -> None:
    processor = ToolProcessor()
    run_step = types.SimpleNamespace(created_at=1000, completed_at=1010)
    tool_call = types.SimpleNamespace(id="t1")

    # first call creates the step
    step1 = await processor.process_tool_call(
        step=run_step,  # type: ignore[arg-type]
        tool_call=tool_call,  # type: ignore[arg-type]
        name="tool",
        t_input="in1",
        t_output="out1",
    )

    assert step1.name == "tool"
    assert step1.type == "tool"
    assert step1.start == datetime.fromtimestamp(1000).isoformat()
    assert step1.end == datetime.fromtimestamp(1010).isoformat()
    assert step1.input == "in1"
    assert step1.output == "out1"
    assert processor.tool_outputs["t1"]["output"] == "out1"
    assert processor.update is False

    # second call with same tool_call updates the same step
    run_step2 = types.SimpleNamespace(created_at=1002, completed_at=1012)
    step2 = await processor.process_tool_call(
        step=run_step2,  # type: ignore[arg-type]
        tool_call=tool_call,  # type: ignore[arg-type]
        name="tool",
        t_input="in2",
        t_output="out2",
    )

    assert step1 is step2
    assert processor.update is True
    assert step2.input == "in2"
    assert step2.output == "out2"
    assert processor.tool_outputs["t1"]["output"] == "out2"
