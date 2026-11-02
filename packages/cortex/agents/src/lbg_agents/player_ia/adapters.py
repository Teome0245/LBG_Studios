"""Adapters d'environnement pour le noyau O3.

1. GodotHubHttpAdapter — Lost Heaven via HTTP ``prime-hub`` :8787 (1er monde).
2. StudioDeskAdapter — bureau Compagnon (2e environnement, hors MMO).
3. SandboxAdapter — banc de tests déterministe (sans réseau).
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import httpx

from lbg_agents.player_ia.contract import (
    ACTION_CRAFT,
    ACTION_IDLE,
    ACTION_INTERACT,
    ACTION_MOVE,
    ACTION_NOTE,
    ACTION_SAY,
    ACTION_TRADE,
    make_observation,
    validate_action,
)


class SandboxAdapter:
    """Environnement mémoire — prouve que le noyau tourne sans Godot."""

    adapter_id = "sandbox"

    def __init__(self, zone_id: str = "sandbox_arena") -> None:
        self.zone_id = zone_id
        self.positions: dict[str, list[float]] = {}
        self.inventory: dict[str, list[dict[str, Any]]] = {}
        self.log: list[dict[str, Any]] = []
        self.pois = [{"id": "poi:sandbox_beacon", "distance": 12.0}]
        self.events: list[dict[str, Any]] = []

    def seed_inventory(self, agent_id: str, items: list[dict[str, Any]]) -> None:
        self.inventory[agent_id] = list(items)

    def get_observation(self, agent_id: str) -> dict[str, Any]:
        return make_observation(
            agent_id,
            position=self.positions.get(agent_id, [0.0, 0.0, 0.0]),
            zone_id=self.zone_id,
            nearby_pois=list(self.pois),
            active_events=list(self.events),
            inventory=list(self.inventory.get(agent_id, [])),
        )

    def perform_action(self, agent_id: str, action: dict[str, Any]) -> dict[str, Any]:
        blocked = validate_action(action)
        if blocked is not None:
            return blocked
        act = str(action.get("type"))
        if act == ACTION_MOVE:
            self.positions[agent_id] = [8.0, 0.0, 4.0]
        record = {"ok": True, "action": act, "agent_id": agent_id, "params": dict(action)}
        self.log.append(record)
        return record


class StudioDeskAdapter:
    """2e adapter : le bureau Compagnon n'est pas un MMO.

    Observations = focus fenêtre + dernière ligne utilisateur.
    Actions allowlistées = SAY / NOTE / IDLE (suggestions Studio, pas apply monde).
    """

    adapter_id = "studio_desk"

    def __init__(
        self,
        *,
        focus_title: str = "",
        last_user_line: str = "",
        companion_url: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.focus_title = focus_title
        self.last_user_line = last_user_line
        self.companion_url = (companion_url or "").rstrip("/")
        self._client = client
        self.notes: list[str] = []
        self.said: list[str] = []

    def set_focus(self, title: str) -> None:
        self.focus_title = title

    def get_observation(self, agent_id: str) -> dict[str, Any]:
        return make_observation(
            agent_id,
            zone_id="studio_desk",
            extra={
                "desk": {
                    "focus_title": self.focus_title,
                    "last_user_line": self.last_user_line,
                    "companion_url": self.companion_url,
                }
            },
        )

    def perform_action(self, agent_id: str, action: dict[str, Any]) -> dict[str, Any]:
        blocked = validate_action(action)
        if blocked is not None:
            return blocked
        act = str(action.get("type"))
        if act == ACTION_NOTE:
            text = str(action.get("text") or "").strip()
            self.notes.append(text)
            return {"ok": True, "action": act, "agent_id": agent_id, "note": text, "applied": False}
        if act == ACTION_SAY:
            msg = str(action.get("message") or "").strip()
            self.said.append(msg)
            posted = False
            if self._client is not None and self.companion_url:
                try:
                    res = self._client.post(
                        f"{self.companion_url}/api/ask",
                        json={"prompt": msg, "mode": "auto", "profile": "compagnon"},
                        timeout=8.0,
                    )
                    posted = res.status_code < 500
                except httpx.HTTPError:
                    posted = False
            return {
                "ok": True,
                "action": act,
                "agent_id": agent_id,
                "message": msg,
                "posted": posted,
                "applied_world": False,
            }
        if act == ACTION_IDLE:
            return {"ok": True, "action": act, "agent_id": agent_id, "idle": True}
        return {"ok": False, "action": act, "error": "unsupported_on_studio_desk"}


class GodotHubHttpAdapter:
    """1er adapter monde : peel HTTP prime-hub (aucune scène Godot dans le noyau)."""

    adapter_id = "godot_hub"

    def __init__(self, base_url: str = "http://192.168.0.246:8787", *, client: httpx.Client | None = None) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self._client = client

    def _url(self, path: str) -> str:
        return urljoin(self.base_url, path.lstrip("/"))

    def _get(self, path: str, **params: Any) -> dict[str, Any]:
        if self._client is None:
            return {}
        res = self._client.get(self._url(path), params=params, timeout=8.0)
        res.raise_for_status()
        data = res.json()
        return data if isinstance(data, dict) else {}

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        if self._client is None:
            return {"ok": False, "error": "no_http_client"}
        res = self._client.post(self._url(path), json=payload, timeout=8.0)
        if res.status_code >= 400:
            return {"ok": False, "error": f"http_{res.status_code}", "body": res.text[:300]}
        data = res.json()
        return data if isinstance(data, dict) else {"ok": True, "raw": data}

    def get_observation(self, agent_id: str) -> dict[str, Any]:
        health = self._get("/healthz")
        inv = self._get("/v1/inventory", player=agent_id)
        events = self._get("/v1/events/active")
        items = inv.get("inventory") if isinstance(inv.get("inventory"), list) else []
        active = []
        ev = events.get("active_event") if isinstance(events.get("active_event"), dict) else events
        if isinstance(ev, dict) and ev.get("active"):
            active.append(
                {
                    "event_id": ev.get("event_id"),
                    "title": ev.get("title"),
                    "poi_id": ev.get("poi") or ev.get("board_quest_id"),
                }
            )
        clock = {}
        if isinstance(health.get("active_event"), dict):
            clock = (health["active_event"].get("world_clock") or {}) if isinstance(health["active_event"], dict) else {}
        return make_observation(
            agent_id,
            zone_id="scrapaltai",
            inventory=list(items or []),
            active_events=active,
            extra={"world_clock": clock, "hub_ok": bool(health.get("ok"))},
        )

    def perform_action(self, agent_id: str, action: dict[str, Any]) -> dict[str, Any]:
        blocked = validate_action(action)
        if blocked is not None:
            return blocked
        act = str(action.get("type"))
        player = agent_id
        if act == ACTION_MOVE:
            poi = str(action.get("poi_id") or "")
            return self._post("/v1/bots/move_to", {"player": player, "poi_id": poi})
        if act == ACTION_SAY:
            return self._post("/v1/say", {"player": player, "text": str(action.get("message") or "")})
        if act == ACTION_INTERACT:
            return self._post("/v1/salvage", {"player": player, "poi_id": str(action.get("poi_id") or "")})
        if act == ACTION_TRADE:
            return self._post(
                "/v1/trade/offer",
                {
                    "player": player,
                    "vendor_id": action.get("vendor_id"),
                    "sku_id": action.get("sku_id"),
                    "offer_price": action.get("offer_price"),
                },
            )
        if act == ACTION_CRAFT:
            return self._post("/v1/craft/combine", {"player": player, "recipe_id": action.get("recipe_id")})
        if act == ACTION_IDLE:
            return {"ok": True, "action": act, "agent_id": agent_id, "idle": True}
        return {"ok": False, "error": "unsupported_on_godot_hub", "action": act}
