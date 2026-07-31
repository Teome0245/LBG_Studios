"""Workflow Team — lance un Cursor Cloud Agent (PR/code), pas un chat LLM."""

from __future__ import annotations

from typing import Any

from team.models import TeamTask

from integrations import cursor_agent as cursor


def run_cursor_cloud_from_task(task: TeamTask) -> dict[str, Any]:
    ctx = task.context or {}
    repo = str(ctx.get("repository") or ctx.get("repo") or "").strip()
    prompt = str(ctx.get("cursor_prompt") or task.objective or "").strip()
    model = str(ctx.get("cursor_model") or "").strip() or None
    dry = bool(ctx.get("dry_run", False)) or str(ctx.get("cursor_dry_run", "")).lower() in (
        "1",
        "true",
        "yes",
    )
    auto_pr = ctx.get("auto_create_pr")
    if auto_pr is None:
        auto_pr = True

    if dry or not cursor.enabled():
        preview = cursor.launch_agent_dry_run(prompt=prompt, repository=repo, model=model)
        return {
            "ok": bool(preview.get("ok")),
            "kind": "cursor_cloud_agent",
            "dry_run": True,
            "preview": preview,
            "health": cursor.health(),
        }

    result = cursor.launch_cloud_agent(
        prompt=prompt,
        repository=repo,
        model=model,
        auto_create_pr=bool(auto_pr),
        wait=bool(ctx.get("cursor_wait", True)),
    )
    return {
        "ok": bool(result.get("ok")),
        "kind": "cursor_cloud_agent",
        "dry_run": False,
        "cursor": result,
        "health": cursor.health(),
    }
