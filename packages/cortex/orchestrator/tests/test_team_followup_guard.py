"""Tests garde-fous followups (anti-cascade / cooldown)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

os.environ["LBG_TEAM_DB_PATH"] = ":memory:"
os.environ["LBG_TEAM_FOLLOWUP_STATE"] = ":memory:"
os.environ["LBG_TEAM_GODOT_FOLLOWUP_ENABLED"] = "1"
os.environ["LBG_TEAM_M9_FOLLOWUP_ENABLED"] = "1"

from team import followup_guard  # noqa: E402
from team import store as team_store  # noqa: E402
from team.godot_followup import (  # noqa: E402
    auto_run_dev_enabled,
    auto_run_pm_enabled,
    maybe_spawn_after_godot_failure,
)
from team.m9_map_followup import maybe_spawn_after_m9_failure  # noqa: E402
from team.failure_followup import maybe_spawn_after_failure  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_team_db(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    team_store._conn = None  # type: ignore[attr-defined]
    state_file = tmp_path / "followup_state.json"
    monkeypatch.setenv("LBG_TEAM_FOLLOWUP_STATE", str(state_file))
    monkeypatch.setenv("LBG_TEAM_FOLLOWUP_COOLDOWN_S", "3600")
    monkeypatch.setenv("LBG_TEAM_FOLLOWUP_MAX_DEPTH", "2")
    monkeypatch.setenv("LBG_TEAM_GODOT_FOLLOWUP_AUTO_RUN_PM", "1")
    monkeypatch.setenv("LBG_TEAM_GODOT_FOLLOWUP_AUTO_RUN_DEV", "0")


def _godot_fail_result() -> dict[str, object]:
    return {
        "kind": "godot_client_tracks_workflow",
        "ok": False,
        "tracks": [
            {"track": "lbg_ws2_readiness", "ok": False, "gaps": ["module lbg_ws2 manquant"]},
            {"track": "sidecar_m1", "ok": False, "gaps": ["sidecar KO"]},
        ],
    }


def test_godot_followup_spawns_pm_and_dev_on_root_failure() -> None:
    task = team_store.create_task(role="qa", objective="supervise godot", actor_id="system:team")
    team_store.update_task(task.id, status="failed", result=_godot_fail_result())
    refreshed = team_store.get_task(task.id)
    assert refreshed is not None
    ids = maybe_spawn_after_godot_failure(refreshed)
    assert len(ids) >= 2
    roles = {team_store.get_task(i).role for i in ids if team_store.get_task(i)}
    assert "pm" in roles
    assert "dev_game" in roles


def test_godot_followup_suppressed_on_followup_child() -> None:
    parent = team_store.create_task(role="qa", objective="supervise", actor_id="system:team")
    team_store.update_task(parent.id, status="failed", result=_godot_fail_result())
    parent_ref = team_store.get_task(parent.id)
    assert parent_ref is not None
    first_ids = maybe_spawn_after_godot_failure(parent_ref)
    assert len(first_ids) >= 1

    dev_id = next(i for i in first_ids if team_store.get_task(i) and team_store.get_task(i).role == "dev_game")
    team_store.update_task(dev_id, status="failed", result=_godot_fail_result())
    dev_task = team_store.get_task(dev_id)
    assert dev_task is not None
    assert dev_task.context.get("_godot_followup") is True

    second = maybe_spawn_after_godot_failure(dev_task)
    assert second == []
    assert dev_task.context.get("_godot_followup") is True


def test_godot_followup_cooldown_same_signature() -> None:
    r1 = team_store.create_task(role="qa", objective="a", actor_id="system:team")
    team_store.update_task(r1.id, status="failed", result=_godot_fail_result())
    t1 = team_store.get_task(r1.id)
    assert t1 is not None
    ids1 = maybe_spawn_after_godot_failure(t1)
    assert ids1

    r2 = team_store.create_task(role="qa", objective="b", actor_id="system:team")
    team_store.update_task(r2.id, status="failed", result=_godot_fail_result())
    t2 = team_store.get_task(r2.id)
    assert t2 is not None
    ids2 = maybe_spawn_after_godot_failure(t2)
    assert ids2 == []
    again = team_store.get_task(r2.id)
    assert again is not None
    assert again.context.get("_godot_followup_suppressed") == "cooldown"


def test_m9_followup_suppressed_on_iris_child() -> None:
    iris = team_store.create_task(
        role="dev_godot",
        objective="Iris M9 m9a",
        actor_id="system:team_m9_followup",
        context={"_m9_followup": True, "m9_track": "m9a"},
    )
    team_store.update_task(
        iris.id,
        status="failed",
        result={
            "kind": "godot_dev_workflow",
            "ok": False,
            "godot_dev_track": "m9a",
            "probes": [{"ok": False, "gaps": ["export_scrapaltai_for_godot.py manquant"]}],
        },
    )
    refreshed = team_store.get_task(iris.id)
    assert refreshed is not None
    assert maybe_spawn_after_m9_failure(refreshed) == []


def test_failure_followup_skips_godot_child() -> None:
    child = team_store.create_task(
        role="dev_game",
        objective="Godot lacunes",
        actor_id="system:team_godot_followup",
        context={"_godot_followup": True},
    )
    team_store.update_task(child.id, status="failed", result={"kind": "other", "ok": False})
    refreshed = team_store.get_task(child.id)
    assert refreshed is not None
    assert maybe_spawn_after_failure(refreshed) == []


def test_godot_auto_run_pm_only_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_TEAM_GODOT_FOLLOWUP_AUTO_RUN_DEV", "0")
    monkeypatch.setenv("LBG_TEAM_GODOT_FOLLOWUP_AUTO_RUN_PM", "1")
    assert auto_run_pm_enabled() is True
    assert auto_run_dev_enabled() is False
    monkeypatch.setenv("LBG_TEAM_GODOT_FOLLOWUP_AUTO_RUN", "0")
    assert auto_run_pm_enabled() is False


def test_followup_depth_counts_parents() -> None:
    root = team_store.create_task(role="qa", objective="root", actor_id="system:team")
    mid = team_store.create_task(
        role="pm",
        objective="mid",
        actor_id="system:team",
        context={"parent_task_id": root.id},
    )
    leaf = team_store.create_task(
        role="dev_game",
        objective="leaf",
        actor_id="system:team",
        context={"parent_task_id": mid.id},
    )
    leaf_task = team_store.get_task(leaf.id)
    assert leaf_task is not None
    assert followup_guard.followup_depth(leaf_task) == 2


def test_godot_signature_stable() -> None:
    result = _godot_fail_result()
    s1 = followup_guard.godot_signature(result)
    s2 = followup_guard.godot_signature(result)
    assert s1 == s2
    assert "lbg_ws2_readiness" in s1
