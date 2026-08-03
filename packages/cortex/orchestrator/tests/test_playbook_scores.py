"""Tests A3 — scoring playbooks coffee-fill."""

from __future__ import annotations

import os

os.environ["LBG_TEAM_DB_PATH"] = ":memory:"
os.environ["LBG_TEAM_MEMORY_ENABLED"] = "1"
os.environ["LBG_TEAM_PLAYBOOK_SCORING"] = "1"

from team import playbook_scores  # noqa: E402
from team import store as team_store  # noqa: E402


def setup_function() -> None:
    team_store._conn = None  # type: ignore[attr-defined]


def test_prior_score_without_history() -> None:
    info = playbook_scores.score_utility_key("qa_smoke", role="qa")
    assert info["n"] == 0
    assert info["eligible"] is True
    assert 0.0 < float(info["score"]) <= 1.0


def test_score_from_task_history() -> None:
    for ok in (True, True, False):
        t = team_store.create_task(
            role="qa",
            objective="coffee score hist",
            actor_id="test:score",
            approval_required=False,
            context={"_campus_coffee_fill": True, "utility_key": "qa_godot_owners"},
        )
        team_store.update_task(
            t.id,
            status="done" if ok else "failed",
            result={"ok": ok, "kind": "qa_owner_smokes", "utility_key": "qa_godot_owners"},
        )
    info = playbook_scores.score_utility_key("qa_godot_owners", role="qa")
    assert info["n"] == 3
    assert info["successes"] == 2
    assert info["failures"] == 1
    assert 0.4 <= float(info["score"]) <= 0.9


def test_rank_prefers_higher_score(monkeypatch) -> None:
    monkeypatch.setenv("LBG_TEAM_PLAYBOOK_SCORE_MIN_SAMPLES", "1")

    t_ok = team_store.create_task(
        role="qa",
        objective="high",
        actor_id="test:rank",
        approval_required=False,
        context={"_campus_coffee_fill": True, "utility_key": "qa_godot_owners"},
    )
    team_store.update_task(t_ok.id, status="done", result={"ok": True, "utility_key": "qa_godot_owners"})

    t_bad = team_store.create_task(
        role="ops",
        objective="low",
        actor_id="test:rank",
        approval_required=False,
        context={"_campus_coffee_fill": True, "utility_key": "ops_probe"},
    )
    team_store.update_task(t_bad.id, status="failed", result={"ok": False, "utility_key": "ops_probe"})
    # second fail to pull score down
    t_bad2 = team_store.create_task(
        role="ops",
        objective="low2",
        actor_id="test:rank",
        approval_required=False,
        context={"_campus_coffee_fill": True, "utility_key": "ops_probe"},
    )
    team_store.update_task(t_bad2.id, status="failed", result={"ok": False, "utility_key": "ops_probe"})

    playbooks = [
        {"utility_key": "ops_probe", "role": "ops", "agent_ids": ("studio_ops_hephaistos",), "objective": "ops", "context": {}},
        {"utility_key": "qa_godot_owners", "role": "qa", "agent_ids": ("studio_qa_argus",), "objective": "qa", "context": {}},
    ]
    ranked = playbook_scores.rank_playbooks(playbooks)
    assert ranked[0][0]["utility_key"] == "qa_godot_owners"
    assert float(ranked[0][1]["score"]) >= float(ranked[1][1]["score"])


def test_below_min_not_eligible(monkeypatch) -> None:
    monkeypatch.setenv("LBG_TEAM_PLAYBOOK_SCORE_MIN_SAMPLES", "2")
    monkeypatch.setenv("LBG_TEAM_PLAYBOOK_SCORE_MIN", "0.8")
    for _ in range(3):
        t = team_store.create_task(
            role="pm",
            objective="bad pm",
            actor_id="test:min",
            approval_required=False,
            context={"_campus_coffee_fill": True, "utility_key": "pm_brief"},
        )
        team_store.update_task(t.id, status="failed", result={"ok": False, "utility_key": "pm_brief"})
    info = playbook_scores.score_utility_key("pm_brief", role="pm")
    assert info["eligible"] is False
