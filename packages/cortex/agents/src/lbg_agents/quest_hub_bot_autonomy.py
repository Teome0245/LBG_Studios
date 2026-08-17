"""Autonomie bot — missions hub Lost Heaven (quest_hub_runtime HTTP).

Branche les joueurs IA (Lia/Nix/…) sur le même board / progress / complete
que le prime-client, avec **marche visible** (movement_mode=walk) vers les POI.
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

    Préfère ``client`` (core3client DataTransform / bot_move.jsonl) quand disponible ;
    sinon ``walk`` (pas serveur 5 m). Jamais ``teleport`` pour les missions hub.
    """
    mode = (os.environ.get("LBG_QUEST_HUB_BOT_MOVEMENT") or "client").strip().lower()
    if mode not in {"walk", "client", "teleport"}:
        mode = "client"
    # Hub missions : jamais teleport (sortie intérieur = cell→0 puis marche)
    if mode == "teleport":
        mode = "client"
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
    _last_move_at[key] = now
    _last_move_poi[key] = poi
    out["reason"] = reason
    out["quest_id"] = quest_id
    out["step_id"] = step_id
    out["poi"] = poi
    out["dist_m"] = round(dist, 1) if dist is not None else None
    out["movement"] = ensure_walk_mode()
    return out


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
        # Trajets longs visibles en priorité
        prefer = (
            "lh_escort_gate_clinic",
            "lh_delivery_starport",
            "lh_enquete_marche",
            "lh_survey_dunes",
            "lh_aide_generale",
            "lh_show_perle",
        )
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
        if not acc.get("ok"):
            return None
        entry = acc.get("accepted") if isinstance(acc.get("accepted"), dict) else {}
        steps = entry.get("progress_steps") or []
        if isinstance(steps, list) and steps:
            step0 = steps[0] if isinstance(steps[0], dict) else {}
            poi = str(step0.get("poi") or "")
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
        return {
            "ok": bool(done.get("ok")),
            "reason": "hub_quest_complete_no_steps",
            "player": name,
            "quest_id": qid,
            "sidecar": done,
        }

    pending = [s for s in steps if isinstance(s, dict) and not s.get("done")]
    if not pending:
        # Complete seulement si cooldown progress écoulé (pas de multi-étape flash)
        if not _can_progress(name):
            return {
                "ok": True,
                "reason": "hub_quest_wait_turnin",
                "player": name,
                "quest_id": qid,
                "movement": ensure_walk_mode(),
            }
        done = _http_json("POST", "/v1/quests/complete", json_body={"player": name, "quest_id": qid})
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

    # Sur place : attendre le cooldown avant de valider l'étape (marche visible)
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

    # Jamais complete dans le même tick — laisser le temps de voir l'étape
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
