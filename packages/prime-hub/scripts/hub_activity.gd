extends RefCounted
class_name HubActivity
## C2 — activité joueur lisible (humain = IA). Pas de tag espèce.
##
## status ∈ idle | busy | quest
## activity = libellé court nameplate (≤14 car. côté client)

const IDLE_GOALS := {
	"": true,
	"idle": true,
	"none": true,
	"null": true,
	"show_idle": true,
}

const LABEL_MAP := {
	"companion_escort": "escorte",
	"escort_follow": "escorte",
	"escort_wait": "escorte",
	"escort_done": "escorte",
	"http_move_to": "en route",
	"quest_accept": "quête",
	"quest_done": "quête",
	"plaza": "hub",
	"market": "marché",
	"board": "board",
	"cantina": "cantina",
	"clinic": "clinique",
	"show_stage": "scène",
	"salvage": "salvage",
	"wander": "erre",
	"rest": "repos",
	"rest_home": "repos",
	"work": "travail",
	"leisure": "loisir",
}


static func describe(ent: Dictionary) -> Dictionary:
	## Retourne {status, activity, goal} — champs vides si idle.
	var goal := str(ent.get("goal", "")).strip_edges()
	var play_mode := str(ent.get("play_mode", "")).strip_edges().to_lower()
	var quest_id := str(ent.get("quest_id", "")).strip_edges()
	var label := _label_for_goal(goal, play_mode, quest_id)
	var status := "idle"
	if play_mode == "quest" or quest_id != "" or goal.begins_with("quest"):
		status = "quest"
	elif label != "" and not IDLE_GOALS.has(goal.to_lower()):
		status = "busy"
	elif label != "":
		status = "busy"
	else:
		status = "idle"
		label = ""
	return {
		"status": status,
		"activity": label,
		"goal": goal,
	}


static func describe_with_economy(ent: Dictionary, economy) -> Dictionary:
	## Enrichit les humains (pas de goal bot) via quêtes actives economy.
	var base := describe(ent)
	if str(ent.get("kind", "")) != "player":
		return base
	if economy == null or not economy.has_method("status"):
		return base
	if str(base.get("activity", "")) != "":
		return base
	var pname := str(ent.get("name", "")).strip_edges()
	if pname.is_empty():
		return base
	var st: Dictionary = economy.status(pname)
	if not bool(st.get("ok", true)) and st.has("error"):
		return base
	var active = st.get("active", [])
	if typeof(active) != TYPE_ARRAY or active.is_empty():
		return base
	var first = active[0]
	if typeof(first) != TYPE_DICTIONARY:
		return base
	var title := str(first.get("title", first.get("id", "quête"))).strip_edges()
	var short := _short_words(title, 14)
	return {
		"status": "quest",
		"activity": short if short != "" else "quête",
		"goal": str(first.get("id", "")),
	}


static func _label_for_goal(goal: String, play_mode: String, quest_id: String) -> String:
	var g := goal.strip_edges()
	var gl := g.to_lower()
	if IDLE_GOALS.has(gl):
		if play_mode == "quest" or quest_id != "":
			return "quête"
		return ""
	if LABEL_MAP.has(gl):
		return str(LABEL_MAP[gl])
	if gl.begins_with("quest:") or gl.begins_with("quest_"):
		# quest:id:step → dernier segment lisible
		var parts := g.split(":")
		var last := str(parts[parts.size() - 1]).strip_edges()
		if last.is_empty():
			return "quête"
		return _short_words(last.replace("_", " "), 14)
	if gl.begins_with("ring") or gl.contains("explore"):
		return "explore"
	if gl.contains("escort"):
		return "escorte"
	if gl.contains("hunt") or gl.contains("combat"):
		return "chasse"
	# POI / goal_id brut → tronqué sans underscore
	return _short_words(g.replace("_", " "), 14)


static func _short_words(text: String, max_len: int) -> String:
	var t := text.strip_edges()
	if t.is_empty():
		return ""
	if t.length() <= max_len:
		return t
	return t.substr(0, max_len - 1) + "…"
