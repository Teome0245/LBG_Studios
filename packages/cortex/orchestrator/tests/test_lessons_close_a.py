"""Tests Agency Phase A — hard-fail, dédup, lessons_trace, anti-double post_judge."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("LBG_TEAM_DB_PATH", ":memory:")
os.environ.setdefault("LBG_TEAM_LESSONS_ENABLED", "1")
os.environ.setdefault("LBG_TEAM_LESSONS_HARD_FAIL", "1")

from team import lessons_learned  # noqa: E402
from team import post_judge  # noqa: E402
from team import roles as team_roles  # noqa: E402
from team import store as team_store  # noqa: E402
from team.models import TeamTask  # noqa: E402


@pytest.fixture(autouse=True)
def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LBG_TEAM_DB_PATH", ":memory:")
    monkeypatch.setenv("LBG_TEAM_LESSONS_ENABLED", "1")
    monkeypatch.setenv("LBG_TEAM_LESSONS_HARD_FAIL", "1")
    monkeypatch.setenv("LBG_TEAM_LESSONS_DEDUP_HOURS", "48")
    monkeypatch.setenv("LBG_TEAM_POST_JUDGE", "1")
    monkeypatch.setenv("LBG_TEAM_POST_JUDGE_SAMPLE", "1.0")
    monkeypatch.setenv("LBG_TEAM_POST_JUDGE_ROLES", "qa,pm,ops,dev_godot,dev_game,player_ia")
    lessons_file = tmp_path / "lessons_learned.json"
    lessons_file.write_text(
        json.dumps({"schema_version": 1, "lessons": []}, ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setenv("LBG_TEAM_LESSONS_PATH", str(lessons_file))
    team_store.reset_for_tests()
    post_judge._LAST_POST_JUDGE.clear()  # noqa: SLF001


def test_hard_fail_appends_lesson() -> None:
    before = lessons_learned.lessons_count()
    entry = lessons_learned.record_hard_fail_lesson(
        task_id="t-fail-1",
        role="qa",
        objective="smoke LAN rouge",
        result={"ok": False, "kind": "qa_smoke", "error": "smoke red"},
    )
    assert entry is not None
    assert entry.get("deduped") is False
    assert lessons_learned.lessons_count() == before + 1
    assert entry["context"] == "hard_fail"
    assert "Hard-fail" in entry["pattern"]


def test_dedup_bumps_hit_count_no_clone() -> None:
    a = lessons_learned.append_lesson(
        agent_role="ops",
        pattern="Hard-fail ops: storage — boom",
        context="hard_fail",
        do_not_repeat="Échec silencieux sans leçon (ops)",
        refs=["t1"],
    )
    assert a.get("deduped") is False
    count1 = lessons_learned.lessons_count()
    b = lessons_learned.append_lesson(
        agent_role="ops",
        pattern="Hard-fail ops: storage — boom",
        context="hard_fail",
        do_not_repeat="Échec silencieux sans leçon (ops)",
        refs=["t2"],
    )
    assert b.get("deduped") is True
    assert b.get("hit_count") == 2
    assert lessons_learned.lessons_count() == count1
    assert "t2" in (b.get("refs") or [])


def test_post_judge_skips_soft_lesson_when_hard_fail_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = TeamTask(
        id="t-pj-1",
        role="ops",
        objective="healthz probe smoke",
        status="running",
        actor_id="test",
        context={},
    )
    result = {
        "ok": False,
        "kind": "ops_storage",
        "error": "down",
        "hard_fail_lesson": {"id": "lesson_x", "deduped": False},
    }

    def _fail_judge(**kwargs: object) -> dict:
        return {
            "ok": True,
            "pass": False,
            "score": 0.4,
            "mode": "heuristic",
            "reasons": ["faible"],
        }

    monkeypatch.setattr(
        "team.outcome_judge.judge_outcome",
        _fail_judge,
    )
    before = lessons_learned.lessons_count()
    judged = post_judge.maybe_judge_task_outcome(task, result)
    assert judged is not None
    assert judged.get("pass") is False
    assert post_judge.last_post_judge_trace().get("soft_lesson_skipped") is True
    assert lessons_learned.lessons_count() == before


def test_run_task_lessons_trace_and_hard_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    # Seed une leçon pour injection
    lessons_learned.append_lesson(
        agent_role="ops",
        pattern="Ne pas ignorer healthz rouge sur storage",
        context="seed",
        failure_or_success="failure",
        do_not_repeat="ignore healthz",
        refs=["seed"],
    )

    def _fail_ops(task: TeamTask) -> dict:
        return {"ok": False, "kind": "ops_storage", "error": "disk full", "human_summary": "fail"}

    monkeypatch.setitem(team_roles._EXECUTORS, "ops", _fail_ops)  # noqa: SLF001
    # Évite follow-ups bruyants
    monkeypatch.setattr(team_roles, "maybe_spawn_after_failure", lambda *_a, **_k: [])

    task = team_store.create_task(
        role="ops",
        objective="healthz probe smoke storage",
        actor_id="test:agency-a",
        context={"ops_kind": "proxmox_storage"},
    )
    before = lessons_learned.lessons_count()
    ran = team_roles.run_task(task.id)
    assert ran is not None
    assert ran.status == "failed"
    trace = ran.result.get("lessons_trace")
    assert isinstance(trace, dict)
    assert trace.get("injected_count", 0) >= 1
    assert trace.get("injected_ids")
    hf = ran.result.get("hard_fail_lesson")
    assert isinstance(hf, dict)
    assert hf.get("id")
    assert lessons_learned.lessons_count() >= before + 1


def test_meta_status_agency_fields() -> None:
    st = lessons_learned.meta_status()
    assert st["enabled"] is True
    assert st["hard_fail"] is True
    assert st["dedup_hours"] == 48
    assert "last_lesson_id" in st


def test_default_post_judge_roles_include_ops_player_ia(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LBG_TEAM_POST_JUDGE_ROLES", raising=False)
    roles = post_judge.post_judge_roles()
    assert "ops" in roles
    assert "player_ia" in roles
    assert "qa" in roles
