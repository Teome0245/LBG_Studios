"""Workflow dev_game — pipeline LoRA Pygmalion (vision → Kohya → train)."""

from __future__ import annotations

import re
from typing import Callable

from team.inspiration_lora_pipeline import pipeline_targets, run_lora_pipeline_step
from team.models import TeamTask

Dispatcher = Callable[..., dict[str, object]]


def _is_lora_pipeline_track(task: TeamTask) -> bool:
    ctx = task.context
    if ctx.get("lora_pipeline") or ctx.get("infographiste_lora_pipeline"):
        return True
    text = (task.objective or "").lower()
    return bool(
        re.search(
            r"\b("
            r"lora.?pipeline|vision.?classif|unclassified|"
            r"entra[îi]n.*lora|mmorpg_insp|lbg_sprite2d|prime_sprite|kohya"
            r")\b",
            text,
        )
    )


def execute_infographiste_lora_workflow(task: TeamTask, dispatch: Dispatcher) -> dict[str, object]:
    del dispatch  # pipeline direct, pas de brief PM lourd
    pipeline = run_lora_pipeline_step(persist_state=True)
    targets = pipeline_targets()
    ok = bool(pipeline.get("ok"))
    return {
        "kind": "infographiste_lora_workflow",
        "ok": ok,
        "pipeline": pipeline,
        "targets": targets,
        "subproject": "infographiste_ia",
        "persona": "Pygmalion",
    }


def resolve_infographiste_lora_workflow(task: TeamTask) -> bool:
    return _is_lora_pipeline_track(task)
