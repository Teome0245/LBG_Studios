"""Autonomie bot — missions hub Lost Heaven (quest_hub_runtime HTTP).

Branche les joueurs IA (Lia/Nix/…) sur le même board / progress / complete
que le prime-client, avec **marche visible** (movement_mode=walk) vers les POI.

C11 SpaceMolt : consomme ``GET /catalog`` + ``/guide`` ; respecte ``429 tick_busy``.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Callable

import httpx

# POI hub : buildings JSON x/z ; enqueue Lua = x | y_nord | z_hauteur
_DEFAULT_POI_XZ: dict[str, tuple[float, float]] = {
    "poi:lost_heaven_starport": (4832.8, -819.8),
    "poi:lost_heaven_cantina": (5028.3, -784.1),
    "poi:lost_heaven_market": (4859.3, -1008.3),
    "poi:lost_heaven_mission_post": (5028.3, -1008.8),
    "poi:lost_heaven_gate": (5813.6, -982.5),
    "poi:lh_hunt_chacal": (5985.0, -1120.0),
    "poi:lost_heaven_clinic": (4620.8, -610.6),
    "poi:lost_heaven_town_hall": (4622.3, -999.8),
    "poi:lost_heaven_artisan_hall": (5199.3, -769.5),
}

_ARRIVE_M = float(os.environ.get("LBG_QUEST_HUB_BOT_ARRIVE_M", "28") or 28)
_HEIGHT = float(os.environ.get("LBG_QUEST_HUB_BOT_HEIGHT", "32") or 32)
# Délai mini entre deux progress (laisse le temps de marcher jusqu'au POI)
_PROGRESS_COOLDOWN_S = float(os.environ.get("LBG_QUEST_HUB_BOT_PROGRESS_COOLDOWN_S", "45") or 45)
# Re-enqueue move_to espacé : trop fréquent = cancel/restart walk Lua
_MOVE_REENQUEUE_S = float(os.environ.get("LBG_QUEST_HUB_BOT_MOVE_REENQUEUE_S", "20") or 20)

_MOVEMENT_MODE_PATHS = [
    Path(os.environ.get("LBG_CORE3_MOVEMENT_MODE_FILE") or ""),
    Path("/opt/lbg-new-mmo-clean/MMOCoreORB/bin/ia_bridge/movement_mode"),
]

# player -> monotonic ts
_last_progress_at: dict[str, float] = {}
_last_move_at: dict[str, float] = {}
_last_move_poi: dict[str, str] = {}
# playstyle guide cache (C10)
_guide_cache: dict[str, dict[str, Any]] = {}
_catalog_poi_ids: set[str] | None = None
_last_tip_at: dict[str, float] = {}

_DEFAULT_PLAYSTYLE_BY_BOT: dict[str, str] = {
    "lia": "scene",
    "nix": "prospecteur",
    "mira": "artisan",
    "kael": "scout",
}

# quest_id préférés par playstyle (ordre)
_QUEST_PREFER_BY_PLAYSTYLE: dict[str, tuple[str, ...]] = {
    "prospecteur": (
        "lh_survey_dunes",
        "lh_delivery_starport",
        "lh_enquete_marche",
        "lh_aide_generale",
        "lh_escort_gate_clinic",
        "lh_hunt_chacal",
        "lh_show_perle",
    ),
    "artisan": (
        "lh_delivery_starport",
        "lh_enquete_marche",
        "lh_aide_generale",
        "lh_survey_dunes",
        "lh_escort_gate_clinic",
        "lh_hunt_chacal",
        "lh_show_perle",
    ),
    "scene": (
        "lh_show_perle",
        "lh_aide_generale",
        "lh_enquete_marche",
        "lh_delivery_starport",
        "lh_escort_gate_clinic",
        "lh_survey_dunes",
        "lh_hunt_chacal",
    ),
    "medecin": (
        "lh_escort_gate_clinic",
        "lh_aide_generale",
        "lh_delivery_starport",
        "lh_enquete_marche",
        "lh_survey_dunes",
        "lh_hunt_chacal",
        "lh_show_perle",
    ),
    "scout": (
        "lh_hunt_chacal",
        "lh_survey_dunes",
        "lh_escort_gate_clinic",
        "lh_delivery_starport",
        "lh_enquete_marche",
        "lh_aide_generale",
        "lh_show_perle",
    ),
}


def quest_hub_bot_enabled() -> bool:
    raw = (os.environ.get("LBG_QUEST_HUB_BOT") or "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def sidecar_base() -> str:
    return (
        os.environ.get("LBG_CORE3_IA_SIDECAR_URL")
        or os.environ.get("CORE3_IA_SIDECAR_URL")
        or "http://127.0.0.1:8791"
    ).rstrip("/")


def ensure_walk_mode() -> str:
    """Force marche visible pour le hub.

    Préfère ``walk`` (pas serveur visible) ; ``client`` (bot_move/DataTransform) si
    ``LBG_QUEST_HUB_BOT_MOVEMENT=client``. Jamais ``teleport`` pour les missions hub.
    """
    mode = (os.environ.get("LBG_QUEST_HUB_BOT_MOVEMENT") or "walk").strip().lower()
    if mode not in {"walk", "client", "teleport"}:
        mode = "walk"
    # Hub missions : jamais teleport (sortie intérieur = cell→0 puis marche)
    if mode == "teleport":
        mode = "walk"
    for p in _MOVEMENT_MODE_PATHS:
        if not p or not str(p).strip():
            continue
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            cur = p.read_text(encoding="utf-8").strip() if p.is_file() else ""
            if cur != mode:
                p.write_text(mode + "\n", encoding="utf-8")
        except OSError:
            continue
    return mode


def is_tick_busy(resp: dict[str, Any] | None) -> bool:
    """True si le sidecar a renvoyé C11 ``tick_busy`` (HTTP 429 ou payload)."""
    if not isinstance(resp, dict):
        return False
    if resp.get("error") == "tick_busy":
        return True
    if int(resp.get("http_status") or 0) == 429 and resp.get("reason") in {
        "cooldown",
        "queue_full",
        "tick_busy",
    }:
        return True
    return False


def playstyle_for_player(name: str) -> str:
    key = (name or "").strip().lower()
    env_key = f"LBG_BOT_PLAYSTYLE_{key.upper()}"
    raw = (os.environ.get(env_key) or os.environ.get("LBG_BOT_PLAYSTYLE") or "").strip().lower()
    if raw:
        return raw
    return _DEFAULT_PLAYSTYLE_BY_BOT.get(key, "prospecteur")


def _load_poi_xz() -> dict[str, tuple[float, float]]:
    out = dict(_DEFAULT_POI_XZ)
    candidates = [
        Path(os.environ.get("LBG_LOST_HEAVEN_BUILDINGS_JSON") or ""),
        Path("/opt/LBG_IA_MMO/content/world/lost_heaven_buildings.json"),
    ]
    root = Path(__file__).resolve().parents[4] if len(Path(__file__).resolve().parents) > 4 else Path(".")
    candidates.append(root / "prime-client" / "assets" / "maps" / "lost_heaven_buildings.json")
    for p in candidates:
        if not p or not str(p).strip() or not p.is_file():
            continue
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for b in raw.get("buildings") or []:
            if not isinstance(b, dict) or not b.get("id"):
                continue
            out[str(b["id"])] = (float(b.get("x") or 0), float(b.get("z") or 0))
        break
    return out


def _poi_xyz(poi_id: str) -> tuple[float, float, float] | None:
    """Enqueue Lua : x | y_nord | z_hauteur → approachCoords / walk sur plan X/Y."""
    xz = _load_poi_xz().get(poi_id)
    if xz is None:
        return None
    return (xz[0], xz[1], _HEIGHT)


def _http_json(method: str, path: str, *, json_body: dict | None = None, timeout: float = 8.0) -> dict[str, Any]:
    url = f"{sidecar_base()}{path}"
    try:
        with httpx.Client(timeout=timeout) as client:
            if method == "GET":
                resp = client.get(url)
            else:
                resp = client.post(url, json=json_body or {})
        data = resp.json() if resp.content else {}
        if not isinstance(data, dict):
            return {"ok": False, "error": "bad_json", "http_status": resp.status_code}
        data.setdefault("http_status", resp.status_code)
        return data
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:160]}


def _tick_busy_outcome(name: str, resp: dict[str, Any], *, quest_id: str = "") -> dict[str, Any]:
    return {
        "ok": True,
        "outcome": "tick_busy",
        "reason": "tick_busy",
        "player": name,
        "quest_id": quest_id or None,
        "retry_after_s": resp.get("retry_after_s"),
        "sidecar": resp,
        "movement": ensure_walk_mode(),
    }


def fetch_playstyle_guide(name: str, *, force: bool = False) -> dict[str, Any] | None:
    """C10 — ``GET /guide?playstyle=`` (cache par bot)."""
    style = playstyle_for_player(name)
    key = f"{name.lower()}::{style}"
    if not force and key in _guide_cache:
        return _guide_cache[key]
    payload = _http_json("GET", f"/guide?playstyle={style}")
    if not payload.get("ok"):
        payload = _http_json("GET", f"/v1/guide?playstyle={style}")
    if payload.get("ok") and isinstance(payload.get("guide"), dict):
        _guide_cache[key] = payload["guide"]
        return payload["guide"]
    return None


def ensure_catalog_poi_cache(*, force: bool = False) -> set[str]:
    """C10 — ``GET /catalog?type=poi`` (ids connus hub)."""
    global _catalog_poi_ids
    if _catalog_poi_ids is not None and not force:
        return _catalog_poi_ids
    payload = _http_json("GET", "/catalog?type=poi")
    if not payload.get("ok"):
        payload = _http_json("GET", "/v1/catalog?type=poi")
    ids: set[str] = set()
    items = payload.get("items") if payload.get("ok") else None
    if isinstance(items, list):
        for row in items:
            if isinstance(row, dict) and isinstance(row.get("id"), str):
                ids.add(row["id"].strip())
    _catalog_poi_ids = ids
    return ids


def _prefer_quest_ids(name: str) -> tuple[str, ...]:
    guide = fetch_playstyle_guide(name)
    style = playstyle_for_player(name)
    if guide and isinstance(guide.get("playstyle"), str):
        style = str(guide["playstyle"])
    return _QUEST_PREFER_BY_PLAYSTYLE.get(style, _QUEST_PREFER_BY_PLAYSTYLE["prospecteur"])


def _player_horiz(snap: dict[str, Any]) -> tuple[float, float]:
    """Retourne (x, nord) depuis un snapshot Core3."""
    px = float(snap.get("x") or 0)
    py = float(snap.get("y") or 0)
    pz = float(snap.get("z") or 0)
    # Outdoor typique : y=nord (|y| grand), z=hauteur (~0–80). Interior ME : y=nord monde, z=hauteur.
    if abs(py) > 80 and abs(pz) < 80:
        return px, py
    if abs(pz) > 80 and abs(py) < 80:
        return px, pz
    # Zone bridge / snapshot LH : souvent [x, nord, height] → y=nord
    return px, py


def _dist_xz(snap: dict[str, Any], target: tuple[float, float, float]) -> float:
    """Distance horizontale. target enqueue = (x, nord, height)."""
    px, p_north = _player_horiz(snap)
    tx, t_north = target[0], target[1]
    return ((px - tx) ** 2 + (p_north - t_north) ** 2) ** 0.5


def _player_name(player: Any) -> str:
    return str(getattr(player, "firstname", None) or getattr(player, "id", "") or "Lia")


def _can_progress(name: str) -> bool:
    last = _last_progress_at.get(name.lower(), 0.0)
    return (time.monotonic() - last) >= _PROGRESS_COOLDOWN_S


def _mark_progress(name: str) -> None:
    _last_progress_at[name.lower()] = time.monotonic()


def _enqueue_move(
    enqueue: Callable[..., dict[str, Any]],
    player: Any,
    name: str,
    *,
    snap: dict[str, Any],
    xyz: tuple[float, float, float],
    poi: str,
    message: str,
    reason: str,
    quest_id: str,
    step_id: str | None = None,
    dist: float | None = None,
) -> dict[str, Any]:
    key = name.lower()
    now = time.monotonic()
    last = _last_move_at.get(key, 0.0)
    same_poi = _last_move_poi.get(key) == poi
    # Déjà sur place (ex. return au même POI que errand) : ne pas spam move_to.
    if dist is not None and dist <= max(2.0, min(8.0, _ARRIVE_M * 0.25)):
        _last_move_poi[key] = poi
        return {
            "ok": True,
            "outcome": "ok",
            "reason": "hub_quest_arrived",
            "player": name,
            "quest_id": quest_id,
            "step_id": step_id,
            "poi": poi,
            "dist_m": round(dist, 1),
            "movement": ensure_walk_mode(),
        }
    if same_poi and (now - last) < _MOVE_REENQUEUE_S:
        out = {
            "ok": True,
            "outcome": "ok",
            "reason": "hub_quest_walking",
            "player": name,
            "quest_id": quest_id,
            "step_id": step_id,
            "poi": poi,
            "dist_m": round(dist, 1) if dist is not None else None,
            "movement": ensure_walk_mode(),
        }
        return out
    out = enqueue(
        player,
        action="move_to",
        message=message,
        snapshot=snap,
        target_xyz=xyz,
    )
    if is_tick_busy(out):
        return _tick_busy_outcome(name, out, quest_id=quest_id)
    _last_move_at[key] = now
    _last_move_poi[key] = poi
    out["reason"] = reason
    out["quest_id"] = quest_id
    out["step_id"] = step_id
    out["poi"] = poi
    out["dist_m"] = round(dist, 1) if dist is not None else None
    out["movement"] = ensure_walk_mode()
    return out


def _maybe_tip_stage(name: str, qid: str, step_id: str) -> dict[str, Any] | None:
    """Mutation tip_stage pour quête scène (playstyle scene / lh_show_perle)."""
    if qid != "lh_show_perle":
        return None
    tip_like = any(k in step_id.lower() for k in ("tip", "show", "danse", "scene", "perle"))
    if playstyle_for_player(name) != "scene" and not tip_like:
        return None
    key = name.lower()
    now = time.monotonic()
    if (now - _last_tip_at.get(key, 0.0)) < max(_PROGRESS_COOLDOWN_S, 30.0):
        return None
    tip = _http_json(
        "POST",
        "/v1/quests/tip",
        json_body={"player": name, "quest_id": qid, "amount": 5},
    )
    _last_tip_at[key] = now
    if is_tick_busy(tip):
        return _tick_busy_outcome(name, tip, quest_id=qid)
    if tip.get("ok"):
        return {
            "ok": True,
            "reason": "hub_tip_stage",
            "player": name,
            "quest_id": qid,
            "step_id": step_id,
            "sidecar": tip,
            "movement": ensure_walk_mode(),
        }
    return None


def deterministic_hub_quest_action(
    player: Any,
    *,
    snapshot: dict[str, Any] | None,
    enqueue: Callable[..., dict[str, Any]],
) -> dict[str, Any] | None:
    """Un tick : sortir intérieur / accepter / marcher POI / progress (lent) / complete."""
    if not quest_hub_bot_enabled():
        return None
    ensure_walk_mode()
    snap = snapshot if isinstance(snapshot, dict) else {}
    name = _player_name(player)
    if not name:
        return None

    # C10 — warm catalog + guide (queries free)
    ensure_catalog_poi_cache()
    fetch_playstyle_guide(name)

    # Sortir d'un intérieur hors hub avant de jouer une mission
    in_interior = snap.get("in_interior") in {True, 1, "1", "true", "True"}
    age_s = float(snap.get("age_s") or 0)
    if in_interior and age_s > 90.0:
        in_interior = False
    parent_id = int(snap.get("parent_id") or 0)
    plaza = (4749.0, -737.0, _HEIGHT)
    near_hub = _dist_xz(snap, plaza) < 250.0 and parent_id == 0
    if in_interior and not near_hub:
        # Exit : Lua force cell 0 si coords outdoor (même en walk)
        out = enqueue(
            player,
            action="move_to",
            message="hub_exit_interior",
            snapshot=snap,
            target_xyz=plaza,
        )
        if is_tick_busy(out):
            return _tick_busy_outcome(name, out)
        out["reason"] = "hub_quest_exit_interior"
        out["movement"] = ensure_walk_mode()
        return out

    status = _http_json("GET", f"/v1/quests/status?player={name}")
    active = status.get("active") if status.get("ok") else None
    if not isinstance(active, list):
        active = []

    if not active:
        board = _http_json("GET", f"/v1/quests/board?giver=npc:core3_daan_oth&player={name}")
        quests = board.get("quests") if board.get("ok") else None
        if not isinstance(quests, list) or not quests:
            return None
        prefer = _prefer_quest_ids(name)
        pick = None
        by_id = {str(q.get("id")): q for q in quests if isinstance(q, dict)}
        for pid in prefer:
            if pid in by_id:
                pick = pid
                break
        if pick is None:
            pick = str(quests[0].get("id") or "")
        if not pick:
            return None
        acc = _http_json(
            "POST",
            "/v1/quests/accept",
            json_body={"player": name, "quest_id": pick, "giver_id": "npc:core3_daan_oth"},
        )
        if is_tick_busy(acc):
            return _tick_busy_outcome(name, acc, quest_id=pick)
        if not acc.get("ok"):
            return None
        entry = acc.get("accepted") if isinstance(acc.get("accepted"), dict) else {}
        steps = entry.get("progress_steps") or []
        if isinstance(steps, list) and steps:
            step0 = steps[0] if isinstance(steps[0], dict) else {}
            poi = str(step0.get("poi") or "")
            catalog_ids = _catalog_poi_ids or set()
            if poi and catalog_ids and poi not in catalog_ids and f"poi:{poi}" in catalog_ids:
                poi = f"poi:{poi}"
            xyz = _poi_xyz(poi) if poi else None
            if xyz is not None:
                return _enqueue_move(
                    enqueue,
                    player,
                    name,
                    snap=snap,
                    xyz=xyz,
                    poi=poi,
                    message=f"hub_quest:{pick}:{step0.get('id')}",
                    reason="hub_quest_travel",
                    quest_id=pick,
                    step_id=str(step0.get("id") or ""),
                    dist=_dist_xz(snap, xyz),
                )
        return {
            "ok": True,
            "outcome": "ok",
            "mode": "deterministic_hub_quest",
            "reason": "hub_quest_accept",
            "player": name,
            "quest_id": pick,
            "playstyle": playstyle_for_player(name),
            "accepted": acc.get("accepted"),
            "movement": ensure_walk_mode(),
        }

    entry = next((a for a in active if isinstance(a, dict)), None)
    if entry is None:
        return None
    qid = str(entry.get("id") or "")
    steps = entry.get("progress_steps") or []
    if not isinstance(steps, list) or not steps:
        done = _http_json("POST", "/v1/quests/complete", json_body={"player": name, "quest_id": qid})
        if is_tick_busy(done):
            return _tick_busy_outcome(name, done, quest_id=qid)
        return {
            "ok": bool(done.get("ok")),
            "reason": "hub_quest_complete_no_steps",
            "player": name,
            "quest_id": qid,
            "sidecar": done,
        }

    pending = [s for s in steps if isinstance(s, dict) and not s.get("done")]
    if not pending:
        if not _can_progress(name):
            return {
                "ok": True,
                "reason": "hub_quest_wait_turnin",
                "player": name,
                "quest_id": qid,
                "movement": ensure_walk_mode(),
            }
        done = _http_json("POST", "/v1/quests/complete", json_body={"player": name, "quest_id": qid})
        if is_tick_busy(done):
            return _tick_busy_outcome(name, done, quest_id=qid)
        _mark_progress(name)
        return {
            "ok": bool(done.get("ok")),
            "reason": "hub_quest_complete",
            "player": name,
            "quest_id": qid,
            "new_offer": done.get("new_offer"),
            "sidecar": done,
        }

    step = pending[0]
    step_id = str(step.get("id") or "")
    poi = str(step.get("poi") or "")
    radius = min(float(step.get("radius_m") or _ARRIVE_M), _ARRIVE_M)
    xyz = _poi_xyz(poi) if poi else None
    if xyz is None:
        return None

    dist = _dist_xz(snap, xyz)
    if dist > radius:
        return _enqueue_move(
            enqueue,
            player,
            name,
            snap=snap,
            xyz=xyz,
            poi=poi,
            message=f"hub_quest:{qid}:{step_id}",
            reason="hub_quest_travel",
            quest_id=qid,
            step_id=step_id,
            dist=dist,
        )

    tipped = _maybe_tip_stage(name, qid, step_id)
    if tipped is not None:
        return tipped

    if not _can_progress(name):
        return {
            "ok": True,
            "reason": "hub_quest_dwell",
            "player": name,
            "quest_id": qid,
            "step_id": step_id,
            "poi": poi,
            "dist_m": round(dist, 1),
            "movement": ensure_walk_mode(),
        }

    if qid == "lh_hunt_chacal" and step_id == "meute":
        snap_h = _http_json("GET", "/v1/hunt-yard")
        if snap_h.get("status") != "victory":
            _http_json("POST", "/v1/hunt-yard/reset", json_body={"seed": 1})
            run = _http_json("POST", "/v1/hunt-yard/run", json_body={"max_ticks": 120})
            if is_tick_busy(run):
                return _tick_busy_outcome(name, run, quest_id=qid)
            if run.get("status") != "victory":
                return {
                    "ok": True,
                    "reason": "hub_hunt_ongoing",
                    "player": name,
                    "quest_id": qid,
                    "hunt_status": run.get("status"),
                    "movement": ensure_walk_mode(),
                }
        prog = _http_json(
            "POST",
            "/v1/hunt-yard/claim-quest",
            json_body={"player": name, "quest_id": qid},
        )
        if is_tick_busy(prog):
            return _tick_busy_outcome(name, prog, quest_id=qid)
        if not prog.get("ok"):
            return {
                "ok": False,
                "reason": "hub_hunt_claim_fail",
                "player": name,
                "quest_id": qid,
                "sidecar": prog,
            }
        _mark_progress(name)
        _last_move_poi.pop(name.lower(), None)
        active2 = prog.get("active") if isinstance(prog.get("active"), list) else None
        if active2:
            entry2 = next((a for a in active2 if str(a.get("id")) == qid), entry)
            steps2 = entry2.get("progress_steps") or []
            nxt = next((s for s in steps2 if isinstance(s, dict) and not s.get("done")), None)
            if nxt and nxt.get("poi"):
                nxyz = _poi_xyz(str(nxt["poi"]))
                if nxyz is not None:
                    return _enqueue_move(
                        enqueue,
                        player,
                        name,
                        snap=snap,
                        xyz=nxyz,
                        poi=str(nxt["poi"]),
                        message=f"hub_quest:{qid}:{nxt.get('id')}",
                        reason="hub_quest_travel_next",
                        quest_id=qid,
                        step_id=str(nxt.get("id") or ""),
                        dist=_dist_xz(snap, nxyz),
                    )
        return {
            "ok": True,
            "reason": "hub_hunt_claim",
            "player": name,
            "quest_id": qid,
            "step_id": step_id,
            "movement": ensure_walk_mode(),
            "sidecar": prog,
        }

    prog = _http_json(
        "POST",
        "/v1/quests/progress",
        json_body={
            "player": name,
            "quest_id": qid,
            "step_id": step_id,
            "poi_id": poi,
            "x": float(snap.get("x") or xyz[0]),
            "z": float(_player_horiz(snap)[1]),
        },
    )
    if is_tick_busy(prog):
        return _tick_busy_outcome(name, prog, quest_id=qid)
    if not prog.get("ok"):
        return {
            "ok": False,
            "reason": "hub_quest_progress_fail",
            "player": name,
            "quest_id": qid,
            "step_id": step_id,
            "sidecar": prog,
        }
    _mark_progress(name)
    _last_move_poi.pop(name.lower(), None)

    active2 = prog.get("active") if isinstance(prog.get("active"), list) else None
    if active2:
        entry2 = next((a for a in active2 if str(a.get("id")) == qid), entry)
        steps2 = entry2.get("progress_steps") or []
        nxt = next((s for s in steps2 if isinstance(s, dict) and not s.get("done")), None)
        if nxt and nxt.get("poi"):
            nxyz = _poi_xyz(str(nxt["poi"]))
            if nxyz is not None:
                return _enqueue_move(
                    enqueue,
                    player,
                    name,
                    snap=snap,
                    xyz=nxyz,
                    poi=str(nxt["poi"]),
                    message=f"hub_quest:{qid}:{nxt.get('id')}",
                    reason="hub_quest_travel_next",
                    quest_id=qid,
                    step_id=str(nxt.get("id") or ""),
                    dist=_dist_xz(snap, nxyz),
                )
    return {
        "ok": True,
        "reason": "hub_quest_progress",
        "player": name,
        "quest_id": qid,
        "step_id": step_id,
        "ready_to_turn_in": bool(prog.get("ready_to_turn_in")),
        "movement": ensure_walk_mode(),
        "sidecar": prog,
    }
