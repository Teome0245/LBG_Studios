"""Tests presence Team (mapping + sanitize, sans WS)."""

from __future__ import annotations

from team.models import TeamTask
from team import presence as team_presence


def test_map_task_status():
    assert team_presence.map_task_status("running") == "busy"
    assert team_presence.map_task_status("review") == "review"
    assert team_presence.map_task_status("failed") == "failed"
    assert team_presence.map_task_status("done") == "idle"


def test_sanitize_action_truncates_and_redacts():
    long = "x" * 200
    assert len(team_presence.sanitize_action(long)) <= 120
    red = team_presence.sanitize_action("deploy with api_key=supersecret123 now")
    assert "supersecret123" not in red
    assert "***" in red


def test_emit_from_task_updates_snapshot():
    task = TeamTask(
        id="abcd1234-test",
        role="admin_infra",
        objective="Audit Ollama 111",
        status="running",
        trace_id="tr1",
        context={"host": "192.168.0.111"},
    )
    team_presence.emit_from_task(task, event="status_changed")
    snap = team_presence.snapshot(mode="live")
    assert snap["schema"] == "team.presence.snapshot.v1"
    assert snap["mode"] == "live"
    agents = {a["agent_id"]: a for a in snap["agents"]}
    assert "admin_infra" in agents
    assert agents["admin_infra"]["status"] == "busy"
    assert agents["admin_infra"]["location"] == "zone_llm"
    assert len(agents["admin_infra"]["current_action"]) <= 120
