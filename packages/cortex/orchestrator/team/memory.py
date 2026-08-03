"""Mémoire équipe Team — JSONL append-only (ADR 0019)."""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

from team.plan_schema import TeamMemoryEntry, truncate_text


def memory_enabled() -> bool:
    return os.environ.get("LBG_TEAM_MEMORY_ENABLED", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def memory_path() -> Path:
    raw = os.environ.get("LBG_TEAM_MEMORY_PATH", "").strip()
    if raw:
        return Path(raw)
    return Path("/var/lib/lbg-ia-mmo/team_memory.jsonl")


def _ensure_parent(path: Path) -> None:
    parent = path.parent
    if parent and str(parent) not in (".", ""):
        parent.mkdir(parents=True, exist_ok=True)


def append_learning(
    *,
    agent_id: str,
    summary: str,
    kind: str = "learning",
    tags: list[str] | None = None,
    task_id: str = "",
    meta: dict[str, object] | None = None,
) -> TeamMemoryEntry:
    if not memory_enabled():
        raise RuntimeError("mémoire équipe désactivée (LBG_TEAM_MEMORY_ENABLED=0)")
    aid = truncate_text(agent_id or "", 64)
    if not aid:
        raise ValueError("agent_id vide")
    text = truncate_text(summary or "", 1000)
    if not text:
        raise ValueError("summary vide")
    entry = TeamMemoryEntry(
        id=str(uuid.uuid4()),
        agent_id=aid,
        kind=truncate_text(kind or "learning", 40) or "learning",
        summary=text,
        tags=[truncate_text(str(t), 40) for t in (tags or [])[:12] if str(t).strip()],
        task_id=(task_id or "").strip(),
        created_ts=time.time(),
        meta=_sanitize_meta(meta),
    )
    path = memory_path()
    _ensure_parent(path)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
    return entry


def _sanitize_meta(raw: dict[str, object] | None) -> dict[str, object]:
    if not raw:
        return {}
    out: dict[str, object] = {}
    for i, (k, v) in enumerate(raw.items()):
        if i >= 16:
            break
        key = truncate_text(str(k), 40)
        if isinstance(v, str):
            out[key] = truncate_text(v, 400)
        elif isinstance(v, (int, float, bool)) or v is None:
            out[key] = v
    return out


def _parse_line(line: str) -> TeamMemoryEntry | None:
    line = line.strip()
    if not line:
        return None
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    try:
        return TeamMemoryEntry(
            id=str(data.get("id") or ""),
            agent_id=str(data.get("agent_id") or ""),
            kind=str(data.get("kind") or "learning"),
            summary=str(data.get("summary") or ""),
            tags=[str(t) for t in (data.get("tags") or []) if str(t).strip()][:12],
            task_id=str(data.get("task_id") or ""),
            created_ts=float(data.get("created_ts") or 0.0),
            meta=data.get("meta") if isinstance(data.get("meta"), dict) else {},
        )
    except (TypeError, ValueError):
        return None


def list_learnings(
    *,
    agent_id: str | None = None,
    kind: str | None = None,
    tag: str | None = None,
    limit: int = 50,
) -> list[TeamMemoryEntry]:
    path = memory_path()
    if not path.is_file():
        return []
    cap = max(1, min(int(limit), 200))
    # Lecture depuis la fin : on charge un plafond de lignes récentes.
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out: list[TeamMemoryEntry] = []
    for line in reversed(lines):
        entry = _parse_line(line)
        if entry is None or not entry.summary:
            continue
        if agent_id and entry.agent_id != agent_id:
            continue
        if kind and entry.kind != kind:
            continue
        if tag and tag not in entry.tags:
            continue
        out.append(entry)
        if len(out) >= cap:
            break
    return out


def top_learnings_for_plan(*, limit: int = 8) -> list[dict[str, Any]]:
    """Sous-ensemble compact pour injection prompt plan (Vague 4)."""
    entries = list_learnings(limit=limit)
    return [
        {
            "agent_id": e.agent_id,
            "kind": e.kind,
            "summary": e.summary,
            "tags": e.tags,
        }
        for e in entries
    ]


def prune_learnings(
    *,
    max_entries: int | None = None,
    max_age_days: float | None = None,
) -> dict[str, Any]:
    """Rétention mémoire : garde les N plus récents et/ou écarte les trop vieux.

    Env :
    - LBG_TEAM_MEMORY_MAX_ENTRIES (défaut 500)
    - LBG_TEAM_MEMORY_MAX_AGE_DAYS (défaut 30 ; 0 = pas de filtre âge)
    """
    if not memory_enabled():
        return {"ok": False, "error": "mémoire désactivée"}
    path = memory_path()
    if not path.is_file():
        return {"ok": True, "before": 0, "after": 0, "removed": 0, "path": str(path)}

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return {"ok": False, "error": str(exc)}

    entries: list[TeamMemoryEntry] = []
    for line in lines:
        e = _parse_line(line)
        if e is not None and e.summary:
            entries.append(e)

    before = len(entries)
    cap = max_entries
    if cap is None:
        try:
            cap = int(os.environ.get("LBG_TEAM_MEMORY_MAX_ENTRIES", "500"))
        except ValueError:
            cap = 500
    cap = max(1, min(int(cap), 5000))

    age_days = max_age_days
    if age_days is None:
        try:
            age_days = float(os.environ.get("LBG_TEAM_MEMORY_MAX_AGE_DAYS", "30"))
        except ValueError:
            age_days = 30.0

    now = time.time()
    if age_days and age_days > 0:
        cutoff = now - (float(age_days) * 86400.0)
        entries = [e for e in entries if float(e.created_ts or 0) >= cutoff]

    # plus récents en dernier dans le fichier
    entries.sort(key=lambda e: float(e.created_ts or 0))
    if len(entries) > cap:
        entries = entries[-cap:]

    _ensure_parent(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for e in entries:
            fh.write(json.dumps(e.to_dict(), ensure_ascii=False) + "\n")
    tmp.replace(path)
    after = len(entries)
    return {
        "ok": True,
        "before": before,
        "after": after,
        "removed": max(0, before - after),
        "max_entries": cap,
        "max_age_days": age_days,
        "path": str(path),
    }
