"""Tests Freebox client (audit + auth helpers) — sans appels réseau."""

from __future__ import annotations

from lbg_agents.freebox_client import audit_static_leases, expected_leases, format_audit_text


def test_audit_static_leases_ok() -> None:
    expected = expected_leases()
    leases = [
        {"ip": ip, "mac": meta["mac"], "hostname": meta.get("label") or ""}
        for ip, meta in expected.items()
    ]
    audit = audit_static_leases(leases)
    assert audit["ok"] is True
    assert audit["n_missing"] == 0
    assert audit["n_mac_mismatch"] == 0
    assert audit["n_ok"] == len(expected)


def test_audit_detects_missing_and_mac_mismatch() -> None:
    leases = [
        {"ip": "192.168.0.143", "mac": "aa:bb:cc:dd:ee:ff", "hostname": "wrong"},
        {"ip": "192.168.0.10", "mac": "04:7c:16:cd:98:a5", "hostname": "pc"},
    ]
    audit = audit_static_leases(leases)
    assert audit["ok"] is False
    assert any(r["ip"] == "192.168.0.143" for r in audit["mac_mismatch"])
    assert any(r["ip"] == "192.168.0.140" for r in audit["missing"])


def test_format_audit_not_configured() -> None:
    text = format_audit_text({"configured": False})
    assert "non configurée" in text
