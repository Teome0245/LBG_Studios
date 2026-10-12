"""Tests HITL Slack L2."""

from __future__ import annotations

from lbg_agents.slack_hitl import parse_hitl_command, is_allowed, handle_hitl_action
from lbg_agents.slack_hitl_format import format_l2_pending_blocks, format_l2_pending_text, short_task_id


def test_short_task_id() -> None:
    assert short_task_id("abcdef12-3456-7890") == "abcdef12"


def test_parse_approve_valider() -> None:
    assert parse_hitl_command("approve abcdef12") == ("approve", "abcdef12")
    assert parse_hitl_command("valider deadbeef") == ("approve", "deadbeef")
    assert parse_hitl_command("reject abcdef12") == ("reject", "abcdef12")
    assert parse_hitl_command("hello") is None


def test_allowlist(monkeypatch) -> None:
    monkeypatch.setenv("LBG_SLACK_ALLOWLIST", "U111,U222")
    assert is_allowed("U111")
    assert not is_allowed("U999")


def test_format_blocks_has_actions() -> None:
    task = {
        "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "role": "ops",
        "role_alias": "Héphaïstos",
        "objective": "Restart service X",
    }
    text = format_l2_pending_text(task)
    assert "approve aaaaaaaa" in text
    blocks = format_l2_pending_blocks(task)
    actions = [b for b in blocks if b.get("type") == "actions"]
    assert actions
    ids = {el["action_id"] for el in actions[0]["elements"]}
    assert "lbg_l2_approve" in ids
    assert "lbg_l2_reject" in ids


def test_format_job_payload_links_jobs() -> None:
    job = {
        "id": "bbbbbbbb-cccc-dddd-eeee-ffffffffffff",
        "kind": "job",
        "capability": "desktop_control",
        "objective": "open notepad",
    }
    text = format_l2_pending_text(job)
    assert "Job L2" in text
    assert "#/jobs" in text
    blocks = format_l2_pending_blocks(job)
    pilot_btn = [
        el
        for b in blocks
        if b.get("type") == "actions"
        for el in b.get("elements") or []
        if el.get("action_id") == "lbg_l2_pilot"
    ]
    assert pilot_btn and "#/jobs" in pilot_btn[0].get("url", "")


def test_handle_hitl_not_allowlisted(monkeypatch) -> None:
    monkeypatch.setenv("LBG_SLACK_ALLOWLIST", "UONLY")
    monkeypatch.setenv("LBG_SLACK_HITL", "1")
    out = handle_hitl_action(action="approve", task_ref="abc", user_id="UOTHER")
    assert out.get("ok") is False
    assert out.get("error") == "user_not_allowlisted"
