extends Node
## Sim hub G5+ — flotte autonome + Triplons (work/leisure/rest) + chat sobre.

const HubCollisionScript = preload("res://scripts/hub_collision.gd")
const HubPlayerStoreScript = preload("res://scripts/hub_player_store.gd")
const HubLifeScript = preload("res://scripts/hub_life.gd")
const HubBotAutonomyScript = preload("res://scripts/hub_bot_autonomy.gd")
const HubWorldSuggestScript = preload("res://scripts/hub_world_suggest.gd")
const HubAgentApiScript = preload("res://scripts/hub_agent_api.gd")
const _HubPaths = preload("res://scripts/hub_paths.gd")

const HUMAN_OID := 100001
const ZONE := "scrapaltai"
const SPAWN_HUMAN := Vector3(4758.0, 0.15, -545.0)
const PLAZA := Vector3(4749.0, 0.15, -737.0)
const MARKET := Vector3(4809.0, 0.15, -932.0)
const STARPORT := Vector3(4740.0, 0.15, -820.0)
const CANTINA := Vector3(4939.0, 0.15, -802.0)
const MISSION := Vector3(4939.0, 0.15, -932.0)
const CLINIC := Vector3(4679.0, 0.15, -672.0)
const TRAINING := Vector3(4939.0, 0.15, -672.0)
const INN := Vector3(4809.0, 0.15, -672.0)
const TOWN_HALL := Vector3(4679.0, 0.15, -932.0)
const ARTISAN := Vector3(5069.0, 0.15, -802.0)
const BOT_SPEED := 12.0

const POIS: Dictionary = {
	"plaza": PLAZA,
	"market": MARKET,
	"apron": STARPORT,
	"board": MISSION,
	"cantina": CANTINA,
	"inn": INN,
	"clinic": CLINIC,
	"train": TRAINING,
	"hall": TOWN_HALL,
	"craft": ARTISAN,
}

## Fallback si ai_players.json absent
const BOT_DEFS_FALLBACK: Array = [
	{
		"eid": "player:Nix", "oid": 900002, "name": "Nix",
		"spawn": Vector3(4757.0, 0.15, -720.0), "speed": 12.0,
		"prefer": ["plaza", "market", "apron", "board"],
		"greet": "Salut {who} — bienvenue au hub Lost Heaven.",
		"ambient": "{who}, je tourne sur le hub — board, marché, plaza.",
	},
	{
		"eid": "player:Lia", "oid": 900003, "name": "Lia",
		"spawn": Vector3(4780.0, 0.15, -690.0), "speed": 11.5,
		"prefer": ["inn", "cantina", "plaza", "craft"],
		"greet": "Hey {who}. Lia — auberge, cantina, atelier.",
		"ambient": "{who}, besoin d'un coup de main au hub ?",
	},
	{
		"eid": "player:Mira", "oid": 900004, "name": "Mira",
		"spawn": Vector3(4700.0, 0.15, -900.0), "speed": 11.0,
		"prefer": ["board", "market", "hall", "plaza"],
		"greet": "{who} — Mira. Board et marché, je joue les contrats.",
		"ambient": "Des contrats au board, {who}. Daan Oth t'attend.",
	},
	{
		"eid": "player:Kael", "oid": 900005, "name": "Kael",
		"spawn": Vector3(4809.0, 0.15, -700.0), "speed": 11.0,
		"prefer": ["train", "inn", "plaza", "clinic"],
		"greet": "{who}. Kael — trainers et auberge, côté nord.",
		"ambient": "Hall d'entraînement si tu veux te mesurer, {who}.",
	},
]

const HUB_NPCS: Array = [
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
	{"eid": "npc:videur", "oid": 910010, "name": "Videur", "pos": Vector3(4920.0, 0.15, -790.0), "wander_r": 7.0,
		"ambient": "Pas de bagarre devant La Perle."},
	{"eid": "npc:sergent_rue", "oid": 910011, "name": "Sergent de rue", "pos": Vector3(4880.0, 0.15, -880.0), "wander_r": 16.0,
		"ambient": "Porte est surveillée. Meute ou pas — on tient."},
	{"eid": "npc:rumeuriste", "oid": 910012, "name": "Rumeuriste", "pos": MARKET, "wander_r": 14.0,
		"ambient": "Au marché on entend tout — et on répète la moitié."},
	{"eid": "npc:core3_brawler_trainer_c", "oid": 910013, "name": "Tobin Ress", "pos": TRAINING, "wander_r": 11.0,
		"ambient": "Poing avant paroles. Hall d'entraînement."},
	{"eid": "npc:core3_marksman_trainer_c", "oid": 910014, "name": "Unar Tek", "pos": Vector3(4960.0, 0.15, -690.0), "wander_r": 11.0,
		"ambient": "Visée. Respire, tire, ne rate pas le désert."},
	{"eid": "npc:core3_pilot_imperial_a", "oid": 910015, "name": "Garr Vek", "pos": STARPORT, "wander_r": 12.0,
		"ambient": "Pilotage shuttle — apron propre, décollages courts."},
]

var collision = null
var player_store = null
var life = null
var autonomy = null
var suggest = null
var economy = null
var agent_api = null
var bot_defs: Array = []
var tick: int = 0
var entities: Dictionary = {}
var _chat_queue: Array = []
var _greeted_oids: Dictionary = {}  # oid -> true
var _last_ambient: Dictionary = {}  # eid -> float unix
var _rng := RandomNumberGenerator.new()
var _persist_every_ticks: int = 100  # ~5 s @ 20 Hz
var _life_tick_every: int = 20  # ~1 s


func attach_economy(economy_svc) -> void:
	economy = economy_svc
	if autonomy != null:
		autonomy.economy = economy_svc


func reset() -> void:
	tick = 0
	entities.clear()
	_chat_queue.clear()
	_greeted_oids.clear()
	_last_ambient.clear()
	_rng.randomize()
	if collision == null:
		collision = HubCollisionScript.new()
	collision.reload()
	if player_store == null:
		player_store = HubPlayerStoreScript.new()
		player_store.setup()
	if suggest == null:
		suggest = HubWorldSuggestScript.new()
		suggest.setup()
	if agent_api == null:
		agent_api = HubAgentApiScript.new()
	agent_api.setup()
	_load_bot_defs()
	if life == null:
		life = HubLifeScript.new()
	life.setup(POIS)
	if autonomy == null:
		autonomy = HubBotAutonomyScript.new()
	autonomy.setup(economy, suggest, POIS)
	_ensure_fleet()
	_ensure_hub_npcs()


func _load_bot_defs() -> void:
	bot_defs.clear()
	var raw: Variant = _HubPaths.read_json(_HubPaths.data_file("life/ai_players.json"))
	var max_n := 10
	if agent_api != null:
		max_n = agent_api.effective_max()
	if typeof(raw) == TYPE_DICTIONARY:
		var arr = raw.get("players", [])
		if typeof(arr) == TYPE_ARRAY:
			for p in arr:
				if typeof(p) != TYPE_DICTIONARY:
					continue
				if not bool(p.get("enabled", false)):
					continue
				if bot_defs.size() >= max_n:
					break
				bot_defs.append(_normalize_bot_row(p))
	if bot_defs.is_empty():
		bot_defs = BOT_DEFS_FALLBACK.duplicate(true)
		while bot_defs.size() > max_n:
			bot_defs.pop_back()


func _normalize_bot_row(p: Dictionary) -> Dictionary:
	var spawn_v: Vector3 = Vector3(4757.0, 0.15, -720.0)
	var sp = p.get("spawn", null)
	if typeof(sp) == TYPE_ARRAY and sp.size() >= 3:
		spawn_v = Vector3(float(sp[0]), float(sp[1]), float(sp[2]))
	elif typeof(sp) == TYPE_VECTOR3:
		spawn_v = sp
	var prefer: Array = []
	var pref = p.get("prefer", [])
	if typeof(pref) == TYPE_ARRAY:
		prefer = pref
	var og = p.get("out_game", {})
	if typeof(og) != TYPE_DICTIONARY:
		og = {}
	return {
		"eid": str(p.get("eid", "player:%s" % p.get("name", "Bot"))),
		"oid": int(p.get("oid", 900000)),
		"name": str(p.get("name", "Bot")),
		"spawn": spawn_v,
		"speed": float(p.get("speed", BOT_SPEED)),
		"prefer": prefer,
		"greet": str(p.get("greet", "")),
		"ambient": str(p.get("ambient", "")),
		"playstyle": str(p.get("playstyle", "")),
		"admin_level": int(p.get("admin_level", 0)),
		"admin_label": str(p.get("admin_label", "player")),
		# Login = persona out-game (pas le nom IG)
		"account_login": str(p.get("account_login", og.get("persona", ""))),
		"account_login_legacy": str(p.get("account_login_legacy", "")),
		"out_game_persona": str(og.get("persona", "")),
		"agent_id": str(og.get("agent_id", "")),
	}


func _walkable_xz(x: float, z: float) -> Vector2:
	if collision == null:
		return Vector2(x, z)
	if collision.allows(x, z):
		return Vector2(x, z)
	return collision.nearest_walkable(x, z)


func _bot_def(eid: String) -> Dictionary:
	for b in bot_defs:
		if str(b["eid"]) == eid:
			return b
	return {}


func _ensure_fleet() -> void:
	if bot_defs.is_empty():
		_load_bot_defs()
	for b in bot_defs:
		var eid: String = str(b["eid"])
		if entities.has(eid):
			continue
		var spawn: Vector3 = b["spawn"]
		var wz := _walkable_xz(spawn.x, spawn.z)
		spawn = Vector3(wz.x, spawn.y, wz.y)
		var ent := {
			"eid": eid,
			"oid": int(b["oid"]),
			"kind": "player",
			"name": str(b["name"]),
			"pos": spawn,
			"target": Vector3.ZERO,
			"speed": float(b.get("speed", BOT_SPEED)),
			"is_bot": true,
			"goal": "",
			"play_mode": "hub",
			"quest_id": "",
			"linger_until": 0.0,
			"stuck_ticks": 0,
			"home_x": spawn.x,
			"home_z": spawn.z,
			"wander_r": 0.0,
			"ambient": str(b.get("ambient", "")),
			"path": [],
			"waypoint": Vector2.ZERO,
			"has_waypoint": false,
			"admin_level": int(b.get("admin_level", 0)),
			"admin_label": str(b.get("admin_label", "player")),
			"account_login": str(b.get("account_login", "")),
			"out_game_persona": str(b.get("out_game_persona", "")),
			"agent_id": str(b.get("agent_id", "")),
		}
		entities[eid] = ent
		# Goal sans A* au spawn (évite freeze startup) — path au premier step
		_assign_bot_goal(ent, b, false)


func _ensure_hub_npcs() -> void:
	if life != null and life._sched.size() > 0:
		# Spawn Triplons + solos ; ne pas doubler avec HUB_NPCS legacy
		var missing := false
		for eid in life._sched.keys():
			if not entities.has(eid):
				missing = true
				break
		if missing:
			life.spawn_all(entities)
			# Snap walkable
			for eid2 in life._sched.keys():
				if not entities.has(eid2):
					continue
				var e: Dictionary = entities[eid2]
				var p: Vector3 = e["pos"]
				var wz := _walkable_xz(p.x, p.z)
				e["pos"] = Vector3(wz.x, p.y, wz.y)
				e["home_x"] = wz.x
				e["home_z"] = wz.y
		return
	for n in HUB_NPCS:
		var eid: String = str(n["eid"])
		if entities.has(eid):
			continue
		var p: Vector3 = n["pos"]
		var wz := _walkable_xz(p.x, p.z)
		p = Vector3(wz.x, p.y, wz.y)
		var wander := float(n.get("wander_r", 0.0))
		entities[eid] = {
			"eid": eid,
			"oid": int(n["oid"]),
			"kind": "npc",
			"name": str(n["name"]),
			"pos": p,
			"target": Vector3.ZERO,
			"speed": 4.5 if wander > 0.0 else 0.0,
			"is_bot": false,
			"goal": "",
			"play_mode": "",
			"quest_id": "",
			"linger_until": 0.0,
			"stuck_ticks": 0,
			"home_x": p.x,
			"home_z": p.z,
			"wander_r": wander,
			"ambient": str(n.get("ambient", "")),
			"active": true,
		}


func _assign_bot_goal(bot: Dictionary, bdef: Dictionary = {}, with_path: bool = true) -> void:
	if bdef.is_empty():
		bdef = _bot_def(str(bot["eid"]))
	var prefer: Array = bdef.get("prefer", ["plaza", "market"])
	var target: Vector3 = PLAZA
	var goal_id := "plaza"
	var play_mode := "hub"
	var quest_id := ""
	if autonomy != null:
		var g: Dictionary = autonomy.assign_goal(bot, prefer)
		target = g.get("target", PLAZA)
		goal_id = str(g.get("goal_id", "plaza"))
		play_mode = str(g.get("play_mode", "hub"))
		quest_id = str(g.get("quest_id", ""))
	else:
		if prefer.size() > 0:
			goal_id = str(prefer[_rng.randi() % prefer.size()])
		target = POIS.get(goal_id, PLAZA)
	# jitter léger (sauf explore hors murs — garder le point)
	if play_mode == "hub":
		target = Vector3(
			target.x + _rng.randf_range(-8.0, 8.0),
			0.15,
			target.z + _rng.randf_range(-8.0, 8.0)
		)
	var wz := _walkable_xz(target.x, target.z)
	bot["target"] = Vector3(wz.x, 0.15, wz.y)
	bot["goal"] = goal_id
	bot["play_mode"] = play_mode
	bot["quest_id"] = quest_id
	bot["linger_until"] = 0.0
	bot["stuck_ticks"] = 0
	bot["has_waypoint"] = false
	bot["waypoint"] = Vector2.ZERO
	bot["path"] = []
	if with_path and collision != null:
		var pos: Vector3 = bot["pos"]
		var route: Array = collision.find_path(pos.x, pos.z, wz.x, wz.y)
		var path: Array = []
		for i in range(maxi(0, route.size() - 1)):
			path.append(route[i])
		if path.size() > 0:
			bot["waypoint"] = path.pop_front()
			bot["has_waypoint"] = true
			bot["path"] = path
		else:
			bot["path"] = []


func _pick_wander_target(ent: Dictionary) -> Vector3:
	var r := maxf(2.0, float(ent.get("wander_r", 8.0)))
	var ang := _rng.randf() * TAU
	var dist := _rng.randf_range(r * 0.25, r)
	var tx: float = float(ent["home_x"]) + cos(ang) * dist
	var tz: float = float(ent["home_z"]) + sin(ang) * dist
	var wz := _walkable_xz(tx, tz)
	if Vector2(wz.x - float(ent["home_x"]), wz.y - float(ent["home_z"])).length() > r * 1.4:
		wz = _walkable_xz(float(ent["home_x"]), float(ent["home_z"]))
	return Vector3(wz.x, 0.15, wz.y)


func ensure_human(oid: int, player_name: String) -> void:
	_ensure_fleet()
	_ensure_hub_npcs()
	var eid := "player:%d" % oid
	if entities.has(eid):
		entities[eid]["name"] = player_name
		return
	var slot := Vector3(SPAWN_HUMAN.x + float(entities.size() % 5) * 2.0, SPAWN_HUMAN.y, SPAWN_HUMAN.z)
	# Reprise session serveur
	if player_store != null:
		var saved = player_store.get_pos(oid)
		if saved != null:
			slot = saved as Vector3
	var wz := _walkable_xz(slot.x, slot.z)
	slot = Vector3(wz.x, slot.y, wz.y)
	entities[eid] = {
		"eid": eid,
		"oid": oid,
		"kind": "player",
		"name": player_name,
		"pos": slot,
		"target": Vector3.ZERO,
		"speed": 14.0,
		"is_bot": false,
		"goal": "",
		"play_mode": "",
		"quest_id": "",
		"linger_until": 0.0,
		"stuck_ticks": 0,
		"home_x": slot.x,
		"home_z": slot.z,
		"wander_r": 0.0,
		"ambient": "",
	}


func remove_human(oid: int) -> void:
	var eid := "player:%d" % oid
	if entities.has(eid) and player_store != null:
		var p: Vector3 = entities[eid]["pos"]
		player_store.set_pos(oid, p.x, p.y, p.z, str(entities[eid].get("name", "")))
		player_store.save_all()
	entities.erase(eid)
	_greeted_oids.erase(oid)


func set_human_pos(oid: int, x: float, y: float, z: float) -> void:
	var eid := "player:%d" % oid
	if not entities.has(eid):
		return
	if (absf(x) < 50.0 and absf(z) < 50.0) or x < 2500.0 or x > 7500.0:
		return
	var cur: Vector3 = entities[eid]["pos"]
	var clamped: Vector2 = Vector2(x, z)
	if collision != null:
		clamped = collision.clamp_move(cur.x, cur.z, x, z) as Vector2
	entities[eid]["pos"] = Vector3(clamped.x, y, clamped.y)
	if player_store != null:
		player_store.set_pos(oid, clamped.x, y, clamped.y, str(entities[eid].get("name", "")))


func enqueue_say(from_name: String, oid: int, text: String, source: String = "ia") -> void:
	var t := text.strip_edges()
	if t.is_empty():
		return
	if t.length() > 200:
		t = t.substr(0, 200)
	_chat_queue.append({
		"type": "chat",
		"proto": "lbg-ws/2",
		"from": from_name,
		"oid": oid,
		"from_oid": oid,
		"text": t,
		"source": source,
		"server_time_ms": int(Time.get_unix_time_from_system() * 1000.0),
	})


func drain_chat() -> Array:
	if _chat_queue.is_empty():
		return []
	var out := _chat_queue.duplicate()
	_chat_queue.clear()
	return out


func fleet_greet_human(human_name: String, human_oid: int) -> void:
	if _greeted_oids.has(human_oid):
		return
	_greeted_oids[human_oid] = true
	_ensure_fleet()
	var who := human_name.strip_edges()
	if who.is_empty():
		who = "Voyageur"
	for b in bot_defs:
		var bot = entities.get(str(b["eid"]))
		if bot == null:
			continue
		var line := str(b.get("greet", "Salut {who}.")).replace("{who}", who)
		enqueue_say(str(b["name"]), int(bot["oid"]), line, "ia")


func _humans() -> Array:
	var out: Array = []
	for eid in entities.keys():
		var e: Dictionary = entities[eid]
		if str(e.get("kind", "")) == "player" and not bool(e.get("is_bot", false)):
			out.append(e)
	return out


func _maybe_ambient() -> void:
	var now := Time.get_unix_time_from_system()
	var humans := _humans()
	if humans.is_empty():
		return
	for b in bot_defs:
		var eid: String = str(b["eid"])
		var bot = entities.get(eid)
		if bot == null:
			continue
		# Flotte : pas d'annonce de POI / aller-retour — ambient rare, hors goal.
		var last := float(_last_ambient.get(eid, 0.0))
		if now - last < 180.0 + float(hash(eid) % 90):
			continue
		var near = null
		var bp: Vector3 = bot["pos"]
		for h in humans:
			var hp: Vector3 = h["pos"]
			if Vector2(hp.x - bp.x, hp.z - bp.z).length() <= 28.0:
				near = h
				break
		if near == null:
			continue
		_last_ambient[eid] = now
		var line := str(b.get("ambient", "")).replace("{who}", str(near["name"])).strip_edges()
		if line.is_empty():
			continue
		enqueue_say(str(b["name"]), int(bot["oid"]), line, "ia")

	for eid in entities.keys():
		var e: Dictionary = entities[eid]
		if str(e.get("kind", "")) != "npc":
			continue
		if not bool(e.get("active", true)):
			continue
		var amb := str(e.get("ambient", ""))
		if amb.is_empty():
			continue
		var last2 := float(_last_ambient.get(eid, 0.0))
		if now - last2 < 70.0 + float(int(e["oid"]) % 25):
			continue
		var near2 = null
		var ep: Vector3 = e["pos"]
		for h2 in humans:
			var hp2: Vector3 = h2["pos"]
			if Vector2(hp2.x - ep.x, hp2.z - ep.z).length() <= 22.0:
				near2 = h2
				break
		if near2 == null:
			continue
		_last_ambient[eid] = now
		enqueue_say(str(e["name"]), int(e["oid"]), amb, "ia")


func _step_bot(bot: Dictionary, dt: float) -> void:
	var now := Time.get_unix_time_from_system()
	if float(bot.get("linger_until", 0.0)) > now:
		return
	var target: Vector3 = bot["target"]
	if target == Vector3.ZERO:
		_assign_bot_goal(bot)
		target = bot["target"]
	var pos: Vector3 = bot["pos"]

	# Suivre waypoint A* si présent
	var steer := target
	if bool(bot.get("has_waypoint", false)):
		var wp: Vector2 = bot["waypoint"]
		if Vector2(wp.x - pos.x, wp.y - pos.z).length() < 4.0:
			var path: Array = bot.get("path", [])
			if path.size() > 0:
				bot["waypoint"] = path.pop_front()
				bot["path"] = path
				wp = bot["waypoint"]
			else:
				bot["has_waypoint"] = false
		if bool(bot.get("has_waypoint", false)):
			steer = Vector3(wp.x, pos.y, wp.y)

	var dx := steer.x - pos.x
	var dz := steer.z - pos.z
	var dist := sqrt(dx * dx + dz * dz)
	# Arrivée finale seulement sans waypoint restant
	if not bool(bot.get("has_waypoint", false)) and dist < 4.0:
		if autonomy != null:
			autonomy.on_arrival(bot)
		bot["linger_until"] = now + _rng.randf_range(3.0, 7.0)
		# Pas de « j'y suis / vers X » — les allers-retours ne polluent pas le chat
		_assign_bot_goal(bot)
		return
	if dist < 1e-6:
		return
	var speed: float = float(bot.get("speed", BOT_SPEED))
	var step_len := minf(dist, speed * dt)
	var nx := pos.x + (dx / dist) * step_len
	var nz := pos.z + (dz / dist) * step_len
	if collision != null:
		var c: Vector2 = collision.clamp_move(pos.x, pos.z, nx, nz) as Vector2
		nx = c.x
		nz = c.y
	var moved := Vector2(nx - pos.x, nz - pos.z).length()
	if moved < step_len * 0.15:
		bot["stuck_ticks"] = int(bot.get("stuck_ticks", 0)) + 1
		if int(bot["stuck_ticks"]) >= 6 and collision != null:
			var final: Vector3 = bot["target"]
			var route: Array = collision.find_path(pos.x, pos.z, final.x, final.z)
			var path2: Array = []
			for i in range(maxi(0, route.size() - 1)):
				path2.append(route[i])
			bot["path"] = path2
			if path2.size() > 0:
				bot["waypoint"] = path2.pop_front()
				bot["has_waypoint"] = true
				bot["path"] = path2
			else:
				var detour = collision.detour_waypoint(pos.x, pos.z, final.x, final.z)
				if detour != null:
					bot["waypoint"] = detour
					bot["has_waypoint"] = true
			bot["stuck_ticks"] = 0
		elif int(bot["stuck_ticks"]) >= 12:
			_assign_bot_goal(bot)
			bot["stuck_ticks"] = 0
	else:
		bot["stuck_ticks"] = 0
	bot["pos"] = Vector3(nx, pos.y, nz)


func _step_npc(npc: Dictionary, dt: float) -> void:
	if not bool(npc.get("active", true)):
		return
	var wander := float(npc.get("wander_r", 0.0))
	var speed: float = float(npc.get("speed", 0.0))
	if wander <= 0.0 or speed <= 0.0:
		return
	var target: Vector3 = npc["target"]
	if target == Vector3.ZERO:
		npc["target"] = _pick_wander_target(npc)
		target = npc["target"]
	var pos: Vector3 = npc["pos"]
	var dx := target.x - pos.x
	var dz := target.z - pos.z
	var dist := sqrt(dx * dx + dz * dz)
	if dist < 1.5:
		# Arrivé au poste / loisir : déambuler localement
		npc["target"] = _pick_wander_target(npc)
		npc["stuck_ticks"] = 0
		return
	var step_len := minf(dist, speed * dt)
	var nx := pos.x + (dx / dist) * step_len
	var nz := pos.z + (dz / dist) * step_len
	if collision != null:
		var c: Vector2 = collision.clamp_move(pos.x, pos.z, nx, nz) as Vector2
		nx = c.x
		nz = c.y
	var moved := Vector2(nx - pos.x, nz - pos.z).length()
	if moved < step_len * 0.15:
		npc["stuck_ticks"] = int(npc.get("stuck_ticks", 0)) + 1
		if int(npc["stuck_ticks"]) >= 5:
			var home := _walkable_xz(float(npc["home_x"]), float(npc["home_z"]))
			npc["pos"] = Vector3(home.x, pos.y, home.y)
			npc["target"] = _pick_wander_target(npc)
			npc["stuck_ticks"] = 0
			return
	else:
		npc["stuck_ticks"] = 0
	npc["pos"] = Vector3(nx, pos.y, nz)


func step(dt: float) -> void:
	_ensure_fleet()
	_ensure_hub_npcs()
	tick += 1
	dt = clampf(dt, 0.001, 0.25)
	if life != null and tick % _life_tick_every == 0:
		life.tick_life(entities, Time.get_unix_time_from_system())
	for eid in entities.keys():
		var e: Dictionary = entities[eid]
		if bool(e.get("is_bot", false)):
			_step_bot(e, dt)
		elif str(e.get("kind", "")) == "npc":
			_step_npc(e, dt)
	if tick % 40 == 0:
		_maybe_ambient()
	if tick % _persist_every_ticks == 0 and player_store != null:
		for eid2 in entities.keys():
			var h: Dictionary = entities[eid2]
			if str(h.get("kind", "")) == "player" and not bool(h.get("is_bot", false)):
				var hp: Vector3 = h["pos"]
				player_store.set_pos(int(h["oid"]), hp.x, hp.y, hp.z, str(h.get("name", "")))
		player_store.save_all()


func entity_list() -> Array:
	var out: Array = []
	for eid in entities.keys():
		var e: Dictionary = entities[eid]
		# Repos Triplon : hors zone_state (≈ ⅓ off)
		if str(e.get("kind", "")) == "npc" and not bool(e.get("active", true)):
			continue
		var p: Vector3 = e["pos"]
		out.append({
			"id": int(e["oid"]),
			"entity_key": str(e["eid"]),
			"kind": str(e["kind"]),
			"name": str(e["name"]),
			"pos": [p.x, p.y, p.z],
			"source": "prime_hub",
			"goal": str(e.get("goal", "")),
			"play_mode": str(e.get("play_mode", "")),
			"quest_id": str(e.get("quest_id", "")),
			"is_bot": bool(e.get("is_bot", false)),
			"life_phase": str(e.get("life_phase", "")),
		})
	return out


func bots_payload() -> Array:
	var out: Array = []
	for eid in entities.keys():
		var e: Dictionary = entities[eid]
		if not bool(e.get("is_bot", false)):
			continue
		var p: Vector3 = e["pos"]
		var t: Vector3 = e["target"]
		out.append({
			"id": int(e["oid"]),
			"entity_key": str(e["eid"]),
			"name": str(e["name"]),
			"pos": [p.x, p.y, p.z],
			"target": [t.x, t.y, t.z],
			"goal": str(e.get("goal", "")),
			"play_mode": str(e.get("play_mode", "")),
			"quest_id": str(e.get("quest_id", "")),
			"admin_level": int(e.get("admin_level", 0)),
			"account_login": str(e.get("account_login", "")),
			"agent_id": str(e.get("agent_id", "")),
		})
	return out


func set_bot_target(player: String, x: float, y: float, z: float) -> Variant:
	## Dictionary entité ou null
	var want := player.strip_edges().to_lower()
	for eid in entities.keys():
		var e: Dictionary = entities[eid]
		if not bool(e.get("is_bot", false)):
			continue
		if str(e.get("name", "")).to_lower() != want:
			continue
		# Anneau LH : bornes explore (pas Scrapaltai entière / pas Zalem)
		if autonomy != null and autonomy.has_method("clamp_xz"):
			var ring: Vector2 = autonomy.clamp_xz(x, z)
			x = ring.x
			z = ring.y
		var wz := _walkable_xz(x, z)
		e["target"] = Vector3(wz.x, y, wz.y)
		e["goal"] = "http_move_to"
		e["play_mode"] = "explore"
		return e
	return null


func online_players() -> Array:
	var out: Array = []
	for eid in entities.keys():
		var e: Dictionary = entities[eid]
		if str(e.get("kind", "")) != "player" or bool(e.get("is_bot", false)):
			continue
		out.append({"id": int(e["oid"]), "name": str(e["name"])})
	return out


func bot_count() -> int:
	var n := 0
	for eid in entities.keys():
		if bool(entities[eid].get("is_bot", false)):
			n += 1
	return n


func npc_count() -> int:
	var n := 0
	for eid in entities.keys():
		var e: Dictionary = entities[eid]
		if str(e.get("kind", "")) == "npc" and bool(e.get("active", true)):
			n += 1
	return n


func life_stats() -> Dictionary:
	if life == null:
		return {}
	return life.stats()


func zone_state_payload(your_oid: int) -> Dictionary:
	var online := online_players()
	var payload := {
		"type": "zone_state",
		"proto": "lbg-ws/2",
		"zone": ZONE,
		"tick": tick,
		"server_time_ms": int(Time.get_unix_time_from_system() * 1000.0),
		"entities": entity_list(),
		"your_character_id": your_oid,
		"session_policy": "prime_hub_g4u",
		"collision_blocks": collision.blocks.size() if collision else 0,
		"online_players": online,
		"online_count": online.size(),
		"bots": bots_payload(),
		"bot_count": bot_count(),
		"npc_count": npc_count(),
	}
	var eid := "player:%d" % your_oid
	if entities.has(eid):
		var p: Vector3 = entities[eid]["pos"]
		payload["position"] = [p.x, p.y, p.z]
	return payload


func enter_world_payload(your_oid: int) -> Dictionary:
	ensure_human(your_oid, "Voyageur")
	var base := zone_state_payload(your_oid)
	base["type"] = "enter_world"
	var eid := "player:%d" % your_oid
	if entities.has(eid):
		var p: Vector3 = entities[eid]["pos"]
		base["position"] = [p.x, p.y, p.z]
	return base
