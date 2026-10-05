"""Tests spawn veille concurrents (dry / cooldown)."""

from __future__ import annotations

import json
from pathlib import Path

from lbg_agents import spawn_team_concurrents_wave_job as job


def test_wave_a_has_four_roles() -> None:
    roles = [r for r, _, _ in job.WAVE_TASKS["A"]]
    assert roles == ["pm", "player_ia", "dev_godot", "dev_game"]


def test_dry_run_no_network(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LBG_TEAM_CONCURRENTS_DRY_RUN", "1")
    monkeypatch.setenv("LBG_TEAM_CONCURRENTS_WAVE", "A")
    monkeypatch.setenv("LBG_TEAM_CONCURRENTS_WAVE_STATE", str(tmp_path / "st.json"))
    out = job.run_spawn(persist=True)
    assert out["ok"] is True
    assert out["outcome"] == "dry_run"
    assert out["spawned"] is False
    assert len(out["planned"]) == 4


def test_cooldown(tmp_path: Path, monkeypatch) -> None:
    st_path = tmp_path / "st.json"
    st_path.write_text(json.dumps({"last_spawn_ts_A": 9_999_999_999.0}), encoding="utf-8")
    monkeypatch.setenv("LBG_TEAM_CONCURRENTS_DRY_RUN", "0")
    monkeypatch.setenv("LBG_TEAM_CONCURRENTS_WAVE", "A")
    monkeypatch.setenv("LBG_TEAM_CONCURRENTS_WAVE_STATE", str(st_path))
    monkeypatch.setenv("LBG_TEAM_CONCURRENTS_WAVE_COOLDOWN_S", "3600")
    out = job.run_spawn(persist=True)
    assert out["outcome"] == "cooldown"
