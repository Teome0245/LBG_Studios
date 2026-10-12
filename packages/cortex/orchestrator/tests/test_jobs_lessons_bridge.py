"""Pont jobs → lessons Team (phase D)."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("LBG_TEAM_DB_PATH", ":memory:")
os.environ.setdefault("LBG_JOBS_LESSONS_BRIDGE", "1")
os.environ.setdefault("LBG_TEAM_LESSONS_ENABLED", "1")


def test_bridge_job_failure_writes_lesson(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("LBG_TEAM_LESSONS_PATH", str(tmp_path / "lessons.json"))
    monkeypatch.setenv("LBG_JOBS_LESSONS_BRIDGE", "1")
    monkeypatch.setenv("LBG_TEAM_LESSONS_ENABLED", "1")

    from services import jobs as svc_jobs
    from team import lessons_learned

    job = svc_jobs.Job(
        id="job-test-bridge-1",
        actor_id="test",
        objective="sonde devops stack LAN",
        status="failed",
        error_log=[{"capability": "devops_probe", "error": "timeout"}],
        result_summary="Échec selfcheck",
        trace_id="tr-1",
    )
    svc_jobs._bridge_job_to_lessons(job, outcome="failed")
    doc = lessons_learned.load_lessons_doc()
    lessons = doc.get("lessons") or []
    assert any(
        ("job:job-test-bridge-1" in (x.get("refs") or []))
        or ("job failed" in str(x.get("pattern") or ""))
        for x in lessons
    )


def test_bridge_success_skipped_by_default(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("LBG_TEAM_LESSONS_PATH", str(tmp_path / "lessons2.json"))
    monkeypatch.setenv("LBG_JOBS_LESSONS_BRIDGE", "1")
    monkeypatch.setenv("LBG_JOBS_LESSONS_BRIDGE_SUCCESS", "0")
    monkeypatch.setenv("LBG_TEAM_LESSONS_ENABLED", "1")

    from services import jobs as svc_jobs
    from team import lessons_learned

    before = len(lessons_learned.load_lessons_doc().get("lessons") or [])
    job = svc_jobs.Job(
        id="job-ok-1",
        actor_id="test",
        objective="ok run",
        status="done",
        result_summary="ok",
    )
    svc_jobs._bridge_job_to_lessons(job, outcome="done")
    after = len(lessons_learned.load_lessons_doc().get("lessons") or [])
    assert after == before


def test_elevate_reply_has_job_href(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_CHAT_AGENTIC", "1")
    monkeypatch.setenv("LBG_JOBS_RUNNER_ENABLED", "1")
    from router.agentic import elevate_to_job

    out = elevate_to_job(
        text="sonde devops santé LAN",
        actor_id="pilot:1",
        intent="devops_probe",
        context={"devops_dry_run": True},
    )
    assert out.get("agentic") is True
    assert out.get("job_id")
    assert out.get("pilot_jobs_href", "").startswith("#/jobs?job=")
    assert "#/jobs?job=" in (out.get("reply") or "")
