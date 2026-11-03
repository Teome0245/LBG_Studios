extends RefCounted
## Service Autoritaire des 32+ Professions SWG Pre-CU (Arbres 4x4 & 250 Skill Points)
## Gère l'apprentissage, les prérequis stricts, l'abandon de compétences et le décompte des points.

const _HubPaths := preload("res://scripts/hub_paths.gd")

const MAX_SKILL_POINTS: int = 250

var professions_catalog: Array = []
var skills_by_id: Dictionary = {}

# Suivi par joueur : player_id -> {"skills": Array[String], "points_spent": int}
var player_profiles: Dictionary = {}


func setup(custom_data_path: String = "") -> void:
	var path := custom_data_path
	if path.is_empty():
		path = "res://data/swg_precu_professions.json"

	var raw: Variant = _HubPaths.read_json(path)
	if typeof(raw) != TYPE_DICTIONARY:
		push_error("[SWG-Professions] Impossible de charger le catalogue de professions : %s" % path)
		return

	var d: Dictionary = raw
	professions_catalog = d.get("professions", [])
	skills_by_id = d.get("skills_by_id", {})
	print("[SWG-Professions] Catalogue initialisé avec succès : %d professions et %d boîtes de compétences." % [professions_catalog.size(), skills_by_id.size()])


func get_or_create_profile(player_id: String) -> Dictionary:
	if not player_profiles.has(player_id):
		player_profiles[player_id] = {
			"skills": [],
			"points_spent": 0,
			"points_remaining": MAX_SKILL_POINTS
		}
	return player_profiles[player_id]


func can_learn_skill(player_id: String, skill_id: String) -> Dictionary:
	var profile := get_or_create_profile(player_id)
	var p_skills: Array = profile["skills"]

	if p_skills.has(skill_id):
		return {"ok": false, "reason": "Compétence déjà acquise."}

	if not skills_by_id.has(skill_id):
		return {"ok": false, "reason": "Compétence inconnue dans le catalogue."}

	var sk: Dictionary = skills_by_id[skill_id]
	var cost: int = int(sk.get("cost", 0))
	var remaining: int = MAX_SKILL_POINTS - int(profile.get("points_spent", 0))

	if cost > remaining:
		return {"ok": false, "reason": "Points de compétence insuffisants (%d requis, %d restants sur 250)." % [cost, remaining]}

	var reqs: Array = sk.get("reqs", [])
	for r in reqs:
		if not p_skills.has(str(r)):
			var req_sk: Dictionary = skills_by_id.get(str(r), {})
			var req_name := str(req_sk.get("name", str(r)))
			return {"ok": false, "reason": "Prérequis manquant : %s" % req_name}

	return {"ok": true, "cost": cost}


func learn_skill(player_id: String, skill_id: String) -> Dictionary:
	var check := can_learn_skill(player_id, skill_id)
	if not bool(check.get("ok", false)):
		return check

	var profile := get_or_create_profile(player_id)
	var cost: int = int(check.get("cost", 0))

	profile["skills"].append(skill_id)
	profile["points_spent"] = int(profile["points_spent"]) + cost
	profile["points_remaining"] = MAX_SKILL_POINTS - int(profile["points_spent"])

	return {
		"ok": true,
		"skill_id": skill_id,
		"cost": cost,
		"points_spent": profile["points_spent"],
		"points_remaining": profile["points_remaining"]
	}


func surrender_skill(player_id: String, skill_id: String) -> Dictionary:
	var profile := get_or_create_profile(player_id)
	var p_skills: Array = profile["skills"]

	if not p_skills.has(skill_id):
		return {"ok": false, "reason": "Le joueur ne possède pas cette compétence."}

	# Vérifier si une autre compétence apprise dépend de celle-ci
	for sk in p_skills:
		if sk != skill_id and skills_by_id.has(sk):
			var reqs: Array = skills_by_id[sk].get("reqs", [])
			if reqs.has(skill_id):
				var dep_name := str(skills_by_id[sk].get("name", sk))
				return {"ok": false, "reason": "Impossible d'abandonner : la compétence %s en dépend !" % dep_name}

	var cost: int = int(skills_by_id.get(skill_id, {}).get("cost", 0))
	p_skills.erase(skill_id)
	profile["points_spent"] = maxi(0, int(profile["points_spent"]) - cost)
	profile["points_remaining"] = MAX_SKILL_POINTS - int(profile["points_spent"])

	return {
		"ok": true,
		"skill_id": skill_id,
		"refunded": cost,
		"points_spent": profile["points_spent"],
		"points_remaining": profile["points_remaining"]
	}

