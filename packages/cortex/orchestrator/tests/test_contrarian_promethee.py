"""Prométhée — workflow contrarian + registry."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from team.agent_registry import agent_by_id, load_agent_declarations
from team.contrarian_workflow import execute_contrarian_workflow
from team.models import TeamTask, VALID_ROLES
from team.reason_llm import reason_local_model, reason_route_matrix
from team.roles import ROLE_SPECS, plan_from_objective


def test_contrarian_in_valid_roles() -> None:
    assert "contrarian" in VALID_ROLES
    assert "contrarian" in ROLE_SPECS


def test_promethee_declaration_present() -> None:
    load_agent_declarations.cache_clear()
    decl = agent_by_id("studio_contrarian_promethee")
    assert decl is not None
    assert decl.get("persona") == "promethee"
    assert decl.get("role") == "contrarian"
    assert decl.get("llm_profile") == "uncensored"


def test_uncensored_in_route_matrix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LBG_REASON_MODEL_UNCENSORED", raising=False)
    monkeypatch.setenv("LBG_DIALOGUE_LLM_MODEL_UNCENSORED", "dolphin3:8b")
    assert "uncensored" in reason_route_matrix()
    assert reason_local_model(profile="uncensored") == "dolphin3:8b"
    assert reason_local_model(profile="promethee") == "dolphin3:8b"


def test_plan_routes_promethee_keywords() -> None:
    props = plan_from_objective("Donne un second avis Prométhée hors cadre sur le hub Lost Heaven")
    roles = [p["role"] for p in props]
    assert "contrarian" in roles


def test_execute_contrarian_parses_json(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "summary": "Piste alternative",
        "opinions": ["Trop prudent sur le ton patchwork"],
        "alternatives": [{"title": "Hub nocturne", "why": "risque/récompense", "tradeoffs": "QA +"}],
        "risks": ["scope creep"],
        "out_of_scope_notes": ["hors sprint Iris"],
        "stay_legal": True,
    }

    def fake_complete(**kwargs):
        assert kwargs.get("profile") == "uncensored"
        return {"ok": True, "text": json.dumps(payload), "model": "dolphin3:8b", "tier": "local"}

    monkeypatch.setenv("LBG_REASON_LOCAL_BASE_URL", "http://192.168.0.110:11434")
    monkeypatch.setenv("LBG_DIALOGUE_LLM_MODEL_UNCENSORED", "dolphin3:8b")
    monkeypatch.delenv("LBG_REASON_LLM_DISABLED", raising=False)
    monkeypatch.setattr("team.contrarian_workflow.complete_reason", fake_complete)
    monkeypatch.setattr("team.contrarian_workflow.reason_llm_enabled", lambda: True)

    task = TeamTask(
        id="t-contrarian-1",
        role="contrarian",
        objective="Challenger le plan hub",
        status="queued",
        context={"brief": "Lost Heaven craft loop"},
    )
    out = execute_contrarian_workflow(task)
    assert out["ok"] is True
    assert out["persona"] == "promethee"
    counsel = out["counsel"]
    assert isinstance(counsel, dict)
    assert counsel["summary"] == "Piste alternative"
    assert counsel["alternatives"][0]["title"] == "Hub nocturne"
