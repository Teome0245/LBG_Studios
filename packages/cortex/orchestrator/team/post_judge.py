"""Juge post-tâche (échantillon) — ferme la boucle Miroir sur les runs réels."""

from __future__ import annotations

import json
import os
import random
from typing import Any

from team.models import TeamTask

_LAST_POST_JUDGE: dict[str, Any] = {}


def post_judge_enabled() -> bool:
    return os.environ.get("LBG_TEAM_POST_JUDGE", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def post_judge_sample_rate() -> float:
    try:
        return max(0.0, min(1.0, float(os.environ.get("LBG_TEAM_POST_JUDGE_SAMPLE", "0.35"))))
    except ValueError:
        return 0.35


def post_judge_roles() -> set[str]:
    raw = os.environ.get("LBG_TEAM_POST_JUDGE_ROLES", "qa,pm,dev_godot,dev_game").strip()
    if not raw:
        return {"qa", "pm"}
    return {p.strip() for p in raw.split(",") if p.strip()}


def last_post_judge_trace() -> dict[str, Any]:
    return dict(_LAST_POST_JUDGE) if _LAST_POST_JUDGE else {}


def maybe_judge_task_outcome(task: TeamTask, result: dict[str, object]) -> dict[str, Any] | None:
    """Évalue une fraction des tâches clôturées ; retourne le dict judge ou None."""
    if not post_judge_enabled():
        return None
    # Ne pas juger les meta-workflows (évite récursion / bruit).
    kind = str(result.get("kind") or "")
    if kind in (
        "agent_mutator",
        "agent_mutator_review",
        "feature_proposer",
        "feature_proposal_review",
        "evolution_sprint_workflow",
        "outcome_judge",
    ):
        return None
    role = str(task.role or "")
    if role not in post_judge_roles():
        return None
    rate = post_judge_sample_rate()
    if rate <= 0:
        return None
    if rate < 1.0 and random.random() > rate:
        return None

    artifacts: list[str] = [
        f"role={role}",
        f"objective={task.objective or ''}",
        f"status_result_ok={result.get('ok')}",
        f"human_summary={result.get('human_summary') or ''}",
    ]
    # Slice compact du résultat
    try:
        compact = {k: result[k] for k in list(result.keys())[:12] if k not in ("health_checks",)}
        artifacts.append(json.dumps(compact, ensure_ascii=False)[:1800])
    except Exception:
        artifacts.append(str(result)[:800])

    # Leçons déjà injectées → keywords soft
    lessons = []
    if isinstance(task.context, dict):
        lessons = task.context.get("lessons_slice") or []
    expected: list[str] = []
    if isinstance(lessons, list):
        for les in lessons[:3]:
            if isinstance(les, dict) and les.get("do_not_repeat"):
                expected.append(str(les["do_not_repeat"])[:40])

    from team import outcome_judge

    judged = outcome_judge.judge_outcome(
        task_id=task.id,
        artifacts=artifacts,
        expected_keywords=expected,
        complete_fn=lambda **kwargs: {"ok": False, "skipped": True},  # post-judge déterministe
    )
    global _LAST_POST_JUDGE
    _LAST_POST_JUDGE = {
        "task_id": task.id,
        "role": role,
        "score": judged.get("score"),
        "pass": judged.get("pass"),
        "kind": kind,
    }
    # Capitaliser échecs de qualité
    if judged.get("ok") and judged.get("pass") is False:
        try:
            from team import lessons_learned

            if lessons_learned.lessons_enabled():
                lessons_learned.append_lesson(
                    agent_role=role,
                    pattern=(
                        f"Post-judge faible (score={judged.get('score')}) sur "
                        f"{kind or role}: {(task.objective or '')[:120]}"
                    ),
                    context="post_judge",
                    failure_or_success="failure",
                    do_not_repeat="Ignorer un score judge bas sans follow-up",
                    refs=[task.id, "outcome_judge"],
                )
        except Exception:
            pass
    return judged
