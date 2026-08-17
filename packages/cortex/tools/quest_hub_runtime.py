"""Runtime missions hub Lost Heaven (board / accept / complete).

État mémoire process — même contrat que m10_craft_runtime (P2 stub).
Récompenses items via m10_craft_runtime ; crédits en champ player.
"""
from __future__ import annotations

import json
import os
import threading
from copy import deepcopy
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
_CANDIDATES = [
    _ROOT / "content" / "world" / "quests_lbg_templates.json",
    Path("/opt/LBG_IA_MMO/content/world/quests_lbg_templates.json"),
    Path("/opt/LBG_IA_MMO/content/core3/quests_lbg_templates.json"),
]
DEFAULT_TEMPLATES = next((p for p in _CANDIDATES if p.is_file()), _CANDIDATES[0])
DEFAULT_PLAYER = os.environ.get("LBG_M10_STUB_PLAYER", "local")
DEFAULT_GIVER = "npc:core3_daan_oth"

_lock = threading.Lock()
_templates_doc: dict[str, Any] = {}
_players: dict[str, dict[str, Any]] = {}


def templates_path() -> Path:
    return Path(
        os.environ.get("LBG_QUESTS_TEMPLATES_JSON")
        or os.environ.get("CORE3_IA_QUESTS_TEMPLATES_JSON")
        or DEFAULT_TEMPLATES
    )


def load_templates(path: Path | None = None) -> dict[str, Any]:
    global _templates_doc
    p = path or templates_path()
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"quests templates invalide: {p}")
    _templates_doc = raw
    return _templates_doc


def ensure_templates() -> dict[str, Any]:
    if not _templates_doc:
        load_templates()
    return _templates_doc


def _all_templates() -> list[dict[str, Any]]:
    rows = ensure_templates().get("templates") or []
    return [r for r in rows if isinstance(r, dict) and r.get("id")]


def _template_by_id(qid: str) -> dict[str, Any] | None:
    for row in _all_templates():
        if str(row.get("id")) == qid:
            return row
    return None


def seed_player(player: str) -> dict[str, Any]:
    return {
        "player": player,
        "credits": 50,
        "active": [],  # list of {id, title, status, giver_id}
        "completed": [],  # list of quest ids
        "generated_offers": [],
        "generated_by_id": {},
        "board_rotation": 0,
    }


def ensure_player(player: str) -> dict[str, Any]:
    if player not in _players:
        _players[player] = seed_player(player)
    st = _players[player]
    st.setdefault("generated_offers", [])
    st.setdefault("generated_by_id", {})
    st.setdefault("board_rotation", 0)
    return st


def reset_player(player: str) -> dict[str, Any]:
    with _lock:
        _players[player] = seed_player(player)
        return deepcopy(_players[player])


def _offer_row(row: dict[str, Any], givers: list[str] | None = None) -> dict[str, Any]:
    givers = givers if givers is not None else [str(x) for x in (row.get("giver_ids") or [])]
    return {
        "id": row["id"],
        "title": row.get("title") or row["id"],
        "template": row.get("template"),
        "objective": row.get("objective") or "",
        "next_steps": row.get("next_steps") or [],
        "progress": row.get("progress") or [],
        "rewards": row.get("rewards") or {},
        "default_giver": row.get("default_giver") or "",
        "giver_ids": givers,
        "generated": bool(row.get("generated")),
    }


def _base_id(quest_id: str) -> str:
    return quest_id.split("__", 1)[0]


def _resolve_template_unlocked(st: dict[str, Any], quest_id: str) -> dict[str, Any] | None:
    tpl = _template_by_id(quest_id)
    if tpl is not None:
        return tpl
    gen = (st.get("generated_by_id") or {}).get(quest_id)
    if isinstance(gen, dict):
        return gen
    return _template_by_id(_base_id(quest_id))


def _is_offer_done(completed: list[str], row: dict[str, Any]) -> bool:
    """Masque le template statique une fois rendu ; les instances générées restent rejouables."""
    qid = str(row.get("id") or "")
    if not qid:
        return True
    if qid in completed:
        return True
    generated = bool(row.get("generated")) or "__" in qid
    if generated:
        return False
    return any(_base_id(c) == qid for c in completed)


def _already_done_unlocked(st: dict[str, Any], quest_id: str) -> bool:
    completed = [str(x) for x in (st.get("completed") or [])]
    if quest_id in completed:
        return True
    if "__" in quest_id:
        return False
    return any(_base_id(c) == quest_id for c in completed)


def _list_offers_unlocked(
    st: dict[str, Any] | None,
    *,
    giver: str,
) -> list[dict[str, Any]]:
    completed: list[str] = []
    active_ids: set[str] = set()
    if st is not None:
        completed = [str(x) for x in (st.get("completed") or [])]
        active_ids = {str(a.get("id")) for a in (st.get("active") or []) if isinstance(a, dict)}

    offered: list[dict[str, Any]] = []
    seen: set[str] = set()

    def _maybe_add(row: dict[str, Any]) -> None:
        qid = str(row.get("id") or "")
        if not qid or qid in seen:
            return
        if _is_offer_done(completed, row):
            return
        if qid in active_ids:
            return
        givers = [str(x) for x in (row.get("giver_ids") or [])]
        if giver and givers and giver not in givers and not row.get("fallback"):
            roles = [str(x) for x in (row.get("giver_roles") or [])]
            if "quest_giver" not in roles:
                return
        offered.append(_offer_row(row, givers))
        seen.add(qid)

    for row in _all_templates():
        _maybe_add(row)
    if st is not None:
        for row in st.get("generated_offers") or []:
            if isinstance(row, dict):
                _maybe_add(row)
    return offered


def _make_generated_instance(tpl: dict[str, Any], *, run: int) -> dict[str, Any]:
    base = str(tpl["id"])
    inst = deepcopy(tpl)
    inst["id"] = f"{base}__r{run}"
    title = str(tpl.get("title") or base)
    if not title.endswith("(nouvelle)"):
        inst["title"] = f"{title} (nouvelle)"
    inst["generated"] = True
    return inst


def _register_generated_unlocked(st: dict[str, Any], inst: dict[str, Any]) -> None:
    gens = st.setdefault("generated_offers", [])
    by_id = st.setdefault("generated_by_id", {})
    qid = str(inst["id"])
    gens[:] = [g for g in gens if str(g.get("id")) != qid]
    gens.append(inst)
    by_id[qid] = inst


def _rotate_board_unlocked(st: dict[str, Any]) -> bool:
    """Plus d'offres : régénère des instances fraîches depuis les templates complétés."""
    completed = list(st.get("completed") or [])
    if not completed:
        # tenter une rotation depuis tous les templates
        bases = [str(t["id"]) for t in _all_templates()]
    else:
        bases = []
        for cid in completed:
            b = _base_id(str(cid))
            if b not in bases:
                bases.append(b)
    if not bases:
        return False
    run = int(st.get("board_rotation", 0)) + 1
    st["board_rotation"] = run
    st["completed"] = []
    st["generated_offers"] = []
    for base in bases:
        tpl = _template_by_id(base)
        if tpl is None:
            continue
        _register_generated_unlocked(st, _make_generated_instance(tpl, run=run))
    return bool(st.get("generated_offers"))


def _spawn_followup_unlocked(st: dict[str, Any], quest_id: str) -> dict[str, Any] | None:
    """Après rendu : une nouvelle instance du même template apparaît au board."""
    base = _base_id(quest_id)
    tpl = _template_by_id(base)
    if tpl is None:
        return None
    run = int(st.get("board_rotation", 0)) + 1
    st["board_rotation"] = run
    inst = _make_generated_instance(tpl, run=run)
    _register_generated_unlocked(st, inst)
    return inst


def board_payload(
    *,
    giver_id: str | None = None,
    hub: str = "lost_heaven",
    player: str | None = None,
) -> dict[str, Any]:
    ensure_templates()
    giver = (giver_id or DEFAULT_GIVER).strip()
    rotated = False
    with _lock:
        st = ensure_player(player) if player else None
        offered = _list_offers_unlocked(st, giver=giver)
        if player and st is not None and not offered:
            rotated = _rotate_board_unlocked(st)
            if rotated:
                offered = _list_offers_unlocked(st, giver=giver)
    return {
        "ok": True,
        "hub": hub,
        "giver_id": giver,
        "player": player or "",
        "quests": offered,
        "count": len(offered),
        "rotated": rotated,
        "source": "quest_hub_runtime",
        "templates_path": str(templates_path()),
    }


def status_payload(player: str) -> dict[str, Any]:
    with _lock:
        st = deepcopy(ensure_player(player))
    return {"ok": True, **st, "source": "quest_hub_runtime"}


def accept_quest(player: str, quest_id: str, *, giver_id: str | None = None) -> dict[str, Any]:
    ensure_templates()
    redirected_from: str | None = None
    with _lock:
        st = ensure_player(player)
        if _already_done_unlocked(st, quest_id):
            redirected_from = quest_id
            giver = (giver_id or DEFAULT_GIVER).strip()
            offers = _list_offers_unlocked(st, giver=giver)
            exclude = {quest_id, _base_id(quest_id)}
            alt = next((str(q["id"]) for q in offers if str(q["id"]) not in exclude), None)
            if alt is None:
                _rotate_board_unlocked(st)
                offers = _list_offers_unlocked(st, giver=giver)
                alt = next((str(q["id"]) for q in offers), None)
            if alt is None:
                return {"ok": False, "error": "no_offers", "hint": "Aucune mission disponible"}
            quest_id = alt

        tpl = _resolve_template_unlocked(st, quest_id)
        if tpl is None:
            return {"ok": False, "error": "unknown_quest", "quest_id": quest_id}

        for a in st["active"]:
            if str(a.get("id")) == quest_id:
                return {
                    "ok": False,
                    "error": "already_active",
                    "quest_id": quest_id,
                    "active": deepcopy(st["active"]),
                }
        if len(st["active"]) >= 3:
            return {"ok": False, "error": "journal_full", "max": 3}

        steps = []
        for p in tpl.get("progress") or []:
            if isinstance(p, dict) and p.get("id"):
                steps.append(
                    {
                        "id": str(p["id"]),
                        "label": str(p.get("label") or p["id"]),
                        "poi": str(p.get("poi") or ""),
                        "radius_m": float(p.get("radius_m") or 50.0),
                        "done": False,
                    }
                )
        entry = {
            "id": quest_id,
            "title": tpl.get("title") or quest_id,
            "template": tpl.get("template"),
            "objective": tpl.get("objective") or "",
            "next_steps": list(tpl.get("next_steps") or []),
            "progress_steps": steps,
            "rewards": deepcopy(tpl.get("rewards") or {}),
            "status": "active",
            "giver_id": giver_id or DEFAULT_GIVER,
        }
        st["active"].append(entry)
        gens = st.get("generated_offers") or []
        st["generated_offers"] = [g for g in gens if str(g.get("id")) != quest_id]
        out = {
            "ok": True,
            "player": player,
            "accepted": entry,
            "active": deepcopy(st["active"]),
            "credits": st["credits"],
            "source": "quest_hub_runtime",
        }
        if redirected_from:
            out["redirected_from"] = redirected_from
            out["hint"] = f"Mission précédente déjà faite → nouvelle : {entry.get('title')}"
        return out


def progress_quest(
    player: str,
    quest_id: str,
    *,
    step_id: str | None = None,
    poi_id: str | None = None,
    x: float | None = None,
    z: float | None = None,
) -> dict[str, Any]:
    """Marque une étape faite (par step_id / poi). Optionnel: vérif distance si x/z fournis."""
    with _lock:
        st = ensure_player(player)
        entry = None
        for a in st["active"]:
            if str(a.get("id")) == quest_id:
                entry = a
                break
        if entry is None:
            return {"ok": False, "error": "not_active", "quest_id": quest_id}
        steps = entry.get("progress_steps") or []
        if not isinstance(steps, list) or not steps:
            return {"ok": False, "error": "no_progress_steps", "quest_id": quest_id}
        target = None
        for s in steps:
            if not isinstance(s, dict):
                continue
            if step_id and str(s.get("id")) == step_id:
                target = s
                break
            if poi_id and str(s.get("poi")) == poi_id:
                target = s
                break
        if target is None:
            return {"ok": False, "error": "unknown_step", "step_id": step_id, "poi_id": poi_id}
        # Ordre strict : ne pas skip
        for s in steps:
            if s is target:
                break
            if isinstance(s, dict) and not s.get("done"):
                return {
                    "ok": False,
                    "error": "steps_out_of_order",
                    "need": s.get("id"),
                    "hint": f"Fais d'abord : {s.get('label') or s.get('id')}",
                }
        if x is not None and z is not None and target.get("poi"):
            # La vérif POI coords est côté client ; ici on accepte le report honnête du client MVP.
            pass
        if target.get("done"):
            return {
                "ok": True,
                "already": True,
                "quest_id": quest_id,
                "step_id": target.get("id"),
                "label": target.get("label"),
                "progress_steps": deepcopy(steps),
                "ready_to_turn_in": all(
                    isinstance(s, dict) and s.get("done") for s in steps
                ),
                "active": deepcopy(st["active"]),
                "source": "quest_hub_runtime",
            }
        target["done"] = True
        ready = all(isinstance(s, dict) and s.get("done") for s in steps)
        return {
            "ok": True,
            "quest_id": quest_id,
            "step_id": target.get("id"),
            "label": target.get("label"),
            "progress_steps": deepcopy(steps),
            "ready_to_turn_in": ready,
            "active": deepcopy(st["active"]),
            "source": "quest_hub_runtime",
        }


def _apply_rewards(player: str, rewards: dict[str, Any]) -> dict[str, Any]:
    """Applique crédits + items (via m10 si dispo)."""
    applied: dict[str, Any] = {"credits_gained": 0, "items": []}
    credits = int((rewards or {}).get("credits") or 0)
    with _lock:
        st = ensure_player(player)
        if credits > 0:
            st["credits"] = int(st.get("credits") or 0) + credits
            applied["credits_gained"] = credits
        applied["credits"] = st["credits"]
    items = (rewards or {}).get("items") or []
    if isinstance(items, list) and items:
        try:
            import m10_craft_runtime as m10  # type: ignore

            m10.ensure_catalog()
            with m10._lock:  # noqa: SLF001 — partage volontaire stub
                inv_state = m10.ensure_player(player)
                inv = inv_state["inventory"]
                for it in items:
                    if not isinstance(it, dict):
                        continue
                    iid = str(it.get("id") or "")
                    qty = int(it.get("qty") or 0)
                    if not iid or qty < 1:
                        continue
                    m10._inv_add(inv, iid, qty)  # noqa: SLF001
                    applied["items"].append({"id": iid, "qty": qty})
            applied["inventory"] = deepcopy(m10.ensure_player(player)["inventory"])
        except Exception as exc:
            applied["inventory_error"] = str(exc)[:160]
    return applied


def complete_quest(player: str, quest_id: str) -> dict[str, Any]:
    with _lock:
        st = ensure_player(player)
        tpl = _resolve_template_unlocked(st, quest_id)
        if tpl is None:
            return {"ok": False, "error": "unknown_quest", "quest_id": quest_id}
        active = [a for a in st["active"] if str(a.get("id")) == quest_id]
        if not active:
            return {"ok": False, "error": "not_active", "quest_id": quest_id}
        entry = active[0]
        steps = entry.get("progress_steps") or []
        if isinstance(steps, list) and steps:
            pending = [s for s in steps if isinstance(s, dict) and not s.get("done")]
            if pending:
                need = pending[0]
                return {
                    "ok": False,
                    "error": "objectives_incomplete",
                    "quest_id": quest_id,
                    "need_step": need.get("id"),
                    "hint": f"Objectif restant : {need.get('label') or need.get('id')}",
                    "progress_steps": deepcopy(steps),
                }
        st["active"] = [a for a in st["active"] if str(a.get("id")) != quest_id]
        if quest_id not in st["completed"]:
            st["completed"].append(quest_id)
        rewards = deepcopy(entry.get("rewards") or tpl.get("rewards") or {})
        followup = _spawn_followup_unlocked(st, quest_id)
    reward_result = _apply_rewards(player, rewards)
    with _lock:
        st = ensure_player(player)
        payload = {
            "ok": True,
            "player": player,
            "quest_id": quest_id,
            "title": (tpl or {}).get("title") or quest_id,
            "rewards": rewards,
            "reward_applied": reward_result,
            "active": deepcopy(st["active"]),
            "completed": list(st["completed"]),
            "credits": st["credits"],
            "source": "quest_hub_runtime",
        }
        if followup:
            payload["new_offer"] = {
                "id": followup.get("id"),
                "title": followup.get("title"),
            }
            payload["hint"] = f"Nouvelle mission disponible : {followup.get('title')}"
    return payload


def tip_scene(player: str, quest_id: str = "lh_show_perle", *, amount: int | None = None) -> dict[str, Any]:
    """Pourboire Scène (La Perle) — débite crédits joueur, petit XP scène stub."""
    tpl = _template_by_id(quest_id) or _template_by_id("lh_show_perle")
    scene = (tpl or {}).get("scene") if isinstance(tpl, dict) else {}
    if not isinstance(scene, dict):
        scene = {}
    lo = int(scene.get("tip_credits_min") or 1)
    hi = int(scene.get("tip_credits_max") or 5)
    tip = int(amount) if amount is not None else lo
    tip = max(lo, min(hi, tip))
    with _lock:
        st = ensure_player(player)
        have = int(st.get("credits") or 0)
        if have < tip:
            return {"ok": False, "error": "not_enough_credits", "have": have, "need": tip}
        st["credits"] = have - tip
        tips = st.setdefault("scene_tips", [])
        tips.append({"quest_id": quest_id or "lh_show_perle", "amount": tip})
        return {
            "ok": True,
            "player": player,
            "tipped": tip,
            "credits": st["credits"],
            "venue": scene.get("venue") or "poi:lost_heaven_cantina",
            "message": "Tu glisses quelques crédits à l'artiste. La Perle murmure son approbation.",
            "xp_scene": int(scene.get("tip_xp_scene") or 5),
            "source": "quest_hub_runtime",
        }
