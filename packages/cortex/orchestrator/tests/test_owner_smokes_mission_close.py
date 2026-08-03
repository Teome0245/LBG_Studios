"""Tests A2 — owner smokes + anti-clôture (stub hybrid_proactive_agent)."""

from __future__ import annotations

import os
import sys
from types import ModuleType

import pytest

# Stub legacy avant import team.roles / campus_conductor
if "hybrid_proactive_agent" not in sys.modules:
    _stub = ModuleType("hybrid_proactive_agent")

    class LongTermMemoryStore:  # noqa: N801
        pass

    class MemoryEntry:  # noqa: N801
        pass

    _stub.LongTermMemoryStore = LongTermMemoryStore
    _stub.MemoryEntry = MemoryEntry
    sys.modules["hybrid_proactive_agent"] = _stub

os.environ["LBG_TEAM_DB_PATH"] = ":memory:"

from team import campus_conductor  # noqa: E402
from team import owner_smokes  # noqa: E402
from team import store as team_store  # noqa: E402


@pytest.fixture(autouse=True)
def _reset(monkeypatch: pytest.MonkeyPatch) -> None:
    team_store.reset_for_tests()
    campus_conductor._set_mission({})
    monkeypatch.setenv("LBG_TEAM_MISSION_BLOCK_CLOSE_ON_SMOKE_FAIL", "1")


def test_owners_for_bundle_godot_login() -> None:
    assert "hermes_m11" in owner_smokes.owners_for_bundle("godot_login")
    assert "hermes_m12" in owner_smokes.owners_for_bundle("godot_login")


def test_owners_for_bundle_godot_craft() -> None:
    assert owner_smokes.owners_for_bundle("godot_craft") == ["iris_m10"]
    assert "iris_m10" in owner_smokes.OWNER_SCRIPTS
    assert "iris_m10" in owner_smokes.owners_for_bundle("godot_client")


def test_block_close_when_qa_smoke_red() -> None:
    qa = team_store.create_task(
        role="qa",
        objective="Owner smoke fail",
        actor_id="test",
        context={"owner_smoke_bundle": "godot_login", "mmo_jalon": True},
    )
    team_store.update_task(
        qa.id,
        status="done",
        result={"ok": False, "owner_smokes": {"ok": False}},
    )
    campus_conductor._set_mission(
        {
            "id": "mission-smoke-red",
            "status": "open",
            "objective": "P1 m12",
            "task_ids": [qa.id],
            "require_owner_smoke": True,
        }
    )
    ev = campus_conductor.evaluate_mission_closure()
    assert ev.get("closable") is False
    assert ev.get("blocked_on_smoke") is True
    assert ev.get("smoke_ok") is False


def test_close_ok_when_owner_smoke_green() -> None:
    qa = team_store.create_task(
        role="qa",
        objective="Owner smoke ok",
        actor_id="test",
        context={"owner_smoke_bundle": "godot_login", "mmo_jalon": True},
    )
    hermes = team_store.create_task(
        role="dev_godot",
        objective="Hermès audit",
        actor_id="test",
        context={"mmo_jalon": True, "godot_dev_persona": "hermes"},
    )
    team_store.update_task(
        qa.id,
        status="done",
        result={"ok": True, "owner_smokes": {"ok": True, "bundle": "godot_login"}},
    )
    team_store.update_task(hermes.id, status="done", result={"ok": True})
    campus_conductor._set_mission(
        {
            "id": "mission-smoke-green",
            "status": "open",
            "objective": "P1 m12",
            "task_ids": [qa.id, hermes.id],
        }
    )
    ev = campus_conductor.evaluate_mission_closure()
    assert ev.get("closable") is True
    assert ev.get("outcome") == "closed"
    assert ev.get("smoke_ok") is True


def test_godot_mission_without_qa_not_closable() -> None:
    hermes = team_store.create_task(
        role="dev_godot",
        objective="Hermès only",
        actor_id="test",
        context={"mmo_jalon": True, "godot_dev_persona": "hermes"},
    )
    team_store.update_task(hermes.id, status="done", result={"ok": True})
    campus_conductor._set_mission(
        {
            "id": "mission-no-qa",
            "status": "open",
            "objective": "missing qa",
            "task_ids": [hermes.id],
        }
    )
    ev = campus_conductor.evaluate_mission_closure()
    assert ev.get("closable") is False
    assert "owner_smoke" in str(ev.get("reason") or "")
