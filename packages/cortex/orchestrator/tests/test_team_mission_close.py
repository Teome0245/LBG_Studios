"""Tests Vague 4 — clôture mission Lyra + prune mémoire (sans orchestrator.main)."""

from __future__ import annotations

import os
import sys
import types
import time
from pathlib import Path

import pytest

if "hybrid_proactive_agent" not in sys.modules:
    _stub = types.ModuleType("hybrid_proactive_agent")

    class LongTermMemoryStore:  # noqa: N801
        pass

    class MemoryEntry:  # noqa: N801
        pass

    _stub.LongTermMemoryStore = LongTermMemoryStore  # type: ignore[attr-defined]
    _stub.MemoryEntry = MemoryEntry  # type: ignore[attr-defined]
    sys.modules["hybrid_proactive_agent"] = _stub

os.environ["LBG_TEAM_DB_PATH"] = ":memory:"
os.environ["LBG_TEAM_CAMPUS_CONDUCTOR_ENABLED"] = "1"
os.environ["LBG_TEAM_CAMPUS_MISSION_AUTO_CLOSE"] = "1"
os.environ["LBG_TEAM_BUS_HOOKS"] = "0"
os.environ["LBG_TEAM_MEMORY_ENABLED"] = "1"

from team import campus_conductor  # noqa: E402
from team import memory as team_memory  # noqa: E402
from team import store as team_store  # noqa: E402


@pytest.fixture(autouse=True)
def _reset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_TEAM_DB_PATH", ":memory:")
    monkeypatch.setenv("LBG_TEAM_CAMPUS_CONDUCTOR_ENABLED", "1")
    monkeypatch.setenv("LBG_TEAM_CAMPUS_MISSION_AUTO_CLOSE", "1")
    monkeypatch.setenv("LBG_TEAM_BUS_HOOKS", "0")
    monkeypatch.setenv("LBG_TEAM_MISSION_PATH", str(tmp_path / "campus_mission.json"))
    monkeypatch.setenv("LBG_TEAM_MEMORY_PATH", str(tmp_path / "mem.jsonl"))
    monkeypatch.setenv("LBG_TEAM_MEMORY_ENABLED", "1")
    monkeypatch.setenv("LBG_TEAM_MEMORY_MAX_ENTRIES", "3")
    team_store.reset_for_tests()
    campus_conductor._mission_loaded = False  # type: ignore[attr-defined]
    campus_conductor._set_mission({})
    campus_conductor._set_report({})
    campus_conductor._set_decision({})


def _open_mission_with_tasks(*, qa_ok: bool = True, pending: bool = False) -> dict:
    qa = team_store.create_task(
        role="qa",
        objective="smoke mission",
        actor_id="test:mission",
        context={"_campus_mission_id": "m1"},
    )
    pm = team_store.create_task(
        role="pm",
        objective="brief mission",
        actor_id="test:mission",
        context={"_campus_mission_id": "m1"},
    )
    if not pending:
        team_store.update_task(qa.id, status="done", result={"ok": qa_ok, "kind": "qa"})
        team_store.update_task(pm.id, status="done", result={"ok": True, "kind": "pm"})
    mission = {
        "id": "m1",
        "objective": "valide le LAN",
        "status": "driving",
        "task_ids": [qa.id, pm.id],
        "created_ts": time.time(),
        "dry_run": False,
    }
    campus_conductor._set_mission(mission)
    return mission


def test_evaluate_not_closable_while_pending() -> None:
    _open_mission_with_tasks(pending=True)
    ev = campus_conductor.evaluate_mission_closure()
    assert ev["closable"] is False
    assert "active" in str(ev.get("reason") or "")


def test_evaluate_closed_success_smoke_green() -> None:
    _open_mission_with_tasks(qa_ok=True)
    ev = campus_conductor.evaluate_mission_closure()
    assert ev["closable"] is True
    assert ev["outcome"] == "closed"
    assert ev.get("smoke_ok") is True


def test_evaluate_closed_failed_smoke_red(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_TEAM_MISSION_BLOCK_CLOSE_ON_SMOKE_FAIL", "0")
    _open_mission_with_tasks(qa_ok=False)
    ev = campus_conductor.evaluate_mission_closure()
    assert ev["closable"] is True
    assert ev["outcome"] == "closed_failed"
    assert ev.get("smoke_ok") is False


def test_maybe_close_mission_auto() -> None:
    _open_mission_with_tasks(qa_ok=True)
    out = campus_conductor.maybe_close_mission()
    assert out is not None
    assert out["ok"] is True
    assert out["mission"]["status"] == "closed"
    assert campus_conductor.last_mission()["status"] == "closed"


def test_decide_action_mission_close_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    _open_mission_with_tasks(qa_ok=True)
    monkeypatch.setattr(campus_conductor, "analyze_idle", lambda snap=None: [])
    monkeypatch.setattr(campus_conductor, "_failed_agents", lambda snap=None: [])
    monkeypatch.setattr(campus_conductor, "_running_tasks", lambda: [])
    monkeypatch.setattr(campus_conductor, "_queued_tasks", lambda: [])
    monkeypatch.setattr(campus_conductor, "_busy_agent_ids", lambda running: set())
    dec = campus_conductor.decide_action(snap={"agents": []})
    assert dec["mode"] == "mission_close"


def test_act_closes_mission(monkeypatch: pytest.MonkeyPatch) -> None:
    _open_mission_with_tasks(qa_ok=True)
    monkeypatch.setattr(campus_conductor, "analyze_idle", lambda snap=None: [])
    monkeypatch.setattr(campus_conductor, "_failed_agents", lambda snap=None: [])
    monkeypatch.setattr(campus_conductor, "_running_tasks", lambda: [])
    monkeypatch.setattr(campus_conductor, "_queued_tasks", lambda: [])
    monkeypatch.setattr(campus_conductor, "_busy_agent_ids", lambda running: set())
    monkeypatch.setattr(campus_conductor, "_emit_conductor", lambda *a, **k: None)
    report = campus_conductor.act(dry_run=False)
    assert report["outcome"] == "mission_closed"
    assert campus_conductor.last_mission()["status"] == "closed"


def test_memory_prune_keeps_recent(tmp_path: Path) -> None:
    for i in range(5):
        team_memory.append_learning(
            agent_id="themis",
            summary=f"learning {i}",
            tags=["t"],
        )
        time.sleep(0.01)
    out = team_memory.prune_learnings(max_entries=3, max_age_days=30)
    assert out["ok"] is True
    assert out["before"] == 5
    assert out["after"] == 3
    assert out["removed"] == 2
    left = team_memory.list_learnings(limit=10)
    assert len(left) == 3


def test_mission_persists_across_reload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "campus_mission.json"
    monkeypatch.setenv("LBG_TEAM_MISSION_PATH", str(path))
    mission = {
        "id": "persist-1",
        "objective": "smoke persist",
        "status": "driving",
        "task_ids": [],
        "created_ts": time.time(),
    }
    campus_conductor._set_mission(mission)
    assert path.is_file()
    # Simule reboot process
    campus_conductor._last_mission = {}  # type: ignore[attr-defined]
    campus_conductor._mission_loaded = False  # type: ignore[attr-defined]
    loaded = campus_conductor.last_mission()
    assert loaded.get("id") == "persist-1"
    assert loaded.get("status") == "driving"
