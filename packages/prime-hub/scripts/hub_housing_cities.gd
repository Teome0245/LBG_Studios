extends RefCounted
class_name HubHousingCities
## Système SWG Pre-CU : Housing Libre, Décoration Intérieure, Actes de Propriété
## et Villes de Joueurs (Player Cities & Municipalités) — Lost Heaven (Ticket 2).

const _HubPaths := preload("res://scripts/hub_paths.gd")

# Modèles de structures constructibles
const STRUCTURE_TEMPLATES := {
	"deed_tente_nomade": {
		"id": "deed_tente_nomade",
		"label": "Tente Nomade en Toile",
		"category": "camp",
		"width": 8.0,
		"depth": 8.0,
		"max_decorations": 15,
		"daily_maintenance": 0,
		"cost_credits": 200,
		"required_skill": "artisan_novice"
	},
	"deed_maison_sable_p": {
		"id": "deed_maison_sable_p",
		"label": "Petite Maison en Pisé",
		"category": "house",
		"width": 14.0,
		"depth": 14.0,
		"max_decorations": 60,
		"daily_maintenance": 15,
		"cost_credits": 1500,
		"required_skill": "artisan_novice"
	},
	"deed_bunker_metal_m": {
		"id": "deed_bunker_metal_m",
		"label": "Bunker Métallique Moyen",
		"category": "house",
		"width": 22.0,
		"depth": 20.0,
		"max_decorations": 150,
		"daily_maintenance": 35,
		"cost_credits": 5000,
		"required_skill": "artisan_pieces_02"
	},
	"deed_cantina_joueur": {
		"id": "deed_cantina_joueur",
		"label": "Cantina & Scène Privée",
		"category": "civic",
		"width": 30.0,
		"depth": 28.0,
		"max_decorations": 300,
		"daily_maintenance": 80,
		"cost_credits": 12000,
		"required_skill": "citoyen_novice"
	},
	"deed_hall_guilde": {
		"id": "deed_hall_guilde",
		"label": "Hall d'Organisation / Guilde",
		"category": "guild",
		"width": 36.0,
		"depth": 36.0,
		"max_decorations": 500,
		"daily_maintenance": 120,
		"cost_credits": 25000,
		"required_skill": "citoyen_badge_02"
	}
}

var sim = null
var economy = null
var skills = null
var collision = null

var structures_by_id: Dictionary = {}
var cities_by_id: Dictionary = {}

var _next_struct_id := 1001
var _next_deco_id := 5001
var _next_city_id := 6001


func setup(parent_sim, economy_svc = null, skills_svc = null, collision_svc = null) -> void:
	sim = parent_sim
	economy = economy_svc
	skills = skills_svc
	collision = collision_svc


# ==============================================================================
# SECTION 1 : ACTES & DÉPLOIEMENT LIBRE DE STRUCTURES (HOUSING)
# ==============================================================================

func deploy_structure(
	player: String,
	deed_id: String,
	x: float,
	z: float,
	yaw_deg: float = 0.0
) -> Dictionary:
	var did := deed_id.strip_edges()
	if not STRUCTURE_TEMPLATES.has(did):
		return {"ok": false, "error": "unknown_structure_deed", "deed_id": did}

	var tmpl: Dictionary = STRUCTURE_TEMPLATES[did]

	# Restriction urbaine (Lost Heaven intra-muros inconstructible)
	var dist_lh := Vector2(x - 5100.0, z - (-800.0)).length()
	if dist_lh < 130.0:
		return {
			"ok": false,
			"error": "too_close_to_city_core",
			"distance_m": snappedf(dist_lh, 0.1),
			"min_m": 130.0,
			"hint": "La place forte de Lost Heaven est une zone protégée. Pose ta structure dans les dunes périphériques."
		}

	# Vérifier compétences
	var req_skill := str(tmpl.get("required_skill", ""))
	if skills != null and not req_skill.is_empty():
		var has_skill: bool = bool(skills.has_box(player, req_skill) or skills.has_box(player, "artisan_novice") or skills.has_box(player, "citoyen_novice"))
		if not has_skill:
			return {
				"ok": false,
				"error": "skill_required",
				"required_skill": req_skill
			}

	# Vérifier le deed dans l'inventaire ou le solde de crédits
	var cost := int(tmpl.get("cost_credits", 0))
	if economy != null:
		var p: Dictionary = economy._player(player)
		var inv_deed: int = int(economy._inv_qty(p, did))
		if inv_deed > 0:
			economy._consume(p, did, 1)
		else:
			var cr := int(p.get("credits", 0))
			if cr < cost:
				return {
					"ok": false,
					"error": "insufficient_deed_or_credits",
					"cost": cost,
					"available": cr
				}
			p["credits"] = cr - cost

	# Vérifier absence de chevauchement avec une autre structure
	var w: float = float(tmpl.get("width", 10.0))
	var d: float = float(tmpl.get("depth", 10.0))
	var half_w := w * 0.5
	var half_d := d * 0.5

	for sid in structures_by_id.keys():
		var other: Dictionary = structures_by_id[sid]
		var op: Vector3 = other.get("pos", Vector3.ZERO)
		var ow: float = float(other.get("width", 10.0))
		var od: float = float(other.get("depth", 10.0))
		var min_clearance := (maxf(w, d) + maxf(ow, od)) * 0.5 + 2.0
		var dist_other := Vector2(op.x - x, op.z - z).length()
		if dist_other < min_clearance:
			return {
				"ok": false,
				"error": "overlapping_structure",
				"conflicting_structure_id": sid,
				"distance_m": snappedf(dist_other, 0.1),
				"min_required_m": snappedf(min_clearance, 0.1)
			}

	var struct_id := "struct_h_%d" % _next_struct_id
	_next_struct_id += 1

	var entry := {
		"struct_id": struct_id,
		"deed_id": did,
		"label": str(tmpl.get("label", "Structure")),
		"category": str(tmpl.get("category", "house")),
		"owner": player,
		"pos": Vector3(x, 0.15, z),
		"yaw_deg": yaw_deg,
		"width": w,
		"depth": d,
		"max_decorations": int(tmpl.get("max_decorations", 50)),
		"daily_maintenance": int(tmpl.get("daily_maintenance", 10)),
		"maintenance_pool": 100, # 100 crédits d'avance
		"condition_pct": 100,
		"is_public": true,
		"admin_list": [player],
		"entry_list": [],
		"ban_list": [],
		"decorations": [],
		"created_at": Time.get_unix_time_from_system()
	}
	structures_by_id[struct_id] = entry

	# Enregistrement dans les entités du simulateur pour affichage
	if sim != null:
		sim.entities[struct_id] = {
			"eid": struct_id,
			"kind": "structure",
			"name": entry["label"],
			"owner": player,
			"pos": entry["pos"],
			"width": w,
			"depth": d,
			"target": Vector3.ZERO,
			"goal": "structure_idle",
			"active": true
		}

	if sim != null and sim.has_method("_stream"):
		sim._stream(
			"structure.constructed",
			"%s a érigé : « %s » à (%.0f, %.0f)." % [player, entry["label"], x, z],
			player,
			"wild",
			{"struct_id": struct_id, "label": entry["label"]}
		)

	return {
		"ok": true,
		"struct_id": struct_id,
		"structure": entry.duplicate(true)
	}


func get_structure(struct_id: String) -> Dictionary:
	var sid := struct_id.strip_edges()
	if structures_by_id.has(sid):
		return (structures_by_id[sid] as Dictionary).duplicate(true)
	return {}


func list_player_structures(player: String) -> Array:
	var out: Array = []
	for sid in structures_by_id.keys():
		var s: Dictionary = structures_by_id[sid]
		if str(s.get("owner", "")) == player:
			out.append(s.duplicate(true))
	return out


func list_structures_near(x: float, z: float, radius_m: float = 100.0) -> Array:
	var out: Array = []
	for sid in structures_by_id.keys():
		var s: Dictionary = structures_by_id[sid]
		var p: Vector3 = s.get("pos", Vector3.ZERO)
		var d := Vector2(p.x - x, p.z - z).length()
		if d <= radius_m:
			var copy := s.duplicate(true)
			copy["distance_m"] = snappedf(d, 0.1)
			out.append(copy)
	return out


# ==============================================================================
# SECTION 2 : DROITS D'ACCÈS & PERMISSIONS (ACCESS CONTROL LIST)
# ==============================================================================

func set_structure_privacy(player: String, struct_id: String, is_public: bool) -> Dictionary:
	var sid := struct_id.strip_edges()
	if not structures_by_id.has(sid):
		return {"ok": false, "error": "structure_not_found"}

	var st: Dictionary = structures_by_id[sid]
	var admins: Array = st.get("admin_list", [])
	if str(st.get("owner", "")) != player and not player in admins:
		return {"ok": false, "error": "permission_denied"}

	st["is_public"] = is_public
	return {"ok": true, "struct_id": sid, "is_public": is_public}


func manage_structure_acl(
	player: String,
	struct_id: String,
	action: String,
	target_player: String
) -> Dictionary:
	var sid := struct_id.strip_edges()
	if not structures_by_id.has(sid):
		return {"ok": false, "error": "structure_not_found"}

	var st: Dictionary = structures_by_id[sid]
	var admins: Array = st.get("admin_list", [])
	if str(st.get("owner", "")) != player and not player in admins:
		return {"ok": false, "error": "permission_denied"}

	var target := target_player.strip_edges()
	if target.is_empty():
		return {"ok": false, "error": "target_player_required"}

	match action.to_lower():
		"add_admin":
			if not target in admins: admins.append(target)
		"remove_admin":
			admins.erase(target)
		"add_entry":
			var entries: Array = st.get("entry_list", [])
			if not target in entries: entries.append(target)
			st["entry_list"] = entries
		"remove_entry":
			var entries2: Array = st.get("entry_list", [])
			entries2.erase(target)
			st["entry_list"] = entries2
		"add_ban":
			var bans: Array = st.get("ban_list", [])
			if not target in bans: bans.append(target)
			st["ban_list"] = bans
		"remove_ban":
			var bans2: Array = st.get("ban_list", [])
			bans2.erase(target)
			st["ban_list"] = bans2
		_:
			return {"ok": false, "error": "invalid_acl_action", "hint": "add_admin, remove_admin, add_entry, remove_entry, add_ban, remove_ban"}

	st["admin_list"] = admins
	return {
		"ok": true,
		"struct_id": sid,
		"action": action,
		"target": target,
		"admin_list": st.get("admin_list", []),
		"entry_list": st.get("entry_list", []),
		"ban_list": st.get("ban_list", [])
	}


func can_enter_structure(player: String, struct_id: String) -> bool:
	var sid := struct_id.strip_edges()
	if not structures_by_id.has(sid):
		return false

	var st: Dictionary = structures_by_id[sid]
	var bans: Array = st.get("ban_list", [])
	if player in bans:
		return false

	if str(st.get("owner", "")) == player:
		return true

	var admins: Array = st.get("admin_list", [])
	if player in admins:
		return true

	if bool(st.get("is_public", true)):
		return true

	var entries: Array = st.get("entry_list", [])
	return player in entries


func deposit_maintenance(player: String, struct_id: String, credits_amount: int) -> Dictionary:
	if economy == null:
		return {"ok": false, "error": "economy_unavailable"}

	var sid := struct_id.strip_edges()
	if not structures_by_id.has(sid):
		return {"ok": false, "error": "structure_not_found"}

	var st: Dictionary = structures_by_id[sid]
	var p: Dictionary = economy._player(player)
	var cr := int(p.get("credits", 0))
	if cr < credits_amount or credits_amount <= 0:
		return {"ok": false, "error": "insufficient_credits", "available": cr}

	p["credits"] = cr - credits_amount
	st["maintenance_pool"] = int(st.get("maintenance_pool", 0)) + credits_amount

	return {
		"ok": true,
		"struct_id": sid,
		"deposited": credits_amount,
		"maintenance_pool": int(st["maintenance_pool"]),
		"player_credits": int(p["credits"])
	}


# ==============================================================================
# SECTION 3 : DÉCORATION INTÉRIEURE LIBRE (FREEFORM DECORATION)
# ==============================================================================

func place_decoration(
	player: String,
	struct_id: String,
	item_id: String,
	local_x: float,
	local_y: float,
	local_z: float,
	rot_yaw: float = 0.0,
	item_name: String = ""
) -> Dictionary:
	var sid := struct_id.strip_edges()
	if not structures_by_id.has(sid):
		return {"ok": false, "error": "structure_not_found"}

	var st: Dictionary = structures_by_id[sid]
	var admins: Array = st.get("admin_list", [])
	if str(st.get("owner", "")) != player and not player in admins:
		return {"ok": false, "error": "permission_denied"}

	var decos: Array = st.get("decorations", [])
	var max_d := int(st.get("max_decorations", 50))
	if decos.size() >= max_d:
		return {
			"ok": false,
			"error": "max_decorations_reached",
			"max": max_d,
			"current": decos.size()
		}

	# Vérifier et consommer l'objet de l'inventaire
	if economy != null:
		var p: Dictionary = economy._player(player)
		var inv_q: int = int(economy._inv_qty(p, item_id))
		if inv_q <= 0:
			return {"ok": false, "error": "item_not_in_inventory", "item_id": item_id}
		economy._consume(p, item_id, 1)

	var deco_id := "deco_%d" % _next_deco_id
	_next_deco_id += 1

	var iname := item_name
	if iname.is_empty():
		iname = item_id.capitalize().replace("_", " ")

	var deco_entry := {
		"deco_id": deco_id,
		"item_id": item_id,
		"item_name": iname,
		"local_pos": {"x": local_x, "y": local_y, "z": local_z},
		"rot_yaw": rot_yaw,
		"placed_by": player,
		"locked": true,
		"placed_at": Time.get_unix_time_from_system()
	}
	decos.append(deco_entry)
	st["decorations"] = decos

	return {
		"ok": true,
		"struct_id": sid,
		"deco_id": deco_id,
		"item_name": iname,
		"local_pos": deco_entry["local_pos"],
		"total_decorations": decos.size()
	}


func move_decoration(
	player: String,
	struct_id: String,
	deco_id: String,
	dx: float,
	dy: float,
	dz: float,
	d_yaw: float = 0.0
) -> Dictionary:
	var sid := struct_id.strip_edges()
	if not structures_by_id.has(sid):
		return {"ok": false, "error": "structure_not_found"}

	var st: Dictionary = structures_by_id[sid]
	var admins: Array = st.get("admin_list", [])
	if str(st.get("owner", "")) != player and not player in admins:
		return {"ok": false, "error": "permission_denied"}

	var decos: Array = st.get("decorations", [])
	for d in decos:
		if str(d.get("deco_id", "")) == deco_id:
			var lp: Dictionary = d.get("local_pos", {})
			lp["x"] = float(lp.get("x", 0.0)) + dx
			lp["y"] = float(lp.get("y", 0.0)) + dy
			lp["z"] = float(lp.get("z", 0.0)) + dz
			d["local_pos"] = lp
			d["rot_yaw"] = float(d.get("rot_yaw", 0.0)) + d_yaw
			return {
				"ok": true,
				"struct_id": sid,
				"deco_id": deco_id,
				"new_local_pos": lp,
				"new_rot_yaw": d["rot_yaw"]
			}

	return {"ok": false, "error": "decoration_not_found"}


func pickup_decoration(player: String, struct_id: String, deco_id: String) -> Dictionary:
	var sid := struct_id.strip_edges()
	if not structures_by_id.has(sid):
		return {"ok": false, "error": "structure_not_found"}

	var st: Dictionary = structures_by_id[sid]
	var admins: Array = st.get("admin_list", [])
	if str(st.get("owner", "")) != player and not player in admins:
		return {"ok": false, "error": "permission_denied"}

	var decos: Array = st.get("decorations", [])
	var target_idx := -1
	var target_deco: Dictionary = {}
	for i in range(decos.size()):
		if str(decos[i].get("deco_id", "")) == deco_id:
			target_idx = i
			target_deco = decos[i]
			break

	if target_idx < 0:
		return {"ok": false, "error": "decoration_not_found"}

	decos.remove_at(target_idx)
	st["decorations"] = decos

	# Rendre l'objet dans l'inventaire joueur
	if economy != null:
		var p: Dictionary = economy._player(player)
		economy._add_item(p, str(target_deco.get("item_id", "")), 1, str(target_deco.get("item_name", "")))

	return {
		"ok": true,
		"struct_id": sid,
		"deco_id": deco_id,
		"item_id": str(target_deco.get("item_id", "")),
		"remaining_decorations": decos.size()
	}


# ==============================================================================
# SECTION 4 : VILLES DE JOUEURS & MUNICIPALITÉS (PLAYER CITIES)
# ==============================================================================

func evaluate_city_tier(structure_count: int) -> Dictionary:
	if structure_count >= 35:
		return {"tier": 5, "name": "Cité Métropolitaine", "radius_m": 450.0, "max_civic": 8}
	elif structure_count >= 20:
		return {"tier": 4, "name": "Bourgade", "radius_m": 300.0, "max_civic": 5}
	elif structure_count >= 12:
		return {"tier": 3, "name": "Village", "radius_m": 200.0, "max_civic": 3}
	elif structure_count >= 6:
		return {"tier": 2, "name": "Hameau", "radius_m": 120.0, "max_civic": 2}
	elif structure_count >= 3:
		return {"tier": 1, "name": "Campement", "radius_m": 60.0, "max_civic": 1}
	return {"tier": 0, "name": "Zone Sauvage", "radius_m": 0.0, "max_civic": 0}


func found_player_city(
	founder: String,
	city_name: String,
	center_x: float,
	center_z: float
) -> Dictionary:
	var cname := city_name.strip_edges()
	if cname.is_empty():
		return {"ok": false, "error": "city_name_required"}

	# Compter les structures dans un rayon initial de 80m
	var local_structs := list_structures_near(center_x, center_z, 80.0)
	if local_structs.size() < 3:
		return {
			"ok": false,
			"error": "insufficient_structures_to_incorporate",
			"found": local_structs.size(),
			"required": 3,
			"hint": "Il faut au moins 3 structures de joueurs regroupées pour fonder une municipalité."
		}

	var tier_info := evaluate_city_tier(local_structs.size())
	var city_id := "city_%d" % _next_city_id
	_next_city_id += 1

	var citizens := [founder]
	for s in local_structs:
		var owner := str(s.get("owner", ""))
		if not owner.is_empty() and not owner in citizens:
			citizens.append(owner)

	var city_entry := {
		"city_id": city_id,
		"city_name": cname,
		"founder": founder,
		"mayor": founder,
		"center_pos": Vector3(center_x, 0.15, center_z),
		"radius_m": float(tier_info.get("radius_m", 60.0)),
		"tier": int(tier_info.get("tier", 1)),
		"tier_name": str(tier_info.get("name", "Campement")),
		"citizens": citizens,
		"treasury_credits": 500, # Dotation municipale initiale
		"property_tax": 5, # 5 cr par structure / cycle
		"sales_tax_pct": 2, # 2% sur les vendeurs locaux
		"civic_structures": [],
		"created_at": Time.get_unix_time_from_system()
	}
	cities_by_id[city_id] = city_entry

	if sim != null and sim.has_method("_stream"):
		sim._stream(
			"city.founded",
			"%s a fondé la cité de « %s » (Rang : %s, %d citoyens)." % [founder, cname, city_entry["tier_name"], citizens.size()],
			founder,
			"cities",
			{"city_id": city_id, "name": cname, "tier": city_entry["tier"]}
		)

	return {
		"ok": true,
		"city_id": city_id,
		"city": city_entry.duplicate(true)
	}


func get_city(city_id: String) -> Dictionary:
	var cid := city_id.strip_edges()
	if cities_by_id.has(cid):
		return (cities_by_id[cid] as Dictionary).duplicate(true)
	return {}


func hold_mayoral_election(
	city_id: String,
	votes_by_citizen: Dictionary
) -> Dictionary:
	var cid := city_id.strip_edges()
	if not cities_by_id.has(cid):
		return {"ok": false, "error": "city_not_found"}

	var city: Dictionary = cities_by_id[cid]
	var citizens: Array = city.get("citizens", [])

	# Décompte des votes valides
	var tally: Dictionary = {}
	for voter in votes_by_citizen.keys():
		if str(voter) in citizens:
			var candidate := str(votes_by_citizen[voter])
			tally[candidate] = int(tally.get(candidate, 0)) + 1

	var best_candidate := str(city.get("mayor", ""))
	var max_votes := -1
	for cand in tally.keys():
		if int(tally[cand]) > max_votes:
			max_votes = int(tally[cand])
			best_candidate = cand

	var old_mayor := str(city.get("mayor", ""))
	city["mayor"] = best_candidate

	if sim != null and sim.has_method("_stream"):
		sim._stream(
			"city.election",
			"Élection à %s : %s est élu Maire avec %d voix !" % [str(city.get("city_name", "")), best_candidate, max_votes],
			best_candidate,
			"cities",
			{"city_id": cid, "mayor": best_candidate, "votes": max_votes}
		)

	return {
		"ok": true,
		"city_id": cid,
		"previous_mayor": old_mayor,
		"elected_mayor": best_candidate,
		"votes_tally": tally
	}


func set_city_taxes(
	mayor_player: String,
	city_id: String,
	property_tax: int,
	sales_tax_pct: int
) -> Dictionary:
	var cid := city_id.strip_edges()
	if not cities_by_id.has(cid):
		return {"ok": false, "error": "city_not_found"}

	var city: Dictionary = cities_by_id[cid]
	if str(city.get("mayor", "")) != mayor_player:
		return {"ok": false, "error": "only_mayor_can_set_taxes"}

	city["property_tax"] = maxi(0, property_tax)
	city["sales_tax_pct"] = clamp(sales_tax_pct, 0, 10)

	return {
		"ok": true,
		"city_id": cid,
		"property_tax": int(city["property_tax"]),
		"sales_tax_pct": int(city["sales_tax_pct"])
	}


func place_city_civic_structure(
	mayor_player: String,
	city_id: String,
	civic_type: String,
	x: float,
	z: float
) -> Dictionary:
	var cid := city_id.strip_edges()
	if not cities_by_id.has(cid):
		return {"ok": false, "error": "city_not_found"}

	var city: Dictionary = cities_by_id[cid]
	if str(city.get("mayor", "")) != mayor_player:
		return {"ok": false, "error": "only_mayor_can_place_civic"}

	var ctype := civic_type.strip_edges().to_lower()
	if not ctype in ["shuttleport", "cloning_facility", "bank_terminal", "garage"]:
		return {"ok": false, "error": "invalid_civic_type", "hint": "shuttleport, cloning_facility, bank_terminal, garage"}

	var civics: Array = city.get("civic_structures", [])
	var tier_info := evaluate_city_tier(civics.size() + 3)
	var max_c := int(tier_info.get("max_civic", 1))
	if civics.size() >= max_c:
		return {"ok": false, "error": "civic_cap_reached_for_tier", "tier": int(city.get("tier", 1)), "max": max_c}

	var civic_entry := {
		"civic_id": "civic_%s_%d" % [ctype, civics.size() + 1],
		"type": ctype,
		"pos": {"x": x, "y": 0.15, "z": z},
		"placed_at": Time.get_unix_time_from_system()
	}
	civics.append(civic_entry)
	city["civic_structures"] = civics

	return {
		"ok": true,
		"city_id": cid,
		"civic_structure": civic_entry,
		"total_civics": civics.size()
	}

