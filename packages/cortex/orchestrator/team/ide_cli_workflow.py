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


def execute_ide_cli_workflow(task: TeamTask, dispatch: Dispatcher) -> dict[str, object]:
    """Dispatch desktop run_cli_agent vers Omarchy .143 (dry-run par défaut)."""
    ctx = dict(task.context or {})
    app = _default_app(task)
    prompt = str(ctx.get("ide_cli_prompt") or task.objective or "").strip()
    cwd = str(ctx.get("ide_cli_cwd") or os.environ.get("LBG_OMARCHY_STUDIO_WORKSPACE") or _DEFAULT_CWD).strip()
    dry = True
    if ctx.get("desktop_dry_run") is False or ctx.get("ide_cli_live") is True:
        dry = False
    if not ide_cli_enabled():
        # Toujours autoriser un dry-run de preview même si flag Team off
        dry = True

    action = {
        "kind": "run_cli_agent",
        "app": app,
        "prompt": prompt,
        "cwd": cwd,
    }
    if ctx.get("ide_cli_timeout_s") is not None:
        try:
            action["timeout_s"] = int(ctx["ide_cli_timeout_s"])  # type: ignore[arg-type]
        except (TypeError, ValueError):
            pass

    desk_ctx = {
        **ctx,
        "desktop_action": action,
        "desktop_target": ctx.get("desktop_target") or "omarchy",
        "desktop_dry_run": dry,
        "ide_cli": True,
    }
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
