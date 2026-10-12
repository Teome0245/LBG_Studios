"""Tests inventaire réseau LAN."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from lbg_agents.network_inventory import (
    _catalog_from_freebox,
    _diff_against_previous,
    _role_from_name_vendor,
    run_network_inventory,
)


def _no_persist() -> dict:
    return {"persist_state": False, "freebox_probe": False, "nas_probe": False}


def test_network_inventory_returns_devices(monkeypatch) -> None:
    monkeypatch.setenv("LBG_LAN_HOST_CORE", "192.168.0.140")
    monkeypatch.setenv("LBG_LAN_HOST_FRONT", "192.168.0.110")
    monkeypatch.setenv("LBG_LAN_HOST_MMO", "192.168.0.245")
    monkeypatch.setenv("LBG_AGENT_DESKTOP_URL", "http://192.168.0.10:5005")

    def fake_scan(cidr: str) -> dict[str, list[int]]:
        return {
            "192.168.0.1": [80, 443],
            "192.168.0.50": [5000, 5001],
            "192.168.0.60": [8006],
            "192.168.0.70": [902, 443],
        }

    with patch("lbg_agents.network_inventory._scan_subnet", side_effect=fake_scan):
        with patch("lbg_agents.network_inventory._http_probe", return_value={"ok": True, "status_code": 200}):
            with patch("lbg_agents.network_inventory._tcp_reachable", return_value=True):
                with patch("lbg_agents.network_inventory._http_fingerprint", return_value={"ok": False}):
                    out = run_network_inventory(
                        actor_id="ops:1", text="inventaire réseau", context=_no_persist()
                    )

    assert out["ok"] is True
    assert out["agent"] == "network_inventory"
    devices = out["devices"]
    assert isinstance(devices, list) and len(devices) >= 7
    hosts = {d["host"] for d in devices}
    assert "192.168.0.140" in hosts
    assert "192.168.0.1" in hosts
    assert "192.168.0.50" in hosts
    assert out["n_hosts_alive"] == 4
    assert "scan_cidr" in out
    syn = next(d for d in devices if d["host"] == "192.168.0.50")
    assert syn.get("device_hint") == "synology/nas"
    prox = next(d for d in devices if d["host"] == "192.168.0.60")
    assert prox.get("device_hint") == "proxmox"
    assert isinstance(out.get("devices_export"), list)
    core = next(d for d in devices if d["host"] == "192.168.0.140")
    assert "devops_probe" in (core.get("action_suggestions") or [])


def test_action_suggestions_for_desktop(monkeypatch) -> None:
    monkeypatch.setenv("LBG_NETWORK_SCAN_ENABLED", "0")
    monkeypatch.setenv(
        "LBG_NETWORK_KNOWN_DEVICES",
        '[{"host":"192.168.0.10","label":"pc-windows","role":"desktop"}]',
    )
    with patch("lbg_agents.network_inventory._tcp_reachable", return_value=True):
        with patch("lbg_agents.network_inventory._http_probe", return_value={"ok": True, "status_code": 200}):
            out = run_network_inventory(actor_id="ops:1", text="scan", context=_no_persist())
    pc = next(d for d in out["devices"] if d["host"] == "192.168.0.10")
    assert "desktop_control" in pc.get("action_suggestions", [])


def test_router_override_replaces_wrong_gateway(monkeypatch) -> None:
    monkeypatch.setenv("LBG_NETWORK_SCAN_ENABLED", "0")
    monkeypatch.setenv("LBG_NETWORK_ROUTER_HOST", "192.168.0.254")
    monkeypatch.setenv(
        "LBG_NETWORK_KNOWN_DEVICES",
        '[{"host":"192.168.0.1","label":"freebox-routeur","role":"router"}]',
    )
    out = run_network_inventory(actor_id="ops:1", text="inventaire", context=_no_persist())
    hosts = {d["host"]: d for d in out["devices"]}
    assert "192.168.0.1" not in hosts
    assert hosts["192.168.0.254"]["label"] == "freebox-routeur"


def test_network_inventory_known_devices_json(monkeypatch) -> None:
    monkeypatch.setenv(
        "LBG_NETWORK_KNOWN_DEVICES",
        '[{"host":"192.168.0.254","label":"freebox","role":"router"},'
        '{"host":"192.168.0.246","label":"precu-vm","role":"precu","server_id":"precu"}]',
    )
    monkeypatch.setenv("LBG_NETWORK_SCAN_ENABLED", "0")

    out = run_network_inventory(actor_id="ops:1", text="inventaire", context=_no_persist())
    hosts = {d["host"] for d in out["devices"]}
    assert "192.168.0.254" in hosts
    assert "192.168.0.246" in hosts
    fb = next(d for d in out["devices"] if d["host"] == "192.168.0.254")
    assert fb.get("label") == "freebox"
    precu = next(d for d in out["devices"] if d["host"] == "192.168.0.246")
    assert precu.get("label") == "precu-vm"
    assert precu.get("server_id") == "precu"


def test_network_inventory_includes_hands_topology(monkeypatch) -> None:
    monkeypatch.setenv("LBG_NETWORK_SCAN_ENABLED", "0")
    monkeypatch.setenv("LBG_AGENT_HANDS_URL", "http://192.168.0.143:5005")
    monkeypatch.setenv("LBG_LAN_HOST_HANDS", "192.168.0.143")
    monkeypatch.delenv("LBG_NETWORK_KNOWN_DEVICES", raising=False)
    with patch("lbg_agents.network_inventory._tcp_reachable", return_value=True):
        with patch("lbg_agents.network_inventory._http_probe", return_value={"ok": True, "status_code": 200}):
            out = run_network_inventory(actor_id="ops:1", text="inventaire", context=_no_persist())
    hands = next(d for d in out["devices"] if d["host"] == "192.168.0.143")
    assert hands.get("role") in {"hands", "known"}
    assert "desktop_control" in (hands.get("action_suggestions") or [])


def test_role_from_name_vendor_switch_phone_iot() -> None:
    assert _role_from_name_vendor("TL-SG108E-SW", "TP-Link")[0] == "switch"
    assert _role_from_name_vendor("Freebox Server", "Freebox")[0] == "router"
    assert _role_from_name_vendor("iPhone de LBG", "")[0] == "phone"
    assert _role_from_name_vendor("Nest Cam salon", "Google")[0] == "iot"
    assert _role_from_name_vendor("Google-Nest-Mini", "Google")[0] == "cast"
    assert _role_from_name_vendor("Nintendo Switch", "Nintendo")[0] == "console"


def test_catalog_from_freebox_roles() -> None:
    fb = {
        "lan_hosts": [
            {
                "name": "TL-SG108E-SW",
                "vendor": "TP-Link",
                "mac": "aa:bb:cc:dd:ee:01",
                "ipv4": ["192.168.0.251"],
                "active": True,
                "reachable": True,
            },
            {
                "name": "Redmi Note",
                "vendor": "Xiaomi",
                "mac": "aa:bb:cc:dd:ee:02",
                "ipv4": ["192.168.0.88"],
                "active": True,
                "reachable": False,
            },
            {
                "name": "offline-cam",
                "vendor": "Nest",
                "mac": "aa:bb:cc:dd:ee:03",
                "ipv4": ["192.168.0.99"],
                "active": False,
                "reachable": False,
            },
        ]
    }
    rows = _catalog_from_freebox(fb, cidr="192.168.0.0/24")
    by_host = {r["host"]: r for r in rows}
    assert by_host["192.168.0.251"]["role"] == "switch"
    assert by_host["192.168.0.251"]["reachable"] is True
    assert by_host["192.168.0.88"]["role"] == "phone"
    assert by_host["192.168.0.99"]["reachable"] is False
    assert by_host["192.168.0.99"]["role"] == "iot"


def test_freebox_merged_into_inventory(monkeypatch) -> None:
    monkeypatch.setenv("LBG_NETWORK_SCAN_ENABLED", "0")
    monkeypatch.delenv("LBG_NETWORK_KNOWN_DEVICES", raising=False)
    fake_fb = {
        "ok": True,
        "configured": True,
        "lan_hosts": [
            {
                "name": "TL-SG108E-SW",
                "vendor": "TP-Link",
                "mac": "aa:bb:cc:01:02:03",
                "ipv4": ["192.168.0.251"],
                "active": True,
                "reachable": True,
            },
            {
                "name": "Portable-LBG",
                "vendor": "Dell",
                "mac": "aa:bb:cc:01:02:04",
                "ipv4": ["192.168.0.42"],
                "active": True,
                "reachable": True,
            },
        ],
    }
    with patch("lbg_agents.freebox_client.freebox_enabled", return_value=True):
        with patch("lbg_agents.freebox_client.probe_freebox", return_value=fake_fb):
            out = run_network_inventory(
                actor_id="ops:1",
                text="inventaire",
                context={"persist_state": False, "nas_probe": False},
            )
    hosts = {d["host"]: d for d in out["devices"]}
    assert hosts["192.168.0.251"]["role"] == "switch"
    assert hosts["192.168.0.251"]["mac"] == "aa:bb:cc:01:02:03"
    assert hosts["192.168.0.42"]["role"] == "desktop"
    assert out["by_role"].get("switch", 0) >= 1
    assert out["n_present"] >= 2


def test_diff_appeared_and_disappeared(tmp_path: Path, monkeypatch) -> None:
    state = tmp_path / "state.json"
    monkeypatch.setenv("LBG_NETWORK_INVENTORY_STATE", str(state))
    state.write_text(
        json.dumps(
            {
                "ts": 1.0,
                "hosts": {
                    "192.168.0.10": {"label": "pc-a", "role": "desktop", "reachable": True},
                    "192.168.0.20": {"label": "phone-b", "role": "phone", "reachable": True},
                },
            }
        ),
        encoding="utf-8",
    )
    devices = [
        {"host": "192.168.0.10", "label": "pc-a", "role": "desktop", "reachable": True},
        {"host": "192.168.0.30", "label": "iot-c", "role": "iot", "reachable": True, "freebox_active": True},
        {"host": "192.168.0.20", "label": "phone-b", "role": "phone", "reachable": False},
    ]
    diff = _diff_against_previous(devices)
    assert diff["n_appeared"] == 1
    assert diff["appeared"][0]["host"] == "192.168.0.30"
    assert diff["n_disappeared"] == 1
    assert diff["disappeared"][0]["host"] == "192.168.0.20"
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["hosts"]["192.168.0.30"]["reachable"] is True
    assert saved["hosts"]["192.168.0.20"]["reachable"] is False


def test_inventory_reply_includes_diff(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LBG_NETWORK_SCAN_ENABLED", "1")
    monkeypatch.setenv("LBG_NETWORK_INVENTORY_STATE", str(tmp_path / "state.json"))
    monkeypatch.delenv("LBG_NETWORK_KNOWN_DEVICES", raising=False)
    monkeypatch.delenv("LBG_AGENT_DESKTOP_URL", raising=False)

    def scan_a(cidr: str) -> dict[str, list[int]]:
        return {"192.168.0.10": [22]}

    def scan_b(cidr: str) -> dict[str, list[int]]:
        return {"192.168.0.99": [22]}

    with patch("lbg_agents.network_inventory._scan_subnet", side_effect=scan_a):
        with patch("lbg_agents.network_inventory._tcp_reachable", return_value=True):
            with patch("lbg_agents.network_inventory._http_probe", return_value={"ok": False}):
                with patch("lbg_agents.network_inventory._topology_probes", return_value=[]):
                    out1 = run_network_inventory(
                        actor_id="ops:1",
                        text="scan1",
                        context={"nas_probe": False, "freebox_probe": False},
                    )
    assert out1["diff"]["n_appeared"] >= 1
    assert "Changements depuis le dernier scan" in out1["reply"]

    with patch("lbg_agents.network_inventory._scan_subnet", side_effect=scan_b):
        with patch("lbg_agents.network_inventory._tcp_reachable", return_value=True):
            with patch("lbg_agents.network_inventory._http_probe", return_value={"ok": False}):
                with patch("lbg_agents.network_inventory._topology_probes", return_value=[]):
                    out2 = run_network_inventory(
                        actor_id="ops:1",
                        text="scan2",
                        context={"nas_probe": False, "freebox_probe": False},
                    )
    assert out2["diff"]["n_appeared"] >= 1
    assert out2["diff"]["n_disappeared"] >= 1
    assert any(r["host"] == "192.168.0.10" for r in out2["diff"]["disappeared"])
    assert any(r["host"] == "192.168.0.99" for r in out2["diff"]["appeared"])
