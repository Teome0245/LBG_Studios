"""Tests workflow Team face_parts (Pygmalion)."""

from __future__ import annotations

from team.face_parts_workflow import execute_face_parts_workflow, resolve_face_parts_workflow
from team.models import TeamTask


def test_resolve_face_parts_from_context() -> None:
    task = TeamTask(
        id="t1",
        role="dev_game",
        actor_id="test",
        objective="assets",
        context={"face_parts": True},
    )
    assert resolve_face_parts_workflow(task) is True


def test_resolve_face_parts_from_objective() -> None:
    task = TeamTask(
        id="t2",
        role="dev_game",
        actor_id="test",
        objective="importe les calques visage Lyra face_rig",
    )
    assert resolve_face_parts_workflow(task) is True


def test_resolve_skips_lora() -> None:
    task = TeamTask(
        id="t3",
        role="dev_game",
        actor_id="test",
        objective="face_rig",
        context={"lora_pipeline": True},
    )
    assert resolve_face_parts_workflow(task) is False


def test_execute_dispatches_desktop_dry_run() -> None:
    seen: dict = {}

    def fake_dispatch(handler: str, **kwargs):
        seen["handler"] = handler
        seen["kwargs"] = kwargs
        return {"ok": True, "outcome": "dry_run", "eyes_frames": ["idle"]}

    task = TeamTask(
        id="t4",
        role="dev_game",
        actor_id="ui:team",
        objective="import_face_parts Lyra",
        context={"face_parts": True, "desktop_dry_run": True},
    )
    out = execute_face_parts_workflow(task, fake_dispatch)
    assert out["kind"] == "face_parts_workflow"
    assert out["ok"] is True
    assert seen["handler"] == "agent.desktop"
    action = seen["kwargs"]["context"]["desktop_action"]
    assert action["kind"] == "import_face_parts"
    assert action["character_id"] == "lyra_assistant"
    assert seen["kwargs"]["context"]["desktop_dry_run"] is True
    assert seen["kwargs"]["context"]["desktop_target"] == "hands"
