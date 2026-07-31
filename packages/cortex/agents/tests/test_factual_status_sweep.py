"""Tests balayage anti-hallucination — statuts factuels."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "agents" / "src"))
sys.path.insert(0, str(ROOT / "orchestrator"))

from introspection.deterministic_classifier import DeterministicIntentClassifier  # noqa: E402
from lbg_agents.status_intent import (  # noqa: E402
    classify_status_intent,
    is_operational_status_query,
)
from lbg_agents.status_router import (  # noqa: E402
    should_answer_with_factual_status,
    try_factual_status_for_dialogue,
)


def test_lora_question_with_npc_context_still_classified() -> None:
    c = DeterministicIntentClassifier()
    text = "où on en est des entraînements LoRA et du tri des images ?"
    intent, conf = c.classify(text)
    assert intent == "infographiste_status"
    assert conf >= 0.9


def test_operational_status_not_quest() -> None:
    c = DeterministicIntentClassifier()
    text = "où en est le tri des images et les buckets ?"
    intent, _ = c.classify(text)
    assert intent == "infographiste_status"
    assert intent != "quest_request"


def test_godot_status_intent() -> None:
    intent, conf = classify_status_intent("statut Godot et ZB-1 sidecar ?")
    assert intent == "godot_status"
    assert conf >= 0.85


def test_infra_status_intent() -> None:
    intent, _ = classify_status_intent("où en est l'infra et les healthz orchestrateur ?")
    assert intent == "infra_status"


def test_generic_project_status() -> None:
    intent, _ = classify_status_intent("où en sommes-nous sur le projet ?")
    assert intent == "project_status"


def test_dialogue_intercept_no_jira(monkeypatch) -> None:
    monkeypatch.setenv("LBG_ORCHESTRATOR_URL", "http://127.0.0.1:9")
    monkeypatch.setenv("LBG_TEAM_INFOGRAPHISTE_LORA_STATE", "/nonexistent/lora.json")
    assert should_answer_with_factual_status("où en est LoRA ?")
    out = try_factual_status_for_dialogue(actor_id="u:t", text="où en est LoRA ?", context={})
    assert out is not None
    assert out["meta"]["factual_status"] is True
    assert out["meta"]["llm"] is False
    reply = out["reply"].lower()
    assert "jira" not in reply
    assert "lbg_project" not in reply


def test_npc_name_route_would_not_block_status() -> None:
    assert is_operational_status_query("Bonjour, où en est le tri LoRA ?")
