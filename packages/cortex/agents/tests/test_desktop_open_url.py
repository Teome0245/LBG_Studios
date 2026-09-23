"""Tests action desktop open_url (exécuteur local, dry-run)."""

from __future__ import annotations

import pytest

from lbg_agents.desktop_executor import run_desktop_action


def test_open_url_allowlist_denied_without_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LBG_DESKTOP_URL_ALLOWLIST", raising=False)
    monkeypatch.delenv("LBG_DESKTOP_URL_HOST_ALLOWLIST", raising=False)
    out = run_desktop_action(
        actor_id="a",
        text="t",
        action={"kind": "open_url", "url": "https://example.org/"},
        context={"desktop_dry_run": True},
    )
    assert out.get("ok") is False
    assert out.get("outcome") == "allowlist_denied"


def test_open_url_dry_run_with_host_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_DESKTOP_URL_HOST_ALLOWLIST", "example.org")
    monkeypatch.delenv("LBG_DESKTOP_DRY_RUN", raising=False)
    monkeypatch.delenv("LBG_DESKTOP_URL_ALLOW_LAN", raising=False)
    out = run_desktop_action(
        actor_id="a",
        text="t",
        action={"kind": "open_url", "url": "https://example.org/foo"},
        context={"desktop_dry_run": True},
    )
    assert out.get("ok") is True
    assert out.get("outcome") == "dry_run"
    assert out.get("url") == "https://example.org/foo"


def test_open_url_lan_allow_and_normalize(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LBG_DESKTOP_URL_ALLOWLIST", raising=False)
    monkeypatch.delenv("LBG_DESKTOP_URL_HOST_ALLOWLIST", raising=False)
    monkeypatch.setenv("LBG_DESKTOP_URL_ALLOW_LAN", "1")
    monkeypatch.delenv("LBG_DESKTOP_DRY_RUN", raising=False)
    out = run_desktop_action(
        actor_id="a",
        text="t",
        action={"kind": "open_url", "url": "192.168.0.140:8080"},
        context={"desktop_dry_run": True},
    )
    assert out.get("ok") is True
    assert out.get("outcome") == "dry_run"
    assert out.get("url") == "http://192.168.0.140:8080"


def test_context_dry_run_wins_over_env_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    """LBG_DESKTOP_DRY_RUN=0 ne doit pas bloquer context.desktop_dry_run (Agir / Pilot)."""
    from lbg_agents.desktop_executor import desktop_dry_run

    monkeypatch.setenv("LBG_DESKTOP_DRY_RUN", "0")
    assert desktop_dry_run({"desktop_dry_run": True}) is True
    assert desktop_dry_run({}) is False
    monkeypatch.setenv("LBG_DESKTOP_DRY_RUN", "1")
    assert desktop_dry_run({}) is True
