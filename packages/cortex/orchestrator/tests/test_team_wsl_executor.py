"""Tests pont WSL executor (pull Team) — module pur + routes si app importable."""

from __future__ import annotations

import os

import pytest

os.environ["LBG_TEAM_DB_PATH"] = ":memory:"
os.environ["LBG_WSL_EXECUTOR_TOKEN"] = "test-wsl-token"

from team import store as team_store  # noqa: E402
from team import wsl_executor  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_team_db() -> None:
    team_store._conn = None  # type: ignore[attr-defined]


def test_wsl_health_lists_skills() -> None:
    h = wsl_executor.health()
    assert h["service"] == "wsl_executor"
    assert "diag_godot_supervisor" in h["skills_allowlist"]
    skills = wsl_executor.list_skills()
    assert any(s["id"] == "smoke_godot_owners" for s in skills)


def test_enqueue_poll_complete_wsl_task() -> None:
    task = wsl_executor.enqueue_wsl_task(
        wsl_skill="diag_godot_supervisor",
        objective="Diag Godot depuis WSL test",
        actor_id="test:wsl",
    )
    assert task.status == "queued"

    claimed = wsl_executor.claim_next_wsl_task(executor_id="test-host")
    assert claimed is not None
    assert claimed.id == task.id
    assert claimed.status == "running"
    assert claimed.context.get("wsl_claimed_by") == "test-host"

    assert wsl_executor.claim_next_wsl_task(executor_id="other") is None

    done = wsl_executor.complete_wsl_task(
        task.id,
        ok=True,
        exit_code=0,
        stdout_tail="OK diag",
        executor_id="test-host",
    )
    assert done is not None
    assert done.status == "done"
    assert done.result.get("kind") == "wsl_executor"


def test_unknown_skill_rejected_on_enqueue() -> None:
    with pytest.raises(ValueError, match="hors allowlist"):
        wsl_executor.enqueue_wsl_task(
            wsl_skill="rm_rf_everything",
            objective="nope",
        )


def test_wsl_token_check() -> None:
    assert wsl_executor.check_token("test-wsl-token") is True
    assert wsl_executor.check_token("wrong") is False


@pytest.mark.skipif(
    os.environ.get("LBG_TEST_ORCH_APP") != "1",
    reason="import orchestrator.main nécessite deps legacy complètes",
)
def test_wsl_routes_http() -> None:
    from fastapi.testclient import TestClient

    from orchestrator.main import app  # noqa: WPS433

    client = TestClient(app)
    headers = {"X-LBG-WSL-TOKEN": "test-wsl-token"}
    r = client.get("/v1/team/wsl/health", headers=headers)
    assert r.status_code == 200
    assert r.json()["service"] == "wsl_executor"
