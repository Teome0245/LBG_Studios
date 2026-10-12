"""Mémoire relations joueur ↔ PNJ (C2) — lecture stub + phrase memory_hint / world_hint.

Schéma : ``packages/cortex/content/world/relation_memory_schema.json``.
Stub d’exemple : ``relation_memory_example.json`` (hub Lost Heaven, Jax).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_entries_cache: list[dict[str, Any]] | None = None

_KIND_PREFIX = {
    "debt": "Dette",
    "met": "Rencontre",
    "gift": "Cadeau",
    "quest": "Quête",
}


def reset_cache() -> None:
    global _entries_cache
    _entries_cache = None


def content_dir() -> Path:
    raw = os.environ.get("LBG_WORLD_CONTENT_DIR", "").strip()
    if raw:
        return Path(raw)
    # lbg_agents/relation_memory.py -> parents[3] = packages/cortex
    return Path(__file__).resolve().parents[3] / "content" / "world"


def default_memory_path() -> Path:
    raw = os.environ.get("LBG_RELATION_MEMORY_PATH", "").strip()
    if raw:
        return Path(raw)
    return content_dir() / "relation_memory_example.json"


def load_entries(*, path: Path | None = None) -> list[dict[str, Any]]:
    """Charge les entrées relation (fichier stub ou path explicite)."""
    global _entries_cache
    if path is None and _entries_cache is not None:
        return _entries_cache
    p = path if path is not None else default_memory_path()
    out: list[dict[str, Any]] = []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        if path is None:
            _entries_cache = out
        return out
    rows = data.get("entries") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        if path is None:
            _entries_cache = out
        return out
    for row in rows:
        if not isinstance(row, dict):
            continue
        npc = row.get("npc_id")
        note = row.get("note")
        kind = row.get("kind")
        if not (isinstance(npc, str) and npc.strip()):
            continue
        if not (isinstance(note, str) and note.strip()):
            continue
        if not (isinstance(kind, str) and kind.strip()):
            continue
        out.append(row)
    if path is None:
        _entries_cache = out
    return out


def _player_matches(entry_player: str, player_id: str | None) -> bool:
    if not player_id or not str(player_id).strip():
        return True
    needle = str(player_id).strip().lower()
    hay = entry_player.strip().lower()
    if hay == needle:
        return True
    # actor_id style « prime:Lia » / « player:Lia »
    return hay in needle or needle.endswith(":" + hay) or needle.endswith("/" + hay)


def entries_for_npc(
    npc_id: str,
    *,
    player_id: str | None = None,
    entries: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    rid = (npc_id or "").strip()
    if not rid:
        return []
    rows = entries if entries is not None else load_entries()
    out: list[dict[str, Any]] = []
    for row in rows:
        if str(row.get("npc_id", "")).strip() != rid:
            continue
        ep = row.get("player_id")
        if isinstance(ep, str) and ep.strip() and not _player_matches(ep, player_id):
            continue
        out.append(row)
    # Plus récent d’abord si ts présent
    def _ts_key(r: dict[str, Any]) -> str:
        t = r.get("ts")
        return t if isinstance(t, str) else ""

    out.sort(key=_ts_key, reverse=True)
    return out


def memory_hint_for(
    npc_id: str,
    *,
    player_id: str | None = None,
    entries: list[dict[str, Any]] | None = None,
    max_len: int = 160,
    max_notes: int = 2,
) -> str | None:
    """Phrase courte pour ``session_summary.memory_hint`` (1 PNJ hub)."""
    rows = entries_for_npc(npc_id, player_id=player_id, entries=entries)
    if not rows:
        return None
    parts: list[str] = []
    for row in rows[: max(1, max_notes)]:
        note = str(row.get("note", "")).strip().replace("\n", " ")
        if not note:
            continue
        kind = str(row.get("kind", "")).strip()
        prefix = _KIND_PREFIX.get(kind, kind)
        if prefix:
            parts.append(f"{prefix}: {note}")
        else:
            parts.append(note)
    if not parts:
        return None
    text = " · ".join(parts)
    if len(text) > max_len:
        text = text[: max_len - 1] + "…"
    return text


def world_hint_injection(
    npc_id: str,
    *,
    player_id: str | None = None,
    entries: list[dict[str, Any]] | None = None,
    max_len: int = 200,
) -> str | None:
    """Fragment à concaténer dans ``context.world_hint`` (faits relationnels)."""
    hint = memory_hint_for(
        npc_id,
        player_id=player_id,
        entries=entries,
        max_len=max_len,
        max_notes=1,
    )
    if not hint:
        return None
    return f"Mémoire relation (C2) : {hint}"


def merge_into_context(
    context: dict[str, Any],
    *,
    actor_id: str | None = None,
    npc_id: str | None = None,
) -> dict[str, Any]:
    """Injecte ``memory_hint`` + append ``world_hint`` si absents / incomplets.

    Mutates ``context`` in place and returns a small meta dict for HTTP.
    """
    meta: dict[str, Any] = {"applied": False}
    if not isinstance(context, dict):
        return meta
    rid = npc_id
    if not (isinstance(rid, str) and rid.strip()):
        raw = context.get("world_npc_id")
        rid = raw.strip() if isinstance(raw, str) else ""
    if not rid:
        return meta
    pid = actor_id
    if not (isinstance(pid, str) and pid.strip()):
        inv = context.get("_invoke_actor_id")
        pid = inv if isinstance(inv, str) else None
    hint = memory_hint_for(rid, player_id=pid if isinstance(pid, str) else None)
    if not hint:
        return meta
    ss = context.get("session_summary")
    if not isinstance(ss, dict):
        ss = {}
        context["session_summary"] = ss
    existing = ss.get("memory_hint")
    if not (isinstance(existing, str) and existing.strip()):
        ss["memory_hint"] = hint
        meta["memory_hint"] = hint
        meta["applied"] = True
    inj = world_hint_injection(rid, player_id=pid if isinstance(pid, str) else None)
    if inj:
        wh = context.get("world_hint")
        base = wh.strip() if isinstance(wh, str) else ""
        if inj not in base:
            context["world_hint"] = f"{base} {inj}".strip() if base else inj
            meta["world_hint_injected"] = True
            meta["applied"] = True
    meta["source"] = "relation_memory"
    return meta
