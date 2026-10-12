extends RefCounted
class_name HubSimAmbient
## Gestion du chat, ambiances périodiques et salutations compagnon — Ticket 2.2.

const ZONE := "scrapaltai"

var sim = null
var _chat_queue: Array = []
var _greeted_oids: Dictionary = {}  # oid -> true
var _last_ambient: Dictionary = {}  # eid -> float unix


func setup(parent_sim) -> void:
	sim = parent_sim


func clear() -> void:
	_chat_queue.clear()
	_greeted_oids.clear()
	_last_ambient.clear()


func remove_human(oid: int) -> void:
	_greeted_oids.erase(oid)


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


func _humans() -> Array:
	var out: Array = []
	if sim == null:
		return out
	for eid in sim.entities.keys():
		var e: Dictionary = sim.entities[eid]
		if str(e.get("kind", "")) == "player" and not bool(e.get("is_bot", false)):
			out.append(e)
	return out


func pick_companion_bot() -> Dictionary:
	if sim == null:
		return {}
	var prefer := ["player:Nix", "Nix", "player:Lia", "Lia"]
	for want in prefer:
		var w := str(want).to_lower()
		for b in sim.bot_defs:
			var bot = sim.entities.get(str(b["eid"]))
			if bot == null:
				continue
			var eid := str(b.get("eid", "")).to_lower()
			var nm := str(b.get("name", "")).to_lower()
			if eid == w or nm == w or eid.ends_with(":" + w):
				return bot
	for b in sim.bot_defs:
		var bot2 = sim.entities.get(str(b["eid"]))
		if bot2 != null:
			return bot2
	return {}


func start_companion_escort(bot: Dictionary, duration_s: float) -> void:
	if sim == null:
		return
	var now := Time.get_unix_time_from_system()
	bot["_escort_until"] = now + maxf(8.0, duration_s)
	bot["goal"] = "companion_escort"
	bot["linger_until"] = 0.0
	bot["has_waypoint"] = false
	bot["path"] = []
	bot["needs_path"] = false
	var humans := _humans()
	if humans.is_empty():
		return
	var hp: Vector3 = humans[0]["pos"]
	var wz: Vector2 = sim._walkable_xz(hp.x + 5.0, hp.z + 3.0)
	bot["target"] = Vector3(wz.x, hp.y, wz.y)


func fleet_greet_human(human_name: String, human_oid: int) -> void:
	if _greeted_oids.has(human_oid) or sim == null:
		return
	_greeted_oids[human_oid] = true
	sim._ensure_fleet()
	var who := human_name.strip_edges()
	if who.is_empty():
		who = "Voyageur"
	var companion := pick_companion_bot()
	if companion.is_empty():
		return
	var decision: Dictionary = sim.presence_resolve_action(companion, 12.0)
	var act := str(decision.get("action", "greet"))
	if act == "ignore":
		return
	var line := str(companion.get("greet", "Salut {who}.")).replace("{who}", who)
	var dial_line: String = sim.presence_line_for(companion, who)
	if not dial_line.is_empty() and not line.contains(dial_line):
		line = "%s %s" % [line, dial_line]
	enqueue_say(str(companion.get("name", "Nix")), int(companion.get("oid", 0)), line, "ia")
	if act == "escort":
		var dur := float(decision.get("escort_duration_s", 28.0))
		start_companion_escort(companion, dur if dur > 0.0 else 28.0)
		sim._stream(
			"companion.escort",
			"%s a escorté %s près du hub." % [str(companion.get("name", "Nix")), who],
			str(companion.get("name", "Nix")),
			ZONE,
			{"human": who, "human_oid": human_oid, "chaleur": float(decision.get("chaleur", 0.0))}
		)


func maybe_ambient() -> void:
	if sim == null:
		return
	var now := Time.get_unix_time_from_system()
	var humans := _humans()
	if humans.is_empty():
		return
	for b in sim.bot_defs:
		var eid: String = str(b["eid"])
		var bot = sim.entities.get(eid)
		if bot == null:
			continue
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
		var hp_n: Vector3 = near["pos"]
		var dist_n := Vector2(hp_n.x - bp.x, hp_n.z - bp.z).length()
		var decision_n: Dictionary = sim.presence_resolve_action(bot if not bot.is_empty() else b, dist_n)
		if str(decision_n.get("action", "")) == "ignore":
			continue
		_last_ambient[eid] = now
		var who_n := str(near["name"])
		var line := str(b.get("ambient", "")).replace("{who}", who_n).strip_edges()
		var dial_amb: String = sim.presence_line_for(bot if not bot.is_empty() else b, who_n)
		if not dial_amb.is_empty() and (hash(eid) % 2) == 0:
			line = dial_amb
		if line.is_empty():
			continue
		enqueue_say(str(b["name"]), int(bot["oid"]), line, "ia")

	for eid in sim.entities.keys():
		var e: Dictionary = sim.entities[eid]
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
