"""Maturité contenu A/B/C (Bible V60–V65) — resolve + filtre + prompt."""

from __future__ import annotations

import pytest

from lbg_agents import dialogue_llm


def test_normalize_and_aliases() -> None:
    assert dialogue_llm.normalize_maturity_cap("a") == "A"
    assert dialogue_llm.normalize_maturity_cap("teen") == "B"
    assert dialogue_llm.normalize_maturity_cap("mature") == "C"
    assert dialogue_llm.normalize_maturity_cap("cap=B") == "B"
    assert dialogue_llm.normalize_maturity_cap("nope") == ""


def test_resolve_maturity_cap_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LBG_DIALOGUE_MATURITY_DEFAULT", raising=False)
    assert dialogue_llm.resolve_maturity_cap({}) == "C"
    assert dialogue_llm.resolve_maturity_cap({"maturity_cap": "A"}) == "A"
    assert dialogue_llm.resolve_maturity_cap({"player": {"maturity_cap": "B"}}) == "B"
    assert (
        dialogue_llm.resolve_maturity_cap({"session_summary": {"content_maturity": "teen"}}) == "B"
    )
    # top-level gagne sur nested
    assert (
        dialogue_llm.resolve_maturity_cap(
            {"maturity_cap": "C", "player": {"maturity_cap": "A"}}
        )
        == "C"
    )


def test_default_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_DIALOGUE_MATURITY_DEFAULT", "A")
    assert dialogue_llm.resolve_maturity_cap({}) == "A"


def test_filter_by_maturity() -> None:
    items = [
        {"text": "soft", "maturity": "A"},
        {"text": "teen", "maturity": "B"},
        {"text": "dark", "maturity": "C"},
        {"text": "untagged"},
        "plain",
    ]
    a = dialogue_llm.filter_by_maturity(items, "A")
    assert [x.get("text") if isinstance(x, dict) else x for x in a] == [
        "soft",
        "untagged",
        "plain",
    ]
    b = dialogue_llm.filter_by_maturity(items, "B")
    assert [x["text"] for x in b if isinstance(x, dict) and "maturity" in x] == ["soft", "teen"]
    c = dialogue_llm.filter_by_maturity(items, "C")
    assert len(c) == 5


def test_prompt_includes_maturity_block_default_c() -> None:
    p = dialogue_llm.build_system_prompt(
        "Mara",
        {"world_npc_id": "npc:innkeeper"},
    )
    assert "Maturité joueur **C**" in p
    assert "canon large" in p


def test_prompt_maturity_a_from_context() -> None:
    p = dialogue_llm.build_system_prompt(
        "Mara",
        {"world_npc_id": "npc:innkeeper", "maturity_cap": "A"},
    )
    assert "Maturité joueur **A**" in p
    assert "bienveillance max" in p
    assert "Maturité joueur **C**" not in p


def test_prompt_filters_tagged_quest_hints() -> None:
    p = dialogue_llm.build_system_prompt(
        "Mara",
        {
            "world_npc_id": "npc:innkeeper",
            "maturity_cap": "A",
            "quest_hints": [
                {"text": "Apporte de l'eau au camp", "maturity": "A"},
                {"text": "Scène gore du hangar", "maturity": "C"},
            ],
        },
    )
    assert "Apporte de l'eau" in p
    assert "gore" not in p.lower()
