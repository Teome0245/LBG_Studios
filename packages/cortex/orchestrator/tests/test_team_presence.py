"""Tests presence Team (mapping + sanitize, sans WS)."""

from __future__ import annotations

from team.models import TeamTask
from team import presence as team_presence


def test_map_task_status():
    assert team_presence.map_task_status("running") == "busy"
    assert team_presence.map_task_status("review") == "review"
    assert team_presence.map_task_status("failed") == "failed"
    assert team_presence.map_task_status("done") == "idle"
    assert team_presence.map_task_status("queued") == "idle"
    assert team_presence.map_task_status("queued", approval_required=True) == "review"
    assert team_presence.map_task_status("queued", approval_required=True, approved=True) == "review"
    assert team_presence.map_task_status("waiting_approval", approval_required=True) == "review"



def test_presence_l2_queued_shows_review():
    task = TeamTask(
        id="l2-queued-test",
        role="dev_game",
        objective="Ouvre une PR Core3",
        status="queued",
        approval_required=True,
        trace_id="tr-l2",
        context={"cursor_cloud_agent": True},
    )
    team_presence.emit_from_task(task, event="status_changed")
    snap = team_presence.snapshot(mode="live")
    agents = {a["agent_id"]: a for a in snap["agents"]}
    # résolu vers un agent du rôle (Vulcan/Dédale selon registre)
    matches = [a for a in agents.values() if a.get("task_id") == "l2-queued-test"]
    assert matches, "agent lié à la tâche L2 attendu"
    assert matches[0]["status"] == "review"
    assert matches[0].get("approval_required") is True
    assert matches[0].get("awaiting_human_approval") is True
    assert matches[0].get("awaiting_run") is False


def test_presence_reconcile_clears_done_ghost(monkeypatch):
    """Pastille PRÊT fantôme si la tâche est déjà done en store."""
    ghost = TeamTask(
        id="ghost-done-l2",
        role="pm",
        objective="Revue L2 — Feature proposal fantôme",
        status="queued",
        approval_required=True,
        stored_approval_token="tok",
        context={"approved": True, "feature_proposal_review": True},
    )
    team_presence.emit_from_task(ghost, event="status_changed")
    matches0 = [
        a
        for a in team_presence.snapshot(mode="live")["agents"]
        if a.get("task_id") == "ghost-done-l2"
    ]
    assert matches0 and matches0[0].get("awaiting_run") is True

    done = TeamTask(
        id="ghost-done-l2",
        role="pm",
        objective="Revue L2 — Feature proposal fantôme",
        status="done",
        approval_required=True,
        context={"approved": True},
        result={"ok": True, "kind": "feature_proposal_review"},
    )

    import team.store as ts

    monkeypatch.setattr(ts, "get_task", lambda tid: done if tid == "ghost-done-l2" else None)

    n = team_presence.reconcile_with_store()
    assert n >= 1
    matches = [
        a
        for a in team_presence.snapshot(mode="live")["agents"]
        if a.get("task_id") == "ghost-done-l2"
    ]
    assert not matches
    themis = [
        a
        for a in team_presence.snapshot(mode="live")["agents"]
        if a.get("agent_id") == "studio_pm_themis" or a.get("display_name") == "Thémis"
    ]
    assert themis
    assert themis[0]["status"] == "idle"
    assert themis[0].get("awaiting_run") in (False, None)



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
    matches = [a for a in snap["agents"] if a.get("task_id") == "abcd1234-test"]
    assert matches, "agent lié à la tâche attendu"
    assert matches[0]["status"] == "busy"
    assert matches[0]["location"] == "zone_llm"
    assert len(matches[0]["current_action"]) <= 120
