"""Tests rapport superviseur Godot (blocking vs advisory)."""

from __future__ import annotations

import os

import pytest

os.environ["LBG_TEAM_DB_PATH"] = ":memory:"

from team.godot_supervisor_report import build_supervisor_report  # noqa: E402


def test_blocking_only_sidecar_mirror() -> None:
    tracks = [
        {"track": "sidecar_m1", "ok": False, "sidecar": "http://246:8791", "online_count": 0, "checks": []},
        {"track": "godot_mirror_m1", "ok": False, "entities": 0},
        {"track": "lbg_ws2_readiness", "ok": False, "checks": {}, "gaps": ["zone_state_v2"]},
        {"track": "zb0_readiness", "ok": False, "gaps": ["LbgZoneBridge.h absent (ZB-0)"], "checks": {}},
        {"track": "infographiste_assets", "ok": False, "hint": "manifest absent"},
    ]
    report = build_supervisor_report(tracks=tracks, sidecar_ok=False, mode="full")
    assert report["ok"] is False
    assert "sidecar_m1" in report["blocking_failed"]
    assert "godot_mirror_m1" in report["blocking_failed"]
    assert "lbg_ws2_readiness" in report["advisory_failed"]
    assert "zb0_readiness" in report["advisory_failed"]
    assert "sidecar_m1" in report["human_summary"]
    assert "Bloquant" in report["human_summary"]


def test_advisory_only_passes_ok() -> None:
    tracks = [
        {"track": "sidecar_m1", "ok": True, "online_count": 2, "checks": []},
        {"track": "godot_mirror_m1", "ok": True, "entities": 2},
        {"track": "lbg_ws2_readiness", "ok": True, "checks": {}, "gaps": []},
        {"track": "zb0_readiness", "ok": False, "gaps": ["hook ZoneServer"], "checks": {}},
    ]
    report = build_supervisor_report(tracks=tracks, sidecar_ok=True, mode="full")
    assert report["ok"] is True
    assert report["blocking_failed"] == []
    assert "zb0_readiness" in report["advisory_failed"]


def test_sidecar_line_shows_healthz() -> None:
    tracks = [
        {
            "track": "sidecar_m1",
            "ok": False,
            "sidecar": "http://192.168.0.246:8791",
            "checks": [{"kind": "sidecar_healthz", "ok": False, "error": "Connection refused"}],
        },
    ]
    report = build_supervisor_report(tracks=tracks, sidecar_ok=False)
    assert "healthz KO" in report["human_summary"]
    assert "Connection refused" in report["human_summary"]


def test_godot_followup_skips_advisory_only(monkeypatch: pytest.MonkeyPatch) -> None:
    os.environ["LBG_TEAM_FOLLOWUP_STATE"] = ":memory:"
    from team import store as team_store
    from team.godot_followup import maybe_spawn_after_godot_failure

    team_store._conn = None  # type: ignore[attr-defined]
    task = team_store.create_task(role="qa", objective="supervise", actor_id="system:team")
    team_store.update_task(
        task.id,
        status="failed",
        result={
            "kind": "godot_supervisor",
            "ok": False,
            "blocking_failed": [],
            "advisory_failed": ["zb0_readiness"],
            "tracks": [{"track": "zb0_readiness", "ok": False}],
        },
    )
    refreshed = team_store.get_task(task.id)
    assert refreshed is not None
    assert maybe_spawn_after_godot_failure(refreshed) == []
    again = team_store.get_task(task.id)
    assert again is not None
    assert again.context.get("_godot_followup_suppressed") == "advisory_only"
