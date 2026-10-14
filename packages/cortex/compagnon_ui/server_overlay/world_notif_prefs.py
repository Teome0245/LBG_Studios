"""Préférences de rapports monde (style Dynasty Nova) — filtre greeting / stream / contexte.

Catégories :
  world_marking     — boss, événements zone, chute ferraille…
  companion_social  — escorte / greets hub
  ops_jobs          — réservé (Jobs L2 / sondes) — pas du world_stream
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

_lock = threading.RLock()

CATEGORIES = ("world_marking", "companion_social", "ops_jobs")

_DEFAULTS: dict[str, bool] = {
    "world_marking": True,
    "companion_social": True,
    "ops_jobs": True,
}

_STATE: dict[str, bool] = dict(_DEFAULTS)


def prefs_path() -> Path:
    raw = (os.getenv("LBG_WORLD_NOTIF_PREFS_PATH") or "").strip()
    if raw:
        return Path(raw)
    return Path("/tmp/lbg_world_notif_prefs_v1.json")


def load_prefs() -> dict[str, bool]:
    global _STATE
    with _lock:
        p = prefs_path()
        try:
            if p.is_file():
                data = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    next_state = dict(_DEFAULTS)
                    for k in CATEGORIES:
                        if k in data:
                            next_state[k] = bool(data[k])
                    _STATE = next_state
        except Exception:
            pass
        return dict(_STATE)


def save_prefs(patch: dict[str, Any] | None) -> dict[str, bool]:
    global _STATE
    with _lock:
        next_state = dict(_STATE) if _STATE else dict(_DEFAULTS)
        if isinstance(patch, dict):
            for k in CATEGORIES:
                if k in patch:
                    next_state[k] = bool(patch[k])
        _STATE = next_state
        try:
            p = prefs_path()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(_STATE, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
        return dict(_STATE)


def category_for_event(ev: dict[str, Any] | None) -> str:
    kind = str((ev or {}).get("kind") or "").lower()
    if "companion" in kind or "escort" in kind:
        return "companion_social"
    if any(
        x in kind
        for x in ("boss", "beast", "event.", "scrap", "ferraille", "world.", "activate", "end")
    ):
        return "world_marking"
    return "world_marking"


def allows_category(cat: str, prefs: dict[str, bool] | None = None) -> bool:
    p = prefs if isinstance(prefs, dict) else load_prefs()
    key = str(cat or "")
    if key not in CATEGORIES:
        return True
    return bool(p.get(key, True))


def filter_events(
    events: list[Any] | None,
    prefs: dict[str, bool] | None = None,
) -> list[dict[str, Any]]:
    p = prefs if isinstance(prefs, dict) else load_prefs()
    out: list[dict[str, Any]] = []
    for ev in events or []:
        if not isinstance(ev, dict):
            continue
        cat = category_for_event(ev)
        if allows_category(cat, p):
            out.append(ev)
    return out
