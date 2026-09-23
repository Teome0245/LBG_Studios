"""Politique de buts Lia (Agency C) — déterministe depuis drives Self.

Pas de LLM ici : seuils → candidats goal. Apply / expire = ``services.self_state``.
"""

from __future__ import annotations

import os
import time
import uuid
from typing import Any


def lia_goals_enabled() -> bool:
    return os.environ.get("LBG_LIA_GOALS_ENABLED", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def max_active_lia_goals() -> int:
    try:
        return max(1, min(int(os.environ.get("LBG_LIA_GOALS_MAX_ACTIVE", "2")), 4))
    except ValueError:
        return 2


def _threshold(env_key: str, default: float) -> float:
    try:
        return max(0.0, min(1.0, float(os.environ.get(env_key, str(default)))))
    except ValueError:
        return default


def social_hunger_min() -> float:
    return _threshold("LBG_LIA_GOAL_SOCIAL_HUNGER_MIN", 0.45)


def curiosity_min() -> float:
    return _threshold("LBG_LIA_GOAL_CURIOSITY_MIN", 0.55)


def tension_min() -> float:
    return _threshold("LBG_LIA_GOAL_TENSION_MIN", 0.60)


def goal_ttl_s() -> float:
    try:
        return max(60.0, min(float(os.environ.get("LBG_LIA_GOAL_TTL_S", "1800")), 86400.0))
    except ValueError:
        return 1800.0


def _drive(drives: dict[str, Any], key: str) -> float:
    try:
        return max(0.0, min(1.0, float(drives.get(key) or 0.0)))
    except (TypeError, ValueError):
        return 0.0


def propose_lia_goals(
    *,
    drives: dict[str, Any],
    existing_goals: list[dict[str, Any]] | None = None,
    now: float | None = None,
) -> list[dict[str, Any]]:
    """Propose de nouveaux goals ``owner=lia`` sans dépasser le plafond d'actifs."""
    ts = float(now if now is not None else time.time())
    existing = [g for g in (existing_goals or []) if isinstance(g, dict)]
    active = [
        g
        for g in existing
        if str(g.get("owner") or "") == "lia" and str(g.get("status") or "") == "active"
    ]
    active_origins = {str(g.get("origin") or "") for g in active}
    room = max_active_lia_goals() - len(active)
    if room <= 0:
        return []

    social = _drive(drives, "social_hunger")
    curiosity = _drive(drives, "curiosity")
    tension = _drive(drives, "tension")
    candidates: list[tuple[float, dict[str, Any]]] = []

    if social >= social_hunger_min() and "drive:social_hunger" not in active_origins:
        candidates.append(
            (
                social,
                _new_goal(
                    title="Saluer un joueur proche",
                    origin="drive:social_hunger",
                    priority=social,
                    success_when=["interact:greet", "say:hello", "approach_player"],
                    ts=ts,
                ),
            )
        )
    if curiosity >= curiosity_min() and "drive:curiosity" not in active_origins:
        candidates.append(
            (
                curiosity,
                _new_goal(
                    title="Explorer / se manifester",
                    origin="drive:curiosity",
                    priority=curiosity,
                    success_when=["perform:wave", "perform:search"],
                    ts=ts,
                ),
            )
        )
    if tension >= tension_min() and "drive:tension" not in active_origins:
        candidates.append(
            (
                tension,
                _new_goal(
                    title="Relâcher la tension (geste / danse)",
                    origin="drive:tension",
                    priority=tension,
                    success_when=["perform:dance", "perform:wave"],
                    ts=ts,
                ),
            )
        )

    candidates.sort(key=lambda x: x[0], reverse=True)
    return [g for _, g in candidates[:room]]


def _new_goal(
    *,
    title: str,
    origin: str,
    priority: float,
    success_when: list[str],
    ts: float,
) -> dict[str, Any]:
    return {
        "id": f"goal_{uuid.uuid4().hex[:10]}",
        "surface": "mmo",
        "owner": "lia",
        "title": title,
        "origin": origin,
        "priority": round(priority, 3),
        "status": "active",
        "autonomy": "L1",
        "created_ts": ts,
        "expires_ts": ts + goal_ttl_s(),
        "success_when": list(success_when),
        "lesson_refs": [],
        "last_action": None,
    }


def pick_active_lia_goal(goals: list[Any] | None) -> dict[str, Any] | None:
    active = [
        g
        for g in (goals or [])
        if isinstance(g, dict)
        and str(g.get("owner") or "") == "lia"
        and str(g.get("status") or "") == "active"
    ]
    if not active:
        return None
    active.sort(key=lambda g: float(g.get("priority") or 0.0), reverse=True)
    return active[0]


def origin_drive_key(origin: str) -> str | None:
    raw = (origin or "").strip()
    if raw.startswith("drive:"):
        return raw.split(":", 1)[1].strip() or None
    return None


def action_spec_for_goal(goal: dict[str, Any], *, relay_player: str = "Gally") -> dict[str, str]:
    """Mappe un goal vers une action sidecar déterministe."""
    origin = str(goal.get("origin") or "")
    if origin == "drive:social_hunger":
        target = (relay_player or "Gally").strip() or "Gally"
        return {"action": "approach_player", "message": target, "success_tag": "approach_player"}
    if origin == "drive:tension":
        return {"action": "perform", "message": "dance", "success_tag": "perform:dance"}
    # curiosity default
    return {"action": "perform", "message": "wave", "success_tag": "perform:wave"}


def meta_status() -> dict[str, object]:
    return {
        "enabled": lia_goals_enabled(),
        "max_active": max_active_lia_goals(),
        "thresholds": {
            "social_hunger": social_hunger_min(),
            "curiosity": curiosity_min(),
            "tension": tension_min(),
        },
        "ttl_s": goal_ttl_s(),
    }
