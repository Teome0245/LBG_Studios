"""Contexte LAN pour Atlas — lecture read-only de l’état inventaire réseau."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


def network_inventory_state_path() -> Path:
    raw = os.environ.get("LBG_NETWORK_INVENTORY_STATE", "").strip()
    if raw:
        return Path(raw)
    return Path("/var/lib/lbg/network_inventory/state.json")


def _fresh_max_age_s() -> float:
    try:
        return max(60.0, float(os.environ.get("LBG_ATLAS_LAN_STATE_MAX_AGE_S", "7200")))
    except ValueError:
        return 7200.0


def load_network_lan_context() -> dict[str, Any]:
    """Résumé inventaire LAN pour enrichir le workflow Atlas (pas de scan)."""
    path = network_inventory_state_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "ok": False,
            "configured": False,
            "error": "state_missing",
            "path": str(path),
            "hint": "Timer lbg-network-inventory-job (Héphaïstos) ou inventaire Compagnon",
        }
    if not isinstance(data, dict):
        return {"ok": False, "configured": True, "error": "state_invalid", "path": str(path)}

    ts = float(data.get("ts") or 0)
    age_s = (time.time() - ts) if ts else None
    fresh = age_s is not None and age_s <= _fresh_max_age_s()
    last_diff = data.get("last_diff") if isinstance(data.get("last_diff"), dict) else {}
    hosts = data.get("hosts") if isinstance(data.get("hosts"), dict) else {}
    present = [h for h, meta in hosts.items() if isinstance(meta, dict) and meta.get("reachable")]
    by_role: dict[str, int] = {}
    cast_or_iot: list[dict[str, Any]] = []
    for host, meta in hosts.items():
        if not isinstance(meta, dict):
            continue
        role = str(meta.get("role") or "lan")
        by_role[role] = by_role.get(role, 0) + 1
        if role in {"iot", "cast", "speaker", "stb", "phone", "console"} and meta.get("reachable"):
            cast_or_iot.append(
                {
                    "host": host,
                    "label": meta.get("label"),
                    "role": role,
                    "mac": meta.get("mac"),
                }
            )

    return {
        "ok": True,
        "configured": True,
        "fresh": fresh,
        "path": str(path),
        "ts": ts,
        "age_s": round(age_s, 1) if age_s is not None else None,
        "n_hosts": int(data.get("n_hosts") or len(hosts)),
        "n_present": int(data.get("n_present") or len(present)),
        "by_role": by_role,
        "last_diff": {
            "n_appeared": int(last_diff.get("n_appeared") or 0),
            "n_disappeared": int(last_diff.get("n_disappeared") or 0),
            "appeared": (last_diff.get("appeared") or [])[:12],
            "disappeared": (last_diff.get("disappeared") or [])[:12],
            "still_count": last_diff.get("still_count"),
        },
        "edge_devices": cast_or_iot[:20],
    }
