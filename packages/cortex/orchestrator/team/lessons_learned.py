"""Mémoire épisodique réflexive — leçons structurées (P0 + Agency A).

Registre versionné sous ``packages/cortex/knowledge/lessons_learned.json``.
Injection : slice dans ``task.context["lessons_slice"]`` au ``run_task``.
Phase A : hard-fail append, dédup fenêtre, lessons_trace.
"""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any

# Kinds meta — pas de leçon hard-fail / bruit (aligné post_judge).
HARD_FAIL_SKIP_KINDS = frozenset(
    {
        "agent_mutator",
        "agent_mutator_review",
        "feature_proposer",
        "feature_proposal_review",
        "evolution_sprint_workflow",
        "outcome_judge",
    }
)


def lessons_enabled() -> bool:
    return os.environ.get("LBG_TEAM_LESSONS_ENABLED", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def hard_fail_enabled() -> bool:
    return os.environ.get("LBG_TEAM_LESSONS_HARD_FAIL", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def dedup_hours() -> int:
    try:
        return max(0, min(int(os.environ.get("LBG_TEAM_LESSONS_DEDUP_HOURS", "48")), 720))
    except ValueError:
        return 48


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


def last_lesson_id() -> str | None:
    items = [x for x in (load_lessons_doc().get("lessons") or []) if isinstance(x, dict)]
    if not items:
        return None
    lid = str(items[-1].get("id") or "").strip()
    return lid or None


def _normalize_dedup_key(*, agent_role: str, pattern: str, do_not_repeat: str) -> str:
    blob = f"{(agent_role or '').strip().lower()}|{(pattern or '').strip().lower()}|{(do_not_repeat or '').strip().lower()}"
    return re.sub(r"\s+", " ", blob).strip()


def _lesson_seen_ts(lesson: dict[str, Any]) -> float:
    raw = lesson.get("last_seen_ts")
    if isinstance(raw, (int, float)):
        return float(raw)
    date_s = str(lesson.get("date") or "").strip()
    if date_s:
        try:
            return time.mktime(time.strptime(date_s, "%Y-%m-%d"))
        except ValueError:
            pass
    return 0.0


def _persist_doc(doc: dict[str, Any]) -> None:
    path = lessons_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


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
    role = (agent_role or "pm").strip() or "pm"
    dnr = (do_not_repeat or "").strip()[:400]
    key = _normalize_dedup_key(agent_role=role, pattern=text[:1000], do_not_repeat=dnr)
    now = time.time()
    window_s = float(dedup_hours()) * 3600.0

    path = lessons_path()
    doc = load_lessons_doc()
    lessons = [x for x in (doc.get("lessons") or []) if isinstance(x, dict)]

    if window_s > 0:
        for existing in reversed(lessons):
            ek = _normalize_dedup_key(
                agent_role=str(existing.get("agent_role") or ""),
                pattern=str(existing.get("pattern") or ""),
                do_not_repeat=str(existing.get("do_not_repeat") or ""),
            )
            if ek != key:
                continue
            age = now - _lesson_seen_ts(existing)
            if age <= window_s or _lesson_seen_ts(existing) <= 0:
                # Même clé dans la fenêtre (ou date seule) → bump
                existing["last_seen_ts"] = now
                existing["last_seen"] = time.strftime("%Y-%m-%d")
                try:
                    existing["hit_count"] = int(existing.get("hit_count") or 1) + 1
                except (TypeError, ValueError):
                    existing["hit_count"] = 2
                merged_refs = [str(r)[:120] for r in (existing.get("refs") or []) if str(r).strip()]
                for r in refs or []:
                    rs = str(r).strip()[:120]
                    if rs and rs not in merged_refs:
                        merged_refs.append(rs)
                existing["refs"] = merged_refs[:12]
                if context and not existing.get("context"):
                    existing["context"] = (context or "").strip()[:400]
                doc["lessons"] = lessons
                doc["schema_version"] = int(doc.get("schema_version") or 1)
                _persist_doc(doc)
                out = dict(existing)
                out["deduped"] = True
                try:
                    from services import self_state as svc_self

                    svc_self.note_lesson_append(
                        lesson_id=str(out.get("id") or ""),
                        lessons_count=len(lessons),
                    )
                except Exception:
                    pass
                return out

    entry: dict[str, Any] = {
        "id": (lesson_id or "").strip() or f"lesson_{uuid.uuid4().hex[:10]}",
        "date": time.strftime("%Y-%m-%d"),
        "agent_role": role,
        "context": (context or "").strip()[:400],
        "failure_or_success": (failure_or_success or "failure").strip()[:40],
        "pattern": text[:1000],
        "do_not_repeat": dnr,
        "refs": [str(r)[:120] for r in (refs or [])[:8] if str(r).strip()],
        "hit_count": 1,
        "last_seen_ts": now,
        "last_seen": time.strftime("%Y-%m-%d"),
        "deduped": False,
    }
    lessons.append({k: v for k, v in entry.items() if k != "deduped"})
    doc["schema_version"] = int(doc.get("schema_version") or 1)
    doc["lessons"] = lessons
    _persist_doc(doc)
    try:
        from services import self_state as svc_self

        svc_self.note_lesson_append(
            lesson_id=str(entry.get("id") or ""),
            lessons_count=len(lessons),
        )
    except Exception:
        pass
    return entry


def record_hard_fail_lesson(
    *,
    task_id: str,
    role: str,
    objective: str = "",
    result: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Capitalise un échec dur (result.ok=False). Retourne l'entrée ou None si skip."""
    if not lessons_enabled() or not hard_fail_enabled():
        return None
    res = result if isinstance(result, dict) else {}
    kind = str(res.get("kind") or "").strip()
    if kind in HARD_FAIL_SKIP_KINDS:
        return None
    role_n = (role or "pm").strip() or "pm"
    err = res.get("error") or res.get("human_summary") or res.get("detail") or "task failed"
    err_s = str(err).strip()[:160]
    obj = (objective or "").strip()[:100]
    label = kind or role_n
    pattern = f"Hard-fail {label}: {obj} — {err_s}".strip(" —")
    do_not_repeat = f"Échec silencieux sans leçon ({label})"
    try:
        return append_lesson(
            agent_role=role_n,
            pattern=pattern,
            context="hard_fail",
            failure_or_success="failure",
            do_not_repeat=do_not_repeat,
            refs=[task_id, "hard_fail"] + ([kind] if kind else []),
        )
    except Exception:
        return None


def lessons_trace_from_slice(lessons_slice: list[Any] | None) -> dict[str, Any]:
    """Trace compacte pour result.lessons_trace (Agency A.6)."""
    ids: list[str] = []
    preview: list[str] = []
    if isinstance(lessons_slice, list):
        for les in lessons_slice[:8]:
            if not isinstance(les, dict):
                continue
            lid = str(les.get("id") or "").strip()
            if lid:
                ids.append(lid)
            pat = str(les.get("pattern") or "").strip()
            if pat:
                preview.append(pat[:80])
    return {
        "injected_ids": ids,
        "patterns_preview": preview,
        "injected_count": len(ids),
    }


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
        "hard_fail": hard_fail_enabled(),
        "dedup_hours": dedup_hours(),
        "path": str(path),
        "count": lessons_count(),
        "last_lesson_id": last_lesson_id(),
        "exists": path.is_file(),
    }
