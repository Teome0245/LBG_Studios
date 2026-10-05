"""Tests Fleet + Ops Health Pilot (plan gaps A2/A4/B1)."""

from __future__ import annotations

import os

import pytest

os.environ["LBG_TEAM_DB_PATH"] = ":memory:"
os.environ.setdefault("LBG_TEAM_ENABLED", "1")
os.environ.setdefault(
    "LBG_DEVOPS_HTTP_ALLOWLIST",
    "http://127.0.0.1:8010/healthz,http://127.0.0.1:8000/healthz",
)

from team import fleet as team_fleet  # noqa: E402
from team import ops_health_pilot  # noqa: E402
from team import store as team_store  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_team_db(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    team_store._conn = None  # type: ignore[attr-defined]
    monkeypatch.setenv("LBG_TEAM_DB_PATH", ":memory:")
    # Éviter écriture lessons / alertes pendant dry-run tests
    monkeypatch.setenv("LBG_TEAM_LESSONS_ENABLED", "0")


def test_fleet_snapshot_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "team.admin_infra_platform.audit_admin_infra_platform",
        lambda: {"perimeter": ["140"], "hosts": [], "gaps": []},
        raising=False,
    )
    snap = team_fleet.fleet_snapshot()
    assert snap.get("ok") is True
    assert "agents" in snap
    assert "metrics" in snap
    assert "jobs" in snap
    assert "team" in snap
    assert "flags" in snap
    m = snap["metrics"]
    assert "team_l2_pending" in m
    assert "jobs_waiting_approval" in m
    assert "jobs_by_status" in m


def test_fleet_includes_l2_pending() -> None:
    task = team_store.create_task(
        role="ops",
        objective="remediation test L2",
        actor_id="test:fleet",
        approval_required=True,
    )
    assert task.status == "review"
    snap = team_fleet.fleet_snapshot()
    pending = (snap.get("team") or {}).get("l2_pending") or []
    ids = {p.get("id") for p in pending}
    assert task.id in ids


def test_ops_health_pilot_dry_run(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("LBG_OPS_HEALTH_PILOT_STATE", str(tmp_path / "state.json"))
    monkeypatch.setattr(
        "team.admin_infra_platform.audit_admin_infra_platform",
        lambda: {
            "perimeter": ["140", "246"],
            "hosts": [
                {
                    "ok": True,
                    "required": True,
                    "perimeter_id": "140",
                    "label": "Core",
                    "host": "192.168.0.140",
                },
                {
                    "ok": False,
                    "required": False,
                    "perimeter_id": "245",
                    "label": "PreCU",
                    "host": "192.168.0.245",
                },
            ],
            "gaps": ["ollama-config: soft ignored"],
        },
    )
    # Ne plus mocker perimeter_has_ko : 245 OFF + gaps soft → healthy
    out = ops_health_pilot.run_ops_health_pilot(dry_run=True, notify=False, persist=True)
    assert out.get("ok") is True
    assert out.get("dry_run") is True
    assert out.get("decision") == "healthy"
    step_ids = [s.get("id") for s in (out.get("steps") or [])]
    assert step_ids == [
        "perception",
        "diagnostic",
        "decision",
        "remediation_l2",
        "notify",
        "lesson",
    ]


def test_ops_health_pilot_dry_run_ko_would_spawn(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("LBG_OPS_HEALTH_PILOT_STATE", str(tmp_path / "state.json"))
    monkeypatch.setattr(
        "team.admin_infra_platform.audit_admin_infra_platform",
        lambda: {
            "perimeter": ["140"],
            "hosts": [
                {
                    "ok": False,
                    "perimeter_id": "140",
                    "label": "Core",
                    "host": "192.168.0.140",
                }
            ],
            "gaps": ["140: core probe KO"],
        },
    )
    monkeypatch.setattr(
        "team.admin_infra_element.perimeter_has_ko",
        lambda platform: True,
    )
    out = ops_health_pilot.run_ops_health_pilot(
        dry_run=True, notify=True, spawn_l2_remediation=True, persist=True
    )
    assert out.get("decision") == "remediate"
    rem = next(s for s in out["steps"] if s["id"] == "remediation_l2")
    assert rem.get("skipped") is True
    assert rem.get("would_create", {}).get("approval_required") is True
    # dry-run → aucune tâche créée
    tasks = team_store.list_tasks(limit=50)
    assert not any((t.context or {}).get("ops_health_pilot") for t in tasks)
    assert ops_health_pilot.last_run().get("decision") == "remediate"


def test_ops_health_pilot_live_ko_spawns_l2(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("LBG_OPS_HEALTH_PILOT_STATE", str(tmp_path / "state.json"))
    monkeypatch.setenv("LBG_TEAM_LESSONS_ENABLED", "1")
    monkeypatch.setenv("LBG_TEAM_LESSONS_PATH", str(tmp_path / "lessons.json"))
    monkeypatch.setattr(
        "team.admin_infra_platform.audit_admin_infra_platform",
        lambda: {
            "perimeter": ["140"],
            "hosts": [{"ok": False, "perimeter_id": "140", "label": "Core", "host": "x"}],
            "gaps": ["140 ko"],
        },
    )
    monkeypatch.setattr("team.admin_infra_element.perimeter_has_ko", lambda platform: True)
    monkeypatch.setattr(
        "lbg_agents.ops_notify.send_text",
        lambda msg, **kw: {"ok": True, "backend": "test", "skipped": False},
    )
    monkeypatch.setattr(
        "lbg_agents.ops_notify.send_l2_pending",
        lambda task: {"ok": True, "kind": "l2_pending", "task_id": task.get("id")},
    )
    out = ops_health_pilot.run_ops_health_pilot(dry_run=False, notify=True, persist=True)
    assert out.get("decision") == "remediate"
    assert out.get("remediation_task_id")
    rem = next(s for s in out["steps"] if s["id"] == "remediation_l2")
    assert rem.get("task_id") == out["remediation_task_id"]
    assert rem.get("hitl", {}).get("ok") is True
    # dedup second live run
    out2 = ops_health_pilot.run_ops_health_pilot(dry_run=False, notify=False, persist=True)
    rem2 = next(s for s in out2["steps"] if s["id"] == "remediation_l2")
    assert rem2.get("deduped") is True
    assert rem2.get("task_id") == out["remediation_task_id"]
