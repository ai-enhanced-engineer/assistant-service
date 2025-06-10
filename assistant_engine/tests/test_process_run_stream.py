import types

import pytest

pytestmark = pytest.mark.asyncio


class DummyMessages:
    async def create(self, thread_id: str, role: str, content: str):
        self.created = (thread_id, role, content)

    async def retrieve(self, thread_id: str, message_id: str):
        assert thread_id == "thread"
        assert message_id == "msg1"
        return types.SimpleNamespace(content=[types.SimpleNamespace(text=types.SimpleNamespace(value="hello"))])


class DummyRuns:
    def __init__(self):
        self.created_kwargs = None

    async def create(self, thread_id: str, assistant_id: str, stream: bool):
        assert thread_id == "thread"
        assert assistant_id == "aid"
        assert stream is True
        self.created_kwargs = stream

        async def gen():
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
                    id="run1", required_action=types.SimpleNamespace(type="submit_tool_outputs")
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


async def dummy_submit(*_args, **kwargs):
    dummy_submit.called_with = list(kwargs["tool_outputs"])


async def dummy_function():
    return "out"


@pytest.fixture()
def api(monkeypatch):
    monkeypatch.setenv("PROJECT_ID", "p")
    monkeypatch.setenv("BUCKET_ID", "b")
    monkeypatch.setenv("CLIENT_ID", "c")
    monkeypatch.setenv("ASSISTANT_ID", "aid")

    from botbrew_commons import repositories as repos

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
            return types.SimpleNamespace(
                assistant_id="aid",
                assistant_name="name",
                initial_message="hi",
            )

    monkeypatch.setattr(repos, "GCPSecretRepository", DummySecretRepo)
    monkeypatch.setattr(repos, "GCPConfigRepository", DummyConfigRepo)

    from assistant_engine import main

    monkeypatch.setattr(main, "GCPSecretRepository", DummySecretRepo)
    monkeypatch.setattr(main, "GCPConfigRepository", DummyConfigRepo)

    api = main.AssistantEngineAPI()
    api.client = DummyClient()
    monkeypatch.setattr(main, "submit_tool_outputs_with_backoff", dummy_submit)
    monkeypatch.setattr(main, "TOOL_MAP", {"func": lambda: "out"})
    return api


async def test_process_run(api):
    result = await api._process_run("thread", "hi")
    assert result == ["hello"]
    assert dummy_submit.called_with == [{"tool_call_id": "call1", "output": "out"}]


async def test_process_run_stream(api):
    events = [event async for event in api._process_run_stream("thread", "hi")]
    assert [e.event for e in events] == [
        "thread.run.created",
        "thread.run.step.completed",
        "thread.run.step.completed",
        "thread.run.requires_action",
        "thread.run.completed",
    ]
    assert dummy_submit.called_with == [{"tool_call_id": "call1", "output": "out"}]
