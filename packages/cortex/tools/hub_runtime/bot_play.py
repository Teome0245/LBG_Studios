"""Mode SpaceMolt léger — joueurs IA : quêtes ECONOMY + exploration (pas de couloirs)."""

from __future__ import annotations

import random
import time
from typing import Any

from tools.hub_runtime.bot_goals import linger_seconds, pick_goal
from tools.hub_runtime.economy import ECONOMY
from tools.hub_runtime.hub_collision import COLLISION

# POI hub + hors palissade (Scrapaltai)
POI_XYZ: dict[str, tuple[float, float, float]] = {
    "poi:lost_heaven": (4749.0, 0.15, -737.0),
    "poi:lost_heaven_market": (4809.0, 0.15, -932.0),
    "poi:lost_heaven_starport": (4740.0, 0.15, -820.0),  # apron ouest
    "poi:lost_heaven_cantina": (4939.0, 0.15, -802.0),
    "poi:lost_heaven_mission_post": (4939.0, 0.15, -932.0),
    "poi:lost_heaven_clinic": (4679.0, 0.15, -672.0),
    "poi:lost_heaven_training_hall": (4939.0, 0.15, -672.0),
    "poi:lost_heaven_inn": (4809.0, 0.15, -672.0),
    "poi:lost_heaven_town_hall": (4679.0, 0.15, -932.0),
    "poi:lost_heaven_artisan_hall": (5069.0, 0.15, -802.0),
    "poi:lost_heaven_gate": (5813.6, 0.15, -982.5),
    "poi:lost_heaven_gate_west": (3688.9, 0.15, -675.9),
    "poi:lh_hunt_chacal": (5985.0, 0.15, -1120.0),
    "poi:player_spawn": (4749.0, 0.15, -537.0),
}

# Points d'exploration (désert / portes) — au-delà de la plaza
EXPLORE_SPOTS: list[dict[str, Any]] = [
    {"id": "gate_east", "label": "explorer porte est / dunes", "poi": "poi:lost_heaven_gate"},
    {"id": "hunt", "label": "reconnaître la meute hors murs", "poi": "poi:lh_hunt_chacal"},
    {"id": "gate_west", "label": "surveiller porte ouest Zalem", "poi": "poi:lost_heaven_gate_west"},
    {"id": "spawn_apron", "label": "repasser au shuttleport", "poi": "poi:player_spawn"},
]

# Préférences quêtes par bot (SpaceMolt playstyles)
_QUEST_PREFER: dict[str, tuple[str, ...]] = {
    "Nix": ("lh_survey_dunes", "lh_delivery_starport", "lh_aide_generale"),
    "Lia": ("lh_rumor_perle", "lh_show_perle", "lh_repair_perle", "lh_aide_generale"),
    "Mira": ("lh_delivery_starport", "lh_enquete_marche", "lh_survey_dunes"),
    "Kael": ("lh_survey_dunes", "lh_escort_gate_clinic", "lh_hunt_chacal"),
}

_last_quest_ts: dict[str, float] = {}
_QUEST_COOLDOWN_S = 6.0


def _walkable(x: float, z: float) -> tuple[float, float]:
    if COLLISION.allows(x, z):
        return x, z
    return COLLISION.nearest_walkable(x, z)


def poi_pos(poi: str) -> tuple[float, float, float] | None:
    p = POI_XYZ.get(poi) or POI_XYZ.get(f"poi:{poi}" if not poi.startswith("poi:") else poi)
    if p is None:
        return None
    wx, wz = _walkable(p[0], p[2])
    return (wx, 0.15, wz)


def _can_quest_tick(name: str) -> bool:
    now = time.monotonic()
    last = _last_quest_ts.get(name, 0.0)
    return (now - last) >= _QUEST_COOLDOWN_S


def _mark_quest_tick(name: str) -> None:
    _last_quest_ts[name] = time.monotonic()


def _pick_quest_id(name: str) -> str | None:
    board = ECONOMY.board(player=name, giver="npc:core3_daan_oth")
    quests = board.get("quests") if board.get("ok") else None
    if not isinstance(quests, list) or not quests:
        return None
    by_id = {str(q.get("id")): q for q in quests if isinstance(q, dict)}
    for qid in _QUEST_PREFER.get(name, ()):
        if qid in by_id:
            return qid
    return str(quests[0].get("id") or "") or None


def _active_entry(name: str) -> dict[str, Any] | None:
    st = ECONOMY.status(name)
    active = st.get("active") if st.get("ok") else None
    if not isinstance(active, list) or not active:
        return None
    for a in active:
        if isinstance(a, dict):
            return a
    return None


def _pending_step(entry: dict[str, Any]) -> dict[str, Any] | None:
    steps = entry.get("progress") or []
    done = set(entry.get("steps_done") or [])
    if not isinstance(steps, list):
        return None
    for s in steps:
        if not isinstance(s, dict):
            continue
        sid = str(s.get("id") or "")
        if sid and sid not in done:
            return s
    return None


def assign_play_goal(bot: Any, *, prefer: list[str] | None = None) -> dict[str, Any]:
    """Choisit un objectif : quête SpaceMolt > explore > hub play."""
    name = str(getattr(bot, "name", "") or "")
    roll = random.random()

    # 45% quête / 25% explore / 30% hub idle goals
    if roll < 0.45 and name:
        return _quest_goal(bot, name)
    if roll < 0.70:
        return _explore_goal(bot)
    goal = pick_goal(avoid_id=str(getattr(bot, "goal_id", "") or None), prefer=prefer)
    pos = goal["pos"]
    wx, wz = _walkable(float(pos[0]), float(pos[2]))
    return {
        "goal_id": str(goal["id"]),
        "goal_label": str(goal["label"]),
        "target": (wx, 0.15, wz),
        "mode": "hub",
        "quest_id": "",
        "step_id": "",
        "radius_m": 4.0,
    }


def _quest_goal(bot: Any, name: str) -> dict[str, Any]:
    entry = _active_entry(name)
    if entry is None:
        if not _can_quest_tick(name):
            return _explore_goal(bot)
        qid = _pick_quest_id(name)
        if not qid:
            return _explore_goal(bot)
        acc = ECONOMY.accept(name, qid, giver_id="npc:core3_daan_oth")
        _mark_quest_tick(name)
        if not acc.get("ok"):
            return _explore_goal(bot)
        entry = _active_entry(name)
        if entry is None:
            return {
                "goal_id": "quest_accept",
                "goal_label": f"accepte la quête {qid}",
                "target": poi_pos("poi:lost_heaven_mission_post") or (4749.0, 0.15, -737.0),
                "mode": "quest",
                "quest_id": qid,
                "step_id": "",
                "radius_m": 8.0,
                "say": f"{name} prend la mission {qid}.",
            }
    qid = str(entry.get("id") or "")
    step = _pending_step(entry)
    if step is None:
        ECONOMY.complete(name, qid)
        _mark_quest_tick(name)
        return {
            "goal_id": "quest_done",
            "goal_label": f"termine {entry.get('title') or qid}",
            "target": poi_pos("poi:lost_heaven_mission_post") or (4749.0, 0.15, -737.0),
            "mode": "quest",
            "quest_id": qid,
            "step_id": "",
            "radius_m": 8.0,
            "say": f"{name} valide la mission.",
        }
    sid = str(step.get("id") or "")
    poi = str(step.get("poi") or "")
    radius = float(step.get("radius_m") or 40.0)
    pos = poi_pos(poi)
    if pos is None:
        return _explore_goal(bot)
    return {
        "goal_id": f"quest:{qid}:{sid}",
        "goal_label": str(step.get("label") or sid),
        "target": pos,
        "mode": "quest",
        "quest_id": qid,
        "step_id": sid,
        "radius_m": min(radius, 80.0),
        "say": f"{name} — {step.get('label') or sid}.",
    }


def _explore_goal(bot: Any) -> dict[str, Any]:
    spot = random.choice(EXPLORE_SPOTS)
    pos = poi_pos(str(spot["poi"]))
    if pos is None:
        g = pick_goal()
        p = g["pos"]
        wx, wz = _walkable(float(p[0]), float(p[2]))
        pos = (wx, 0.15, wz)
    return {
        "goal_id": str(spot["id"]),
        "goal_label": str(spot["label"]),
        "target": pos,
        "mode": "explore",
        "quest_id": "",
        "step_id": "",
        "radius_m": 25.0,
    }


def on_bot_arrived_play(bot: Any) -> dict[str, Any]:
    """Appelé à l'arrivée : progress quête si applicable + linger."""
    name = str(getattr(bot, "name", "") or "")
    mode = str(getattr(bot, "play_mode", "") or "")
    qid = str(getattr(bot, "quest_id", "") or "")
    sid = str(getattr(bot, "quest_step_id", "") or "")
    out: dict[str, Any] = {"linger": linger_seconds(), "say": "", "progressed": False}
    if mode == "quest" and name and qid and sid:
        pr = ECONOMY.progress(name, qid, sid)
        _mark_quest_tick(name)
        if pr.get("ok"):
            out["progressed"] = True
            out["say"] = f"{name} avance la quête ({sid})."
            entry = _active_entry(name)
            if entry and _pending_step(entry) is None:
                ECONOMY.complete(name, qid)
                out["say"] = f"{name} termine la mission !"
    elif mode == "explore":
        out["say"] = f"{name} — {getattr(bot, 'goal_label', 'exploration')}."
    else:
        out["say"] = f"{name} — {getattr(bot, 'goal_label', 'sur le hub')}."
    return out
