"""Tests pipeline LoRA Pygmalion (équipe virtuelle)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

os.environ["LBG_TEAM_DB_PATH"] = ":memory:"
os.environ.setdefault("LBG_DEVOPS_HTTP_ALLOWLIST", "http://127.0.0.1:8010/healthz")

from orchestrator.main import app  # noqa: E402
from team import roles as team_roles  # noqa: E402
from team import store as team_store  # noqa: E402
from team.inspiration_lora_pipeline import pipeline_targets, run_lora_pipeline_step  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_team_db() -> None:
    team_store._conn = None  # type: ignore[attr-defined]
    team_roles.set_dispatch_for_tests(None)


def test_pipeline_targets_defaults() -> None:
    t = pipeline_targets()
    assert t["unclassified_target"] == 200
    assert t["batch_limit"] == 100
    assert "mmorpg_general" in t["styles_to_train"]


def test_lora_pipeline_vision_phase(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    ia = tmp_path / "Infographiste_IA"
    styles = ia / "dataset" / "styles_sorted" / "styles"
    (styles / "unclassified").mkdir(parents=True)
    for i in range(5):
        (styles / "unclassified" / f"img{i}.jpg").write_bytes(b"x")
    (ia / "orchestrator.py").write_text("# stub\n", encoding="utf-8")
    (ia / "config").mkdir()
    (ia / "config" / "art_styles.json").write_text('{"styles": {}}', encoding="utf-8")

    monkeypatch.setenv("LBG_INFOGRAPHISTE_IA_ROOT", str(ia))
    monkeypatch.setenv("LBG_LORA_VISION_UNCLASSIFIED_TARGET", "2")
    monkeypatch.setenv("LBG_TEAM_INFOGRAPHISTE_LORA_STATE", str(tmp_path / "lora.json"))

    with patch("team.inspiration_lora_pipeline.run_vision_classify_batch") as vision, patch(
        "team.inspiration_lora_pipeline.run_prepare_styles_sorted"
    ) as prep, patch("team.inspiration_lora_pipeline.count_sorted_buckets") as buckets:
        buckets.side_effect = [
            {"unclassified": 5, "mmorpg_general": 0},
            {"unclassified": 3, "mmorpg_general": 2},
        ]
        vision.return_value = {"ok": True, "scanned": 2}
        prep.return_value = {"ok": True, "styles": {"mmorpg_general": {"ok": True}}}

        out = run_lora_pipeline_step(persist_state=True)

    assert out["phase"] == "vision_batch"
    assert out["unclassified"] == 3
    vision.assert_called_once()
    prep.assert_called_once()
    assert (tmp_path / "lora.json").is_file()


def test_team_run_infographiste_lora_workflow(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_pipeline = {
        "ok": True,
        "phase": "vision_batch",
        "unclassified": 1200,
        "buckets": {"unclassified": 1200},
        "steps": [],
    }
    monkeypatch.setattr(
        "team.infographiste_lora_workflow.run_lora_pipeline_step",
        lambda **_: fake_pipeline,
    )

    client = TestClient(app)
    created = client.post(
        "/v1/team/tasks",
        json={
            "role": "dev_game",
            "objective": "Pipeline LoRA vision unclassified mmorpg_insp",
            "actor_id": "u:pygmalion",
            "context": {"lora_pipeline": True, "infographiste_ia": True},
        },
    ).json()
    ran = client.post(f"/v1/team/tasks/{created['id']}/run").json()
    assert ran["status"] == "done"
    res = ran["result"]
    assert res["kind"] == "infographiste_lora_workflow"
    assert res["ok"] is True
    assert res["pipeline"]["phase"] == "vision_batch"
