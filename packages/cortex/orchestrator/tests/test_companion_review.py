"""Tests contre-pouvoir Compagnon (déterministe, sans LLM)."""

from __future__ import annotations

from services.companion_review import review_companion_proposal


def test_soft_mail_preview_auto_dry_run():
    r = review_companion_proposal(
        {
            "capability": "desktop_control",
            "risk_level": "high",
            "summary": "Mails récents",
            "action": {"kind": "mail_imap_preview", "recent": True},
        },
        source_text="regarde mes mails",
    )
    assert r.pass_ is True
    assert r.block_real is False
    assert r.auto_dry_run is True
    assert r.source == "deterministic"


def test_hard_fix_session0_blocks_real():
    r = review_companion_proposal(
        {
            "capability": "desktop_control",
            "risk_level": "high",
            "summary": "Réparer Session 0",
            "action": {"kind": "fix_session0"},
        },
        source_text="répare session 0",
    )
    assert r.pass_ is True
    assert r.block_real is True
    assert r.auto_dry_run is True


def test_review_disabled(monkeypatch):
    monkeypatch.setenv("LBG_COMPANION_REVIEW", "0")
    r = review_companion_proposal({"action": {"kind": "open_app", "app": "notepad"}}, source_text="x")
    assert r.source == "fallback"
    assert r.block_real is False
