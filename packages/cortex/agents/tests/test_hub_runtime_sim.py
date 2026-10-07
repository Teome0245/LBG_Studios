"""Tests collision hub + sim clamp."""

from __future__ import annotations

import math
from pathlib import Path

from tools.hub_runtime.hub_collision import HubCollision
from tools.hub_runtime.sim import MARKET, PLAZA, TRAINING, WorldSim

MAPS = Path(__file__).resolve().parents[3] / "prime-client" / "assets" / "maps"
BUILDINGS = MAPS / "lost_heaven_buildings.json"
PROPS = MAPS / "lost_heaven_props.json"


def test_buildings_loaded() -> None:
    col = HubCollision(BUILDINGS, PROPS)
    assert BUILDINGS.is_file()
    assert len(col.blocks) > 5
    assert len(col.fence_ring) > 10


def test_market_poi_walkable() -> None:
    col = HubCollision(BUILDINGS, PROPS)
    assert col.allows(MARKET[0], MARKET[2])
    assert col.allows(PLAZA[0], PLAZA[2])
    assert not col.allows(4859.3, -1008.3)


def test_fence_blocks_closed_segment() -> None:
    col = HubCollision(BUILDINGS, PROPS, enforce_fence=True)
    # traverse rempart nord (segment fermé)
    assert col._crosses_blocked_fence(5200.0, -700.0, 5200.0, -200.0)
    cx, cz = col.clamp_move(5200.0, -700.0, 5200.0, -200.0)
    assert abs(cz + 700.0) < 2.0


def test_human_cannot_teleport_into_building() -> None:
    from tools.hub_runtime import hub_collision as hc
    from tools.hub_runtime.sim import HUMAN_OID

    hc.COLLISION.path = BUILDINGS
    hc.COLLISION.props_path = PROPS
    hc.COLLISION.reload()
    sim = WorldSim()
    sim.reset()
    sim.ensure_human(HUMAN_OID, "Voyageur")
    h = sim.entities[f"player:{HUMAN_OID}"]
    sim.set_human_pos(HUMAN_OID, 4832.8, 0.15, -819.8)
    assert hc.COLLISION.allows(h.x, h.z)
    assert abs(h.x - 4832.8) > 1.0 or abs(h.z + 819.8) > 1.0


def test_multi_humans_visible() -> None:
    sim = WorldSim()
    sim.reset()
    a = sim.ensure_human(100001, "Voyageur")
    b = sim.ensure_human(100002, "Forma")
    assert a.oid != b.oid
    assert sim.human_count() == 2
    names = {e["name"] for e in sim.entity_list()}
    assert "Voyageur" in names and "Forma" in names and "Nix" in names
    assert "Lia" in names and "Mira" in names
    assert "Kael" in names
    assert "Daan Oth" in names
    assert "Tobin Ress" in names
    payload = sim.zone_state_payload(100002)
    assert payload["your_character_id"] == 100002
    assert len(payload["entities"]) >= 5
    assert payload["online_count"] == 2
    assert payload["bot_count"] == 4
    assert payload["npc_count"] >= 12
    online_names = {p["name"] for p in payload["online_players"]}
    assert online_names == {"Voyageur", "Forma"}


def test_find_path_around_starport() -> None:
    col = HubCollision(BUILDINGS, PROPS)
    # Plaza → marché : doit contourner le starport AABB
    path = col.find_path(PLAZA[0], PLAZA[2], MARKET[0], MARKET[2])
    assert path, "path empty"
    assert math.hypot(path[-1][0] - MARKET[0], path[-1][1] - MARKET[2]) < 15.0
    # Aucun waypoint dans le bâtiment starport (approx AABB center)
    for px, pz in path:
        assert col.allows(px, pz), (px, pz)


def test_bot_goals_move() -> None:
    from tools.hub_runtime import hub_collision as hc

    hc.COLLISION.path = BUILDINGS
    hc.COLLISION.props_path = PROPS
    hc.COLLISION.reload()
    sim = WorldSim()
    sim.reset()
    nix = sim.entities["player:Nix"]
    x0, z0 = nix.x, nix.z
    moved = False
    for _ in range(400):
        sim.step(dt=0.1)
        if abs(nix.x - x0) > 8.0 or abs(nix.z - z0) > 8.0:
            moved = True
            break
    assert moved
    assert hc.COLLISION.allows(nix.x, nix.z)
    assert nix.goal_id != ""


def test_bot_quest_and_explore_cycle() -> None:
    """SpaceMolt léger : accept → progress → complete + mode explore."""
    from tools.hub_runtime import hub_collision as hc
    from tools.hub_runtime.bot_play import assign_play_goal, on_bot_arrived_play
    from tools.hub_runtime.economy import ECONOMY
    import tools.hub_runtime.bot_play as bp

    hc.COLLISION.path = BUILDINGS
    hc.COLLISION.props_path = PROPS
    hc.COLLISION.reload()

    ECONOMY._players.pop("Nix", None)
    bp._last_quest_ts.pop("Nix", None)

    class _B:
        name = "Nix"
        goal_id = ""

    old = bp.random.random
    bp.random.random = lambda: 0.1  # < 0.45 → quête
    try:
        g1 = assign_play_goal(_B())
        assert g1["mode"] == "quest"
        assert g1["quest_id"]
        st = ECONOMY.status("Nix")
        assert any(a.get("id") == g1["quest_id"] for a in st["active"])

        bot = type("Ent", (), {})()
        bot.name = "Nix"
        bot.play_mode = g1["mode"]
        bot.quest_id = g1["quest_id"]
        bot.quest_step_id = g1["step_id"]
        bot.goal_label = g1["goal_label"]
        if g1["step_id"]:
            info = on_bot_arrived_play(bot)
            assert info["progressed"] is True
            st2 = ECONOMY.status("Nix")
            entry = next(a for a in st2["active"] if a.get("id") == g1["quest_id"])
            assert g1["step_id"] in (entry.get("steps_done") or [])
    finally:
        bp.random.random = old
        ECONOMY._players.pop("Nix", None)
        bp._last_quest_ts.pop("Nix", None)

    bp.random.random = lambda: 0.55  # explore
    try:
        g2 = assign_play_goal(_B())
        assert g2["mode"] == "explore"
        assert g2["goal_id"] in {"gate_east", "hunt", "gate_west", "spawn_apron"}
    finally:
        bp.random.random = old


def test_fleet_and_move_to() -> None:
    sim = WorldSim()
    sim.reset()
    assert sim.bot_count() == 4
    lia = sim.set_bot_target("Lia", MARKET[0], MARKET[1], MARKET[2])
    assert lia is not None and lia.name == "Lia"
    assert lia.target is not None
    mira = sim.set_bot_target("player:Mira", PLAZA[0], PLAZA[1], PLAZA[2])
    assert mira is not None
    kael = sim.set_bot_target("Kael", TRAINING[0], TRAINING[1], TRAINING[2])
    assert kael is not None and kael.name == "Kael"
    sim.fleet_greet_human("Teome", 100010)
    chats = sim.drain_chat()
    assert len(chats) >= 4
    assert "ia" in {c["source"] for c in chats}
    assert {"Nix", "Lia", "Mira", "Kael"} <= {c["from"] for c in chats}


def test_npc_wander_moves() -> None:
    from tools.hub_runtime import hub_collision as hc

    hc.COLLISION.path = BUILDINGS
    hc.COLLISION.props_path = PROPS
    hc.COLLISION.reload()
    sim = WorldSim()
    sim.reset()
    jax = sim.entities["npc:core3_barman_jax"]
    x0, z0 = jax.x, jax.z
    moved = False
    for _ in range(120):
        sim.step(dt=0.2)
        if abs(jax.x - x0) > 0.8 or abs(jax.z - z0) > 0.8:
            moved = True
            break
    assert moved
    assert hc.COLLISION.allows(jax.x, jax.z)
