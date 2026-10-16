extends RefCounted
class_name HubBotAutonomy
## Flotte IA : choix quête / explore (anneau LH) / hub + suggestions monde occasionnelles.

const _HubPaths = preload("res://scripts/hub_paths.gd")

## Fallback si explore_ring_lh.json absent
const EXPLORE_FALLBACK: Dictionary = {
	"gate_east": {"label": "explorer porte est / dunes", "pos": Vector3(5813.6, 0.15, -982.5)},
	"gate_west": {"label": "surveiller porte ouest Zalem", "pos": Vector3(3688.9, 0.15, -675.9)},
	"hunt": {"label": "reconnaître hors murs", "pos": Vector3(5985.0, 0.15, -1120.0)},
	"spawn_apron": {"label": "repasser au shuttleport", "pos": Vector3(4749.0, 0.15, -537.0)},
}

const RING_CENTER_FALLBACK := Vector3(4749.0, 0.15, -737.0)
const RING_RADIUS_FALLBACK := 9500.0
const OUTPOST_ZALEM_CENTER := Vector3(-1200.0, 0.15, -550.0)
const OUTPOST_KSAR_CENTER := Vector3(4950.0, 0.15, -3800.0)

var personas: Dictionary = {}
var economy = null
var suggest = null
var pois: Dictionary = {}
var explore: Dictionary = {}
var ring_center: Vector3 = RING_CENTER_FALLBACK
var ring_radius_m: float = RING_RADIUS_FALLBACK
var random_sample_chance: float = 0.28
var _rng := RandomNumberGenerator.new()
var _last_suggest: Dictionary = {}  # name -> unix
var _quest_cd: Dictionary = {}


func setup(economy_svc, suggest_svc, poi_map: Dictionary) -> void:
	economy = economy_svc
	suggest = suggest_svc
	pois = poi_map
	_rng.randomize()
	_load_explore_ring()
	personas.clear()
	# Source primaire : ai_players.json (personas inline) ; fallback bot_personas.json
	var fleet: Variant = _HubPaths.read_json(_HubPaths.data_file("life/ai_players.json"))
	if typeof(fleet) == TYPE_DICTIONARY:
		var arr = fleet.get("players", [])
		if typeof(arr) == TYPE_ARRAY:
			for p in arr:
				if typeof(p) != TYPE_DICTIONARY:
					continue
				var nm := str(p.get("name", ""))
				if nm.is_empty():
					continue
				var og = p.get("out_game", {})
				if typeof(og) != TYPE_DICTIONARY:
					og = {}
				personas[nm] = {
					"short": str(p.get("short", "")),
					"medium": str(p.get("medium", "")),
					"long": str(p.get("long", "")),
					"quest_prefer": p.get("quest_prefer", []),
					"explore_prefer": p.get("explore_prefer", []),
					"suggest_kinds": p.get("suggest_kinds", ["poi"]),
					"playstyle": str(p.get("playstyle", "")),
					"admin_level": int(p.get("admin_level", 0)),
					"account_login": str(p.get("account_login", "")),
					"agent_id": str(og.get("agent_id", "")),
				}
	if personas.is_empty():
		var raw: Variant = _HubPaths.read_json(_HubPaths.data_file("life/bot_personas.json"))
		if typeof(raw) == TYPE_DICTIONARY:
			var bots = raw.get("bots", {})
			if typeof(bots) == TYPE_DICTIONARY:
				personas = bots


func _load_explore_ring() -> void:
	explore = EXPLORE_FALLBACK.duplicate(true)
	ring_center = RING_CENTER_FALLBACK
	ring_radius_m = RING_RADIUS_FALLBACK
	random_sample_chance = 0.28
	var raw: Variant = _HubPaths.read_json(_HubPaths.data_file("life/explore_ring_lh.json"))
	if typeof(raw) != TYPE_DICTIONARY:
		return
	var c = raw.get("center", {})
	if typeof(c) == TYPE_DICTIONARY:
		ring_center = Vector3(float(c.get("x", ring_center.x)), float(c.get("y", 0.15)), float(c.get("z", ring_center.z)))
	ring_radius_m = maxf(200.0, float(raw.get("max_radius_m", ring_radius_m)))
	random_sample_chance = clampf(float(raw.get("random_sample_chance", random_sample_chance)), 0.0, 1.0)
	var wps = raw.get("waypoints", {})
	if typeof(wps) != TYPE_DICTIONARY:
		return
	for id in wps.keys():
		var spot = wps[id]
		if typeof(spot) != TYPE_DICTIONARY:
			continue
		var p = spot.get("pos", {})
		if typeof(p) != TYPE_DICTIONARY:
			continue
		var pos := Vector3(float(p.get("x", 0.0)), float(p.get("y", 0.15)), float(p.get("z", 0.0)))
		pos = clamp_pos(pos)
		explore[str(id)] = {
			"label": str(spot.get("label", id)),
			"pos": pos,
		}


func clamp_xz(x: float, z: float) -> Vector2:
	var dx := x - ring_center.x
	var dz := z - ring_center.z
	var d := sqrt(dx * dx + dz * dz)
	if d <= ring_radius_m or d < 1e-6:
		return Vector2(x, z)
	var s := ring_radius_m / d
	return Vector2(ring_center.x + dx * s, ring_center.z + dz * s)


func clamp_pos(pos: Vector3) -> Vector3:
	var xz := clamp_xz(pos.x, pos.z)
	return Vector3(xz.x, pos.y, xz.y)


func in_ring(x: float, z: float) -> bool:
	var dx := x - ring_center.x
	var dz := z - ring_center.z
	return sqrt(dx * dx + dz * dz) <= ring_radius_m + 0.5


func assign_goal(bot: Dictionary, prefer: Array = []) -> Dictionary:
	## Retourne {target: Vector3, goal_id, goal_label, play_mode, quest_id, maybe_suggest?}
	var name := str(bot.get("name", ""))
	var persona: Dictionary = personas.get(name, {}) if personas.has(name) else {}
	var roll := _rng.randf()
	var out: Dictionary
	if roll < 0.45 and economy != null:
		out = _quest_goal(bot, name, persona)
	elif roll < 0.70:
		out = _explore_goal(bot, persona)
	else:
		out = _hub_goal(bot, prefer, persona)
	# Objectifs persona (méta, pas annoncé chat)
	bot["obj_short"] = str(persona.get("short", out.get("goal_label", "")))
	bot["obj_medium"] = str(persona.get("medium", ""))
	bot["obj_long"] = str(persona.get("long", ""))
	_maybe_world_suggest(bot, persona, out)
	return out


func _hub_goal(bot: Dictionary, prefer: Array, persona: Dictionary) -> Dictionary:
	var keys: Array = prefer.duplicate() if prefer.size() > 0 else pois.keys()
	if keys.is_empty():
		keys = ["plaza"]
	var avoid := str(bot.get("goal", ""))
	var pick := str(keys[_rng.randi() % keys.size()])
	if keys.size() > 1 and pick == avoid:
		pick = str(keys[_rng.randi() % keys.size()])
	var pos: Vector3 = pois.get(pick, Vector3(4749.0, 0.15, -737.0))
	return {
		"target": pos,
		"goal_id": pick,
		"goal_label": pick,
		"play_mode": "hub",
		"quest_id": "",
	}


func _explore_goal(bot: Dictionary, persona: Dictionary) -> Dictionary:
	# Point libre dans l'anneau (désert vide OK) — sinon waypoint catalogué
	if explore.size() > 0 and _rng.randf() < random_sample_chance:
		var rnd := _random_ring_pos(bot)
		return {
			"target": rnd,
			"goal_id": "ring_sample",
			"goal_label": "reconnaître l'anneau désert",
			"play_mode": "explore",
			"quest_id": "",
		}
	var prefer: Array = persona.get("explore_prefer", []) if typeof(persona.get("explore_prefer", null)) == TYPE_ARRAY else []
	var id := "gate_east"
	if prefer.size() > 0:
		id = str(prefer[_rng.randi() % prefer.size()])
	elif explore.size() > 0:
		var keys := explore.keys()
		id = str(keys[_rng.randi() % keys.size()])
	var spot: Dictionary = explore.get(id, explore.get("gate_east", EXPLORE_FALLBACK["gate_east"]))
	var raw_pos: Variant = spot.get("pos", RING_CENTER_FALLBACK)
	var pos: Vector3 = clamp_pos(raw_pos if typeof(raw_pos) == TYPE_VECTOR3 else RING_CENTER_FALLBACK)
	return {
		"target": pos,
		"goal_id": id,
		"goal_label": str(spot.get("label", id)),
		"play_mode": "explore",
		"quest_id": "",
	}


func _random_ring_pos(bot: Dictionary = {}) -> Vector3:
	var bpos: Vector3 = bot.get("pos", ring_center) if bot.has("pos") and typeof(bot["pos"]) == TYPE_VECTOR3 else ring_center
	var d_zalem := Vector2(bpos.x - OUTPOST_ZALEM_CENTER.x, bpos.z - OUTPOST_ZALEM_CENTER.z).length()
	var d_ksar := Vector2(bpos.x - OUTPOST_KSAR_CENTER.x, bpos.z - OUTPOST_KSAR_CENTER.z).length()
	
	# Échantillonnage local si le bot patrouille ou explore près d'un village
	if d_zalem < 1400.0:
		var ang_z := _rng.randf() * TAU
		var dist_z := _rng.randf_range(160.0, 750.0)
		return Vector3(OUTPOST_ZALEM_CENTER.x + cos(ang_z) * dist_z, 0.15, OUTPOST_ZALEM_CENTER.z + sin(ang_z) * dist_z)
	elif d_ksar < 1400.0:
		var ang_k := _rng.randf() * TAU
		var dist_k := _rng.randf_range(160.0, 750.0)
		return Vector3(OUTPOST_KSAR_CENTER.x + cos(ang_k) * dist_k, 0.15, OUTPOST_KSAR_CENTER.z + sin(ang_k) * dist_k)

	## Grand anneau désert global (30–95 % du rayon)
	var ang := _rng.randf() * TAU
	var dist := _rng.randf_range(ring_radius_m * 0.30, ring_radius_m * 0.95)
	return Vector3(
		ring_center.x + cos(ang) * dist,
		0.15,
		ring_center.z + sin(ang) * dist
	)


func _quest_goal(bot: Dictionary, name: String, persona: Dictionary) -> Dictionary:
	var now := Time.get_unix_time_from_system()
	if now - float(_quest_cd.get(name, 0.0)) < 6.0:
		return _explore_goal(bot, persona)
	_quest_cd[name] = now
	var active = null
	var st: Dictionary = economy.status(name)
	var act: Array = st.get("active", [])
	if typeof(act) == TYPE_ARRAY and act.size() > 0 and typeof(act[0]) == TYPE_DICTIONARY:
		active = act[0]
	if active == null:
		var qid := _pick_quest_id(name, persona)
		if qid.is_empty():
			return _explore_goal(bot, persona)
		economy.accept(name, qid, "npc:core3_daan_oth")
		return {
			"target": pois.get("board", Vector3(4939.0, 0.15, -932.0)),
			"goal_id": "quest_accept",
			"goal_label": "accepte %s" % qid,
			"play_mode": "quest",
			"quest_id": qid,
		}
	var qid2 := str(active.get("id", ""))
	var steps: Array = active.get("progress", [])
	var done: Array = active.get("steps_done", [])
	var pending = null
	for s in steps:
		if typeof(s) != TYPE_DICTIONARY:
			continue
		var sid := str(s.get("id", ""))
		if sid != "" and sid not in done:
			pending = s
			break
	if pending == null:
		economy.complete(name, qid2)
		return {
			"target": pois.get("board", Vector3(4939.0, 0.15, -932.0)),
			"goal_id": "quest_done",
			"goal_label": "termine %s" % qid2,
			"play_mode": "quest",
			"quest_id": qid2,
		}
	var poi := str(pending.get("poi", "poi:lost_heaven_gate"))
	var pos := _poi_to_pos(poi)
	# progress when close — handled in sim on arrival via autonomy.arrive
	bot["_pending_step"] = str(pending.get("id", ""))
	bot["_pending_quest"] = qid2
	return {
		"target": pos,
		"goal_id": "quest:%s:%s" % [qid2, str(pending.get("id", ""))],
		"goal_label": str(pending.get("label", pending.get("id", ""))),
		"play_mode": "quest",
		"quest_id": qid2,
	}


func on_arrival(bot: Dictionary) -> void:
	var qid := str(bot.get("_pending_quest", ""))
	var sid := str(bot.get("_pending_step", ""))
	if qid.is_empty() or sid.is_empty() or economy == null:
		return
	economy.progress(str(bot.get("name", "")), qid, sid)
	bot.erase("_pending_quest")
	bot.erase("_pending_step")


func _pick_quest_id(name: String, persona: Dictionary) -> String:
	var board: Dictionary = economy.board("npc:core3_daan_oth", name)
	var quests: Array = board.get("quests", [])
	if typeof(quests) != TYPE_ARRAY or quests.is_empty():
		return ""
	var by_id: Dictionary = {}
	for q in quests:
		if typeof(q) == TYPE_DICTIONARY and str(q.get("id", "")) != "":
			by_id[str(q["id"])] = q
	var prefer: Array = persona.get("quest_prefer", []) if typeof(persona.get("quest_prefer", null)) == TYPE_ARRAY else []
	for qid in prefer:
		if by_id.has(str(qid)):
			return str(qid)
	return str(quests[0].get("id", ""))


func _poi_to_pos(poi: String) -> Vector3:
	var p := poi
	if p.begins_with("poi:"):
		p = p.substr(4)
	# map common
	var map := {
		"lost_heaven": "plaza",
		"lost_heaven_market": "market",
		"lost_heaven_starport": "apron",
		"lost_heaven_cantina": "cantina",
		"lost_heaven_mission_post": "board",
		"lost_heaven_clinic": "clinic",
		"lost_heaven_training_hall": "train",
		"lost_heaven_inn": "inn",
		"lost_heaven_town_hall": "hall",
		"lost_heaven_artisan_hall": "craft",
		"lost_heaven_gate": "gate_east",
		"lost_heaven_gate_west": "gate_west",
		"lh_hunt_chacal": "hunt",
		"player_spawn": "spawn_apron",
	}
	var key := str(map.get(p, p))
	if pois.has(key):
		return pois[key]
	if explore.has(key):
		return explore[key]["pos"]
	return pois.get("plaza", Vector3(4749.0, 0.15, -737.0))


func _maybe_world_suggest(bot: Dictionary, persona: Dictionary, goal: Dictionary) -> void:
	if suggest == null:
		return
	var name := str(bot.get("name", ""))
	var now := Time.get_unix_time_from_system()
	if now - float(_last_suggest.get(name, 0.0)) < 420.0:
		return
	if _rng.randf() > 0.18:
		return
	_last_suggest[name] = now
	var kinds: Array = persona.get("suggest_kinds", ["poi"]) if typeof(persona.get("suggest_kinds", null)) == TYPE_ARRAY else ["poi"]
	var kind := str(kinds[_rng.randi() % kinds.size()]) if kinds.size() > 0 else "poi"
	var text := "Suggestion hub : %s pourrait enrichir %s (obj. %s)." % [
		str(goal.get("goal_label", "ce lieu")),
		kind,
		str(persona.get("long", "vie hub")),
	]
	suggest.submit(name, kind, text, {
		"goal_id": str(goal.get("goal_id", "")),
		"play_mode": str(goal.get("play_mode", "")),
		"obj_long": str(persona.get("long", "")),
		"agent_id": str(persona.get("agent_id", "")),
		"admin_level": int(persona.get("admin_level", 0)),
		"account_login": str(persona.get("account_login", "")),
	})
