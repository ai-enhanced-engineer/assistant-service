import types
from typing import Any, AsyncIterator
from unittest.mock import AsyncMock

import pytest

pytestmark = pytest.mark.asyncio


class DummyMessages:
    async def create(self, thread_id: str, role: str, content: str) -> None:
        self.created = (thread_id, role, content)

    async def retrieve(self, thread_id: str, message_id: str) -> Any:
        assert thread_id == "thread"
        assert message_id == "msg1"
        return types.SimpleNamespace(content=[types.SimpleNamespace(text=types.SimpleNamespace(value="hello"))])


class DummyRuns:
    def __init__(self):
        self.created_kwargs = None
        self.retrieve = AsyncMock(return_value=types.SimpleNamespace(status="completed"))
        self.cancel = AsyncMock(return_value=True)
        # Mock submit_tool_outputs method
        self.submit_tool_outputs = AsyncMock(return_value="success")

    async def create(self, thread_id: str, assistant_id: str, stream: bool) -> AsyncIterator[Any]:
        assert thread_id == "thread"
        assert assistant_id == "aid"
        assert stream is True
        self.created_kwargs = stream

        async def gen() -> AsyncIterator[Any]:
            yield types.SimpleNamespace(event="thread.run.created", data=types.SimpleNamespace(id="run1"))
            yield types.SimpleNamespace(
                event="thread.run.step.completed",
                data=types.SimpleNamespace(
                    step_details=types.SimpleNamespace(
                        type="message_creation",
                        message_creation=types.SimpleNamespace(message_id="msg1"),
                    )
                ),
            )
            yield types.SimpleNamespace(
                event="thread.run.step.completed",
                data=types.SimpleNamespace(
                    step_details=types.SimpleNamespace(
                        type="tool_calls",
                        tool_calls=[
                            types.SimpleNamespace(
                                id="call1",
                                type="function",
                                function=types.SimpleNamespace(name="func", arguments="{}"),
                            )
                        ],
                    )
                ),
            )
            yield types.SimpleNamespace(
                event="thread.run.requires_action",
                data=types.SimpleNamespace(
                    id="run1",
                    required_action=types.SimpleNamespace(
                        type="submit_tool_outputs", submit_tool_outputs=types.SimpleNamespace(tool_calls=[])
                    ),
                ),
            )
            yield types.SimpleNamespace(event="thread.run.completed", data=types.SimpleNamespace())

        return gen()


class DummyThreads:
    def __init__(self):
        self.messages = DummyMessages()
        self.runs = DummyRuns()


class DummyBeta:
    def __init__(self):
        self.threads = DummyThreads()


class DummyClient:
    def __init__(self):
        self.beta = DummyBeta()

    async def aclose(self):
        pass


# Create a class to track calls instead of using function attributes
class DummySubmit:
    def __init__(self):
        self.called_with = None

    async def __call__(
        self, client: Any, thread_id: str, run_id: str, tool_outputs: Any, *args: Any, **kwargs: Any
    ) -> str:
        self.called_with = list(tool_outputs)
        return "success"  # Return success instead of None


dummy_submit = DummySubmit()


async def dummy_function() -> str:
    return "out"


@pytest.fixture()
def api(monkeypatch):
    monkeypatch.setenv("PROJECT_ID", "p")
    monkeypatch.setenv("BUCKET_ID", "b")
    monkeypatch.setenv("CLIENT_ID", "c")
    monkeypatch.setenv("ASSISTANT_ID", "aid")

    from assistant_service import repositories as repos

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
            from assistant_service.models import EngineAssistantConfig

            return EngineAssistantConfig(
                assistant_id="aid",
                assistant_name="name",
                initial_message="hi",
                code_interpreter=False,
                retrieval=False,
                function_names=[],
            )

    monkeypatch.setattr(repos, "GCPSecretRepository", DummySecretRepo)
    monkeypatch.setattr(repos, "GCPConfigRepository", DummyConfigRepo)

    from assistant_service import main

    monkeypatch.setattr(main, "GCPSecretRepository", DummySecretRepo)
    monkeypatch.setattr(main, "GCPConfigRepository", DummyConfigRepo)

    api = main.AssistantEngineAPI()
    api.client = DummyClient()  # type: ignore[assignment]

    # Import the modules where these are actually located
    from assistant_service import functions, openai_helpers

    # Create a new instance of DummySubmit for this test
    test_dummy_submit = DummySubmit()

    monkeypatch.setattr(openai_helpers, "submit_tool_outputs_with_backoff", test_dummy_submit)
    monkeypatch.setattr(functions, "TOOL_MAP", {"func": lambda: "out"})

    # Also need to patch in the run_processor module since it imports directly
    from assistant_service.core import run_processor as run_processor_module

    monkeypatch.setattr(run_processor_module, "submit_tool_outputs_with_backoff", test_dummy_submit)

    # Initialize components that would normally be initialized in lifespan
    from assistant_service.api.endpoints import APIEndpoints
    from assistant_service.core.run_processor import RunProcessor

    api.run_processor = RunProcessor(api.client, api.engine_config, api.tool_executor)  # type: ignore[arg-type]
    api.api_endpoints = APIEndpoints(api.client, api.engine_config, api.run_processor)  # type: ignore[arg-type]

    # Also patch the tool_map on the tool_executor instance
    api.tool_executor.tool_map = {"func": lambda: "out"}

    # Attach the dummy_submit to the api object so tests can access it
    api.dummy_submit = test_dummy_submit  # type: ignore[attr-defined]

    return api


async def test_process_run(api):
    result = await api.run_processor.process_run("thread", "hi")
    assert result == ["hello"]
    assert api.dummy_submit.called_with == [{"tool_call_id": "call1", "output": "out"}]  # type: ignore[attr-defined]


async def test_process_run_stream(api):
    events = [event async for event in api.run_processor.process_run_stream("thread", "hi")]
    assert [e.event for e in events] == [
        "thread.run.created",
        "thread.run.step.completed",
        "thread.run.step.completed",
        "thread.run.requires_action",
        "thread.run.completed",
    ]
    assert api.dummy_submit.called_with == [{"tool_call_id": "call1", "output": "out"}]  # type: ignore[attr-defined]
