"""Juge post-tâche (échantillon) — ferme la boucle Miroir sur les runs réels.

Agency A : soft-judge seulement si pas déjà capitalisé en hard-fail ;
rôles défaut étendus (ops, player_ia).
"""

from __future__ import annotations

import json
import os
import random
from typing import Any

from team.models import TeamTask

_LAST_POST_JUDGE: dict[str, Any] = {}

_DEFAULT_ROLES = "qa,pm,ops,dev_godot,dev_game,player_ia"


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
    raw = os.environ.get("LBG_TEAM_POST_JUDGE_ROLES", _DEFAULT_ROLES).strip()
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

    hard_fail_done = bool(result.get("hard_fail_lesson"))
    result_ok = bool(result.get("ok", True))
    # Soft sample : inchangé. Hard-fail déjà capitalisé → on peut encore scorer,
    # mais on n'ajoute pas une 2e leçon clone.
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
        compact = {
            k: result[k]
            for k in list(result.keys())[:12]
            if k not in ("health_checks", "lessons_trace")
        }
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
        "soft_lesson_skipped": False,
    }
    # Capitaliser échecs de qualité soft — pas si hard-fail a déjà écrit
    # (ou si hard-fail est actif et result.ok=False : A.1 est la source de vérité).
    if judged.get("ok") and judged.get("pass") is False:
        skip_soft = hard_fail_done
        if not skip_soft and not result_ok:
            try:
                from team import lessons_learned as _ll

                skip_soft = _ll.hard_fail_enabled()
            except Exception:
                skip_soft = False
        if skip_soft:
            _LAST_POST_JUDGE["soft_lesson_skipped"] = True
        else:
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
