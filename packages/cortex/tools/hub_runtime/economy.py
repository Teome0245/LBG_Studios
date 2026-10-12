"""Inventaire + quêtes hub (hors Core3) — contrats sidecar M10 / board Daan."""

from __future__ import annotations

import copy
import json
import os
import threading
from pathlib import Path
from typing import Any

_DEFAULT_INV: list[dict[str, Any]] = [
    {"id": "scrap_metal", "name": "Ferraille", "qty": 4, "icon": "copper"},
    {"id": "binding_tape", "name": "Ruban de liaison", "qty": 2, "icon": "screw"},
    {"id": "dried_grain", "name": "Grain séché", "qty": 4, "icon": "ration"},
    {"id": "water_capsule", "name": "Capsule d'eau", "qty": 2, "icon": "kit"},
]

_DEFAULT_SKILLS = [
    "prospecteur_r1",
    "artisan_rue_r1",
    "medecine_camp_r1",
    "pilotage_shuttle_r1",
]


def _state_dir() -> Path:
    env = os.environ.get("LBG_HUB_STATE_DIR", "").strip()
    if env:
        return Path(env)
    # Local / CI : writable sous tools/hub_runtime/data
    local = Path(__file__).resolve().parent / "data"
    remote = Path("/opt/lbg-hub-runtime/data")
    if remote.is_dir() or os.environ.get("LBG_HUB_RUNTIME_PORT"):
        try:
            remote.mkdir(parents=True, exist_ok=True)
            return remote
        except OSError:
            pass
    local.mkdir(parents=True, exist_ok=True)
    return local


def _templates_path() -> Path:
    env = os.environ.get("LBG_HUB_QUESTS_JSON", "").strip()
    if env:
        return Path(env)
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "content" / "world" / "quests_lbg_templates.json",
        Path("/opt/lbg-hub-runtime/data/quests_lbg_templates.json"),
        Path("/opt/LBG_IA_MMO/content/world/quests_lbg_templates.json"),
    ]
    for p in candidates:
        if p.is_file():
            return p
    return candidates[0]


class HubEconomy:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._templates: list[dict[str, Any]] = []
        self._by_id: dict[str, dict[str, Any]] = {}
        self._players: dict[str, dict[str, Any]] = {}
        self.reload_templates()
        self._load_players()

    def _players_path(self) -> Path:
        return _state_dir() / "players_state.json"

    def _load_players(self) -> None:
        path = self._players_path()
        if not path.is_file():
            return
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(raw, dict):
            return
        players = raw.get("players") or {}
        if isinstance(players, dict):
            for k, v in players.items():
                if isinstance(v, dict):
                    self._players[str(k)] = v

    def _save_players(self) -> None:
        path = self._players_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "players": self._players,
            "saved_at": int(__import__("time").time()),
        }
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)

    def reload_templates(self) -> None:
        path = _templates_path()
        self._templates = []
        self._by_id = {}
        if path.is_file():
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                for t in raw.get("templates") or []:
                    if isinstance(t, dict) and t.get("id"):
                        self._templates.append(t)
                        self._by_id[str(t["id"])] = t
        # fallback minimal si fichier absent
        if not self._templates:
            self._templates = [
                {
                    "id": "lh_survey_dunes",
                    "title": "Relevé hors palissade",
                    "template": "survey",
                    "objective": "Sortir porte est et revenir.",
                    "progress": [
                        {
                            "id": "exit",
                            "label": "Sortir vers la porte est",
                            "poi": "poi:lost_heaven_gate",
                            "radius_m": 70,
                        }
                    ],
                    "rewards": {"credits": 25, "items": [{"id": "scrap_metal", "qty": 2}]},
                    "giver_ids": ["npc:core3_daan_oth"],
                    "default_giver": "Daan Oth",
                    "next_steps": ["Sortir porte est", "Revenir"],
                }
            ]
            self._by_id = {str(t["id"]): t for t in self._templates}

    def _player(self, name: str) -> dict[str, Any]:
        key = (name or "Voyageur").strip() or "Voyageur"
        if key not in self._players:
            self._players[key] = {
                "inventory": copy.deepcopy(_DEFAULT_INV),
                "skills": list(_DEFAULT_SKILLS),
                "credits": 50,
                "active": [],  # list of {id, steps_done:[]}
                "completed": [],
            }
        return self._players[key]

    def inventory(self, player: str) -> dict[str, Any]:
        with self._lock:
            p = self._player(player)
            return {
                "ok": True,
                "player": player,
                "skills": list(p["skills"]),
                "inventory": copy.deepcopy(p["inventory"]),
                "source": "hub_runtime",
                "core3_live": False,
                "persisted": self._players_path().is_file(),
            }

    def board(self, giver: str, player: str) -> dict[str, Any]:
        with self._lock:
            quests = []
            for t in self._templates:
                givers = t.get("giver_ids") or []
                # board Daan : toutes templates hub (comme sidecar)
                q = {
                    "id": t["id"],
                    "title": t.get("title", t["id"]),
                    "template": t.get("template", ""),
                    "objective": t.get("objective", ""),
                    "next_steps": list(t.get("next_steps") or []),
                    "progress": list(t.get("progress") or []),
                    "rewards": copy.deepcopy(t.get("rewards") or {}),
                    "default_giver": t.get("default_giver", ""),
                    "giver_ids": list(givers),
                    "generated": False,
                }
                quests.append(q)
            return {
                "ok": True,
                "hub": "lost_heaven",
                "giver_id": giver or "npc:core3_daan_oth",
                "player": player,
                "quests": quests,
                "source": "hub_runtime",
            }

    def status(self, player: str) -> dict[str, Any]:
        with self._lock:
            p = self._player(player)
            return {
                "ok": True,
                "player": player,
                "credits": int(p["credits"]),
                "active": copy.deepcopy(p["active"]),
                "completed": list(p["completed"]),
                "generated_offers": [],
                "generated_by_id": {},
                "board_rotation": 0,
                "source": "hub_runtime",
                "persisted": self._players_path().is_file(),
            }

    def accept(self, player: str, quest_id: str, giver_id: str = "") -> dict[str, Any]:
        with self._lock:
            p = self._player(player)
            qid = str(quest_id)
            if qid not in self._by_id:
                return {"ok": False, "error": "unknown_quest", "quest_id": qid}
            for a in p["active"]:
                if a.get("id") == qid:
                    return {"ok": True, "already": True, "quest_id": qid, "active": copy.deepcopy(p["active"])}
            if qid in p["completed"]:
                return {"ok": False, "error": "already_completed", "quest_id": qid}
            entry = {
                "id": qid,
                "title": self._by_id[qid].get("title", qid),
                "giver_id": giver_id or "npc:core3_daan_oth",
                "steps_done": [],
                "progress": copy.deepcopy(self._by_id[qid].get("progress") or []),
            }
            p["active"].append(entry)
            self._save_players()
            return {"ok": True, "quest_id": qid, "active": copy.deepcopy(p["active"]), "source": "hub_runtime"}

    def progress(self, player: str, quest_id: str, step_id: str) -> dict[str, Any]:
        with self._lock:
            p = self._player(player)
            qid = str(quest_id)
            sid = str(step_id)
            for a in p["active"]:
                if a.get("id") != qid:
                    continue
                done = a.setdefault("steps_done", [])
                if sid not in done:
                    done.append(sid)
                self._save_players()
                return {"ok": True, "quest_id": qid, "step_id": sid, "steps_done": list(done), "source": "hub_runtime"}
            return {"ok": False, "error": "not_active", "quest_id": qid}

    def complete(self, player: str, quest_id: str) -> dict[str, Any]:
        with self._lock:
            p = self._player(player)
            qid = str(quest_id)
            tmpl = self._by_id.get(qid)
            if tmpl is None:
                return {"ok": False, "error": "unknown_quest"}
            found = None
            for a in p["active"]:
                if a.get("id") == qid:
                    found = a
                    break
            if found is None:
                return {"ok": False, "error": "not_active"}
            needed = [s.get("id") for s in (tmpl.get("progress") or []) if isinstance(s, dict)]
            done = set(found.get("steps_done") or [])
            if needed and not set(needed).issubset(done):
                return {
                    "ok": False,
                    "error": "incomplete",
                    "needed": needed,
                    "steps_done": list(done),
                }
            p["active"] = [a for a in p["active"] if a.get("id") != qid]
            if qid not in p["completed"]:
                p["completed"].append(qid)
            rewards = tmpl.get("rewards") or {}
            credits = int(rewards.get("credits", 0) or 0)
            p["credits"] += credits
            granted = []
            for it in rewards.get("items") or []:
                if not isinstance(it, dict):
                    continue
                iid = str(it.get("id", ""))
                qty = int(it.get("qty", 1))
                if not iid:
                    continue
                self._add_item(p, iid, qty, str(it.get("name", iid)))
                granted.append({"id": iid, "qty": qty})
            self._save_players()
            return {
                "ok": True,
                "quest_id": qid,
                "credits": p["credits"],
                "credits_gained": credits,
                "items": granted,
                "inventory": copy.deepcopy(p["inventory"]),
                "source": "hub_runtime",
            }

    def tip(self, player: str, quest_id: str, amount: int = 2) -> dict[str, Any]:
        with self._lock:
            p = self._player(player)
            amt = max(0, int(amount))
            if p["credits"] < amt:
                return {"ok": False, "error": "insufficient_credits", "credits": p["credits"]}
            p["credits"] -= amt
            self._save_players()
            return {
                "ok": True,
                "quest_id": quest_id,
                "amount": amt,
                "credits": p["credits"],
                "source": "hub_runtime",
            }

    def _add_item(self, p: dict[str, Any], item_id: str, qty: int, name: str = "") -> None:
        for it in p["inventory"]:
            if it.get("id") == item_id:
                it["qty"] = int(it.get("qty", 0)) + qty
                return
        p["inventory"].append(
            {"id": item_id, "name": name or item_id, "qty": qty, "icon": "copper"}
        )

    def craft_combine(self, player: str, recipe_id: str = "") -> dict[str, Any]:
        """Stub craft — consomme ferraille+ruban → kit_reparation."""
        with self._lock:
            p = self._player(player)
            need = {"scrap_metal": 1, "binding_tape": 1}
            for iid, q in need.items():
                have = next((int(i.get("qty", 0)) for i in p["inventory"] if i.get("id") == iid), 0)
                if have < q:
                    return {"ok": False, "error": "missing_ingredients", "need": need}
            for iid, q in need.items():
                for it in p["inventory"]:
                    if it.get("id") == iid:
                        it["qty"] = int(it["qty"]) - q
            p["inventory"] = [i for i in p["inventory"] if int(i.get("qty", 0)) > 0]
            crafted = {"id": "kit_reparation", "name": "Kit de réparation", "qty": 1, "icon": "kit"}
            self._add_item(p, crafted["id"], 1, crafted["name"])
            self._save_players()
            return {
                "ok": True,
                "recipe_id": recipe_id or "bind_scrap",
                "crafted": crafted,
                "inventory": copy.deepcopy(p["inventory"]),
                "source": "hub_runtime",
            }


ECONOMY = HubEconomy()
