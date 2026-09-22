"""Tests Laya System One — client HTTP + classifieur intent (sans torch)."""

from __future__ import annotations

import json
from unittest.mock import patch

from introspection.deterministic_classifier import DeterministicIntentClassifier
from introspection.laya_intent_classifier import (
    INTENT_CRITERIA,
    classify_intent_laya,
    intent_questions,
    laya_should_accept,
    should_use_laya_intent,
)
from introspection.llm_intent_classifier import ALLOWED_INTENTS, hybrid_classify
from services.laya_client import extract_choice, extract_noul, systemone_predict


def test_intent_criteria_match_allowed() -> None:
    assert set(INTENT_CRITERIA) == set(ALLOWED_INTENTS)


def test_should_use_laya_context_modes(monkeypatch) -> None:
    monkeypatch.delenv("LBG_ORCHESTRATOR_INTENT_LAYA", raising=False)
    assert should_use_laya_intent({"_intent_classify": "deterministic"}) is False
    assert should_use_laya_intent({"_intent_classify": "llm"}) is False
    assert should_use_laya_intent({"_intent_classify": "laya"}) is True
    monkeypatch.setenv("LBG_ORCHESTRATOR_INTENT_LAYA", "1")
    assert should_use_laya_intent({}) is True


def test_extract_choice_and_noul() -> None:
    resp = {
        "answers": {
            "intent": {
                "choice": "devops_probe",
                "confidence": 0.91,
                "probabilities": {"devops_probe": 0.91, "unknown": 0.09},
            },
            "needs_llm": {"noul": 0.12},
        }
    }
    label, conf, probs = extract_choice(resp, "intent")
    assert label == "devops_probe"
    assert conf == 0.91
    assert probs["devops_probe"] == 0.91
    assert extract_noul(resp, "needs_llm") == 0.12


def test_laya_should_accept_rules() -> None:
    assert laya_should_accept(
        det_intent="unknown", laya_intent="devops_probe", laya_conf=0.7, needs_llm=0.1
    )
    assert not laya_should_accept(
        det_intent="unknown", laya_intent="devops_probe", laya_conf=0.7, needs_llm=0.9
    )
    assert not laya_should_accept(
        det_intent="quest_request", laya_intent="npc_dialogue", laya_conf=0.7, needs_llm=0.1
    )
    assert laya_should_accept(
        det_intent="quest_request", laya_intent="npc_dialogue", laya_conf=0.9, needs_llm=0.1
    )


def test_systemone_predict_parses(monkeypatch) -> None:
    monkeypatch.setenv("LBG_ORCHESTRATOR_INTENT_LAYA_BASE_URL", "http://127.0.0.1:9")
    payload = {"model": "laya-english", "answers": {"intent": {"choice": "project_pm", "confidence": 0.8}}}

    class CM:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(payload).encode("utf-8")

    class R:
        def __enter__(self):
            return CM()

        def __exit__(self, *args):
            return False

    with patch("services.laya_client.urllib.request.urlopen", return_value=R()):
        out = systemone_predict(state="hi", questions=intent_questions())
    assert out is not None
    assert out["model"] == "laya-english"


def test_classify_intent_laya(monkeypatch) -> None:
    monkeypatch.setenv("LBG_ORCHESTRATOR_INTENT_LAYA_BASE_URL", "http://fake")

    fake = {
        "model": "laya-latest",
        "answers": {
            "intent": {
                "choice": "devops_probe",
                "confidence": 0.88,
                "probabilities": {"devops_probe": 0.88},
            },
            "needs_llm": {"noul": 0.2},
        },
    }
    with patch("introspection.laya_intent_classifier.systemone_predict", return_value=fake):
        out = classify_intent_laya("vérifie healthz backend")
    assert out is not None
    intent, conf, meta = out
    assert intent == "devops_probe"
    assert conf == 0.88
    assert meta["intent_source"] == "laya"
    assert meta["laya_needs_llm"] == 0.2


def test_hybrid_uses_laya_when_det_unknown(monkeypatch) -> None:
    monkeypatch.setenv("LBG_ORCHESTRATOR_INTENT_LAYA", "1")
    monkeypatch.setenv("LBG_ORCHESTRATOR_INTENT_LAYA_BASE_URL", "http://fake")
    monkeypatch.delenv("LBG_ORCHESTRATOR_INTENT_LLM", raising=False)

    def fake_laya(_t: str):
        return ("devops_probe", 0.82, {"intent_source": "laya", "laya_needs_llm": 0.1})

    with patch("introspection.laya_intent_classifier.classify_intent_laya", fake_laya):
        det = DeterministicIntentClassifier()
        intent, conf, meta = hybrid_classify(
            "vérifie si les services tournent encore",
            {},
            det.classify,
        )
    assert intent == "devops_probe"
    assert conf == 0.82
    assert meta.get("intent_source") == "laya"


def test_hybrid_defers_laya_when_needs_llm(monkeypatch) -> None:
    monkeypatch.setenv("LBG_ORCHESTRATOR_INTENT_LAYA", "1")
    monkeypatch.setenv("LBG_ORCHESTRATOR_INTENT_LAYA_BASE_URL", "http://fake")
    monkeypatch.setenv("LBG_ORCHESTRATOR_INTENT_LLM", "1")
    monkeypatch.setenv("LBG_ORCHESTRATOR_INTENT_LLM_BASE_URL", "http://fake-llm")

    def fake_laya(_t: str):
        return ("unknown", 0.6, {"intent_source": "laya", "laya_needs_llm": 0.95})

    def fake_llm(_t: str):
        return ("project_pm", 0.9, {"intent_source": "llm"})

    with (
        patch("introspection.laya_intent_classifier.classify_intent_laya", fake_laya),
        patch("introspection.llm_intent_classifier.classify_intent_llm", fake_llm),
    ):
        det = DeterministicIntentClassifier()
        intent, conf, meta = hybrid_classify(
            "un truc un peu flou sur le planning",
            {},
            det.classify,
        )
    assert intent == "project_pm"
    assert meta.get("intent_source") == "llm"
    assert meta.get("intent_laya_deferred") is True


def test_hybrid_skips_laya_when_forced_llm(monkeypatch) -> None:
    monkeypatch.setenv("LBG_ORCHESTRATOR_INTENT_LAYA", "1")
    monkeypatch.setenv("LBG_ORCHESTRATOR_INTENT_LAYA_BASE_URL", "http://fake")
    monkeypatch.setenv("LBG_ORCHESTRATOR_INTENT_LLM", "1")
    monkeypatch.setenv("LBG_ORCHESTRATOR_INTENT_LLM_BASE_URL", "http://fake")

    def boom(_t: str):
        raise AssertionError("Laya should not be called")

    def fake_llm(_t: str):
        return ("devops_probe", 0.8, {"intent_source": "llm"})

    with (
        patch("introspection.laya_intent_classifier.classify_intent_laya", boom),
        patch("introspection.llm_intent_classifier.classify_intent_llm", fake_llm),
    ):
        det = DeterministicIntentClassifier()
        intent, conf, meta = hybrid_classify(
            "vérifie si les services tournent encore",
            {"_intent_classify": "llm"},
            det.classify,
        )
    assert intent == "devops_probe"
    assert meta.get("intent_source") == "llm"
