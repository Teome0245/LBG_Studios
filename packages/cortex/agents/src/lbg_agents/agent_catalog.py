"""C10 catalog read-only + C11 tick matrix (SpaceMolt → Chœur / sidecar).

Lectures gratuites ; mutations monde = ``tick_cost=mutation``. Stub local —
pas de dépendance sidecar ``:8791``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Literal

CatalogType = Literal["skills", "recipes", "npcs", "poi"]
TickCost = Literal["free", "mutation"]
ActionKind = Literal["query", "mutation"]

CATALOG_TYPES: tuple[str, ...] = ("skills", "recipes", "npcs", "poi")

# C11 — contrat machine-readable (voir design_c10_c11_catalog_tick.md).
TICK_MATRIX: dict[str, dict[str, Any]] = {
    "catalog": {"kind": "query", "tick_cost": "free", "requires_tick": False},
    "get_guide": {"kind": "query", "tick_cost": "free", "requires_tick": False},
    "snapshot": {"kind": "query", "tick_cost": "free", "requires_tick": False},
    "self/status": {"kind": "query", "tick_cost": "free", "requires_tick": False},
    "quests/board": {"kind": "query", "tick_cost": "free", "requires_tick": False},
    "quests/status": {"kind": "query", "tick_cost": "free", "requires_tick": False},
    "inventory/list": {"kind": "query", "tick_cost": "free", "requires_tick": False},
    "skills/list": {"kind": "query", "tick_cost": "free", "requires_tick": False},
    "relation_memory/list": {"kind": "query", "tick_cost": "free", "requires_tick": False},
    "npc/registry": {"kind": "query", "tick_cost": "free", "requires_tick": False},
    "move_to": {"kind": "mutation", "tick_cost": "mutation", "requires_tick": True},
    "quests/accept": {"kind": "mutation", "tick_cost": "mutation", "requires_tick": True},
    "quests/progress": {"kind": "mutation", "tick_cost": "mutation", "requires_tick": True},
    "quests/complete": {"kind": "mutation", "tick_cost": "mutation", "requires_tick": True},
    "craft/start": {"kind": "mutation", "tick_cost": "mutation", "requires_tick": True},
    "craft/complete": {"kind": "mutation", "tick_cost": "mutation", "requires_tick": True},
    "survey/execute": {"kind": "mutation", "tick_cost": "mutation", "requires_tick": True},
    "hunt/engage": {"kind": "mutation", "tick_cost": "mutation", "requires_tick": True},
    "tip_stage": {"kind": "mutation", "tick_cost": "mutation", "requires_tick": True},
    "talk_npc": {"kind": "mutation", "tick_cost": "mutation", "requires_tick": True},
    "trade/offer": {"kind": "mutation", "tick_cost": "mutation", "requires_tick": True},
    "salvage/loot": {"kind": "mutation", "tick_cost": "mutation", "requires_tick": True},
    "relation_memory/append": {"kind": "mutation", "tick_cost": "mutation", "requires_tick": True},
}

_PLAYSTYLE_GUIDES: dict[str, dict[str, Any]] = {
    "prospecteur": {
        "playstyle": "prospecteur",
        "profession_id": "prospecteur",
        "loop": "survey dunes → ressources → vendeur / craft",
        "hub_actions": ["survey/execute", "inventory/list", "trade/offer", "craft/start"],
    },
    "artisan": {
        "playstyle": "artisan",
        "profession_id": "artisan",
        "loop": "atelier → schematic novices → kit / pièce",
        "hub_actions": ["craft/start", "craft/complete", "inventory/list", "catalog"],
    },
    "scene": {
        "playstyle": "scene",
        "profession_id": "scene",
        "loop": "Talen / Perle → danse ou tip → réconfort moral",
        "hub_actions": ["tip_stage", "talk_npc", "move_to"],
    },
    "medecin": {
        "playstyle": "medecin",
        "profession_id": "medecin",
        "loop": "clinique → kits terrain → escort blessé (backlog)",
        "hub_actions": ["craft/start", "talk_npc", "quests/accept"],
    },
    "scout": {
        "playstyle": "scout",
        "profession_id": "prospecteur",
        "loop": "chasse légère, camp, faune portes",
        "hub_actions": ["hunt/engage", "survey/execute", "move_to"],
        "alias_of": "prospecteur",
    },
}

_m10_cache: dict[str, Any] | None = None
_npc_cache: list[dict[str, Any]] | None = None
_poi_cache: list[dict[str, Any]] | None = None


def reset_cache() -> None:
    global _m10_cache, _npc_cache, _poi_cache
    _m10_cache = None
    _npc_cache = None
    _poi_cache = None


def cortex_root() -> Path:
    # lbg_agents/agent_catalog.py → parents[3] = packages/cortex
    return Path(__file__).resolve().parents[3]


def m10_catalog_path() -> Path:
    raw = os.environ.get("LBG_M10_CATALOG_PATH", "").strip()
    if raw:
        return Path(raw)
    root = cortex_root()
    # Studios : content/m10/… · Prime /opt/LBG_IA_MMO : content/core3/…
    for cand in (
        root / "content" / "m10" / "m10_skills_catalog.json",
        root / "content" / "core3" / "m10_skills_catalog.json",
    ):
        if cand.is_file():
            return cand
    return root / "content" / "m10" / "m10_skills_catalog.json"


def npc_registry_path() -> Path:
    raw = os.environ.get("LBG_DIALOGUE_NPC_REGISTRY_PATH", "").strip()
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parent / "npc_registry.json"


def poi_catalog_path() -> Path:
    raw = os.environ.get("LBG_POI_CATALOG_PATH", "").strip()
    if raw:
        return Path(raw)
    # packages/prime-client/assets/maps/scrapaltai_pois.json
    return cortex_root().parent / "prime-client" / "assets" / "maps" / "scrapaltai_pois.json"


def world_poi_stub_dir() -> Path:
    return cortex_root() / "content" / "world"


def classify_action(action: str) -> dict[str, Any]:
    """Retourne le flag context C11 pour une action (ou unknown → mutation prudente)."""
    key = (action or "").strip()
    row = TICK_MATRIX.get(key)
    if row is None:
        return {
            "action": key or "unknown",
            "kind": "mutation",
            "tick_cost": "mutation",
            "requires_tick": True,
            "known": False,
        }
    return {
        "action": key,
        "kind": row["kind"],
        "tick_cost": row["tick_cost"],
        "requires_tick": bool(row["requires_tick"]),
        "known": True,
    }


def tick_context_for(action: str) -> dict[str, Any]:
    """Sous-objet ``context`` à injecter dans les réponses wire."""
    c = classify_action(action)
    return {
        "tick_cost": c["tick_cost"],
        "requires_tick": c["requires_tick"],
        "kind": c["kind"],
        "action": c["action"],
    }


def tick_matrix_rows() -> list[dict[str, Any]]:
    rows = [classify_action(k) for k in sorted(TICK_MATRIX.keys())]
    return rows


def is_query(action: str) -> bool:
    return classify_action(action).get("kind") == "query"


def is_mutation(action: str) -> bool:
    return classify_action(action).get("kind") == "mutation"


def _load_m10() -> dict[str, Any]:
    global _m10_cache
    if _m10_cache is not None:
        return _m10_cache
    out: dict[str, Any] = {}
    try:
        data = json.loads(m10_catalog_path().read_text(encoding="utf-8"))
        if isinstance(data, dict):
            out = data
    except Exception:
        out = {}
    _m10_cache = out
    return out


def _skills_items() -> list[dict[str, Any]]:
    data = _load_m10()
    items: list[dict[str, Any]] = []
    professions = data.get("professions")
    if isinstance(professions, list):
        for row in professions:
            if not isinstance(row, dict):
                continue
            pid = row.get("id")
            if not (isinstance(pid, str) and pid.strip()):
                continue
            items.append(
                {
                    "id": pid.strip(),
                    "name": row.get("name"),
                    "tree": row.get("tree"),
                    "priority": row.get("priority"),
                    "boxes": row.get("boxes"),
                    "kind": "profession",
                }
            )
    skills = data.get("skills")
    if isinstance(skills, list):
        for row in skills:
            if not isinstance(row, dict):
                continue
            sid = row.get("id")
            if not (isinstance(sid, str) and sid.strip()):
                continue
            items.append(
                {
                    "id": sid.strip(),
                    "name": row.get("name"),
                    "box": row.get("box") or row.get("requires_box"),
                    "unlocks_schematics": row.get("unlocks_schematics"),
                    "kind": "skill_box",
                }
            )
    return items


def _recipes_items() -> list[dict[str, Any]]:
    data = _load_m10()
    schematics = data.get("schematics")
    if not isinstance(schematics, list):
        return []
    items: list[dict[str, Any]] = []
    for row in schematics:
        if not isinstance(row, dict):
            continue
        rid = row.get("id")
        if not (isinstance(rid, str) and rid.strip()):
            continue
        items.append(
            {
                "id": rid.strip(),
                "name": row.get("name"),
                "category": row.get("category"),
                "requires_skill": row.get("requires_skill"),
                "requires_box": row.get("requires_box"),
                "inputs": row.get("inputs"),
                "output": row.get("output"),
                "kind": "schematic",
            }
        )
    return items


def _npc_summary(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "name": row.get("name"),
        "role": row.get("role"),
        "zone": row.get("zone"),
        "faction": row.get("faction"),
        "summary": row.get("summary"),
        "pilot_id": (row.get("core3_reference") or {}).get("pilot_id")
        if isinstance(row.get("core3_reference"), dict)
        else None,
    }


def _npcs_items() -> list[dict[str, Any]]:
    global _npc_cache
    if _npc_cache is not None:
        return _npc_cache
    out: list[dict[str, Any]] = []
    try:
        data = json.loads(npc_registry_path().read_text(encoding="utf-8"))
    except Exception:
        _npc_cache = out
        return out
    rows = data.get("npcs") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        _npc_cache = out
        return out
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get("id"), str):
            out.append(_npc_summary(row))
    out.sort(key=lambda x: str(x.get("id", "")))
    _npc_cache = out
    return out


def _poi_from_scrapaltai() -> list[dict[str, Any]]:
    path = poi_catalog_path()
    out: list[dict[str, Any]] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return out
    rows = data.get("pois") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        return out
    for row in rows:
        if not isinstance(row, dict):
            continue
        pid = row.get("id")
        if not (isinstance(pid, str) and pid.strip()):
            continue
        out.append(
            {
                "id": pid.strip(),
                "label": row.get("label"),
                "kind": row.get("kind"),
                "x": row.get("x"),
                "z": row.get("z"),
                "group": row.get("group"),
                "active": row.get("active"),
                "essential": row.get("essential"),
                "source": "scrapaltai_pois",
            }
        )
    return out


def _poi_from_world_stubs() -> list[dict[str, Any]]:
    d = world_poi_stub_dir()
    out: list[dict[str, Any]] = []
    if not d.is_dir():
        return out
    for path in sorted(d.glob("poi_*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        pid = data.get("id")
        if not (isinstance(pid, str) and pid.strip()):
            continue
        placement = data.get("placement") if isinstance(data.get("placement"), dict) else {}
        out.append(
            {
                "id": pid.strip(),
                "label": data.get("label"),
                "kind": data.get("kind"),
                "x": placement.get("x"),
                "z": placement.get("z"),
                "group": placement.get("group") or data.get("hub"),
                "active": placement.get("active"),
                "essential": placement.get("essential"),
                "ticket": data.get("ticket"),
                "status": data.get("status"),
                "source": path.name,
            }
        )
    return out


def _pois_items() -> list[dict[str, Any]]:
    global _poi_cache
    if _poi_cache is not None:
        return _poi_cache
    by_id: dict[str, dict[str, Any]] = {}
    for row in _poi_from_scrapaltai():
        by_id[str(row["id"])] = row
    for row in _poi_from_world_stubs():
        # stubs content écrasent / enrichissent (ex. C8 salvage)
        by_id[str(row["id"])] = row
    out = sorted(by_id.values(), key=lambda x: str(x.get("id", "")))
    _poi_cache = out
    return out


def catalog(type_: str) -> dict[str, Any]:
    """Catalogue read-only C10 — ``type`` ∈ skills|recipes|npcs|poi."""
    t = (type_ or "").strip().lower()
    if t not in CATALOG_TYPES:
        return {
            "ok": False,
            "error": "bad_type",
            "hint": f"type doit être l'un de {list(CATALOG_TYPES)}",
            "type": t,
            **{k: v for k, v in tick_context_for("catalog").items() if k != "action"},
            "context": tick_context_for("catalog"),
        }
    loaders = {
        "skills": _skills_items,
        "recipes": _recipes_items,
        "npcs": _npcs_items,
        "poi": _pois_items,
    }
    items = loaders[t]()
    ctx = tick_context_for("catalog")
    return {
        "ok": True,
        "type": t,
        "count": len(items),
        "items": items,
        "tick_cost": ctx["tick_cost"],
        "requires_tick": ctx["requires_tick"],
        "context": ctx,
    }


def get_guide(playstyle: str) -> dict[str, Any]:
    """Guide playstyle hub (data M10, pas hallucination)."""
    key = (playstyle or "").strip().lower()
    ctx = tick_context_for("get_guide")
    guide = _PLAYSTYLE_GUIDES.get(key)
    if guide is None:
        return {
            "ok": False,
            "error": "unknown_playstyle",
            "hint": f"playstyle ∈ {sorted(_PLAYSTYLE_GUIDES.keys())}",
            "playstyle": key,
            "tick_cost": ctx["tick_cost"],
            "requires_tick": ctx["requires_tick"],
            "context": ctx,
        }
    # Enrichir avec nom profession M10 si dispo.
    prof_id = guide.get("profession_id")
    prof_name = None
    for row in _skills_items():
        if row.get("kind") == "profession" and row.get("id") == prof_id:
            prof_name = row.get("name")
            break
    body = dict(guide)
    if prof_name:
        body["profession_name"] = prof_name
    return {
        "ok": True,
        "guide": body,
        "tick_cost": ctx["tick_cost"],
        "requires_tick": ctx["requires_tick"],
        "context": ctx,
    }


def list_playstyles() -> list[str]:
    return sorted(_PLAYSTYLE_GUIDES.keys())


def tick_matrix_payload() -> dict[str, Any]:
    """Réponse HTTP C11 (dialogue + sidecar ``:8791``)."""
    rows = tick_matrix_rows()
    return {
        "ok": True,
        "count": len(rows),
        "actions": rows,
        "flag_context": {
            "tick_cost": "free|mutation",
            "requires_tick": "bool",
            "kind": "query|mutation",
            "action": "string",
        },
        "design": "packages/cortex/docs/design_c10_c11_catalog_tick.md",
    }


def http_get_dispatch(path: str, query: dict[str, list[str]] | None = None) -> tuple[int, dict[str, Any]] | None:
    """Routes C10/C11 partagées : ``/catalog``, ``/guide``, ``/tick-matrix`` (+ alias ``/v1/…``).

    Retourne ``None`` si le path n'est pas géré (le caller continue sa table de routes).
    ``query`` = ``urllib.parse.parse_qs`` (listes de valeurs).
    """
    p = (path or "").rstrip("/") or "/"
    qs = query or {}

    def _first(key: str, default: str = "") -> str:
        vals = qs.get(key) or []
        return str(vals[0]) if vals else default

    aliases = {
        "/v1/catalog": "/catalog",
        "/v1/guide": "/guide",
        "/v1/tick-matrix": "/tick-matrix",
    }
    p = aliases.get(p, p)

    if p == "/catalog":
        payload = catalog(_first("type", "skills"))
        return (200 if payload.get("ok") else 400, payload)
    if p == "/guide":
        payload = get_guide(_first("playstyle", "prospecteur"))
        return (200 if payload.get("ok") else 404, payload)
    if p == "/tick-matrix":
        return (200, tick_matrix_payload())
    return None
