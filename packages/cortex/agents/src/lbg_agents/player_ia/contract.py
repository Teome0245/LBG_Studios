"""Contrat d'environnement Joueurs IA (O3) — hors Godot.

Miroir Python du contrat GDScript ``AgentEnvironmentAdapter``.
Le noyau ne parle qu'à ce contrat ; Lost Heaven n'est qu'un adapter.
Les mutations dures (prix, dégâts, loot, craft forcé, quête, réputation)
ne passent pas par un LLM : elles sont allowlistées ou refusées.
"""

from __future__ import annotations

from typing import Any, Protocol

ACTION_MOVE = "MOVE"
ACTION_SAY = "SAY"
ACTION_EMOTE = "EMOTE"
ACTION_INTERACT = "INTERACT_POI"
ACTION_TRADE = "TRADE"
ACTION_CRAFT = "CRAFT"
ACTION_IDLE = "IDLE"
ACTION_FORMATION_FOLLOW = "FORMATION_FOLLOW"
ACTION_COVER_TARGET = "COVER_TARGET"
ACTION_TACTICAL_RETREAT = "TACTICAL_RETREAT"
ACTION_NOTE = "NOTE"

ALLOWED_ACTIONS = frozenset(
    {
        ACTION_MOVE,
        ACTION_SAY,
        ACTION_EMOTE,
        ACTION_INTERACT,
        ACTION_TRADE,
        ACTION_CRAFT,
        ACTION_IDLE,
        ACTION_FORMATION_FOLLOW,
        ACTION_COVER_TARGET,
        ACTION_TACTICAL_RETREAT,
        ACTION_NOTE,
    }
)

# Intentionnellement hors allowlist — refus déterministe, pas un appel LLM.
HARD_MUTATION_TYPES = frozenset(
    {
        "SET_PRICE",
        "DEAL_DAMAGE",
        "GRANT_LOOT",
        "FORCE_CRAFT",
        "COMPLETE_QUEST",
        "SET_REPUTATION",
        "APPLY_WORLD",
    }
)

TRADE_PRICE_DELTA_MAX = 0.15


def make_observation(
    agent_id: str,
    *,
    position: list[float] | None = None,
    zone_id: str = "default",
    health: int = 100,
    credits: int = 0,
    nearby_entities: list[dict[str, Any]] | None = None,
    nearby_pois: list[dict[str, Any]] | None = None,
    active_events: list[dict[str, Any]] | None = None,
    presence_dials: dict[str, Any] | None = None,
    inventory: list[dict[str, Any]] | None = None,
    team_context: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    obs: dict[str, Any] = {
        "agent_id": agent_id,
        "position": list(position or [0.0, 0.0, 0.0]),
        "zone_id": zone_id,
        "health": int(health),
        "credits": int(credits),
        "nearby_entities": list(nearby_entities or []),
        "nearby_pois": list(nearby_pois or []),
        "active_events": list(active_events or []),
        "presence_dials": dict(presence_dials or {}),
        "inventory": list(inventory or []),
        "team_context": dict(team_context or {}),
    }
    if extra:
        obs.update(extra)
    return obs


def make_action(action_type: str, **params: Any) -> dict[str, Any]:
    body = dict(params)
    body["type"] = action_type
    return body


def is_hard_mutation(action: dict[str, Any]) -> bool:
    return str(action.get("type", "")).upper() in HARD_MUTATION_TYPES


def validate_action(action: dict[str, Any]) -> dict[str, Any] | None:
    """None si OK, sinon dict d'erreur déterministe."""
    act_type = str(action.get("type", "")).upper()
    if act_type in HARD_MUTATION_TYPES:
        return {
            "ok": False,
            "error": "hard_mutation_blocked",
            "action": act_type,
            "rule": "no_free_llm_on_economy_combat_craft_quest_reputation",
        }
    if act_type not in ALLOWED_ACTIONS:
        return {"ok": False, "error": "action_not_allowlisted", "action": act_type}
    if act_type == ACTION_TRADE:
        listed = action.get("listed_price")
        offer = action.get("offer_price")
        if listed is not None and offer is not None:
            try:
                listed_f = float(listed)
                offer_f = float(offer)
            except (TypeError, ValueError):
                return {"ok": False, "error": "trade_price_invalid", "action": act_type}
            if listed_f > 0:
                delta = abs(offer_f - listed_f) / listed_f
                if delta > TRADE_PRICE_DELTA_MAX:
                    return {
                        "ok": False,
                        "error": "trade_price_out_of_band",
                        "action": act_type,
                        "delta": round(delta, 4),
                        "max": TRADE_PRICE_DELTA_MAX,
                    }
    return None


class EnvironmentAdapter(Protocol):
    adapter_id: str

    def get_observation(self, agent_id: str) -> dict[str, Any]: ...

    def perform_action(self, agent_id: str, action: dict[str, Any]) -> dict[str, Any]: ...
