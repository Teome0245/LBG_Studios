"""Tests Synology client (helpers locaux) — sans appels réseau."""

from __future__ import annotations

from lbg_agents.synology_client import (
    _summarize_storage,
    format_nas_probe_text,
    nas_configured,
)


def test_summarize_storage_volume_pct() -> None:
    raw = {
        "volumes": [
            {
                "id": "volume_1",
                "status": "normal",
                "size": {"total": "1000", "used": "890"},
            }
        ],
        "disks": [{"id": "sda", "status": "normal", "model": "X", "temp": 35}],
    }
    summary = _summarize_storage(raw)
    assert len(summary["volumes"]) == 1
    assert summary["volumes"][0]["used_pct"] == 89.0
    assert len(summary["disks"]) == 1


def test_format_probe_not_configured() -> None:
    text = format_nas_probe_text({"configured": False})
    assert "non configuré" in text


def test_nas_configured_false_without_env(monkeypatch) -> None:
    monkeypatch.delenv("LBG_NAS_PASSWORD", raising=False)
    monkeypatch.delenv("LBG_NAS_TOKEN", raising=False)
    assert nas_configured() is False
