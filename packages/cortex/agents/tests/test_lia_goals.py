"""Tests Agency C — client lia_goals (HTTP mock)."""

from __future__ import annotations

import httpx
import pytest

from lbg_agents import lia_goals


@pytest.fixture(autouse=True)
def _env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_LIA_GOALS_ENABLED", "1")
    monkeypatch.setenv("LBG_ORCHESTRATOR_URL", "http://127.0.0.1:8010")
    monkeypatch.setenv("LBG_CORE3_IA_SIDECAR_URL", "http://127.0.0.1:8791")


def test_pick_active_lia_goal_priority() -> None:
    payload = {
        "enabled": True,
        "state": {
            "goals": [
                {
                    "id": "g1",
                    "owner": "lia",
                    "status": "active",
                    "priority": 0.4,
                    "origin": "drive:curiosity",
                },
                {
                    "id": "g2",
                    "owner": "lia",
                    "status": "active",
                    "priority": 0.9,
                    "origin": "drive:social_hunger",
                },
                {"id": "g3", "owner": "lia", "status": "done", "priority": 1.0},
            ]
        },
    }
    g = lia_goals.pick_active_lia_goal(payload)
    assert g is not None
    assert g["id"] == "g2"


def test_try_execute_active_goal(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "/v1/self/status" in url:
            return httpx.Response(
                200,
                json={
                    "enabled": True,
                    "state": {
                        "goals": [
                            {
                                "id": "goal_abc",
                                "owner": "lia",
                                "status": "active",
                                "priority": 0.8,
                                "origin": "drive:curiosity",
                                "title": "Explorer",
                            }
                        ]
                    },
                },
            )
        if "/v1/enqueue" in url:
            calls.append("enqueue")
            return httpx.Response(200, json={"ok": True, "line": "perform|...|wave"})
        if "/v1/self/goals/complete" in url:
            calls.append("complete")
            return httpx.Response(200, json={"ok": True, "state": {}})
        return httpx.Response(404, json={"ok": False})

    transport = httpx.MockTransport(handler)
    _real = httpx.Client

    def _client(*a, **k):
        k["transport"] = transport
        return _real(*a, **k)

    monkeypatch.setattr(httpx, "Client", _client)
    out = lia_goals.try_execute_active_goal(snapshot={"zone": "tatooine", "x": 1, "y": 2, "z": 3})
    assert out is not None
    assert out["ok"] is True
    assert out["reason"].startswith("lia_goal:goal_abc")
    assert "enqueue" in calls
    assert "complete" in calls


def test_disabled_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_LIA_GOALS_ENABLED", "0")
    assert lia_goals.try_execute_active_goal() is None
