"""Workflow dev_game — sprites 2D Prime (Pygmalion)."""

from __future__ import annotations

import re
from typing import Callable

from team.models import TeamTask
from team.sprites_2d_pipeline import (
    probe_sprites_2d_readiness,
    run_sprites_2d_deploy_step,
    sprites_deploy_enabled,
)

Dispatcher = Callable[..., dict[str, object]]


def _is_sprites_2d_track(task: TeamTask) -> bool:
    ctx = task.context
    if ctx.get("sprites_2d") or ctx.get("sprites_2d_pipeline"):
        return True
    text = (task.objective or "").lower()
    return bool(
        re.search(
            r"\b(sprite?s? 2d|top.?down|prime.?client.?sprite|deploy.?sprite|lbg_sprite2d)\b",
            text,
        )
    )


def execute_sprites_2d_workflow(task: TeamTask, dispatch: Dispatcher) -> dict[str, object]:
    del dispatch
    probe = probe_sprites_2d_readiness()
    deploy = None
    missing = probe.get("missing") if isinstance(probe.get("missing"), list) else []
    should_deploy = sprites_deploy_enabled() and (
        bool(missing) or bool(task.context.get("sprites_2d_deploy"))
    )
    if should_deploy:
        deploy = run_sprites_2d_deploy_step(sync_to_core=True)
        probe = probe_sprites_2d_readiness()

    ok = bool(probe.get("ok")) and (deploy is None or bool(deploy.get("ok")))
    return {
        "kind": "sprites_2d_workflow",
        "ok": ok,
        "probe": probe,
        "deploy": deploy,
        "subproject": "infographiste_ia",
        "persona": "Pygmalion",
    }


def resolve_sprites_2d_workflow(task: TeamTask) -> bool:
    ctx = task.context
    if ctx.get("lora_pipeline"):
        return False
    return _is_sprites_2d_track(task)
