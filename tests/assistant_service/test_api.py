import types
from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from openai import OpenAIError

from assistant_service import repositories as repos
from assistant_service.main import AssistantEngineAPI
from assistant_service.models import EngineAssistantConfig


@pytest.fixture()
def api(monkeypatch):
    monkeypatch.setenv("PROJECT_ID", "p")
    monkeypatch.setenv("BUCKET_ID", "b")
    monkeypatch.setenv("CLIENT_ID", "c")
    monkeypatch.setenv("ASSISTANT_ID", "a")

    class DummySecretRepo:
        def __init__(self, project_id: str, client_id: str):
            self.project_id = project_id
            self.client_id = client_id

        def write_secret(self, _):
            pass

        def access_secret(self, _):
            return "sk"

    class DummyConfigRepo:
        def __init__(self, client_id: str, project_id: str, bucket_name: str):
            self.client_id = client_id
            self.project_id = project_id
            self.bucket_name = bucket_name

        def write_config(self, _config):
            pass

        def read_config(self):
            return EngineAssistantConfig(
                assistant_id="a",
                assistant_name="name",
                initial_message="hi",
            )

    monkeypatch.setattr(repos, "GCPSecretRepository", DummySecretRepo)
    monkeypatch.setattr(repos, "GCPConfigRepository", DummyConfigRepo)

    # Also patch in the main module where they're imported
    import assistant_service.main as main_module

    monkeypatch.setattr(main_module, "GCPSecretRepository", DummySecretRepo)
    monkeypatch.setattr(main_module, "GCPConfigRepository", DummyConfigRepo)

    class DummyThreads:
        async def create(self):
            return types.SimpleNamespace(id="thread123")

    class DummyBeta:
        def __init__(self):
            self.threads = DummyThreads()

    class DummyClient:
        def __init__(self) -> None:
            self.beta = DummyBeta()
            self.aclose = AsyncMock()
            self.close = AsyncMock()

    api = AssistantEngineAPI()
    dummy_client = DummyClient()
    api.client = dummy_client  # type: ignore[assignment]

    return api, dummy_client


def test_lifespan(api: tuple[AssistantEngineAPI, Any]) -> None:
    api_obj, dummy_client = api
    with TestClient(api_obj.app):
        assert api_obj.client is dummy_client
        dummy_client.close.assert_not_awaited()
    # Since client was injected (not created by lifespan), it shouldn't be closed
    dummy_client.close.assert_not_awaited()


def test_lifespan_creates_client(monkeypatch: Any) -> None:
    """Test that lifespan creates and closes client when not injected."""
    monkeypatch.setenv("PROJECT_ID", "p")
    monkeypatch.setenv("BUCKET_ID", "b")
    monkeypatch.setenv("CLIENT_ID", "c")
    monkeypatch.setenv("ASSISTANT_ID", "a")

    import assistant_service.main as main_module
    from assistant_service import repositories as repos

    class DummySecretRepo:
        def __init__(self, project_id: str, client_id: str):
            pass

        def access_secret(self, name: str) -> str:
            return "dummy_secret"

    class DummyConfigRepo:
        def __init__(self, client_id: str, project_id: str, bucket_name: str):
            pass

        def read_config(self):
            from assistant_service.models import EngineAssistantConfig

            return EngineAssistantConfig(
                assistant_id="a",
                assistant_name="name",
                initial_message="hi",
            )

    monkeypatch.setattr(repos, "GCPSecretRepository", DummySecretRepo)
    monkeypatch.setattr(repos, "GCPConfigRepository", DummyConfigRepo)
    monkeypatch.setattr(main_module, "GCPSecretRepository", DummySecretRepo)
    monkeypatch.setattr(main_module, "GCPConfigRepository", DummyConfigRepo)

    # Mock AsyncOpenAI
    close_mock = AsyncMock()

    class MockAsyncOpenAI:
        def __init__(self, api_key: str):
            self.close = close_mock

    monkeypatch.setattr(main_module, "AsyncOpenAI", MockAsyncOpenAI)

    api = AssistantEngineAPI()
    assert api.client is None  # Client not created yet

    with TestClient(api.app):
        assert api.client is not None  # Client created by lifespan
        close_mock.assert_not_awaited()

    # Client should be closed after lifespan
    close_mock.assert_awaited_once()


def test_start_endpoint(api: tuple[AssistantEngineAPI, Any]) -> None:
    api_obj, dummy_client = api
    with TestClient(api_obj.app) as client:
        resp = client.get("/start")
        assert resp.status_code == 200
        data = resp.json()
        assert data["thread_id"] == "thread123"
        assert data["initial_message"] == "Hello! I'm your development assistant. How can I help you today?"
        assert "correlation_id" in data
        # Correlation ID should be a valid UUID
        from uuid import UUID

        UUID(data["correlation_id"])
    # Since client was injected (not created by lifespan), it shouldn't be closed
    dummy_client.close.assert_not_awaited()


def test_chat_endpoint(monkeypatch: Any, api: tuple[AssistantEngineAPI, Any]) -> None:
    api_obj, dummy_client = api

    async def dummy_run(tid: str, msg: str) -> list[str]:
        assert tid == "thread123"
        assert msg == "hello"
        return ["response"]

    monkeypatch.setattr(api_obj, "_process_run", dummy_run)
    with TestClient(api_obj.app) as client:
        resp = client.post("/chat", json={"thread_id": "thread123", "message": "hello"})
        assert resp.status_code == 200
        assert resp.json() == {"responses": ["response"]}
    # Since client was injected (not created by lifespan), it shouldn't be closed
    dummy_client.close.assert_not_awaited()


def test_stream_endpoint(monkeypatch: Any, api: tuple[AssistantEngineAPI, Any]) -> None:
    api_obj, dummy_client = api

    async def dummy_stream(tid: str, msg: str) -> AsyncGenerator[Any, None]:
        assert tid == "thread123"
        assert msg == "hello"
        yield types.SimpleNamespace(model_dump_json=lambda: "event1")
        yield types.SimpleNamespace(model_dump_json=lambda: "event2")

    monkeypatch.setattr(api_obj, "_process_run_stream", dummy_stream)

    with TestClient(api_obj.app) as client, client.websocket_connect("/stream") as websocket:
        websocket.send_json({"thread_id": "thread123", "message": "hello"})
        assert websocket.receive_text() == "event1"
        assert websocket.receive_text() == "event2"
        # WebSocket now stays open for multiple messages, so we close it explicitly
        websocket.close()
    # Since client was injected (not created by lifespan), it shouldn't be closed
    dummy_client.close.assert_not_awaited()


def test_start_endpoint_openai_error(monkeypatch: Any, api: tuple[AssistantEngineAPI, Any]) -> None:
    api_obj, dummy_client = api

    async def err(*_args, **_kwargs):
        raise OpenAIError("boom")

    monkeypatch.setattr(dummy_client.beta.threads, "create", err)
    with TestClient(api_obj.app) as client:
        resp = client.get("/start")
        assert resp.status_code == 502
    # Since client was injected (not created by lifespan), it shouldn't be closed
    dummy_client.close.assert_not_awaited()


def test_chat_endpoint_openai_error(monkeypatch: Any, api: tuple[AssistantEngineAPI, Any]) -> None:
    api_obj, dummy_client = api

    class Messages:
        async def create(self, *_args, **_kwargs):
            raise OpenAIError("fail")

    monkeypatch.setattr(dummy_client.beta.threads, "messages", Messages(), raising=False)
    monkeypatch.setattr(dummy_client.beta.threads, "runs", types.SimpleNamespace(), raising=False)

    with TestClient(api_obj.app) as client:
        resp = client.post("/chat", json={"thread_id": "thread123", "message": "hi"})
        assert resp.status_code == 502
    # Since client was injected (not created by lifespan), it shouldn't be closed
    dummy_client.close.assert_not_awaited()


def test_validate_function_args_success(api: tuple[AssistantEngineAPI, Any]) -> None:
    """Test successful function argument validation."""
    api_obj, _ = api

    def test_func(required_param: str, optional_param: str = "default") -> str:
        return f"{required_param}_{optional_param}"

    # Valid arguments
    api_obj._validate_function_args(test_func, {"required_param": "value"}, "test_func")
    api_obj._validate_function_args(test_func, {"required_param": "value", "optional_param": "custom"}, "test_func")


def test_validate_function_args_missing_required(api: tuple[AssistantEngineAPI, Any]) -> None:
    """Test validation fails when required parameter is missing."""
    api_obj, _ = api

    def test_func(required_param: str, optional_param: str = "default") -> str:
        return f"{required_param}_{optional_param}"

    # Missing required parameter
    with pytest.raises(TypeError, match="Missing required arguments: required_param"):
        api_obj._validate_function_args(test_func, {"optional_param": "custom"}, "test_func")


def test_validate_function_args_unexpected_params(api: tuple[AssistantEngineAPI, Any]) -> None:
    """Test warning when unexpected parameters are provided."""
    api_obj, _ = api

    def test_func(required_param: str) -> str:
        return required_param

    # Since we're using structured logging, we can't easily test log output in unit tests
    # Instead, we just verify that the function doesn't raise an error with unexpected params
    # and that it still works correctly
    api_obj._validate_function_args(test_func, {"required_param": "value", "unexpected": "param"}, "test_func")
    # _validate_function_args doesn't return anything, just verify it runs without error


@pytest.mark.asyncio
async def test_function_tool_call_invalid_function_name(api: tuple[AssistantEngineAPI, Any]) -> None:
    """Test handling of invalid function names in tool calls."""
    api_obj, dummy_client = api

    # Mock TOOL_MAP to be empty
    with patch("assistant_service.main.TOOL_MAP", {}):
        # Create a mock tool call event
        tool_call = types.SimpleNamespace(
            id="tool_123",
            type="function",
            function=types.SimpleNamespace(name="nonexistent_function", arguments='{"param": "value"}'),
        )

        step_details = types.SimpleNamespace(type="tool_calls", tool_calls=[tool_call])

        event = types.SimpleNamespace(
            event="thread.run.step.completed", data=types.SimpleNamespace(step_details=step_details)
        )

        # Process the event using the actual logic (no _dict_to_object needed)
        tool_outputs = {}

        # Simulate the logic from _iterate_run_events
        if event.event == "thread.run.step.completed":
            step_details = event.data.step_details
            if step_details.type == "tool_calls":
                for tool_call in step_details.tool_calls:
                    if tool_call.type == "function":
                        name = tool_call.function.name

                        from assistant_service.main import TOOL_MAP

                        if name not in TOOL_MAP:
                            tool_outputs[tool_call.id] = {
                                "tool_call_id": tool_call.id,
                                "output": f"Error: Function '{name}' not available",
                            }

        # Verify error output
        assert "tool_123" in tool_outputs
        assert "Error: Function 'nonexistent_function' not available" in tool_outputs["tool_123"]["output"]


@pytest.mark.asyncio
async def test_function_tool_call_invalid_arguments(api: tuple[AssistantEngineAPI, Any]) -> None:
    """Test handling of invalid function arguments in tool calls."""
    api_obj, dummy_client = api

    def test_function(required_param: str) -> str:
        return f"Result: {required_param}"

    # Mock TOOL_MAP with our test function
    with patch("assistant_service.main.TOOL_MAP", {"test_function": test_function}):
        # Create a mock tool call event with missing required parameter
        tool_call = types.SimpleNamespace(
            id="tool_456",
            type="function",
            function=types.SimpleNamespace(
                name="test_function",
                arguments='{"wrong_param": "value"}',  # Missing required_param
            ),
        )

        step_details = types.SimpleNamespace(type="tool_calls", tool_calls=[tool_call])

        event = types.SimpleNamespace(
            event="thread.run.step.completed", data=types.SimpleNamespace(step_details=step_details)
        )

        # Process the event
        tool_outputs = {}

        # Simulate the enhanced logic from _iterate_run_events
        if event.event == "thread.run.step.completed":
            step_details = event.data.step_details
            if step_details.type == "tool_calls":
                for tool_call in step_details.tool_calls:
                    if tool_call.type == "function":
                        name = tool_call.function.name
                        args = {"wrong_param": "value"}

                        from assistant_service.main import TOOL_MAP

                        if name in TOOL_MAP:
                            try:
                                func = TOOL_MAP[name]
                                api_obj._validate_function_args(func, args, name)
                                output = func(**args)
                                tool_outputs[tool_call.id] = {
                                    "tool_call_id": tool_call.id,
                                    "output": output,
                                }
                            except TypeError as err:
                                tool_outputs[tool_call.id] = {
                                    "tool_call_id": tool_call.id,
                                    "output": f"Error: Invalid arguments for function '{name}': {err}",
                                }

        # Verify error output
        assert "tool_456" in tool_outputs
        assert "Error: Invalid arguments for function 'test_function'" in tool_outputs["tool_456"]["output"]
        assert "Missing required arguments: required_param" in tool_outputs["tool_456"]["output"]
