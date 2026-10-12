"""Tests timer inventaire réseau."""

from __future__ import annotations

from unittest.mock import patch

from lbg_agents.spawn_network_inventory_job import run_job


def test_job_skipped_when_disabled(monkeypatch) -> None:
    monkeypatch.setenv("LBG_NETWORK_INVENTORY_JOB_ENABLED", "0")
    out = run_job()
    assert out["ok"] is True
    assert out["outcome"] == "skipped"


def test_job_stable_and_changed(monkeypatch) -> None:
    monkeypatch.setenv("LBG_NETWORK_INVENTORY_JOB_ENABLED", "1")
    monkeypatch.setenv("LBG_NETWORK_INVENTORY_NOTIFY", "0")
    monkeypatch.setenv("LBG_NETWORK_INVENTORY_SPAWN_OPS", "0")

    stable = {
        "ok": True,
        "n_devices": 10,
        "n_present": 8,
        "by_role": {"server": 5, "switch": 1},
        "diff": {"n_appeared": 0, "n_disappeared": 0, "appeared": [], "disappeared": []},
        "reply": "ok",
    }
    with patch("lbg_agents.spawn_network_inventory_job.run_network_inventory", return_value=stable):
        out = run_job(persist=True)
    assert out["outcome"] == "stable"
    assert out["n_present"] == 8

    changed = {
        **stable,
        "diff": {
            "n_appeared": 1,
            "n_disappeared": 1,
            "appeared": [{"host": "192.168.0.88", "label": "phone", "role": "phone"}],
            "disappeared": [{"host": "192.168.0.42", "label": "laptop", "role": "desktop"}],
        },
    }
    with patch("lbg_agents.spawn_network_inventory_job.run_network_inventory", return_value=changed):
        out2 = run_job(persist=True)
    assert out2["outcome"] == "changed"
    assert "+1" in out2["reply"] and "−1" in out2["reply"]
    assert out2["hephaistos_spawn"]["skipped"] is True
