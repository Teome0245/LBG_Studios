"""Tests sprint évolution 7j — Thémis audit full + L1 auto / L2 Pilot."""

from __future__ import annotations

import os
from typing import Any

import pytest

os.environ["LBG_TEAM_DB_PATH"] = ":memory:"
os.environ.setdefault("LBG_DEVOPS_HTTP_ALLOWLIST", "http://127.0.0.1:8010/healthz")

from team import roles as team_roles  # noqa: E402
from team import store as team_store  # noqa: E402
from team import evolution_sprint_workflow as evo_mod  # noqa: E402
from team.evolution_sprint_workflow import (  # noqa: E402
    execute_evolution_sprint_workflow,
    resolve_evolution_sprint_workflow,
)
from team.models import TeamTask  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_team_db(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    team_store._conn = None  # type: ignore[attr-defined]
    team_roles.set_dispatch_for_tests(None)
    monkeypatch.setenv("LBG_TEAM_EVOLUTION_SPRINT_PATH", str(tmp_path / "last_sprint.json"))
    monkeypatch.setenv("LBG_TEAM_EVOLUTION_L1_AUTO_RUN", "0")
    monkeypatch.setenv("LBG_TEAM_EVOLUTION_PLATFORM_AUDIT", "0")
    monkeypatch.delenv("LBG_REASON_LOCAL_MODEL", raising=False)
    evo_mod._last_sprint = {}


def _patch_health_probes(monkeypatch: pytest.MonkeyPatch) -> None:
    healthy = lambda track: (lambda: {"track": track, "ok": True, "gaps": []})
    monkeypatch.setattr("team.autoconsult_workflow._qa_probe", healthy("qa_health"))
    monkeypatch.setattr("team.autoconsult_workflow._ops_probe", healthy("ops_lan"))
    monkeypatch.setattr("team.autoconsult_workflow._iris_probe", healthy("iris_m9"))
    monkeypatch.setattr("team.autoconsult_workflow._hermes_probe", healthy("hermes_soe"))
    monkeypatch.setattr("team.autoconsult_workflow._pygmalion_probe", healthy("infographiste"))
    monkeypatch.setattr("team.autoconsult_workflow._dedale_probe", healthy("dedale_gameplay"))
    monkeypatch.setattr("team.autoconsult_workflow._launchpad_probe", healthy("hermes_launchpad"))
    monkeypatch.setattr("team.autoconsult_workflow._choeur_probe", healthy("choeur_player_ia"))
    monkeypatch.setattr("team.autoconsult_workflow._prime_ui_probe", healthy("vulcan_prime_ui"))


def test_resolve_evolution_from_context() -> None:
    task = TeamTask(id="t1", role="pm", objective="brief", context={"evolution_sprint": True})
    assert resolve_evolution_sprint_workflow(task) is True


def test_team_plan_includes_evolution_sprint() -> None:
    proposals = team_roles.plan_from_objective(
        "lancer un sprint évolution et amélioration continue",
        actor_id="u:plan",
    )
    pm = [p for p in proposals if p["role"] == "pm"]
    assert pm
    assert (pm[0].get("context") or {}).get("evolution_sprint") is True


def test_evolution_sprint_collects_probes(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_health_probes(monkeypatch)
    monkeypatch.setattr("team.bus_hooks.bus_hooks_enabled", lambda: True)

    def fake_dispatch(agent: str, **kwargs: Any) -> dict[str, object]:
        return {"agent": agent, "text": "brief ok"}

    stored = team_store.create_task(
        role="pm",
        objective="Sprint évolution 7j",
        actor_id="u:evo",
        context={"evolution_sprint": True},
    )
    out = execute_evolution_sprint_workflow(stored, fake_dispatch)
    assert out["kind"] == "evolution_sprint_workflow"
    assert out["ok"] is True
    assert len(out["probes"]) == 15
    assert out.get("l1_auto_rate") == 1.0
    assert out["gaps_count"] == 0
    # Méta mutator + feature proposer (L1) même sans gaps
    assert len(out.get("meta_task_ids") or []) == 2
    assert len(out["l1_task_ids"]) == 2
    from team.evolution_sprint_workflow import last_sprint

    persisted = last_sprint()
    assert persisted.get("task_id") == stored.id
    assert len(persisted.get("meta_task_ids") or []) == 2


def test_evolution_l1_spawns_on_gap_and_l2_on_forbidden_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_health_probes(monkeypatch)
    monkeypatch.setattr(
        "team.autoconsult_workflow._ops_probe",
        lambda: {"track": "ops_lan", "ok": False, "gaps": ["orchestrator healthz KO"]},
    )
    monkeypatch.setenv("LBG_REASON_LOCAL_MODEL", "gemma3:4b")
    monkeypatch.setattr("team.bus_hooks.bus_hooks_enabled", lambda: True)

    def fake_dispatch(agent: str, **kwargs: Any) -> dict[str, object]:
        return {"agent": agent, "text": "brief ok"}

    stored = team_store.create_task(
        role="pm",
        objective="Sprint évolution",
        actor_id="u:evo2",
        context={"evolution_sprint": True},
    )
    out = execute_evolution_sprint_workflow(stored, fake_dispatch)
    assert out["gaps_count"] >= 1
    assert out["l1_task_ids"]
    l1 = team_store.get_task(out["l1_task_ids"][0])
    assert l1 is not None
    assert l1.approval_required is False
    assert l1.status == "queued"
    assert out["l2_task_ids"]
    l2 = team_store.get_task(out["l2_task_ids"][0])
    assert l2 is not None
    assert l2.approval_required is True
    assert l2.status == "review"


def test_pm_role_routes_to_evolution(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict[str, object] = {}

    def fake_evo(task: TeamTask, dispatch: Any) -> dict[str, object]:
        called["task_id"] = task.id
        return {"kind": "evolution_sprint_workflow", "ok": True, "probes": []}

    monkeypatch.setattr("team.roles.execute_evolution_sprint_workflow", fake_evo)
    monkeypatch.setattr("team.roles.resolve_evolution_sprint_workflow", lambda t: True)

    task = team_store.create_task(
        role="pm",
        objective="Sprint évolution 7j",
        actor_id="u:test",
        context={"evolution_sprint": True},
    )
    result = team_roles.run_task(task.id)
    assert result is not None
    assert result.status == "done"
    assert called.get("task_id") == task.id
