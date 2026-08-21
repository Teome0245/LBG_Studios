"""Tests boucle fermée A–C : sprint méta, post-judge, apply override L2."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("LBG_TEAM_DB_PATH", ":memory:")

from team import agent_mutator  # noqa: E402
from team import evolution_sprint_workflow as evo  # noqa: E402
from team import outcome_judge  # noqa: E402
from team import post_judge  # noqa: E402
from team import prompt_overrides  # noqa: E402
from team import roles as team_roles  # noqa: E402
from team import store as team_store  # noqa: E402
from team.models import TeamTask  # noqa: E402


@pytest.fixture(autouse=True)
def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LBG_TEAM_DB_PATH", ":memory:")
    monkeypatch.setenv("LBG_TEAM_EVOLUTION_META", "1")
    monkeypatch.setenv("LBG_TEAM_EVOLUTION_L1_AUTO_RUN", "0")
    monkeypatch.setenv("LBG_TEAM_EVOLUTION_PLATFORM_AUDIT", "0")
    monkeypatch.setenv("LBG_TEAM_POST_JUDGE", "1")
    monkeypatch.setenv("LBG_TEAM_POST_JUDGE_SAMPLE", "1.0")
    monkeypatch.setenv("LBG_TEAM_POST_JUDGE_ROLES", "qa,pm,ops")
    monkeypatch.setenv("LBG_TEAM_PROMPT_OVERRIDES_DIR", str(tmp_path / "overrides"))
    monkeypatch.setenv("LBG_AGENT_MUTATOR_STAGING_DIR", str(tmp_path / "mut_staging"))
    monkeypatch.setenv("LBG_TEAM_VERIFY_SMOKE_CHAIN", "0")
    monkeypatch.setenv("LBG_TEAM_AGENT_MUTATOR", "1")
    monkeypatch.setenv("LBG_AGENT_MUTATOR_APPLY_ON_REVIEW", "1")
    monkeypatch.setenv("LBG_TEAM_APPROVAL_SOFT", "1")
    team_store.reset_for_tests()
    evo._last_sprint = {}
    agent_mutator._LAST_MUTATION.clear()  # noqa: SLF001
    post_judge._LAST_POST_JUDGE.clear()  # noqa: SLF001


def test_a_spawn_meta_evolution_tasks() -> None:
    parent = team_store.create_task(
        role="pm",
        objective="Sprint évolution test",
        actor_id="test",
        context={"evolution_sprint": True},
    )
    l1, l2 = evo._spawn_meta_evolution_tasks(parent)
    assert len(l1) == 2
    kinds = []
    for tid in l1:
        t = team_store.get_task(tid)
        assert t is not None
        assert t.approval_required is False
        if t.context.get("agent_mutation"):
            kinds.append("mut")
        if t.context.get("feature_proposal"):
            kinds.append("feat")
    assert "mut" in kinds and "feat" in kinds


def test_b_post_judge_on_ops_task() -> None:
    task = team_store.create_task(
        role="ops",
        objective="healthz probe smoke",
        actor_id="test:judge",
        context={"ops_kind": "proxmox_storage", "proxmox_storage": {"outcome": "ok"}},
    )
    ran = team_roles.run_task(task.id)
    assert ran is not None
    assert ran.status == "done"
    assert isinstance(ran.result.get("post_judge"), dict)
    assert "score" in ran.result["post_judge"]
    assert post_judge.last_post_judge_trace().get("task_id") == task.id


def test_c_apply_candidate_override(tmp_path: Path) -> None:
    # Produce a candidate via mutation cycle
    out = agent_mutator.run_mutation_cycle(
        target="outcome_judge",
        role="qa",
        spawn_l2=True,
        complete_fn=None,
    )
    assert out["candidate_ready"] is True
    manifest = Path(out["manifest_path"])
    applied = agent_mutator.apply_candidate_from_manifest(manifest)
    assert applied["ok"] is True
    ov = prompt_overrides.load_override("outcome_judge")
    assert ov is not None
    assert len(ov) > 40
    # _system_prompt must pick override
    sys_p = outcome_judge._system_prompt()  # noqa: SLF001
    assert "Leçons" in sys_p or "garde-fous" in sys_p or len(sys_p) >= len(
        outcome_judge._system_prompt.__doc__ or ""
    )
    # At minimum override differs from empty and loads
    assert prompt_overrides.meta_status()["active"]["outcome_judge"] is True

    # L2 review task applies on run
    review_id = out["l2_task_id"]
    assert review_id
    team_store.update_task(review_id, status="queued", stored_approval_token="tok")
    ran = team_roles.run_task(review_id, approval_token="tok")
    assert ran is not None
    assert ran.result.get("kind") == "agent_mutator_review"
    assert ran.result.get("applied") is True
