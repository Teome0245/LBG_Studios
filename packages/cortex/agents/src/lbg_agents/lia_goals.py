"""Client Lia — buts Self (Agency C). HTTP vers orchestrateur + actions déterministes."""

from __future__ import annotations

import os
from typing import Any

import httpx

from lbg_agents.lia_orchestrator import (
    _post_sidecar_enqueue,
    bot_player_name,
    orchestrator_base_url,
    relay_player_names,
)


def lia_goals_enabled() -> bool:
    return os.environ.get("LBG_LIA_GOALS_ENABLED", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def fetch_self_status(*, ensure_goals: bool = True, timeout: float = 5.0) -> dict[str, Any] | None:
    base = orchestrator_base_url()
    if not base:
        return None
    q = "ensure_goals=1" if ensure_goals else "ensure_goals=0"
    try:
        with httpx.Client(timeout=httpx.Timeout(timeout)) as client:
            resp = client.get(f"{base}/v1/self/status?{q}")
        if resp.status_code != 200:
            return None
        data = resp.json()
        return data if isinstance(data, dict) else None
    except httpx.HTTPError:
        return None


def pick_active_lia_goal(self_payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(self_payload, dict):
        return None
    state = self_payload.get("state")
    if not isinstance(state, dict):
        return None
    goals = state.get("goals")
    if not isinstance(goals, list):
        return None
    active = [
        g
        for g in goals
        if isinstance(g, dict)
        and str(g.get("owner") or "") == "lia"
        and str(g.get("status") or "") == "active"
    ]
    if not active:
        return None
    active.sort(key=lambda g: float(g.get("priority") or 0.0), reverse=True)
    return active[0]


def action_spec_for_goal(goal: dict[str, Any]) -> dict[str, str]:
    origin = str(goal.get("origin") or "")
    if origin == "drive:social_hunger":
        relays = relay_player_names()
        target = relays[0] if relays else "Gally"
        return {"action": "approach_player", "message": target, "success_tag": "approach_player"}
    if origin == "drive:tension":
        return {"action": "perform", "message": "dance", "success_tag": "perform:dance"}
    return {"action": "perform", "message": "wave", "success_tag": "perform:wave"}


def complete_goal_remote(
    goal_id: str,
    *,
    last_action: str | None = None,
    decay_amount: float = 0.25,
    timeout: float = 5.0,
) -> dict[str, Any] | None:
    base = orchestrator_base_url()
    if not base or not goal_id:
        return None
    body = {
        "goal_id": goal_id,
        "last_action": last_action,
        "decay_drive": True,
        "decay_amount": decay_amount,
    }
    try:
        with httpx.Client(timeout=httpx.Timeout(timeout)) as client:
            resp = client.post(f"{base}/v1/self/goals/complete", json=body)
        if resp.status_code != 200:
            return None
        data = resp.json()
        return data if isinstance(data, dict) else None
    except httpx.HTTPError:
        return None


def bump_drive_remote(key: str, delta: float, *, timeout: float = 5.0) -> None:
    base = orchestrator_base_url()
    if not base:
        return
    try:
        with httpx.Client(timeout=httpx.Timeout(timeout)) as client:
            client.post(
                f"{base}/v1/self/drives/bump",
                json={"key": key, "delta": float(delta)},
            )
    except httpx.HTTPError:
        return


def lessons_hint_from_self(self_payload: dict[str, Any] | None, *, limit: int = 2) -> str:
    """Petite injection textuelle (ids leçons) pour le prompt proactif."""
    if not isinstance(self_payload, dict):
        return ""
    state = self_payload.get("state")
    if not isinstance(state, dict):
        return ""
    refs = state.get("memory_refs")
    if not isinstance(refs, dict):
        return ""
    last_id = str(refs.get("last_lesson_id") or "").strip()
    count = refs.get("lessons_count")
    parts: list[str] = []
    if last_id:
        parts.append(f"derniere lecon={last_id}")
    if isinstance(count, int) and count > 0:
        parts.append(f"lecons={count}")
    if not parts:
        return ""
    return "Memoire Self (" + ", ".join(parts[:limit]) + ")."


def try_execute_active_goal(*, snapshot: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Si goals enabled + Self : exécute le goal Lia prioritaire. Sinon None."""
    if not lia_goals_enabled():
        return None
    payload = fetch_self_status(ensure_goals=True)
    if not payload or not payload.get("enabled"):
        return None
    goal = pick_active_lia_goal(payload)
    if goal is None:
        return None
    spec = action_spec_for_goal(goal)
    out = _post_sidecar_enqueue(
        action=spec["action"],
        message=spec["message"],
        player=bot_player_name(),
        snapshot=snapshot,
    )
    out["reason"] = f"lia_goal:{goal.get('id')}:{goal.get('origin')}"
    out["lia_goal"] = {
        "id": goal.get("id"),
        "title": goal.get("title"),
        "origin": goal.get("origin"),
        "priority": goal.get("priority"),
    }
    out["incarnation"] = True
    if out.get("ok"):
        complete_goal_remote(
            str(goal.get("id") or ""),
            last_action=spec.get("success_tag") or spec.get("action"),
        )
        # Succès social → baisse faim sociale un cran de plus si besoin
        if str(goal.get("origin") or "") == "drive:social_hunger":
            bump_drive_remote("social_hunger", -0.05)
    return out
