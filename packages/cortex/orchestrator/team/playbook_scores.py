"""A3 — scoring playbooks coffee-fill (mémoire + historique tâches).

Score ∈ [0, 1] : taux de succès récent du utility_key, boost mémoire lyra.
Utilisé par Campus Conductor pour ordonner / filtrer les coffee proposals.
"""

from __future__ import annotations

import os
import time
from typing import Any


def scoring_enabled() -> bool:
    return os.environ.get("LBG_TEAM_PLAYBOOK_SCORING", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def score_window_s() -> float:
    try:
        return max(3600.0, float(os.environ.get("LBG_TEAM_PLAYBOOK_SCORE_WINDOW_S", "604800")))
    except ValueError:
        return 604800.0


def min_samples() -> int:
    try:
        return max(0, int(os.environ.get("LBG_TEAM_PLAYBOOK_SCORE_MIN_SAMPLES", "2")))
    except ValueError:
        return 2


def min_score_to_spawn() -> float:
    """Sous ce score (si assez d'échantillons) → skip coffee fill pour ce playbook."""
    try:
        return max(0.0, min(1.0, float(os.environ.get("LBG_TEAM_PLAYBOOK_SCORE_MIN", "0.25"))))
    except ValueError:
        return 0.25


def prior_score() -> float:
    """Score neutre sans historique (exploration)."""
    try:
        return max(0.0, min(1.0, float(os.environ.get("LBG_TEAM_PLAYBOOK_SCORE_PRIOR", "0.55"))))
    except ValueError:
        return 0.55


def _task_utility_key(task: Any) -> str:
    ctx = getattr(task, "context", None) or {}
    if isinstance(ctx, dict):
        key = str(ctx.get("utility_key") or "").strip()
        if key:
            return key
    res = getattr(task, "result", None)
    if isinstance(res, dict):
        key = str(res.get("utility_key") or "").strip()
        if key:
            return key
        kind = str(res.get("kind") or "").strip()
        if kind:
            return kind
    return ""


def _task_ok(task: Any) -> bool | None:
    status = str(getattr(task, "status", "") or "")
    res = getattr(task, "result", None)
    if isinstance(res, dict) and "ok" in res:
        return bool(res.get("ok"))
    if status == "done":
        return True
    if status in ("failed", "cancelled", "closed_failed"):
        return False
    return None


def score_utility_key(utility_key: str, *, role: str = "") -> dict[str, Any]:
    """Calcule un score pour un playbook coffee (utility_key)."""
    key = (utility_key or "").strip()
    if not key:
        return {"utility_key": key, "score": prior_score(), "n": 0, "why": "empty_key", "eligible": True}

    if not scoring_enabled():
        return {"utility_key": key, "score": prior_score(), "n": 0, "why": "scoring_disabled", "eligible": True}

    from team import store as team_store

    window = score_window_s()
    now = time.time()
    successes = 0
    failures = 0
    samples: list[dict[str, Any]] = []

    # Tâches done/failed récentes du rôle (ou toutes si role vide)
    statuses = ("done", "failed")
    for status in statuses:
        try:
            tasks = team_store.list_tasks(role=role or None, status=status, limit=80)
        except Exception:
            tasks = []
        for t in tasks:
            age = now - float(getattr(t, "updated_ts", 0) or getattr(t, "created_ts", 0) or 0)
            if age > window:
                continue
            uk = _task_utility_key(t)
            if uk != key:
                continue
            ok = _task_ok(t)
            if ok is None:
                continue
            if ok:
                successes += 1
            else:
                failures += 1
            samples.append({"task_id": getattr(t, "id", ""), "ok": ok, "age_s": int(age)})

    n = successes + failures
    if n == 0:
        mem_boost = _memory_boost(key)
        score = min(1.0, prior_score() + mem_boost)
        return {
            "utility_key": key,
            "score": round(score, 3),
            "n": 0,
            "successes": 0,
            "failures": 0,
            "why": "prior" + (f"+mem:{mem_boost:+.2f}" if mem_boost else ""),
            "eligible": True,
            "memory_boost": mem_boost,
        }

    rate = successes / float(n)
    mem_boost = _memory_boost(key)
    # Bayes léger : tirer vers prior si peu d'échantillons
    alpha = min(1.0, n / max(1.0, float(min_samples() * 2)))
    score = (1.0 - alpha) * prior_score() + alpha * rate + mem_boost
    score = max(0.0, min(1.0, score))

    eligible = True
    why = f"rate={rate:.2f} n={n}"
    if n >= min_samples() and score < min_score_to_spawn():
        eligible = False
        why += f" below_min={min_score_to_spawn()}"

    return {
        "utility_key": key,
        "score": round(score, 3),
        "n": n,
        "successes": successes,
        "failures": failures,
        "why": why,
        "eligible": eligible,
        "memory_boost": mem_boost,
        "samples_tail": samples[:5],
    }


def _memory_boost(utility_key: str) -> float:
    """Petit boost/pénalité depuis learnings coffee_fill tagués."""
    try:
        from team import memory as team_memory

        if not team_memory.memory_enabled():
            return 0.0
        entries = team_memory.list_learnings(kind="coffee_fill", limit=40)
    except Exception:
        return 0.0
    now = time.time()
    window = score_window_s()
    up = 0
    down = 0
    for e in entries:
        if now - float(e.created_ts or 0) > window:
            continue
        tags = e.tags or []
        meta = e.meta if isinstance(e.meta, dict) else {}
        if utility_key not in tags and meta.get("utility_key") != utility_key:
            continue
        if "ok" in tags or meta.get("ok") is True:
            up += 1
        elif "fail" in tags or meta.get("ok") is False:
            down += 1
    if up == 0 and down == 0:
        return 0.0
    return max(-0.15, min(0.15, 0.05 * (up - down)))


def record_coffee_outcome(
    *,
    utility_key: str,
    ok: bool,
    role: str = "",
    task_id: str = "",
    agent_id: str = "lyra",
) -> None:
    """Écrit un learning coffee_fill pour A3 (best-effort)."""
    key = (utility_key or "").strip()
    if not key or not scoring_enabled():
        return
    try:
        from team import memory as team_memory

        if not team_memory.memory_enabled():
            return
        team_memory.append_learning(
            agent_id=agent_id or "lyra",
            summary=f"Coffee fill {'ok' if ok else 'fail'} — {key}" + (f" ({role})" if role else ""),
            kind="coffee_fill",
            tags=["campus", "coffee", key, "ok" if ok else "fail"],
            task_id=task_id or "",
            meta={"utility_key": key, "ok": ok, "role": role},
        )
    except Exception:
        return


def rank_playbooks(playbooks: list[dict[str, Any]]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Retourne [(playbook, score_info)] triés score desc, éligibles d'abord."""
    ranked: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for pb in playbooks:
        uk = str(pb.get("utility_key") or pb.get("role") or "")
        role = str(pb.get("role") or "")
        info = score_utility_key(uk, role=role)
        ranked.append((pb, info))
    ranked.sort(key=lambda pair: (1 if pair[1].get("eligible") else 0, float(pair[1].get("score") or 0)), reverse=True)
    return ranked
