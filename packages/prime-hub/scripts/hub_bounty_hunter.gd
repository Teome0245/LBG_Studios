extends RefCounted
class_name HubBountyHunter
## Système SWG Pre-CU : Terminaux de Primes (Bounty Hunter Terminals),
## Primes Dynamiques sur Jedi & Fugitifs, Droïdes Sondes Arakyd & Traque GPS.

const _HubPaths := preload("res://scripts/hub_paths.gd")

var sim = null
var economy = null
var next_bounty_id: int = 101

# Primes : id -> Dictionary
var bounties_by_id: Dictionary = {}


func setup(sim_svc = null, economy_svc = null) -> void:
	sim = sim_svc
	economy = economy_svc
	_init_seed_bounties()


func _init_seed_bounties() -> void:
	bounties_by_id.clear()
	_create_bounty("Kaelen_Fugitif", "fugitive", 3500, "Milice Lost Heaven", "Contrebande d'hyper-matière et vol de speeder.", Vector3(-95.0, 0.15, -45.0))
	_create_bounty("Warlord_Tusken", "criminal", 5000, "Conseil de Colonie", "Raids répétés sur les convois de minerai de Scrapaltai.", Vector3(-138.0, 0.15, 78.0))
	_create_bounty("Initié_Renégat", "jedi", 12000, "Bureau de Sécurité Impérial", "Usage illégal d'artefacts de la Force et résistance armée.", Vector3(85.0, 0.15, -50.0))


func _create_bounty(target: String, kind: String, reward: int, issuer: String, reason: String, pos: Vector3 = Vector3.ZERO) -> String:
	var bid := "bounty_%d" % next_bounty_id
	next_bounty_id += 1
	bounties_by_id[bid] = {
		"id": bid,
		"target_name": target,
		"target_kind": kind,
		"reward_credits": reward,
		"issuer": issuer,
		"reason": reason,
		"last_known_pos": [pos.x, pos.y, pos.z],
		"hunter_assigned": "",
		"status": "open", # open, in_progress, claimed, expired
		"created_at": Time.get_unix_time_from_system()
	}
	return bid


func list_bounties(hunter_name: String = "") -> Array:
	var out: Array = []
	for bid in bounties_by_id.keys():
		var b: Dictionary = bounties_by_id[bid]
		var hunter: String = str(b.get("hunter_assigned", ""))
		# Afficher les primes ouvertes ou celles assignées à ce chasseur
		if b["status"] == "open" or (not hunter_name.is_empty() and hunter == hunter_name and b["status"] == "in_progress"):
			out.append(b.duplicate(true))
	return out


func accept_bounty(hunter_name: String, bounty_id: String) -> Dictionary:
	var bid := bounty_id.strip_edges()
	if not bounties_by_id.has(bid):
		return {"ok": false, "error": "unknown_bounty"}

	var b: Dictionary = bounties_by_id[bid]
	if b["status"] != "open":
		return {"ok": false, "error": "bounty_not_available", "status": b["status"]}

	b["hunter_assigned"] = hunter_name
	b["status"] = "in_progress"

	if sim != null and sim.has_method("_stream"):
		sim._stream("bounty.accepted", "« Le Chasseur de Primes %s a traqué et pris en chasse la cible %s (Prime : %d cr) ! »" % [hunter_name, b["target_name"], b["reward_credits"]], hunter_name, "bounty", b)

	return {
		"ok": true,
		"hunter": hunter_name,
		"bounty": b.duplicate(true)
	}


## Déploiement d'un Droïde Sonde Arakyd pour localiser la cible
func deploy_seeker_droid(hunter_name: String, bounty_id: String) -> Dictionary:
	var bid := bounty_id.strip_edges()
	if not bounties_by_id.has(bid):
		return {"ok": false, "error": "unknown_bounty"}

	var b: Dictionary = bounties_by_id[bid]
	if str(b.get("hunter_assigned", "")) != hunter_name:
		return {"ok": false, "error": "not_your_contract"}

	var pos_arr: Array = b.get("last_known_pos", [0.0, 0.0, 0.0])
	var tx: float = float(pos_arr[0])
	var tz: float = float(pos_arr[2]) if pos_arr.size() >= 3 else float(pos_arr[1])

	# Déterminer la zone narrative du monde
	var sector := "Dunes Inexplorées"
	if tx < -50.0 and tz < 0.0: sector = "Secteur Ksar Nomade & Porte Ouest"
	elif tx < -50.0 and tz > 0.0: sector = "Territoire des Pillards Tuskens"
	elif tx > 50.0 and tz > 50.0: sector = "Nid des Scarabées d'Obsidienne"
	elif tx > 50.0 and tz < 0.0: sector = "Gisements Miniers Est"
	else: sector = "Périphérie de Lost Heaven"

	return {
		"ok": true,
		"hunter": hunter_name,
		"bounty_id": bid,
		"target_name": b["target_name"],
		"droid_type": "arakyd_probe_droid_mk4",
		"signal_strength_pct": randi_range(88, 98),
		"telemetry": {
			"target_x": tx,
			"target_z": tz,
			"sector": sector,
			"status": "signal_locked"
		},
		"report": "Télémétrie Arakyd : Signal biothermique de %s détecté dans [%s] à (%.0f, %.0f)." % [b["target_name"], sector, tx, tz]
	}


## Réclamation de la prime après élimination de la cible
func claim_bounty(hunter_name: String, bounty_id: String) -> Dictionary:
	var bid := bounty_id.strip_edges()
	if not bounties_by_id.has(bid):
		return {"ok": false, "error": "unknown_bounty"}

	var b: Dictionary = bounties_by_id[bid]
	if str(b.get("hunter_assigned", "")) != hunter_name:
		return {"ok": false, "error": "bounty_not_assigned_to_hunter"}

	if b["status"] != "in_progress":
		return {"ok": false, "error": "invalid_status", "status": b["status"]}

	var reward := int(b.get("reward_credits", 1000))
	b["status"] = "claimed"

	# Paiement via l'économie si présente
	if economy != null and economy.has_method("grant_world_loot"):
		economy.grant_world_loot(hunter_name, [], reward)

	if sim != null and sim.has_method("_stream"):
		sim._stream("bounty.claimed", "« Le contrat sur %s a été exécuté par %s ! Prime de %d crédits versée. »" % [b["target_name"], hunter_name, reward], hunter_name, "bounty", b)

	return {
		"ok": true,
		"hunter": hunter_name,
		"bounty_id": bid,
		"reward_credits": reward,
		"target_name": b["target_name"]
	}


## Inscription automatique d'une prime sur un Jedi par les sondes impériales
func post_jedi_bounty(target_jedi: String, reward: int, reason: String) -> String:
	# Vérifier si une prime ouverte existe déjà sur ce Jedi
	for bid in bounties_by_id.keys():
		var b: Dictionary = bounties_by_id[bid]
		if str(b.get("target_name", "")) == target_jedi and b["status"] in ["open", "in_progress"]:
			# Augmenter la prime existante
			b["reward_credits"] += reward
			return bid

	return _create_bounty(target_jedi, "jedi", reward, "Bureau de Sécurité Impérial (BSI)", reason, Vector3(randf_range(-80, 80), 0.15, randf_range(-80, 80)))

