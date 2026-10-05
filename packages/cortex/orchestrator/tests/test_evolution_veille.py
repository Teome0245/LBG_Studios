"""Tests workflow veille évolution (Thémis + reason_llm)."""

from __future__ import annotations

import json

import pytest

from team.evolution_veille_workflow import (
    execute_evolution_veille_workflow,
    resolve_evolution_veille_workflow,
)
from team.models import TeamTask
from team.roles import plan_from_objective


def test_resolve_from_context() -> None:
    task = TeamTask(
        id="t-veille-1",
        role="pm",
        objective="Autre chose",
        status="queued",
        context={"evolution_veille": True},
    )
    assert resolve_evolution_veille_workflow(task) is True


def test_resolve_from_keywords() -> None:
    task = TeamTask(
        id="t-veille-2",
        role="pm",
        objective="Veille évolution LBG — analyser pistes TikTok",
        status="queued",
        context={},
    )
    assert resolve_evolution_veille_workflow(task) is True


def test_plan_routes_veille_before_sprint() -> None:
    props = plan_from_objective(
        "Veille évolution LBG batch — faisabilité pour l'écosystème, verdicts, top 3"
    )
    veille = [p for p in props if (p.get("context") or {}).get("evolution_veille")]
    assert veille, "attendu une proposal evolution_veille"
    assert veille[0]["role"] == "pm"
    assert veille[0]["priority"] == "high"


def test_execute_veille_parses_json(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "summary": "3 pistes utiles, 1 bruit.",
        "leads": [
            {
                "index": 1,
                "title": "Agentic RAG",
                "domain": "agent_orchestration",
                "feasibility": "Mappe sur Team Campus",
                "integration": "Mémoire Compagnon + outils",
                "pros": ["aligné OS agentique"],
                "cons": ["pas de nouveau framework"],
                "verdict": "inspiration",
                "plan": "Doc mapping Agentic RAG → bus Team",
            },
            {
                "index": 2,
                "title": "Geekshopeek",
                "domain": "general_studio",
                "feasibility": "Extrait pauvre",
                "integration": "—",
                "pros": [],
                "cons": ["pas de signal"],
                "verdict": "non_pertinent",
                "plan": None,
            },
        ],
        "top_3_actions": [
            {
                "title": "Spike DSH .10",
                "owner_role": "dev_game",
                "autonomy": "L2",
                "why": "ADR 0020",
            },
            {
                "title": "Mémoire Agentique light",
                "owner_role": "pm",
                "autonomy": "L1",
                "why": "Compagnon",
            },
            {
                "title": "VoiceStudio local",
                "owner_role": "ops",
                "autonomy": "L2",
                "why": "voice_local",
            },
        ],
    }

    def fake_complete(**kwargs):
        assert kwargs.get("profile") in ("pm", "json", "forge", "fast")
        return {"ok": True, "text": json.dumps(payload), "model": "test-pm", "tier": "local"}

    monkeypatch.setenv("LBG_REASON_LOCAL_BASE_URL", "http://192.168.0.110:11434")
    monkeypatch.delenv("LBG_REASON_LLM_DISABLED", raising=False)
    monkeypatch.setattr("team.evolution_veille_workflow.complete_reason", fake_complete)
    monkeypatch.setattr("team.evolution_veille_workflow.reason_llm_enabled", lambda: True)

    task = TeamTask(
        id="t-veille-3",
        role="pm",
        objective="Veille évolution LBG batch",
        status="queued",
        context={
            "evolution_veille": True,
            "leads": [
                {"title": "Agentic RAG", "domain": "agent_orchestration", "description": "diagram"},
                {"title": "Geekshopeek", "domain": "general_studio", "description": "BGM"},
            ],
        },
    )
    out = execute_evolution_veille_workflow(task)
    assert out["ok"] is True
    assert out["kind"] == "evolution_veille_workflow"
    assert out["browser_open"] is False
    assert len(out["leads"]) == 2  # type: ignore[arg-type]
    assert out["leads"][0]["verdict"] == "inspiration"  # type: ignore[index]
    assert len(out["top_3_actions"]) == 3  # type: ignore[arg-type]
    assert "Top actions" in str(out["human_summary"])


def test_execute_veille_heuristic_on_llm_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "team.evolution_veille_workflow.complete_reason",
        lambda **k: {"ok": False, "error": "timed out", "text": ""},
    )
    monkeypatch.setattr("team.evolution_veille_workflow.reason_llm_enabled", lambda: True)
    monkeypatch.setenv("LBG_VEILLE_TIMEOUT_S", "5")
    task = TeamTask(
        id="t-veille-h",
        role="pm",
        objective="Veille évolution",
        status="queued",
        context={
            "evolution_veille": True,
            "leads": [
                {"title": "DeepSeek Harness", "domain": "general_studio", "description": "agent harness"},
                {"title": "VoiceStudio", "domain": "voice_local", "description": "TTS local ElevenLabs"},
                {"title": "Mael conseils", "domain": "general_studio", "description": "Abonne toi"},
            ],
        },
    )
    out = execute_evolution_veille_workflow(task)
    assert out["ok"] is True
    assert out["context_echo"]["heuristic"] is True  # type: ignore[index]
    assert any(l["verdict"] == "utilisable" for l in out["leads"])  # type: ignore[union-attr]
    assert len(out["top_3_actions"]) >= 1  # type: ignore[arg-type]
