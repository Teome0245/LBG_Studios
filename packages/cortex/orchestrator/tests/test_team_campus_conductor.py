"""Tests Campus Conductor (Lyra)."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

os.environ["LBG_TEAM_DB_PATH"] = ":memory:"
os.environ["LBG_TEAM_CAMPUS_CONDUCTOR_ENABLED"] = "1"
os.environ["LBG_TEAM_CAMPUS_CONDUCTOR_MAX_BUSY"] = "4"
os.environ["LBG_TEAM_CAMPUS_CONDUCTOR_MAX_STARTS"] = "1"
os.environ.setdefault("LBG_DEVOPS_HTTP_ALLOWLIST", "http://127.0.0.1:8010/healthz,http://127.0.0.1:8000/healthz")

from orchestrator.main import app  # noqa: E402
from team import campus_conductor  # noqa: E402
from team import roles as team_roles  # noqa: E402
from team import store as team_store  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_team_db(monkeypatch: pytest.MonkeyPatch) -> None:
    team_store._conn = None  # type: ignore[attr-defined]
    team_roles.set_dispatch_for_tests(None)
    monkeypatch.setenv("LBG_TEAM_CAMPUS_CONDUCTOR_ENABLED", "1")
    monkeypatch.setenv("LBG_TEAM_CAMPUS_CONDUCTOR_MAX_STARTS", "1")
    campus_conductor._set_report({})


def test_campus_status_endpoint() -> None:
    client = TestClient(app)
    r = client.get("/v1/team/campus/status")
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    assert body.get("conductor_agent_id") == "studio_conductor_lyra"


def test_campus_conduct_dry_run_prefers_queued(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    created = client.post(
        "/v1/team/tasks",
        json={
            "role": "qa",
            "objective": "Smoke conductor dry-run",
            "actor_id": "test:campus",
            "approval_required": False,
            "context": {},
        },
    )
    assert created.status_code == 200
    task_id = created.json()["id"]

    started: list[str] = []

    def _fake_run(tid: str, *, approval_token: str | None = None):
        started.append(tid)
        return team_store.get_task(tid)

    monkeypatch.setattr(team_roles, "run_task", _fake_run)

    r = client.post("/v1/team/campus/conduct", json={"dry_run": True})
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    assert body.get("dry_run") is True
    assert any(c.get("task_id") == task_id for c in (body.get("candidates") or []))
    assert started == []


def test_campus_conduct_starts_in_background(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    created = client.post(
        "/v1/team/tasks",
        json={
            "role": "ops",
            "objective": "Sonde conductor start",
            "actor_id": "test:campus",
            "approval_required": False,
            "context": {},
        },
    )
    task_id = created.json()["id"]
    started: list[str] = []

    class ImmediateThread:
        def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None):
            self._target = target
            self._args = args
            self._kwargs = kwargs or {}

        def start(self) -> None:
            if self._target:
                self._target(*self._args, **self._kwargs)

    def _fake_run(tid: str) -> None:
        started.append(tid)
        team_store.update_task(tid, status="done", result={"ok": True, "kind": "fake"})

    monkeypatch.setattr(campus_conductor.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(campus_conductor, "_run_task_safe", _fake_run)

    r = client.post("/v1/team/campus/conduct", json={"dry_run": False, "max_starts": 1})
    assert r.status_code == 200
    body = r.json()
    assert body.get("outcome") == "started"
    assert any(s.get("task_id") == task_id for s in (body.get("started") or []))
    assert task_id in started


def test_campus_skips_approval_required() -> None:
    client = TestClient(app)
    created = client.post(
        "/v1/team/tasks",
        json={
            "role": "dev_game",
            "objective": "Needs L2",
            "actor_id": "test:campus",
            "approval_required": True,
            "context": {},
        },
    )
    task_id = created.json()["id"]
    r = client.post("/v1/team/campus/conduct", json={"dry_run": True})
    body = r.json()
    skipped = body.get("skipped") or []
    assert any(s.get("task_id") == task_id and s.get("reason") == "approval_required" for s in skipped)


def test_campus_coffee_fill_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_TEAM_CAMPUS_CONDUCTOR_COFFEE_FILL", "1")
    monkeypatch.setenv("LBG_TEAM_CAMPUS_CONDUCTOR_COFFEE_MIN", "2")
    monkeypatch.setenv("LBG_TEAM_CAMPUS_CONDUCTOR_COFFEE_MAX_SPAWN", "1")
    monkeypatch.setenv("LBG_TEAM_CAMPUS_CONDUCTOR_COFFEE_COOLDOWN_S", "60")
    monkeypatch.setenv("LBG_TEAM_PLAYBOOK_SCORING", "1")
    campus_conductor._last_coffee_spawn_ts = 0.0

    def fake_idle(_snap=None):
        return [
            {"agent_id": "studio_qa_argus", "display_name": "Argus", "reason": "coffee_available", "location": "zone_coffee"},
            {"agent_id": "studio_ops_hephaistos", "display_name": "Héphaïstos", "reason": "coffee_available", "location": "zone_coffee"},
            {"agent_id": "studio_pm_themis", "display_name": "Thémis", "reason": "coffee_available", "location": "zone_coffee"},
        ]

    monkeypatch.setattr(campus_conductor, "analyze_idle", fake_idle)
    monkeypatch.setattr(campus_conductor, "_queued_tasks", lambda: [])
    monkeypatch.setattr(campus_conductor, "_running_tasks", lambda: [])
    monkeypatch.setattr(campus_conductor, "_busy_agent_ids", lambda _r: set())
    monkeypatch.setattr(campus_conductor, "_coffee_utility_ok", lambda role, key: (True, "ok"))

    client = TestClient(app)
    r = client.post("/v1/team/campus/conduct", json={"dry_run": True, "max_starts": 2})
    assert r.status_code == 200
    body = r.json()
    props = body.get("coffee_proposals") or []
    assert props, body
    assert props[0].get("kind") == "coffee_fill"
    assert props[0].get("role") in ("qa", "ops", "pm", "admin_infra")
    assert "playbook_score" in props[0]
    assert props[0].get("context", {}).get("utility_key")

def test_campus_act_observe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        campus_conductor,
        "decide_action",
        lambda snap=None: {"mode": "observe", "reason": "test observe"},
    )
    client = TestClient(app)
    r = client.post("/v1/team/campus/act", json={"dry_run": True})
    assert r.status_code == 200
    assert r.json().get("outcome") == "observe"


def test_campus_mission_dry_run() -> None:
    client = TestClient(app)
    r = client.post(
        "/v1/team/campus/mission",
        json={"objective": "valide le LAN et fais un brief PM", "dry_run": True, "auto_act": False},
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    assert body.get("created")
    assert body["mission"].get("dry_run") is True


def test_campus_utility_skips_recent_qa(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_TEAM_CAMPUS_CONDUCTOR_COFFEE_UTILITY_S", "21600")
    # create a recent successful qa task
    t = team_store.create_task(
        role="qa",
        objective="Smoke recent",
        actor_id="test:util",
        approval_required=False,
        context={"_campus_coffee_fill": True},
    )
    team_store.update_task(t.id, status="done", result={"ok": True, "kind": "qa_smoke"})
    ok, why = campus_conductor._coffee_utility_ok("qa", "qa_smoke")
    assert ok is False
    assert "recent" in why
