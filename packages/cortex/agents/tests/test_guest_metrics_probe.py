"""Tests sonde guest mur INFRA LAN + remédiation."""

from __future__ import annotations

from unittest.mock import patch

from lbg_agents.guest_metrics_probe import (
    disk_crit_pct,
    disk_warn_pct,
    probe_guest_host,
    probe_guest_metrics_wall,
)
from lbg_agents.infra_guest_remediation import build_guest_remediation_plan


def test_probe_warn_disk(monkeypatch):
    monkeypatch.setenv("LBG_GUEST_DISK_WARN_PCT", "70")
    monkeypatch.setenv("LBG_GUEST_DISK_CRIT_PCT", "85")
    stdout = "disk_pct=81\nload1=3.34\nnproc=4\nmem_pct=27\n"
    with patch("lbg_agents.guest_metrics_probe._run_probe_ssh", return_value=(True, stdout, "")):
        with patch("lbg_agents.guest_metrics_probe._local_ips", return_value=set()):
            row = probe_guest_host({"id": "web", "label": "Front web", "host": "192.168.0.100"})
    assert row["ok"] is True
    assert row["outcome"] == "warn"
    assert row["disk_percent"] == 81.0
    assert row["load_ratio"] == 0.835  # 3.34/4 < 1.0 → disk alone drives warn


def test_probe_critical_load_soft_warn_by_default(monkeypatch):
    monkeypatch.setenv("LBG_GUEST_LOAD_WARN_RATIO", "1.0")
    monkeypatch.setenv("LBG_GUEST_LOAD_CRIT_RATIO", "2.0")
    monkeypatch.delenv("LBG_GUEST_LOAD_CAN_CRIT", raising=False)
    stdout = "disk_pct=20\nload1=8.5\nnproc=4\nmem_pct=10\n"
    with patch("lbg_agents.guest_metrics_probe._run_probe_ssh", return_value=(True, stdout, "")):
        with patch("lbg_agents.guest_metrics_probe._local_ips", return_value=set()):
            row = probe_guest_host({"id": "web", "label": "Front web", "host": "192.168.0.100"})
    assert row["outcome"] == "warn"
    assert any("soft→warn" in a for a in row["alerts"])


def test_probe_critical_load_hard_when_enabled(monkeypatch):
    monkeypatch.setenv("LBG_GUEST_LOAD_WARN_RATIO", "1.0")
    monkeypatch.setenv("LBG_GUEST_LOAD_CRIT_RATIO", "2.0")
    monkeypatch.setenv("LBG_GUEST_LOAD_CAN_CRIT", "1")
    stdout = "disk_pct=20\nload1=8.5\nnproc=4\nmem_pct=10\n"
    with patch("lbg_agents.guest_metrics_probe._run_probe_ssh", return_value=(True, stdout, "")):
        with patch("lbg_agents.guest_metrics_probe._local_ips", return_value=set()):
            row = probe_guest_host({"id": "web", "label": "Front web", "host": "192.168.0.100"})
    assert row["outcome"] == "critical"


def test_probe_ssh_failure():
    with patch("lbg_agents.guest_metrics_probe._run_probe_ssh", return_value=(False, "", "timeout")):
        with patch("lbg_agents.guest_metrics_probe._local_ips", return_value=set()):
            row = probe_guest_host({"id": "prime", "label": "Prime", "host": "192.168.0.246"})
    assert row["ok"] is False
    assert row["outcome"] == "critical"


def test_wall_worst_outcome(monkeypatch):
    monkeypatch.setenv(
        "LBG_GUEST_METRICS_HOSTS",
        "web:192.168.0.100:Front,core:192.168.0.140:Core",
    )
    monkeypatch.setenv("LBG_GUEST_DISK_WARN_PCT", "70")

    def fake_ssh(host, timeout_s=12.0):
        if host.endswith(".100"):
            return True, "disk_pct=81\nload1=1.0\nnproc=4\nmem_pct=27\n", ""
        return True, "disk_pct=25\nload1=0.1\nnproc=4\nmem_pct=11\n", ""

    with patch("lbg_agents.guest_metrics_probe._run_probe_ssh", side_effect=fake_ssh):
        with patch("lbg_agents.guest_metrics_probe._local_ips", return_value=set()):
            wall = probe_guest_metrics_wall()
    assert wall["outcome"] == "warn"
    assert len(wall["stressed"]) == 1
    assert wall["stressed"][0]["id"] == "web"


def test_remediation_front_web():
    wall = {
        "ok": True,
        "outcome": "warn",
        "stressed": [
            {
                "ok": True,
                "id": "web",
                "label": "Front web",
                "host": "192.168.0.100",
                "outcome": "warn",
                "disk_percent": 81.0,
                "load1": 3.34,
                "nproc": 2,
            }
        ],
        "hosts": [],
    }
    plan = build_guest_remediation_plan(wall)
    assert plan["outcome"] == "warn"
    assert plan["suggested_actions"]
    labels = " ".join(str(a.get("label") or "") for a in plan["suggested_actions"])
    assert "Docker" in labels or "docker" in labels.lower() or "inventaire" in labels.lower()


def test_remediation_prime_hygiene():
    wall = {
        "ok": True,
        "outcome": "warn",
        "stressed": [
            {
                "ok": True,
                "id": "prime",
                "label": "Prime monde",
                "host": "192.168.0.246",
                "outcome": "warn",
                "disk_percent": 70.0,
                "load1": 1.0,
                "nproc": 4,
            }
        ],
    }
    plan = build_guest_remediation_plan(wall)
    assert any(
        isinstance(a, dict) and a.get("devops_action")
        for a in plan["suggested_actions"]
    )


def test_thresholds(monkeypatch):
    monkeypatch.setenv("LBG_GUEST_DISK_WARN_PCT", "70")
    monkeypatch.setenv("LBG_GUEST_DISK_CRIT_PCT", "85")
    assert disk_warn_pct() == 70
    assert disk_crit_pct() == 85


def test_default_wall_precu_245_off_is_not_error(monkeypatch):
    monkeypatch.delenv("LBG_GUEST_METRICS_HOSTS", raising=False)
    monkeypatch.delenv("LBG_GUEST_METRICS_PRECU_REQUIRED", raising=False)

    def fake_ssh(host, timeout_s=12.0):
        if host.endswith(".245"):
            return False, "", "ssh: connect to host 192.168.0.245 port 22: Connection timed out"
        return True, "disk_pct=30\nload1=0.2\nnproc=4\nmem_pct=20\n", ""

    with patch("lbg_agents.guest_metrics_probe._run_probe_ssh", side_effect=fake_ssh):
        with patch("lbg_agents.guest_metrics_probe._local_ips", return_value=set()):
            wall = probe_guest_metrics_wall()

    assert wall["ok"] is True
    assert wall["outcome"] == "ok"
    assert wall["stressed"] == []
    assert wall["alerts"] == []
    precu_row = next(h for h in wall["hosts"] if h["id"] == "precu")
    assert precu_row["outcome"] == "off"

