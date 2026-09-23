"""Proxies Pilot → Orch UI API (P0 plan_pilot_hub_orch_absorb)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import api.v1.routes.pilot as pilot_mod


class _FakeResp:
    def __init__(self, status_code: int, payload: object, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text or ""
        self.content = b"{}" if payload is not None else b""

    def json(self) -> object:
        return self._payload


class _FakeClient:
    last_url: str | None = None
    last_method: str | None = None
    last_json: dict[str, object] | None = None
    last_params: object = None

    def __init__(self, *a: object, **k: object) -> None:
        pass

    async def __aenter__(self) -> "_FakeClient":
        return self

    async def __aexit__(self, *a: object) -> None:
        return None

    async def get(self, url: str, params: object = None) -> _FakeResp:
        _FakeClient.last_method = "GET"
        _FakeClient.last_url = url
        _FakeClient.last_params = params
        if url.endswith("/lyra/state"):
            return _FakeResp(200, {"gauges": {"chaleur": 70}})
        if url.endswith("/agents/map"):
            return _FakeResp(200, {"agents": [{"id": "a1"}]})
        if url.endswith("/providers/catalog"):
            return _FakeResp(200, {"providers": []})
        if url.endswith("/monitor/cockpit"):
            return _FakeResp(200, {"ram": 1})
        if url.endswith("/monitor/agents"):
            return _FakeResp(200, {"agents": []})
        if "/chat/conversations" in url:
            return _FakeResp(200, {"conversations": [{"id": "c1"}]})
        if "/chat/context/" in url:
            return _FakeResp(
                200,
                {
                    "conversation_id": "c1",
                    "turns": [
                        {"role": "user", "content": "bonjour"},
                        {"role": "assistant", "content": "salut"},
                    ],
                },
            )
        if url.endswith("/health"):
            return _FakeResp(200, {"status": "ok"})
        return _FakeResp(404, {}, text="missing")

    async def post(self, url: str, json: dict[str, object] | None = None) -> _FakeResp:
        _FakeClient.last_method = "POST"
        _FakeClient.last_url = url
        _FakeClient.last_json = json
        if url.endswith("/ask"):
            return _FakeResp(200, {"response": {"role": "assistant", "content": "hi"}})
        if url.endswith("/lyra/update"):
            return _FakeResp(200, {"status": "ok", "gauges": {"chaleur": 71}})
        if url.endswith("/archive") or url.endswith("/unarchive"):
            return _FakeResp(200, {"ok": True})
        return _FakeResp(404, {}, text="missing")

    async def delete(self, url: str) -> _FakeResp:
        _FakeClient.last_method = "DELETE"
        _FakeClient.last_url = url
        return _FakeResp(200, {"deleted": True})


@pytest.fixture
def orch_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("LBG_ORCH_UI_API_URL", "http://orch-fake:3000")
    monkeypatch.setattr(pilot_mod.httpx, "AsyncClient", _FakeClient)
    from main import app

    return TestClient(app)


def test_orch_disabled_when_url_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_ORCH_UI_API_URL", "")
    from main import app

    client = TestClient(app)
    r = client.get("/v1/pilot/orch/lyra/state")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is False
    assert data.get("disabled") is True


def test_orch_lyra_state(orch_client: TestClient) -> None:
    r = orch_client.get("/v1/pilot/orch/lyra/state")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["gauges"]["chaleur"] == 70
    assert _FakeClient.last_url == "http://orch-fake:3000/lyra/state"


def test_orch_lyra_update(orch_client: TestClient) -> None:
    r = orch_client.post("/v1/pilot/orch/lyra/update", json={"gauge": "chaleur", "delta": 1})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert _FakeClient.last_json == {"gauge": "chaleur", "delta": 1, "reset": False}


def test_orch_ask(orch_client: TestClient) -> None:
    r = orch_client.post(
        "/v1/pilot/orch/ask",
        json={"prompt": "bonjour", "mode": "auto", "profile": "chaleureux"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["response"]["content"] == "hi"
    assert _FakeClient.last_url == "http://orch-fake:3000/ask"
    assert "web_lookup" not in data


def test_orch_ask_web_lookup_enriches_prompt(
    orch_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _fake_enrich(prompt: str):
        # Pas de hits → forward Orch avec prompt enrichi
        return (
            prompt + " — (Consignes) Hits: (aucun)",
            {
                "ok": False,
                "query": "Edgar",
                "hit_count": 0,
                "sources": [],
                "ms": 9.0,
                "direct_reply": None,
            },
        )

    monkeypatch.setattr("services.web_lookup.enrich_ask_prompt", _fake_enrich)
    prompt = (
        "Bonjour, je cherche un vieux film d'animation : "
        "Le Voyage d'Edgar dans la forêt magique ?"
    )
    r = orch_client.post(
        "/v1/pilot/orch/ask",
        json={"prompt": prompt, "mode": "auto", "profile": "chaleureux"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["web_lookup"]["query"] == "Edgar"
    assert data["timeline"][0]["kind"] == "web_lookup"
    sent = _FakeClient.last_json or {}
    assert prompt in str(sent.get("prompt") or "")


def test_orch_ask_web_lookup_direct_reply(
    orch_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _FakeClient.last_url = None
    _FakeClient.last_json = None

    async def _fake_enrich(prompt: str):
        return (
            prompt,
            {
                "ok": True,
                "query": "Edgar",
                "hit_count": 1,
                "sources": ["wikipedia_fr"],
                "ms": 12.0,
                "hits": [{"title": "Le Voyage d'Edgar"}],
                "direct_reply": "Probable : **Le Voyage d'Edgar**\nSource : https://ex.test",
            },
        )

    monkeypatch.setattr("services.web_lookup.enrich_ask_prompt", _fake_enrich)
    r = orch_client.post(
        "/v1/pilot/orch/ask",
        json={
            "prompt": "Je cherche un film d'animation Le Voyage d'Edgar",
            "mode": "auto",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["response"]["source"] == "web_lookup"
    assert "Le Voyage d'Edgar" in data["response"]["content"]
    assert data["timeline"][0]["kind"] == "web_lookup"
    assert data["timeline"][1]["kind"] == "answer"
    assert _FakeClient.last_url is None


def test_orch_agents_map_and_providers(orch_client: TestClient) -> None:
    r = orch_client.get("/v1/pilot/orch/agents/map")
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert r.json()["agents"][0]["id"] == "a1"

    r2 = orch_client.get("/v1/pilot/orch/providers/catalog")
    assert r2.status_code == 200
    assert r2.json()["ok"] is True


def test_orch_monitor_and_conversations(orch_client: TestClient) -> None:
    assert orch_client.get("/v1/pilot/orch/monitor/cockpit").json()["ok"] is True
    assert orch_client.get("/v1/pilot/orch/monitor/agents").json()["ok"] is True
    r = orch_client.get("/v1/pilot/orch/chat/conversations")
    assert r.status_code == 200
    assert r.json()["conversations"][0]["id"] == "c1"


def test_orch_chat_archive_delete(orch_client: TestClient) -> None:
    assert orch_client.post("/v1/pilot/orch/chat/conversations/c1/archive").json()["ok"] is True
    assert orch_client.post("/v1/pilot/orch/chat/conversations/c1/unarchive").json()["ok"] is True
    assert orch_client.delete("/v1/pilot/orch/chat/conversations/c1").json()["ok"] is True


def test_orch_chat_context(orch_client: TestClient) -> None:
    r = orch_client.get("/v1/pilot/orch/chat/context/c1")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["turns"][0]["content"] == "bonjour"
    assert _FakeClient.last_url == "http://orch-fake:3000/chat/context/c1"


def test_orch_health(orch_client: TestClient) -> None:
    r = orch_client.get("/v1/pilot/orch/health")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["upstream_base"] == "http://orch-fake:3000"
