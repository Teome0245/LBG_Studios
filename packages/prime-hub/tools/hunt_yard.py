"""Cour de chasse Lost Heaven — boucle combat+loot sans Core3.

Réflexes déterministes (pas de LLM) : Lia tank, Nix kiting, Mira soins.
Même contrat d'actions que le futur pont Prime : move / attack / pickup / heal / use_potion.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import pickle
import random
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

WIDTH = 28.0
HEIGHT = 18.0
QUEST_ID = "lh_hunt_chacal"
LOG_CAP = 48
TICK_CAP_DEFAULT = 400

Status = Literal["ongoing", "victory", "defeat"]


def action_contract() -> tuple[str, ...]:
    return ("move", "attack", "pickup", "heal", "use_potion", "idle")


@dataclass
class Actor:
    id: str
    name: str
    kind: str
    role: str
    x: float
    y: float
    hp: int
    hp_max: int
    speed: float
    atk_range: float
    dmg: int
    cooldown_max: int
    color: str
    cooldown: int = 0
    potions: int = 0
    loot_count: int = 0
    last_action: str = "idle"
    last_target: str = ""
    heal_range: float = 0.0
    heal_amount: int = 0
    kite_min: float = 0.0
    kite_max: float = 0.0
    threat: float = 1.0

    @property
    def alive(self) -> bool:
        return self.hp > 0

    def hp_ratio(self) -> float:
        if self.hp_max <= 0:
            return 0.0
        return self.hp / float(self.hp_max)


@dataclass
class LootDrop:
    id: str
    item_id: str
    item_name: str
    x: float
    y: float


@dataclass
class HuntYard:
    seed: int
    tick: int = 0
    status: str = "ongoing"
    players: list[Actor] = field(default_factory=list)
    beasts: list[Actor] = field(default_factory=list)
    loot: list[LootDrop] = field(default_factory=list)
    log: list[str] = field(default_factory=list)
    kills: int = 0
    heals: int = 0
    quest_id: str = QUEST_ID
    _loot_seq: int = 0

    def living_players(self) -> list[Actor]:
        return [p for p in self.players if p.alive]

    def living_beasts(self) -> list[Actor]:
        return [b for b in self.beasts if b.alive]


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _dist(a: Actor | LootDrop, b: Actor | LootDrop) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


def _move_towards(actor: Actor, tx: float, ty: float, *, reverse: bool = False) -> None:
    dx, dy = tx - actor.x, ty - actor.y
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return
    step = actor.speed
    ux, uy = dx / length, dy / length
    if reverse:
        ux, uy = -ux, -uy
    actor.x = _clamp(actor.x + ux * step, 0.6, WIDTH - 0.6)
    actor.y = _clamp(actor.y + uy * step, 0.6, HEIGHT - 0.6)


def _nearest(actor: Actor, others: list[Actor]) -> Actor | None:
    living = [o for o in others if o.alive and o.id != actor.id]
    if not living:
        return None
    return min(living, key=lambda o: _dist(actor, o))


def _append_log(yard: HuntYard, line: str) -> None:
    yard.log.append(f"t{yard.tick} {line}")
    if len(yard.log) > LOG_CAP:
        yard.log = yard.log[-LOG_CAP:]


def new_yard(*, seed: int = 1) -> HuntYard:
    rng = random.Random(int(seed))
    yard = HuntYard(seed=int(seed))
    yard.players = [
        Actor(
            id="lia",
            name="Lia",
            kind="player",
            role="tank",
            x=4.0,
            y=8.5,
            hp=140,
            hp_max=140,
            speed=0.62,
            atk_range=1.7,
            dmg=14,
            cooldown_max=6,
            color="#c45c26",
            potions=1,
            threat=3.0,
        ),
        Actor(
            id="nix",
            name="Nix",
            kind="player",
            role="ranged",
            x=3.2,
            y=10.4,
            hp=90,
            hp_max=90,
            speed=0.72,
            atk_range=6.4,
            dmg=9,
            cooldown_max=7,
            color="#2a8f8a",
            potions=1,
            kite_min=3.6,
            kite_max=6.0,
            threat=1.2,
        ),
        Actor(
            id="mira",
            name="Mira",
            kind="player",
            role="support",
            x=3.4,
            y=7.2,
            hp=100,
            hp_max=100,
            speed=0.58,
            atk_range=5.2,
            dmg=6,
            cooldown_max=8,
            color="#c9a227",
            potions=2,
            heal_range=6.5,
            heal_amount=14,
            threat=0.8,
        ),
    ]
    beasts: list[Actor] = []
    for i in range(5):
        beasts.append(
            Actor(
                id=f"chacal_{i + 1}",
                name=f"Chacal {i + 1}",
                kind="beast",
                role="pack",
                x=18.5 + rng.uniform(-2.2, 3.4),
                y=5.5 + i * 2.2 + rng.uniform(-0.4, 0.4),
                hp=28,
                hp_max=28,
                speed=0.48,
                atk_range=1.45,
                dmg=6,
                cooldown_max=8,
                color="#5c4030",
                threat=1.0,
            )
        )
    yard.beasts = beasts
    _append_log(yard, "Meute aux portes — Lia avance, Nix couvre, Mira soigne.")
    return yard


def _pick_player_target(actor: Actor, beasts: list[Actor]) -> Actor | None:
    living = [b for b in beasts if b.alive]
    if not living:
        return None
    if actor.role == "tank":
        return max(living, key=lambda b: (b.hp, -_dist(actor, b)))
    return min(living, key=lambda b: _dist(actor, b))


def _pick_beast_target(beast: Actor, players: list[Actor]) -> Actor | None:
    living = [p for p in players if p.alive]
    if not living:
        return None
    return max(living, key=lambda p: (p.threat / (1.0 + _dist(beast, p)), p.threat))


def _ally_to_heal(mira: Actor, players: list[Actor]) -> Actor | None:
    needy = [p for p in players if p.alive and p.id != mira.id and p.hp_ratio() <= 0.68]
    if not needy:
        return None
    needy.sort(key=lambda p: p.hp_ratio())
    for ally in needy:
        if _dist(mira, ally) <= mira.heal_range:
            return ally
    return needy[0]


def _nearby_loot(actor: Actor, drops: list[LootDrop], *, radius: float = 1.35) -> LootDrop | None:
    if not drops:
        return None
    close = [d for d in drops if math.hypot(actor.x - d.x, actor.y - d.y) <= radius]
    if not close:
        return None
    return min(close, key=lambda d: math.hypot(actor.x - d.x, actor.y - d.y))


def _threat_close(actor: Actor, beasts: list[Actor], *, radius: float = 3.2) -> bool:
    return any(b.alive and _dist(actor, b) <= radius for b in beasts)


def _drop_loot(yard: HuntYard, beast: Actor) -> None:
    yard._loot_seq += 1
    drop = LootDrop(
        id=f"loot_{yard._loot_seq}",
        item_id="fourrure_doree",
        item_name="Fourrure dorée",
        x=beast.x,
        y=beast.y,
    )
    yard.loot.append(drop)
    _append_log(yard, f"{beast.name} tombe — fourrure au sol.")


def _apply_damage(yard: HuntYard, attacker: Actor, target: Actor) -> None:
    target.hp = max(0, target.hp - attacker.dmg)
    attacker.last_action = "attack"
    attacker.last_target = target.id
    attacker.cooldown = attacker.cooldown_max
    _append_log(yard, f"{attacker.name} frappe {target.name} (−{attacker.dmg}).")
    if target.hp <= 0:
        if target.kind == "beast":
            yard.kills += 1
            _drop_loot(yard, target)
        else:
            _append_log(yard, f"{target.name} est hors combat.")


def _player_intent(yard: HuntYard, actor: Actor) -> None:
    if actor.cooldown > 0:
        actor.cooldown -= 1

    if actor.hp_ratio() <= 0.34 and actor.potions > 0:
        heal = 28
        actor.hp = min(actor.hp_max, actor.hp + heal)
        actor.potions -= 1
        actor.last_action = "use_potion"
        actor.last_target = actor.id
        _append_log(yard, f"{actor.name} boit une potion (+{heal}).")
        return

    if actor.role == "support":
        ally = _ally_to_heal(actor, yard.players)
        if ally is not None and actor.heal_amount > 0:
            if _dist(actor, ally) <= actor.heal_range and actor.cooldown == 0:
                ally.hp = min(ally.hp_max, ally.hp + actor.heal_amount)
                actor.last_action = "heal"
                actor.last_target = ally.id
                actor.cooldown = actor.cooldown_max
                yard.heals += 1
                _append_log(yard, f"{actor.name} soigne {ally.name} (+{actor.heal_amount}).")
                return
            if _dist(actor, ally) > actor.heal_range * 0.7:
                _move_towards(actor, ally.x, ally.y)
                actor.last_action = "move"
                actor.last_target = ally.id
                return

    drop = _nearby_loot(actor, yard.loot)
    if drop is not None and not _threat_close(actor, yard.beasts, radius=2.4):
        yard.loot = [d for d in yard.loot if d.id != drop.id]
        actor.loot_count += 1
        actor.last_action = "pickup"
        actor.last_target = drop.id
        _append_log(yard, f"{actor.name} ramasse {drop.item_name}.")
        return

    if not yard.living_beasts() and yard.loot:
        nearest = min(yard.loot, key=lambda d: math.hypot(actor.x - d.x, actor.y - d.y))
        _move_towards(actor, nearest.x, nearest.y)
        actor.last_action = "move"
        actor.last_target = nearest.id
        return

    target = _pick_player_target(actor, yard.beasts)
    if target is None:
        actor.last_action = "idle"
        actor.last_target = ""
        return

    dist = _dist(actor, target)
    if actor.role == "ranged" and dist < actor.kite_min and target.alive:
        _move_towards(actor, target.x, target.y, reverse=True)
        actor.last_action = "move"
        actor.last_target = target.id
        return

    if dist <= actor.atk_range and actor.cooldown == 0:
        _apply_damage(yard, actor, target)
        return

    if actor.role == "ranged" and dist > actor.kite_max:
        _move_towards(actor, target.x, target.y)
        actor.last_action = "move"
        actor.last_target = target.id
        return

    if dist > actor.atk_range:
        _move_towards(actor, target.x, target.y)
        actor.last_action = "move"
        actor.last_target = target.id
        return

    actor.last_action = "idle"
    actor.last_target = target.id


def _beast_intent(yard: HuntYard, beast: Actor) -> None:
    if beast.cooldown > 0:
        beast.cooldown -= 1
    target = _pick_beast_target(beast, yard.players)
    if target is None:
        beast.last_action = "idle"
        beast.last_target = ""
        return
    dist = _dist(beast, target)
    if dist <= beast.atk_range and beast.cooldown == 0:
        _apply_damage(yard, beast, target)
        return
    _move_towards(beast, target.x, target.y)
    beast.last_action = "move"
    beast.last_target = target.id


def _refresh_status(yard: HuntYard) -> None:
    if not yard.living_players():
        yard.status = "defeat"
        _append_log(yard, "Défaite — le chœur est à terre.")
        return
    if not yard.living_beasts() and not yard.loot:
        yard.status = "victory"
        _append_log(yard, "Victoire — meute dispersée, fourrures ramassées.")
        return
    if not yard.living_beasts():
        # encore du loot : on laisse ramasser
        return
    yard.status = "ongoing"


def tick(yard: HuntYard, n: int = 1) -> HuntYard:
    steps = max(1, min(int(n), 80))
    for _ in range(steps):
        if yard.status != "ongoing":
            break
        yard.tick += 1
        for player in yard.living_players():
            _player_intent(yard, player)
        for beast in yard.living_beasts():
            _beast_intent(yard, beast)
        _refresh_status(yard)
        if yard.tick >= TICK_CAP_DEFAULT and yard.status == "ongoing":
            yard.status = "defeat"
            _append_log(yard, "Temps écoulé — la meute tient encore la dune.")
            break
    return yard


def run_until_done(yard: HuntYard, *, max_ticks: int = TICK_CAP_DEFAULT) -> HuntYard:
    remain = max(1, int(max_ticks) - yard.tick)
    if remain > 0:
        tick(yard, remain)
    return yard


def _actor_payload(actor: Actor) -> dict[str, Any]:
    return {
        "id": actor.id,
        "name": actor.name,
        "kind": actor.kind,
        "role": actor.role,
        "x": round(actor.x, 3),
        "y": round(actor.y, 3),
        "hp": actor.hp,
        "hp_max": actor.hp_max,
        "alive": actor.alive,
        "potions": actor.potions,
        "loot_count": actor.loot_count,
        "last_action": actor.last_action,
        "last_target": actor.last_target,
        "color": actor.color,
        "atk_range": actor.atk_range,
    }


def snapshot(yard: HuntYard) -> dict[str, Any]:
    return {
        "ok": True,
        "seed": yard.seed,
        "tick": yard.tick,
        "status": yard.status,
        "quest_id": yard.quest_id,
        "width": WIDTH,
        "height": HEIGHT,
        "kills": yard.kills,
        "heals": yard.heals,
        "actions": list(action_contract()),
        "players": [_actor_payload(p) for p in yard.players],
        "beasts": [_actor_payload(b) for b in yard.beasts],
        "loot": [
            {
                "id": d.id,
                "item_id": d.item_id,
                "item_name": d.item_name,
                "x": round(d.x, 3),
                "y": round(d.y, 3),
            }
            for d in yard.loot
        ],
        "log": list(yard.log),
    }


_SESSION: HuntYard | None = None
_LOCK = threading.Lock()


def _state_path() -> Path:
    raw = os.environ.get("LBG_HUNT_YARD_STATE", "").strip()
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parent.parent / "data" / "hunt_yard_session.pkl"


def _persist(yard: HuntYard) -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as fh:
        pickle.dump(yard, fh, protocol=pickle.HIGHEST_PROTOCOL)


def _restore() -> HuntYard | None:
    path = _state_path()
    if not path.is_file():
        return None
    try:
        with path.open("rb") as fh:
            yard = pickle.load(fh)
        return yard if isinstance(yard, HuntYard) else None
    except Exception:
        return None


def session_reset(*, seed: int = 1) -> dict[str, Any]:
    global _SESSION
    with _LOCK:
        _SESSION = new_yard(seed=seed)
        _persist(_SESSION)
        return snapshot(_SESSION)


def session_snapshot() -> dict[str, Any]:
    global _SESSION
    with _LOCK:
        if _SESSION is None:
            _SESSION = _restore() or new_yard(seed=1)
            _persist(_SESSION)
        return snapshot(_SESSION)


def session_tick(n: int = 1) -> dict[str, Any]:
    global _SESSION
    with _LOCK:
        if _SESSION is None:
            _SESSION = _restore() or new_yard(seed=1)
        tick(_SESSION, n)
        _persist(_SESSION)
        return snapshot(_SESSION)


def session_run(*, max_ticks: int = TICK_CAP_DEFAULT) -> dict[str, Any]:
    global _SESSION
    with _LOCK:
        if _SESSION is None:
            _SESSION = _restore() or new_yard(seed=1)
        run_until_done(_SESSION, max_ticks=max_ticks)
        _persist(_SESSION)
        return snapshot(_SESSION)


def _ascii(yard: HuntYard) -> str:
    cols, rows = 28, 18
    grid = [["." for _ in range(cols)] for _ in range(rows)]
    for drop in yard.loot:
        gx = min(cols - 1, max(0, int(drop.x)))
        gy = min(rows - 1, max(0, int(drop.y)))
        grid[gy][gx] = "*"
    marks = {"lia": "L", "nix": "N", "mira": "M"}
    for beast in yard.beasts:
        gx = min(cols - 1, max(0, int(beast.x)))
        gy = min(rows - 1, max(0, int(beast.y)))
        grid[gy][gx] = "c" if beast.alive else "x"
    for player in yard.players:
        gx = min(cols - 1, max(0, int(player.x)))
        gy = min(rows - 1, max(0, int(player.y)))
        grid[gy][gx] = marks.get(player.id, "?") if player.alive else "_"
    return "\n".join("".join(row) for row in grid)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cour de chasse Lia / Nix / Mira")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--ticks", type=int, default=120)
    parser.add_argument("--ascii", action="store_true")
    parser.add_argument(
        "--json-cmd",
        choices=("reset", "snapshot", "tick", "run"),
        help="API session JSON (prime-hub peel) — état persisté via LBG_HUNT_YARD_STATE",
    )
    parser.add_argument("--max-ticks", type=int, default=TICK_CAP_DEFAULT)
    args = parser.parse_args(argv)
    if args.json_cmd:
        if args.json_cmd == "reset":
            out = session_reset(seed=int(args.seed))
        elif args.json_cmd == "snapshot":
            out = session_snapshot()
        elif args.json_cmd == "tick":
            out = session_tick(int(args.ticks))
        else:
            out = session_run(max_ticks=int(args.max_ticks))
        sys.stdout.write(json.dumps(out, ensure_ascii=False))
        sys.stdout.write("\n")
        return 0 if out.get("ok") is not False else 1
    yard = new_yard(seed=args.seed)
    tick(yard, args.ticks)
    snap = snapshot(yard)
    print(f"status={snap['status']} tick={snap['tick']} kills={snap['kills']} heals={snap['heals']}")
    for player in snap["players"]:
        print(
            f"  {player['name']}: hp={player['hp']}/{player['hp_max']} "
            f"loot={player['loot_count']} last={player['last_action']}"
        )
    if args.ascii:
        print(_ascii(yard))
    if snap["log"]:
        print("log:")
        for line in snap["log"][-12:]:
            print(f"  {line}")
    return 0 if snap["status"] == "victory" else 1


if __name__ == "__main__":
    raise SystemExit(main())
