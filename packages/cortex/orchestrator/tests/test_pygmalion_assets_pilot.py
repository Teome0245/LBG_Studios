"""Tests playbook Pygmalion assets (F2)."""

from __future__ import annotations

import pytest


def test_dry_run_proposes_l2(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("LBG_PYGMALION_ASSETS_PILOT_STATE", str(tmp_path / "st.json"))
    monkeypatch.setenv("LBG_COMFYUI_BASE_URL", "http://127.0.0.1:9")

    from team import pygmalion_assets_pilot

    monkeypatch.setattr(
        pygmalion_assets_pilot,
        "probe_comfy",
        lambda **kw: {"ok": True, "base": "http://fake", "status": 200},
    )
    out = pygmalion_assets_pilot.run_pygmalion_assets_pilot(
        brief="Génère un asset sprite via ComfyUI",
        dry_run=True,
        spawn_l2=True,
    )
    assert out.get("ok") is True
    assert out.get("dry_run") is True
    assert out.get("decision") == "spawn_l2"
    assert out.get("comfy_ok") is True
    ensure = next(s for s in out["steps"] if s["id"] == "comfy_ensure")
    assert ensure.get("skipped") is True  # already up
    l2 = next(s for s in out["steps"] if s["id"] == "assets_l2")
    assert l2.get("would_create", {}).get("approval_required") is True
    assert l2["would_create"]["desktop_action"]["kind"] == "comfyui_ensure"


def test_dry_run_would_ensure_when_down(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("LBG_PYGMALION_ASSETS_PILOT_STATE", str(tmp_path / "st-ens.json"))
    from team import pygmalion_assets_pilot

    monkeypatch.setattr(
        pygmalion_assets_pilot,
        "probe_comfy",
        lambda **kw: {"ok": False, "base": "http://fake", "error": "down"},
    )
    out = pygmalion_assets_pilot.run_pygmalion_assets_pilot(
        brief="brief comfy down",
        dry_run=True,
        spawn_l2=True,
        auto_ensure=True,
    )
    ensure = next(s for s in out["steps"] if s["id"] == "comfy_ensure")
    assert ensure.get("would") == "comfyui_ensure"
    assert ensure.get("root") == r"C:\Users\sdesh\ComfyUI"


def test_live_creates_task(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("LBG_PYGMALION_ASSETS_PILOT_STATE", str(tmp_path / "st2.json"))

    from team import pygmalion_assets_pilot

    monkeypatch.setattr(
        pygmalion_assets_pilot,
        "probe_comfy",
        lambda **kw: {"ok": False, "base": "http://fake", "error": "down"},
    )

    class FakeTask:
        id = "task-pyg-1"
        role = "dev_game"
        objective = "obj"
        status = "queued"
        actor_id = "pilot:x"

    class FakeStore:
        @staticmethod
        def team_enabled():
            return True

        @staticmethod
        def list_tasks(limit=200):
            return []

        @staticmethod
        def create_task(**kwargs):
            assert kwargs["approval_required"] is True
            assert kwargs["context"]["pygmalion_assets_pilot"] is True
            assert kwargs["context"]["desktop_action"]["kind"] == "comfyui_ensure"
            return FakeTask()

    monkeypatch.setattr("team.store.team_enabled", FakeStore.team_enabled)
    monkeypatch.setattr("team.store.list_tasks", FakeStore.list_tasks)
    monkeypatch.setattr("team.store.create_task", FakeStore.create_task)
    monkeypatch.setattr(
        "lbg_agents.ops_notify.send_l2_pending",
        lambda task: {"ok": True, "kind": "l2_pending"},
    )
    monkeypatch.setattr(
        "team.lessons_learned.append_lesson",
        lambda **kw: {"id": "les-1"},
    )

    out = pygmalion_assets_pilot.run_pygmalion_assets_pilot(
        brief="brief pygmalion mesh",
        dry_run=False,
        notify=False,
        spawn_l2=True,
    )
    assert out.get("l2_task_id") == "task-pyg-1"
    assert out.get("comfy_ok") is False
    last = pygmalion_assets_pilot.last_run()
    assert last.get("l2_task_id") == "task-pyg-1"


def test_classifier_pygmalion_to_desktop() -> None:
    from introspection.deterministic_classifier import DeterministicIntentClassifier

    c = DeterministicIntentClassifier()
    intent, conf = c.classify("prépare comfyui pour un brief pygmalion sprite")
    assert intent == "desktop_control"
    assert conf >= 0.76


def test_elevate_desktop_defaults_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_CHAT_AGENTIC", "1")
    monkeypatch.setenv("LBG_JOBS_RUNNER_ENABLED", "1")
    monkeypatch.setenv("LBG_CHAT_AGENTIC_INTENTS", "desktop_control")
    from router.agentic import elevate_to_job, should_elevate_to_agentic
    from services import jobs as svc_jobs

    assert should_elevate_to_agentic("desktop_control", {"prefer_agentic": True}) is True
    out = elevate_to_job(
        text="pipeline assets pygmalion",
        actor_id="pilot:pyg",
        intent="desktop_control",
        context={"prefer_agentic": True, "_pygmalion_brief": True},
    )
    assert out["agentic"] is True
    job = svc_jobs.get_job(out["job_id"])
    assert job is not None
    assert job.base_context.get("desktop_dry_run") is True
    assert job.base_context.get("infographiste_ia") is True
