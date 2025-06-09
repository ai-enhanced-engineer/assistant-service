import types
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from botbrew_commons import repositories as repos
from botbrew_commons.data_models import EngineAssistantConfig


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

    from assistant_engine.main import AssistantEngineAPI

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

    api = AssistantEngineAPI()
    dummy_client = DummyClient()
    api.client = dummy_client

    return api, dummy_client


def test_lifespan(api):
    api_obj, dummy_client = api
    with TestClient(api_obj.app):
        assert api_obj.client is dummy_client
        dummy_client.aclose.assert_not_awaited()
    dummy_client.aclose.assert_awaited_once()


def test_start_endpoint(api):
    api_obj, dummy_client = api
    with TestClient(api_obj.app) as client:
        resp = client.get("/start")
        assert resp.status_code == 200
        assert resp.json() == {"thread_id": "thread123", "initial_message": "hi"}
    dummy_client.aclose.assert_awaited_once()


def test_chat_endpoint(monkeypatch, api):
    api_obj, dummy_client = api

    async def dummy_run(tid: str, msg: str):
        assert tid == "thread123"
        assert msg == "hello"
        return ["response"]

    monkeypatch.setattr(api_obj, "_process_run", dummy_run)
    with TestClient(api_obj.app) as client:
        resp = client.post("/chat", json={"thread_id": "thread123", "message": "hello"})
        assert resp.status_code == 200
        assert resp.json() == {"responses": ["response"]}
    dummy_client.aclose.assert_awaited_once()


def test_stream_endpoint(monkeypatch, api):
    api_obj, dummy_client = api

    async def dummy_stream(tid: str, msg: str):
        assert tid == "thread123"
        assert msg == "hello"
        yield types.SimpleNamespace(model_dump_json=lambda: "event1")
        yield types.SimpleNamespace(model_dump_json=lambda: "event2")

    monkeypatch.setattr(api_obj, "_process_run_stream", dummy_stream)

    with TestClient(api_obj.app) as client, client.websocket_connect("/stream") as websocket:
        websocket.send_json({"thread_id": "thread123", "message": "hello"})
        assert websocket.receive_text() == "event1"
        assert websocket.receive_text() == "event2"
        with pytest.raises(WebSocketDisconnect):
            websocket.receive_text()
    dummy_client.aclose.assert_awaited_once()
