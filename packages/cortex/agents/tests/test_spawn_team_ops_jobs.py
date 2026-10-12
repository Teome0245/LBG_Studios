"""Tests spawn playbooks ops équipe (stockage + Ollama + HW)."""

from __future__ import annotations

import json
import time
from unittest.mock import patch

from lbg_agents.spawn_team_ops_ollama_job import run_spawn as run_ollama
from lbg_agents.spawn_team_ops_hw_job import run_spawn as run_hw
from lbg_agents.spawn_team_ops_storage_job import run_spawn as run_storage
from lbg_agents.spawn_team_ops_guest_job import run_spawn as run_guest


def test_storage_skips_ok_by_default(monkeypatch, tmp_path):
    monkeypatch.setenv("LBG_TEAM_OPS_STORAGE_JOB_STATE", str(tmp_path / "state.json"))
    with patch(
        "lbg_agents.spawn_team_ops_storage_job.probe_proxmox_storage_local",
        return_value={"ok": True, "outcome": "ok", "data_percent": 42},
    ):
        out = run_storage()
    assert out["spawned"] is False
    assert out["outcome"] == "ok"


def test_storage_spawns_on_warn(monkeypatch, tmp_path):
    monkeypatch.setenv("LBG_TEAM_OPS_STORAGE_JOB_STATE", str(tmp_path / "state.json"))
    storage = {"ok": True, "outcome": "warn", "data_percent": 88}

    with patch("lbg_agents.spawn_team_ops_storage_job.probe_proxmox_storage_local", return_value=storage):
        with patch(
            "lbg_agents.spawn_team_ops_storage_job.create_and_run_team_task",
            return_value={
                "task_id": "ops-st-1",
                "ran": {"status": "done", "result": {"kind": "ops_storage", "ok": True}},
            },
        ) as mock_create:
            out = run_storage()

    assert out["spawned"] is True
    assert out["task_id"] == "ops-st-1"
    mock_create.assert_called_once()
    call_kw = mock_create.call_args.kwargs
    assert call_kw["role"] == "ops"
    assert call_kw["context"]["ops_kind"] == "proxmox_storage"


def test_guest_skips_ok_by_default(monkeypatch, tmp_path):
    monkeypatch.setenv("LBG_TEAM_OPS_GUEST_JOB_STATE", str(tmp_path / "state.json"))
    wall = {"ok": True, "outcome": "ok", "hosts": [], "stressed": [], "alerts": []}
    with patch("lbg_agents.spawn_team_ops_guest_job.probe_guest_metrics_wall", return_value=wall):
        out = run_guest()
    assert out["spawned"] is False
    assert out["outcome"] == "ok"


def test_guest_spawns_on_warn(monkeypatch, tmp_path):
    monkeypatch.setenv("LBG_TEAM_OPS_GUEST_JOB_STATE", str(tmp_path / "state.json"))
    wall = {
        "ok": True,
        "outcome": "warn",
        "alerts": ["web: disk 81%"],
        "stressed": [
            {
                "ok": True,
                "id": "web",
                "label": "Front web",
                "host": "192.168.0.100",
                "outcome": "warn",
                "disk_percent": 81.0,
                "load1": 3.34,
            }
        ],
        "hosts": [],
    }
    with patch("lbg_agents.spawn_team_ops_guest_job.probe_guest_metrics_wall", return_value=wall):
        with patch(
            "lbg_agents.spawn_team_ops_guest_job.create_and_run_team_task",
            return_value={
                "task_id": "ops-guest-1",
                "ran": {"status": "done", "result": {"kind": "ops_guest_metrics", "ok": True}},
            },
        ) as mock_create:
            out = run_guest()
    assert out["spawned"] is True
    assert out["task_id"] == "ops-guest-1"
    assert out["remediation_plan"]["suggested_actions"]
    call_kw = mock_create.call_args.kwargs
    assert call_kw["role"] == "ops"
    assert call_kw["context"]["ops_kind"] == "guest_metrics"
    assert call_kw["context"]["presence_agent_id"] == "studio_ops_hephaistos"
    assert call_kw["context"]["presence_zone"] == "zone_core"
    assert "Front web" in call_kw["objective"]


def test_guest_respects_cooldown(monkeypatch, tmp_path):
    state_file = tmp_path / "state.json"
    monkeypatch.setenv("LBG_TEAM_OPS_GUEST_JOB_STATE", str(state_file))
    state_file.write_text(
        json.dumps({"last_spawn_ts": time.time(), "last_spawn_outcome": "warn"}) + "\n",
        encoding="utf-8",
    )
    wall = {"ok": True, "outcome": "warn", "stressed": [{"id": "web", "outcome": "warn"}], "alerts": []}
    with patch("lbg_agents.spawn_team_ops_guest_job.probe_guest_metrics_wall", return_value=wall):
        out = run_guest()
    assert out["spawned"] is False


def test_ollama_spawn_respects_cooldown(monkeypatch, tmp_path):
    state_file = tmp_path / "state.json"
    monkeypatch.setenv("LBG_TEAM_OPS_OLLAMA_JOB_STATE", str(state_file))
    state_file.write_text(json.dumps({"last_spawn_ts": time.time()}) + "\n", encoding="utf-8")
    out = run_ollama()
    assert out["spawned"] is False
    assert out["outcome"] == "cooldown"


def test_ollama_spawn_creates_ops_task(monkeypatch, tmp_path):
    monkeypatch.setenv("LBG_TEAM_OPS_OLLAMA_JOB_STATE", str(tmp_path / "state.json"))
    with patch(
        "lbg_agents.spawn_team_ops_ollama_job.create_and_run_team_task",
        return_value={
            "task_id": "ops-ol-1",
            "ran": {"status": "done", "result": {"kind": "ops_ollama", "ok": True}},
        },
    ) as mock_create:
        out = run_ollama()
    assert out["spawned"] is True
    assert out["task_ok"] is True
    assert mock_create.call_args.kwargs["context"]["ops_kind"] == "ollama_audit"



def test_hw_skips_ok_by_default(monkeypatch, tmp_path):
    monkeypatch.setenv("LBG_TEAM_OPS_HW_JOB_STATE", str(tmp_path / "state.json"))
    with patch(
        "lbg_agents.spawn_team_ops_hw_job.probe_proxmox_hw_local",
        return_value={"ok": True, "outcome": "ok", "host": "192.168.0.201"},
    ):
        out = run_hw()
    assert out["spawned"] is False
    assert out["outcome"] == "ok"


def test_hw_spawns_on_degraded(monkeypatch, tmp_path):
    monkeypatch.setenv("LBG_TEAM_OPS_HW_JOB_STATE", str(tmp_path / "state.json"))
    hw = {"ok": True, "outcome": "degraded", "host": "192.168.0.201", "bmc": {"state": "dead"}}

    with patch("lbg_agents.spawn_team_ops_hw_job.probe_proxmox_hw_local", return_value=hw):
        with patch(
            "lbg_agents.spawn_team_ops_hw_job.create_and_run_team_task",
            return_value={
                "task_id": "ops-hw-1",
                "ran": {"status": "done", "result": {"kind": "ops_hw", "ok": True}},
            },
        ) as mock_create:
            out = run_hw()

    assert out["spawned"] is True
    assert out["task_id"] == "ops-hw-1"
    call_kw = mock_create.call_args.kwargs
    assert call_kw["role"] == "ops"
    assert call_kw["context"]["ops_kind"] == "proxmox_hw"
    assert call_kw["context"]["proxmox_hw"]["outcome"] == "degraded"


def test_hw_spawns_on_warn(monkeypatch, tmp_path):
    monkeypatch.setenv("LBG_TEAM_OPS_HW_JOB_STATE", str(tmp_path / "state.json"))
    hw = {"ok": True, "outcome": "warn", "host": "192.168.0.201"}
    with patch("lbg_agents.spawn_team_ops_hw_job.probe_proxmox_hw_local", return_value=hw):
        with patch(
            "lbg_agents.spawn_team_ops_hw_job.create_and_run_team_task",
            return_value={
                "task_id": "ops-hw-2",
                "ran": {"status": "done", "result": {"kind": "ops_hw", "ok": True}},
            },
        ):
            out = run_hw()
    assert out["spawned"] is True
    assert out["outcome"] == "warn"
