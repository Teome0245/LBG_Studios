"""C2 — mémoire relations → memory_hint / world_hint."""

from __future__ import annotations

import json

from lbg_agents import dialogue_llm
from lbg_agents import relation_memory as rm


def test_memory_hint_for_jax_from_example_stub() -> None:
    rm.reset_cache()
    hint = rm.memory_hint_for("npc:core3_barman_jax", player_id="Lia")
    assert hint is not None
    assert "Cactus Noir" in hint or "Dette" in hint
    assert len(hint) <= 160


def test_world_hint_injection_jax() -> None:
    rm.reset_cache()
    inj = rm.world_hint_injection("npc:core3_barman_jax", player_id="Lia")
    assert inj is not None
    assert inj.startswith("Mémoire relation")
    assert "Cactus Noir" in inj or "Dette" in inj


def test_merge_into_context_sets_memory_hint() -> None:
    rm.reset_cache()
    ctx: dict = {
        "world_npc_id": "npc:core3_barman_jax",
        "world_hint": "Planète Scrapaltai, hub Lost Heaven.",
        "session_summary": {},
    }
    meta = rm.merge_into_context(ctx, actor_id="prime:Lia")
    assert meta.get("applied") is True
    assert "memory_hint" in ctx["session_summary"]
    assert "Cactus Noir" in ctx["session_summary"]["memory_hint"] or "Dette" in ctx[
        "session_summary"
    ]["memory_hint"]
    assert "Mémoire relation" in str(ctx.get("world_hint", ""))


def test_merge_preserves_existing_memory_hint() -> None:
    rm.reset_cache()
    ctx: dict = {
        "world_npc_id": "npc:core3_barman_jax",
        "session_summary": {"memory_hint": "aid_hunger,reputation_delta"},
    }
    rm.merge_into_context(ctx, actor_id="prime:Lia")
    assert ctx["session_summary"]["memory_hint"] == "aid_hunger,reputation_delta"


def test_build_prompt_includes_merged_relation_memory_hint() -> None:
    """Chemin backend merge → prompt (complète test_build_prompt_includes_memory_hint)."""
    rm.reset_cache()
    ctx: dict = {
        "world_npc_id": "npc:core3_barman_jax",
        "npc_name": "Jax Moro",
        "lyra_engagement": "mmo_persona",
        "planet_display": "Scrapaltai",
        "hub_city": "Lost Heaven",
        "session_summary": {},
    }
    rm.merge_into_context(ctx, actor_id="prime:Lia")
    p = dialogue_llm.build_system_prompt("Jax Moro", ctx)
    assert "Mémoire monde PNJ" in p
    assert "Cactus Noir" in p or "Dette" in p


def test_example_stub_validates_schema_shape() -> None:
    path = rm.default_memory_path()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data.get("schema_version") == 1
    assert isinstance(data.get("entries"), list)
    assert any(e.get("npc_id") == "npc:core3_barman_jax" for e in data["entries"])
