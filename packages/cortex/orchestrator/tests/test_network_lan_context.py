"""Tests contexte LAN Atlas."""

from __future__ import annotations

import json
from pathlib import Path

from team.network_lan_context import load_network_lan_context


def test_load_network_lan_context_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LBG_NETWORK_INVENTORY_STATE", str(tmp_path / "missing.json"))
    out = load_network_lan_context()
    assert out["ok"] is False
    assert out["error"] == "state_missing"


def test_load_network_lan_context_ok(tmp_path: Path, monkeypatch) -> None:
    import time

    state = tmp_path / "state.json"
    state.write_text(
        json.dumps(
            {
                "ts": time.time(),
                "n_hosts": 3,
                "n_present": 2,
                "last_diff": {
                    "n_appeared": 1,
                    "n_disappeared": 0,
                    "appeared": [{"host": "192.168.0.75", "label": "Séjour", "role": "cast"}],
                    "disappeared": [],
                    "still_count": 1,
                },
                "hosts": {
                    "192.168.0.75": {
                        "label": "Séjour",
                        "role": "cast",
                        "reachable": True,
                        "mac": "D4:F5:47:16:23:64",
                    },
                    "192.168.0.140": {"label": "core", "role": "core", "reachable": True},
                    "192.168.0.99": {"label": "gone", "role": "phone", "reachable": False},
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("LBG_NETWORK_INVENTORY_STATE", str(state))
    out = load_network_lan_context()
    assert out["ok"] is True
    assert out["fresh"] is True
    assert out["last_diff"]["n_appeared"] == 1
    assert out["by_role"].get("cast") == 1
    assert any(e["host"] == "192.168.0.75" for e in out["edge_devices"])
