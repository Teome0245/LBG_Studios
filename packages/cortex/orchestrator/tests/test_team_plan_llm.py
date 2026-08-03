"""Tests ADR 0019 Vague 2 — plan LLM borné (mocks, sans Ollama)."""

from __future__ import annotations

import json
import os
import sys
import types
from pathlib import Path

import pytest

# Stub legacy gelé (même contrainte AGENTS.md / monorepo extrait).
if "hybrid_proactive_agent" not in sys.modules:
    _stub = types.ModuleType("hybrid_proactive_agent")

    class LongTermMemoryStore:  # noqa: N801
        pass

    class MemoryEntry:  # noqa: N801
        pass

    _stub.LongTermMemoryStore = LongTermMemoryStore  # type: ignore[attr-defined]
    _stub.MemoryEntry = MemoryEntry  # type: ignore[attr-defined]
    sys.modules["hybrid_proactive_agent"] = _stub

os.environ["LBG_TEAM_DB_PATH"] = ":memory:"
os.environ["LBG_TEAM_PLAN_LLM"] = "0"

from team import plan_llm  # noqa: E402
from team import roles as team_roles  # noqa: E402
from team import store as team_store  # noqa: E402


@pytest.fixture(autouse=True)
def _env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_TEAM_DB_PATH", ":memory:")
    monkeypatch.setenv("LBG_TEAM_PLAN_LLM", "0")
    team_store.reset_for_tests()


def _heur_qa_pm(objective: str, *, actor_id: str = "system:team") -> list[dict[str, object]]:
    text = (objective or "").lower()
    out: list[dict[str, object]] = []
    if any(k in text for k in ("qa", "smoke", "lan", "valide", "vérif", "verif", "health")):
        out.append(
            {
                "role": "qa",
                "objective": "Smoke LAN",
                "priority": "normal",
                "approval_required": False,
                "actor_id": actor_id,
                "context": {},
            }
        )
    if any(k in text for k in ("pm", "brief", "plan")):
        out.append(
            {
                "role": "pm",
                "objective": "Brief PM",
                "priority": "normal",
                "approval_required": False,
                "actor_id": actor_id,
                "context": {},
            }
        )
    if not out:
        out.append(
            {
                "role": "pm",
                "objective": objective,
                "priority": "normal",
                "approval_required": False,
                "actor_id": actor_id,
                "context": {},
            }
        )
        out.append(
            {
                "role": "qa",
                "objective": "Smoke par défaut",
                "priority": "normal",
                "approval_required": False,
                "actor_id": actor_id,
                "context": {},
            }
        )
    return out


def test_extract_json_object_from_fence() -> None:
    text = 'Voici:\n```json\n{"proposals":[{"role":"qa","objective":"smoke"}]}\n```\n'
    data = plan_llm.extract_json_object(text)
    assert data is not None
    assert len(data["proposals"]) == 1


def test_merge_proposals_prefers_llm_then_heuristic_context() -> None:
    heur = [
        {
            "role": "qa",
            "objective": "Smoke LAN",
            "context": {"godot_supervisor": True},
            "plan_source": "heuristic",
        },
        {"role": "pm", "objective": "Brief", "context": {}, "plan_source": "heuristic"},
    ]
    llm = [
        {
            "role": "qa",
            "objective": "Vérifier healthz avant démo",
            "rationale": "démo demain",
            "plan_source": "llm",
        },
        {
            "role": "ops",
            "objective": "Sonde disque",
            "rationale": "infra",
            "plan_source": "llm",
        },
    ]
    merged = plan_llm.merge_proposals(heur, llm)
    roles = [m["role"] for m in merged]
    assert roles[0] == "qa"
    assert "ops" in roles
    assert any(m["role"] == "qa" and m.get("plan_source") == "heuristic" for m in merged)
    assert any(m["role"] == "pm" for m in merged)


def test_plan_objective_heuristic_only_when_flag_off() -> None:
    out = plan_llm.plan_objective(
        "valide le LAN et fais un brief PM",
        actor_id="u:test",
        use_llm=False,
        heuristic_fn=_heur_qa_pm,
    )
    assert out["source"] == "heuristic"
    roles = {p["role"] for p in out["proposals"]}
    assert "qa" in roles and "pm" in roles


def test_plan_objective_llm_hybrid_with_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_TEAM_PLAN_LLM", "1")

    def fake_complete(*, system: str, user: str, **kwargs: object) -> dict:
        payload = {
            "proposals": [
                {
                    "role": "qa",
                    "objective": "Smoke healthz + systemd avant démo",
                    "priority": "high",
                    "autonomy": "L1",
                    "approval_required": False,
                    "rationale": "démo demain",
                    "context": {},
                },
                {
                    "role": "ops",
                    "objective": "Sonde disque VM 140",
                    "priority": "normal",
                    "autonomy": "L1",
                    "rationale": "prévenir full disk",
                    "context": {},
                },
            ]
        }
        return {"ok": True, "text": json.dumps(payload), "model": "mock", "tier": "local"}

    monkeypatch.setattr(plan_llm, "reason_llm_enabled", lambda: True)
    out = plan_llm.plan_objective(
        "l'équipe doit vérifier que tout fonctionne avant la démo de demain",
        actor_id="u:llm",
        use_llm=True,
        heuristic_fn=_heur_qa_pm,
        complete_fn=fake_complete,
    )
    assert out["source"] in ("hybrid", "llm")
    roles = {p["role"] for p in out["proposals"]}
    assert "qa" in roles
    assert "ops" in roles
    assert out["meta"]["llm"]["ok"] is True


def test_plan_objective_llm_fallback_on_bad_json(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_complete(*, system: str, user: str, **kwargs: object) -> dict:
        return {"ok": True, "text": "pas de json ici", "model": "mock", "tier": "local"}

    monkeypatch.setattr(plan_llm, "reason_llm_enabled", lambda: True)
    out = plan_llm.plan_objective(
        "valide le LAN",
        use_llm=True,
        heuristic_fn=_heur_qa_pm,
        complete_fn=fake_complete,
    )
    assert out["source"] == "heuristic"
    assert out["meta"].get("fallback") == "heuristic"
    assert any(p["role"] == "qa" for p in out["proposals"])


def test_plan_rejects_invalid_llm_roles(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_complete(*, system: str, user: str, **kwargs: object) -> dict:
        return {
            "ok": True,
            "text": json.dumps(
                {
                    "proposals": [
                        {"role": "hacker", "objective": "pwn"},
                        {"role": "pm", "objective": "brief démo", "autonomy": "L0"},
                    ]
                }
            ),
            "model": "mock",
            "tier": "local",
        }

    monkeypatch.setattr(plan_llm, "reason_llm_enabled", lambda: True)
    raw = plan_llm.call_plan_llm("x", complete_fn=fake_complete)
    assert raw["ok"] is True
    assert len(raw["proposals"]) == 1
    assert raw["proposals"][0]["role"] == "pm"
    assert raw["llm_meta"]["rejected"] >= 1


def test_corpus_heuristic_coverage() -> None:
    """Bench léger corpus : expected_roles / expected_roles_any_of vs heuristique."""
    fixture = Path(__file__).resolve().parent / "fixtures" / "plan_corpus.json"
    data = json.loads(fixture.read_text(encoding="utf-8"))
    failures: list[str] = []
    for case in data["cases"]:
        cid = case["id"]
        props = team_roles.plan_from_objective(case["objective"], actor_id="corpus")
        roles = {p["role"] for p in props}
        expected = set(case.get("expected_roles") or [])
        any_of = set(case.get("expected_roles_any_of") or [])
        if expected and not expected.issubset(roles):
            failures.append(f"{cid}: missing {expected - roles} (got {roles})")
        if any_of and roles.isdisjoint(any_of):
            failures.append(f"{cid}: none of {any_of} in {roles}")
    assert not failures, "\n".join(failures)
