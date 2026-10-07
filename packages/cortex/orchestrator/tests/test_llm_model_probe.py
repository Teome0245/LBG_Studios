"""Tests audit Groq dialogue fast (LBG_DIALOGUE_FAST_MODEL)."""

from __future__ import annotations

import os

import pytest

from team.llm_model_probe import ProbeResult, audit_dialogue_fast_cloud, auto_fix_env, probe_all_cloud


def test_audit_dialogue_fast_flags_legacy_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_DIALOGUE_FAST_ENABLED", "1")
    monkeypatch.setenv("LBG_DIALOGUE_FAST_MODEL", "llama-3.1-8b-instant")
    monkeypatch.setenv("LBG_DIALOGUE_FAST_BASE_URL", "https://api.groq.com/openai/v1")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    def fake_probe(**kwargs: object) -> ProbeResult:
        return ProbeResult(
            provider="groq_dialogue_fast",
            base_url=str(kwargs.get("base_url", "")),
            configured_model=str(kwargs.get("configured_model", "")),
            configured_available=False,
            recommended_model="qwen/qwen3.8-27b",
            available_models=["qwen/qwen3.8-27b"],
        )

    monkeypatch.setattr("team.llm_model_probe.probe_cloud_models", fake_probe)
    out = audit_dialogue_fast_cloud(probe=True)
    assert out["ok"] is False
    assert any("legacy" in g for g in out["gaps"])
    assert any("push_secrets_vm.sh" in r for r in out["recommendations"])


def test_audit_dialogue_fast_flags_env_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_DIALOGUE_FAST_ENABLED", "1")
    monkeypatch.setenv("LBG_DIALOGUE_FAST_MODEL", "qwen/qwen3.8-27b")
    monkeypatch.setenv("GROQ_MODEL_FAST", "llama-3.1-8b-instant")
    monkeypatch.setenv("LBG_DIALOGUE_FAST_BASE_URL", "https://api.groq.com/openai/v1")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    monkeypatch.setattr(
        "team.llm_model_probe.probe_cloud_models",
        lambda **kwargs: ProbeResult(
            provider="groq_dialogue_fast",
            base_url="https://api.groq.com/openai/v1",
            configured_model="qwen/qwen3.8-27b",
            configured_available=True,
            available_models=["qwen/qwen3.8-27b"],
        ),
    )
    out = audit_dialogue_fast_cloud(probe=True)
    assert out["ok"] is False
    assert any("désalignement" in g for g in out["gaps"])


def test_probe_all_cloud_prioritizes_dialogue_fast_model(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_probe(**kwargs: object) -> ProbeResult:
        calls.append(str(kwargs.get("configured_model", "")))
        return ProbeResult(
            provider=str(kwargs.get("provider", "")),
            base_url="https://api.groq.com/openai/v1",
            configured_model=str(kwargs.get("configured_model", "")),
            configured_available=True,
        )

    monkeypatch.setenv("LBG_DIALOGUE_FAST_BASE_URL", "https://api.groq.com/openai/v1")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("LBG_DIALOGUE_FAST_MODEL", "qwen/qwen3.8-27b")
    monkeypatch.setenv("GROQ_MODEL_FAST", "qwen/qwen3.8-27b")
    monkeypatch.setattr("team.llm_model_probe.probe_cloud_models", fake_probe)

    results = probe_all_cloud()
    assert len(results) == 1
    assert calls == ["qwen/qwen3.8-27b"]


def test_auto_fix_env_patches_dialogue_fast_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_DIALOGUE_FAST_MODEL", "llama-3.1-8b-instant")
    monkeypatch.setenv("GROQ_MODEL_FAST", "llama-3.1-8b-instant")
    results = [
        ProbeResult(
            provider="groq_dialogue_fast",
            base_url="https://api.groq.com/openai/v1",
            configured_model="llama-3.1-8b-instant",
            configured_available=False,
            recommended_model="qwen/qwen3.8-27b",
            available_models=["qwen/qwen3.8-27b"],
        )
    ]
    summary = auto_fix_env(results)
    assert summary["patched"] is True
    assert os.environ.get("LBG_DIALOGUE_FAST_MODEL") == "qwen/qwen3.8-27b"
