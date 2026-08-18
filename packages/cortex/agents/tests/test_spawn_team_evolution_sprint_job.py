"""Tests spawn playbook sprint évolution 7j."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from lbg_agents import spawn_team_evolution_sprint_job as job


def test_run_spawn_skipped_when_disabled(monkeypatch) -> None:
    monkeypatch.setenv("LBG_TEAM_EVOLUTION_JOB_ENABLED", "0")
    out = job.run_spawn(persist=False)
    assert out.get("outcome") == "skipped"


def test_run_spawn_creates_pm_task(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LBG_TEAM_EVOLUTION_JOB_ENABLED", "1")
    monkeypatch.setenv("LBG_TEAM_EVOLUTION_JOB_STATE", str(tmp_path / "state.json"))
    monkeypatch.setenv("LBG_TEAM_EVOLUTION_JOB_COOLDOWN_S", "1")

    def fake_create(**kwargs):
        assert kwargs["role"] == "pm"
        assert kwargs["context"]["evolution_sprint"] is True
        return {
            "task_id": "t-evo",
            "created": {},
            "ran": {"status": "done", "result": {"kind": "evolution_sprint_workflow", "ok": True}},
        }

    with patch("lbg_agents.spawn_team_evolution_sprint_job.create_and_run_team_task", fake_create):
        result = job.run_spawn(persist=True)
    assert result["spawned"] is True
    assert result["outcome"] in ("done", "ran")
