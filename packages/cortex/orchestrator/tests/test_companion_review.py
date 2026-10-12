"""Tests contre-pouvoir Compagnon (déterministe, sans LLM)."""

from __future__ import annotations

from services.companion_review import review_companion_proposal


def test_soft_mail_preview_auto_real():
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
    assert r.auto_real is True
    assert r.auto_dry_run is False
    assert r.source == "deterministic"


def test_soft_open_url_stays_dry_run_not_auto_real():
    r = review_companion_proposal(
        {
            "capability": "desktop_control",
            "risk_level": "high",
            "summary": "Ouvrir Pilot Jobs",
            "action": {"kind": "open_url", "url": "http://192.168.0.140:8080/#/jobs"},
        },
        source_text="ouvre les jobs",
    )
    assert r.pass_ is True
    assert r.block_real is False
    assert r.auto_real is False
    assert r.auto_dry_run is True
    assert r.source == "deterministic"


def test_auto_real_can_be_disabled(monkeypatch):
    monkeypatch.setenv("LBG_COMPANION_AUTO_REAL_SOFT", "0")
    r = review_companion_proposal(
        {"action": {"kind": "mail_imap_preview", "recent": True}, "risk_level": "low"},
        source_text="mails",
    )
    assert r.auto_real is False
    assert r.auto_dry_run is True


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
