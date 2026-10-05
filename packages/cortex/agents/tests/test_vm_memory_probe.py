"""Sonde mémoire VM — parsing et planificateur."""

from __future__ import annotations

import pytest

from lbg_agents.vm_memory_probe import _parse_probe_output, _status


def test_parse_probe_output():
    raw = (
        "mem_total=12884901888 mem_used=8589934592 mem_avail=4294967296\n"
        "swap_total=4294967296 swap_used=0\n"
        "proc core3-clean 7864320\n"
        "proc python3 65536\n"
    )
    m = _parse_probe_output(raw)
    assert m["mem_total_b"] == 12884901888
    assert m["mem_avail_pct"] > 30
    assert m["top_processes"][0]["comm"] == "core3-clean"


def test_status_warn_and_critical():
    warn = _status({"mem_avail_pct": 12.0, "swap_used_pct": 0})
    crit = _status({"mem_avail_pct": 5.0, "swap_used_pct": 95.0})
    assert warn == "warn"
    assert crit == "critical"


def test_sticky_swap_critical_with_ram_headroom():
    from lbg_agents.vm_memory_probe import is_sticky_swap

    metrics = {"mem_avail_pct": 70.0, "swap_used_pct": 100.0}
    assert is_sticky_swap(metrics) is True
    assert _status(metrics) == "critical"


def test_default_hosts_include_light(monkeypatch):
    from lbg_agents.vm_memory_probe import _DEFAULT_HOSTS, _probe_hosts

    monkeypatch.delenv("LBG_VM_MEMORY_PROBE_HOSTS", raising=False)
    monkeypatch.delenv("LBG_VM_MEMORY_PROBE_EXCLUDE", raising=False)
    monkeypatch.setenv("LBG_INFRA_WATCHDOG_EXCLUDE_PRIME", "0")
    labels = {label for label, _ in _DEFAULT_HOSTS}
    assert "light" in labels
    hosts = _probe_hosts()
    by_label = {label: host for label, host in hosts}
    assert by_label.get("light") == "192.168.0.111"
