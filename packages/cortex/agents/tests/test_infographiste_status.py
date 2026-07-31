"""Tests statut LoRA factuel + classifieur."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Autocomplete imports both packages
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "agents" / "src"))
sys.path.insert(0, str(ROOT / "orchestrator"))

from introspection.deterministic_classifier import DeterministicIntentClassifier  # noqa: E402
from lbg_agents.infographiste_status import run_infographiste_status  # noqa: E402


def test_classifier_lora_before_dialogue() -> None:
    c = DeterministicIntentClassifier()
    intent, conf = c.classify("où on en est des entraînements LoRA et du tri des images ?")
    assert intent == "infographiste_status"
    assert conf >= 0.9


def test_classifier_pygmalion() -> None:
    c = DeterministicIntentClassifier()
    intent, _ = c.classify("statut pygmalion pipeline inspiration")
    assert intent == "infographiste_status"


def test_format_reply_includes_phase(tmp_path: Path, monkeypatch) -> None:
    state = tmp_path / "lora.json"
    state.write_text(
        json.dumps({"last_phase": "vision_batch", "last_unclassified": 1200, "batches_total": 9}),
        encoding="utf-8",
    )
    monkeypatch.setenv("LBG_TEAM_INFOGRAPHISTE_LORA_STATE", str(state))
    monkeypatch.setenv("LBG_ORCHESTRATOR_URL", "http://127.0.0.1:9")
    out = run_infographiste_status(actor_id="u:t", text="LoRA ?", context={})
    assert out["ok"] is True
    assert out["remote"]["source"] == "deterministic_lora_status"
    assert "vision_batch" in out["reply"]
    assert "1200" in out["reply"]
    assert "spécialiste" not in out["reply"].lower()
