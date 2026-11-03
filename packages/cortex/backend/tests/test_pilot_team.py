import pytest
from fastapi.testclient import TestClient

import api.v1.routes.pilot as pilot_mod


class _FakeResponse:
    def __init__(self, payload: dict[str, object], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code
        self.text = ""

    def json(self) -> dict[str, object]:
        return self._payload


class _FakeAsyncClient:
    last_call: dict[str, object] = {}

    def __init__(self, *args: object, **kwargs: object) -> None:
        pass

    async def __aenter__(self) -> "_FakeAsyncClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def post(self, url: str, json: dict[str, object] | None = None) -> _FakeResponse:
        _FakeAsyncClient.last_call = {"method": "POST", "url": url, "json": json}
        return _FakeResponse({"id": "task-1", "status": "queued", "role": "qa", "objective": "smoke"})

    async def get(self, url: str, params: dict[str, object] | None = None) -> _FakeResponse:
        _FakeAsyncClient.last_call = {"method": "GET", "url": url, "params": params}
        return _FakeResponse({"tasks": [{"id": "task-1", "role": "qa", "status": "done"}]})


def _client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("LBG_ORCHESTRATOR_URL", "http://fake:8010")
    monkeypatch.setattr(pilot_mod.httpx, "AsyncClient", _FakeAsyncClient)
    from backend.main import app

    return TestClient(app)


def test_pilot_team_create_proxy_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(monkeypatch)
    r = client.post("/v1/pilot/team/tasks", json={"role": "qa", "objective": "smoke LAN"})
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert data["id"] == "task-1"
    assert _FakeAsyncClient.last_call["url"].endswith("/v1/team/tasks")


def test_pilot_team_list_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(monkeypatch)
    r = client.get("/v1/pilot/team/tasks", params={"role": "qa"})
    assert r.status_code == 200
    assert r.json().get("ok") is True
    assert _FakeAsyncClient.last_call["params"]["role"] == "qa"


def test_pilot_team_run_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(monkeypatch)
    r = client.post("/v1/pilot/team/tasks/task-1/run", json={"approval_token": "tok"})
    assert r.status_code == 200
    assert _FakeAsyncClient.last_call["url"].endswith("/v1/team/tasks/task-1/run")


def test_pilot_team_messages_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(monkeypatch)
    r = client.get("/v1/pilot/team/messages", params={"task_id": "t1", "limit": 10})
    assert r.status_code == 200
    assert r.json().get("ok") is True
    assert _FakeAsyncClient.last_call["url"].endswith("/v1/team/messages")
    assert _FakeAsyncClient.last_call["params"]["task_id"] == "t1"

    r2 = client.post(
        "/v1/pilot/team/messages",
        json={
            "from_agent": "themis",
            "to_agent": "argus",
            "kind": "consult",
            "payload": {"topic": "smoke"},
            "task_id": "t1",
        },
    )
    assert r2.status_code == 200
    assert _FakeAsyncClient.last_call["method"] == "POST"
    assert _FakeAsyncClient.last_call["url"].endswith("/v1/team/messages")


def test_pilot_team_memory_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(monkeypatch)
    r = client.get("/v1/pilot/team/memory", params={"agent_id": "argus"})
    assert r.status_code == 200
    assert r.json().get("ok") is True
    assert _FakeAsyncClient.last_call["url"].endswith("/v1/team/memory")


def test_pilot_team_super_agent_endpoints(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(monkeypatch)
    # Test GET status
    r_status = client.get("/v1/pilot/team/super-agent/status")
    assert r_status.status_code == 200
    data_status = r_status.json()
    assert data_status["ok"] is True
    assert "code" in data_status["team"]
    assert "game" in data_status["team"]

    # Test POST event avec assainissement
    r_ev = client.post(
        "/v1/pilot/team/super-agent/event",
        json={
            "v": 1,
            "event": "session.tool_pre",
            "agent": "cline_code",
            "summary": "Execution avec token super_secret_123456789abc",
        },
    )
    assert r_ev.status_code == 200
    data_ev = r_ev.json()
    assert data_ev["ok"] is True
    filtered = data_ev["filtered_event"]
    assert filtered["domain"] == "code"
    assert "[REDACTED_SECRET]" in filtered["summary"]
    assert "super_secret_123456789abc" not in filtered["summary"]


    r2 = client.post(
        "/v1/pilot/team/memory",
        json={"agent_id": "argus", "summary": "smoke vert", "tags": ["qa"]},
    )
    assert r2.status_code == 200
    assert _FakeAsyncClient.last_call["method"] == "POST"
