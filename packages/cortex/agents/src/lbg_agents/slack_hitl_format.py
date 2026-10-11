"""Format L2 HITL Slack — texte + Block Kit (ADR 0021 S2)."""

from __future__ import annotations

import os
from typing import Any


def short_task_id(task_id: str, *, n: int = 8) -> str:
    tid = (task_id or "").strip()
    return tid[:n] if tid else "?"


def pilot_team_url(task_id: str = "") -> str:
    base = os.environ.get("LBG_PILOT_PUBLIC_URL", "http://192.168.0.140:8080").strip().rstrip("/")
    url = f"{base}/#/team"
    if task_id:
        url = f"{url}?task={task_id}"
    return url


def pilot_jobs_url(job_id: str = "") -> str:
    base = os.environ.get("LBG_PILOT_PUBLIC_URL", "http://192.168.0.140:8080").strip().rstrip("/")
    url = f"{base}/#/jobs"
    if job_id:
        url = f"{url}?job={job_id}"
    return url


def _is_job_payload(task: dict[str, Any]) -> bool:
    kind = str(task.get("kind") or task.get("hitl_kind") or "").strip().lower()
    if kind in ("job", "jobs"):
        return True
    return bool(task.get("job_id")) and not task.get("role")


def format_l2_pending_text(task: dict[str, Any]) -> str:
    tid = str(task.get("id") or task.get("job_id") or "?")
    sid = short_task_id(tid)
    is_job = _is_job_payload(task)
    alias = str(
        task.get("role_alias")
        or task.get("role_label")
        or task.get("role")
        or (task.get("capability") if is_job else None)
        or ("job" if is_job else "?")
    )
    obj = str(task.get("objective") or "").strip()
    pilot = pilot_jobs_url(tid) if is_job else pilot_team_url(tid)
    kind_label = "Job L2" if is_job else "L2"
    ready = bool(task.get("awaiting_run")) or (
        not is_job and str(task.get("status") or "").lower() == "queued" and task.get("stored_approval_token")
    )
    if ready:
        lines = [
            f"▶️ {kind_label} approuvé — prêt à exécuter `{sid}` [{alias}]",
            obj[:500] if obj else "(sans objectif)",
            "",
            f"→ Pilot `#/team/fleet` ou bureau Campus — **Exécuter**",
            f"Pilot : {pilot}",
        ]
    else:
        lines = [
            f"🔔 {kind_label} en attente — `{sid}` [{alias}]",
            obj[:500] if obj else "(sans objectif)",
            "",
            f"→ `approve {sid}`  ou  `valider {sid}`",
            f"→ `reject {sid}`  ou  `annuler {sid}`",
            f"Pilot : {pilot}",
        ]
    return "\n".join(lines)


def format_l2_pending_blocks(task: dict[str, Any]) -> list[dict[str, Any]]:
    """Block Kit : boutons action (bot) + lien Pilot (webhook OK)."""
    tid = str(task.get("id") or task.get("job_id") or "")
    sid = short_task_id(tid)
    is_job = _is_job_payload(task)
    alias = str(
        task.get("role_alias")
        or task.get("role_label")
        or task.get("role")
        or (task.get("capability") if is_job else None)
        or ("job" if is_job else "?")
    )
    obj = str(task.get("objective") or "").strip() or "(sans objectif)"
    if len(obj) > 280:
        obj = obj[:277].rstrip() + "…"
    pilot = pilot_jobs_url(tid) if is_job else pilot_team_url(tid)
    header = f"{'Job L2' if is_job else 'L2'} en attente — {sid}"

    blocks: list[dict[str, Any]] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": header[:150], "emoji": True},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Rôle*\n{alias}"},
                {"type": "mrkdwn", "text": f"*Id*\n`{sid}`"},
            ],
        },
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Objectif*\n{obj}"}},
        {
            "type": "actions",
            "block_id": f"lbg_l2_{sid}",
            "elements": [
                {
                    "type": "button",
                    "action_id": "lbg_l2_approve",
                    "text": {"type": "plain_text", "text": "Approve", "emoji": True},
                    "style": "primary",
                    "value": tid or sid,
                },
                {
                    "type": "button",
                    "action_id": "lbg_l2_reject",
                    "text": {"type": "plain_text", "text": "Reject", "emoji": True},
                    "style": "danger",
                    "value": tid or sid,
                },
                {
                    "type": "button",
                    "action_id": "lbg_l2_pilot",
                    "text": {"type": "plain_text", "text": "Ouvrir Pilot", "emoji": True},
                    "url": pilot,
                },
            ],
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Fallback texte : `approve {sid}` · `reject {sid}`",
                }
            ],
        },
    ]
    return blocks
