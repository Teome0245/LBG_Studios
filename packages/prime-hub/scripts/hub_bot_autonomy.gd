extends RefCounted
class_name HubBotAutonomy
## Flotte IA : choix quête / explore / hub + suggestions monde occasionnelles.

const _HubPaths = preload("res://scripts/hub_paths.gd")

const EXPLORE: Dictionary = {
	"gate_east": {"label": "explorer porte est / dunes", "pos": Vector3(5813.6, 0.15, -982.5)},
	"gate_west": {"label": "surveiller porte ouest Zalem", "pos": Vector3(3688.9, 0.15, -675.9)},
	"hunt": {"label": "reconnaître hors murs", "pos": Vector3(5985.0, 0.15, -1120.0)},
	"spawn_apron": {"label": "repasser au shuttleport", "pos": Vector3(4749.0, 0.15, -537.0)},
}

var personas: Dictionary = {}
var economy = null
var suggest = null
var pois: Dictionary = {}
var _rng := RandomNumberGenerator.new()
var _last_suggest: Dictionary = {}  # name -> unix
var _quest_cd: Dictionary = {}


func setup(economy_svc, suggest_svc, poi_map: Dictionary) -> void:
	economy = economy_svc
	suggest = suggest_svc
	pois = poi_map
	_rng.randomize()
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
				personas[nm] = {
					"short": str(p.get("short", "")),
					"medium": str(p.get("medium", "")),
					"long": str(p.get("long", "")),
					"quest_prefer": p.get("quest_prefer", []),
					"explore_prefer": p.get("explore_prefer", []),
					"suggest_kinds": p.get("suggest_kinds", ["poi"]),
					"playstyle": str(p.get("playstyle", "")),
				}
	if personas.is_empty():
		var raw: Variant = _HubPaths.read_json(_HubPaths.data_file("life/bot_personas.json"))
		if typeof(raw) == TYPE_DICTIONARY:
			var bots = raw.get("bots", {})
			if typeof(bots) == TYPE_DICTIONARY:
				personas = bots


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
	var prefer: Array = persona.get("explore_prefer", []) if typeof(persona.get("explore_prefer", null)) == TYPE_ARRAY else []
	var id := "gate_east"
	if prefer.size() > 0:
		id = str(prefer[_rng.randi() % prefer.size()])
	elif EXPLORE.size() > 0:
		var keys := EXPLORE.keys()
		id = str(keys[_rng.randi() % keys.size()])
	var spot: Dictionary = EXPLORE.get(id, EXPLORE["gate_east"])
	return {
		"target": spot["pos"],
		"goal_id": id,
		"goal_label": str(spot.get("label", id)),
		"play_mode": "explore",
		"quest_id": "",
	}


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
	if EXPLORE.has(key):
		return EXPLORE[key]["pos"]
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
	})
