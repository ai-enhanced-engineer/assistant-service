from fastapi.testclient import TestClient

from assistant_engine.api import app

client = TestClient(app)


def test_start_and_chat():
    resp = client.get("/start")
    assert resp.status_code == 200
    tid = resp.json()["thread_id"]

    resp = client.post("/chat", json={"thread_id": tid, "message": "hello"})
    assert resp.status_code == 200
    assert "hello" in resp.json()["response"]
