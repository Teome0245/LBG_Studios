extends RefCounted
class_name HubSkills
## Ticket 4.1 (O2 Phase 4 SWG Pre-CU) — Arbres de Compétences 4×4 Boxes (Novice -> 4 Branches -> Master)
## & Plafond de 250 Skill Points sous autorité serveur Godot (`prime-hub`).

const _HubPaths := preload("res://scripts/hub_paths.gd")

const MAX_SKILL_POINTS := 250
const COST_SP_NOVICE := 15
const COST_SP_TIER := [2, 3, 4, 5]
const COST_SP_MASTER := 6

const COST_XP_NOVICE := 0
const COST_XP_TIER := [1000, 2500, 5000, 10000]
const COST_XP_MASTER := 20000

const DEFAULT_XP_POOLS := {
	"xp_artisanat": 1500,
	"xp_prospection": 1500,
	"xp_medecine": 1000,
	"xp_scene": 1000,
	"xp_combat": 1500,
	"xp_civique": 1000,
	"xp_pilotage": 1000,
}

var economy = null
var professions_by_id: Dictionary = {}
var box_index: Dictionary = {}  # box_id -> {profession_id, kind, branch_id, tier, requires: Array, sp_cost, xp_type, xp_cost}


func setup(economy_svc = null) -> void:
	economy = economy_svc
	reload_catalog()


func reload_catalog(custom_path: String = "") -> void:
	professions_by_id.clear()
	box_index.clear()
	var path := custom_path
	if path.is_empty():
		path = _HubPaths.data_file("catalog_skills.json")
	var raw: Variant = _HubPaths.read_json(path)
	if typeof(raw) != TYPE_DICTIONARY:
		return
	var items: Variant = raw.get("items", [])
	if typeof(items) != TYPE_ARRAY:
		return
	for it in items:
		if typeof(it) != TYPE_DICTIONARY:
			continue
		if str(it.get("kind", "")) != "profession":
			continue
		var prof_id := str(it.get("id", "")).strip_edges()
		var boxes_dict: Variant = it.get("boxes", null)
		if prof_id.is_empty() or typeof(boxes_dict) != TYPE_DICTIONARY:
			continue
		var prof_copy: Dictionary = (it as Dictionary).duplicate(true)
		professions_by_id[prof_id] = prof_copy
		var xp_type := str(prof_copy.get("xp", "xp_artisanat"))
		var novice_id := str(boxes_dict.get("novice", "%s_novice" % prof_id))
		var master_id := str(boxes_dict.get("master", "%s_master" % prof_id))

		box_index[novice_id] = {
			"id": novice_id,
			"profession_id": prof_id,
			"profession_name": str(prof_copy.get("name", prof_id)),
			"kind": "novice",
			"branch_id": "",
			"tier": 0,
			"requires": [],
			"sp_cost": COST_SP_NOVICE,
			"xp_type": xp_type,
			"xp_cost": COST_XP_NOVICE,
		}

		var tier4_boxes: Array = []
		var branches: Variant = boxes_dict.get("branches", [])
		if typeof(branches) == TYPE_ARRAY:
			for br in branches:
				if typeof(br) != TYPE_DICTIONARY:
					continue
				var br_id := str(br.get("id", ""))
				var br_boxes: Variant = br.get("boxes", [])
				if typeof(br_boxes) != TYPE_ARRAY:
					continue
				var prev_box := novice_id
				for idx in range(br_boxes.size()):
					var bid := str(br_boxes[idx])
					var tier_num := idx + 1
					var sp_cost: int = COST_SP_TIER[mini(idx, COST_SP_TIER.size() - 1)]
					var xp_cost: int = COST_XP_TIER[mini(idx, COST_XP_TIER.size() - 1)]
					box_index[bid] = {
						"id": bid,
						"profession_id": prof_id,
						"profession_name": str(prof_copy.get("name", prof_id)),
						"kind": "branch",
						"branch_id": br_id,
						"branch_label": str(br.get("label", br_id)),
						"tier": tier_num,
						"requires": [prev_box],
						"sp_cost": sp_cost,
						"xp_type": xp_type,
						"xp_cost": xp_cost,
					}
					prev_box = bid
					if idx == br_boxes.size() - 1:
						tier4_boxes.append(bid)

		box_index[master_id] = {
			"id": master_id,
			"profession_id": prof_id,
			"profession_name": str(prof_copy.get("name", prof_id)),
			"kind": "master",
			"branch_id": "master",
			"tier": 5,
			"requires": tier4_boxes,
			"sp_cost": COST_SP_MASTER,
			"xp_type": xp_type,
			"xp_cost": COST_XP_MASTER,
		}


func _ensure_player_skill_state(player: String) -> Dictionary:
	if economy == null:
		return {}
	var p: Dictionary = economy._player(player)
	if typeof(p.get("skills")) != TYPE_ARRAY:
		p["skills"] = []
	var skills: Array = p["skills"]
	# Synchronisation rétrocompatible r1 -> novice box
	var legacy_map := {
		"artisan_rue_r1": "artisan_novice",
		"prospecteur_r1": "prospecteur_novice",
		"medecine_camp_r1": "medecin_novice",
		"pilotage_shuttle_r1": "shuttle_novice",
		"scene_danse_r1": "scene_novice",
		"quartier_r1": "citoyen_novice",
	}
	for leg_key in legacy_map.keys():
		if leg_key in skills and legacy_map[leg_key] not in skills:
			skills.append(legacy_map[leg_key])
	if typeof(p.get("xp_pools")) != TYPE_DICTIONARY:
		p["xp_pools"] = DEFAULT_XP_POOLS.duplicate(true)
	else:
		var xp_pools: Dictionary = p["xp_pools"]
		for k in DEFAULT_XP_POOLS.keys():
			if not xp_pools.has(k):
				xp_pools[k] = DEFAULT_XP_POOLS[k]
	return p


func has_box(player: String, box_id: String) -> bool:
	var p := _ensure_player_skill_state(player)
	if p.is_empty():
		return false
	var sk_list: Array = p.get("skills", [])
	return box_id in sk_list or str(box_id) in sk_list


func add_xp(player: String, xp_type: String, amount: int) -> Dictionary:
	return grant_xp(player, xp_type, amount)


func used_skill_points(player: String) -> int:
	var p := _ensure_player_skill_state(player)
	if p.is_empty():
		return 0
	var skills: Array = p.get("skills", [])
	var total := 0
	for s in skills:
		var bid := str(s)
		if box_index.has(bid):
			total += int((box_index[bid] as Dictionary).get("sp_cost", 0))
	return total


func compute_skill_mods(player: String) -> Dictionary:
	var p := _ensure_player_skill_state(player)
	var skills: Array = p.get("skills", []) if not p.is_empty() else []
	var mods := {
		"assembly_bonus": 0,
		"experimentation_points": 0,
		"survey_range": 32.0,
		"survey_resolution": 1,
		"wound_heal_efficiency": 10,
		"fatigue_heal_power": 8,
		"harvester_slots": 1,
		"combat_accuracy": 0,
		"combat_defense": 0,
	}
	for s in skills:
		var bid := str(s)
		if bid == "artisan_novice":
			mods["assembly_bonus"] += 10
			mods["experimentation_points"] += 2
		elif bid.begins_with("artisan_"):
			mods["assembly_bonus"] += 6
			mods["experimentation_points"] += 1
			if bid == "artisan_master":
				mods["experimentation_points"] += 4
				mods["harvester_slots"] += 2
		elif bid == "prospecteur_novice":
			mods["survey_range"] += 16.0
		elif bid.begins_with("prospecteur_"):
			mods["survey_range"] += 12.0
			mods["survey_resolution"] += 1
			if bid == "prospecteur_master":
				mods["harvester_slots"] += 2
		elif bid == "medecin_novice":
			mods["wound_heal_efficiency"] += 15
		elif bid.begins_with("medecin_"):
			mods["wound_heal_efficiency"] += 12
		elif bid == "scene_novice":
			mods["fatigue_heal_power"] += 10
		elif bid.begins_with("scene_"):
			mods["fatigue_heal_power"] += 8
		elif bid.begins_with("poing_") or bid.begins_with("visee_"):
			mods["combat_accuracy"] += 5
			mods["combat_defense"] += 4
		elif bid.begins_with("citoyen_"):
			mods["harvester_slots"] += 1
	return mods


func grant_xp(player: String, xp_type: String, amount: int) -> Dictionary:
	var p := _ensure_player_skill_state(player)
	if p.is_empty():
		return {"ok": false, "error": "economy_unavailable"}
	var key := xp_type.strip_edges()
	if key.is_empty():
		key = "xp_artisanat"
	var add_val := maxi(0, amount)
	var pools: Dictionary = p["xp_pools"]
	pools[key] = int(pools.get(key, 0)) + add_val
	economy._save_players()
	return {
		"ok": true,
		"player": player,
		"xp_type": key,
		"added": add_val,
		"new_total": int(pools[key]),
	}


func learn_box(player: String, box_id: String, bypass_xp: bool = false) -> Dictionary:
	var p := _ensure_player_skill_state(player)
	if p.is_empty():
		return {"ok": false, "error": "economy_unavailable"}
	var bid := box_id.strip_edges()
	if not box_index.has(bid):
		return {"ok": false, "error": "unknown_skill_box", "box_id": bid}

	var skills: Array = p["skills"]
	if bid in skills:
		return {"ok": false, "error": "already_learned", "box_id": bid}

	var meta: Dictionary = box_index[bid]
	var reqs: Array = meta.get("requires", [])
	var missing_reqs: Array = []
	for req in reqs:
		if str(req) not in skills:
			missing_reqs.append(str(req))
	if not missing_reqs.is_empty():
		return {
			"ok": false,
			"error": "missing_prerequisites",
			"box_id": bid,
			"missing": missing_reqs,
		}

	var sp_cost := int(meta.get("sp_cost", 0))
	var current_sp := used_skill_points(player)
	if current_sp + sp_cost > MAX_SKILL_POINTS:
		return {
			"ok": false,
			"error": "insufficient_skill_points",
			"box_id": bid,
			"required_sp": sp_cost,
			"available_sp": MAX_SKILL_POINTS - current_sp,
			"max_sp": MAX_SKILL_POINTS,
		}

	var xp_type := str(meta.get("xp_type", "xp_artisanat"))
	var xp_cost := int(meta.get("xp_cost", 0))
	var pools: Dictionary = p["xp_pools"]
	var have_xp := int(pools.get(xp_type, 0))
	if not bypass_xp and have_xp < xp_cost:
		return {
			"ok": false,
			"error": "insufficient_xp",
			"box_id": bid,
			"xp_type": xp_type,
			"required_xp": xp_cost,
			"available_xp": have_xp,
		}

	if not bypass_xp and xp_cost > 0:
		pools[xp_type] = have_xp - xp_cost

	skills.append(bid)
	# Compatibilité inverse avec les checks recettes M10
	if bid == "artisan_novice" and "artisan_rue_r1" not in skills:
		skills.append("artisan_rue_r1")
	elif bid == "prospecteur_novice" and "prospecteur_r1" not in skills:
		skills.append("prospecteur_r1")
	elif bid == "medecin_novice" and "medecine_camp_r1" not in skills:
		skills.append("medecine_camp_r1")

	if str(meta.get("kind", "")) == "master":
		p["title"] = "Maître %s" % str(meta.get("profession_name", meta.get("profession_id", "")))

	economy.log_session_event(
		player,
		"skill_learn",
		"Apprentissage Pre-CU : %s (%d SP)" % [bid, sp_cost],
		{"box_id": bid, "sp_cost": sp_cost, "xp_type": xp_type}
	)
	economy._save_players()

	return {
		"ok": true,
		"player": player,
		"learned_box": bid,
		"sp_cost": sp_cost,
		"used_skill_points": used_skill_points(player),
		"available_skill_points": MAX_SKILL_POINTS - used_skill_points(player),
		"xp_pools": pools.duplicate(true),
		"skill_mods": compute_skill_mods(player),
		"title": str(p.get("title", "")),
	}


func surrender_box(player: String, box_id: String) -> Dictionary:
	var p := _ensure_player_skill_state(player)
	if p.is_empty():
		return {"ok": false, "error": "economy_unavailable"}
	var bid := box_id.strip_edges()
	var skills: Array = p["skills"]
	if bid not in skills:
		return {"ok": false, "error": "skill_not_learned", "box_id": bid}

	# Empêche d'abandonner une box dont dépend une box supérieure encore apprise
	var dependents: Array = []
	for learned in skills:
		var l_str := str(learned)
		if l_str == bid or not box_index.has(l_str):
			continue
		var reqs: Array = (box_index[l_str] as Dictionary).get("requires", [])
		if bid in reqs:
			dependents.append(l_str)
	if not dependents.is_empty():
		return {
			"ok": false,
			"error": "has_dependent_boxes",
			"box_id": bid,
			"dependents": dependents,
		}

	skills.erase(bid)
	economy.log_session_event(player, "skill_surrender", "Abandon de box : %s" % bid, {"box_id": bid})
	economy._save_players()
	return {
		"ok": true,
		"player": player,
		"surrendered_box": bid,
		"used_skill_points": used_skill_points(player),
		"available_skill_points": MAX_SKILL_POINTS - used_skill_points(player),
		"skill_mods": compute_skill_mods(player),
	}


func player_tree_snapshot(player: String) -> Dictionary:
	var p := _ensure_player_skill_state(player)
	var skills: Array = p.get("skills", []) if not p.is_empty() else []
	var used_sp := used_skill_points(player)
	var profs_out: Array = []
	for prof_id in professions_by_id.keys():
		var prof: Dictionary = (professions_by_id[prof_id] as Dictionary).duplicate(true)
		var b_dict: Dictionary = prof.get("boxes", {})
		var nov_id := str(b_dict.get("novice", ""))
		var mas_id := str(b_dict.get("master", ""))
		prof["novice_learned"] = nov_id in skills
		prof["master_learned"] = mas_id in skills
		profs_out.append(prof)
	return {
		"ok": true,
		"player": player,
		"max_skill_points": MAX_SKILL_POINTS,
		"used_skill_points": used_sp,
		"available_skill_points": MAX_SKILL_POINTS - used_sp,
		"learned_boxes": skills.duplicate(),
		"xp_pools": (p.get("xp_pools", DEFAULT_XP_POOLS) as Dictionary).duplicate(true),
		"skill_mods": compute_skill_mods(player),
		"title": str(p.get("title", "")),
		"professions": profs_out,
	}

