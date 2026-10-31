extends Node
## Sim hub G5+ — flotte autonome + Triplons (work/leisure/rest) + chat sobre.
## Découpage modulaire Ticket 2.2 : HubCombat, HubPresence, HubSimViews, HubSimAmbient, HubSimDefs.

const HubCollisionScript = preload("res://scripts/hub_collision.gd")
const HubNavScript = preload("res://scripts/hub_nav.gd")
const HubPlayerStoreScript = preload("res://scripts/hub_player_store.gd")
const HubLifeScript = preload("res://scripts/hub_life.gd")
const HubBotAutonomyScript = preload("res://scripts/hub_bot_autonomy.gd")
const HubWorldSuggestScript = preload("res://scripts/hub_world_suggest.gd")
const HubAgentApiScript = preload("res://scripts/hub_agent_api.gd")
const HubCombatScript = preload("res://scripts/hub_combat.gd")
const HubPresenceScript = preload("res://scripts/hub_presence.gd")
const HubSimViewsScript = preload("res://scripts/hub_sim_views.gd")
const HubSimAmbientScript = preload("res://scripts/hub_sim_ambient.gd")
const HubSimDefsScript = preload("res://scripts/hub_sim_defs.gd")
const HubEscortScript = preload("res://scripts/hub_escort.gd")
const HubShowScript = preload("res://scripts/hub_show.gd")
const _HubPaths = preload("res://scripts/hub_paths.gd")

const HUMAN_OID := HubSimDefsScript.HUMAN_OID
const ZONE := HubSimDefsScript.ZONE
const SPAWN_HUMAN := HubSimDefsScript.SPAWN_HUMAN
const PLAZA := HubSimDefsScript.PLAZA
const MARKET := HubSimDefsScript.MARKET
const BOT_SPEED := HubSimDefsScript.BOT_SPEED
const POIS: Dictionary = HubSimDefsScript.POIS
const BOT_DEFS_FALLBACK: Array = HubSimDefsScript.BOT_DEFS_FALLBACK
const HUB_NPCS: Array = HubSimDefsScript.HUB_NPCS

var collision = null
var nav = null
var player_store = null
var life = null
var autonomy = null
var suggest = null
var economy = null
var agent_api = null
var events = null
var world_stream = null
var combat = null
var presence = null
var ambient = null
var escort = null
var show = null

var bot_defs: Array = []
var tick: int = 0
var entities: Dictionary = {}
var _rng := RandomNumberGenerator.new()
var _persist_every_ticks: int = 100  # ~5 s @ 20 Hz
var _life_tick_every: int = 20  # ~1 s


func attach_economy(economy_svc) -> void:
	economy = economy_svc
	if autonomy != null:
		autonomy.economy = economy_svc


func attach_events(events_svc) -> void:
	events = events_svc
	if autonomy != null:
		autonomy.events = events_svc


func attach_world_stream(stream_svc) -> void:
	world_stream = stream_svc


func _stream(kind: String, text: String, actor: String = "", zone: String = "", detail: Dictionary = {}) -> void:
	## Plan 3.1 — émet un événement monde léger (no-op si stream absent).
	if world_stream != null and world_stream.has_method("emit"):
		world_stream.emit(kind, text, actor, zone, detail)


func reset() -> void:
	tick = 0
	entities.clear()
	_rng.randomize()
	if collision == null:
		collision = HubCollisionScript.new()
	collision.reload()
	if nav == null:
		nav = HubNavScript.new()
		nav.build(collision)
	if player_store == null:
		player_store = HubPlayerStoreScript.new()
		player_store.setup()
	if suggest == null:
		suggest = HubWorldSuggestScript.new()
		suggest.setup()
	if agent_api == null:
		agent_api = HubAgentApiScript.new()
	agent_api.setup()
	if presence == null:
		presence = HubPresenceScript.new()
	presence.load_presence_dials()
	if ambient == null:
		ambient = HubSimAmbientScript.new()
	ambient.setup(self)
	ambient.clear()
	if combat == null:
		combat = HubCombatScript.new()
	combat.setup(self)
	if escort == null:
		escort = HubEscortScript.new()
	escort.clear()
	if show == null:
		show = HubShowScript.new()
	show.clear()
	show.bootstrap(self)
	_load_bot_defs()
	if life == null:
		life = HubLifeScript.new()
	life.setup(POIS, collision)
	if autonomy == null:
		autonomy = HubBotAutonomyScript.new()
	autonomy.setup(economy, suggest, POIS, events)
	_ensure_fleet()
	_ensure_hub_npcs()
	if combat != null:
		combat.ensure_density_beasts()


func _load_presence_dials() -> void:
	if presence != null:
		presence.load_presence_dials()


func _dials_for_persona(name: String) -> Dictionary:
	if presence != null:
		return presence.dials_for_persona(name)
	return {"chaleur": 0.45, "humeur": 0.4, "humour": 0.3, "initiative": 0.4}


func presence_line_for(bot: Dictionary, who: String) -> String:
	if presence != null:
		return presence.presence_line_for(bot, who)
	return ""


func presence_resolve_action(bot: Dictionary, distance_m: float) -> Dictionary:
	if presence != null:
		return presence.presence_resolve_action(bot, distance_m)
	return {"action": "ambient", "reason": "default"}


func presence_dials_payload() -> Dictionary:
	if presence != null:
		return presence.presence_dials_payload(bot_defs)
	return {"ok": false}


func _load_bot_defs() -> void:
	bot_defs.clear()
	_load_presence_dials()
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
		for i in range(bot_defs.size()):
			var fb: Dictionary = bot_defs[i]
			fb["presence_dials"] = _dials_for_persona(str(fb.get("name", "")))
			bot_defs[i] = fb


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
	var ls = og.get("linked_studio", {})
	if typeof(ls) != TYPE_DICTIONARY:
		ls = {}
	var nm := str(p.get("name", "Bot"))
	var dials := _dials_for_persona(nm)
	var inline = p.get("presence_dials", null)
	if typeof(inline) == TYPE_DICTIONARY:
		for dk in ["chaleur", "humeur", "humour", "initiative"]:
			if inline.has(dk):
				dials[dk] = clampf(float(inline[dk]), 0.0, 1.0)
	return {
		"eid": str(p.get("eid", "player:%s" % nm)),
		"oid": int(p.get("oid", 900000)),
		"name": nm,
		"spawn": spawn_v,
		"speed": float(p.get("speed", BOT_SPEED)),
		"prefer": prefer,
		"greet": str(p.get("greet", "")),
		"ambient": str(p.get("ambient", "")),
		"playstyle": str(p.get("playstyle", "")),
		"admin_level": int(p.get("admin_level", 0)),
		"admin_label": str(p.get("admin_label", "player")),
		"account_login": str(p.get("account_login", og.get("persona", ""))),
		"account_login_legacy": str(p.get("account_login_legacy", "")),
		"out_game_persona": str(og.get("persona", "")),
		"agent_id": str(og.get("agent_id", "")),
		"linked_studio_agent_id": str(ls.get("agent_id", "")),
		"linked_studio_display": str(ls.get("display_name", "")),
		"presence_dials": dials,
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
			"linked_studio_agent_id": str(b.get("linked_studio_agent_id", "")),
			"linked_studio_display": str(b.get("linked_studio_display", "")),
			"presence_dials": (b.get("presence_dials", {}) as Dictionary).duplicate(true),
		}
		entities[eid] = ent
		_assign_bot_goal(ent, b, false)


func _ensure_hub_npcs() -> void:
	if life != null and life._sched.size() > 0:
		var missing := false
		for eid in life._sched.keys():
			if not entities.has(eid):
				missing = true
				break
		if missing:
			life.spawn_all(entities)
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
	var now_sec := float(Time.get_ticks_msec()) * 0.001
	if float(bot.get("linger_until", 0.0)) <= now_sec:
		bot["linger_until"] = 0.0
	bot["stuck_ticks"] = 0
	bot["has_waypoint"] = false
	bot["waypoint"] = Vector2.ZERO
	bot["path"] = []
	bot["needs_path"] = true
	if with_path and collision != null:
		_apply_path_to_bot(bot, wz.x, wz.y)


func _nav_path(sx: float, sz: float, tx: float, tz: float) -> Array:
	if nav != null and nav.ready_ok:
		var route: Array = nav.find_path(sx, sz, tx, tz)
		if not route.is_empty():
			return route
	if collision != null:
		return collision.find_path(sx, sz, tx, tz)
	return []


func _apply_path_to_bot(bot: Dictionary, tx: float, tz: float) -> void:
	if collision == null and (nav == null or not nav.ready_ok):
		return
	var pos: Vector3 = bot["pos"]
	var route: Array = _nav_path(pos.x, pos.z, tx, tz)
	var path: Array = []
	for i in range(route.size()):
		var wp: Vector2 = route[i]
		if i == 0 and Vector2(wp.x - pos.x, wp.y - pos.z).length() < 2.5:
			continue
		if Vector2(wp.x - tx, wp.y - tz).length() < 1.5:
			continue
		path.append(wp)
	if path.size() > 0:
		bot["waypoint"] = path.pop_front()
		bot["has_waypoint"] = true
		bot["path"] = path
	else:
		bot["path"] = []
		bot["has_waypoint"] = false
	bot["needs_path"] = false


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
	if ambient != null:
		ambient.remove_human(oid)


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
	if ambient != null:
		ambient.enqueue_say(from_name, oid, text, source)


func drain_chat() -> Array:
	if ambient != null:
		return ambient.drain_chat()
	return []


func fleet_greet_human(human_name: String, human_oid: int) -> void:
	if ambient != null:
		ambient.fleet_greet_human(human_name, human_oid)


func start_companion_escort_for(player_name: String, duration_s: float = 28.0) -> Dictionary:
	## Hotbar « Compagnon » — Nix/Lia escorte le joueur un moment.
	if ambient == null:
		return {"ok": false, "error": "ambient_unavailable"}
	var companion: Dictionary = ambient.pick_companion_bot()
	if companion.is_empty():
		return {"ok": false, "error": "no_companion", "hint": "Aucun bot compagnon en flotte"}
	# Assure un humain suivable (oid synthétique si hors WS).
	var want := player_name.strip_edges()
	var found_oid := 0
	for eid in entities.keys():
		var e: Dictionary = entities[eid]
		if str(e.get("kind", "")) == "player" and not bool(e.get("is_bot", false)):
			if str(e.get("name", "")).strip_edges().to_lower() == want.to_lower():
				found_oid = int(e.get("oid", 0))
				break
	if found_oid == 0:
		found_oid = HUMAN_OID
		ensure_human(found_oid, want if want != "" else "Voyageur")
	ambient.start_companion_escort(companion, duration_s)
	var cname := str(companion.get("name", "Nix"))
	_stream("companion.escort", "%s escorte %s." % [cname, want], cname, "hub")
	return {
		"ok": true,
		"companion": cname,
		"duration_s": maxf(8.0, duration_s),
		"message": "%s te suit un moment — reste à proximité." % cname,
		"source": "prime_hub",
	}


func _step_bot(bot: Dictionary, dt: float) -> void:
	var now := Time.get_unix_time_from_system()
	var escort_until := float(bot.get("_escort_until", 0.0))
	var escorting := escort_until > now
	if escorting:
		var humans := HubSimViewsScript.online_players(entities)
		if not humans.is_empty():
			var first_human = entities.get("player:%d" % int(humans[0]["id"]))
			if first_human != null:
				var hp: Vector3 = first_human["pos"]
				var wz := _walkable_xz(hp.x + 5.0, hp.z + 3.0)
				bot["target"] = Vector3(wz.x, hp.y, wz.y)
				bot["goal"] = "companion_escort"
				bot["linger_until"] = 0.0
	elif str(bot.get("goal", "")) == "companion_escort":
		bot.erase("_escort_until")
		_assign_bot_goal(bot)
	elif events != null and events.has_method("is_weather_shelter_active") and events.is_weather_shelter_active() and str(bot.get("play_mode", "")) != "shelter":
		# Réflexe immédiat : repli d'urgence vers un bâtiment abrité
		_assign_bot_goal(bot)
	elif events != null and events.has_method("is_weather_shelter_active") and not events.is_weather_shelter_active() and str(bot.get("play_mode", "")) == "shelter":
		# Fin de la tempête : reprise du cours normal des activités
		_assign_bot_goal(bot)
	if float(bot.get("linger_until", 0.0)) > now:
		return
	var target: Vector3 = bot["target"]
	if target == Vector3.ZERO:
		_assign_bot_goal(bot)
		target = bot["target"]
	var pos: Vector3 = bot["pos"]
	if bool(bot.get("needs_path", false)):
		_apply_path_to_bot(bot, target.x, target.z)

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
	if not bool(bot.get("has_waypoint", false)) and dist < 4.0:
		if escorting:
			bot["linger_until"] = now + 1.2
			return
		if events != null and events.has_method("is_weather_shelter_active") and events.is_weather_shelter_active():
			# Reste à l'abri tant que la tempête souffle !
			bot["linger_until"] = now + 10.0
			return
		if autonomy != null:
			autonomy.on_arrival(bot)
		bot["linger_until"] = now + _rng.randf_range(3.0, 7.0)
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
		var st := int(bot.get("stuck_ticks", 0)) + 1
		bot["stuck_ticks"] = st
		if st == 6 and collision != null:
			var final: Vector3 = bot["target"]
			_apply_path_to_bot(bot, final.x, final.z)
			if not bool(bot.get("has_waypoint", false)):
				var detour = collision.detour_waypoint(pos.x, pos.z, final.x, final.z)
				if detour != null:
					bot["waypoint"] = detour
					bot["has_waypoint"] = true
		elif st >= 12:
			bot["has_waypoint"] = false
			bot["path"] = []
			if collision != null:
				var free_spot: Vector2 = collision.nearest_walkable(pos.x, pos.z, 20.0)
				bot["pos"] = Vector3(free_spot.x, pos.y, free_spot.y)
				pos = bot["pos"]
				nx = pos.x
				nz = pos.z
			_assign_bot_goal(bot)
			bot["stuck_ticks"] = 0
	else:
		bot["stuck_ticks"] = 0
	bot["pos"] = Vector3(nx, pos.y, nz)


func _finalize_npc_rest(npc: Dictionary) -> void:
	var home := _walkable_xz(float(npc.get("home_x", npc["pos"].x)), float(npc.get("home_z", npc["pos"].z)))
	npc["pos"] = Vector3(home.x, float(npc["pos"].y), home.y)
	npc["target"] = Vector3.ZERO
	npc["speed"] = 0.0
	npc["active"] = false
	npc["wander_r"] = 0.0
	npc["_rest_commute"] = false
	npc["goal"] = "rest"
	npc["stuck_ticks"] = 0


func _step_npc(npc: Dictionary, dt: float) -> void:
	if not bool(npc.get("active", true)):
		return
	var speed: float = float(npc.get("speed", 0.0))
	if speed <= 0.0:
		return
	var rest_home := str(npc.get("goal", "")) == "rest_home" or bool(npc.get("_rest_commute", false))
	var wander := float(npc.get("wander_r", 0.0))
	if not rest_home and wander <= 0.0:
		return
	var target: Vector3 = npc["target"]
	if target == Vector3.ZERO:
		if rest_home:
			target = Vector3(float(npc.get("home_x", 0.0)), 0.15, float(npc.get("home_z", 0.0)))
			npc["target"] = target
		else:
			npc["target"] = _pick_wander_target(npc)
			target = npc["target"]
	var pos: Vector3 = npc["pos"]
	var dx := target.x - pos.x
	var dz := target.z - pos.z
	var dist := sqrt(dx * dx + dz * dz)
	if dist < (2.8 if rest_home else 1.5):
		if rest_home:
			_finalize_npc_rest(npc)
			return
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
			if rest_home:
				_finalize_npc_rest(npc)
				return
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
	if combat != null:
		combat.ensure_density_beasts()
		combat.revive_density_beasts()
	tick += 1
	dt = clampf(dt, 0.001, 0.25)
	if events != null and tick % _life_tick_every == 0 and events.has_method("tick"):
		events.tick(Time.get_unix_time_from_system())
	if life != null and tick % _life_tick_every == 0:
		life.tick_life(entities, Time.get_unix_time_from_system())
	for eid in entities.keys():
		var e: Dictionary = entities[eid]
		if bool(e.get("is_bot", false)):
			_step_bot(e, dt)
		elif str(e.get("kind", "")) == "beast":
			if combat != null:
				combat.step_beast(e, dt)
		elif str(e.get("kind", "")) == "npc":
			# Escorte / show : mouvement géré par modules dédiés.
			var g := str(e.get("goal", ""))
			if g.begins_with("escort_") or g.begins_with("show_"):
				continue
			_step_npc(e, dt)
	if escort != null:
		escort.tick(self, dt, economy)
	if show != null:
		show.tick(self, dt)
	if tick % 40 == 0 and ambient != null:
		ambient.maybe_ambient()
	if tick % _persist_every_ticks == 0 and player_store != null:
		for eid2 in entities.keys():
			var h: Dictionary = entities[eid2]
			if str(h.get("kind", "")) == "player" and not bool(h.get("is_bot", false)):
				var hp: Vector3 = h["pos"]
				player_store.set_pos(int(h["oid"]), hp.x, hp.y, hp.z, str(h.get("name", "")))
		player_store.save_all()


func entity_list(slim: bool = false) -> Array:
	return HubSimViewsScript.entity_list(entities, slim)


func bots_payload() -> Array:
	return HubSimViewsScript.bots_payload(entities)


func set_bot_target(player: String, x: float, y: float, z: float) -> Variant:
	var want := player.strip_edges().to_lower()
	for eid in entities.keys():
		var e: Dictionary = entities[eid]
		if not bool(e.get("is_bot", false)):
			continue
		if str(e.get("name", "")).to_lower() != want:
			continue
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
	return HubSimViewsScript.online_players(entities)


func bot_count() -> int:
	return HubSimViewsScript.bot_count(entities)


func npc_count() -> int:
	return HubSimViewsScript.npc_count(entities)


func beast_count() -> int:
	if combat != null:
		return combat.beast_count()
	return 0


func navmesh_stats() -> Dictionary:
	if nav == null:
		return {"ok": false, "reason": "nav_absent"}
	return nav.stats()


func persistence_stats() -> Dictionary:
	if player_store == null:
		return {"ok": false, "reason": "player_store_absent"}
	return player_store.stats()


func nav_probe(sx: float, sz: float, tx: float, tz: float) -> Dictionary:
	if nav == null or not nav.ready_ok:
		return {"ok": false, "error": "navmesh_unavailable"}
	var route: Array = _nav_path(sx, sz, tx, tz)
	var waypoints: Array = []
	for p in route:
		waypoints.append([snappedf(p.x, 0.1), snappedf(p.y, 0.1)])
	return {
		"ok": not route.is_empty(),
		"engine": "NavigationServer3D",
		"source": "navmesh" if (nav.ready_ok and nav.in_bounds(sx, sz) and nav.in_bounds(tx, tz)) else "grid_fallback",
		"from": [sx, sz],
		"to": [tx, tz],
		"waypoints": waypoints,
		"count": waypoints.size(),
		"last_query_us": nav.last_query_us,
	}


func beasts_snapshot() -> Dictionary:
	if combat != null:
		return combat.beasts_snapshot()
	return {"ok": true, "count": 0, "beasts": [], "source": "prime_hub", "ticket": "P5b"}


func force_beast_telegraph(x: float, z: float, radius_m: float = 120.0, bosses_only: bool = true) -> Dictionary:
	if combat != null:
		return combat.force_beast_telegraph(x, z, radius_m, bosses_only)
	return {"ok": false, "error": "combat_unavailable"}


func engage_nearest_beast(player: String, x: float, z: float, radius_m: float = 42.0) -> Dictionary:
	if combat != null:
		return combat.engage_nearest_beast(player, x, z, radius_m)
	return {"ok": false, "error": "combat_unavailable"}


func life_stats() -> Dictionary:
	if life == null:
		return {}
	return life.stats()


func zone_state_payload(your_oid: int) -> Dictionary:
	return HubSimViewsScript.zone_state_payload(self, your_oid)


func enter_world_payload(your_oid: int) -> Dictionary:
	return HubSimViewsScript.enter_world_payload(self, your_oid)
