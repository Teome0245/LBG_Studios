"""Tests unitaires cursor_agent — sans importer orchestrator.main (legacy)."""

from __future__ import annotations

import os

import pytest

from integrations import cursor_agent as cursor


def test_health_shape() -> None:
    h = cursor.health()
    assert h["service"] == "cursor_cloud_agent"
    assert "enabled" in h
    assert "api_key_configured" in h
    assert "repos_allowlist" in h
    assert "sdk_installed" in h
    assert "ready" in h


def test_repos_allowlist_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_CURSOR_AGENT_REPOS", "Teome0245/LBG_Studios, Teome0245/new_mmo")
    assert cursor.repos_allowlist() == ["Teome0245/LBG_Studios", "Teome0245/new_mmo"]


def test_launch_dry_run_repo_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_CURSOR_AGENT_ENABLED", "1")
    monkeypatch.setenv("CURSOR_API_KEY", "cursor_test_key")
    monkeypatch.setenv("LBG_CURSOR_AGENT_REPOS", "Teome0245/LBG_Studios")
    preview = cursor.launch_agent_dry_run(
        prompt="Documenter X",
        repository="Teome0245/other_repo",
    )
    assert preview["dry_run"] is True
    assert preview["repo_allowed"] is False


def test_launch_dry_run_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_CURSOR_AGENT_ENABLED", "1")
    monkeypatch.setenv("CURSOR_API_KEY", "cursor_test_key")
    monkeypatch.setenv("LBG_CURSOR_AGENT_REPOS", "Teome0245/LBG_Studios")
    preview = cursor.launch_agent_dry_run(
        prompt="Documenter X",
        repository="Teome0245/LBG_Studios",
    )
    assert preview["repo_allowed"] is True
    assert preview["prompt_preview"].startswith("Documenter")


def test_launch_real_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LBG_CURSOR_AGENT_ENABLED", raising=False)
    out = cursor.launch_cloud_agent(
        prompt="fix bug",
        repository="Teome0245/LBG_Studios",
    )
    assert out["ok"] is False
    assert "LBG_CURSOR_AGENT_ENABLED" in out["error"]


def test_launch_real_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_CURSOR_AGENT_ENABLED", "1")
    monkeypatch.delenv("CURSOR_API_KEY", raising=False)
    out = cursor.launch_cloud_agent(
        prompt="fix bug",
        repository="Teome0245/LBG_Studios",
    )
    assert out["ok"] is False
    assert "CURSOR_API_KEY" in out["error"]
