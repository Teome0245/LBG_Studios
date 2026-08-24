"""Cour de chasse — Lia / Nix / Mira vs meute de Chacals."""

from lbg_agents.hunt_yard import action_contract, new_yard, run_until_done, snapshot, tick


def test_action_contract_is_the_future_bridge():
    assert action_contract() == ("move", "attack", "pickup", "heal", "use_potion", "idle")


def test_new_yard_has_choir_and_pack():
    yard = new_yard(seed=1)
    assert [p.id for p in yard.players] == ["lia", "nix", "mira"]
    assert len(yard.beasts) == 5
    snap = snapshot(yard)
    assert snap["quest_id"] == "lh_hunt_chacal"
    assert snap["status"] == "ongoing"
    assert snap["tick"] == 0


def test_seed_is_deterministic():
    a = snapshot(tick(new_yard(seed=7), 25))
    b = snapshot(tick(new_yard(seed=7), 25))
    assert [(p["x"], p["y"], p["hp"]) for p in a["players"]] == [
        (p["x"], p["y"], p["hp"]) for p in b["players"]
    ]
    assert [beast["hp"] for beast in a["beasts"]] == [beast["hp"] for beast in b["beasts"]]


def test_choir_moves_and_attacks():
    yard = tick(new_yard(seed=1), 12)
    log = " ".join(yard.log)
    assert yard.tick == 12
    assert "frappe" in log
    assert "Lia" in log


def test_pack_dies_and_loot_is_gathered():
    yard = run_until_done(new_yard(seed=1), max_ticks=350)
    snap = snapshot(yard)
    assert snap["status"] == "victory"
    assert snap["kills"] == 5
    assert snap["loot"] == []
    total_loot = sum(p["loot_count"] for p in snap["players"])
    assert total_loot == 5
    assert any(p["hp"] > 0 for p in snap["players"])


def test_roles_show_up_in_the_log():
    yard = run_until_done(new_yard(seed=2), max_ticks=350)
    log = "\n".join(yard.log)
    assert "Lia frappe" in log
    assert "Nix frappe" in log
    assert "fourrure" in log.lower()


def test_mira_heals_when_lia_is_hurt():
    yard = new_yard(seed=1)
    lia = yard.players[0]
    mira = yard.players[2]
    lia.hp = 50
    mira.x, mira.y = lia.x + 1.0, lia.y
    tick(yard, 3)
    assert any("soigne Lia" in line for line in yard.log)
    assert yard.heals >= 1
    assert lia.hp > 50
