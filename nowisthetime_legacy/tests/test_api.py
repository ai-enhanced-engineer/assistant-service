import importlib
import sys
import types

from fastapi.testclient import TestClient


def load_app(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    import openai

    class DummyRuns:
        def create(self, thread_id, assistant_id):
            self.created = (thread_id, assistant_id)
            return types.SimpleNamespace(id="run1")

        def retrieve(self, **_kwargs):
            return types.SimpleNamespace(status="completed")

    class DummyMessages:
        def __init__(self):
            self.created = None

        def create(self, thread_id, role, content):
            self.created = (thread_id, role, content)

        def list(self, **_kwargs):
            return types.SimpleNamespace(
                data=[
                    types.SimpleNamespace(
                        content=[types.SimpleNamespace(text=types.SimpleNamespace(value="assistant response"))]
                    )
                ]
            )

    class DummyThreads:
        def __init__(self):
            self.runs = DummyRuns()
            self.messages = DummyMessages()

        def create(self):
            return types.SimpleNamespace(id="thread1")

    class DummyBeta:
        def __init__(self):
            self.threads = DummyThreads()

    class DummyClient:
        def __init__(self):
            self.beta = DummyBeta()

    dummy_client = DummyClient()
    monkeypatch.setattr(openai, "__version__", "1.1.1", raising=False)
    monkeypatch.setattr(openai, "OpenAI", lambda **_: dummy_client)

    monkeypatch.setattr("nowisthetime_legacy.utilities.create_assistant", lambda _client: "asst1")
    import nowisthetime_legacy.utilities as utils

    sys.modules["utilities"] = utils

    sys.modules.pop("nowisthetime_legacy.main", None)
    module = importlib.import_module("nowisthetime_legacy.main")
    return module, dummy_client


def test_start_endpoint(monkeypatch):
    module, _ = load_app(monkeypatch)
    client = TestClient(module.app)

    response = client.get("/start")
    assert response.status_code == 200
    assert response.json() == {"thread_id": "thread1"}


def test_chat_endpoint(monkeypatch):
    module, dummy_client = load_app(monkeypatch)
    client = TestClient(module.app)

    payload = {"thread_id": "thread1", "message": "hello"}
    response = client.post("/chat", json=payload)

    assert response.status_code == 200
    assert response.json() == {"response": "assistant response"}
    assert dummy_client.beta.threads.messages.created == ("thread1", "user", "hello")
