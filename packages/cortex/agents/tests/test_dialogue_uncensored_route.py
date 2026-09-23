"""Routage modèle local selon maturité (uncensored option A/B)."""

from __future__ import annotations

import pytest

from lbg_agents import dialogue_llm


def test_resolve_local_model_maturity_c_uses_uncensored(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_DIALOGUE_LLM_MODEL", "qwen3.8:27b")
    monkeypatch.setenv("LBG_DIALOGUE_LLM_MODEL_UNCENSORED", "huihui_ai/qwen3-abliterated:14b")
    monkeypatch.setenv("LBG_DIALOGUE_UNCENSORED_ON_MATURITY_C", "1")
    monkeypatch.delenv("LBG_DIALOGUE_UNCENSORED_ALWAYS", raising=False)
    monkeypatch.delenv("LBG_DIALOGUE_MATURITY_DEFAULT", raising=False)

    assert dialogue_llm.resolve_dialogue_local_model({"maturity_cap": "A"}) == "qwen3.8:27b"
    assert dialogue_llm.resolve_dialogue_local_model({"maturity_cap": "B"}) == "qwen3.8:27b"
    assert dialogue_llm.resolve_dialogue_local_model({"maturity_cap": "C"}) == "huihui_ai/qwen3-abliterated:14b"
    # défaut maturity = C
    assert dialogue_llm.resolve_dialogue_local_model({}) == "huihui_ai/qwen3-abliterated:14b"


def test_resolve_local_model_always_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_DIALOGUE_LLM_MODEL", "qwen3.8:27b")
    monkeypatch.setenv("LBG_DIALOGUE_LLM_MODEL_UNCENSORED", "dolphin3:8b")
    monkeypatch.setenv("LBG_DIALOGUE_UNCENSORED_ALWAYS", "1")
    assert dialogue_llm.resolve_dialogue_local_model({"maturity_cap": "A"}) == "dolphin3:8b"


def test_resolve_local_model_force_context(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_DIALOGUE_LLM_MODEL", "qwen3.8:27b")
    monkeypatch.setenv("LBG_DIALOGUE_LLM_MODEL_UNCENSORED", "dolphin3:8b")
    monkeypatch.setenv("LBG_DIALOGUE_UNCENSORED_ON_MATURITY_C", "1")
    monkeypatch.delenv("LBG_DIALOGUE_UNCENSORED_ALWAYS", raising=False)
    assert (
        dialogue_llm.resolve_dialogue_local_model({"maturity_cap": "A", "force_uncensored": True})
        == "dolphin3:8b"
    )


def test_tier_route_local_passes_uncensored_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_DIALOGUE_LLM_BASE_URL", "http://192.168.0.110:11434/v1")
    monkeypatch.setenv("LBG_DIALOGUE_LLM_MODEL", "qwen3.8:27b")
    monkeypatch.setenv("LBG_DIALOGUE_LLM_MODEL_UNCENSORED", "huihui_ai/qwen3-abliterated:14b")
    monkeypatch.delenv("LBG_DIALOGUE_LLM_DISABLED", raising=False)
    r = dialogue_llm._tier_route("local", context={"maturity_cap": "C"})
    assert r is not None
    assert r["model"] == "huihui_ai/qwen3-abliterated:14b"


def test_no_uncensored_env_keeps_base(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_DIALOGUE_LLM_MODEL", "qwen3.8:27b")
    monkeypatch.delenv("LBG_DIALOGUE_LLM_MODEL_UNCENSORED", raising=False)
    assert dialogue_llm.resolve_dialogue_local_model({"maturity_cap": "C"}) == "qwen3.8:27b"
