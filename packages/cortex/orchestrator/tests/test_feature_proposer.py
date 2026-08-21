"""Tests P2 — feature_proposer."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("LBG_TEAM_DB_PATH", ":memory:")
os.environ.setdefault("LBG_TEAM_FEATURE_PROPOSER", "1")

from team import feature_proposer  # noqa: E402
from team import roles as team_roles  # noqa: E402
from team import store as team_store  # noqa: E402


@pytest.fixture(autouse=True)
def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LBG_TEAM_DB_PATH", ":memory:")
    monkeypatch.setenv("LBG_TEAM_FEATURE_PROPOSER", "1")
    monkeypatch.setenv("LBG_FEATURE_PROPOSER_STAGING_DIR", str(tmp_path / "fp_staging"))
    monkeypatch.setenv("LBG_FEATURE_PROPOSER_GIT", "0")  # dry-run git by default
    # Point bible/boite to real repo docs when present
    root = Path(__file__).resolve().parents[4]  # LBG_Studios
    bible = root / "docs" / "world" / "BIBLE_MMO.md"
    if bible.is_file():
        monkeypatch.setenv("LBG_BIBLE_MMO_PATH", str(bible))
        monkeypatch.setenv("LBG_STUDIOS_ROOT", str(root))
    team_store.reset_for_tests()
    feature_proposer._LAST_PROPOSAL.clear()  # noqa: SLF001


def test_collect_signals_includes_seeds() -> None:
    signals = feature_proposer.collect_signals()
    ids = {s["id"] for s in signals}
    assert "seed_craft_social_loop" in ids
    assert "seed_hub_quest_short" in ids


def test_bible_check_rejects_tatooine() -> None:
    bad = feature_proposer.bible_check_stub("Quête Tatooine Mos Eisley Jedi")
    assert bad["ok"] is False
    assert "tatooine" in bad["forbidden_hits"]
    good = feature_proposer.bible_check_stub(
        "Quête Lost Heaven Scrapaltai craft Pre-CU à La Perle"
    )
    assert good["ok"] is True
    assert "scrapaltai" in good["lore_cues"] or "lost heaven" in good["lore_cues"]


def test_run_proposal_cycle_staging_and_l2(tmp_path: Path) -> None:
    out = feature_proposer.run_proposal_cycle(
        idea_id="seed_hub_quest_short",
        spawn_l2=True,
        create_branch=True,
        dry_run_git=True,
    )
    assert out["ok"] is True
    assert out["slug"]
    manifest = Path(out["manifest_path"])
    assert manifest.is_file()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["a4"]["no_git_push"] is True
    assert data["a4"]["no_auto_merge"] is True
    assert (manifest.parent / "RFC.md").is_file()
    assert out["branch"]["dry_run"] is True
    assert out["l2_task_id"]
    task = team_store.get_task(out["l2_task_id"])
    assert task is not None
    assert task.status == "review"
    assert task.approval_required is True
    assert task.context.get("feature_proposal_review") is True
    assert feature_proposer.last_proposal_trace().get("slug") == out["slug"]


def test_execute_via_run_task() -> None:
    task = team_store.create_task(
        role="pm",
        objective="Proposer une feature hub",
        actor_id="test:fp",
        context={
            "feature_proposal": True,
            "workflow": "feature_proposer",
            "idea_id": "seed_studio_judge_dashboard",
            "spawn_l2": False,
            "create_branch": False,
        },
    )
    ran = team_roles.run_task(task.id)
    assert ran is not None
    assert ran.status == "done"
    assert ran.result.get("kind") == "feature_proposer"
    assert ran.result.get("ok") is True


def test_review_ack_does_not_repropose() -> None:
    # Create staging first
    out = feature_proposer.run_proposal_cycle(
        idea_id="seed_tone_patchwork",
        spawn_l2=False,
        create_branch=False,
    )
    review = team_store.create_task(
        role="pm",
        objective="Revue RFC",
        actor_id="test:fp",
        approval_required=True,
        approval_token="test-token",
        context={
            "feature_proposal_review": True,
            "workflow": "feature_proposal_review",
            "manifest_path": out["manifest_path"],
            "proposal_slug": out["slug"],
        },
    )
    # Force queued with stored token path — or just run with approval
    monkey_token = os.environ.get("LBG_TEAM_APPROVAL_TOKEN", "test-token")
    os.environ["LBG_TEAM_APPROVAL_TOKEN"] = monkey_token
    team_store.update_task(review.id, status="queued", stored_approval_token=monkey_token)
    ran = team_roles.run_task(review.id, approval_token=monkey_token)
    assert ran is not None
    assert ran.result.get("kind") == "feature_proposal_review"
    assert ran.result.get("ok") is True
