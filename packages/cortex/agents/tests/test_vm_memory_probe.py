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


def test_precu_245_off_is_not_critical(monkeypatch):
    from unittest.mock import patch
    from lbg_agents.vm_memory_probe import run_vm_memory_probe

    monkeypatch.setenv("LBG_MCP_SSH_ENABLED", "1")
    monkeypatch.setenv("LBG_VM_MEMORY_PROBE_ENABLED", "1")
    monkeypatch.setenv("LBG_VM_MEMORY_PROBE_HOSTS", "prime=246,precu=245")
    monkeypatch.delenv("LBG_VM_MEMORY_PROBE_PRECU_REQUIRED", raising=False)

    good_out = "mem_total=12884901888 mem_used=2147483648 mem_avail=10737418240\nswap_total=4294967296 swap_used=0\nproc godot 155000\n"

    def fake_probe(host: str):
        if host.endswith(".245"):
            return False, "", "ssh: connect to host 192.168.0.245 port 22: Connection timed out"
        return True, good_out, ""

    with patch("lbg_agents.vm_memory_probe._run_probe", side_effect=fake_probe):
        res = run_vm_memory_probe(actor_id="test", text="check")

    assert res["ok"] is True
    assert res["worst_status"] == "ok"
    precu = next(h for h in res["hosts"] if h["label"] == "precu")
    assert precu["ok"] is True
    assert precu["status"] == "off"



