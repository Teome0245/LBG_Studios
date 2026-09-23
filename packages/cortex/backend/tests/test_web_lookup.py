"""Lookup web serveur — détection + formatage (autonomie chat Orch)."""

from __future__ import annotations

import pytest

from services.web_lookup import (
    enrich_ask_prompt,
    extract_lookup_query,
    format_web_lookup_grounding,
    wants_web_lookup,
)


def test_wants_film_search() -> None:
    prompt = (
        "Bonjour, je cherche un vieux film d'animation, vous pourriez m'aider "
        "à le trouver ? Le Voyage d'Edgar dans la forêt magique ?"
    )
    assert wants_web_lookup(prompt) is True


def test_rejects_ops_and_social() -> None:
    assert wants_web_lookup("bonjour") is False
    assert wants_web_lookup("team: status orchestrateur") is False
    assert wants_web_lookup("ouvre notepad sur mon poste") is False


def test_extract_titleish_query() -> None:
    prompt = (
        "Bonjour, je cherche un vieux film d'animation. "
        "Le Voyage d'Edgar dans la forêt magique ?"
    )
    q = extract_lookup_query(prompt)
    assert "Edgar" in q
    assert "forêt" in q.lower() or "foret" in q.lower() or "Voyage" in q


def test_extract_after_colon() -> None:
    q = extract_lookup_query(
        "Bonjour, je cherche un vieux film d'animation : Le Voyage d'Edgar dans la forêt magique ?"
    )
    assert q.startswith("Le Voyage")
    assert "Edgar" in q
    assert "vieux film" not in q.lower()


def test_extract_quoted() -> None:
    assert extract_lookup_query('Tu connais le film « Totoro » ?') == "Totoro"


def test_format_grounding_anti_interrogatoire() -> None:
    block = format_web_lookup_grounding(
        query="Edgar forêt",
        hits=[{"title": "Un titre", "snippet": "desc", "url": "https://example.test"}],
        sources=["wikipedia_fr"],
    )
    assert "interdit interrogatoire" in block
    assert "Un titre" in block
    assert "\n" not in block


@pytest.mark.asyncio
async def test_enrich_ask_prompt_injects(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_fetch(query: str, *, timeout_s: float = 4.0) -> dict:
        return {
            "ok": True,
            "query": query,
            "hits": [{"title": "Hit", "snippet": "s", "url": "https://ex.test", "source": "wikipedia_fr"}],
            "sources": ["wikipedia_fr"],
            "ms": 12.0,
            "error": None,
        }

    monkeypatch.setattr("services.web_lookup.fetch_web_lookup", _fake_fetch)
    prompt = "Je cherche un film d'animation : Le Voyage d'Edgar"
    enriched, meta = await enrich_ask_prompt(prompt)
    assert meta is not None
    assert meta["hit_count"] == 1
    assert "interdit interrogatoire" in enriched
    assert "Je cherche un film" in enriched
    assert "\n" not in enriched


@pytest.mark.asyncio
async def test_enrich_skips_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LBG_ORCH_WEB_LOOKUP", "0")
    enriched, meta = await enrich_ask_prompt("Je cherche un film d'animation Edgar")
    assert meta is None
    assert enriched == "Je cherche un film d'animation Edgar"
