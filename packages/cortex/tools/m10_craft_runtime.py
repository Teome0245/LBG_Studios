"""Runtime inventaire + craft_combine M10 (stub local et sidecar 246).

Persistance bridge partagée: l'inventaire joueur est sauvegardé dans
``ia_bridge/inventory_players.json`` pour survivre aux redémarrages du sidecar.
"""
from __future__ import annotations

import json
import os
import threading
from copy import deepcopy
from pathlib import Path
from typing import Any

from core3_bridge_state import (
    bridge_dir,
    inventory_state_path,
    load_json_doc,
    player_items_path,
    save_json_doc,
)

_ROOT = Path(__file__).resolve().parents[1]  # packages/cortex (Studios) ou …/tools parent
_CANDIDATES = [
    _ROOT / "content" / "m10" / "m10_skills_catalog.json",
    Path("/opt/LBG_IA_MMO/content/core3/m10_skills_catalog.json"),
    Path("/opt/LBG_IA_MMO/content/m10/m10_skills_catalog.json"),
]
DEFAULT_CATALOG = next((p for p in _CANDIDATES if p.is_file()), _CANDIDATES[0])
DEFAULT_PLAYER = os.environ.get("LBG_M10_STUB_PLAYER", "local")

_lock = threading.Lock()
_catalog: dict[str, Any] = {}
_players: dict[str, dict[str, Any]] = {}


def catalog_path() -> Path:
    return Path(
        os.environ.get("CORE3_IA_M10_SKILLS_CATALOG_JSON")
        or os.environ.get("LBG_M10_CATALOG_JSON")
        or DEFAULT_CATALOG
    )


def load_catalog(path: Path | None = None) -> dict[str, Any]:
    global _catalog
    p = path or catalog_path()
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"catalog invalide: {p}")
    _catalog = raw
    return _catalog


def ensure_catalog() -> dict[str, Any]:
    if not _catalog:
        load_catalog()
    return _catalog


def _resource_name(rid: str) -> str:
    cat = ensure_catalog()
    for row in cat.get("resources_stub") or []:
        if isinstance(row, dict) and str(row.get("id")) == rid:
            return str(row.get("name") or rid)
    for row in cat.get("schematics") or []:
        if isinstance(row, dict) and str(row.get("id")) == rid:
            return str(row.get("name") or rid)
    return rid


def _schematic_by_id(sid: str) -> dict[str, Any] | None:
    for row in ensure_catalog().get("schematics") or []:
        if isinstance(row, dict) and str(row.get("id")) == sid:
            return row
    return None


def seed_player(player: str) -> dict[str, Any]:
    inv = [
        {"id": "scrap_metal", "name": _resource_name("scrap_metal"), "qty": 4, "icon": "copper"},
        {"id": "binding_tape", "name": _resource_name("binding_tape"), "qty": 2, "icon": "screw"},
        {"id": "dried_grain", "name": _resource_name("dried_grain"), "qty": 4, "icon": "ration"},
        {"id": "water_capsule", "name": _resource_name("water_capsule"), "qty": 2, "icon": "kit"},
    ]
    return {
        "player": player,
        "skills": ["prospecteur_r1", "artisan_rue_r1", "medecine_camp_r1", "pilotage_shuttle_r1"],
        "inventory": inv,
    }


def _normalize_player_state(player: str, raw: Any) -> dict[str, Any]:
    seeded = seed_player(player)
    if not isinstance(raw, dict):
        return seeded
    inv = raw.get("inventory")
    skills = raw.get("skills")
    return {
        "player": str(raw.get("player") or player),
        "skills": [str(x) for x in skills if isinstance(x, str) and str(x).strip()] if isinstance(skills, list) else seeded["skills"],
        "inventory": [dict(x) for x in inv if isinstance(x, dict)] if isinstance(inv, list) else seeded["inventory"],
    }


def _load_players_from_bridge() -> dict[str, dict[str, Any]]:
    doc = load_json_doc(inventory_state_path())
    rows = doc.get("players")
    out: dict[str, dict[str, Any]] = {}
    if isinstance(rows, dict):
        for player, state in rows.items():
            out[str(player)] = _normalize_player_state(str(player), state)
    return out


def _save_players_to_bridge() -> None:
    save_json_doc(
        inventory_state_path(),
        {
            "kind": "core3_inventory_bridge",
            "bridge_dir": str(bridge_dir()),
            "players": _players,
        },
    )


def ensure_player(player: str) -> dict[str, Any]:
    if not _players:
        _players.update(_load_players_from_bridge())
    if player not in _players:
        _players[player] = seed_player(player)
        _save_players_to_bridge()
    return _players[player]


def reset_player(player: str) -> dict[str, Any]:
    with _lock:
        _players[player] = seed_player(player)
        _save_players_to_bridge()
        return deepcopy(_players[player])


def _inventory_aliases(player: str) -> list[str]:
    raw = str(player or "").strip()
    names: list[str] = []
    seen: set[str] = set()

    def _add(name: str) -> None:
        key = name.strip()
        if not key:
            return
        low = key.lower()
        if low in seen:
            return
        seen.add(low)
        names.append(key)

    _add(raw)
    bot = os.environ.get("CORE3_IA_BOT_CHARACTER", "").strip()
    if raw.lower() in {"", "local", "player", "me"}:
        _add(bot)
        _add("Lia")
        _add("Teome")
    return names


def _normalize_core3_item(row: dict[str, Any]) -> dict[str, Any] | None:
    iid = str(row.get("id") or "").strip()
    if not iid:
        return None
    try:
        qty = int(row.get("qty") or 0)
    except (TypeError, ValueError):
        qty = 0
    if qty <= 0:
        return None
    return {
        "id": iid,
        "name": str(row.get("name") or iid),
        "qty": qty,
        "icon": str(row.get("icon") or "misc"),
        "template": str(row.get("template") or ""),
    }


def _core3_live_overlay(player: str) -> dict[str, Any] | None:
    """Sac Core3 si le dump Lua marque le perso *online* ; sinon None (JSON local)."""
    if os.environ.get("LBG_INVENTORY_CORE3", "1").strip().lower() in {"0", "false", "no"}:
        return None
    doc = load_json_doc(player_items_path())
    rows = doc.get("players")
    if not isinstance(rows, dict) or not rows:
        return None
    by_low = {str(k).lower(): (str(k), v) for k, v in rows.items()}
    for alias in _inventory_aliases(player):
        hit = by_low.get(alias.lower())
        if hit is None:
            continue
        _key, raw = hit
        if not isinstance(raw, dict) or raw.get("online") is not True:
            continue
        items_in = raw.get("inventory")
        items: list[dict[str, Any]] = []
        if isinstance(items_in, list):
            for row in items_in:
                if isinstance(row, dict):
                    norm = _normalize_core3_item(row)
                    if norm is not None:
                        items.append(norm)
        skills_in = raw.get("skills")
        skills = [str(x) for x in skills_in if isinstance(x, str) and x.strip()] if isinstance(skills_in, list) else []
        try:
            count = int(raw.get("inventory_count") or len(items))
        except (TypeError, ValueError):
            count = len(items)
        return {
            "core3_player": _key,
            "inventory": items,
            "skills": skills,
            "inventory_count": count,
            "zone": str(raw.get("zone") or ""),
            "dump": str(player_items_path()),
            "dump_source": str(doc.get("source") or "core3_lua_inventory_v1"),
        }
    return None


def inventory_payload(player: str) -> dict[str, Any]:
    overlay = _core3_live_overlay(player)
    with _lock:
        state = deepcopy(ensure_player(player))
    if overlay is None:
        return {
            "ok": True,
            **state,
            "source": "core3_bridge_inventory",
            "core3_live": False,
            "persisted": True,
            "bridge_dir": str(bridge_dir()),
        }
    skills = overlay["skills"] or list(state.get("skills") or [])
    return {
        "ok": True,
        "player": player,
        "core3_player": overlay["core3_player"],
        "skills": skills,
        "inventory": overlay["inventory"],
        "inventory_count": overlay["inventory_count"],
        "zone": overlay["zone"],
        "source": "core3_lua_inventory",
        "core3_live": True,
        "dump": overlay["dump"],
        "dump_source": overlay["dump_source"],
        "persisted": True,
        "bridge_dir": str(bridge_dir()),
    }


def player_skills_payload(player: str) -> dict[str, Any]:
    overlay = _core3_live_overlay(player)
    with _lock:
        state = ensure_player(player)
        skills = list(state["skills"])
    if overlay is not None and overlay["skills"]:
        skills = list(overlay["skills"])
        source = "core3_lua_inventory"
        live = True
    else:
        source = "core3_bridge_inventory"
        live = False
    return {
        "ok": True,
        "player": player,
        "skills": skills,
        "source": source,
        "core3_live": live,
        "persisted": True,
        "bridge_dir": str(bridge_dir()),
    }


def _inv_qty(inv: list[dict[str, Any]], item_id: str) -> int:
    for row in inv:
        if str(row.get("id")) == item_id:
            return int(row.get("qty") or 0)
    return 0


def _inv_consume(inv: list[dict[str, Any]], item_id: str, qty: int) -> bool:
    for row in inv:
        if str(row.get("id")) != item_id:
            continue
        have = int(row.get("qty") or 0)
        if have < qty:
            return False
        left = have - qty
        if left <= 0:
            inv.remove(row)
        else:
            row["qty"] = left
        return True
    return False


def _inv_add(inv: list[dict[str, Any]], item_id: str, qty: int, *, name: str | None = None) -> None:
    icon_map = {
        "kit_reparation": "kit",
        "ration_compacte": "ration",
        "badge_quartier": "badge",
        "scrap_metal": "copper",
        "binding_tape": "screw",
        "dried_grain": "ration",
        "water_capsule": "kit",
    }
    for row in inv:
        if str(row.get("id")) == item_id:
            row["qty"] = int(row.get("qty") or 0) + qty
            return
    inv.append(
        {
            "id": item_id,
            "name": name or _resource_name(item_id),
            "qty": qty,
            "icon": icon_map.get(item_id, "misc"),
        }
    )


def craft_combine(player: str, schematic_id: str) -> dict[str, Any]:
    ensure_catalog()
    with _lock:
        state = ensure_player(player)
        schem = _schematic_by_id(schematic_id)
        if schem is None:
            return {"ok": False, "error": "unknown_schematic", "schematic_id": schematic_id}
        if schem.get("status") == "draft":
            return {"ok": False, "error": "schematic_draft", "schematic_id": schematic_id}
        req = str(schem.get("requires_skill") or "")
        if req and req not in state["skills"]:
            return {
                "ok": False,
                "error": "missing_skill",
                "requires_skill": req,
                "skills": list(state["skills"]),
            }
        inv = state["inventory"]
        inputs = schem.get("inputs") or []
        if not isinstance(inputs, list) or not inputs:
            return {"ok": False, "error": "no_inputs", "schematic_id": schematic_id}
        for inp in inputs:
            if not isinstance(inp, dict):
                return {"ok": False, "error": "bad_input"}
            iid = str(inp.get("id") or "")
            need = int(inp.get("qty") or 0)
            if not iid or need < 1:
                return {"ok": False, "error": "bad_input"}
            if _inv_qty(inv, iid) < need:
                return {
                    "ok": False,
                    "error": "missing_inputs",
                    "item_id": iid,
                    "need": need,
                    "have": _inv_qty(inv, iid),
                }
        for inp in inputs:
            assert isinstance(inp, dict)
            _inv_consume(inv, str(inp["id"]), int(inp["qty"]))
        out = schem.get("output") or {}
        if not isinstance(out, dict) or not out.get("id"):
            return {"ok": False, "error": "no_output"}
        oid = str(out["id"])
        oqty = int(out.get("qty") or 1)
        _inv_add(inv, oid, oqty, name=str(schem.get("name") or oid))
        _save_players_to_bridge()
        return {
            "ok": True,
            "player": player,
            "schematic_id": schematic_id,
            "crafted": {"id": oid, "name": schem.get("name"), "qty": oqty},
            "inventory": deepcopy(inv),
            "skills": list(state["skills"]),
            "source": "core3_bridge_inventory",
            "persisted": True,
            "bridge_dir": str(bridge_dir()),
        }
