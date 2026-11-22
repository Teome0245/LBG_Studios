"""Suivi générique après échec Team avec boucle de contrôle et relance sécurisée.

Opt-in : LBG_TEAM_FAILURE_FOLLOWUP_ENABLED=1 (défaut 1).
Retry même rôle : LBG_TEAM_FAILURE_RETRY=1 (défaut 1).
Auto-run retry : LBG_TEAM_FAILURE_RETRY_AUTO_RUN=1 (défaut 1).
Plafond relances : LBG_TEAM_FAILURE_MAX_RETRIES=2 (défaut 2).
"""

from __future__ import annotations

import os
import re
import socket
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
    return os.environ.get("LBG_TEAM_FAILURE_RETRY", "1").strip().lower() in (
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


def retry_auto_run_enabled() -> bool:
    return os.environ.get("LBG_TEAM_FAILURE_RETRY_AUTO_RUN", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def max_retries() -> int:
    try:
        return max(1, int(os.environ.get("LBG_TEAM_FAILURE_MAX_RETRIES", "2")))
    except ValueError:
        return 2


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
    if ctx.get("_godot_followup") or ctx.get("_m9_followup"):
        return True
    if ctx.get("_failure_followup") and not ctx.get("_failure_retry"):
        return True
    if ctx.get("_failure_retry"):
        retry_count = int(ctx.get("retry_count", 1))
        if retry_count >= max_retries():
            return True
        return False
    return False


def _summarize(result: dict[str, Any]) -> dict[str, Any]:
    err = result.get("error")
    return {
        "kind": result.get("kind"),
        "ok": result.get("ok"),
        "error": (str(err)[:300] if err else None),
        "keys": sorted(str(k) for k in list(result.keys())[:20]),
    }


def control_check_before_retry(task: TeamTask) -> tuple[bool, str]:
    """Agent de contrôle (Thémis / Gladys) : valide si une tâche échouée est éligible à la relance.

    Retourne:
        (True, reason) si la relance est approuvée.
        (False, reason) si la relance est bloquée (ex: code manquant ou hôte toujours hors ligne).
    """
    ctx = task.context or {}
    failure_summary = ctx.get("failure_summary") or {}
    err_text = str(failure_summary.get("error") or "") + " " + str(ctx.get("error") or "")
    err_lower = err_text.lower()

    # 1. Erreurs logicielles permanentes : pas de retry sans intervention de dev / forge
    permanent_code_patterns = (
        "syntaxerror",
        "modulenotfounderror",
        "filenotfounderror",
        "manquant",
        "missing script",
        "no such file or directory",
        "nosuchmethoderror",
        "classnotfoundexception",
    )
    if any(p in err_lower for p in permanent_code_patterns):
        return False, f"permanent_code_error: requires fix before retry ({err_text[:120]})"

    # 2. Erreurs réseau / services distants : vérifier si la ressource est revenue
    ip_port_match = re.search(r"(\b(?:\d{1,3}\.){3}\d{1,3}\b):(\d{2,5})", err_text)
    if ip_port_match:
        ip, port_str = ip_port_match.group(1), ip_port_match.group(2)
        try:
            port = int(port_str)
            with socket.create_connection((ip, port), timeout=1.5):
                return True, f"service_recovered: {ip}:{port} responds"
        except (socket.timeout, OSError) as e:
            return False, f"service_still_unreachable: {ip}:{port} ({e})"

    # 3. Transitoire ou standard : approuvé
    return True, "transient_or_approved_retry"


def maybe_spawn_after_failure(task: TeamTask) -> list[str]:
    """Crée triage PM (+ retry optionnel avec contrôle) après un failed non déjà suivi."""
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

    current_retry_count = int((task.context or {}).get("retry_count", 0))
    if retry_enabled() and current_retry_count < max_retries():
        next_retry_count = current_retry_count + 1
        clean_context = {
            k: v
            for k, v in (task.context or {}).items()
            if not str(k).startswith("_") and k != "retry_count"
        }
        retry = team_store.create_task(
            role=task.role,
            objective=f"Relancer après échec ({next_retry_count}/{max_retries()}) — {task.objective}"[:400],
            actor_id=actor_id(),
            priority="high",
            context={
                **parent_ref,
                **clean_context,
                "_failure_followup": True,
                "_failure_retry": True,
                "retry_count": next_retry_count,
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
        # PM L1 auto (Thémis analyse)
        if task.role == "pm":
            ran = team_roles.run_task(tid)
            if ran is not None:
                out.append({"task_id": tid, "role": ran.role, "status": ran.status})
            continue

        # Retry soumis à l'agent de contrôle
        if task.context.get("_failure_retry"):
            should_run, reason = control_check_before_retry(task)
            team_store.update_task(
                tid,
                context_patch={
                    "_control_check_ok": should_run,
                    "_control_check_reason": reason,
                    "_control_check_ts": time.time(),
                },
            )
            if not should_run or not retry_auto_run_enabled():
                # L'agent de contrôle bloque la relance immédiate (ex: service KO ou code fix requis)
                continue
            ran = team_roles.run_task(tid)
            if ran is not None:
                out.append({"task_id": tid, "role": ran.role, "status": ran.status})
    return out
