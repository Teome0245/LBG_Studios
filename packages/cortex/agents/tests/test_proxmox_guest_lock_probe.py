"""Tests sonde locks Proxmox / snapshots vzdump orphelins."""

from __future__ import annotations

from unittest.mock import patch

from lbg_agents.proxmox_guest_lock_probe import probe_proxmox_guest_lock_host, run_proxmox_guest_lock_probe


def test_critical_on_snapshot_delete_lock():
    stdout = "\n".join(
        [
            "root_pct=70",
            "locked kind=lxc vmid=111 lock=snapshot-delete name=ollama-light",
            "orphan_snap lv=snap_vm-111-disk-0_vzdump origin=vm-111-disk-0",
        ]
    )
    with patch(
        "lbg_agents.proxmox_guest_lock_probe._ssh_proxmox_host",
        return_value=(True, stdout, ""),
    ):
        out = probe_proxmox_guest_lock_host("192.168.0.200")
    assert out["ok"] is True
    assert out["outcome"] == "critical"
    assert len(out["locked_guests"]) == 1
    assert out["locked_guests"][0]["vmid"] == "111"
    assert len(out["orphan_snaps"]) == 1
    assert any("lock:" in a for a in out["alerts"])


def test_warn_on_root_disk():
    stdout = "root_pct=92\n"
    with patch(
        "lbg_agents.proxmox_guest_lock_probe._ssh_proxmox_host",
        return_value=(True, stdout, ""),
    ):
        out = probe_proxmox_guest_lock_host("192.168.0.200")
    assert out["outcome"] == "warn"
    assert out["root_pct"] == 92.0


def test_run_probe_aggregates(monkeypatch):
    monkeypatch.setenv("LBG_PROXMOX_HOSTS", "192.168.0.200")
    fake = {
        "ok": True,
        "outcome": "ok",
        "host": "192.168.0.200",
        "root_pct": 40.0,
        "locked_guests": [],
        "orphan_snaps": [],
        "alerts": [],
    }
    with patch(
        "lbg_agents.proxmox_guest_lock_probe.probe_proxmox_guest_lock_host",
        return_value=fake,
    ):
        out = run_proxmox_guest_lock_probe(actor_id="ops", text="locks")
    assert out["ok"] is True
    assert out["outcome"] == "ok"
    assert out["agent"] == "proxmox_guest_lock_probe"
