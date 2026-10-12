"""Enrichit session_summary depuis le sidecar Prime autoritatif.

Priorité:
- ``GET /v1/quests/status?player=...`` pour l'état joueur consolidé,
- ``GET /v1/inventory?player=...`` pour le signal craft/inventaire,
- fallback ``GET /v1/quest-state`` pour compatibilité bots/debug.
"""
from __future__ import annotations

import os
from typing import Any

import httpx
from backend.services.session_summary_export import SESSION_SUMMARY_KEYS, sanitize_session_summary


def _sidecar_base() -> str:
    return (
        os.environ.get("LBG_CORE3_IA_SIDECAR_URL")
        or os.environ.get("LBG_SIDECAR_HTTP")
        or "http://192.168.0.246:8791"
    ).strip().rstrip("/")


def _player_hint(context: dict[str, Any], actor_id: str) -> str:
    for key in ("player_name", "character_name", "core3_player"):
        raw = context.get(key)
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    ss = context.get("session_summary")
    if isinstance(ss, dict):
        note = ss.get("player_note")
        if isinstance(note, str) and note.strip().startswith("player:"):
            return note.strip().split(":", 1)[1].strip()
    # actor_id type prime:client / character:Teome
    if ":" in actor_id:
        tail = actor_id.rsplit(":", 1)[-1].strip()
        if tail and tail not in ("client", "cursor", "pilot"):
            return tail
    return ""


def _latest_accept_for_player(states: list[Any], player: str) -> dict[str, Any] | None:
    pl = player.strip().lower()
    if not pl:
        return None
    latest: dict[str, Any] | None = None
    latest_ts = -1
    for row in states:
        if not isinstance(row, dict):
            continue
        if str(row.get("player") or "").strip().lower() != pl:
            continue
        if str(row.get("type") or "").strip().lower() not in ("accept", "update", "progress"):
            continue
        try:
            ts = int(row.get("ts") or 0)
        except (TypeError, ValueError):
            ts = 0
        if ts >= latest_ts:
            latest_ts = ts
            latest = row
    return latest


def _get_json(path: str, *, timeout_s: float = 2.5) -> dict[str, Any]:
    base = _sidecar_base()
    if not base:
        return {}
    try:
        with httpx.Client(timeout=timeout_s) as client:
            r = client.get(f"{base}{path}")
        if r.status_code != 200:
            return {}
        data = r.json()
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def fetch_quest_states(*, timeout_s: float = 2.5) -> list[Any]:
    data = _get_json("/v1/quest-state", timeout_s=timeout_s)
    states = data.get("quest_states")
    return states if isinstance(states, list) else []


def merge_quest_into_session_summary(
    context: dict[str, Any],
    *,
    actor_id: str = "",
    force: bool = False,
) -> dict[str, Any]:
    """Retourne un nouveau context avec session_summary enrichi (best-effort)."""
    ctx = dict(context)
    raw_ss = ctx.get("session_summary")
    ss: dict[str, Any] = dict(raw_ss) if isinstance(raw_ss, dict) else {}

    has_tracked = bool(str(ss.get("tracked_quest") or "").strip())
    has_snap = bool(str(ss.get("quest_snapshot") or "").strip())
    has_progress = bool(str(ss.get("session_mood") or "").strip())
    if has_tracked and has_snap and has_progress and not force:
        return ctx

    player = _player_hint(ctx, actor_id)
    source = "sidecar:/v1/quest-state"
    qid = ""
    if player:
        status = _get_json(f"/v1/quests/status?player={player}")
        active = status.get("active")
        completed = status.get("completed")
        rewards = status.get("credits")
        active_row = active[0] if isinstance(active, list) and active and isinstance(active[0], dict) else None
        if active_row is not None:
            qid = str(active_row.get("id") or "").strip()
            if (not has_tracked or force) and qid:
                ss["tracked_quest"] = qid[:160]
            if not has_snap or force:
                title = str(active_row.get("title") or qid).strip()
                steps = active_row.get("progress_steps")
                done = 0
                total = 0
                if isinstance(steps, list):
                    total = len([s for s in steps if isinstance(s, dict)])
                    done = len([s for s in steps if isinstance(s, dict) and s.get("done")])
                ss["quest_snapshot"] = f"id={qid} active={title} progress={done}/{total} player={player}"[:160]
            if (not has_progress or force) and isinstance(active_row.get("objective"), str):
                ss["session_mood"] = f"quest:{str(active_row.get('objective') or '').strip()[:148]}"
            if isinstance(rewards, int) or isinstance(rewards, float):
                ss["session_mood"] = f"credits:{int(rewards)}"[:160]
            source = "sidecar:/v1/quests/status"
        elif isinstance(completed, list) and completed:
            qid = str(completed[-1] or "").strip()
            if (not has_tracked or force) and qid:
                ss["tracked_quest"] = qid[:160]
            if not has_snap or force:
                ss["quest_snapshot"] = f"id={qid} status=completed player={player}"[:160]
            source = "sidecar:/v1/quests/status"

        inv = _get_json(f"/v1/inventory?player={player}")
        if inv.get("ok") and (force or not str(ss.get("player_note") or "").strip()):
            count = len(inv.get("inventory") or []) if isinstance(inv.get("inventory"), list) else 0
            ss["player_note"] = f"player:{player} inv:{count}"[:160]
            source = "sidecar:/v1/inventory"

    if not qid:
        states = fetch_quest_states()
        row = _latest_accept_for_player(states, player) if player else None
        if row is None and states:
            for cand in reversed(states):
                if isinstance(cand, dict) and str(cand.get("type") or "").lower() == "accept":
                    row = cand
                    break
        if row is None:
            return ctx
        qid = str(row.get("quest_id") or "").strip()
        if not qid:
            return ctx
        if not has_tracked or force:
            ss["tracked_quest"] = qid[:160]
        if not has_snap or force:
            typ = str(row.get("type") or "accept")
            who = str(row.get("player") or player or "?")
            ss["quest_snapshot"] = f"id={qid} type={typ} player={who}"[:160]
    ss["memory_hint"] = str(ss.get("memory_hint") or "quest_sidecar").strip()[:160]

    cleaned = sanitize_session_summary({k: v for k, v in ss.items() if k in SESSION_SUMMARY_KEYS})
    if cleaned:
        ctx["session_summary"] = cleaned
        ctx["_quest_enrich"] = {
            "source": source,
            "player": player or None,
            "quest_id": qid,
        }
    return ctx
