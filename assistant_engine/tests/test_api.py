import types

import pytest
from fastapi.testclient import TestClient

from botbrew_commons import repositories as repos
from botbrew_commons.data_models import EngineAssistantConfig


@pytest.fixture()
def client(monkeypatch):
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

    import assistant_engine.main as main

    class DummyThreads:
        async def create(self):
            return types.SimpleNamespace(id="thread123")

    class DummyBeta:
        def __init__(self):
            self.threads = DummyThreads()

    main.api.client = types.SimpleNamespace(beta=DummyBeta())
    monkeypatch.setattr(main.api, "engine_config", types.SimpleNamespace(initial_message="hi"))
    return TestClient(main.app)


def test_start_endpoint(client):
    resp = client.get("/start")
    assert resp.status_code == 200
    assert resp.json() == {"thread_id": "thread123", "initial_message": "hi"}


def test_chat_endpoint(monkeypatch, client):
    import assistant_engine.main as main

    async def dummy_run(tid: str, msg: str):
        assert tid == "thread123"
        assert msg == "hello"
        return ["response"]

    monkeypatch.setattr(main.api, "_process_run", dummy_run)
    resp = client.post("/chat", json={"thread_id": "thread123", "message": "hello"})
    assert resp.status_code == 200
    assert resp.json() == {"responses": ["response"]}


def _make_api(monkeypatch):
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

    from assistant_engine.main import AssistantEngineAPI

    return AssistantEngineAPI()


def test_dependency_injected_client_is_used(monkeypatch):
    api = _make_api(monkeypatch)

    class DummyThreads:
        async def create(self):
            return types.SimpleNamespace(id="di")

    class DummyBeta:
        def __init__(self):
            self.threads = DummyThreads()

    class DummyClient:
        def __init__(self):
            self.beta = DummyBeta()
            self.closed = False

        async def aclose(self):
            self.closed = True

    api.client = DummyClient()

    with TestClient(api.app) as test_client:
        resp = test_client.get("/start")
        assert resp.status_code == 200
        assert resp.json() == {"thread_id": "di", "initial_message": "hi"}

    assert api.client.closed is False


def test_lifespan_opens_and_closes_client(monkeypatch):
    api = _make_api(monkeypatch)

    class DummyThreads:
        async def create(self):
            return types.SimpleNamespace(id="ls")

    class DummyBeta:
        def __init__(self):
            self.threads = DummyThreads()

    class DummyOpenAI:
        def __init__(self, *_, **__):
            self.beta = DummyBeta()
            self.closed = False

        async def aclose(self):
            self.closed = True

    monkeypatch.setattr("assistant_engine.main.AsyncOpenAI", DummyOpenAI)
    api.client = None

    with TestClient(api.app) as test_client:
        resp = test_client.get("/start")
        assert resp.status_code == 200
        assert resp.json() == {"thread_id": "ls", "initial_message": "hi"}

    assert isinstance(api.client, DummyOpenAI)
    assert api.client.closed is True
