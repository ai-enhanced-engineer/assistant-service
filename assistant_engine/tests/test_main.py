import importlib
import os
import sys
from types import SimpleNamespace

import pytest

import assistant_engine.config as real_config
import assistant_engine.functions as real_functions
import assistant_engine.processors as real_processors


@pytest.mark.asyncio
async def test_run_stream_consumes_events(mocker):
    sys.modules.setdefault("config", real_config)
    sys.modules.setdefault("functions", real_functions)
    sys.modules.setdefault("processors", real_processors)
    mocker.patch.dict(
        os.environ,
        {
            "PROJECT_ID": "pid",
            "CLIENT_ID": "cid",
            "BUCKET_ID": "bid",
            "ASSISTANT_ID": "aid",
        },
    )

    import types

    class DummySecretRepo:
        def __init__(self, *_, **__):
            pass

        def write_secret(self, *_, **__):
            pass

        def access_secret(self, *_):
            return "sk"

    class DummyConfigRepo:
        def __init__(self, *_, **__):
            pass

        def write_config(self, *_):
            pass

        def read_config(self):
            from botbrew_commons.data_models import EngineAssistantConfig

            return EngineAssistantConfig(assistant_id="aid", assistant_name="name", initial_message="hi")

    dummy_module = types.ModuleType("botbrew_commons.repositories")
    dummy_module.GCPSecretRepository = DummySecretRepo
    dummy_module.GCPConfigRepository = DummyConfigRepo
    sys.modules["botbrew_commons.repositories"] = dummy_module
    mocker.patch("google.auth.default", return_value=(None, None))
    mocker.patch("chainlit.step", lambda *_a, **_k: (lambda f: f))
    mocker.patch("chainlit.on_chat_start", lambda f: f)
    mocker.patch("chainlit.on_message", lambda f: f)
    main = importlib.reload(importlib.import_module("assistant_engine.main"))

    class DummyMsg:
        def __init__(self, *_, **__):
            pass

        async def send(self):
            pass

        async def update(self):
            pass

    class DummyStep(DummyMsg):
        pass

    mock_message_cls = mocker.patch("assistant_engine.main.cl.Message", DummyMsg)
    mock_step_cls = mocker.patch("assistant_engine.main.cl.Step", DummyStep)
    mocker.patch("assistant_engine.main.cl.sleep", new=mocker.AsyncMock())
    mocker.patch("assistant_engine.main.cl.sleep", new=mocker.AsyncMock())

    class DummyProcessor:
        def __init__(self):
            self.send_message = True

        async def process(self, *_):
            return mock_message_cls()

    class DummyToolProcessor:
        def __init__(self):
            self.tool_outputs = {}
            self.update = False

        async def process_tool_call(self, *_, **__):
            return mock_step_cls()

    mocker.patch("assistant_engine.main.ThreadMessageProcessor", DummyProcessor)
    mocker.patch("assistant_engine.main.ToolProcessor", DummyToolProcessor)

    async def fake_create_message(*_, **__):
        return SimpleNamespace(id="user_msg", content="hi")

    async def fake_retrieve_message(*_, **__):
        return SimpleNamespace(
            id="assistant_msg",
            content=[SimpleNamespace(text=SimpleNamespace(value="ok"), type="text")],
            role="assistant",
        )

    async def fake_steps_retrieve(*_, **__):
        mc = SimpleNamespace(message_id="assistant_msg")
        return SimpleNamespace(step_details=SimpleNamespace(type="message_creation", message_creation=mc))

    async def fake_runs_create(*_, **kwargs):
        assert kwargs.get("stream") is True

        async def gen():
            yield SimpleNamespace(event="thread.run.created", data=SimpleNamespace(id="run1"))
            yield SimpleNamespace(event="thread.run.step.created", data=SimpleNamespace(id="step1"))
            yield SimpleNamespace(event="thread.message.created", data=SimpleNamespace(id="assistant_msg"))
            yield SimpleNamespace(event="thread.run.completed", data=SimpleNamespace(id="run1"))

        return gen()

    fake_client = SimpleNamespace(
        beta=SimpleNamespace(
            threads=SimpleNamespace(
                messages=SimpleNamespace(
                    create=mocker.AsyncMock(side_effect=fake_create_message),
                    retrieve=mocker.AsyncMock(side_effect=fake_retrieve_message),
                ),
                runs=SimpleNamespace(
                    create=mocker.AsyncMock(side_effect=fake_runs_create),
                    steps=SimpleNamespace(retrieve=mocker.AsyncMock(side_effect=fake_steps_retrieve)),
                    submit_tool_outputs=mocker.AsyncMock(),
                ),
            )
        )
    )
    mocker.patch.object(main, "client", fake_client)

    await main.run(thread_id="t1", human_query="hi")

    assert fake_client.beta.threads.messages.retrieve.called
