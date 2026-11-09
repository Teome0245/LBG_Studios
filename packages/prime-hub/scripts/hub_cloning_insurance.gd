extends RefCounted
class_name HubCloningInsurance
## Système SWG Pre-CU : Terminaux d'Assurance d'Équipement, Centres de Clonage,
## Dégradation d'Objets (Item Decay) & Mal de Clonage (Cloning Sickness).

const _HubPaths := preload("res://scripts/hub_paths.gd")

const CLONING_FACILITIES := {
	"clone_lost_heaven": {
		"id": "clone_lost_heaven",
		"label": "Centre de Clonage de Lost Heaven",
		"pos": [-28.0, 0.2, 18.0],
		"cost_credits": 0
	},
	"clone_nomad_ksar": {
		"id": "clone_nomad_ksar",
		"label": "Baie de Clonage du Ksar Nomade",
		"pos": [-95.0, 0.15, -45.0],
		"cost_credits": 50
	}
}

var sim = null
var economy = null

# Profil de clonage et d'assurance : player -> Dictionary
var player_profiles: Dictionary = {}


func setup(sim_svc = null, economy_svc = null) -> void:
	sim = sim_svc
	economy = economy_svc


func _ensure_profile(player: String) -> Dictionary:
	var p := player.strip_edges()
	if not player_profiles.has(p):
		player_profiles[p] = {
			"player": p,
			"bind_facility_id": "clone_lost_heaven",
			"has_cloning_sickness": false,
			"sickness_expires_ts": 0.0,
			"insured_items_count": 0,
			"uninsured_decay_count": 0,
			"total_deaths": 0
		}
	return player_profiles[p]


func get_status(player: String) -> Dictionary:
	var prof := _ensure_profile(player)
	var now := Time.get_unix_time_from_system()
	if prof["has_cloning_sickness"] and now >= float(prof.get("sickness_expires_ts", 0.0)):
		prof["has_cloning_sickness"] = false

	var fac_id: String = str(prof.get("bind_facility_id", "clone_lost_heaven"))
	var fac: Dictionary = CLONING_FACILITIES.get(fac_id, CLONING_FACILITIES["clone_lost_heaven"])

	var out := prof.duplicate(true)
	out["facility"] = fac.duplicate(true)
	return out


func bind_cloning_facility(player: String, facility_id: String) -> Dictionary:
	if not CLONING_FACILITIES.has(facility_id):
		return {"ok": false, "error": "unknown_cloning_facility"}

	var prof := _ensure_profile(player)
	prof["bind_facility_id"] = facility_id
	var fac: Dictionary = CLONING_FACILITIES[facility_id]

	return {
		"ok": true,
		"player": player,
		"facility_id": facility_id,
		"facility_label": fac["label"],
		"message": "Matrice ADN liée avec succès au %s." % fac["label"]
	}


## Assurance des équipements du joueur au Terminal d'Assurance
func insure_items(player: String, item_count: int = 8) -> Dictionary:
	var cost_per_item := 25
	var total_cost := item_count * cost_per_item

	if economy != null:
		var st: Dictionary = economy.status(player) if economy.has_method("status") else {}
		var creds := int(st.get("credits", 1000))
		if creds < total_cost:
			return {
				"ok": false,
				"error": "insufficient_credits",
				"cost": total_cost,
				"available": creds
			}
		if economy.has_method("_consume_credits"):
			economy._consume_credits(player, total_cost)

	var prof := _ensure_profile(player)
	prof["insured_items_count"] = item_count

	return {
		"ok": true,
		"player": player,
		"insured_items_count": item_count,
		"cost_paid": total_cost,
		"message": "Vos %d équipements sont désormais intégralement assurés contre la dégradation post-mortem." % item_count
	}


## Traitement post-mortem : téléportation au centre de clonage & mal de clonage
func process_death_and_clone(player: String) -> Dictionary:
	var prof := _ensure_profile(player)
	prof["total_deaths"] = int(prof.get("total_deaths", 0)) + 1

	var insured := int(prof.get("insured_items_count", 0))
	var decay_applied := false
	if insured <= 0:
		prof["uninsured_decay_count"] = int(prof.get("uninsured_decay_count", 0)) + 1
		decay_applied = true
	else:
		# Consommation de l'assurance
		prof["insured_items_count"] = 0

	# Application du Mal de Clonage (Cloning Sickness) pour 60 secondes
	prof["has_cloning_sickness"] = true
	prof["sickness_expires_ts"] = Time.get_unix_time_from_system() + 60.0

	var fac_id: String = str(prof.get("bind_facility_id", "clone_lost_heaven"))
	var fac: Dictionary = CLONING_FACILITIES.get(fac_id, CLONING_FACILITIES["clone_lost_heaven"])

	if sim != null and sim.has_method("_stream"):
		sim._stream("cloning.respawn", "« Protocole de clonage exécuté : %s réapparaît dans la cuve du %s. »" % [player, fac["label"]], player, "world", {"pos": fac["pos"]})

	return {
		"ok": true,
		"player": player,
		"spawn_pos": fac["pos"],
		"facility_label": fac["label"],
		"decay_applied": decay_applied,
		"cloning_sickness": true,
		"sickness_duration_s": 60.0
	}


## Guérison du Mal de Clonage par un Médecin
func cure_cloning_sickness(player: String, doctor_name: String) -> Dictionary:
	var prof := _ensure_profile(player)
	prof["has_cloning_sickness"] = false
	prof["sickness_expires_ts"] = 0.0

	return {
		"ok": true,
		"player": player,
		"doctor": doctor_name,
		"message": "Le Docteur %s a injecté un stimulant neuro-cellulaire : Mal de clonage complètement dissipé !" % doctor_name
	}

