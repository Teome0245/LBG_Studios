"""Tests ADR 0019 Vague 3 — bus_hooks + followup propose/ack."""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path

import pytest

if "hybrid_proactive_agent" not in sys.modules:
    _stub = types.ModuleType("hybrid_proactive_agent")

    class LongTermMemoryStore:  # noqa: N801
        pass

    class MemoryEntry:  # noqa: N801
        pass

    _stub.LongTermMemoryStore = LongTermMemoryStore  # type: ignore[attr-defined]
    _stub.MemoryEntry = MemoryEntry  # type: ignore[attr-defined]
    sys.modules["hybrid_proactive_agent"] = _stub

os.environ["LBG_TEAM_DB_PATH"] = ":memory:"
os.environ["LBG_TEAM_BUS_HOOKS"] = "1"
os.environ["LBG_TEAM_MEMORY_ENABLED"] = "1"

from team import bus_hooks  # noqa: E402
from team import messages as team_messages  # noqa: E402
from team import store as team_store  # noqa: E402
from team.models import TeamTask  # noqa: E402
from team.qa_followup import maybe_spawn_after_qa_failure  # noqa: E402


@pytest.fixture(autouse=True)
def _reset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_TEAM_DB_PATH", ":memory:")
    monkeypatch.setenv("LBG_TEAM_BUS_HOOKS", "1")
    monkeypatch.setenv("LBG_TEAM_MEMORY_PATH", str(tmp_path / "mem.jsonl"))
    monkeypatch.setenv("LBG_TEAM_MEMORY_ENABLED", "1")
    monkeypatch.setenv("LBG_TEAM_QA_FOLLOWUP_ENABLED", "1")
    team_store.reset_for_tests()


def test_emit_consult_and_gaps() -> None:
    parent = team_store.create_task(role="pm", objective="autoconsult", actor_id="u:bus")
    n = bus_hooks.emit_consult_round(
        task_id=parent.id,
        specialists=[bus_hooks.AGENT_ARGUS, bus_hooks.AGENT_IRIS],
    )
    assert n == 2
    n2 = bus_hooks.emit_gaps(
        task_id=parent.id,
        gaps=[{"owner": "argus", "track": "qa_health", "gap": "healthz down"}],
    )
    assert n2 == 1
    msgs = team_messages.list_messages(task_id=parent.id)
    kinds = {m.kind for m in msgs}
    assert kinds == {"consult", "gap"}


def test_emit_spawned_followups_propose_ack() -> None:
    parent = team_store.create_task(role="qa", objective="smoke", actor_id="u:bus")
    child = team_store.create_task(
        role="pm",
        objective="triage",
        actor_id="u:bus",
        context={"parent_task_id": parent.id},
    )
    n = bus_hooks.emit_spawned_followups(
        parent_task_id=parent.id,
        child_task_ids=[child.id],
        from_agent=bus_hooks.AGENT_ARGUS,
        verify_summary="failed",
        verify_ok=False,
    )
    assert n >= 2
    msgs = team_messages.list_messages(task_id=parent.id)
    kinds = {m.kind for m in msgs}
    assert "propose" in kinds
    assert "ack" in kinds
    assert "verify_result" in kinds


def test_qa_followup_emits_bus(monkeypatch: pytest.MonkeyPatch) -> None:
    task = team_store.create_task(role="qa", objective="smoke LAN", actor_id="u:qa")
    team_store.update_task(
        task.id,
        status="failed",
        result={
            "kind": "qa_smoke",
            "ok": False,
            "smoke_script": {"ok": False, "exit_code": 1},
            "health_checks": [],
        },
    )
    failed = team_store.get_task(task.id)
    assert failed is not None
    ids = maybe_spawn_after_qa_failure(failed)
    assert len(ids) >= 1
    msgs = team_messages.list_messages(task_id=task.id)
    assert any(m.kind == "propose" for m in msgs)
    assert any(m.kind == "ack" for m in msgs)


def test_format_bus_aware_summary_lists_owners() -> None:
    text = bus_hooks.format_bus_aware_summary(
        title="Test",
        probes=[{"track": "qa_health", "ok": False, "error": "down"}],
        gaps=[{"owner": "argus", "track": "qa_health", "gap": "down"}],
        followup_ids=["abc"],
        bus_emitted=3,
        memory_lines=["themis: round ok"],
    )
    assert "argus" in text
    assert "message(s) bus" in text
    assert "themis:" in text


def test_agent_for_role_persona() -> None:
    assert bus_hooks.agent_for_role("dev_godot", context={"godot_dev_persona": "hermes"}) == "hermes"
    assert bus_hooks.agent_for_role("dev_game", context={"infographiste_ia": True}) == "pygmalion"
