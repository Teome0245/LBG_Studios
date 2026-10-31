"""Workflow Pygmalion — import calques Gemini → face_rig (agent Windows/Linux)."""

from __future__ import annotations

import re
from typing import Callable

from team.models import TeamTask

Dispatcher = Callable[..., dict[str, object]]


def _is_face_parts_track(task: TeamTask) -> bool:
    ctx = task.context or {}
    if ctx.get("face_parts") or ctx.get("import_face_parts") or ctx.get("face_rig_import"):
        return True
    text = (task.objective or "").lower()
    return bool(
        re.search(
            r"\b(import_face_parts|face.?rig|calques? (yeux|bouche|visage)|lyra.?face|face_parts)\b",
            text,
        )
    )


def execute_face_parts_workflow(task: TeamTask, dispatch: Dispatcher) -> dict[str, object]:
    ctx = dict(task.context or {})
    ctx.setdefault("subproject", "infographiste_ia")
    ctx.setdefault("infographiste_ia", True)
    character_id = str(ctx.get("character_id") or "lyra_assistant")
    deploy = bool(ctx.get("face_parts_deploy"))
    action = {
        "kind": "import_face_parts",
        "character_id": character_id,
        "deploy": deploy,
    }
    inbox = ctx.get("face_parts_inbox")
    if isinstance(inbox, str) and inbox.strip():
        action["inbox"] = inbox.strip()

    desk_ctx = {
        **ctx,
        "desktop_action": action,
        "desktop_dry_run": ctx.get("desktop_dry_run", True),
        # Mains 24/7 Omarchy (.143:5005) si LBG_AGENT_HANDS_URL est défini ; sinon fallback default (.10).
        "desktop_target": ctx.get("desktop_target") or "hands",
    }
    remote = dispatch(
        "agent.desktop",
        actor_id=task.actor_id,
        text=task.objective,
        context=desk_ctx,
    )
    ok = bool(remote.get("ok")) and str(remote.get("outcome") or "") in {"ok", "dry_run"}
    return {
        "kind": "face_parts_workflow",
        "ok": ok,
        "desktop": remote,
        "action": action,
        "subproject": "infographiste_ia",
        "persona": "Pygmalion",
        "hint": (
            "Cible Team : VM Omarchy .143:5005 (LBG_AGENT_HANDS_URL) inbox /var/lib/lbg-hands/inbox. "
            "Poste .10 (C:\\Agent_IA) : LBG_DESKTOP_FACE_PARTS_ENABLED=1 + inbox N:\\…\\Expressions. "
            "Dry-run par défaut ; deploy réel = context.face_parts_deploy + approval."
        ),
    }


def resolve_face_parts_workflow(task: TeamTask) -> bool:
    ctx = task.context or {}
    if ctx.get("lora_pipeline") or ctx.get("sprites_2d"):
        return False
    return _is_face_parts_track(task)
