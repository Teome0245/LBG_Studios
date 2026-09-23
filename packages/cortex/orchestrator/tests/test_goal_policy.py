"""Tests Agency C — goal_policy + Self goals + ensure."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("LBG_TEAM_DB_PATH", ":memory:")

from services import self_state as svc_self  # noqa: E402
from team import goal_policy  # noqa: E402


@pytest.fixture(autouse=True)
def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LBG_SELF_STATE_ENABLED", "1")
    monkeypatch.setenv("LBG_SELF_STATE_PATH", str(tmp_path / "self" / "state.json"))
    monkeypatch.setenv("LBG_LIA_GOALS_ENABLED", "1")
    monkeypatch.setenv("LBG_LIA_GOAL_SOCIAL_HUNGER_MIN", "0.4")
    monkeypatch.setenv("LBG_LIA_GOAL_CURIOSITY_MIN", "0.5")
    monkeypatch.setenv("LBG_LIA_GOAL_TENSION_MIN", "0.55")
    monkeypatch.setenv("LBG_TEAM_DB_PATH", ":memory:")
    svc_self.reset_cache_for_tests()


def test_propose_lia_goals_from_drives() -> None:
    goals = goal_policy.propose_lia_goals(
        drives={"social_hunger": 0.8, "curiosity": 0.2, "tension": 0.1},
        existing_goals=[],
    )
    assert len(goals) == 1
    assert goals[0]["origin"] == "drive:social_hunger"
    assert goals[0]["owner"] == "lia"
    assert goals[0]["status"] == "active"


def test_propose_respects_max_and_origin_dedup() -> None:
    existing = goal_policy.propose_lia_goals(
        drives={"social_hunger": 0.9, "curiosity": 0.1, "tension": 0.1},
    )
    more = goal_policy.propose_lia_goals(
        drives={"social_hunger": 0.95, "curiosity": 0.9, "tension": 0.9},
        existing_goals=existing,
    )
    # social already active → only curiosity + tension, capped by max 2 total → 1 new
    assert len(existing) == 1
    assert len(more) == 1
    assert more[0]["origin"] in ("drive:curiosity", "drive:tension")


def test_ensure_lia_goals_and_complete() -> None:
    svc_self.persist_state(svc_self.default_state())
    svc_self.patch_drives({"social_hunger": 0.9, "curiosity": 0.1, "tension": 0.1})
    st = svc_self.ensure_lia_goals()
    assert st is not None
    active = [g for g in st["goals"] if g.get("status") == "active"]
    assert len(active) >= 1
    gid = active[0]["id"]
    before = float(st["drives"]["social_hunger"])
    st2 = svc_self.complete_goal(gid, last_action="approach_player", decay_amount=0.3)
    assert st2 is not None
    done = [g for g in st2["goals"] if g.get("id") == gid][0]
    assert done["status"] == "done"
    assert float(st2["drives"]["social_hunger"]) == pytest.approx(max(0.0, before - 0.3))


def test_self_status_ensures_goals_route() -> None:
    from main import app

    svc_self.persist_state(svc_self.default_state())
    svc_self.patch_drives({"curiosity": 0.95, "social_hunger": 0.0, "tension": 0.0})
    client = TestClient(app)
    r = client.get("/v1/self/status?ensure_goals=1")
    assert r.status_code == 200
    data = r.json()
    goals = data["state"]["goals"]
    assert any(g.get("origin") == "drive:curiosity" for g in goals if isinstance(g, dict))
    assert data["meta"]["lia_goals"]["enabled"] is True


def test_complete_goal_route() -> None:
    from main import app

    svc_self.persist_state(svc_self.default_state())
    svc_self.patch_drives({"tension": 0.9})
    svc_self.ensure_lia_goals()
    active = svc_self.list_goals(owner="lia", status="active")
    assert active
    client = TestClient(app)
    r = client.post(
        "/v1/self/goals/complete",
        json={"goal_id": active[0]["id"], "last_action": "perform:dance", "decay_amount": 0.2},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True
