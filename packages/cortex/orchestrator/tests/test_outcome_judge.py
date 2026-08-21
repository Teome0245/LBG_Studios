"""Tests P0 — golden dataset, outcome_judge, lessons_learned."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("LBG_TEAM_DB_PATH", ":memory:")
os.environ.setdefault("LBG_TEAM_OUTCOME_JUDGE", "1")
os.environ.setdefault("LBG_TEAM_LESSONS_ENABLED", "1")

from team import lessons_learned  # noqa: E402
from team import outcome_judge  # noqa: E402
from team import roles as team_roles  # noqa: E402
from team import store as team_store  # noqa: E402


@pytest.fixture(autouse=True)
def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LBG_TEAM_DB_PATH", ":memory:")
    monkeypatch.setenv("LBG_TEAM_OUTCOME_JUDGE", "1")
    monkeypatch.setenv("LBG_TEAM_LESSONS_ENABLED", "1")
    lessons_file = tmp_path / "lessons_learned.json"
    lessons_file.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "lessons": [
                    {
                        "id": "lesson_test_smoke",
                        "date": "2026-08-21",
                        "agent_role": "qa",
                        "context": "smoke rouge",
                        "failure_or_success": "failure",
                        "pattern": "Ne pas clôturer succès si smoke rouge",
                        "do_not_repeat": "close on red",
                        "refs": ["A2"],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("LBG_TEAM_LESSONS_PATH", str(lessons_file))
    team_store.reset_for_tests()


def test_golden_dataset_loads_cases() -> None:
    cases = outcome_judge.list_golden_cases()
    assert len(cases) >= 5
    ids = {str(c.get("id")) for c in cases}
    assert "godot_signal_connect" in ids
    assert "lore_bible_guard" in ids
    case = outcome_judge.get_golden_case("ops_healthz")
    assert case is not None
    assert "healthz" in " ".join(str(k) for k in case.get("expected_keywords") or []).lower()


def test_judge_heuristic_pass_without_llm() -> None:
    out = outcome_judge.judge_golden_case(
        case_id="ops_healthz",
        artifact_text="Le backend répond sur GET /healthz.",
        complete_fn=lambda **kwargs: {"ok": False, "error": "skip", "skipped": True},
    )
    assert out["ok"] is True
    assert out["pass"] is True
    assert out["score"] >= 0.55
    assert out["mode"] == "heuristic"
    assert outcome_judge.last_judge_trace().get("task_id") == "golden:ops_healthz"


def test_judge_llm_mock_blend() -> None:
    def fake_complete(*, system: str, user: str, **kwargs: object) -> dict:
        return {
            "ok": True,
            "text": json.dumps(
                {
                    "score": 0.9,
                    "pass": True,
                    "reasons": ["réponse claire"],
                    "suggested_followups": [],
                    "dimensions": {
                        "exactitude": 0.9,
                        "concision": 0.8,
                        "respect_regles": 1.0,
                        "cout": 1.0,
                    },
                }
            ),
            "model": "mock",
            "tier": "local",
        }

    out = outcome_judge.judge_outcome(
        task_id="t1",
        artifacts=["Oui, write hors allowlist Iris exige un token L2 Pilot."],
        expected_keywords=["oui", "L2", "token"],
        complete_fn=fake_complete,
    )
    assert out["ok"] is True
    assert out["pass"] is True
    assert out["score"] >= 0.7
    assert "llm" in str(out.get("mode"))


def test_lessons_slice_and_append(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    slice_ = lessons_learned.lessons_slice_for_task(role="qa", objective="smoke LAN rouge mission")
    assert slice_
    assert any("smoke" in x["pattern"].lower() or "clôtur" in x["pattern"].lower() for x in slice_)

    entry = lessons_learned.append_lesson(
        agent_role="pm",
        pattern="Toujours greffer Judge sur Team, pas un second OS.",
        context="architecture",
        failure_or_success="success",
        do_not_repeat="CrewAI on critical path",
        refs=["lbg_agentic_os.md"],
    )
    assert entry["id"]
    assert lessons_learned.lessons_count() >= 2


def test_run_task_injects_lessons_slice() -> None:
    ops = team_store.create_task(
        role="ops",
        objective="healthz probe smoke",
        actor_id="test:lessons",
        context={"ops_kind": "proxmox_storage", "proxmox_storage": {"outcome": "ok"}},
    )
    ran = team_roles.run_task(ops.id)
    assert ran is not None
    assert ran.status == "done"
    assert isinstance(ran.context.get("lessons_slice"), list)
    assert ran.context["lessons_slice"]

