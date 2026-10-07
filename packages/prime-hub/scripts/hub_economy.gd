extends RefCounted
class_name HubEconomy
const _HubPaths = preload("res://scripts/hub_paths.gd")

## Inventaire / board / quêtes / craft — contrats peel C10/C11.

const DEFAULT_INV := [
	{"id": "scrap_metal", "name": "Ferraille", "qty": 4, "icon": "copper"},
	{"id": "binding_tape", "name": "Ruban de liaison", "qty": 2, "icon": "screw"},
	{"id": "dried_grain", "name": "Grain séché", "qty": 4, "icon": "ration"},
	{"id": "water_capsule", "name": "Capsule d'eau", "qty": 2, "icon": "kit"},
]
const DEFAULT_SKILLS := [
	"prospecteur_r1", "artisan_rue_r1", "medecine_camp_r1", "pilotage_shuttle_r1",
]

var _templates: Array = []
var _by_id: Dictionary = {}
var _players: Dictionary = {}
var _path: String = ""


func setup() -> void:
	_path = _HubPaths.data_file("players_state.json")
	reload_templates()
	_load_players()


func reload_templates() -> void:
	_templates.clear()
	_by_id.clear()
	var qpath := OS.get_environment("LBG_HUB_QUESTS_JSON").strip_edges()
	if qpath.is_empty():
		qpath = _HubPaths.data_file("quests_lbg_templates.json")
	var raw: Variant = _HubPaths.read_json(qpath)
	if typeof(raw) == TYPE_DICTIONARY:
		var arr = raw.get("templates", [])
		if typeof(arr) == TYPE_ARRAY:
			for t in arr:
				if typeof(t) == TYPE_DICTIONARY and str(t.get("id", "")) != "":
					_templates.append(t)
					_by_id[str(t["id"])] = t
	if _templates.is_empty():
		var fb := {
			"id": "lh_survey_dunes",
			"title": "Relevé hors palissade",
			"template": "survey",
			"objective": "Sortir porte est et revenir.",
			"progress": [{"id": "exit", "label": "Sortir vers la porte est", "poi": "poi:lost_heaven_gate", "radius_m": 70}],
			"rewards": {"credits": 25, "items": [{"id": "scrap_metal", "qty": 2}]},
			"giver_ids": ["npc:core3_daan_oth"],
			"default_giver": "Daan Oth",
			"next_steps": ["Sortir porte est", "Revenir"],
		}
		_templates.append(fb)
		_by_id[str(fb["id"])] = fb


func _load_players() -> void:
	_players.clear()
	var raw: Variant = _HubPaths.read_json(_path)
	if typeof(raw) != TYPE_DICTIONARY:
		return
	var players = raw.get("players", {})
	if typeof(players) == TYPE_DICTIONARY:
		for k in players.keys():
			var v = players[k]
			if typeof(v) == TYPE_DICTIONARY:
				_players[str(k)] = v


func _save_players() -> void:
	_HubPaths.write_json(_path, {
		"schema_version": 1,
		"players": _players,
		"saved_at": int(Time.get_unix_time_from_system()),
	})


func _player(name: String) -> Dictionary:
	var key := name.strip_edges()
	if key.is_empty():
		key = "Voyageur"
	if not _players.has(key):
		_players[key] = {
			"inventory": DEFAULT_INV.duplicate(true),
			"skills": DEFAULT_SKILLS.duplicate(),
			"credits": 50,
			"active": [],
			"completed": [],
		}
	return _players[key]


func inventory(player: String) -> Dictionary:
	var p := _player(player)
	return {
		"ok": true,
		"player": player if not player.strip_edges().is_empty() else "Voyageur",
		"skills": (p["skills"] as Array).duplicate(),
		"inventory": (p["inventory"] as Array).duplicate(true),
		"source": "prime_hub",
		"core3_live": false,
		"persisted": FileAccess.file_exists(_path),
	}


func board(giver: String, player: String) -> Dictionary:
	var quests: Array = []
	for t in _templates:
		quests.append({
			"id": t["id"],
			"title": t.get("title", t["id"]),
			"template": t.get("template", ""),
			"objective": t.get("objective", ""),
			"next_steps": (t.get("next_steps", []) as Array).duplicate(),
			"progress": (t.get("progress", []) as Array).duplicate(true),
			"rewards": (t.get("rewards", {}) as Dictionary).duplicate(true),
			"default_giver": t.get("default_giver", ""),
			"giver_ids": (t.get("giver_ids", []) as Array).duplicate(),
			"generated": false,
		})
	return {
		"ok": true,
		"hub": "lost_heaven",
		"giver_id": giver if not giver.is_empty() else "npc:core3_daan_oth",
		"player": player if not player.is_empty() else "Voyageur",
		"quests": quests,
		"source": "prime_hub",
	}


func status(player: String) -> Dictionary:
	var p := _player(player)
	return {
		"ok": true,
		"player": player if not player.is_empty() else "Voyageur",
		"credits": int(p["credits"]),
		"active": (p["active"] as Array).duplicate(true),
		"completed": (p["completed"] as Array).duplicate(),
		"generated_offers": [],
		"generated_by_id": {},
		"board_rotation": 0,
		"source": "prime_hub",
		"persisted": FileAccess.file_exists(_path),
	}


func accept(player: String, quest_id: String, giver_id: String = "") -> Dictionary:
	var p := _player(player)
	var qid := quest_id.strip_edges()
	if not _by_id.has(qid):
		return {"ok": false, "error": "unknown_quest", "quest_id": qid}
	for a in p["active"]:
		if typeof(a) == TYPE_DICTIONARY and str(a.get("id", "")) == qid:
			return {"ok": true, "already": true, "quest_id": qid, "active": (p["active"] as Array).duplicate(true)}
	if qid in (p["completed"] as Array):
		return {"ok": false, "error": "already_completed", "quest_id": qid}
	var tmpl: Dictionary = _by_id[qid]
	var entry := {
		"id": qid,
		"title": tmpl.get("title", qid),
		"giver_id": giver_id if not giver_id.is_empty() else "npc:core3_daan_oth",
		"steps_done": [],
		"progress": (tmpl.get("progress", []) as Array).duplicate(true),
	}
	(p["active"] as Array).append(entry)
	_save_players()
	return {"ok": true, "quest_id": qid, "active": (p["active"] as Array).duplicate(true), "source": "prime_hub"}


func progress(player: String, quest_id: String, step_id: String) -> Dictionary:
	var p := _player(player)
	var qid := quest_id.strip_edges()
	var sid := step_id.strip_edges()
	for a in p["active"]:
		if typeof(a) != TYPE_DICTIONARY or str(a.get("id", "")) != qid:
			continue
		var done: Array = a.get("steps_done", [])
		if sid not in done:
			done.append(sid)
		a["steps_done"] = done
		_save_players()
		return {"ok": true, "quest_id": qid, "step_id": sid, "steps_done": done.duplicate(), "source": "prime_hub"}
	return {"ok": false, "error": "not_active", "quest_id": qid}


func complete(player: String, quest_id: String) -> Dictionary:
	var p := _player(player)
	var qid := quest_id.strip_edges()
	if not _by_id.has(qid):
		return {"ok": false, "error": "unknown_quest"}
	var tmpl: Dictionary = _by_id[qid]
	var found = null
	for a in p["active"]:
		if typeof(a) == TYPE_DICTIONARY and str(a.get("id", "")) == qid:
			found = a
			break
	if found == null:
		return {"ok": false, "error": "not_active"}
	var needed: Array = []
	for s in tmpl.get("progress", []):
		if typeof(s) == TYPE_DICTIONARY and str(s.get("id", "")) != "":
			needed.append(str(s["id"]))
	var done: Array = found.get("steps_done", [])
	for n in needed:
		if n not in done:
			return {"ok": false, "error": "incomplete", "needed": needed, "steps_done": done.duplicate()}
	var active: Array = []
	for a in p["active"]:
		if typeof(a) == TYPE_DICTIONARY and str(a.get("id", "")) != qid:
			active.append(a)
	p["active"] = active
	if qid not in (p["completed"] as Array):
		(p["completed"] as Array).append(qid)
	var rewards: Dictionary = tmpl.get("rewards", {})
	var credits := int(rewards.get("credits", 0))
	p["credits"] = int(p["credits"]) + credits
	var granted: Array = []
	for it in rewards.get("items", []):
		if typeof(it) != TYPE_DICTIONARY:
			continue
		var iid := str(it.get("id", ""))
		var qty := int(it.get("qty", 1))
		if iid.is_empty():
			continue
		_add_item(p, iid, qty, str(it.get("name", iid)))
		granted.append({"id": iid, "qty": qty})
	_save_players()
	return {
		"ok": true,
		"quest_id": qid,
		"credits": int(p["credits"]),
		"credits_gained": credits,
		"items": granted,
		"inventory": (p["inventory"] as Array).duplicate(true),
		"source": "prime_hub",
	}


func tip(player: String, quest_id: String, amount: int = 2) -> Dictionary:
	var p := _player(player)
	var amt := maxi(0, amount)
	if int(p["credits"]) < amt:
		return {"ok": false, "error": "insufficient_credits", "credits": int(p["credits"])}
	p["credits"] = int(p["credits"]) - amt
	_save_players()
	return {"ok": true, "quest_id": quest_id, "amount": amt, "credits": int(p["credits"]), "source": "prime_hub"}


func _add_item(p: Dictionary, item_id: String, qty: int, item_name: String = "") -> void:
	for it in p["inventory"]:
		if typeof(it) == TYPE_DICTIONARY and str(it.get("id", "")) == item_id:
			it["qty"] = int(it.get("qty", 0)) + qty
			return
	(p["inventory"] as Array).append({
		"id": item_id,
		"name": item_name if not item_name.is_empty() else item_id,
		"qty": qty,
		"icon": "copper",
	})


func craft_combine(player: String, recipe_id: String = "") -> Dictionary:
	var p := _player(player)
	var need := {"scrap_metal": 1, "binding_tape": 1}
	for iid in need.keys():
		var have := 0
		for i in p["inventory"]:
			if typeof(i) == TYPE_DICTIONARY and str(i.get("id", "")) == str(iid):
				have = int(i.get("qty", 0))
				break
		if have < int(need[iid]):
			return {"ok": false, "error": "missing_ingredients", "need": need}
	for iid in need.keys():
		for it in p["inventory"]:
			if typeof(it) == TYPE_DICTIONARY and str(it.get("id", "")) == str(iid):
				it["qty"] = int(it["qty"]) - int(need[iid])
	var cleaned: Array = []
	for i in p["inventory"]:
		if typeof(i) == TYPE_DICTIONARY and int(i.get("qty", 0)) > 0:
			cleaned.append(i)
	p["inventory"] = cleaned
	var crafted := {"id": "kit_reparation", "name": "Kit de réparation", "qty": 1, "icon": "kit"}
	_add_item(p, crafted["id"], 1, crafted["name"])
	_save_players()
	return {
		"ok": true,
		"recipe_id": recipe_id if not recipe_id.is_empty() else "bind_scrap",
		"crafted": crafted,
		"inventory": (p["inventory"] as Array).duplicate(true),
		"source": "prime_hub",
	}
