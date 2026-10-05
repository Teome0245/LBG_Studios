"""Tests remédiation RAM (infra_memory_remediation)."""

from __future__ import annotations

from unittest.mock import patch

from lbg_agents.infra_memory_remediation import (
    build_memory_remediation_plan,
    remediation_prime_enabled,
)
from lbg_agents.infra_watchdog import run_infra_watchdog
from lbg_agents.remediation import run_remediation


def _watchdog_critical_prime() -> dict:
    return {
        "ok": True,
        "outcome": "critical",
        "memory": {
            "ok": True,
            "worst_status": "critical",
            "hosts": [
                {
                    "label": "prime",
                    "host": "192.168.0.246",
                    "ok": True,
                    "status": "critical",
                    "metrics": {
                        "mem_avail_pct": 5.0,
                        "swap_used_pct": 12.0,
                        "top_processes": [{"comm": "core3-clean", "rss_kb": 7000000}],
                    },
                }
            ],
        },
        "alerts": ["mem:prime: critical"],
    }


def test_build_plan_prime_without_restart_flag(monkeypatch):
    monkeypatch.delenv("LBG_REMEDIATION_PRIME_ENABLED", raising=False)
    plan = build_memory_remediation_plan(_watchdog_critical_prime())
    assert plan["kind"] == "remediation_plan"
    assert plan["memory_worst_status"] == "critical"
    kinds = {a.get("devops_action", {}).get("kind") for a in plan["suggested_actions"] if a.get("devops_action")}
    assert "infra_watchdog" in kinds
    assert "systemd_restart" not in kinds
    assert any("LBG_REMEDIATION_PRIME_ENABLED=0" in h for h in plan["hints"])


def test_build_plan_prime_with_restart_flag(monkeypatch):
    monkeypatch.setenv("LBG_REMEDIATION_PRIME_ENABLED", "1")
    plan = build_memory_remediation_plan(_watchdog_critical_prime())
    restart = [
        a for a in plan["suggested_actions"]
        if a.get("devops_action", {}).get("kind") == "systemd_restart"
    ]
    assert restart
    assert restart[0]["devops_action"]["unit"] == "lbg-core3-prime.service"
    assert restart[0]["requires_approval"] is True


def test_build_plan_ok_no_actions():
    plan = build_memory_remediation_plan(
        {
            "outcome": "ok",
            "memory": {"worst_status": "ok", "hosts": [{"label": "core", "ok": True, "status": "ok"}]},
        }
    )
    assert plan["suggested_actions"] == []


def test_infra_watchdog_attaches_plan_on_warn(monkeypatch, tmp_path):
    monkeypatch.setenv("LBG_INFRA_WATCHDOG_STATE", str(tmp_path / "state.json"))
    fake_mem = {
        "ok": True,
        "worst_status": "warn",
        "hosts": [
            {
                "label": "precu",
                "host": "192.168.0.245",
                "ok": True,
                "status": "warn",
                "metrics": {"mem_avail_pct": 10.0, "top_processes": []},
            }
        ],
        "reply": "mem warn",
    }
    with patch("lbg_agents.infra_watchdog.proxmox_configured", return_value=False):
        with patch("lbg_agents.infra_watchdog.run_vm_memory_probe", return_value=fake_mem):
            out = run_infra_watchdog(persist=False)
    assert out["outcome"] == "warn"
    assert out["remediation_plan"]["kind"] == "remediation_plan"
    assert out["remediation_plan"]["stressed_hosts"]


def test_remediation_plan_memory_step(monkeypatch):
    wd = _watchdog_critical_prime()

    def fake_watchdog(**kwargs):
        return wd

    monkeypatch.setenv("LBG_REMEDIATION_PRIME_ENABLED", "0")
    with patch("lbg_agents.infra_watchdog.run_infra_watchdog", side_effect=fake_watchdog):
        out = run_remediation(
            actor_id="ops",
            text="plan mémoire",
            action={"step": "plan", "source": "memory"},
            context={},
        )
    assert out["ok"] is True
    assert out["meta"]["source"] == "infra_memory"
    assert "RAM" in out["reply"] or "mémoire" in out["reply"].lower() or "Prime" in out["reply"]


def test_remediation_prime_enabled_default_off():
    assert remediation_prime_enabled() is False


def _watchdog_critical_light_sticky() -> dict:
    return {
        "ok": True,
        "outcome": "critical",
        "memory": {
            "ok": True,
            "worst_status": "critical",
            "hosts": [
                {
                    "label": "light",
                    "host": "192.168.0.111",
                    "ok": True,
                    "status": "critical",
                    "metrics": {
                        "mem_avail_pct": 70.0,
                        "swap_used_pct": 100.0,
                        "sticky_swap": True,
                        "top_processes": [{"comm": "ollama", "rss_kb": 4000000}],
                    },
                }
            ],
        },
        "alerts": ["mem:light: critical"],
    }


def test_build_plan_light_sticky_swap():
    plan = build_memory_remediation_plan(_watchdog_critical_light_sticky())
    assert plan["memory_worst_status"] == "critical"
    assert any("swap collé" in h or "swap saturé" in h for h in plan["hints"])
    labels = [a.get("label", "") for a in plan["suggested_actions"]]
    assert any("laya-serve" in lab for lab in labels)
    ssh_kinds = [
        a for a in plan["suggested_actions"]
        if (a.get("devops_action") or {}).get("kind") == "ssh_run"
    ]
    assert ssh_kinds
    assert all(a["devops_action"]["server_id"] == "light" for a in ssh_kinds)
    # Pas de systemd_restart local 140 pour light
    assert not any(
        (a.get("devops_action") or {}).get("kind") == "systemd_restart"
        for a in plan["suggested_actions"]
    )