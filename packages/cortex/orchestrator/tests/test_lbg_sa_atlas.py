"""Tests mémoire Atlas + workflow admin_infra (LBG_SA)."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from lbg_sa.atlas_memory import build_atlas_learning_summary, recall_atlas_hints, record_atlas_admin_infra_run
from lbg_sa.memory_store import reset_memory_cache_for_tests
from main import app
from team import roles as team_roles


@pytest.fixture(autouse=True)
def _memory_env(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    reset_memory_cache_for_tests()
    monkeypatch.setenv("LBG_TEAM_DB_PATH", ":memory:")
    monkeypatch.setenv("LBG_STUDIOS_AGENTS_MEMORY_ROOT", str(tmp_path / "mem"))
    monkeypatch.setenv("LBG_STUDIOS_AGENTS_MEMORY_ENABLED", "1")
    os.environ["LBG_TEAM_DB_PATH"] = ":memory:"


def test_build_atlas_summary_includes_gaps() -> None:
    text = build_atlas_learning_summary(
        platform={"hosts_ok": 3, "hosts_total": 4, "perimeter": ["110", "140"], "gaps": ["245 KO"]},
        ollama={"ok": True, "track": "ollama_audit_110"},
        workflow_ok=False,
    )
    assert "245 KO" in text
    assert "attention" in text


def test_record_and_recall_atlas() -> None:
    rec = record_atlas_admin_infra_run(
        "t-1",
        platform={"hosts_ok": 4, "hosts_total": 4, "perimeter": ["110"], "gaps": []},
        ollama={"ok": True, "track": "ollama_audit_110"},
        workflow_ok=True,
    )
    assert rec.get("recorded") is True
    hints = recall_atlas_hints()
    assert hints.get("entries", 0) >= 1
    assert "Atlas run" in str(hints.get("hints"))


def test_admin_infra_run_includes_lbg_sa_memory(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_dispatch(routed_to, *, actor_id, text, context):  # noqa: ANN001
        return {"ok": True, "agent": routed_to}

    monkeypatch.setattr(
        "team.admin_infra_workflow.audit_ollama_lan",
        lambda **kw: {"ok": True, "track": "ollama_audit_110", "recommendations": [], "gaps": []},
    )
    monkeypatch.setattr(
        "team.admin_infra_workflow.audit_admin_infra_platform",
        lambda: {
            "ok": True,
            "track": "admin_infra_platform",
            "hosts_ok": 4,
            "hosts_total": 4,
            "perimeter": ["110", "140", "245", "246"],
            "gaps": [],
            "ollama_primary": {"ok": True},
        },
    )
    monkeypatch.setattr(
        "team.admin_infra_workflow.maybe_notify_perimeter_ko",
        lambda platform: {"skipped": "test"},
    )
    team_roles.set_dispatch_for_tests(fake_dispatch)
    client = TestClient(app)
    created = client.post(
        "/v1/team/tasks",
        json={"role": "admin_infra", "objective": "lbg_sa atlas", "actor_id": "u:test"},
    ).json()
    ran = client.post(f"/v1/team/tasks/{created['id']}/run").json()
    assert ran["status"] == "done"
    mem = ran["result"].get("lbg_sa_memory") or {}
    assert mem.get("record", {}).get("recorded") is True
