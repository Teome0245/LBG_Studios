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


def format_l2_pending_text(task: dict[str, Any]) -> str:
    tid = str(task.get("id") or "?")
    sid = short_task_id(tid)
    alias = str(task.get("role_alias") or task.get("role_label") or task.get("role") or "?")
    obj = str(task.get("objective") or "").strip()
    lines = [
        f"🔔 L2 en attente — `{sid}` [{alias}]",
        obj[:500] if obj else "(sans objectif)",
        "",
        f"→ `approve {sid}`  ou  `valider {sid}`",
        f"→ `reject {sid}`  ou  `annuler {sid}`",
        f"Pilot : {pilot_team_url(tid)}",
    ]
    return "\n".join(lines)


def format_l2_pending_blocks(task: dict[str, Any]) -> list[dict[str, Any]]:
    """Block Kit : boutons action (bot) + lien Pilot (webhook OK)."""
    tid = str(task.get("id") or "")
    sid = short_task_id(tid)
    alias = str(task.get("role_alias") or task.get("role_label") or task.get("role") or "?")
    obj = str(task.get("objective") or "").strip() or "(sans objectif)"
    if len(obj) > 280:
        obj = obj[:277].rstrip() + "…"

    blocks: list[dict[str, Any]] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"L2 en attente — {sid}", "emoji": True},
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
                    "url": pilot_team_url(tid),
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
