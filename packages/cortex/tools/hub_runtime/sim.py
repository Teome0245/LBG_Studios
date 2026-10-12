"""Sim Lost Heaven — multi-humains + flotte IA (Nix/Lia/Mira/Kael) + PNJ vivants + collision."""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from typing import Any

from tools.hub_runtime.hub_collision import COLLISION

PLAZA = (4749.0, 0.15, -737.0)
MARKET = (4809.0, 0.15, -932.0)
# Apron OUEST du port shuttle (hors AABB 4832/-819 size 142) — évite Mira/Lia coincées dedans
STARPORT = (4740.0, 0.15, -820.0)
CANTINA = (4939.0, 0.15, -802.0)
MISSION = (4939.0, 0.15, -932.0)
CLINIC = (4679.0, 0.15, -672.0)
TRAINING = (4939.0, 0.15, -672.0)
INN = (4809.0, 0.15, -672.0)
TOWN_HALL = (4679.0, 0.15, -932.0)
ARTISAN = (5069.0, 0.15, -802.0)
SPAWN_HUMAN = (4758.0, 0.15, -545.0)

HUMAN_OID = 100001
BOT_WALK_SPEED = 12.0
HUMAN_DEFAULT_SPEED = 14.0

# Joueurs IA — oids stables ; préférences d'activité (pas de couloir)
BOT_DEFS: list[dict[str, Any]] = [
    {
        "eid": "player:Nix",
        "oid": 900002,
        "name": "Nix",
        "spawn": (4757.0, 0.15, -720.0),
        "prefer": ["plaza", "market", "apron", "board"],
        "greet": "Salut {who} — bienvenue au hub Lost Heaven.",
        "ambient": "{who}, je tourne sur le hub — board, marché, plaza.",
        "speed": BOT_WALK_SPEED,
    },
    {
        "eid": "player:Lia",
        "oid": 900003,
        "name": "Lia",
        "spawn": (4780.0, 0.15, -690.0),
        "prefer": ["inn", "cantina", "plaza", "craft"],
        "greet": "Hey {who}. Lia — auberge, cantina, atelier.",
        "ambient": "{who}, besoin d'un coup de main au hub ?",
        "speed": 11.5,
    },
    {
        "eid": "player:Mira",
        "oid": 900004,
        "name": "Mira",
        "spawn": (4700.0, 0.15, -900.0),
        "prefer": ["board", "market", "hall", "plaza"],
        "greet": "{who} — Mira. Board et marché, je joue les contrats.",
        "ambient": "Des contrats au board, {who}. Daan Oth t'attend.",
        "speed": 11.0,
    },
    {
        "eid": "player:Kael",
        "oid": 900005,
        "name": "Kael",
        "spawn": (4809.0, 0.15, -700.0),
        "prefer": ["train", "inn", "plaza", "clinic"],
        "greet": "{who}. Kael — trainers et auberge, côté nord.",
        "ambient": "Hall d'entraînement si tu veux te mesurer, {who}.",
        "speed": 11.0,
    },
]

# PNJ hub vivants — home + rayon wander (m) + ligne ambient
HUB_NPCS: list[dict[str, Any]] = [
    {"eid": "npc:core3_daan_oth", "oid": 910001, "name": "Daan Oth", "pos": MISSION, "wander_r": 10.0,
     "ambient": "Des offres au board — pas de touristes, des contrats."},
    {"eid": "npc:core3_barman_jax", "oid": 910002, "name": "Jax Moro", "pos": CANTINA, "wander_r": 6.0,
     "ambient": "La Perle reste ouverte. Un verre, ou juste l'ombre."},
    {"eid": "npc:guide_quartier", "oid": 910003, "name": "Guide de quartier", "pos": STARPORT, "wander_r": 14.0,
     "ambient": "Starport, marché, porte est — tu te perds, tu cries."},
    {"eid": "npc:core3_medic_trainer_c", "oid": 910004, "name": "Odo Merr", "pos": CLINIC, "wander_r": 8.0,
     "ambient": "Clinique. Kits d'abord, discours après."},
    {"eid": "npc:core3_scout_trainer_c", "oid": 910005, "name": "Yara Nis", "pos": TRAINING, "wander_r": 12.0,
     "ambient": "Pistes hors remparts — le désert ne pardonne pas."},
    {"eid": "npc:core3_artisan_trainer_c", "oid": 910006, "name": "Kell Asa", "pos": ARTISAN, "wander_r": 10.0,
     "ambient": "Atelier ouvert. On assemble ce qu'on ramasse."},
    {"eid": "npc:core3_talen_ress", "oid": 910007, "name": "Talen Ress", "pos": INN, "wander_r": 8.0,
     "ambient": "Formation scène à l'auberge — danse, musique, moral."},
    {"eid": "npc:scribe", "oid": 910008, "name": "Scribe", "pos": TOWN_HALL, "wander_r": 6.0,
     "ambient": "Chroniques de session. Pas de légendes inventées."},
    {"eid": "npc:habitue_cantina", "oid": 910009, "name": "Habitué", "pos": CANTINA, "wander_r": 9.0,
     "ambient": "Toujours la même table à La Perle…"},
    {"eid": "npc:videur", "oid": 910010, "name": "Videur", "pos": (4920.0, 0.15, -790.0), "wander_r": 7.0,
     "ambient": "Pas de bagarre devant La Perle."},
    {"eid": "npc:sergent_rue", "oid": 910011, "name": "Sergent de rue", "pos": (4880.0, 0.15, -880.0), "wander_r": 16.0,
     "ambient": "Porte est surveillée. Meute ou pas — on tient."},
    {"eid": "npc:rumeuriste", "oid": 910012, "name": "Rumeuriste", "pos": MARKET, "wander_r": 14.0,
     "ambient": "Au marché on entend tout — et on répète la moitié."},
    {"eid": "npc:core3_brawler_trainer_c", "oid": 910013, "name": "Tobin Ress", "pos": TRAINING, "wander_r": 11.0,
     "ambient": "Poing avant paroles. Hall d'entraînement."},
    {"eid": "npc:core3_marksman_trainer_c", "oid": 910014, "name": "Unar Tek", "pos": (4960.0, 0.15, -690.0), "wander_r": 11.0,
     "ambient": "Visée. Respire, tire, ne rate pas le désert."},
    {"eid": "npc:core3_pilot_imperial_a", "oid": 910015, "name": "Garr Vek", "pos": STARPORT, "wander_r": 12.0,
     "ambient": "Pilotage shuttle — apron propre, décollages courts."},
]

IA_NAMES = frozenset(str(b["name"]).lower() for b in BOT_DEFS)
IA_EIDS = frozenset(str(b["eid"]) for b in BOT_DEFS)


def _human_key(oid: int) -> str:
    return f"player:{int(oid)}"


def _walkable(x: float, z: float) -> tuple[float, float]:
    if COLLISION.allows(x, z):
        return x, z
    return COLLISION.nearest_walkable(x, z)


@dataclass
class Entity:
    eid: str
    oid: int
    kind: str
    name: str
    x: float
    y: float
    z: float
    target: tuple[float, float, float] | None = None
    speed: float = BOT_WALK_SPEED
    stuck_ticks: int = 0
    patrol_i: int = 0
    waypoint: tuple[float, float] | None = None
    is_bot: bool = False
    home_x: float = 0.0
    home_z: float = 0.0
    wander_r: float = 0.0
    ambient: str = ""
    goal_id: str = ""
    goal_label: str = ""
    linger_until: float = 0.0
    play_mode: str = ""  # hub | quest | explore | social
    quest_id: str = ""
    quest_step_id: str = ""
    arrive_radius: float = 3.0
    path: list[tuple[float, float]] = field(default_factory=list)


@dataclass
class WorldSim:
    zone: str = "scrapaltai"
    tick: int = 0
    entities: dict[str, Entity] = field(default_factory=dict)
    human_oid: int = HUMAN_OID
    _last_ts: float = field(default_factory=time.monotonic)
    _spawn_slot: int = 0
    _chat_queue: list[dict[str, Any]] = field(default_factory=list)
    _greeted_oids: set[int] = field(default_factory=set)
    _last_ambient: dict[str, float] = field(default_factory=dict)
    _last_agent_ts: float = 0.0
    _agent_bot_i: int = 0
    _llm_say_requests: list[dict[str, Any]] = field(default_factory=list)

    def reset(self) -> None:
        self.tick = 0
        self.entities.clear()
        self._spawn_slot = 0
        self._chat_queue.clear()
        self._greeted_oids.clear()
        self._last_ambient.clear()
        self._last_agent_ts = 0.0
        self._agent_bot_i = 0
        self._llm_say_requests.clear()
        COLLISION.reload()
        self._ensure_fleet()
        self._ensure_hub_npcs()
        self._last_ts = time.monotonic()

    def _ensure_fleet(self) -> None:
        for b in BOT_DEFS:
            eid = str(b["eid"])
            if eid in self.entities:
                continue
            sx, sy, sz = b["spawn"]
            sx, sz = _walkable(float(sx), float(sz))
            ent = Entity(
                eid=eid,
                oid=int(b["oid"]),
                kind="player",
                name=str(b["name"]),
                x=sx,
                y=float(sy),
                z=sz,
                speed=float(b.get("speed", BOT_WALK_SPEED)),
                is_bot=True,
            )
            ent.target = self._bot_patrol_target(ent, b)
            self.entities[eid] = ent

    def _ensure_hub_npcs(self) -> None:
        for n in HUB_NPCS:
            eid = str(n["eid"])
            if eid in self.entities:
                continue
            px, py, pz = n["pos"]
            px, pz = _walkable(float(px), float(pz))
            wander = float(n.get("wander_r") or 0.0)
            self.entities[eid] = Entity(
                eid=eid,
                oid=int(n["oid"]),
                kind="npc",
                name=str(n["name"]),
                x=px,
                y=float(py),
                z=pz,
                speed=4.5 if wander > 0 else 0.0,
                is_bot=False,
                home_x=px,
                home_z=pz,
                wander_r=wander,
                ambient=str(n.get("ambient") or ""),
            )

    def ensure(self) -> None:
        if not self.entities:
            self.reset()
            return
        self._ensure_fleet()
        self._ensure_hub_npcs()

    def _bot_def(self, eid: str) -> dict[str, Any] | None:
        for b in BOT_DEFS:
            if b["eid"] == eid:
                return b
        return None

    def _bot_patrol_target(self, bot: Entity, bdef: dict[str, Any] | None = None) -> tuple[float, float, float]:
        """Compat — délègue au pick goal."""
        return self._assign_bot_goal(bot, bdef) or MARKET

    def _assign_bot_goal(
        self, bot: Entity, bdef: dict[str, Any] | None = None
    ) -> tuple[float, float, float]:
        from tools.hub_runtime.bot_play import assign_play_goal

        bdef = bdef or self._bot_def(bot.eid) or {}
        prefer = list(bdef.get("prefer") or [])
        # parfois suivre un humain (jouer social)
        humans = [e for e in self.entities.values() if e.kind == "player" and not e.is_bot]
        if humans and random.random() < 0.12:
            h = random.choice(humans)
            gx, gz = _walkable(h.x + random.uniform(-6, 6), h.z + random.uniform(-6, 6))
            bot.goal_id = "social"
            bot.goal_label = f"rejoindre {h.name}"
            bot.play_mode = "social"
            bot.quest_id = ""
            bot.quest_step_id = ""
            bot.arrive_radius = 4.0
            bot.linger_until = 0.0
            bot.target = (gx, 0.15, gz)
            bot.waypoint = None
            bot.path = []
            bot.stuck_ticks = 0
            return bot.target
        play = assign_play_goal(bot, prefer=prefer)
        tx, ty, tz = play["target"]
        gx, gz = _walkable(float(tx), float(tz))
        bot.goal_id = str(play["goal_id"])
        bot.goal_label = str(play["goal_label"])
        bot.play_mode = str(play.get("mode") or "hub")
        bot.quest_id = str(play.get("quest_id") or "")
        bot.quest_step_id = str(play.get("step_id") or "")
        bot.arrive_radius = float(play.get("radius_m") or 4.0)
        bot.linger_until = 0.0
        bot.target = (gx, 0.15, gz)
        bot.waypoint = None
        bot.stuck_ticks = 0
        # Path A* (évite starport / AABB) — waypoints intermédiaires
        route = COLLISION.find_path(bot.x, bot.z, gx, gz)
        bot.path = list(route[:-1]) if len(route) > 1 else []
        if bot.path:
            bot.waypoint = bot.path.pop(0)
        say = str(play.get("say") or "")
        if say:
            self.enqueue_say(bot.name, int(bot.oid), say, source="ia")
        return bot.target

    def _on_bot_arrived(self, bot: Entity) -> None:
        from tools.hub_runtime.bot_play import on_bot_arrived_play

        info = on_bot_arrived_play(bot)
        bot.linger_until = time.monotonic() + float(info.get("linger") or 4.0)
        near = ""
        for h in self.entities.values():
            if h.kind == "player" and not h.is_bot and math.hypot(h.x - bot.x, h.z - bot.z) < 35:
                near = h.name
                break
        line = str(info.get("say") or "") or f"{bot.name} — {bot.goal_label or 'je bouge'}."
        self.enqueue_say(bot.name, int(bot.oid), line, source="ia")
        self._llm_say_requests.append(
            {
                "name": bot.name,
                "oid": int(bot.oid),
                "goal": bot.goal_label or bot.goal_id or "explorer",
                "near": near,
                "place": bot.play_mode or bot.goal_id or "hub",
            }
        )

    def drain_llm_say_requests(self) -> list[dict[str, Any]]:
        if not self._llm_say_requests:
            return []
        out = list(self._llm_say_requests)
        self._llm_say_requests.clear()
        return out

    def resolve_bot_key(self, player: str) -> str | None:
        p = str(player or "").strip()
        if not p:
            return None
        if p in self.entities and self.entities[p].is_bot:
            return p
        low = p.lower()
        if low.startswith("player:"):
            low = low.split(":", 1)[1]
        for b in BOT_DEFS:
            if str(b["name"]).lower() == low or str(b["eid"]).lower().endswith(low):
                return str(b["eid"])
        return None

    def ensure_human(self, oid: int, name: str) -> Entity:
        self.ensure()
        key = _human_key(oid)
        existing = self.entities.get(key)
        if existing is not None:
            existing.name = name or existing.name
            existing.oid = int(oid)
            self.human_oid = int(oid)
            return existing
        slot = self._spawn_slot
        self._spawn_slot += 1
        hx = SPAWN_HUMAN[0] + (slot % 5) * 6.0
        hz = SPAWN_HUMAN[2] - (slot // 5) * 6.0
        hx, hz = _walkable(hx, hz)
        ent = Entity(
            eid=key,
            oid=int(oid),
            kind="player",
            name=name or f"Joueur{oid}",
            x=hx,
            y=SPAWN_HUMAN[1],
            z=hz,
            speed=HUMAN_DEFAULT_SPEED,
            is_bot=False,
        )
        self.entities[key] = ent
        self.human_oid = int(oid)
        return ent

    def remove_human(self, oid: int) -> None:
        self.entities.pop(_human_key(oid), None)
        self._greeted_oids.discard(int(oid))

    def enqueue_say(
        self,
        from_name: str,
        oid: int,
        text: str,
        *,
        source: str = "human",
        queue: bool = True,
    ) -> dict[str, Any] | None:
        t = str(text or "").strip()
        if not t:
            return None
        if len(t) > 200:
            t = t[:200]
        msg = {
            "type": "chat",
            "proto": "lbg-ws/2",
            "from": str(from_name or "?"),
            "oid": int(oid),
            "text": t,
            "source": source if source in {"human", "ia", "system"} else "human",
            "server_time_ms": int(time.time() * 1000),
        }
        if queue:
            self._chat_queue.append(msg)
        return msg

    def drain_chat(self) -> list[dict[str, Any]]:
        if not self._chat_queue:
            return []
        out = list(self._chat_queue)
        self._chat_queue.clear()
        return out

    def fleet_greet_human(self, human_name: str, human_oid: int) -> None:
        oid = int(human_oid)
        if oid in self._greeted_oids:
            return
        self._greeted_oids.add(oid)
        self.ensure()
        who = (human_name or "Voyageur").strip() or "Voyageur"
        for b in BOT_DEFS:
            bot = self.entities.get(str(b["eid"]))
            if bot is None:
                continue
            line = str(b.get("greet") or "Salut {who}.").format(who=who)
            self.enqueue_say(str(b["name"]), int(bot.oid), line, source="ia")

    # compat ancien nom
    def nix_greet_human(self, human_name: str, human_oid: int) -> None:
        self.fleet_greet_human(human_name, human_oid)

    def maybe_fleet_ambient(self) -> None:
        now = time.monotonic()
        humans = [
            e
            for e in self.entities.values()
            if e.kind == "player" and not e.is_bot
        ]
        if not humans:
            return
        for b in BOT_DEFS:
            eid = str(b["eid"])
            bot = self.entities.get(eid)
            if bot is None:
                continue
            last = self._last_ambient.get(eid, 0.0)
            if now - last < 50.0 + (hash(eid) % 20):
                continue
            near = None
            for h in humans:
                if math.hypot(h.x - bot.x, h.z - bot.z) <= 32.0:
                    near = h
                    break
            if near is None:
                continue
            self._last_ambient[eid] = now
            template = str(b.get("ambient") or "{who}.")
            # ligne goal si dispo
            if bot.goal_label:
                line = f"{bot.name} — {bot.goal_label}."
            else:
                line = template.format(who=near.name)
            self.enqueue_say(str(b["name"]), int(bot.oid), line, source="ia")
            # demande LLM async (serveur drainera)
            self._llm_say_requests.append(
                {
                    "name": str(b["name"]),
                    "oid": int(bot.oid),
                    "goal": bot.goal_label or "explorer",
                    "near": near.name,
                    "place": bot.goal_id or "hub",
                }
            )

    def maybe_npc_ambient(self) -> None:
        """PNJ vivants — réplique courte si humain proche."""
        now = time.monotonic()
        humans = [e for e in self.entities.values() if e.kind == "player" and not e.is_bot]
        if not humans:
            return
        for e in self.entities.values():
            if e.kind != "npc" or not e.ambient:
                continue
            last = self._last_ambient.get(e.eid, 0.0)
            if now - last < 70.0 + (e.oid % 25):
                continue
            near = None
            for h in humans:
                if math.hypot(h.x - e.x, h.z - e.z) <= 22.0:
                    near = h
                    break
            if near is None:
                continue
            self._last_ambient[e.eid] = now
            self.enqueue_say(e.name, int(e.oid), e.ambient, source="ia")

    def _pick_wander_target(self, ent: Entity) -> tuple[float, float, float]:
        r = max(2.0, float(ent.wander_r))
        ang = random.uniform(0.0, math.tau)
        dist = random.uniform(r * 0.25, r)
        tx = ent.home_x + math.cos(ang) * dist
        tz = ent.home_z + math.sin(ang) * dist
        wx, wz = _walkable(tx, tz)
        if math.hypot(wx - ent.home_x, wz - ent.home_z) > r * 1.4:
            wx, wz = _walkable(ent.home_x, ent.home_z)
        return (wx, ent.y, wz)

    def _step_npc(self, npc: Entity, dt: float) -> None:
        if npc.wander_r <= 0 or npc.speed <= 0:
            return
        if npc.target is None:
            npc.target = self._pick_wander_target(npc)
        assert npc.target is not None
        tx, ty, tz = npc.target
        dx, dz = tx - npc.x, tz - npc.z
        dist = math.hypot(dx, dz)
        if dist < 1.5:
            npc.target = self._pick_wander_target(npc)
            npc.stuck_ticks = 0
            return
        step = min(dist, npc.speed * dt)
        nx = npc.x + (dx / dist) * step
        nz = npc.z + (dz / dist) * step
        cx, cz = COLLISION.clamp_move(npc.x, npc.z, nx, nz)
        moved = math.hypot(cx - npc.x, cz - npc.z)
        if moved < step * 0.15:
            npc.stuck_ticks += 1
            if npc.stuck_ticks >= 5:
                hx, hz = _walkable(npc.home_x, npc.home_z)
                npc.x, npc.z = hx, hz
                npc.target = self._pick_wander_target(npc)
                npc.stuck_ticks = 0
                return
        else:
            npc.stuck_ticks = 0
        npc.x, npc.z = cx, cz
        npc.y = ty

    def maybe_agent_directive(self) -> None:
        """Si un bot n'a plus de cible — nouveau goal joué (pas de couloir)."""
        now = time.monotonic()
        if now - self._last_agent_ts < 8.0:
            return
        self._last_agent_ts = now
        for b in BOT_DEFS:
            bot = self.entities.get(str(b["eid"]))
            if bot is None:
                continue
            if bot.linger_until > now:
                continue
            if bot.target is None:
                self._assign_bot_goal(bot, b)

    def set_bot_target(self, player: str, x: float, y: float, z: float) -> Entity | None:
        key = self.resolve_bot_key(player)
        if key is None:
            return None
        self.ensure()
        ent = self.entities.get(key)
        if ent is None or not ent.is_bot:
            return None
        wx, wz = _walkable(float(x), float(z))
        ent.target = (wx, float(y), wz)
        ent.waypoint = None
        ent.stuck_ticks = 0
        return ent

    def set_human_pos(self, oid: int, x: float, y: float, z: float) -> None:
        self.ensure()
        h = self.entities.get(_human_key(oid))
        if h is None:
            return
        # Rejeter origine / hors Scrapaltai (client LastPos pourri)
        if (abs(float(x)) < 50.0 and abs(float(z)) < 50.0) or float(x) < 2500.0 or float(x) > 7500.0:
            return
        nx, nz = COLLISION.clamp_move(h.x, h.z, float(x), float(z))
        h.x, h.y, h.z = nx, float(y), nz
        h.target = None

    def _step_bot(self, bot: Entity, dt: float) -> None:
        bdef = self._bot_def(bot.eid)
        now = time.monotonic()
        # Linger sur l'objectif (joue sur place)
        if bot.linger_until > now:
            return
        if bot.linger_until > 0 and bot.linger_until <= now:
            bot.linger_until = 0.0
            self._assign_bot_goal(bot, bdef)
            return
        if bot.target is None:
            self._assign_bot_goal(bot, bdef)
        goal = bot.target
        if bot.waypoint is not None:
            wx, wz = bot.waypoint
            if math.hypot(wx - bot.x, wz - bot.z) < 4.0:
                if bot.path:
                    bot.waypoint = bot.path.pop(0)
                else:
                    bot.waypoint = None
            else:
                goal = (wx, bot.y, wz)
        elif bot.path:
            bot.waypoint = bot.path.pop(0)
            wx, wz = bot.waypoint
            goal = (wx, bot.y, wz)
        if goal is None:
            return
        tx, ty, tz = goal
        dx, dz = tx - bot.x, tz - bot.z
        dist = math.hypot(dx, dz)
        arrive_r = max(3.0, float(getattr(bot, "arrive_radius", 3.0) or 3.0))
        if bot.play_mode in ("quest", "explore"):
            arrive_r = max(arrive_r * 0.35, 8.0)
        # Arrivée finale seulement si plus de waypoint path
        if bot.waypoint is None and not bot.path and dist < arrive_r:
            self._on_bot_arrived(bot)
            bot.stuck_ticks = 0
            return
        if dist < 1e-6:
            return
        step = min(dist, bot.speed * dt)
        nx = bot.x + (dx / dist) * step
        nz = bot.z + (dz / dist) * step
        cx, cz = COLLISION.clamp_move(bot.x, bot.z, nx, nz)
        moved = math.hypot(cx - bot.x, cz - bot.z)
        if moved < step * 0.15:
            bot.stuck_ticks += 1
            if bot.stuck_ticks >= 3:
                final = bot.target or MARKET
                if bot.stuck_ticks >= 8 and bot.play_mode in ("quest", "explore") and not bot.path:
                    self._on_bot_arrived(bot)
                    bot.stuck_ticks = 0
                    return
                if bot.stuck_ticks >= 6:
                    # Re-plan A* depuis position actuelle
                    fx, fz = final[0], final[2]
                    route = COLLISION.find_path(bot.x, bot.z, fx, fz)
                    bot.path = list(route[:-1]) if len(route) > 1 else []
                    bot.waypoint = bot.path.pop(0) if bot.path else None
                    if bot.waypoint is None and route:
                        # un seul point — detour classique
                        detour = COLLISION.detour_waypoint(bot.x, bot.z, fx, fz)
                        bot.waypoint = detour
                    bot.stuck_ticks = 0
                    return
                if bot.stuck_ticks >= 12:
                    # Unstick local (pas de téléport plaza = snap caméra)
                    sx, sz = _walkable(bot.x + random.uniform(-20, 20), bot.z + random.uniform(-20, 20))
                    bot.x, bot.z = sx, sz
                    bot.waypoint = None
                    bot.path.clear()
                    self._assign_bot_goal(bot, bdef)
                    bot.stuck_ticks = 0
                    return
                detour = COLLISION.detour_waypoint(bot.x, bot.z, final[0], final[2])
                if detour is not None:
                    bot.waypoint = detour
                bot.stuck_ticks = 0
        else:
            bot.stuck_ticks = 0
        bot.x, bot.z = cx, cz
        bot.y = ty


    def step(self, dt: float | None = None) -> None:
        self.ensure()
        now = time.monotonic()
        if dt is None:
            dt = max(0.001, min(0.25, now - self._last_ts))
        else:
            dt = max(0.001, min(0.25, float(dt)))
        self._last_ts = now
        self.tick += 1
        for e in list(self.entities.values()):
            if e.is_bot:
                self._step_bot(e, dt)
            elif e.kind == "npc":
                self._step_npc(e, dt)
        self.maybe_agent_directive()
        self.maybe_fleet_ambient()
        self.maybe_npc_ambient()

    def entity_list(self) -> list[dict[str, Any]]:
        self.ensure()
        out: list[dict[str, Any]] = []
        for e in self.entities.values():
            out.append(
                {
                    "id": e.oid,
                    "entity_key": e.eid,
                    "kind": e.kind,
                    "name": e.name,
                    "pos": [e.x, e.y, e.z],
                    "source": "hub_runtime",
                    "goal": e.goal_id if e.is_bot else "",
                    "play_mode": e.play_mode if e.is_bot else "",
                    "quest_id": e.quest_id if e.is_bot else "",
                    "is_bot": bool(e.is_bot),
                }
            )
        return out

    def human_count(self) -> int:
        return sum(1 for e in self.entities.values() if e.kind == "player" and not e.is_bot)

    def bot_count(self) -> int:
        return sum(1 for e in self.entities.values() if e.is_bot)

    def npc_count(self) -> int:
        return sum(1 for e in self.entities.values() if e.kind == "npc")

    def online_players(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for e in self.entities.values():
            if e.kind != "player" or e.is_bot:
                continue
            out.append({"id": e.oid, "name": e.name})
        return out

    def bots_payload(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for e in self.entities.values():
            if not e.is_bot:
                continue
            out.append(
                {
                    "id": e.oid,
                    "entity_key": e.eid,
                    "name": e.name,
                    "pos": [e.x, e.y, e.z],
                    "target": list(e.target) if e.target else None,
                    "goal": e.goal_id,
                    "play_mode": e.play_mode,
                    "quest_id": e.quest_id,
                }
            )
        return out

    def zone_state_payload(self, your_oid: int | None = None) -> dict[str, Any]:
        oid = int(your_oid) if your_oid else self.human_oid
        online = self.online_players()
        h = self.entities.get(_human_key(oid))
        payload: dict[str, Any] = {
            "type": "zone_state",
            "proto": "lbg-ws/2",
            "zone": self.zone,
            "tick": self.tick,
            "server_time_ms": int(time.time() * 1000),
            "entities": self.entity_list(),
            "your_character_id": oid,
            "session_policy": "spike",
            "collision_blocks": len(COLLISION.blocks),
            "online_players": online,
            "online_count": len(online),
            "bots": self.bots_payload(),
            "bot_count": self.bot_count(),
            "npc_count": self.npc_count(),
        }
        # Toujours renvoyer la pos joueur (évite client coincé en 0,0 si enter_world raté)
        if h is not None:
            payload["position"] = [h.x, h.y, h.z]
        return payload

    def enter_world_payload(self, your_oid: int) -> dict[str, Any]:
        self.ensure()
        h = self.entities.get(_human_key(your_oid)) or self.ensure_human(your_oid, "Voyageur")
        base = self.zone_state_payload(your_oid)
        base["type"] = "enter_world"
        base["position"] = [h.x, h.y, h.z]
        return base


SIM = WorldSim()
