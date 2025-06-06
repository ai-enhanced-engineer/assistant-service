import os
import sys
import types

import chainlit as cl
import openai
import pytest

import assistant_engine.config as config_module
import assistant_engine.functions as functions_module
import assistant_engine.processors as processors_module
import botbrew_commons.botbrew_commons.repositories.secrets as secrets_mod
import botbrew_commons.repositories as repositories_pkg
from botbrew_commons.botbrew_commons.data_models.config import EngineAssistantConfig


class DummyConfigRepository:
    def __init__(self, *args, **kwargs):
        pass

    def write_config(self, config: EngineAssistantConfig) -> None:
        pass

    def read_config(self) -> EngineAssistantConfig:
        return EngineAssistantConfig(assistant_id="aid", assistant_name="name", initial_message="hi")


os.environ.setdefault("PROJECT_ID", "pid")
os.environ.setdefault("CLIENT_ID", "cid")
os.environ.setdefault("BUCKET_ID", "bid")
os.environ.setdefault("OPENAI_API_KEY", "dummy")

sys.modules.setdefault("config", config_module)
sys.modules.setdefault("functions", functions_module)
sys.modules.setdefault("processors", processors_module)
repositories_pkg.GCPSecretRepository = secrets_mod.LocalSecretRepository
repositories_pkg.GCPConfigRepository = DummyConfigRepository


class DummyClient:
    def __init__(self, *args, **kwargs):
        pass


openai.AsyncOpenAI = DummyClient
cl.step = lambda *_, **__: (lambda f: f)
cl.on_chat_start = lambda f: f
cl.on_message = lambda f: f

from assistant_engine import main  # noqa: E402
from assistant_engine.main import ToolProcessor, handle_function_tool_call  # noqa: E402


@pytest.mark.asyncio
async def test_unknown_function_skipped(mocker):
    tool_processor = ToolProcessor()
    step = mocker.Mock()
    tool_call = types.SimpleNamespace(
        id="1",
        type="function",
        function=types.SimpleNamespace(name="missing", arguments="{}"),
    )

    log_err = mocker.patch.object(main.logger, "error")

    result = await handle_function_tool_call(tool_call=tool_call, step=step, tool_processor=tool_processor)

    assert result is None
    log_err.assert_called_once()


@pytest.mark.asyncio
async def test_missing_parameters_skipped(mocker):
    tool_processor = ToolProcessor()
    step = mocker.Mock()

    def sample(a, b):
        return a + b

    mocker.patch.object(main, "TOOL_MAP", {"sample": sample})

    tool_call = types.SimpleNamespace(
        id="1",
        type="function",
        function=types.SimpleNamespace(name="sample", arguments='{"a": 1}'),
    )

    log_err = mocker.patch.object(main.logger, "error")

    result = await handle_function_tool_call(tool_call=tool_call, step=step, tool_processor=tool_processor)

    assert result is None
    log_err.assert_called_once()


@pytest.mark.asyncio
async def test_valid_function_invoked(mocker):
    tool_processor = ToolProcessor()
    step = mocker.Mock()

    def sample(a, b):
        return a + b

    mocker.patch.object(main, "TOOL_MAP", {"sample": sample})

    tool_call = types.SimpleNamespace(
        id="1",
        type="function",
        function=types.SimpleNamespace(name="sample", arguments='{"a": 1, "b": 2}'),
    )

    process_mock = mocker.patch.object(ToolProcessor, "process_tool_call", return_value=mocker.sentinel.step)

    result = await handle_function_tool_call(tool_call=tool_call, step=step, tool_processor=tool_processor)

    assert result == mocker.sentinel.step
    process_mock.assert_called_once()
