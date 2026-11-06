"""Tests audit Ollama dual 110/111."""

from __future__ import annotations

import pytest

from team import ollama_audit as oa


def test_base_url_router_uses_light(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_REASON_LIGHT_BASE_URL", "http://192.168.0.111:11434")
    monkeypatch.setenv("LBG_REASON_LOCAL_BASE_URL", "http://192.168.0.110:11434")
    assert oa._base_url_for_role("reason_router") == "http://192.168.0.111:11434"
    assert oa._base_url_for_role("reason_code").endswith("110:11434")


def test_audit_ollama_lan_dual(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_REASON_LIGHT_BASE_URL", "http://192.168.0.111:11434")
    monkeypatch.setenv("LBG_REASON_LOCAL_BASE_URL", "http://192.168.0.110:11434")
    monkeypatch.setenv("LBG_REASON_MODEL_ROUTER", "qwen2.5:3b")
    monkeypatch.setenv("LBG_REASON_MODEL_JSON", "qwen2.5:3b")
    monkeypatch.setenv("LBG_REASON_MODEL_FAST", "llama3.2:3b")
    monkeypatch.setenv("LBG_REASON_MODEL_CODE", "gemma4:26b")
    monkeypatch.setenv("LBG_REASON_MODEL_FORGE", "gemma4:e2b")
    monkeypatch.delenv("LBG_DIALOGUE_LLM_MODEL", raising=False)
    monkeypatch.delenv("LBG_DIALOGUE_FAST_MODEL", raising=False)
    monkeypatch.delenv("LBG_REASON_LOCAL_MODEL", raising=False)
    monkeypatch.delenv("LBG_REASON_MODEL_PM", raising=False)
    monkeypatch.delenv("LBG_JOBS_PLANNER_LLM_MODEL", raising=False)
    monkeypatch.delenv("LBG_COMPANION_LLM_MODEL", raising=False)

    def fake_fetch(base: str, *, timeout: float = 10.0) -> dict:
        if "111" in base:
            return {
                "installed": [
                    {"name": "qwen2.5:3b", "size_gb": 1.9},
                    {"name": "llama3.2:3b", "size_gb": 2.0},
                ],
                "names": {"qwen2.5:3b", "llama3.2:3b"},
            }
        return {
            "installed": [
                {"name": "huihui_ai/gemma-4-abliterated:E4b-qat", "size_gb": 4.0},
                {"name": "huihui_ai/gemma-4-abliterated:12b-qat", "size_gb": 12.0},
                {"name": "huihui_ai/qwen2.5-coder-abliterate:14b", "size_gb": 14.0},
                {"name": "gemma4:e2b", "size_gb": 7.2},
                {"name": "gemma4:26b", "size_gb": 17.0},
                {"name": "huihui_ai/Qwen3.8-abliterated:27b", "size_gb": 18.0},
            ],
            "names": {
                "huihui_ai/gemma-4-abliterated:E4b-qat",
                "huihui_ai/gemma-4-abliterated:12b-qat",
                "huihui_ai/qwen2.5-coder-abliterate:14b",
                "gemma4:e2b",
                "gemma4:26b",
                "huihui_ai/Qwen3.8-abliterated:27b",
            },
        }

    monkeypatch.setattr(oa, "_fetch_tags", fake_fetch)
    out = oa.audit_ollama_lan()
    assert out["ok"] is True
    assert out["track"] == "ollama_audit_dual_110_111"
    assert out["light"]["ok"] is True
    assert out["heavy"]["ok"] is True
    assert out["gaps"] == []


def test_audit_companion_legacy_is_advisory(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_REASON_LIGHT_BASE_URL", "http://192.168.0.111:11434")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://192.168.0.110:11434")
    monkeypatch.setenv("LBG_COMPANION_LLM_MODEL", "phi4-mini:latest")
    monkeypatch.delenv("LBG_REASON_MODEL_FAST", raising=False)
    for k in (
        "LBG_REASON_MODEL_ROUTER",
        "LBG_REASON_MODEL_JSON",
        "LBG_REASON_MODEL_CODE",
        "LBG_REASON_MODEL_FORGE",
        "LBG_REASON_MODEL_PM",
        "LBG_REASON_LOCAL_MODEL",
        "LBG_DIALOGUE_LLM_MODEL",
        "LBG_DIALOGUE_FAST_MODEL",
        "LBG_JOBS_PLANNER_LLM_MODEL",
    ):
        monkeypatch.delenv(k, raising=False)

    def fake_fetch(base: str, *, timeout: float = 10.0) -> dict:
        if "111" in base:
            return {
                "installed": [
                    {"name": "huihui_ai/qwen3.5-abliterated:2B", "size_gb": 2.0},
                    {"name": "huihui_ai/qwen3.5-abliterated:0.8B", "size_gb": 0.8},
                    {"name": "qwen2.5:3b", "size_gb": 1.9},
                ],
                "names": {"huihui_ai/qwen3.5-abliterated:2B", "huihui_ai/qwen3.5-abliterated:0.8B", "qwen2.5:3b"},
            }
        return {
            "installed": [
                {"name": "huihui_ai/gemma-4-abliterated:E4b-qat", "size_gb": 4.0},
                {"name": "huihui_ai/gemma-4-abliterated:12b-qat", "size_gb": 12.0},
                {"name": "huihui_ai/qwen2.5-coder-abliterate:14b", "size_gb": 14.0},
                {"name": "gemma4:e2b", "size_gb": 7.0},
                {"name": "huihui_ai/Qwen3.8-abliterated:27b", "size_gb": 18.0},
            ],
            "names": {
                "huihui_ai/gemma-4-abliterated:E4b-qat",
                "huihui_ai/gemma-4-abliterated:12b-qat",
                "huihui_ai/qwen2.5-coder-abliterate:14b",
                "gemma4:e2b",
                "huihui_ai/Qwen3.8-abliterated:27b",
            },
        }

    monkeypatch.setattr(oa, "_fetch_tags", fake_fetch)
    out = oa.audit_ollama_lan()
    assert out["ok"] is True
    assert any("companion" in w for w in out.get("warnings") or [])
    assert not any("companion" in g for g in out.get("blocking_gaps") or [])


def test_audit_detects_missing_light_model_failover_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_REASON_LIGHT_BASE_URL", "http://192.168.0.111:11434")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://192.168.0.110:11434")
    monkeypatch.setenv("LBG_REASON_MODEL_ROUTER", "qwen2.5:3b")
    monkeypatch.setenv("LBG_REASON_MODEL_FAST", "gemma4:e2b")
    monkeypatch.setenv("LBG_REASON_LIGHT_FAILOVER_HEAVY", "1")
    for k in (
        "LBG_REASON_MODEL_JSON",
        "LBG_REASON_MODEL_CODE",
        "LBG_REASON_MODEL_FORGE",
        "LBG_REASON_MODEL_PM",
        "LBG_REASON_LOCAL_MODEL",
        "LBG_DIALOGUE_LLM_MODEL",
        "LBG_DIALOGUE_FAST_MODEL",
        "LBG_JOBS_PLANNER_LLM_MODEL",
        "LBG_COMPANION_LLM_MODEL",
    ):
        monkeypatch.delenv(k, raising=False)

    def fake_fetch(base: str, *, timeout: float = 10.0) -> dict:
        if "111" in base:
            return {"installed": [], "names": set()}
        return {
            "installed": [
                {"name": "huihui_ai/gemma-4-abliterated:E4b-qat", "size_gb": 4.0},
                {"name": "huihui_ai/gemma-4-abliterated:12b-qat", "size_gb": 12.0},
                {"name": "huihui_ai/qwen2.5-coder-abliterate:14b", "size_gb": 14.0},
                {"name": "qwen2.5:3b", "size_gb": 1.9},
                {"name": "gemma4:e2b", "size_gb": 7.0},
                {"name": "huihui_ai/Qwen3.8-abliterated:27b", "size_gb": 18.0},
            ],
            "names": {
                "huihui_ai/gemma-4-abliterated:E4b-qat",
                "huihui_ai/gemma-4-abliterated:12b-qat",
                "huihui_ai/qwen2.5-coder-abliterate:14b",
                "qwen2.5:3b",
                "gemma4:e2b",
                "huihui_ai/Qwen3.8-abliterated:27b",
            },
        }

    monkeypatch.setattr(oa, "_fetch_tags", fake_fetch)
    out = oa.audit_ollama_lan()
    assert out["ok"] is True
    assert any("reason_router" in w for w in out.get("warnings") or [])
