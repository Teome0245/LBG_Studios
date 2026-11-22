extends RefCounted
class_name HubCreatures
## Système SWG Pre-CU Faune, Métier Scout (Survie/Dépeçage) & Creature Handler (Domptage)
## Conforme au canon Lost Heaven (Ticket 4).

const _HubPaths := preload("res://scripts/hub_paths.gd")

var sim = null
var economy = null
var skills = null
var survey = null
var collision = null

var bestiary_by_id: Dictionary = {}
var corpses_by_id: Dictionary = {}
var camps_by_id: Dictionary = {}
var pets_by_id: Dictionary = {}
var lairs_by_id: Dictionary = {}
var scent_masked_players: Dictionary = {}

var _rng := RandomNumberGenerator.new()
var _next_corpse_id := 5001
var _next_camp_id := 7001
var _next_pet_id := 9001


func setup(parent_sim, economy_svc = null, skills_svc = null, survey_svc = null, collision_svc = null) -> void:
	sim = parent_sim
	economy = economy_svc
	skills = skills_svc
	survey = survey_svc
	collision = collision_svc
	_rng.randomize()
	reload_bestiary()
	init_default_lairs()


func reload_bestiary(custom_path: String = "") -> void:
	bestiary_by_id.clear()
	var path := custom_path
	if path.is_empty():
		path = _HubPaths.data_file("bestiaire_lh.json")
	var raw: Variant = _HubPaths.read_json(path)
	if typeof(raw) != TYPE_DICTIONARY:
		return
	var arr: Variant = raw.get("creatures", [])
	if typeof(arr) != TYPE_ARRAY:
		return
	for c in arr:
		if typeof(c) == TYPE_DICTIONARY and not str(c.get("id", "")).is_empty():
			bestiary_by_id[str(c["id"])] = (c as Dictionary).duplicate(true)


func get_creature_def(beast_id: String) -> Dictionary:
	var bid := beast_id.strip_edges()
	if bestiary_by_id.has(bid):
		return (bestiary_by_id[bid] as Dictionary).duplicate(true)
	return {}


func list_creatures() -> Array:
	var out: Array = []
	for k in bestiary_by_id.keys():
		out.append((bestiary_by_id[k] as Dictionary).duplicate(true))
	return out


# ==============================================================================
# SECTION 1 : CADAVRES & DÉPEÇAGE SCOUT (HARVESTING MEAT / HIDE / BONE)
# ==============================================================================

func create_corpse(beast_id: String, beast_name: String, pos: Vector3, killer: String = "", zone_id: String = "") -> Dictionary:
	var now := Time.get_unix_time_from_system()
	var cid := "corpse_%d" % _next_corpse_id
	_next_corpse_id += 1

	var cdef := get_creature_def(beast_id)
	var harvest_data := {}
	if not cdef.is_empty() and cdef.has("harvest"):
		harvest_data = (cdef["harvest"] as Dictionary).duplicate(true)

	var entry := {
		"corpse_id": cid,
		"beast_id": beast_id,
		"beast_name": beast_name,
		"pos": pos,
		"killer": killer,
		"zone_id": zone_id,
		"created_at": now,
		"expires_at": now + 120.0, # 2 minutes avant décomposition
		"harvested": false,
		"harvested_by": "",
		"harvest_type": "",
		"harvest_data": harvest_data,
		"danger_level": int(cdef.get("danger_level", 1)),
		"is_boss": bool(cdef.get("is_boss", false)),
	}
	corpses_by_id[cid] = entry
	return entry.duplicate(true)


func list_active_corpses() -> Array:
	var out: Array = []
	var now := Time.get_unix_time_from_system()
	for cid in corpses_by_id.keys():
		var c: Dictionary = corpses_by_id[cid]
		if float(c.get("expires_at", 0.0)) >= now and not bool(c.get("harvested", false)):
			out.append(c.duplicate(true))
	return out


func list_corpses_near(x: float, z: float, radius_m: float = 30.0) -> Array:
	var out: Array = []
	var now := Time.get_unix_time_from_system()
	for cid in corpses_by_id.keys():
		var c: Dictionary = corpses_by_id[cid]
		if float(c.get("expires_at", 0.0)) < now or bool(c.get("harvested", false)):
			continue
		var p: Vector3 = c.get("pos", Vector3.ZERO)
		var dist := Vector2(p.x - x, p.z - z).length()
		if dist <= radius_m:
			var copy := c.duplicate(true)
			copy["distance_m"] = snappedf(dist, 0.1)
			out.append(copy)
	return out


func harvest_corpse(player: String, corpse_id: String, harvest_type: String) -> Dictionary:
	var cid := corpse_id.strip_edges()
	if not corpses_by_id.has(cid):
		return {"ok": false, "error": "corpse_not_found"}

	var corpse: Dictionary = corpses_by_id[cid]
	var now := Time.get_unix_time_from_system()
	if float(corpse.get("expires_at", 0.0)) < now:
		corpses_by_id.erase(cid)
		return {"ok": false, "error": "corpse_decomposed"}

	if bool(corpse.get("harvested", false)):
		return {"ok": false, "error": "corpse_already_harvested", "harvested_by": str(corpse.get("harvested_by", ""))}

	var htype := harvest_type.strip_edges().to_lower()
	if not htype in ["meat", "hide", "bone"]:
		return {"ok": false, "error": "invalid_harvest_type", "hint": "choisir meat, hide ou bone"}

	var hdata: Dictionary = corpse.get("harvest_data", {})
	if not hdata.has(htype):
		return {"ok": false, "error": "resource_not_available_on_creature", "type": htype}

	var res_spec: Dictionary = hdata[htype]
	var base_qty := int(res_spec.get("base_qty", 2))
	var res_id := str(res_spec.get("id", "organique"))
	var res_name := str(res_spec.get("name", "Ressource organique"))

	# Multiplicateur Scout / Prélèvement Faunique
	var skill_mult := 1.0
	var xp_reward := 25
	if skills != null:
		if skills.has_box(player, "prospecteur_master"):
			skill_mult = 3.0
			xp_reward = 80
		elif skills.has_box(player, "prospecteur_faune_04"):
			skill_mult = 2.5
			xp_reward = 65
		elif skills.has_box(player, "prospecteur_faune_03"):
			skill_mult = 2.0
			xp_reward = 50
		elif skills.has_box(player, "prospecteur_faune_02"):
			skill_mult = 1.5
			xp_reward = 35
		elif skills.has_box(player, "prospecteur_faune_01"):
			skill_mult = 1.25
			xp_reward = 25

	var final_qty := maxi(1, int(round(float(base_qty) * skill_mult)))

	# Stats de la ressource (OQ, etc.)
	var stats := {
		"oq": int(res_spec.get("oq", 500)),
		"pe": int(res_spec.get("pe", 400)),
		"ma": int(res_spec.get("ma", 400)),
		"cd": int(res_spec.get("cd", 300)),
		"sr": int(res_spec.get("sr", 300)),
		"nutrition": int(res_spec.get("nutrition", 50))
	}

	# Attribution au joueur dans l'économie
	if economy != null and economy.has_method("grant_world_loot"):
		economy.grant_world_loot(player, [{"id": res_id, "name": res_name, "qty": final_qty, "stats": stats}], 0)

	# Attribution XP prospection
	if skills != null and skills.has_method("add_xp"):
		skills.add_xp(player, "xp_prospection", xp_reward)

	corpse["harvested"] = true
	corpse["harvested_by"] = player
	corpse["harvest_type"] = htype

	if sim != null and sim.has_method("_stream"):
		sim._stream(
			"scout.harvest",
			"%s a prélevé %d× %s (%s) sur %s." % [player, final_qty, res_name, htype, str(corpse.get("beast_name", "la bête"))],
			player,
			str(corpse.get("zone_id", "")),
			{"corpse_id": cid, "resource_id": res_id, "qty": final_qty, "type": htype}
		)

	return {
		"ok": true,
		"corpse_id": cid,
		"harvest_type": htype,
		"resource_id": res_id,
		"resource_name": res_name,
		"qty": final_qty,
		"stats": stats,
		"xp_gained": xp_reward,
		"source": "prime_hub"
	}


# ==============================================================================
# SECTION 2 : CAMPS DE SURVIE & ABRI (SCOUT WILDERNESS CAMPS)
# ==============================================================================

func deploy_camp(player: String, x: float, z: float, camp_type: String = "abri_toile") -> Dictionary:
	var ctype := camp_type.strip_edges().to_lower()
	if not ctype in ["abri_toile", "camp_chasseur"]:
		ctype = "abri_toile"

	# Vérifier restrictions urbaines (Lost Heaven intra-muros interdit le camping)
	var dist_center := Vector2(x - 5100.0, z - (-800.0)).length()
	if dist_center < 120.0:
		return {
			"ok": false,
			"error": "too_close_to_city",
			"hint": "Installe ton camp hors des remparts de Lost Heaven (terres sauvages)."
		}

	# Prérequis de compétences
	var req_box := "prospecteur_camp_01" if ctype == "abri_toile" else "prospecteur_camp_03"
	if skills != null and not skills.has_box(player, req_box) and not skills.has_box(player, "prospecteur_novice"):
		return {
			"ok": false,
			"error": "skill_required",
			"required_box": req_box
		}

	var now := Time.get_unix_time_from_system()
	var camp_id := "camp_%d" % _next_camp_id
	_next_camp_id += 1

	var duration_s := 300.0 if ctype == "abri_toile" else 600.0
	var radius := 15.0 if ctype == "abri_toile" else 30.0
	var regen_mult := 1.5 if ctype == "abri_toile" else 2.2
	var repels := (ctype == "camp_chasseur")

	var entry := {
		"camp_id": camp_id,
		"owner": player,
		"camp_type": ctype,
		"pos": Vector3(x, 0.15, z),
		"radius": radius,
		"created_at": now,
		"expires_at": now + duration_s,
		"ham_regen_mult": regen_mult,
		"repels_predators": repels,
		"visitors": [player]
	}
	camps_by_id[camp_id] = entry

	if sim != null and sim.has_method("_stream"):
		sim._stream(
			"camp.deployed",
			"%s a dressé un %s à (%.0f, %.0f)." % [player, ctype, x, z],
			player,
			"wild",
			{"camp_id": camp_id, "type": ctype, "radius": radius, "duration_s": duration_s}
		)

	return {
		"ok": true,
		"camp_id": camp_id,
		"camp_type": ctype,
		"pos": {"x": x, "y": 0.15, "z": z},
		"radius": radius,
		"duration_s": duration_s,
		"ham_regen_mult": regen_mult,
		"repels_predators": repels,
		"source": "prime_hub"
	}


func get_active_camp_at(x: float, z: float) -> Dictionary:
	var now := Time.get_unix_time_from_system()
	for cid in camps_by_id.keys():
		var c: Dictionary = camps_by_id[cid]
		if float(c.get("expires_at", 0.0)) < now:
			continue
		var p: Vector3 = c.get("pos", Vector3.ZERO)
		var dist := Vector2(p.x - x, p.z - z).length()
		if dist <= float(c.get("radius", 15.0)):
			var res := c.duplicate(true)
			res["distance_m"] = snappedf(dist, 0.1)
			return res
	return {}


func abandon_camp(player: String, camp_id: String) -> Dictionary:
	var cid := camp_id.strip_edges()
	if not camps_by_id.has(cid):
		return {"ok": false, "error": "camp_not_found"}
	var camp: Dictionary = camps_by_id[cid]
	if str(camp.get("owner", "")) != player:
		return {"ok": false, "error": "not_camp_owner"}
	camps_by_id.erase(cid)
	return {"ok": true, "camp_id": cid, "status": "abandoned"}


# ==============================================================================
# SECTION 3 : CAMOUFLAGE D'ODEUR (MASK SCENT)
# ==============================================================================

func mask_scent(player: String) -> Dictionary:
	var req_box := "prospecteur_piste_01"
	if skills != null and not skills.has_box(player, req_box) and not skills.has_box(player, "prospecteur_novice"):
		return {"ok": false, "error": "skill_required", "required_box": req_box}

	var now := Time.get_unix_time_from_system()
	var duration_s := 120.0
	if skills != null and skills.has_box(player, "prospecteur_piste_03"):
		duration_s = 240.0

	scent_masked_players[player] = now + duration_s
	return {
		"ok": true,
		"player": player,
		"masked": true,
		"duration_s": duration_s,
		"expires_at": now + duration_s
	}


func is_scent_masked(player: String) -> bool:
	var now := Time.get_unix_time_from_system()
	if scent_masked_players.has(player):
		if float(scent_masked_players[player]) > now:
			return true
		scent_masked_players.erase(player)
	return false


# ==============================================================================
# SECTION 4 : CREATURE HANDLER (DOMPTAGE, FAMILIERS & ORDRES)
# ==============================================================================

func tame_creature(player: String, beast_eid: String, force_success: bool = false) -> Dictionary:
	if sim == null or not sim.entities.has(beast_eid):
		return {"ok": false, "error": "entity_not_found"}

	var beast: Dictionary = sim.entities[beast_eid]
	if str(beast.get("kind", "")) != "beast":
		return {"ok": false, "error": "target_is_not_a_beast"}

	var beast_id := str(beast.get("beast_id", ""))
	var cdef := get_creature_def(beast_id)

	# Bête domptable ?
	var is_tameable := bool(cdef.get("is_tameable", false))
	if not is_tameable:
		return {
			"ok": false,
			"error": "creature_not_tameable",
			"hint": "Cette bête adulte est trop sauvage. Cherche un jeune spécimen ou un chiot."
		}

	# Vérifier compétence requise
	var req_skill := str(cdef.get("taming_skill_required", "prospecteur_faune_01"))
	var player_has_req := true
	if not force_success and skills != null:
		player_has_req = skills.has_box(player, req_skill) or skills.has_box(player, "prospecteur_master")

	if not player_has_req:
		return {
			"ok": false,
			"error": "taming_skill_insufficient",
			"required_skill": req_skill
		}

	# Vérifier distance au joueur
	var player_pos := Vector3(5100.0, 0.15, -800.0)
	if sim.entities.has(player):
		player_pos = sim.entities[player].get("pos", player_pos)
	var beast_pos: Vector3 = beast.get("pos", Vector3.ZERO)
	var dist := Vector2(beast_pos.x - player_pos.x, beast_pos.z - player_pos.z).length()
	if not force_success and dist > 14.0:
		return {"ok": false, "error": "too_far", "distance_m": snappedf(dist, 0.1), "max_m": 14.0}

	# Jet de domptage
	var diff := int(cdef.get("taming_difficulty", 2))
	var chance := 60 - (diff * 10)
	if is_scent_masked(player):
		chance += 15 # Bonus camouflage d'odeur
	if skills != null and skills.has_box(player, "prospecteur_faune_04"):
		chance += 20

	var roll := _rng.randi_range(1, 100)
	if not force_success and roll > chance:
		# Échec du domptage : la bête fuit ou s'énerve
		beast["goal"] = "flee"
		return {
			"ok": false,
			"outcome": "taming_failed",
			"message": "La créature a pris peur et s'enfuit !",
			"roll": roll,
			"chance": chance
		}

	# Succès ! La bête devient un familier
	var pet_id := "pet_%d" % _next_pet_id
	_next_pet_id += 1

	var bname := str(beast.get("name", cdef.get("name", "Familier")))
	var pet_name := "%s de %s" % [bname, player]
	var max_hp := int(cdef.get("base_health", 150))
	var dmg := int(cdef.get("base_damage", 10))

	var pet_data := {
		"pet_id": pet_id,
		"species_id": beast_id,
		"name": pet_name,
		"owner": player,
		"loyalty": 80,
		"hunger": 10,
		"level": 1,
		"health": max_hp,
		"max_health": max_hp,
		"damage": dmg,
		"state": "stored",
		"created_at": Time.get_unix_time_from_system()
	}
	pets_by_id[pet_id] = pet_data

	# Retirer la bête sauvage de la simulation
	beast["active"] = false
	beast["goal"] = "tamed"
	sim.entities.erase(beast_eid)

	# XP de domptage
	if skills != null and skills.has_method("add_xp"):
		skills.add_xp(player, "xp_prospection", 100)

	if sim != null and sim.has_method("_stream"):
		sim._stream(
			"creature.tamed",
			"%s a apprivoisé avec succès un %s (%s)." % [player, bname, pet_id],
			player,
			str(beast.get("zone_id", "desert")),
			{"pet_id": pet_id, "species": beast_id}
		)

	return {
		"ok": true,
		"outcome": "tamed",
		"pet": pet_data.duplicate(true),
		"xp_gained": 100,
		"source": "prime_hub"
	}


func list_player_pets(player: String) -> Array:
	var out: Array = []
	for pid in pets_by_id.keys():
		var p: Dictionary = pets_by_id[pid]
		if str(p.get("owner", "")) == player:
			out.append(p.duplicate(true))
	return out


func call_pet(player: String, pet_id: String, x: float, z: float) -> Dictionary:
	var pid := pet_id.strip_edges()
	if not pets_by_id.has(pid):
		return {"ok": false, "error": "pet_not_found"}

	var pet: Dictionary = pets_by_id[pid]
	if str(pet.get("owner", "")) != player:
		return {"ok": false, "error": "not_pet_owner"}

	if str(pet.get("state", "stored")) != "stored":
		return {"ok": false, "error": "pet_already_active"}

	# Invoquer dans sim.entities
	var eid := "pet_entity_%s" % pid
	var entity_data := {
		"eid": eid,
		"kind": "pet",
		"pet_id": pid,
		"name": str(pet.get("name", "Familier")),
		"owner": player,
		"pos": Vector3(x, 0.15, z),
		"target": Vector3.ZERO,
		"goal": "follow",
		"health": int(pet.get("health", 100)),
		"max_health": int(pet.get("max_health", 100)),
		"damage": int(pet.get("damage", 10)),
		"active": true
	}
	if sim != null:
		sim.entities[eid] = entity_data

	pet["state"] = "follow"
	pet["active_eid"] = eid

	return {
		"ok": true,
		"pet_id": pid,
		"eid": eid,
		"state": "follow",
		"pos": {"x": x, "y": 0.15, "z": z}
	}


func store_pet(player: String, pet_id: String) -> Dictionary:
	var pid := pet_id.strip_edges()
	if not pets_by_id.has(pid):
		return {"ok": false, "error": "pet_not_found"}

	var pet: Dictionary = pets_by_id[pid]
	if str(pet.get("owner", "")) != player:
		return {"ok": false, "error": "not_pet_owner"}

	var eid := str(pet.get("active_eid", ""))
	if not eid.is_empty() and sim != null and sim.entities.has(eid):
		sim.entities.erase(eid)

	pet["state"] = "stored"
	pet.erase("active_eid")

	return {"ok": true, "pet_id": pid, "state": "stored"}


func command_pet(player: String, pet_id: String, command: String, target_eid: String = "") -> Dictionary:
	var pid := pet_id.strip_edges()
	if not pets_by_id.has(pid):
		return {"ok": false, "error": "pet_not_found"}

	var pet: Dictionary = pets_by_id[pid]
	if str(pet.get("owner", "")) != player:
		return {"ok": false, "error": "not_pet_owner"}

	var cmd := command.strip_edges().to_lower()
	if not cmd in ["follow", "stay", "attack", "guard"]:
		return {"ok": false, "error": "unknown_command", "valid": ["follow", "stay", "attack", "guard"]}

	var eid := str(pet.get("active_eid", ""))
	if eid.is_empty() or sim == null or not sim.entities.has(eid):
		return {"ok": false, "error": "pet_not_summoned"}

	var ent: Dictionary = sim.entities[eid]
	ent["goal"] = cmd
	if cmd == "attack" and not target_eid.is_empty():
		ent["target_eid"] = target_eid

	pet["state"] = cmd
	return {"ok": true, "pet_id": pid, "command": cmd, "target_eid": target_eid}


func feed_pet(player: String, pet_id: String, food_item_id: String) -> Dictionary:
	var pid := pet_id.strip_edges()
	if not pets_by_id.has(pid):
		return {"ok": false, "error": "pet_not_found"}

	var pet: Dictionary = pets_by_id[pid]
	if str(pet.get("owner", "")) != player:
		return {"ok": false, "error": "not_pet_owner"}

	# Diminution de la faim, hausse de la loyauté
	var cur_hunger := int(pet.get("hunger", 0))
	var new_hunger := maxi(0, cur_hunger - 45)
	var cur_loyalty := int(pet.get("loyalty", 70))
	var new_loyalty := mini(100, cur_loyalty + 15)

	# Soin de PV
	var cur_hp := int(pet.get("health", 100))
	var max_hp := int(pet.get("max_health", 100))
	var new_hp := mini(max_hp, cur_hp + 50)

	pet["hunger"] = new_hunger
	pet["loyalty"] = new_loyalty
	pet["health"] = new_hp

	var eid := str(pet.get("active_eid", ""))
	if not eid.is_empty() and sim != null and sim.entities.has(eid):
		sim.entities[eid]["health"] = new_hp

	return {
		"ok": true,
		"pet_id": pid,
		"hunger": new_hunger,
		"loyalty": new_loyalty,
		"health": new_hp,
		"max_health": max_hp,
		"message": "%s est rassasié et plus fidèle !" % str(pet.get("name", "Le familier"))
	}


## Monter sur un familier apprivoisé éligible (Système de Montures façon Wicked Island / SWG)
func mount_pet(player: String, pet_id: String) -> Dictionary:
	var pid := pet_id.strip_edges()
	if not pets_by_id.has(pid):
		return {"ok": false, "error": "pet_not_found"}

	var pet: Dictionary = pets_by_id[pid]
	if str(pet.get("owner", "")) != player:
		return {"ok": false, "error": "not_pet_owner"}

	var active_eid := str(pet.get("active_eid", ""))
	if active_eid.is_empty() or sim == null or not sim.entities.has(active_eid):
		return {"ok": false, "error": "pet_not_summoned", "message": "Invoquez d'abord votre créature pour la monter."}

	var species := str(pet.get("species_id", ""))
	var cdef: Dictionary = bestiary_by_id.get(species, {})
	var is_mountable := bool(cdef.get("is_mountable", false))
	if not is_mountable:
		return {
			"ok": false,
			"error": "creature_not_mountable",
			"message": "%s n'est pas une créature montable." % str(pet.get("name", "Cette bête"))
		}

	var speed_mult := float(cdef.get("mount_speed_mult", 1.5))
	pet["state"] = "mounted"

	# Mettre à jour l'entité joueur si elle existe dans la sim
	if sim != null and sim.entities.has(player):
		sim.entities[player]["mounted_pet_id"] = pid
		sim.entities[player]["speed_mult"] = speed_mult

	# Synchroniser l'entité pet
	if sim != null and sim.entities.has(active_eid):
		sim.entities[active_eid]["goal"] = "mounted"

	return {
		"ok": true,
		"outcome": "mounted",
		"pet_id": pid,
		"speed_mult": speed_mult,
		"message": "Vous chevauchez fièrement votre %s (+%d%% vitesse) !" % [
			str(pet.get("name", "monture")), int((speed_mult - 1.0) * 100)
		]
	}


## Descendre de sa monture
func dismount_pet(player: String, pet_id: String) -> Dictionary:
	var pid := pet_id.strip_edges()
	if not pets_by_id.has(pid):
		return {"ok": false, "error": "pet_not_found"}

	var pet: Dictionary = pets_by_id[pid]
	if str(pet.get("owner", "")) != player:
		return {"ok": false, "error": "not_pet_owner"}

	pet["state"] = "follow"

	if sim != null and sim.entities.has(player):
		sim.entities[player]["mounted_pet_id"] = ""
		sim.entities[player]["speed_mult"] = 1.0

	var active_eid := str(pet.get("active_eid", ""))
	if sim != null and sim.entities.has(active_eid):
		sim.entities[active_eid]["goal"] = "follow"

	return {
		"ok": true,
		"outcome": "dismounted",
		"pet_id": pid,
		"state": "follow",
		"message": "Vous êtes descendu de votre monture."
	}


# ==============================================================================
# SECTION 5 : TICKS & EXPIRATIONS
# ==============================================================================

func tick_creatures(_delta: float) -> void:
	var now := Time.get_unix_time_from_system()

	# Nettoyage des cadavres expirés
	for cid in corpses_by_id.keys():
		var c: Dictionary = corpses_by_id[cid]
		if float(c.get("expires_at", 0.0)) < now:
			corpses_by_id.erase(cid)

	# Nettoyage des camps expirés
	for camp_id in camps_by_id.keys():
		var camp: Dictionary = camps_by_id[camp_id]
		if float(camp.get("expires_at", 0.0)) < now:
			if sim != null and sim.has_method("_stream"):
				sim._stream(
					"camp.expired",
					"Le camp %s est tombé en ruines." % camp_id,
					str(camp.get("owner", "")),
					"wild"
				)
			camps_by_id.erase(camp_id)


# ==============================================================================
# SECTION 6 : NIDS DE CRÉATURES (LAIRS) & DESTRUCTION DE NID
# ==============================================================================

func init_default_lairs() -> void:
	lairs_by_id = {
		"lair_jackals_west": {
			"id": "lair_jackals_west",
			"name": "Tumulus des Chacals des Dunes",
			"creature_kind": "creature_jackal",
			"guardian_name": "Chacal Protecteur du Nid",
			"x": 4550.0,
			"z": -810.0,
			"max_health": 1400,
			"current_health": 1400,
			"is_destroyed": false,
			"waves_spawned": [],
			"loot_credits": 950,
			"loot_rare_item": "oeuf_chacal_fossile",
			"rare_item_label": "Œuf de Chacal des Sables Fossilisé",
			"is_harvested": false
		},
		"lair_beetles_east": {
			"id": "lair_beetles_east",
			"name": "Nid de Scarabées Obsidiens",
			"creature_kind": "creature_beetle",
			"guardian_name": "Scarabée Ouvrier Défenseur",
			"x": 5420.0,
			"z": -670.0,
			"max_health": 1800,
			"current_health": 1800,
			"is_destroyed": false,
			"waves_spawned": [],
			"loot_credits": 1250,
			"loot_rare_item": "chitine_reine_scarabee",
			"rare_item_label": "Chitine Pure de Reine Scarabée",
			"is_harvested": false
		}
	}


func list_lairs() -> Array:
	var out: Array = []
	for lid in lairs_by_id.keys():
		out.append((lairs_by_id[lid] as Dictionary).duplicate(true))
	return out


func get_lair(lair_id: String) -> Dictionary:
	var lid := lair_id.strip_edges()
	if lairs_by_id.has(lid):
		return (lairs_by_id[lid] as Dictionary).duplicate(true)
	return {}


func attack_lair(player: String, lair_id: String, damage: int) -> Dictionary:
	var p := player.strip_edges()
	var lid := lair_id.strip_edges()
	if not lairs_by_id.has(lid):
		return {"ok": false, "error": "lair_not_found"}

	var lair: Dictionary = lairs_by_id[lid]
	if bool(lair.get("is_destroyed", false)):
		return {"ok": false, "error": "lair_already_destroyed", "is_debris": true}

	var cur_hp: int = int(lair.get("current_health", 1000))
	var max_hp: int = int(lair.get("max_health", 1000))
	var new_hp := maxi(0, cur_hp - damage)
	lair["current_health"] = new_hp

	var waves: Array = lair.get("waves_spawned", [])
	var ratio := float(new_hp) / float(max_hp)
	var spawned_wave := 0

	# Seuils de riposte 75%, 50%, 25%
	if ratio <= 0.75 and not 0.75 in waves:
		waves.append(0.75)
		spawned_wave = 1
	elif ratio <= 0.50 and not 0.50 in waves:
		waves.append(0.50)
		spawned_wave = 2
	elif ratio <= 0.25 and not 0.25 in waves:
		waves.append(0.25)
		spawned_wave = 3

	lair["waves_spawned"] = waves

	if new_hp <= 0:
		lair["is_destroyed"] = true
		lair["current_health"] = 0
		lairs_by_id[lid] = lair
		if sim != null and sim.has_method("_stream"):
			sim._stream(
				"lair.destroyed",
				"%s a détruit le nid %s ! Les décombres sont pillables." % [p, str(lair.get("name", lid))],
				p,
				"combat"
			)
		return {
			"ok": true,
			"player": p,
			"lair_id": lid,
			"damage_dealt": damage,
			"remaining_hp": 0,
			"is_destroyed": true,
			"debris_ready": true,
			"message": "Le nid s'est effondré en décombres !"
		}

	lairs_by_id[lid] = lair
	return {
		"ok": true,
		"player": p,
		"lair_id": lid,
		"damage_dealt": damage,
		"remaining_hp": new_hp,
		"max_hp": max_hp,
		"wave_triggered": spawned_wave,
		"is_destroyed": false
	}


func harvest_debris(player: String, lair_id: String) -> Dictionary:
	var p := player.strip_edges()
	var lid := lair_id.strip_edges()
	if not lairs_by_id.has(lid):
		return {"ok": false, "error": "lair_not_found"}

	var lair: Dictionary = lairs_by_id[lid]
	if not bool(lair.get("is_destroyed", false)):
		return {"ok": false, "error": "lair_not_destroyed"}

	if bool(lair.get("is_harvested", false)):
		return {"ok": false, "error": "debris_already_harvested"}

	lair["is_harvested"] = true
	lairs_by_id[lid] = lair

	var creds := int(lair.get("loot_credits", 500))
	var rare_item := str(lair.get("loot_rare_item", "oeuf_rare"))
	var item_lbl := str(lair.get("rare_item_label", "Objet Rare"))

	if economy != null and economy.has_method("add_credits"):
		economy.add_credits(p, creds)
	if economy != null and economy.has_method("add_inventory_item"):
		economy.add_inventory_item(p, rare_item, 1)

	return {
		"ok": true,
		"player": p,
		"lair_id": lid,
		"credits": creds,
		"rare_item": rare_item,
		"rare_item_label": item_lbl,
		"message": "Décombres fouillés avec succès ! +%d crédits et 1x %s." % [creds, item_lbl]
	}


