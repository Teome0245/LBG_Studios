"""Tests ADR 0019 — plan_schema, messages, memory (sans orchestrator.main)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ["LBG_TEAM_DB_PATH"] = ":memory:"
os.environ["LBG_TEAM_MEMORY_ENABLED"] = "1"

from team import memory as team_memory  # noqa: E402
from team import messages as team_messages  # noqa: E402
from team import store as team_store  # noqa: E402
from team.plan_schema import (  # noqa: E402
    sanitize_plan_proposal,
    sanitize_plan_proposals,
    sanitize_payload,
)


@pytest.fixture(autouse=True)
def _reset_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mem = tmp_path / "team_memory.jsonl"
    monkeypatch.setenv("LBG_TEAM_MEMORY_PATH", str(mem))
    monkeypatch.setenv("LBG_TEAM_DB_PATH", ":memory:")
    monkeypatch.setenv("LBG_TEAM_MEMORY_ENABLED", "1")
    team_store.reset_for_tests()


def test_sanitize_plan_proposal_ok() -> None:
    p = sanitize_plan_proposal(
        {
            "role": "qa",
            "objective": "smoke LAN",
            "priority": "high",
            "autonomy": "L1",
            "context": {"godot_supervisor": True, "secret_key": "drop-me"},
            "rationale": "vérif démo",
        }
    )
    assert p.role == "qa"
    assert p.priority == "high"
    assert "godot_supervisor" in p.context
    assert "secret_key" not in p.context


def test_sanitize_plan_proposal_rejects_bad_role() -> None:
    with pytest.raises(ValueError, match="role invalide"):
        sanitize_plan_proposal({"role": "hacker", "objective": "x"})


def test_sanitize_plan_proposal_l2_forces_approval() -> None:
    p = sanitize_plan_proposal(
        {"role": "dev_game", "objective": "build", "autonomy": "L2", "approval_required": False}
    )
    assert p.approval_required is True


def test_sanitize_plan_proposals_partial() -> None:
    ok, errors = sanitize_plan_proposals(
        [
            {"role": "pm", "objective": "brief"},
            {"role": "nope", "objective": "x"},
            "bad",
        ]
    )
    assert len(ok) == 1
    assert len(errors) == 2


def test_sanitize_payload_truncates() -> None:
    payload = sanitize_payload({"note": "x" * 5000, "n": 1, "drop": {"a": 1, "b": "y"}})
    assert len(payload["note"]) <= 2001
    assert payload["n"] == 1
    assert payload["drop"]["a"] == 1


def test_messages_append_and_list() -> None:
    msg = team_messages.append_message(
        from_agent="themis",
        to_agent="argus",
        kind="consult",
        payload={"topic": "smoke"},
        task_id="task-abc",
    )
    assert msg.kind == "consult"
    listed = team_messages.list_messages(task_id="task-abc")
    assert len(listed) == 1
    assert listed[0].from_agent == "themis"


def test_messages_reject_bad_kind() -> None:
    with pytest.raises(ValueError, match="kind invalide"):
        team_messages.append_message(
            from_agent="a", to_agent="b", kind="chat_libre", payload={}
        )


def test_memory_append_and_list(tmp_path: Path) -> None:
    entry = team_memory.append_learning(
        agent_id="argus",
        summary="Smoke LAN vert après sync nginx",
        tags=["smoke", "lan"],
        task_id="t1",
    )
    assert entry.agent_id == "argus"
    path = team_memory.memory_path()
    assert path.is_file()
    learnings = team_memory.list_learnings(agent_id="argus", tag="smoke")
    assert len(learnings) == 1
    assert "nginx" in learnings[0].summary
    top = team_memory.top_learnings_for_plan(limit=3)
    assert top[0]["agent_id"] == "argus"


def test_plan_corpus_fixture_shape() -> None:
    fixture = (
        Path(__file__).resolve().parent / "fixtures" / "plan_corpus.json"
    )
    data = json.loads(fixture.read_text(encoding="utf-8"))
    assert data["schema"] == "team.plan_corpus.v1"
    assert len(data["cases"]) >= 15
    for case in data["cases"]:
        assert case.get("id")
        assert case.get("objective")
        assert case.get("expected_roles") or case.get("expected_roles_any_of")
