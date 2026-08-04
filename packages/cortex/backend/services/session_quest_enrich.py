"""Enrichit session_summary depuis sidecar Prime ``GET /v1/quest-state`` (Rang2 §5 MVP).

Merge autoritatif borné : serveur prime sur ``tracked_quest`` / ``quest_snapshot``
si le client ne les a pas (ou si ``force``).
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


def fetch_quest_states(*, timeout_s: float = 2.5) -> list[Any]:
    base = _sidecar_base()
    if not base:
        return []
    try:
        with httpx.Client(timeout=timeout_s) as client:
            r = client.get(f"{base}/v1/quest-state")
        if r.status_code != 200:
            return []
        data = r.json()
    except Exception:
        return []
    if not isinstance(data, dict):
        return []
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
    if has_tracked and has_snap and not force:
        return ctx

    player = _player_hint(ctx, actor_id)
    states = fetch_quest_states()
    row = _latest_accept_for_player(states, player) if player else None
    if row is None and states:
        # Pas de match joueur : prendre le dernier accept global (debug / bots)
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
            "source": "sidecar:/v1/quest-state",
            "player": player or None,
            "quest_id": qid,
        }
    return ctx
