"""Tests pour la boucle de contrôle des failed et relance sécurisée."""

import pytest
from team import store as team_store
from team.failure_followup import (
    control_check_before_retry,
    maybe_spawn_after_failure,
    max_retries,
)


def test_failure_followup_creates_pm_and_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_TEAM_FAILURE_FOLLOWUP_ENABLED", "1")
    monkeypatch.setenv("LBG_TEAM_FAILURE_RETRY", "1")
    monkeypatch.setenv("LBG_TEAM_FAILURE_MAX_RETRIES", "2")

    task = team_store.create_task(
        role="ops",
        objective="Sonde storage",
        actor_id="system:test",
    )
    team_store.update_task(
        task.id,
        status="failed",
        result={"kind": "ops", "ok": False, "error": "timeout connection"},
    )
    refreshed = team_store.get_task(task.id)
    assert refreshed is not None

    child_ids = maybe_spawn_after_failure(refreshed)
    assert len(child_ids) == 2

    pm_task = team_store.get_task(child_ids[0])
    retry_task = team_store.get_task(child_ids[1])

    assert pm_task is not None and pm_task.role == "pm"
    assert retry_task is not None and retry_task.role == "ops"
    assert retry_task.context.get("_failure_retry") is True
    assert retry_task.context.get("retry_count") == 1


def test_failure_retry_stops_at_max_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_TEAM_FAILURE_FOLLOWUP_ENABLED", "1")
    monkeypatch.setenv("LBG_TEAM_FAILURE_RETRY", "1")
    monkeypatch.setenv("LBG_TEAM_FAILURE_MAX_RETRIES", "2")

    task = team_store.create_task(
        role="ops",
        objective="Sonde storage",
        actor_id="system:test",
        context={"_failure_retry": True, "retry_count": 2},
    )
    team_store.update_task(
        task.id,
        status="failed",
        result={"kind": "ops", "ok": False, "error": "timeout"},
    )
    refreshed = team_store.get_task(task.id)
    assert refreshed is not None

    # Plafond atteint (2/2) -> pas de nouveau spawn
    child_ids = maybe_spawn_after_failure(refreshed)
    assert child_ids == []


def test_control_check_blocks_permanent_code_errors() -> None:
    task = team_store.create_task(
        role="dev_game",
        objective="Script export",
        actor_id="system:test",
        context={
            "_failure_retry": True,
            "failure_summary": {"error": "FileNotFoundError: export_scrapaltai_for_godot.py manquant"},
        },
    )
    should_run, reason = control_check_before_retry(task)
    assert should_run is False
    assert "permanent_code_error" in reason


def test_control_check_approves_transient_retry() -> None:
    task = team_store.create_task(
        role="qa",
        objective="Smoke LAN",
        actor_id="system:test",
        context={
            "_failure_retry": True,
            "failure_summary": {"error": "Smoke assertion failed on ephemeral metric"},
        },
    )
    should_run, reason = control_check_before_retry(task)
    assert should_run is True
    assert "transient" in reason
