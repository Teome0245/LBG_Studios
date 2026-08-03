"""Persona MMO : factual_status ne doit pas court-circuiter le dialogue PNJ."""

from __future__ import annotations

from lbg_agents import dialogue_llm


def test_mmo_persona_skips_via_resolve() -> None:
    assert dialogue_llm.resolve_lyra_engagement({"world_npc_id": "npc:odo"}) == "mmo_persona"
    assert (
        dialogue_llm.resolve_lyra_engagement(
            {"lyra_engagement": "mmo_persona", "world_npc_id": "npc:odo"}
        )
        == "mmo_persona"
    )
