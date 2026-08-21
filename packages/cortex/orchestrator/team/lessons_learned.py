"""Mémoire épisodique réflexive — leçons structurées (P0 plan_meta_autonomie_l3).

Registre versionné sous ``packages/cortex/knowledge/lessons_learned.json``.
Injection stub : slice dans ``task.context["lessons_slice"]`` au ``run_task``.
"""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any


def lessons_enabled() -> bool:
    return os.environ.get("LBG_TEAM_LESSONS_ENABLED", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def lessons_path() -> Path:
    raw = os.environ.get("LBG_TEAM_LESSONS_PATH", "").strip()
    if raw:
        return Path(raw)
    # packages/cortex/orchestrator/team/ → packages/cortex/knowledge/
    return Path(__file__).resolve().parents[2] / "knowledge" / "lessons_learned.json"


def _empty_doc() -> dict[str, Any]:
    return {"schema_version": 1, "lessons": []}


def load_lessons_doc() -> dict[str, Any]:
    path = lessons_path()
    if not path.is_file():
        return _empty_doc()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_doc()
    if not isinstance(data, dict):
        return _empty_doc()
    lessons = data.get("lessons")
    if not isinstance(lessons, list):
        data["lessons"] = []
    return data


def list_lessons(*, role: str = "", limit: int = 50) -> list[dict[str, Any]]:
    doc = load_lessons_doc()
    items = [x for x in doc.get("lessons") or [] if isinstance(x, dict)]
    role_n = (role or "").strip().lower()
    if role_n:
        # Priorité rôle, mais on ne droppe pas les leçons transverses / autres rôles.
        def _rank_role(lesson: dict[str, Any]) -> int:
            ar = str(lesson.get("agent_role") or "").strip().lower()
            if ar in ("", "any", "*", "pm"):
                return 1
            if ar == role_n or role_n in ar:
                return 0
            return 2

        items = sorted(items, key=_rank_role)
    cap = max(1, min(int(limit), 200))
    return items[:cap]


def lessons_count() -> int:
    return len([x for x in (load_lessons_doc().get("lessons") or []) if isinstance(x, dict)])


def append_lesson(
    *,
    agent_role: str,
    pattern: str,
    context: str = "",
    failure_or_success: str = "failure",
    do_not_repeat: str = "",
    refs: list[str] | None = None,
    lesson_id: str = "",
) -> dict[str, Any]:
    if not lessons_enabled():
        raise RuntimeError("leçons désactivées (LBG_TEAM_LESSONS_ENABLED=0)")
    text = (pattern or "").strip()
    if not text:
        raise ValueError("pattern vide")
    entry: dict[str, Any] = {
        "id": (lesson_id or "").strip() or f"lesson_{uuid.uuid4().hex[:10]}",
        "date": time.strftime("%Y-%m-%d"),
        "agent_role": (agent_role or "pm").strip() or "pm",
        "context": (context or "").strip()[:400],
        "failure_or_success": (failure_or_success or "failure").strip()[:40],
        "pattern": text[:1000],
        "do_not_repeat": (do_not_repeat or "").strip()[:400],
        "refs": [str(r)[:120] for r in (refs or [])[:8] if str(r).strip()],
    }
    path = lessons_path()
    doc = load_lessons_doc()
    lessons = [x for x in (doc.get("lessons") or []) if isinstance(x, dict)]
    lessons.append(entry)
    doc["schema_version"] = int(doc.get("schema_version") or 1)
    doc["lessons"] = lessons
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    return entry


def lessons_slice_for_task(*, role: str, objective: str = "", limit: int | None = None) -> list[dict[str, str]]:
    """Sous-ensemble compact pour ``context["lessons_slice"]``."""
    if not lessons_enabled():
        return []
    if limit is None:
        try:
            limit = int(os.environ.get("LBG_TEAM_LESSONS_INJECT_LIMIT", "4"))
        except ValueError:
            limit = 4
    cap = max(0, min(int(limit), 12))
    if cap == 0:
        return []

    items = list_lessons(role=role, limit=80)
    obj = (objective or "").lower()
    tokens = {t for t in re.split(r"[^\w]+", obj) if len(t) >= 4}
    role_n = (role or "").strip().lower()

    def _score(lesson: dict[str, Any]) -> tuple[int, int]:
        blob = " ".join(
            str(lesson.get(k) or "")
            for k in ("pattern", "context", "do_not_repeat", "agent_role")
        ).lower()
        tok_hit = sum(1 for t in tokens if t in blob)
        ar = str(lesson.get("agent_role") or "").strip().lower()
        role_boost = 2 if ar == role_n else (1 if ar in ("", "any", "*", "pm") else 0)
        return (tok_hit + role_boost, tok_hit)

    ranked = sorted(items, key=_score, reverse=True)
    out: list[dict[str, str]] = []
    for lesson in ranked[:cap]:
        out.append(
            {
                "id": str(lesson.get("id") or ""),
                "agent_role": str(lesson.get("agent_role") or ""),
                "pattern": str(lesson.get("pattern") or "")[:400],
                "do_not_repeat": str(lesson.get("do_not_repeat") or "")[:200],
            }
        )
    return out


def meta_status() -> dict[str, object]:
    path = lessons_path()
    return {
        "enabled": lessons_enabled(),
        "path": str(path),
        "count": lessons_count(),
        "exists": path.is_file(),
    }
