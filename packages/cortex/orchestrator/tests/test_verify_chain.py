"""Tests verify_chain (smoke Argus) + non-régression mutator/proposer."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("LBG_TEAM_DB_PATH", ":memory:")

from team import feature_proposer  # noqa: E402
from team import store as team_store  # noqa: E402
from team import verify_chain  # noqa: E402


@pytest.fixture(autouse=True)
def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LBG_TEAM_DB_PATH", ":memory:")
    monkeypatch.setenv("LBG_TEAM_VERIFY_SMOKE_CHAIN", "1")
    monkeypatch.setenv("LBG_TEAM_VERIFY_SMOKE_AUTO_RUN", "0")
    monkeypatch.setenv("LBG_TEAM_FEATURE_PROPOSER", "1")
    monkeypatch.setenv("LBG_FEATURE_PROPOSER_STAGING_DIR", str(tmp_path / "fp"))
    monkeypatch.setenv("LBG_FEATURE_PROPOSER_GIT", "0")
    root = Path(__file__).resolve().parents[4]
    bible = root / "docs" / "world" / "BIBLE_MMO.md"
    if bible.is_file():
        monkeypatch.setenv("LBG_BIBLE_MMO_PATH", str(bible))
        monkeypatch.setenv("LBG_STUDIOS_ROOT", str(root))
    team_store.reset_for_tests()


def test_spawn_argus_smoke_creates_qa_task() -> None:
    out = verify_chain.maybe_spawn_argus_smoke(
        parent_kind="feature_proposer",
        parent_ref="seed-test",
        manifest_path="/tmp/manifest.json",
    )
    assert out["ok"] is True
    assert out["smoke_task_id"]
    task = team_store.get_task(out["smoke_task_id"])
    assert task is not None
    assert task.role == "qa"
    assert task.approval_required is False
    assert task.context.get("verify_chain") is True
    assert task.context.get("verify_parent_kind") == "feature_proposer"


def test_feature_proposer_includes_smoke_chain() -> None:
    out = feature_proposer.run_proposal_cycle(
        idea_id="seed_studio_judge_dashboard",
        spawn_l2=False,
        create_branch=False,
    )
    assert out["ok"] is True
    assert out.get("smoke_task_id")
    smoke = team_store.get_task(out["smoke_task_id"])
    assert smoke is not None
    assert smoke.role == "qa"


def test_verify_smoke_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_TEAM_VERIFY_SMOKE_CHAIN", "0")
    out = verify_chain.maybe_spawn_argus_smoke(parent_kind="x")
    assert out.get("skipped") is True
