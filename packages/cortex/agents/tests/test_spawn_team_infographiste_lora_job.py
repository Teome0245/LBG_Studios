"""Tests spawn playbook LoRA Pygmalion."""

from __future__ import annotations

import json
import time
from unittest.mock import patch

from lbg_agents.spawn_team_infographiste_lora_job import lora_context, run_spawn


def test_lora_context_flags() -> None:
    ctx = lora_context()
    assert ctx["lora_pipeline"] is True
    assert ctx["infographiste_ia"] is True


def test_spawn_creates_lora_pipeline_task(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("LBG_TEAM_INFOGRAPHISTE_LORA_JOB_STATE", str(tmp_path / "state.json"))
    monkeypatch.setenv("LBG_ORCHESTRATOR_URL", "http://127.0.0.1:8010")

    def fake_create(**kwargs):
        assert kwargs["role"] == "dev_game"
        assert kwargs["context"]["lora_pipeline"] is True
        return {
            "task_id": "l1",
            "created": {"id": "l1"},
            "ran": {
                "id": "l1",
                "status": "done",
                "result": {"kind": "infographiste_lora_workflow", "ok": True},
            },
        }

    with patch("lbg_agents.spawn_team_infographiste_lora_job.create_and_run_team_task", fake_create):
        out = run_spawn()
    assert out["spawned"] is True
    assert out["task_ok"] is True


def test_spawn_respects_cooldown(monkeypatch, tmp_path) -> None:
    state_file = tmp_path / "state.json"
    monkeypatch.setenv("LBG_TEAM_INFOGRAPHISTE_LORA_JOB_STATE", str(state_file))
    state_file.write_text(json.dumps({"last_spawn_ts": time.time()}) + "\n", encoding="utf-8")
    out = run_spawn()
    assert out["outcome"] == "cooldown"
