"""Pont Cloud ↔ LAN — file d'exécution WSL (pull) pour skills ops hors VM Cloud."""

from __future__ import annotations

import json
import os
import time
from typing import Any

from team import store as team_store
from team.models import TeamTask

# Skills autorisés côté poste opérateur (WSL). Clé = wsl_skill dans context.
WSL_SKILLS: dict[str, dict[str, Any]] = {
    "diag_godot_supervisor": {
        "script": "infra/scripts/diag_godot_supervisor_wsl.sh",
        "description": "Diag Godot supervisor via SSH .140",
        "default_args": ["--summary"],
        "role": "qa",
    },
    "smoke_godot_m11_login": {
        "script": "infra/scripts/smoke_godot_m11_login_lan.sh",
        "description": "Smoke M11 login HTTP gateway Prime",
        "role": "qa",
    },
    "smoke_godot_m12_ws": {
        "script": "infra/scripts/smoke_godot_m12_ws_lan.sh",
        "description": "Smoke M12 WS login → zone_state → move",
        "role": "qa",
    },
    "smoke_godot_owners": {
        "script": "infra/scripts/smoke_godot_owners.sh",
        "description": "Bundle owner smokes Godot M11+M12 (+M9/M10)",
        "role": "qa",
    },
    "smoke_lan_surfaces": {
        "script": "../../tools/smoke_lan_surfaces.sh",
        "description": "Smoke HTTP surfaces LAN (depuis racine monorepo)",
        "cwd": "monorepo",
        "role": "qa",
    },
    "smoke_cursor_agent": {
        "script": "infra/scripts/smoke_cursor_agent_lan.sh",
        "description": "Smoke Cursor Cloud Agent health sur orchestrateur",
        "role": "dev_game",
    },
}


def enabled() -> bool:
    return os.environ.get("LBG_WSL_EXECUTOR_ENABLED", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def token_configured() -> bool:
    return bool(os.environ.get("LBG_WSL_EXECUTOR_TOKEN", "").strip())


def check_token(header: str | None) -> bool:
    expected = os.environ.get("LBG_WSL_EXECUTOR_TOKEN", "").strip()
    if not expected:
        return True
    return (header or "").strip() == expected


def is_wsl_task(task: TeamTask) -> bool:
    ctx = task.context or {}
    if ctx.get("local_wsl") is True:
        return True
    if str(ctx.get("executor") or "").strip().lower() in ("wsl", "local_wsl"):
        return True
    return bool(str(ctx.get("wsl_skill") or "").strip())


def list_skills() -> list[dict[str, Any]]:
    return [
        {
            "id": skill_id,
            "description": meta.get("description", ""),
            "script": meta.get("script"),
            "role": meta.get("role", "qa"),
        }
        for skill_id, meta in WSL_SKILLS.items()
    ]


def skill_allowed(skill_id: str) -> bool:
    return skill_id in WSL_SKILLS


def enqueue_wsl_task(
    *,
    wsl_skill: str,
    objective: str,
    actor_id: str = "pilot:wsl",
    priority: str = "normal",
    role: str | None = None,
    args: list[str] | None = None,
    extra_context: dict[str, object] | None = None,
) -> TeamTask:
    if not skill_allowed(wsl_skill):
        raise ValueError(f"wsl_skill hors allowlist: {wsl_skill}")
    meta = WSL_SKILLS[wsl_skill]
    ctx: dict[str, object] = {
        "executor": "wsl",
        "local_wsl": True,
        "wsl_skill": wsl_skill,
        "wsl_args": list(args or meta.get("default_args") or []),
        "utility_key": f"wsl_{wsl_skill}",
    }
    if extra_context:
        ctx.update(extra_context)
    return team_store.create_task(
        role=role or str(meta.get("role") or "qa"),  # type: ignore[arg-type]
        objective=objective,
        actor_id=actor_id,
        priority=priority,  # type: ignore[arg-type]
        approval_required=False,
        context=ctx,
    )


def claim_next_wsl_task(*, executor_id: str) -> TeamTask | None:
    """Atomique queued → running pour la plus ancienne tâche WSL."""
    conn = team_store.get_connection()
    conn.execute("BEGIN IMMEDIATE")
    try:
        rows = conn.execute(
            "SELECT * FROM team_tasks WHERE status = 'queued' ORDER BY created_ts ASC LIMIT 200"
        ).fetchall()
        now = time.time()
        for row in rows:
            task = team_store._row_to_task(row)  # noqa: SLF001
            if not is_wsl_task(task):
                continue
            skill = str((task.context or {}).get("wsl_skill") or "").strip()
            if skill and not skill_allowed(skill):
                continue
            patch = dict(task.context or {})
            patch["wsl_claimed_by"] = executor_id
            patch["wsl_claimed_ts"] = now
            cur = conn.execute(
                """
                UPDATE team_tasks
                SET status = 'running', context_json = ?, updated_ts = ?
                WHERE id = ? AND status = 'queued'
                """,
                (json.dumps(patch, ensure_ascii=False), now, task.id),
            )
            if cur.rowcount == 1:
                conn.commit()
                claimed = team_store.get_task(task.id)
                if claimed is not None:
                    try:
                        from team import presence as team_presence

                        team_presence.emit_from_task(claimed, event="status_changed")
                    except Exception:
                        pass
                return claimed
        conn.commit()
        return None
    except Exception:
        conn.rollback()
        raise


def complete_wsl_task(
    task_id: str,
    *,
    ok: bool,
    exit_code: int | None = None,
    stdout_tail: str = "",
    stderr_tail: str = "",
    result: dict[str, object] | None = None,
    executor_id: str = "",
) -> TeamTask | None:
    task = team_store.get_task(task_id)
    if task is None or not is_wsl_task(task):
        return None
    if task.status not in ("running", "queued"):
        return None
    skill = str((task.context or {}).get("wsl_skill") or "")
    payload: dict[str, object] = {
        "kind": "wsl_executor",
        "ok": ok,
        "wsl_skill": skill,
        "exit_code": exit_code,
        "stdout_tail": (stdout_tail or "")[-4000:],
        "stderr_tail": (stderr_tail or "")[-2000:],
        "completed_by": executor_id or (task.context or {}).get("wsl_claimed_by"),
    }
    if result:
        payload.update(result)
    status = "done" if ok else "failed"
    return team_store.update_task(task_id, status=status, result=payload)


def health() -> dict[str, object]:
    pending = 0
    running = 0
    for t in team_store.list_tasks(status="queued", limit=200):
        if is_wsl_task(t):
            pending += 1
    for t in team_store.list_tasks(status="running", limit=200):
        if is_wsl_task(t):
            running += 1
    return {
        "service": "wsl_executor",
        "enabled": enabled(),
        "token_required": token_configured(),
        "skills_allowlist": list(WSL_SKILLS.keys()),
        "pending": pending,
        "running": running,
        "ready": enabled(),
        "note": "Exécution pull depuis WSL — pas depuis Cloud Agent VM",
    }
