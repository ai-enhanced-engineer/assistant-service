import pytest

from assistant_service.providers.openai_helpers import (
    list_run_steps,
    retrieve_run,
    submit_tool_outputs_with_backoff,
)


class DummyClient:
    class Beta:
        class Threads:
            class Runs:
                def __init__(self, outer):
                    self.outer = outer

                async def retrieve(self, *args, **kwargs):
                    return await self.outer.retrieve(*args, **kwargs)

                class Steps:
                    def __init__(self, outer):
                        self.outer = outer

                    async def list(self, *args, **kwargs):
                        return await self.outer.list(*args, **kwargs)

                steps: "DummyClient.Beta.Threads.Runs.Steps"

                async def submit_tool_outputs(self, *args, **kwargs):
                    return await self.outer.submit(*args, **kwargs)

            def __init__(self, outer):
                self.runs = DummyClient.Beta.Threads.Runs(outer)

        def __init__(self, outer):
            self.threads = DummyClient.Beta.Threads(outer)

    def __init__(self, callbacks):
        self.callbacks = callbacks
        self.beta = DummyClient.Beta(self)

    async def retrieve(self, *args, **kwargs):
        return await self.callbacks["retrieve"](*args, **kwargs)

    async def list(self, *args, **kwargs):
        return await self.callbacks["list"](*args, **kwargs)

    async def submit(self, *args, **kwargs):
        return await self.callbacks["submit"](*args, **kwargs)


@pytest.mark.asyncio
async def test_retrieve_run_returns_none_on_error():
    async def err(*_):
        raise RuntimeError("boom")

    client = DummyClient({"retrieve": err, "list": err, "submit": err})
    result = await retrieve_run(client, "t", "r")
    assert result is None


@pytest.mark.asyncio
async def test_list_run_steps_returns_none_on_error():
    async def err(*_):
        raise RuntimeError("boom")

    client = DummyClient({"retrieve": err, "list": err, "submit": err})
    result = await list_run_steps(client, "t", "r")
    assert result is None


@pytest.mark.asyncio
async def test_submit_tool_outputs_retries():
    calls = 0

    async def fail_then_succeed(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        if calls < 2:
            raise RuntimeError("fail")
        return "ok"

    client = DummyClient({"retrieve": fail_then_succeed, "list": fail_then_succeed, "submit": fail_then_succeed})
    result = await submit_tool_outputs_with_backoff(client, "t", "r", [])
    assert result == "ok"
    assert calls == 2


@pytest.mark.asyncio
async def test_submit_tool_outputs_returns_none_after_retries():
    async def always_fail(*_args, **_kwargs):
        raise RuntimeError("fail")

    client = DummyClient({"retrieve": always_fail, "list": always_fail, "submit": always_fail})
    result = await submit_tool_outputs_with_backoff(client, "t", "r", [], retries=2)
    assert result is None
