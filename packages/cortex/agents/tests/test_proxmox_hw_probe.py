"""Tests sonde matériel Proxmox (BMC / PERC / thermiques) — mocks SSH."""

from __future__ import annotations

from unittest.mock import patch

from lbg_agents.proxmox_hw_probe import (
    _aggregate_hw_probes,
    format_hw_probe_reply,
    probe_proxmox_hw_host,
    probe_proxmox_hw_local,
    proxmox_hw_ssh_hosts,
    run_proxmox_hw_probe,
)


def _kv(**kwargs: str) -> str:
    base = {
        "HOSTNAME": "pve",
        "PRODUCT": "PowerEdge R720",
        "SERIAL": "JDLFS12",
        "BIOS": "2.9.0",
        "PVE": "pve-manager/8.0",
        "UPTIME_S": "1000",
        "LOAD": "0.1 0.2 0.3",
        "IPMI_DEV": "0",
        "IPMI_SI_FAIL": "1",
        "IPMI_MC_OK": "0",
        "BMC_OK": "0",
        "PERC_PRESENT": "1",
        "PERCCLI": "",
        "CPU_PKG0": "45",
        "CPU_PKG1": "46",
        "SMART_COUNT": "2",
        "SMART_WARN": "0",
        "SMART_FAIL": "0",
        "SMART_LINES": "0|ST1000|ABC|PASSED|0|32;1|ST1000|DEF|PASSED|0|33;",
    }
    base.update(kwargs)
    return "".join(f"{k}={v}\n" for k, v in base.items())


def test_hw_hosts_default(monkeypatch):
    monkeypatch.delenv("LBG_PROXMOX_HW_SSH_HOSTS", raising=False)
    monkeypatch.delenv("LBG_PROXMOX_SSH_HOSTS", raising=False)
    monkeypatch.delenv("LBG_PROXMOX_HOSTS", raising=False)
    assert proxmox_hw_ssh_hosts() == ["192.168.0.200", "192.168.0.201"]


def test_hw_hosts_env(monkeypatch):
    monkeypatch.setenv("LBG_PROXMOX_HW_SSH_HOSTS", "192.168.0.200,192.168.0.201")
    assert proxmox_hw_ssh_hosts() == ["192.168.0.200", "192.168.0.201"]


def test_probe_degraded_bmc_dead():
    with patch(
        "lbg_agents.proxmox_hw_probe._ssh_hw_host",
        return_value=(True, _kv(BMC_OK="0", IPMI_MC_OK="0"), ""),
    ):
        payload = probe_proxmox_hw_host("192.168.0.201")
    assert payload["ok"] is True
    assert payload["outcome"] == "degraded"
    assert payload["bmc"]["state"] == "dead"


def test_probe_warn_thermal():
    with patch(
        "lbg_agents.proxmox_hw_probe._ssh_hw_host",
        return_value=(True, _kv(BMC_OK="1", IPMI_MC_OK="1", CPU_PKG0="72", CPU_PKG1="60"), ""),
    ):
        payload = probe_proxmox_hw_host("192.168.0.201")
    assert payload["outcome"] == "warn"
    assert payload["thermal"]["state"] == "warn"


def test_probe_critical_thermal():
    with patch(
        "lbg_agents.proxmox_hw_probe._ssh_hw_host",
        return_value=(True, _kv(BMC_OK="1", IPMI_MC_OK="1", CPU_PKG0="90"), ""),
    ):
        payload = probe_proxmox_hw_host("192.168.0.201")
    assert payload["outcome"] == "critical"


def test_probe_critical_smart_fail():
    with patch(
        "lbg_agents.proxmox_hw_probe._ssh_hw_host",
        return_value=(True, _kv(BMC_OK="1", IPMI_MC_OK="1", SMART_FAIL="1"), ""),
    ):
        payload = probe_proxmox_hw_host("192.168.0.201")
    assert payload["outcome"] == "critical"


def test_probe_warn_smart_realloc():
    lines = "0|ST1000|ABC|PASSED|55|32;"
    with patch(
        "lbg_agents.proxmox_hw_probe._ssh_hw_host",
        return_value=(True, _kv(BMC_OK="1", IPMI_MC_OK="1", SMART_WARN="1", SMART_LINES=lines), ""),
    ):
        payload = probe_proxmox_hw_host("192.168.0.201")
    assert payload["outcome"] == "warn"


def test_probe_ssh_failure():
    with patch("lbg_agents.proxmox_hw_probe._ssh_hw_host", return_value=(False, "", "timeout")):
        payload = probe_proxmox_hw_host("192.168.0.201")
    assert payload["ok"] is False
    assert payload["outcome"] == "critical"


def test_multi_host_worst(monkeypatch):
    monkeypatch.setenv("LBG_PROXMOX_HW_SSH_HOSTS", "192.168.0.200,192.168.0.201")

    def fake_ssh(host, script, timeout_s=45.0):
        if host == "192.168.0.201":
            return True, _kv(BMC_OK="0"), ""
        return True, _kv(BMC_OK="1", IPMI_MC_OK="1", IPMI_SI_FAIL="0", PRODUCT="NUC"), ""

    with patch("lbg_agents.proxmox_hw_probe._ssh_hw_host", side_effect=fake_ssh):
        payload = probe_proxmox_hw_local()
    assert payload["outcome"] == "degraded"
    assert len(payload["hosts"]) == 2
    reply = format_hw_probe_reply(payload)
    assert "192.168.0.201" in reply


def test_aggregate_all_failed():
    hosts = [
        {"ok": False, "outcome": "critical", "error": "timeout", "host": "192.168.0.200"},
        {"ok": False, "outcome": "critical", "error": "timeout", "host": "192.168.0.201"},
    ]
    agg = _aggregate_hw_probes(hosts)
    assert agg["ok"] is False
    assert agg["outcome"] == "critical"


def test_run_proxmox_hw_probe(monkeypatch):
    monkeypatch.setenv("LBG_PROXMOX_HW_SSH_HOSTS", "192.168.0.201")
    with patch(
        "lbg_agents.proxmox_hw_probe._ssh_hw_host",
        return_value=(True, _kv(BMC_OK="1", IPMI_MC_OK="1", IPMI_SI_FAIL="0"), ""),
    ):
        out = run_proxmox_hw_probe()
    assert out["ok"] is True
    assert out["outcome"] == "ok"
    assert "proxmox_hw" in out
