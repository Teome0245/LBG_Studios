"""Notification HITL à la création d'une tâche Team L2 (Slack / Matrix)."""

from __future__ import annotations

import os
from typing import Any

from team.models import TeamTask


def l2_slack_on_create_enabled() -> bool:
    raw = os.environ.get("LBG_TEAM_L2_SLACK_ON_CREATE", "1").strip().lower()
    return raw in ("1", "true", "yes", "on")


def notify_l2_pending(task: TeamTask) -> dict[str, Any] | None:
    """Push HITL si la tâche exige une validation humaine (best-effort)."""
    if not l2_slack_on_create_enabled():
        return None
    if not task.approval_required:
        return None
    if task.status not in ("review", "queued", "waiting_approval"):
        return None
    payload = {
        "id": task.id,
        "role": task.role,
        "status": task.status,
        "objective": (task.objective or "")[:240],
        "actor_id": task.actor_id,
        "approval_required": True,
    }
    try:
        from lbg_agents.ops_notify import send_l2_pending

        return send_l2_pending(payload)
    except Exception:
        return None


def notify_l2_execute_ready(task: TeamTask) -> dict[str, Any] | None:
    """Slack après approbation token — tâche queued prête à Exécuter."""
    if not l2_slack_on_create_enabled():
        return None
    if not task.approval_required:
        return None
    if task.status != "queued" or not task.stored_approval_token:
        return None
    payload = {
        "id": task.id,
        "role": task.role,
        "status": task.status,
        "objective": (task.objective or "")[:240],
        "actor_id": task.actor_id,
        "approval_required": True,
        "awaiting_run": True,
    }
    try:
        from lbg_agents.ops_notify import send_l2_pending

        return send_l2_pending(payload)
    except Exception:
        return None
