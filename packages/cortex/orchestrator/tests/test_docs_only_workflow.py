"""Tests workflow docs_only + plan concurrents + coffee bloqué pendant mission."""

from __future__ import annotations

import os

import pytest

os.environ["LBG_TEAM_DB_PATH"] = ":memory:"

from team import roles as team_roles  # noqa: E402
from team.docs_write_workflow import execute_docs_only_workflow, resolve_docs_only  # noqa: E402
from team.models import TeamTask  # noqa: E402
from team.player_ia_exec import execute_player_ia  # noqa: E402


def test_resolve_docs_only_from_context() -> None:
    task = TeamTask(
        id="t1",
        role="player_ia",
        objective="sonde",
        actor_id="u",
        context={"docs_only": True, "concurrents_ticket": "C9_C2"},
    )
    assert resolve_docs_only(task) is True


def test_player_ia_docs_only_skips_core3_probe(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Chœur docs_only → écrit/vérifie markdown, pas de sonde sidecar."""
    monkeypatch.setenv("LBG_TEAM_DOCS_WRITE_ENABLED", "1")

    called = {"probe": False}

    def _boom(_task=None):
        called["probe"] = True
        raise AssertionError("probe_player_ia ne doit pas être appelé en docs_only")

    monkeypatch.setattr("team.player_ia_exec.probe_player_ia", _boom)

    task = TeamTask(
        id="t-docs",
        role="player_ia",
        objective="Chœur — brouillon AGENT_SKILL_MMO.md + schéma C2",
        actor_id="u:test",
        context={"docs_only": True, "concurrents_ticket": "C9_C2", "write_files": True},
    )
    out = execute_player_ia(task)
    assert called["probe"] is False
    assert out.get("kind") == "docs_only_write"
    assert out.get("ok") is True
    assert out.get("docs_only") is True
    assert len(out.get("deliverables") or []) >= 1


def test_docs_only_verifies_existing_agent_skill() -> None:
    task = TeamTask(
        id="t2",
        role="player_ia",
        objective="C9",
        actor_id="u",
        context={"docs_only": True, "concurrents_ticket": "C9", "write_files": False},
    )
    out = execute_docs_only_workflow(task)
    assert out["ok"] is True
    assert any("AGENT_SKILL_MMO.md" in p for p in (out.get("deliverables") or []))


def test_plan_concurrents_vague_a_focused() -> None:
    props = team_roles.plan_from_objective(
        "Mission veille concurrents Vague A — docs only, max 4 tâches L1",
        actor_id="u:plan",
    )
    roles = [p["role"] for p in props]
    assert roles == ["pm", "player_ia", "dev_godot", "dev_game"]
    assert all((p.get("context") or {}).get("docs_only") for p in props)
    assert "ops" not in roles
    assert "qa" not in roles
    assert "admin_infra" not in roles


def test_plan_fallback_pm_only_not_qa() -> None:
    props = team_roles.plan_from_objective("objectif totalement obscur xyzzy", actor_id="u")
    assert len(props) == 1
    assert props[0]["role"] == "pm"


def test_plan_cap_max_tasks() -> None:
    """Objectif large (plan+qa+ops keywords) plafonné à max_tasks."""
    props = team_roles.plan_from_objective(
        "plan projet + smoke qa + sonde ops infra + jalon — max_tasks=2",
        actor_id="u",
    )
    assert len(props) <= 2
