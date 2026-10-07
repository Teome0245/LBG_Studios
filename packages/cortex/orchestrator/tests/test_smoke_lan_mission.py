"""Tests mission L3 bornée smoke LAN + HITL job format."""

from __future__ import annotations

import time

import pytest


def test_create_tick_dry_run_escalation_path(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    state = tmp_path / "mission.json"
    monkeypatch.setenv("LBG_SMOKE_LAN_MISSION_STATE", str(state))

    from team import smoke_lan_mission

    created = smoke_lan_mission.create_mission(
        days=2,
        budget_retries=3,
        escalate_after_red=2,
        dry_run=False,
    )
    assert created.get("ok") is True
    mid = created["mission"]["id"]

    def fake_pilot(**kwargs):
        return {
            "ok": True,
            "decision": "healthy",
            "summary": "ok",
            "elapsed_ms": 1,
            "dry_run": kwargs.get("dry_run"),
            "steps": [],
        }

    monkeypatch.setattr(
        "team.ops_health_pilot.run_ops_health_pilot",
        fake_pilot,
    )
    tick = smoke_lan_mission.tick_mission(dry_run=True)
    assert tick.get("ok") is True
    assert tick.get("dry_run") is True
    assert tick.get("decision") == "healthy"

    # Live healthy → days_ok++
    tick2 = smoke_lan_mission.tick_mission(dry_run=False)
    assert tick2.get("ok") is True
    assert tick2["mission"]["days_ok"] == 1
    assert tick2["mission"]["id"] == mid

    # Même jour calendaire → pas de double incrément
    tick3 = smoke_lan_mission.tick_mission(dry_run=False)
    assert tick3.get("ok") is True
    assert tick3["mission"]["days_ok"] == 1


def test_escalate_after_consecutive_red(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    state = tmp_path / "mission2.json"
    monkeypatch.setenv("LBG_SMOKE_LAN_MISSION_STATE", str(state))
    from team import smoke_lan_mission

    smoke_lan_mission.create_mission(days=7, budget_retries=10, escalate_after_red=2)

    calls: list[dict] = []

    def fake_pilot(**kwargs):
        calls.append(dict(kwargs))
        if kwargs.get("spawn_l2_remediation"):
            return {
                "ok": True,
                "decision": "remediate",
                "summary": "ko",
                "remediation_task_id": "task-l2-1",
                "steps": [
                    {
                        "id": "remediation_l2",
                        "task_id": "task-l2-1",
                        "hitl": {"ok": True},
                    }
                ],
            }
        return {
            "ok": True,
            "decision": "remediate",
            "summary": "perimeter KO",
            "elapsed_ms": 2,
            "steps": [],
        }

    monkeypatch.setattr("team.ops_health_pilot.run_ops_health_pilot", fake_pilot)
    monkeypatch.setattr(
        "team.lessons_learned.append_lesson",
        lambda **kw: {"id": "lesson-1"},
    )

    t1 = smoke_lan_mission.tick_mission(dry_run=False, notify=False)
    assert t1["mission"]["consecutive_red"] == 1
    assert t1["mission"]["status"] == "active"

    t2 = smoke_lan_mission.tick_mission(dry_run=False, notify=False)
    assert t2.get("escalated") is True
    assert t2["mission"]["status"] == "escalated"
    assert t2["mission"]["l2_task_id"] == "task-l2-1"
    # 2e appel avec spawn_l2
    assert any(c.get("spawn_l2_remediation") for c in calls)

    # Tick suivant : en attente L2, pas de boucle
    t3 = smoke_lan_mission.tick_mission(dry_run=False)
    assert t3.get("decision") == "awaiting_l2"


def test_deadline_done(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    state = tmp_path / "mission3.json"
    monkeypatch.setenv("LBG_SMOKE_LAN_MISSION_STATE", str(state))
    from team import smoke_lan_mission

    out = smoke_lan_mission.create_mission(days=1, dry_run=False)
    m = out["mission"]
    m["days_ok"] = 1
    m["deadline_ts"] = time.time() - 10
    smoke_lan_mission._save({"mission": m, "updated_ts": time.time()})
    tick = smoke_lan_mission.tick_mission(dry_run=False)
    assert tick["mission"]["status"] == "done"


def test_job_l2_format_blocks() -> None:
    from lbg_agents.slack_hitl_format import format_l2_pending_blocks, format_l2_pending_text

    job = {
        "id": "abcd1234ffffeeeeddddccccbbbb9999",
        "kind": "job",
        "capability": "devops_probe",
        "objective": "remediation apply",
    }
    text = format_l2_pending_text(job)
    assert "Job L2" in text
    assert "#/jobs" in text
    blocks = format_l2_pending_blocks(job)
    assert blocks[0]["text"]["text"].startswith("Job L2")
