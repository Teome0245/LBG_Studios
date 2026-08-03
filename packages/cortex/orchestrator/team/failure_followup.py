"""Suivi générique après échec Team — ne se contente pas d'effacer le rouge UI.

Opt-in : LBG_TEAM_FAILURE_FOLLOWUP_ENABLED=1 (défaut 1).
Retry même rôle : LBG_TEAM_FAILURE_RETRY=1 (défaut 0 — évite les boucles).
"""

from __future__ import annotations

import os
import time
from typing import Any

from team import store as team_store
from team.models import TeamTask


def followup_enabled() -> bool:
    return os.environ.get("LBG_TEAM_FAILURE_FOLLOWUP_ENABLED", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def retry_enabled() -> bool:
    return os.environ.get("LBG_TEAM_FAILURE_RETRY", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def auto_run_enabled() -> bool:
    return os.environ.get("LBG_TEAM_FAILURE_FOLLOWUP_AUTO_RUN", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def actor_id() -> str:
    return os.environ.get("LBG_TEAM_FAILURE_FOLLOWUP_ACTOR_ID", "system:team_failure_followup").strip()


def _already_handled(task: TeamTask) -> bool:
    ctx = task.context or {}
    if ctx.get("_failure_followup_spawned"):
        return True
    if ctx.get("_qa_followup_spawned") or ctx.get("_qa_followup"):
        return True
    if ctx.get("_godot_followup_spawned") or ctx.get("_m9_followup_spawned"):
        return True
    if ctx.get("_failure_followup") or ctx.get("_failure_retry"):
        return True
    return False


def _summarize(result: dict[str, Any]) -> dict[str, Any]:
    err = result.get("error")
    return {
        "kind": result.get("kind"),
        "ok": result.get("ok"),
        "error": (str(err)[:300] if err else None),
        "keys": sorted(str(k) for k in list(result.keys())[:20]),
    }


def maybe_spawn_after_failure(task: TeamTask) -> list[str]:
    """Crée triage PM (+ retry optionnel) après un failed non déjà suivi."""
    if not followup_enabled():
        return []
    if task.status != "failed":
        return []
    if _already_handled(task):
        return []

    result = task.result if isinstance(task.result, dict) else {}
    parent_ref = {
        "parent_task_id": task.id,
        "parent_trace_id": task.trace_id,
        "parent_role": task.role,
        "failure_summary": _summarize(result),
    }
    created: list[str] = []

    pm_obj = (
        f"Triage échec {task.role} — analyser et proposer correctif/relance "
        f"(parent={task.id}) : {task.objective[:160]}"
    )
    pm = team_store.create_task(
        role="pm",
        objective=pm_obj,
        actor_id=actor_id(),
        priority="high",
        context={**parent_ref, "_failure_followup": True},
    )
    created.append(pm.id)

    if retry_enabled():
        retry = team_store.create_task(
            role=task.role,
            objective=f"Relancer après échec — {task.objective}"[:400],
            actor_id=actor_id(),
            priority="high",
            context={
                **parent_ref,
                "_failure_followup": True,
                "_failure_retry": True,
                **{k: v for k, v in (task.context or {}).items() if not str(k).startswith("_")},
            },
        )
        created.append(retry.id)

    team_store.update_task(
        task.id,
        context_patch={
            "_failure_followup_spawned": True,
            "_failure_followup_task_ids": created,
            "_failure_followup_ts": time.time(),
        },
    )
    try:
        from team import bus_hooks

        bus_hooks.emit_spawned_followups(
            parent_task_id=task.id,
            child_task_ids=created,
            from_agent=bus_hooks.agent_for_role(task.role, context=task.context),
            actor_id=actor_id(),
            verify_summary=f"échec {task.role} — triage spawnés",
            verify_ok=False,
        )
    except Exception:
        pass
    return created


def auto_run_followup_tasks(task_ids: list[str]) -> list[dict[str, object]]:
    if not auto_run_enabled():
        return []
    from team import roles as team_roles

    out: list[dict[str, object]] = []
    for tid in task_ids:
        task = team_store.get_task(tid)
        if task is None or task.status != "queued":
            continue
        # PM L1 auto ; retry seulement si LBG_TEAM_FAILURE_RETRY_AUTO_RUN=1
        if task.role != "pm":
            if not (
                task.context.get("_failure_retry")
                and os.environ.get("LBG_TEAM_FAILURE_RETRY_AUTO_RUN", "0").strip().lower()
                in ("1", "true", "yes", "on")
            ):
                continue
        ran = team_roles.run_task(tid)
        if ran is not None:
            out.append({"task_id": tid, "role": ran.role, "status": ran.status})
    return out
