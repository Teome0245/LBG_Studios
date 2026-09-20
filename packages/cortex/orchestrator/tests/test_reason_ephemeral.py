"""Tests tier REASON ephemeral (Colab / tunnel GPU)."""

from __future__ import annotations

import pytest

from team.reason_llm import reason_ephemeral_route, reason_routes


@pytest.fixture(autouse=True)
def _clear_reason_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(__import__("os").environ):
        if key.startswith("LBG_REASON_") or key in ("OLLAMA_BASE_URL",):
            monkeypatch.delenv(key, raising=False)


def test_ephemeral_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_REASON_LOCAL_BASE_URL", "http://192.168.0.110:11434")
    monkeypatch.setenv("LBG_REASON_EPHEMERAL_BASE_URL", "https://abc.trycloudflare.com")
    monkeypatch.setenv("LBG_REASON_EPHEMERAL_API_KEY", "secret")
    assert reason_ephemeral_route() is None
    tiers = [r["tier"] for r in reason_routes(profile="forge")]
    assert "ephemeral" not in tiers


def test_ephemeral_requires_url_and_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_REASON_EPHEMERAL_ENABLED", "1")
    monkeypatch.setenv("LBG_REASON_EPHEMERAL_BASE_URL", "https://abc.trycloudflare.com")
    assert reason_ephemeral_route() is None
    monkeypatch.setenv("LBG_REASON_EPHEMERAL_API_KEY", "secret")
    route = reason_ephemeral_route()
    assert route is not None
    assert route["tier"] == "ephemeral"
    assert route["host"] == "colab"
    assert route["model"] == "huihui_ai/qwen3.5-abliterated:9b"
    assert route["timeout"] == "45"


def test_ephemeral_before_cloud(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_REASON_LOCAL_BASE_URL", "http://192.168.0.110:11434")
    monkeypatch.setenv("LBG_REASON_EPHEMERAL_ENABLED", "1")
    monkeypatch.setenv("LBG_REASON_EPHEMERAL_BASE_URL", "https://abc.trycloudflare.com")
    monkeypatch.setenv("LBG_REASON_EPHEMERAL_API_KEY", "secret")
    monkeypatch.setenv("LBG_REASON_EPHEMERAL_BEFORE_CLOUD", "1")
    monkeypatch.setenv("LBG_REASON_CLOUD_BASE_URL", "https://api.groq.com/openai/v1")
    monkeypatch.setenv("LBG_REASON_CLOUD_API_KEY", "gsk")
    monkeypatch.setenv("LBG_REASON_CLOUD_MODEL", "qwen/qwen3.6-27b")
    tiers = [r["tier"] for r in reason_routes(profile="forge")]
    assert tiers == ["local", "ephemeral", "cloud"]


def test_ephemeral_after_cloud(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_REASON_LOCAL_BASE_URL", "http://192.168.0.110:11434")
    monkeypatch.setenv("LBG_REASON_EPHEMERAL_ENABLED", "1")
    monkeypatch.setenv("LBG_REASON_EPHEMERAL_BASE_URL", "https://abc.trycloudflare.com")
    monkeypatch.setenv("LBG_REASON_EPHEMERAL_API_KEY", "tok")
    monkeypatch.setenv("LBG_REASON_EPHEMERAL_BEFORE_CLOUD", "0")
    monkeypatch.setenv("LBG_REASON_CLOUD_BASE_URL", "https://api.groq.com/openai/v1")
    monkeypatch.setenv("LBG_REASON_CLOUD_API_KEY", "gsk")
    tiers = [r["tier"] for r in reason_routes(profile="forge")]
    assert tiers == ["local", "cloud", "ephemeral"]


def test_ephemeral_only_without_local(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_REASON_EPHEMERAL_ENABLED", "1")
    monkeypatch.setenv("LBG_REASON_EPHEMERAL_BASE_URL", "https://abc.trycloudflare.com/v1")
    monkeypatch.setenv("LBG_REASON_EPHEMERAL_API_KEY", "tok")
    monkeypatch.setenv("LBG_REASON_EPHEMERAL_MODEL", "llama3.2:3b")
    # Sans LOCAL_BASE_URL, heavy tombe sur défaut OLLAMA — on force vide via prefer_cloud path.
    monkeypatch.setenv("OLLAMA_BASE_URL", "")
    monkeypatch.setenv("LBG_REASON_LOCAL_BASE_URL", "")
    monkeypatch.setenv("LBG_REASON_HEAVY_BASE_URL", "")
    monkeypatch.setenv("LBG_REASON_BASE_URL", "")
    # reason_heavy_base_url a un défaut 110 : on teste juste que ephemeral est présent.
    routes = reason_routes(profile="forge")
    eph = [r for r in routes if r["tier"] == "ephemeral"]
    assert len(eph) == 1
    assert eph[0]["model"] == "llama3.2:3b"
