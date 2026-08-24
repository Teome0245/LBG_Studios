"""État bridge partagé pour sidecar craft/quêtes.

Persiste un petit état JSON côté ``ia_bridge`` afin que les endpoints :8791
gardent un comportement stable entre redémarrages, tout en restant simples à
déployer sur 246 et en fallback local.
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any

_LOCK = threading.Lock()
_CACHE: dict[str, dict[str, Any]] = {}


def bridge_dir() -> Path:
    raw = os.environ.get("LBG_CORE3_IA_BRIDGE_DIR", "").strip()
    if raw:
        return Path(raw)
    candidates = [
        Path("/opt/lbg-new-mmo-clean/MMOCoreORB/bin/ia_bridge"),
        Path("/opt/LBG_IA_MMO/content/core3/ia_bridge"),
        Path(__file__).resolve().parents[1] / "content" / "core3" / "ia_bridge",
    ]
    for cand in candidates:
        if cand.is_dir():
            return cand
    return candidates[-1]


def _state_path(name: str) -> Path:
    return bridge_dir() / name


def inventory_state_path() -> Path:
    return _state_path("inventory_players.json")


def player_items_path() -> Path:
    """Dump Lua Core3 (`IaBridgeScreenPlay:publishPlayerInventoryItems`)."""
    raw = os.environ.get("LBG_CORE3_PLAYER_ITEMS_JSON", "").strip()
    if raw:
        return Path(raw)
    return _state_path("player_inventory_items.json")


def clear_state_cache() -> None:
    with _LOCK:
        _CACHE.clear()


def quest_state_store_path() -> Path:
    return _state_path("quest_players.json")


def quest_events_path() -> Path:
    return _state_path("quest_state.jsonl")


def ensure_bridge_dir() -> Path:
    root = bridge_dir()
    root.mkdir(parents=True, exist_ok=True)
    return root


def load_json_doc(path: Path) -> dict[str, Any]:
    key = str(path)
    with _LOCK:
        cached = _CACHE.get(key)
        if isinstance(cached, dict):
            return json.loads(json.dumps(cached))
        if not path.is_file():
            doc: dict[str, Any] = {}
            _CACHE[key] = doc
            return {}
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            doc = {}
        if not isinstance(doc, dict):
            doc = {}
        _CACHE[key] = doc
        return json.loads(json.dumps(doc))


def save_json_doc(path: Path, doc: dict[str, Any]) -> dict[str, Any]:
    ensure_bridge_dir()
    clean = doc if isinstance(doc, dict) else {}
    key = str(path)
    with _LOCK:
        path.write_text(json.dumps(clean, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        _CACHE[key] = json.loads(json.dumps(clean))
    return json.loads(json.dumps(clean))


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    ensure_bridge_dir()
    payload = dict(row)
    payload.setdefault("ts", int(time.time()))
    with _LOCK:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
