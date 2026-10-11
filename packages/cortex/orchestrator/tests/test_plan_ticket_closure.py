"""Tests clôture plan — refuse faux done / skip / dry-run."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ["LBG_TEAM_DB_PATH"] = ":memory:"
os.environ["LBG_TEAM_PLAN_CLOSURE_GATE"] = "1"
os.environ["LBG_TEAM_PLAN_SYNC_OMARCHY"] = "0"

from team.models import TeamTask  # noqa: E402
from team.plan_ticket_closure import (  # noqa: E402
    apply_plan_closure_gate,
    looks_like_skip,
    plan_closure_accepted,
)


def test_looks_like_skip_gate_fermee() -> None:
    assert looks_like_skip(
        {
            "human_summary": "Gate fermée — je ne démarre pas 2.2 et je ne le marque pas done.",
            "ok": True,
        }
    )


def test_apply_rejects_skip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan = {
        "tickets": [
            {"id": "2.2", "status": "blocked", "evidence": ""},
        ]
    }
    path = tmp_path / "plan_evolutions.json"
    path.write_text(json.dumps(plan), encoding="utf-8")
    monkeypatch.setenv("LBG_PLAN_EVOLUTIONS_JSON", str(path))
    monkeypatch.setenv("LBG_TEAM_PLAN_SYNC_OMARCHY", "0")

    task = TeamTask(
        id="t1",
        role="dev_godot",
        objective="Ticket plan 2.2 LIVE",
        actor_id="u",
        context={"plan_ticket": "2.2", "plan_id": "PLAN_PROPOSITIONS_EVOLUTIONS"},
    )
    out = apply_plan_closure_gate(
        task,
        {
            "ok": True,
            "dry_run": False,
            "human_summary": "Gate fermée — je ne démarre pas 2.2.",
        },
    )
    assert out["ok"] is False
    assert out["plan_closure"]["ok"] is False
    assert any("skip" in r for r in out["plan_closure"]["reasons"])


def test_apply_accepts_done_with_evidence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan = {
        "tickets": [
            {
                "id": "2.3",
                "status": "done",
                "evidence": "navmesh hub_nav.gd bake 193 polys smoke OK LIVE 2026-10-11",
            },
        ]
    }
    path = tmp_path / "plan_evolutions.json"
    path.write_text(json.dumps(plan), encoding="utf-8")
    monkeypatch.setenv("LBG_PLAN_EVOLUTIONS_JSON", str(path))
    monkeypatch.setenv("LBG_TEAM_PLAN_SYNC_OMARCHY", "0")

    task = TeamTask(
        id="t2",
        role="dev_godot",
        objective="Ticket plan 2.3",
        actor_id="u",
        context={"plan_ticket": "2.3"},
    )
    out = apply_plan_closure_gate(
        task,
        {
            "ok": True,
            "dry_run": False,
            "human_summary": "Iris — navmesh livré",
        },
    )
    assert out["ok"] is True
    assert out["plan_closure"]["ok"] is True
    assert plan_closure_accepted(out) is True


def test_plan_closure_accepted_rejects_skip() -> None:
    assert (
        plan_closure_accepted(
            {
                "ok": True,
                "human_summary": "Gate fermée — je ne démarre pas",
            }
        )
        is False
    )
