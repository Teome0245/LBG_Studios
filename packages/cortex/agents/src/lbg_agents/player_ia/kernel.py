"""Noyau Joueur IA — perception → décision → action → mémoire.

Aucune dépendance Godot. L'environnement est injecté (adapter).
Décision = politique allowlistée (playstyle + observations), pas un LLM
sur les mutations dures.
"""

from __future__ import annotations

from typing import Any

from lbg_agents.player_ia.contract import (
    ACTION_CRAFT,
    ACTION_IDLE,
    ACTION_INTERACT,
    ACTION_MOVE,
    ACTION_NOTE,
    ACTION_SAY,
    ACTION_TRADE,
    EnvironmentAdapter,
    make_action,
    validate_action,
)


class AgentMemory:
    def __init__(self) -> None:
        self.entries: list[dict[str, Any]] = []

    def remember(self, kind: str, payload: dict[str, Any]) -> None:
        self.entries.append({"kind": kind, **payload})

    def last(self, kind: str | None = None) -> dict[str, Any] | None:
        for item in reversed(self.entries):
            if kind is None or item.get("kind") == kind:
                return item
        return None


class PlayerAgentKernel:
    def __init__(
        self,
        agent_id: str,
        *,
        playstyle: str = "prospecteur",
        memory: AgentMemory | None = None,
    ) -> None:
        self.agent_id = agent_id
        self.playstyle = playstyle
        self.memory = memory or AgentMemory()

    def decide(self, observation: dict[str, Any]) -> dict[str, Any]:
        events = observation.get("active_events") or []
        pois = observation.get("nearby_pois") or []
        inventory = observation.get("inventory") or []
        desk = observation.get("desk") or {}

        if self.playstyle == "studio_desk" or observation.get("zone_id") == "studio_desk":
            title = str(desk.get("focus_title") or "")
            if title:
                return make_action(
                    ACTION_NOTE,
                    text=f"focus:{title[:80]}",
                    channel="studio",
                )
            last_user = str(desk.get("last_user_line") or "").strip()
            if last_user:
                return make_action(ACTION_SAY, message="vu", channel="studio")
            return make_action(ACTION_IDLE)

        if events:
            poi_id = str(events[0].get("poi_id") or (pois[0].get("id") if pois else ""))
            if poi_id:
                return make_action(ACTION_MOVE, poi_id=poi_id, goal="event")
            return make_action(ACTION_SAY, message="Quelqu'un a vu ça ?")

        if self.playstyle == "artisan":
            if any(str(i.get("id")) == "scrap_metal" and int(i.get("qty") or 0) >= 2 for i in inventory):
                return make_action(ACTION_CRAFT, recipe_id="kit_reparation_mecatronique")
            bench = next((p for p in pois if "craft" in str(p.get("id", "")).lower() or "hangar" in str(p.get("id", "")).lower()), None)
            if bench:
                return make_action(ACTION_INTERACT, poi_id=str(bench["id"]))

        if self.playstyle == "scene":
            cantina = next((p for p in pois if "cantina" in str(p.get("id", "")).lower() or "perle" in str(p.get("id", "")).lower()), None)
            if cantina:
                return make_action(ACTION_MOVE, poi_id=str(cantina["id"]), goal="leisure")
            return make_action(ACTION_SAY, message="Un verre à La Perle ?")

        vendor = next((e for e in (observation.get("nearby_entities") or []) if e.get("is_vendor")), None)
        if vendor and any(int(i.get("qty") or 0) > 0 for i in inventory):
            sku = next((i for i in inventory if int(i.get("qty") or 0) > 0), None)
            listed = int((sku or {}).get("listed_price") or 10)
            return make_action(
                ACTION_TRADE,
                vendor_id=str(vendor.get("eid") or vendor.get("name") or "vendor"),
                sku_id=str((sku or {}).get("id") or "scrap_metal"),
                listed_price=listed,
                offer_price=listed,
            )

        if pois:
            return make_action(ACTION_MOVE, poi_id=str(pois[0]["id"]), goal="explore")
        return make_action(ACTION_IDLE)

    def tick(self, adapter: EnvironmentAdapter) -> dict[str, Any]:
        observation = adapter.get_observation(self.agent_id)
        self.memory.remember("observe", {"observation": observation, "adapter": adapter.adapter_id})
        action = self.decide(observation)
        blocked = validate_action(action)
        if blocked is not None:
            self.memory.remember("reject", blocked)
            return {
                "ok": False,
                "agent_id": self.agent_id,
                "adapter": adapter.adapter_id,
                "observation": observation,
                "action": action,
                "result": blocked,
            }
        result = adapter.perform_action(self.agent_id, action)
        self.memory.remember("act", {"action": action, "result": result})
        return {
            "ok": bool(result.get("ok", False)),
            "agent_id": self.agent_id,
            "adapter": adapter.adapter_id,
            "observation": observation,
            "action": action,
            "result": result,
        }
