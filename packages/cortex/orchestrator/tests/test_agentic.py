"""Tests élévation agentique Chat → job (point 6, inspiré P03)."""

from __future__ import annotations

import pytest

from router.agentic import chat_agentic_enabled, elevate_to_job, should_elevate_to_agentic


def test_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LBG_CHAT_AGENTIC", raising=False)
    monkeypatch.setenv("LBG_JOBS_RUNNER_ENABLED", "1")
    assert chat_agentic_enabled({}) is False
    assert should_elevate_to_agentic("devops_probe", {}) is False


def test_context_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_CHAT_AGENTIC", "1")
    assert chat_agentic_enabled({"prefer_agentic": False}) is False
    assert chat_agentic_enabled({"prefer_agentic": True}) is True


def test_elevation_requires_runner(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_CHAT_AGENTIC", "1")
    monkeypatch.setenv("LBG_JOBS_RUNNER_ENABLED", "0")
    assert should_elevate_to_agentic("devops_probe", {}) is False
    monkeypatch.setenv("LBG_JOBS_RUNNER_ENABLED", "1")
    assert should_elevate_to_agentic("devops_probe", {}) is True


def test_only_actionable_intents(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_CHAT_AGENTIC", "1")
    monkeypatch.setenv("LBG_JOBS_RUNNER_ENABLED", "1")
    assert should_elevate_to_agentic("devops_probe", {}) is True
    assert should_elevate_to_agentic("npc_dialogue", {}) is False
    assert should_elevate_to_agentic("unknown", {}) is False


def test_no_elevation_with_structured_action(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_CHAT_AGENTIC", "1")
    monkeypatch.setenv("LBG_JOBS_RUNNER_ENABLED", "1")
    # Action structurée explicite (console DevOps) : on ne ré-planifie pas depuis le texte.
    assert should_elevate_to_agentic("devops_probe", {"devops_action": {"kind": "ssh_run"}}) is False
    assert should_elevate_to_agentic("devops_probe", {"prefer_agentic": True, "devops_action": {"kind": "selfcheck"}}) is False
    assert should_elevate_to_agentic("desktop_control", {"desktop_action": {"kind": "open_app"}}) is False


def test_intents_allowlist_restricts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_CHAT_AGENTIC", "1")
    monkeypatch.setenv("LBG_JOBS_RUNNER_ENABLED", "1")
    monkeypatch.setenv("LBG_CHAT_AGENTIC_INTENTS", "devops_probe")
    assert should_elevate_to_agentic("devops_probe", {}) is True
    assert should_elevate_to_agentic("project_pm", {}) is False
    assert should_elevate_to_agentic("desktop_control", {}) is False
    monkeypatch.delenv("LBG_CHAT_AGENTIC_INTENTS", raising=False)
    assert should_elevate_to_agentic("project_pm", {}) is True


def test_phase_f1_allowlist_includes_project_pm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_CHAT_AGENTIC", "1")
    monkeypatch.setenv("LBG_JOBS_RUNNER_ENABLED", "1")
    monkeypatch.setenv("LBG_CHAT_AGENTIC_INTENTS", "devops_probe,project_pm")
    assert should_elevate_to_agentic("devops_probe", {}) is True
    assert should_elevate_to_agentic("project_pm", {"prefer_agentic": True, "pm_focus": True}) is True
    # Bool soft-flag OK ; payload dict = console PM → pas d'élévation.
    assert should_elevate_to_agentic("project_pm", {"project_pm": True}) is True
    assert should_elevate_to_agentic(
        "project_pm", {"project_pm": {"include_plan": True}}
    ) is False
    assert should_elevate_to_agentic("desktop_control", {}) is False


def test_phase_f2_allowlist_desktop_control(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_CHAT_AGENTIC", "1")
    monkeypatch.setenv("LBG_JOBS_RUNNER_ENABLED", "1")
    monkeypatch.setenv(
        "LBG_CHAT_AGENTIC_INTENTS", "devops_probe,project_pm,desktop_control"
    )
    assert should_elevate_to_agentic("desktop_control", {"prefer_agentic": True}) is True
    assert should_elevate_to_agentic(
        "desktop_control", {"desktop_action": {"kind": "comfyui_ensure"}}
    ) is False


def test_elevate_to_job_creates_background_job(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_CHAT_AGENTIC", "1")
    monkeypatch.setenv("LBG_JOBS_RUNNER_ENABLED", "1")
    out = elevate_to_job(
        text="sonde devops complète de la stack",
        actor_id="pilot:1",
        intent="devops_probe",
        context={"devops_dry_run": True},
    )
    assert out["agentic"] is True
    assert out["elevated_from"] == "devops_probe"
    assert isinstance(out["job_id"], str) and out["job_id"]
    assert "arrière-plan" in out["reply"]


def test_elevate_project_pm_sets_pm_focus(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_CHAT_AGENTIC", "1")
    monkeypatch.setenv("LBG_JOBS_RUNNER_ENABLED", "1")
    out = elevate_to_job(
        text="point d'avancement et plan de route",
        actor_id="pilot:pm",
        intent="project_pm",
        context={"prefer_agentic": True},
    )
    assert out["agentic"] is True
    assert out["elevated_from"] == "project_pm"
    assert out.get("pilot_jobs_href", "").startswith("#/jobs")
    from services import jobs as svc_jobs

    job = svc_jobs.get_job(out["job_id"])
    assert job is not None
    assert job.base_context.get("pm_focus") is True
    assert job.base_context.get("_agentic_from") == "project_pm"
