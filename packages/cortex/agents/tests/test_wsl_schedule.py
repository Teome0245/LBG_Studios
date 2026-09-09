"""Tests fenêtre WSL (nuit 22h→7h) + skip jobs Pygmalion."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from lbg_agents.wsl_schedule import (
    in_quiet_hours,
    should_skip_wsl_dependent_job,
)


def test_quiet_hours_paris_night() -> None:
    tz = ZoneInfo("Europe/Paris")
    assert in_quiet_hours(datetime(2026, 9, 5, 23, 0, tzinfo=tz)) is True
    assert in_quiet_hours(datetime(2026, 9, 5, 3, 0, tzinfo=tz)) is True
    assert in_quiet_hours(datetime(2026, 9, 5, 7, 0, tzinfo=tz)) is False
    assert in_quiet_hours(datetime(2026, 9, 5, 14, 0, tzinfo=tz)) is False
    assert in_quiet_hours(datetime(2026, 9, 5, 21, 59, tzinfo=tz)) is False


def test_skip_during_quiet_hours_without_probe(monkeypatch) -> None:
    monkeypatch.setenv("LBG_WSL_TZ", "Europe/Paris")
    tz = ZoneInfo("Europe/Paris")
    night = datetime(2026, 9, 5, 23, 30, tzinfo=tz)
    out = should_skip_wsl_dependent_job(now=night, probe_reachability=False)
    assert out["skip"] is True
    assert out["outcome"] == "wsl_quiet_hours"


def test_force_bypasses_quiet_hours(monkeypatch) -> None:
    monkeypatch.setenv("LBG_WSL_FORCE", "1")
    tz = ZoneInfo("Europe/Paris")
    night = datetime(2026, 9, 5, 23, 30, tzinfo=tz)
    out = should_skip_wsl_dependent_job(now=night, probe_reachability=False)
    assert out["skip"] is False
    assert out["outcome"] == "forced"
