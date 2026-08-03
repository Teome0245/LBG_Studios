"""Tests playbook spawn jalon MMO (A1) — dry, sans orchestrateur."""

from __future__ import annotations

import json
from pathlib import Path

from lbg_agents import spawn_team_mmo_jalon_job as job


def test_jalon_defaults() -> None:
    assert job.jalon_id()
    assert job.owner_smoke_bundle() == "godot_login" or job.owner_smoke_bundle()


def test_run_spawn_skipped_when_disabled(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LBG_TEAM_MMO_JALON_JOB_ENABLED", "0")
    out = job.run_spawn(persist=False)
    assert out.get("outcome") == "skipped"


def test_run_spawn_creates_tasks(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LBG_TEAM_MMO_JALON_JOB_ENABLED", "1")
    monkeypatch.setenv("LBG_TEAM_MMO_JALON_JOB_STATE", str(tmp_path / "state.json"))
    monkeypatch.setenv("LBG_TEAM_MMO_JALON_JOB_COOLDOWN_S", "1")

    calls: list[dict] = []

    def fake_create(**kwargs):
        calls.append(kwargs)
        tid = f"t{len(calls)}"
        return {"task_id": tid, "created": {"id": tid}, "ran": {"status": "done", "result": {"ok": True}}}

    monkeypatch.setattr(job, "create_and_run_team_task", fake_create)
    monkeypatch.setattr(job, "cooldown_active", lambda *_a, **_k: False)

    out = job.run_spawn(persist=True, run_tasks=True)
    assert out.get("ok") is True
    assert out.get("spawned") is True
    assert len(calls) == 2
    assert calls[0]["role"] == "dev_godot"
    assert calls[1]["role"] == "qa"
    assert calls[1]["context"].get("owner_smoke_bundle")
    assert (tmp_path / "state.json").is_file()
    st = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert st.get("last_jalon")
