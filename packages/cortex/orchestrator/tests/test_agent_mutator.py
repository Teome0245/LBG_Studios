"""Tests P1 — agent_mutator (forge V1→V2)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("LBG_TEAM_DB_PATH", ":memory:")
os.environ.setdefault("LBG_TEAM_AGENT_MUTATOR", "1")
os.environ.setdefault("LBG_TEAM_OUTCOME_JUDGE", "1")
os.environ.setdefault("LBG_TEAM_LESSONS_ENABLED", "1")

from team import agent_mutator  # noqa: E402
from team import roles as team_roles  # noqa: E402
from team import store as team_store  # noqa: E402


@pytest.fixture(autouse=True)
def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LBG_TEAM_DB_PATH", ":memory:")
    monkeypatch.setenv("LBG_TEAM_AGENT_MUTATOR", "1")
    monkeypatch.setenv("LBG_TEAM_OUTCOME_JUDGE", "1")
    monkeypatch.setenv("LBG_TEAM_LESSONS_ENABLED", "1")
    monkeypatch.setenv("LBG_AGENT_MUTATOR_STAGING_DIR", str(tmp_path / "mut_staging"))
    monkeypatch.setenv("LBG_AGENT_MUTATOR_SCORE_DELTA", "0.05")
    lessons = tmp_path / "lessons.json"
    lessons.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "lessons": [
                    {
                        "id": "l1",
                        "agent_role": "qa",
                        "pattern": "smoke rouge ne pas clôturer",
                        "do_not_repeat": "close on red smoke",
                        "failure_or_success": "failure",
                        "context": "qa",
                        "refs": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("LBG_TEAM_LESSONS_PATH", str(lessons))
    team_store.reset_for_tests()
    agent_mutator._LAST_MUTATION.clear()  # noqa: SLF001


def test_simulate_and_evaluate_lessons_beat_baseline() -> None:
    baseline = agent_mutator.load_baseline_prompt(target="outcome_judge")
    variants = agent_mutator.generate_variants(baseline, role="qa", n=3, complete_fn=None)
    assert len(variants) >= 2
    assert any(v["id"] == "v1_lessons" for v in variants)

    base_ev = agent_mutator.evaluate_prompt(baseline, role="")
    lessons_prompt = next(v["prompt"] for v in variants if v["id"] == "v1_lessons")
    les_ev = agent_mutator.evaluate_prompt(lessons_prompt, role="")
    assert les_ev["mean_score"] > base_ev["mean_score"]


def test_run_mutation_cycle_writes_staging_and_spawns_l2(tmp_path: Path) -> None:
    out = agent_mutator.run_mutation_cycle(
        target="outcome_judge",
        role="qa",
        spawn_l2=True,
        complete_fn=None,
        n_variants=3,
    )
    assert out["ok"] is True
    assert out["candidate_ready"] is True
    assert out["winner"] is not None
    assert float(out["winner"]["score_delta"]) > 0
    manifest = Path(out["manifest_path"])
    assert manifest.is_file()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["candidate_ready"] is True
    assert (manifest.parent / "candidate" / "prompt_v2_candidate.txt").is_file()
    assert (manifest.parent / "candidate" / "declaration_overlay.json").is_file()
    # A4 : pas d'écriture sous agents/declarations
    decls = Path(__file__).resolve().parents[2] / "agents" / "declarations"
    # staging only
    assert "staging" in str(manifest)
    assert out["l2_task_id"]
    task = team_store.get_task(out["l2_task_id"])
    assert task is not None
    assert task.approval_required is True
    assert task.status == "review"
    assert task.context.get("agent_mutation_review") is True
    assert task.context.get("workflow") == "agent_mutator_review"
    assert agent_mutator.last_mutation_trace().get("run_id") == out["run_id"]
    assert decls.is_dir()  # sanity — inchangé par le cycle


def test_pick_best_respects_threshold() -> None:
    winner = agent_mutator.pick_best(
        baseline_score=0.5,
        variant_results=[
            {"id": "a", "mean_score": 0.52},
            {"id": "b", "mean_score": 0.54},
        ],
        threshold=0.05,
    )
    assert winner is None
    winner2 = agent_mutator.pick_best(
        baseline_score=0.5,
        variant_results=[{"id": "c", "mean_score": 0.58, "prompt": "x"}],
        threshold=0.05,
    )
    assert winner2 is not None
    assert winner2["id"] == "c"


def test_execute_via_run_task() -> None:
    task = team_store.create_task(
        role="qa",
        objective="Forge mutation prompt outcome_judge",
        actor_id="test:mutator",
        context={
            "agent_mutation": True,
            "workflow": "agent_mutator",
            "mutation_target": "outcome_judge",
            "spawn_l2": False,
        },
    )
    ran = team_roles.run_task(task.id)
    assert ran is not None
    assert ran.status == "done"
    assert ran.result.get("kind") == "agent_mutator"
    assert ran.result.get("ok") is True
