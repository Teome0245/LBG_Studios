"""C10 catalog read-only + C11 tick matrix + TickGate (SpaceMolt → Chœur / sidecar).

Lectures gratuites ; mutations monde = ``tick_cost=mutation``.
Gate live : ``http_post_tick_guard`` (cooldown / file → ``429 tick_busy``).
"""

from __future__ import annotations

import json
import os
import threading
import time
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

# HTTP POST path → action catalogue C11 (sidecar :8791).
HTTP_POST_PATH_TO_ACTION: dict[str, str] = {
    "/v1/quests/accept": "quests/accept",
    "/v1/quests/progress": "quests/progress",
    "/v1/quests/complete": "quests/complete",
    "/v1/quests/tip": "tip_stage",
    "/v1/craft/combine": "craft/start",
    "/v1/hunt-yard/run": "hunt/engage",
    "/v1/hunt-yard/claim-quest": "hunt/engage",
}

# Enqueue body.action → action catalogue.
ENQUEUE_ACTION_TO_TICK: dict[str, str] = {
    "move_to": "move_to",
    "craft_combine": "craft/start",
    "craft/start": "craft/start",
    "craft/complete": "craft/complete",
    "survey": "survey/execute",
    "survey/execute": "survey/execute",
    "hunt": "hunt/engage",
    "hunt/engage": "hunt/engage",
    "tip_stage": "tip_stage",
    "talk_npc": "talk_npc",
    "trade/offer": "trade/offer",
    "salvage/loot": "salvage/loot",
}

# POST admin / already-gated — pas de TickGate C11.
HTTP_POST_EXEMPT: frozenset[str] = frozenset(
    {
        "/v1/inventory/reset",
        "/v1/quests/reset",
        "/v1/hunt-yard/reset",
        "/v1/think",
        "/v1/npc-think",
        "/v1/player-think",
    }
)

# Enqueue sociales : free (pas de commit monde fileté).
ENQUEUE_FREE_ACTIONS: frozenset[str] = frozenset({"say", "emote", "mood", "look"})


def reset_cache() -> None:
    global _m10_cache, _npc_cache, _poi_cache
    _m10_cache = None
    _npc_cache = None
    _poi_cache = None
    reset_tick_gate()


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


# ---------------------------------------------------------------------------
# C11 — TickGate live (cooldown / file mutations → 429 tick_busy)
# ---------------------------------------------------------------------------


def tick_gate_enabled() -> bool:
    raw = (os.environ.get("LBG_TICK_GATE") or "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def tick_cooldown_s() -> float:
    raw = os.environ.get("LBG_TICK_COOLDOWN_S", "8")
    try:
        return max(0.0, float(raw))
    except ValueError:
        return 8.0


def tick_queue_max() -> int:
    """Profondeur max de mutations « in-flight » par joueur (MVP = 1)."""
    raw = os.environ.get("LBG_TICK_QUEUE_MAX", "1")
    try:
        return max(1, int(raw))
    except ValueError:
        return 1


def normalize_http_path(path: str) -> str:
    return (path or "").rstrip("/") or "/"


def http_path_to_action(path: str, body: dict[str, Any] | None = None) -> str | None:
    """Mappe un POST sidecar vers une action ``TICK_MATRIX`` (ou None = hors gate)."""
    p = normalize_http_path(path)
    if p in HTTP_POST_EXEMPT:
        return None
    if p in HTTP_POST_PATH_TO_ACTION:
        return HTTP_POST_PATH_TO_ACTION[p]
    if p == "/v1/enqueue":
        data = body if isinstance(body, dict) else {}
        action = str(data.get("action") or "").strip()
        if not action:
            # ligne raw déjà formatée — mutation prudente
            line = str(data.get("line") or "").strip()
            return "move_to" if line else None
        if action in ENQUEUE_FREE_ACTIONS:
            return None
        return ENQUEUE_ACTION_TO_TICK.get(action, action)
    return None


def player_from_body(body: dict[str, Any] | None) -> str:
    data = body if isinstance(body, dict) else {}
    for key in ("player", "player_name", "firstname", "name"):
        raw = data.get(key)
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    return "local"


def attach_tick_context(payload: dict[str, Any], action: str) -> dict[str, Any]:
    """Injecte flags C11 dans une réponse mutation (additif)."""
    ctx = tick_context_for(action)
    out = dict(payload)
    out.setdefault("tick_cost", ctx["tick_cost"])
    out.setdefault("requires_tick", ctx["requires_tick"])
    out["context"] = {**(out.get("context") if isinstance(out.get("context"), dict) else {}), **ctx}
    return out


def mutation_reject_payload(
    *,
    action: str,
    player: str,
    reason: str,
    retry_after_s: float,
    queue_depth: int,
) -> dict[str, Any]:
    ctx = tick_context_for(action)
    return {
        "ok": False,
        "error": "tick_busy",
        "reason": reason,
        "player": player,
        "retry_after_s": round(max(0.0, retry_after_s), 2),
        "queue_depth": queue_depth,
        "tick_cost": ctx["tick_cost"],
        "requires_tick": ctx["requires_tick"],
        "context": ctx,
    }


class TickGate:
    """Cooldown + capacité par joueur pour mutations C11."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # player_key -> last acquire monotonic
        self._last_at: dict[str, float] = {}
        # player_key -> in-flight count
        self._inflight: dict[str, int] = {}

    def reset(self) -> None:
        with self._lock:
            self._last_at.clear()
            self._inflight.clear()

    def status(self, player: str) -> dict[str, Any]:
        key = (player or "local").strip().lower() or "local"
        now = time.monotonic()
        with self._lock:
            last = self._last_at.get(key, 0.0)
            depth = int(self._inflight.get(key, 0))
        cd = tick_cooldown_s()
        remaining = max(0.0, cd - (now - last)) if last > 0 else 0.0
        return {
            "player": key,
            "queue_depth": depth,
            "queue_max": tick_queue_max(),
            "cooldown_s": cd,
            "retry_after_s": round(remaining, 2),
            "busy": depth >= tick_queue_max() or remaining > 0.0,
        }

    def try_acquire(self, player: str, action: str) -> tuple[bool, dict[str, Any]]:
        """Acquiert un slot mutation. Retourne ``(ok, meta_or_reject)``."""
        if not is_mutation(action):
            return True, {"skipped": True, "action": action}
        key = (player or "local").strip().lower() or "local"
        now = time.monotonic()
        cd = tick_cooldown_s()
        qmax = tick_queue_max()
        with self._lock:
            depth = int(self._inflight.get(key, 0))
            last = self._last_at.get(key, 0.0)
            remaining = max(0.0, cd - (now - last)) if last > 0 else 0.0
            if depth >= qmax:
                reject = mutation_reject_payload(
                    action=action,
                    player=key,
                    reason="queue_full",
                    retry_after_s=remaining if remaining > 0 else cd,
                    queue_depth=depth,
                )
                return False, reject
            if remaining > 0.0:
                reject = mutation_reject_payload(
                    action=action,
                    player=key,
                    reason="cooldown",
                    retry_after_s=remaining,
                    queue_depth=depth,
                )
                return False, reject
            self._inflight[key] = depth + 1
            self._last_at[key] = now
        return True, {"player": key, "action": action, "queue_depth": depth + 1}

    def release(self, player: str) -> None:
        key = (player or "local").strip().lower() or "local"
        with self._lock:
            depth = int(self._inflight.get(key, 0))
            if depth <= 1:
                self._inflight.pop(key, None)
            else:
                self._inflight[key] = depth - 1


_TICK_GATE = TickGate()


def reset_tick_gate() -> None:
    _TICK_GATE.reset()


def get_tick_gate() -> TickGate:
    return _TICK_GATE


def try_acquire_mutation(player: str, action: str) -> tuple[bool, dict[str, Any]]:
    return _TICK_GATE.try_acquire(player, action)


def release_mutation(player: str) -> None:
    _TICK_GATE.release(player)


def http_post_tick_guard(
    path: str,
    body: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any]] | None:
    """Gate POST mutations pour le sidecar.

    Retourne ``(status, payload)`` si rejeté (à sérialiser tel quel) ;
    ``None`` si le handler peut continuer.

    MVP : enforcement **cooldown** (``last_at``). Le slot in-flight est
    libéré tout de suite pour éviter les fuites si le sidecar omet ``release``.
    ``queue_full`` reste disponible si un caller retient le slot via
    ``try_acquire_mutation`` sans release.
    """
    if not tick_gate_enabled():
        return None
    action = http_path_to_action(path, body)
    if action is None:
        return None
    cls = classify_action(action)
    if cls.get("kind") != "mutation":
        return None
    player = player_from_body(body)
    ok, meta = try_acquire_mutation(player, action)
    if not ok:
        return (429, meta)
    # Cooldown armé ; ne pas retenir inflight sur le wire HTTP.
    release_mutation(player)
    return None


def http_post_tick_release(path: str, body: dict[str, Any] | None = None) -> None:
    """Libère le slot in-flight après handler (succès ou erreur métier)."""
    if not tick_gate_enabled():
        return
    action = http_path_to_action(path, body)
    if action is None or not is_mutation(action):
        return
    release_mutation(player_from_body(body))
