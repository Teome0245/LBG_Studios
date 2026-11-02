extends RefCounted
class_name HubSurvey
## Ticket 4.2 (O2 Phase 4 SWG Pre-CU) — Prospection Dynamique (Survey Tool) & Spawns de Ressources
## à statistiques procédurales 1..1000 (OQ, CD, PE, MA, SR).

const _HubPaths := preload("res://scripts/hub_paths.gd")

const MIN_SAMPLE_DENSITY := 15

var economy = null
var skills = null
var spawns_by_id: Dictionary = {}
var _rng := RandomNumberGenerator.new()


func setup(economy_svc = null, skills_svc = null) -> void:
	economy = economy_svc
	skills = skills_svc
	_rng.randomize()
	reload_spawns()


func reload_spawns(custom_path: String = "") -> void:
	spawns_by_id.clear()
	var path := custom_path
	if path.is_empty():
		path = _HubPaths.data_file("resources_spawns_lh.json")
	var raw: Variant = _HubPaths.read_json(path)
	if typeof(raw) != TYPE_DICTIONARY:
		return
	var arr: Variant = raw.get("spawns", [])
	if typeof(arr) != TYPE_ARRAY:
		return
	for sp in arr:
		if typeof(sp) == TYPE_DICTIONARY and not str(sp.get("spawn_id", "")).is_empty():
			spawns_by_id[str(sp["spawn_id"])] = (sp as Dictionary).duplicate(true)


func list_spawns() -> Array:
	var out: Array = []
	for k in spawns_by_id.keys():
		out.append((spawns_by_id[k] as Dictionary).duplicate(true))
	return out


func get_spawn(spawn_id: String) -> Dictionary:
	var sid := spawn_id.strip_edges()
	if spawns_by_id.has(sid):
		return (spawns_by_id[sid] as Dictionary).duplicate(true)
	return {}


func density_at(spawn_id: String, x: float, z: float) -> int:
	var sid := spawn_id.strip_edges()
	if not spawns_by_id.has(sid):
		return 0
	var sp: Dictionary = spawns_by_id[sid]
	var hx := float(sp.get("hotspot_x", 0.0))
	var hz := float(sp.get("hotspot_z", 0.0))
	var radius := maxf(1.0, float(sp.get("radius", 60.0)))
	var peak := clampi(int(sp.get("peak_density", 90)), 1, 100)
	var dist := Vector2(x - hx, z - hz).length()
	if dist >= radius * 1.5:
		return 0
	var ratio := clampf(1.0 - (dist / (radius * 1.5)), 0.0, 1.0)
	return clampi(int(round(float(peak) * ratio)), 0, 100)


func _compass_dir(from_x: float, from_z: float, to_x: float, to_z: float) -> String:
	var dx := to_x - from_x
	var dz := to_z - from_z
	if Vector2(dx, dz).length() < 4.0:
		return "HERE"
	var angle := rad_to_deg(atan2(dz, dx))
	if angle >= -22.5 and angle < 22.5:
		return "E"
	elif angle >= 22.5 and angle < 67.5:
		return "SE"
	elif angle >= 67.5 and angle < 112.5:
		return "S"
	elif angle >= 112.5 and angle < 157.5:
		return "SW"
	elif angle >= 157.5 or angle < -157.5:
		return "W"
	elif angle >= -157.5 and angle < -112.5:
		return "NW"
	elif angle >= -112.5 and angle < -67.5:
		return "N"
	return "NE"


func survey_ping(player: String, filter_class_or_id: String, x: float, z: float) -> Dictionary:
	var p_name := player.strip_edges()
	if p_name.is_empty():
		p_name = "Voyageur"
	var mods := {"survey_range": 48.0, "survey_resolution": 1}
	if skills != null and skills.has_method("compute_skill_mods"):
		mods = skills.compute_skill_mods(p_name)
	var survey_range := float(mods.get("survey_range", 48.0))
	var f_key := filter_class_or_id.strip_edges().to_lower()

	var readings: Array = []
	for sid in spawns_by_id.keys():
		var sp: Dictionary = spawns_by_id[sid]
		var r_class := str(sp.get("resource_class", "")).to_lower()
		var base_id := str(sp.get("base_item_id", "")).to_lower()
		if not f_key.is_empty() and f_key != sid.to_lower() and f_key != r_class and f_key != base_id:
			continue
		var hx := float(sp.get("hotspot_x", 0.0))
		var hz := float(sp.get("hotspot_z", 0.0))
		var dist := Vector2(x - hx, z - hz).length()
		var local_dens := density_at(sid, x, z)
		var in_radar := dist <= (survey_range + float(sp.get("radius", 60.0)))
		if in_radar or local_dens > 0:
			readings.append({
				"spawn_id": sid,
				"spawn_name": str(sp.get("spawn_name", sid)),
				"resource_class": str(sp.get("resource_class", "")),
				"base_item_id": str(sp.get("base_item_id", "scrap_metal")),
				"local_density_pct": local_dens,
				"distance_m": snappedf(dist, 0.1),
				"direction": _compass_dir(x, z, hx, hz),
				"stats": (sp.get("stats", {}) as Dictionary).duplicate(true),
				"can_sample": local_dens >= MIN_SAMPLE_DENSITY,
			})

	return {
		"ok": true,
		"player": p_name,
		"survey_range_m": survey_range,
		"pos": {"x": x, "z": z},
		"readings": readings,
		"count": readings.size(),
	}


func sample_resource(player: String, spawn_id: String, x: float, z: float) -> Dictionary:
	var p_name := player.strip_edges()
	if p_name.is_empty():
		p_name = "Voyageur"
	var sid := spawn_id.strip_edges()
	if not spawns_by_id.has(sid):
		return {"ok": false, "error": "unknown_spawn", "spawn_id": sid}
	if economy == null:
		return {"ok": false, "error": "economy_unavailable"}

	var p: Dictionary = economy._player(p_name)
	var p_skills: Array = p.get("skills", [])
	if "prospecteur_novice" not in p_skills and "prospecteur_r1" not in p_skills:
		return {
			"ok": false,
			"error": "missing_survey_skill",
			"requires_skill": "prospecteur_novice",
		}

	var local_dens := density_at(sid, x, z)
	if local_dens < MIN_SAMPLE_DENSITY:
		var sp_miss: Dictionary = spawns_by_id[sid]
		return {
			"ok": false,
			"error": "density_too_low",
			"spawn_id": sid,
			"local_density_pct": local_dens,
			"min_required_pct": MIN_SAMPLE_DENSITY,
			"direction": _compass_dir(x, z, float(sp_miss.get("hotspot_x", 0.0)), float(sp_miss.get("hotspot_z", 0.0))),
		}

	var mods := {"survey_resolution": 1}
	if skills != null and skills.has_method("compute_skill_mods"):
		mods = skills.compute_skill_mods(p_name)
	var bonus_qty := int(mods.get("survey_resolution", 1))
	var extracted_qty := maxi(1, int(round(float(local_dens) / 30.0)) + bonus_qty - 1)

	var sp: Dictionary = spawns_by_id[sid]
	var base_item_id := str(sp.get("base_item_id", "scrap_metal"))
	var stats: Dictionary = (sp.get("stats", {}) as Dictionary).duplicate(true)
	var spawn_name := str(sp.get("spawn_name", sid))

	# Ajoute ou empile la ressource dans l'inventaire tout en conservant les meilleures stats Pre-CU
	var inv: Array = p.get("inventory", [])
	var found := false
	for entry in inv:
		if typeof(entry) == TYPE_DICTIONARY and str(entry.get("id", "")) == base_item_id:
			entry["qty"] = int(entry.get("qty", 0)) + extracted_qty
			entry["spawn_id"] = sid
			entry["spawn_name"] = spawn_name
			entry["resource_stats"] = stats.duplicate(true)
			found = true
			break
	if not found:
		inv.append({
			"id": base_item_id,
			"name": str(sp.get("label", spawn_name)),
			"qty": extracted_qty,
			"icon": str(sp.get("icon", "copper")),
			"spawn_id": sid,
			"spawn_name": spawn_name,
			"resource_stats": stats.duplicate(true),
		})
	p["inventory"] = inv

	var xp_gain := 45 + int(round(float(local_dens) * 0.6))
	if skills != null and skills.has_method("grant_xp"):
		skills.grant_xp(p_name, "xp_prospection", xp_gain)

	economy.log_session_event(
		p_name,
		"survey_sample",
		"Extraction %dx %s (densité %d%%, OQ %d)" % [extracted_qty, spawn_name, local_dens, int(stats.get("oq", 500))],
		{"spawn_id": sid, "qty": extracted_qty, "density": local_dens, "stats": stats}
	)
	economy._save_players()

	return {
		"ok": true,
		"player": p_name,
		"spawn_id": sid,
		"spawn_name": spawn_name,
		"base_item_id": base_item_id,
		"extracted_qty": extracted_qty,
		"local_density_pct": local_dens,
		"resource_stats": stats,
		"xp_gained": xp_gain,
	}


func rotate_spawn_stats(spawn_id: String, seed_val: int = 0) -> Dictionary:
	var sid := spawn_id.strip_edges()
	if not spawns_by_id.has(sid):
		return {"ok": false, "error": "unknown_spawn", "spawn_id": sid}
	var rng := RandomNumberGenerator.new()
	if seed_val != 0:
		rng.seed = seed_val
	else:
		rng.randomize()
	var sp: Dictionary = spawns_by_id[sid]
	var new_stats := {
		"oq": rng.randi_range(350, 995),
		"cd": rng.randi_range(300, 990),
		"pe": rng.randi_range(350, 995),
		"ma": rng.randi_range(300, 990),
		"sr": rng.randi_range(300, 990),
	}
	sp["stats"] = new_stats
	return {
		"ok": true,
		"spawn_id": sid,
		"stats": new_stats.duplicate(true),
	}

