extends RefCounted
class_name HubSpaceJtl
## Extension Jump to Lightspeed (JTL) SWG Pre-CU :
## Combat Spatial 3D Dogfight, Chasseurs (X-Wing, TIE, YT-1300),
## Répartiteur d'Énergie Tri-Voie, Boucliers & Sauts Hyperspatiaux.

const _HubPaths := preload("res://scripts/hub_paths.gd")

const SHIP_TEMPLATES := {
	"xwing_t65": {
		"id": "xwing_t65",
		"label": "Incom T-65B X-Wing",
		"faction": "rebel",
		"max_hull": 1200,
		"max_shield_fwd": 600,
		"max_shield_aft": 600,
		"top_speed": 95.0,
		"boost_speed": 145.0,
		"laser_damage": 85,
		"laser_color": "red"
	},
	"tiefighter_ln": {
		"id": "tiefighter_ln",
		"label": "Chasseur Stellaire TIE/ln",
		"faction": "imperial",
		"max_hull": 900,
		"max_shield_fwd": 0,
		"max_shield_aft": 0,
		"top_speed": 115.0,
		"boost_speed": 170.0,
		"laser_damage": 95,
		"laser_color": "green"
	},
	"yt1300_freighter": {
		"id": "yt1300_freighter",
		"label": "Cargo Léger YT-1300 Corellien",
		"faction": "neutral",
		"max_hull": 3500,
		"max_shield_fwd": 1200,
		"max_shield_aft": 1200,
		"top_speed": 70.0,
		"boost_speed": 110.0,
		"laser_damage": 120,
		"laser_color": "red"
	}
}

var sim = null
var next_ship_instance_id: int = 1

# Vaisseaux actifs dans le secteur spatial : ship_id -> Dictionary
var active_ships: Dictionary = {}


func setup(sim_svc = null) -> void:
	sim = sim_svc
	_init_seed_space_sector()


func _init_seed_space_sector() -> void:
	active_ships.clear()
	# Spawn d'un TIE patrouilleur et d'une frégate pirate
	spawn_starship("Pilote_Imperial_DS1", "tiefighter_ln", Vector3(450.0, 120.0, -300.0))
	spawn_starship("Corsaire_Pirate", "yt1300_freighter", Vector3(-600.0, -80.0, 500.0))


func spawn_starship(pilot: String, ship_type: String, pos: Vector3 = Vector3.ZERO) -> Dictionary:
	if not SHIP_TEMPLATES.has(ship_type):
		return {"ok": false, "error": "unknown_ship_type"}

	var tmpl: Dictionary = SHIP_TEMPLATES[ship_type]
	var sid := "ship_%d" % next_ship_instance_id
	next_ship_instance_id += 1

	var entry := {
		"id": sid,
		"pilot": pilot,
		"ship_type": ship_type,
		"label": str(tmpl.get("label", "Vaisseau")),
		"faction": str(tmpl.get("faction", "neutral")),
		"pos": [pos.x, pos.y, pos.z],
		"hull": int(tmpl.get("max_hull", 1000)),
		"max_hull": int(tmpl.get("max_hull", 1000)),
		"shield_fwd": int(tmpl.get("max_shield_fwd", 500)),
		"max_shield_fwd": int(tmpl.get("max_shield_fwd", 500)),
		"shield_aft": int(tmpl.get("max_shield_aft", 500)),
		"max_shield_aft": int(tmpl.get("max_shield_aft", 500)),
		"power_distribution": {"weapons": 33, "shields": 33, "engines": 34},
		"current_speed": 0.0,
		"is_destroyed": false
	}
	active_ships[sid] = entry

	if sim != null and sim.has_method("_stream"):
		sim._stream("jtl.launch", "« Décollage orbital : %s a mis le cap sur le secteur spatial à bord de : %s ! »" % [pilot, entry["label"]], pilot, "space", entry)

	return {"ok": true, "ship": entry.duplicate(true)}


func list_sector_ships() -> Array:
	return active_ships.values().duplicate(true)


func get_ship(ship_id: String) -> Dictionary:
	var sid := ship_id.strip_edges()
	if active_ships.has(sid):
		return (active_ships[sid] as Dictionary).duplicate(true)
	return {}


## Répartiteur d'Énergie Tri-Voie SWG (Moteurs, Boucliers, Armes)
func adjust_power_distribution(ship_id: String, weapons_pct: int, shields_pct: int, engines_pct: int) -> Dictionary:
	if not active_ships.has(ship_id):
		return {"ok": false, "error": "unknown_ship"}

	var total := weapons_pct + shields_pct + engines_pct
	if total != 100:
		return {"ok": false, "error": "power_must_sum_to_100", "total": total}

	active_ships[ship_id]["power_distribution"] = {
		"weapons": weapons_pct,
		"shields": shields_pct,
		"engines": engines_pct
	}

	return {
		"ok": true,
		"ship_id": ship_id,
		"power_distribution": active_ships[ship_id]["power_distribution"].duplicate()
	}


## Tir de lasers en combat spatial dogfight
func fire_lasers_at_target(attacker_ship_id: String, target_ship_id: String) -> Dictionary:
	if not active_ships.has(attacker_ship_id) or not active_ships.has(target_ship_id):
		return {"ok": false, "error": "invalid_ship_ids"}

	var atk: Dictionary = active_ships[attacker_ship_id]
	var tgt: Dictionary = active_ships[target_ship_id]

	if bool(atk.get("is_destroyed", false)): return {"ok": false, "error": "attacker_destroyed"}
	if bool(tgt.get("is_destroyed", false)): return {"ok": false, "error": "target_already_destroyed"}

	var tmpl_atk: Dictionary = SHIP_TEMPLATES[atk["ship_type"]]
	var base_dmg: int = int(tmpl_atk.get("laser_damage", 80))
	var w_power: int = int(atk.get("power_distribution", {}).get("weapons", 33))
	var final_dmg: int = int(base_dmg * (float(w_power) / 33.0))

	# Absorption bouclier avant
	var fwd_shield: int = int(tgt.get("shield_fwd", 0))
	var absorbed: int = mini(fwd_shield, final_dmg)
	tgt["shield_fwd"] = fwd_shield - absorbed
	var hull_dmg: int = final_dmg - absorbed
	tgt["hull"] = maxi(0, int(tgt.get("hull", 1000)) - hull_dmg)

	var destroyed := (int(tgt["hull"]) <= 0)
	if destroyed:
		tgt["is_destroyed"] = true

	if sim != null and sim.has_method("_stream"):
		if destroyed:
			sim._stream("jtl.kill", "« DOGFIGHT : %s a détruit le vaisseau ennemi %s (%s) dans une explosion spatiale ! »" % [atk["pilot"], tgt["pilot"], tgt["label"]], atk["pilot"], "space", {})
		else:
			sim._stream("jtl.hit", "« Impact laser : %s touche %s (-%d dégâts, Coque restante : %d PV). »" % [atk["pilot"], tgt["pilot"], final_dmg, tgt["hull"]], atk["pilot"], "space", {})

	return {
		"ok": true,
		"attacker": atk["pilot"],
		"target": tgt["pilot"],
		"damage_dealt": final_dmg,
		"target_fwd_shield": tgt["shield_fwd"],
		"target_hull": tgt["hull"],
		"target_destroyed": destroyed
	}


## Saut Hyperspatial vers un autre secteur
func jump_hyperspace(ship_id: String, destination_sector: String = "Corellian_Sector") -> Dictionary:
	if not active_ships.has(ship_id):
		return {"ok": false, "error": "unknown_ship"}

	var ship: Dictionary = active_ships[ship_id]

	if sim != null and sim.has_method("_stream"):
		sim._stream("jtl.hyperspace", "« MOTRICITÉ HYPERSPATIALE ACTIVÉE : %s plonge dans l'hyper-espace vers [%s] ! »" % [ship["label"], destination_sector], ship["pilot"], "space", {})

	return {
		"ok": true,
		"ship_id": ship_id,
		"destination_sector": destination_sector,
		"message": "Saut dans l'hyper-espace complété avec succès."
	}

