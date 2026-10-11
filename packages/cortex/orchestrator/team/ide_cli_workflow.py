"""Workflow Team — mains code .143 via run_cli_agent (ADR 0025).

Personas : Iris (dev_godot), Dédale (dev_game), Pygmalion (infographiste_ia),
Métis (dev_studio). Exécutant headless nominal : OpenCode ; Claude CLI expérimental ;
Cline CLI hors scope (.143 PATH).
"""

from __future__ import annotations

import os
import re
from typing import Callable

from team.models import TeamTask

Dispatcher = Callable[..., dict[str, object]]

_DEFAULT_CWD = "/home/lbg/projects/LBG_Studios"


def ide_cli_enabled() -> bool:
    return os.environ.get("LBG_TEAM_IDE_CLI_ENABLED", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def resolve_ide_cli_workflow(task: TeamTask) -> bool:
    ctx = task.context or {}
    if ctx.get("ide_cli") is True or ctx.get("run_cli_agent") is True:
        return True
    if task.role == "dev_studio":
        return True
    wf = str(ctx.get("workflow") or "").strip().lower()
    if wf in ("ide_cli", "run_cli_agent", "mains_code"):
        return True
    obj = task.objective or ""
    return bool(
        re.search(
            r"(?i)\b(run_cli_agent|ide.?cli|mains?\s+code|claude\s+code\s+headless|"
            r"lance\s+(?:claude|opencode|cline)\s+sur\s+omarchy)\b",
            obj,
        )
    )


def _default_app(task: TeamTask) -> str:
    ctx = task.context or {}
    raw = str(ctx.get("ide_cli_app") or ctx.get("cli_app") or "").strip().lower()
    if raw in ("claude", "cline", "opencode"):
        return raw
    # Nominal OpenCode (Claude CLI expérimental vs Ollama local — ADR 0025)
    return "opencode"


def _persona_label(task: TeamTask) -> str:
    ctx = task.context or {}
    if task.role == "dev_studio" or str(ctx.get("subproject") or "") == "cortex_studio":
        return "Métis"
    if ctx.get("infographiste_ia") or str(ctx.get("subproject") or "") == "infographiste_ia":
        return "Pygmalion"
    persona = str(ctx.get("godot_dev_persona") or "").lower()
    if persona == "hermes":
        return "Hermès"
    if persona == "iris" or task.role == "dev_godot":
        return "Iris"
    if task.role == "dev_game":
        return "Dédale"
    return task.role


def _desktop_approval_token() -> str:
    """Jeton attendu par l'agent .143 (LBG_LINUX_APPROVAL_TOKEN)."""
    return (
        os.environ.get("LBG_DESKTOP_APPROVAL_TOKEN")
        or os.environ.get("LBG_LINUX_APPROVAL_TOKEN")
        or ""
    ).strip()


def _inject_desktop_approval(desk_ctx: dict[str, object], *, dry: bool) -> dict[str, object]:
    """LIVE : passe le jeton (ou soft-confirm) — sinon .143 renvoie approval_denied."""
    if dry:
        return desk_ctx
    if desk_ctx.get("desktop_approval"):
        return desk_ctx
    tok = _desktop_approval_token()
    if tok:
        return {**desk_ctx, "desktop_approval": tok}
    # LAB soft-confirm côté agent si mode confirm — utile si token non sync sur orch
    if os.environ.get("LBG_TEAM_IDE_CLI_SOFT_CONFIRM", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    ):
        return {**desk_ctx, "desktop_confirm": True, "desktop_approval": "confirmed"}
    return desk_ctx


def _resolve_ide_cli_timeout_s(task: TeamTask, prompt: str, app: str) -> int:
    """Timeout mandat → agent .143 (plancher auto si prompt long)."""
    ctx = task.context or {}
    raw = ctx.get("ide_cli_timeout_s")
    if raw is None:
        raw = os.environ.get("LBG_TEAM_IDE_CLI_TIMEOUT_S", "").strip() or None
    try:
        explicit = int(raw) if raw is not None else None  # type: ignore[arg-type]
    except (TypeError, ValueError):
        explicit = None
    # Miroir budget agent (base OpenCode 1200 + 60s/500 car., cap 3600)
    base = 1200 if app == "opencode" else 900
    budget = base + min(1500, (len(prompt or "") // 500) * 60)
    n = max(explicit or 0, budget)
    return max(60, min(n, 3600))


def execute_ide_cli_workflow(task: TeamTask, dispatch: Dispatcher) -> dict[str, object]:
    """Dispatch desktop run_cli_agent vers Omarchy .143 (dry-run par défaut)."""
    ctx = dict(task.context or {})
    app = _default_app(task)
    prompt = str(ctx.get("ide_cli_prompt") or task.objective or "").strip()
    cwd = str(ctx.get("ide_cli_cwd") or os.environ.get("LBG_OMARCHY_STUDIO_WORKSPACE") or _DEFAULT_CWD).strip()
    # LIVE par défaut si le flag Team est ON — sinon dry-run only (preview).
    # Opt-out explicite : desktop_dry_run=true / ide_cli_live=false.
    if not ide_cli_enabled():
        dry = True
    elif ctx.get("desktop_dry_run") is True or ctx.get("ide_cli_live") is False:
        dry = True
    else:
        dry = False

    try:
        from team.plan_ticket_closure import closure_prompt_addon, is_plan_ticket_task

        if is_plan_ticket_task(task):
            addon = closure_prompt_addon(task)
            if addon and addon not in prompt:
                prompt = (prompt + addon).strip()
    except Exception:
        pass

    timeout_s = _resolve_ide_cli_timeout_s(task, prompt, app)
    action = {
        "kind": "run_cli_agent",
        "app": app,
        "prompt": prompt,
        "cwd": cwd,
        "timeout_s": timeout_s,
    }

    desk_ctx = {
        **ctx,
        "desktop_action": action,
        "desktop_target": ctx.get("desktop_target") or "omarchy",
        "desktop_dry_run": dry,
        "ide_cli": True,
        "ide_cli_timeout_s": timeout_s,
    }
    desk_ctx = _inject_desktop_approval(desk_ctx, dry=dry)
    remote = dispatch(
        "agent.desktop",
        actor_id=task.actor_id,
        text=prompt[:500] or f"run_cli_agent {app}",
        context=desk_ctx,
    )
    ok = bool(isinstance(remote, dict) and remote.get("ok"))
    persona = _persona_label(task)
    summary = (
        f"{persona} — ide_cli app={app} "
        f"{'dry-run' if dry else 'live'} "
        f"timeout_s={timeout_s} "
        f"ok={ok} · ADR 0025"
    )
    if isinstance(remote, dict) and remote.get("reply"):
        summary = f"{summary} · {str(remote.get('reply'))[:200]}"

    return {
        "kind": "ide_cli_workflow",
        "ok": ok if ide_cli_enabled() or dry else False,
        "ide_cli": True,
        "app": app,
        "cwd": cwd,
        "dry_run": dry,
        "timeout_s": timeout_s,
        "prompt_chars": len(prompt),
        "team_flag_enabled": ide_cli_enabled(),
        "persona": persona,
        "desktop": remote,
        "deliverables": [],
        "human_summary": summary,
        "summary": summary,
        "mission_track": "mains_code_143",
        "hint": (
            None
            if ide_cli_enabled()
            else "LBG_TEAM_IDE_CLI_ENABLED=0 — dry-run only ; activer après smoke .143"
        ),
    }
