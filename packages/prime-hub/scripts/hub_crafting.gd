extends RefCounted
class_name HubCrafting
## Ticket 2.2 (O2 Phase 3) & Ticket 4.3 (O2 Phase 4 SWG Pre-CU) — Métier de Récupérateur,
## Assemblage Pondéré par Ressources (OQ/CD/PE/MA/SR) & Phase d'Expérimentation.
## Autorité serveur stricte : validation de proximité d'ancrage CAO `craft`, vérification des ingrédients
## et snap en posture Triplon `craft` sur l'établi. Zéro mutation libre LLM.

const _HubPaths := preload("res://scripts/hub_paths.gd")

var economy = null
var collision = null
var skills = null
var schematics_by_id: Dictionary = {}
var active_craft_states: Dictionary = {}  # player -> {schematic_id, anchor_id, snap_pos, posture, duration_sec, started_at}
var experiment_sessions: Dictionary = {}  # session_id -> {session_id, player, schematic_id, output_item_id, remaining_points, attributes, history}
var _serial_seq: int = 1000
var _rng := RandomNumberGenerator.new()


func setup(economy_svc, collision_svc = null, skills_svc = null) -> void:
	economy = economy_svc
	collision = collision_svc
	skills = skills_svc
	_rng.randomize()
	reload_schematics()


func attach_skills(skills_svc) -> void:
	skills = skills_svc


func reload_schematics(custom_path: String = "") -> void:
	schematics_by_id.clear()
	var path := custom_path
	if path.is_empty():
		path = _HubPaths.data_file("craft/schematics_scrap.json")
	var raw: Variant = _HubPaths.read_json(path)
	if typeof(raw) != TYPE_DICTIONARY:
		return
	var arr: Variant = raw.get("schematics", [])
	if typeof(arr) != TYPE_ARRAY:
		return
	for sc in arr:
		if typeof(sc) == TYPE_DICTIONARY and not str(sc.get("id", "")).is_empty():
			schematics_by_id[str(sc["id"])] = (sc as Dictionary).duplicate(true)


func list_schematics() -> Array:
	var out: Array = []
	for k in schematics_by_id.keys():
		out.append((schematics_by_id[k] as Dictionary).duplicate(true))
	return out


func get_schematic(schematic_id: String) -> Dictionary:
	var sid := schematic_id.strip_edges()
	if schematics_by_id.has(sid):
		return (schematics_by_id[sid] as Dictionary).duplicate(true)
	return {}


func _compute_resource_averages(player: String, sc: Dictionary) -> Dictionary:
	var avg := {"oq": 500.0, "cd": 500.0, "pe": 500.0, "ma": 500.0, "sr": 500.0}
	if economy == null:
		return avg
	var p: Dictionary = economy._player(player)
	var inv: Array = p.get("inventory", [])
	var ings: Variant = sc.get("inputs", sc.get("ingredients", []))
	if typeof(ings) != TYPE_ARRAY or (ings as Array).is_empty():
		return avg

	var sum_oq := 0.0
	var sum_cd := 0.0
	var sum_pe := 0.0
	var sum_ma := 0.0
	var sum_sr := 0.0
	var total_weight := 0.0

	for ing in ings:
		if typeof(ing) != TYPE_DICTIONARY:
			continue
		var ing_id := str(ing.get("id", ""))
		var qty := float(maxi(1, int(ing.get("qty", 1))))
		var r_stats := {"oq": 500, "cd": 500, "pe": 500, "ma": 500, "sr": 500}
		for item in inv:
			if typeof(item) == TYPE_DICTIONARY and str(item.get("id", "")) == ing_id:
				if typeof(item.get("resource_stats")) == TYPE_DICTIONARY:
					r_stats = item["resource_stats"]
				break
		sum_oq += float(r_stats.get("oq", 500)) * qty
		sum_cd += float(r_stats.get("cd", 500)) * qty
		sum_pe += float(r_stats.get("pe", 500)) * qty
		sum_ma += float(r_stats.get("ma", 500)) * qty
		sum_sr += float(r_stats.get("sr", 500)) * qty
		total_weight += qty

	if total_weight > 0.0:
		avg["oq"] = sum_oq / total_weight
		avg["cd"] = sum_cd / total_weight
		avg["pe"] = sum_pe / total_weight
		avg["ma"] = sum_ma / total_weight
		avg["sr"] = sum_sr / total_weight
	return avg


func _attach_crafted_item_stats(player: String, output_id: String, item_stats: Dictionary, serial_str: String) -> void:
	if economy == null or output_id.is_empty():
		return
	var p: Dictionary = economy._player(player)
	var inv: Array = p.get("inventory", [])
	for item in inv:
		if typeof(item) == TYPE_DICTIONARY and str(item.get("id", "")) == output_id:
			item["crafted_by"] = player
			item["serial"] = serial_str
			item["item_stats"] = item_stats.duplicate(true)
			break
	economy._save_players()


func assemble_at_bench(
	player: String,
	schematic_id: String,
	entity_pos: Vector3 = Vector3.ZERO,
	max_bench_dist: float = 8.0
) -> Dictionary:
	var p_name := player.strip_edges()
	if p_name.is_empty():
		p_name = "Voyageur"
	var sid := schematic_id.strip_edges()
	if not schematics_by_id.has(sid):
		return {
			"ok": false,
			"error": "unknown_schematic",
			"schematic_id": sid,
		}
	if economy == null:
		return {
			"ok": false,
			"error": "economy_unavailable",
		}

	var sc: Dictionary = schematics_by_id[sid]
	var requires_bench := bool(sc.get("requires_bench", true))
	var bench_info := {"near": false, "anchor": {}, "distance": INF}

	if requires_bench:
		if collision == null or not collision.has_method("is_near_craft_bench"):
			return {
				"ok": false,
				"error": "collision_unavailable",
			}
		bench_info = collision.is_near_craft_bench(entity_pos, max_bench_dist)
		if not bool(bench_info.get("near", false)):
			return {
				"ok": false,
				"error": "not_near_craft_bench",
				"hint": "Approche-toi d'un établi d'assemblage mécatronique (ex. Hangar Dépôt Nord).",
				"schematic_id": sid,
				"distance": bench_info.get("distance", INF),
			}

	# Évalue les statistiques des ressources AVANT consommation
	var res_avg := _compute_resource_averages(p_name, sc)

	# Délègue la vérification déterministe de compétence + consommation d'ingrédients à HubEconomy
	var craft_res: Dictionary = economy.craft_combine(p_name, sid)
	if not bool(craft_res.get("ok", false)):
		return craft_res

	var mods := {"assembly_bonus": 10, "experimentation_points": 2}
	if skills != null and skills.has_method("compute_skill_mods"):
		mods = skills.compute_skill_mods(p_name)

	# Calcul pondéré SWG Pre-CU (Assembly Phase)
	var weighted_score: float = (
		0.50 * float(res_avg["oq"])
		+ 0.25 * float(res_avg["cd"])
		+ 0.15 * float(res_avg["ma"])
		+ 0.10 * float(res_avg["sr"])
	) / 10.0
	var base_quality_pct := clampf(
		snappedf(weighted_score * 0.72 + float(mods.get("assembly_bonus", 10)) * 0.4, 0.1),
		10.0,
		92.0
	)
	var base_power := int(round(20.0 + (float(res_avg["oq"]) * 0.06) + (float(res_avg["pe"]) * 0.04)))
	var base_durability := int(round(100.0 + (float(res_avg["sr"]) * 0.25) + (float(res_avg["oq"]) * 0.15)))

	_serial_seq += 1
	var serial_str := "LH-%d" % _serial_seq
	var out_dict: Dictionary = sc.get("output", {}) if typeof(sc.get("output")) == TYPE_DICTIONARY else {}
	var output_item_id := str(out_dict.get("id", sid))

	var item_stats := {
		"quality_pct": base_quality_pct,
		"power": base_power,
		"durability": base_durability,
		"resource_oq": int(round(float(res_avg["oq"]))),
		"experimented_times": 0,
	}
	_attach_crafted_item_stats(p_name, output_item_id, item_stats, serial_str)

	var exp_points := maxi(2, int(mods.get("experimentation_points", 2)))
	var session_id := "exp_%s_%d" % [p_name.to_lower(), _serial_seq]
	var exp_session := {
		"session_id": session_id,
		"player": p_name,
		"schematic_id": sid,
		"output_item_id": output_item_id,
		"serial": serial_str,
		"remaining_points": exp_points,
		"max_points": exp_points,
		"attributes": item_stats.duplicate(true),
		"history": [],
	}
	experiment_sessions[session_id] = exp_session

	if skills != null and skills.has_method("grant_xp"):
		skills.grant_xp(p_name, "xp_artisanat", 80)

	var anchor: Dictionary = bench_info.get("anchor", {}) if typeof(bench_info.get("anchor")) == TYPE_DICTIONARY else {}
	var snap_pos: Vector3 = anchor.get("pos", entity_pos) if not anchor.is_empty() else entity_pos
	var craft_time_sec := float(sc.get("craft_time_sec", 3.5))
	var state := {
		"player": p_name,
		"schematic_id": sid,
		"anchor_id": str(anchor.get("id", "field_craft")),
		"anchor_label": str(anchor.get("label", "Assemblage terrain")),
		"snap_pos": [snap_pos.x, snap_pos.y, snap_pos.z],
		"posture": "craft",
		"craft_time_sec": craft_time_sec,
		"started_at": Time.get_unix_time_from_system(),
	}
	active_craft_states[p_name] = state

	var out := craft_res.duplicate(true)
	out["schematic_id"] = sid
	out["craft_time_sec"] = craft_time_sec
	out["triplon_state"] = state
	out["bench_anchor_id"] = state["anchor_id"]
	out["posture"] = "craft"
	out["snap_pos"] = state["snap_pos"]
	out["serial"] = serial_str
	out["item_stats"] = item_stats
	out["experiment_session"] = exp_session.duplicate(true)
	return out


func experiment(
	player: String,
	session_id: String,
	attribute_line: String,
	points_to_spend: int,
	deterministic_roll: float = -1.0
) -> Dictionary:
	var p_name := player.strip_edges()
	if p_name.is_empty():
		p_name = "Voyageur"
	var sess_id := session_id.strip_edges()
	if not experiment_sessions.has(sess_id):
		return {"ok": false, "error": "unknown_experiment_session", "session_id": sess_id}

	var sess: Dictionary = experiment_sessions[sess_id]
	if str(sess.get("player", "")) != p_name:
		return {"ok": false, "error": "not_session_owner", "session_id": sess_id}

	var pts := maxi(1, points_to_spend)
	var rem := int(sess.get("remaining_points", 0))
	if pts > rem:
		return {
			"ok": false,
			"error": "insufficient_experimentation_points",
			"requested": pts,
			"remaining_points": rem,
		}

	var attr := attribute_line.strip_edges().to_lower()
	if attr not in ["power", "durability", "quality_pct"]:
		return {"ok": false, "error": "invalid_attribute_line", "attribute": attr}

	var roll := deterministic_roll if deterministic_roll >= 0.0 else _rng.randf()
	var outcome := "great_success"
	var mult := 1.0
	if roll >= 0.88:
		outcome = "amazing_success"
		mult = 1.45
	elif roll >= 0.35:
		outcome = "great_success"
		mult = 1.0
	elif roll >= 0.10:
		outcome = "moderate_success"
		mult = 0.55
	else:
		outcome = "critical_failure"
		mult = -0.50

	var attrs: Dictionary = sess["attributes"]
	var delta := 0.0
	if attr == "quality_pct":
		delta = snappedf(float(pts) * 4.5 * mult, 0.1)
		attrs["quality_pct"] = clampf(float(attrs.get("quality_pct", 50.0)) + delta, 5.0, 99.9)
	elif attr == "power":
		delta = round(float(pts) * 6.0 * mult)
		attrs["power"] = maxi(5, int(attrs.get("power", 25)) + int(delta))
	elif attr == "durability":
		delta = round(float(pts) * 18.0 * mult)
		attrs["durability"] = maxi(20, int(attrs.get("durability", 120)) + int(delta))

	attrs["experimented_times"] = int(attrs.get("experimented_times", 0)) + 1
	sess["remaining_points"] = rem - pts
	var hist: Array = sess.get("history", [])
	hist.append({
		"attribute": attr,
		"points": pts,
		"outcome": outcome,
		"delta": delta,
	})
	sess["history"] = hist

	var output_item_id := str(sess.get("output_item_id", ""))
	var serial_str := str(sess.get("serial", "LH-1000"))
	_attach_crafted_item_stats(p_name, output_item_id, attrs, serial_str)

	var xp_bonus := pts * (35 if mult > 0.0 else 15)
	if skills != null and skills.has_method("grant_xp"):
		skills.grant_xp(p_name, "xp_artisanat", xp_bonus)

	if economy != null:
		economy.log_session_event(
			p_name,
			"craft_experiment",
			"Expérimentation %s (%d pts -> %s)" % [attr, pts, outcome],
			{"session_id": sess_id, "attribute": attr, "outcome": outcome, "delta": delta}
		)

	return {
		"ok": true,
		"session_id": sess_id,
		"player": p_name,
		"attribute": attr,
		"points_spent": pts,
		"remaining_points": int(sess["remaining_points"]),
		"outcome": outcome,
		"delta": delta,
		"item_stats": attrs.duplicate(true),
		"xp_gained": xp_bonus,
	}
