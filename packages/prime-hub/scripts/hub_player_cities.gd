# hub_player_cities.gd — Système de Villes de Joueurs & Politique SWG Pre-CU
# Gère la fondation de villes par les joueurs, l'évolution en 5 échelons (Outpost -> Metropolis),
# les élections démocratiques de maires, la fiscalité municipale et les spécialisations civiques.
class_name HubPlayerCities
extends RefCounted

signal city_founded(city_id: String, city_name: String, mayor: String)
signal citizen_registered(city_id: String, citizen_name: String)
signal election_concluded(city_id: String, winner_mayor: String)
signal civic_structure_placed(city_id: String, structure_type: String, pos: Vector3)

# Échelons de ville SWG Pre-CU
const RANKS: Array[Dictionary] = [
	{"rank": 1, "name": "Outpost", "min_citizens": 5, "radius_m": 150.0, "max_civic": 2},
	{"rank": 2, "name": "Village", "min_citizens": 10, "radius_m": 200.0, "max_civic": 4},
	{"rank": 3, "name": "Township", "min_citizens": 20, "radius_m": 300.0, "max_civic": 7},
	{"rank": 4, "name": "City", "min_citizens": 35, "radius_m": 400.0, "max_civic": 12},
	{"rank": 5, "name": "Metropolis", "min_citizens": 55, "radius_m": 500.0, "max_civic": 20}
]

# Spécialisations de ville (bonus locaux)
const SPECIALIZATIONS: Dictionary = {
	"none": {"name": "Aucune", "desc": "Pas de bonus actif", "maintenance_cost": 0},
	"manufacturing": {"name": "Centre Industriel", "desc": "-10% temps de fabrication usine, +5% succès craft", "maintenance_cost": 2500},
	"medical": {"name": "Sanctuaire Médical", "desc": "+20% guérison HAM & mal de clonage accéléré", "maintenance_cost": 2000},
	"research": {"name": "Avant-poste Scientifique", "desc": "+10% qualité d'échantillonnage de ressources", "maintenance_cost": 3000},
	"entertainment": {"name": "District des Plaisirs", "desc": "+25% durée des buffs de Cantina et spectacle", "maintenance_cost": 1500},
	"clone_haven": {"name": "Refuge de Clonage", "desc": "Assurance et clonage gratuits pour les résidents", "maintenance_cost": 3500}
}

# Registre des villes : city_id -> Dictionary
var cities: Dictionary = {}
var economy_ref = null # Optionnel : lien avec HubEconomy

func _init(p_economy = null) -> void:
	economy_ref = p_economy
	_seed_default_cities()

func _seed_default_cities() -> void:
	# Ville pionnière de joueurs établie à proximité de Lost Heaven
	var pioneer_city = {
		"id": "city_new_coronet",
		"name": "New Coronet",
		"mayor": "Bail_Organa",
		"rank": 3, # Township
		"rank_name": "Township",
		"radius_m": 300.0,
		"center_pos": [450.0, 0.15, -400.0],
		"treasury": 45000,
		"specialization": "manufacturing",
		"tax_rates": {
			"property_tax": 50,      # Prélevé par bâtiment/semaine
			"income_tax": 5,          # 5% sur ventes des marchands
			"travel_tax": 100         # Taxe additionnelle spatioport
		},
		"citizens": [
			"Bail_Organa", "Lia_Ingénieure", "Sola_Armurière", "Mira_Tisseuse",
			"Jorik_Trappeur", "Doran_Prospecteur", "Nix_Sentinelle", "Jax_Barman",
			"Talen_Danseur", "Cael_Vagabond", "Vael_Capitaine", "Wedge_Antilles"
		],
		"election": {
			"is_active": true,
			"candidates": ["Bail_Organa", "Vael_Capitaine"],
			"votes": {
				"Bail_Organa": 7,
				"Vael_Capitaine": 4
			},
			"time_left_s": 120.0
		},
		"civic_structures": [
			{"type": "city_hall", "pos": [450.0, 0.15, -400.0], "name": "Hôtel de Ville de New Coronet"},
			{"type": "civic_bank", "pos": [420.0, 0.15, -380.0], "name": "Succursale Bancaire de New Coronet"},
			{"type": "civic_hospital", "pos": [480.0, 0.15, -420.0], "name": "Centre Médical & Clonage"},
			{"type": "civic_cantina", "pos": [440.0, 0.15, -440.0], "name": "Cantina Étoile Argentée"}
		],
		"created_at": 1794000000.0
	}
	cities[pioneer_city["id"]] = pioneer_city

# Fonde une nouvelle ville (nécessite un joueur et une position)
func found_city(founder_name: String, city_name: String, pos: Array) -> Dictionary:
	var clean_name = city_name.strip_edges()
	if clean_name.is_empty():
		return {"ok": false, "error": "Nom de ville invalide"}
	
	# Vérifier le nom unique
	for cid in cities:
		if cities[cid]["name"].to_lower() == clean_name.to_lower():
			return {"ok": false, "error": "Une ville porte déjà ce nom"}
	
	var city_id = "city_" + clean_name.to_lower().replace(" ", "_").replace("'", "")
	var new_city = {
		"id": city_id,
		"name": clean_name,
		"mayor": founder_name,
		"rank": 1, # Outpost
		"rank_name": "Outpost",
		"radius_m": 150.0,
		"center_pos": pos,
		"treasury": 10000,
		"specialization": "none",
		"tax_rates": {
			"property_tax": 25,
			"income_tax": 2,
			"travel_tax": 50
		},
		"citizens": [founder_name],
		"election": {
			"is_active": false,
			"candidates": [founder_name],
			"votes": {},
			"time_left_s": 0.0
		},
		"civic_structures": [
			{"type": "city_hall", "pos": pos, "name": "Hôtel de Ville de " + clean_name}
		],
		"created_at": Time.get_unix_time_from_system()
	}
	
	cities[city_id] = new_city
	city_founded.emit(city_id, clean_name, founder_name)
	return {"ok": true, "city": new_city}

# Enregistre un nouveau citoyen dans la ville
func register_citizen(city_id: String, citizen_name: String) -> Dictionary:
	if not cities.has(city_id):
		return {"ok": false, "error": "Ville introuvable"}
	
	var city = cities[city_id]
	var citizens: Array = city["citizens"]
	
	if citizens.has(citizen_name):
		return {"ok": false, "error": "Déjà citoyen de cette ville"}
	
	# Retirer le citoyen de toute autre ville existante
	for other_id in cities:
		var other_citizens: Array = cities[other_id]["citizens"]
		if other_citizens.has(citizen_name):
			other_citizens.erase(citizen_name)
	
	citizens.append(citizen_name)
	_update_city_rank(city_id)
	
	citizen_registered.emit(city_id, citizen_name)
	return {"ok": true, "city_id": city_id, "citizen_count": citizens.size(), "rank_name": city["rank_name"]}

# Met à jour le grade de la ville selon le nombre de citoyens
func _update_city_rank(city_id: String) -> void:
	if not cities.has(city_id):
		return
	var city = cities[city_id]
	var c_count = city["citizens"].size()
	
	var chosen_rank = RANKS[0]
	for r in RANKS:
		if c_count >= r["min_citizens"]:
			chosen_rank = r
	
	city["rank"] = chosen_rank["rank"]
	city["rank_name"] = chosen_rank["name"]
	city["radius_m"] = chosen_rank["radius_m"]

# Lancement d'une élection municipale
func start_election(city_id: String) -> Dictionary:
	if not cities.has(city_id):
		return {"ok": false, "error": "Ville introuvable"}
	
	var city = cities[city_id]
	var election: Dictionary = city["election"]
	election["is_active"] = true
	election["candidates"] = [city["mayor"]]
	election["votes"] = {}
	election["time_left_s"] = 180.0 # 3 minutes pour le selftest / cycle démo
	return {"ok": true, "election": election}

# Vote pour un candidat
func cast_vote(city_id: String, citizen_name: String, candidate_name: String) -> Dictionary:
	if not cities.has(city_id):
		return {"ok": false, "error": "Ville introuvable"}
	
	var city = cities[city_id]
	if not city["citizens"].has(citizen_name):
		return {"ok": false, "error": "Seuls les citoyens résidents peuvent voter"}
	
	var election: Dictionary = city["election"]
	if not election.get("is_active", false):
		return {"ok": false, "error": "Aucune élection municipale en cours"}
	
	var candidates: Array = election["candidates"]
	if not candidates.has(candidate_name):
		# Auto-déclaration de candidature si le candidat est citoyen
		if city["citizens"].has(candidate_name):
			candidates.append(candidate_name)
		else:
			return {"ok": false, "error": "Le candidat doit être citoyen de la ville"}
	
	var votes: Dictionary = election["votes"]
	votes[candidate_name] = int(votes.get(candidate_name, 0)) + 1
	
	return {
		"ok": true,
		"city_id": city_id,
		"candidate": candidate_name,
		"total_votes": votes[candidate_name]
	}

# Conclut l'élection et proclame le vainqueur
func conclude_election(city_id: String) -> Dictionary:
	if not cities.has(city_id):
		return {"ok": false, "error": "Ville introuvable"}
	
	var city = cities[city_id]
	var election: Dictionary = city["election"]
	if not election.get("is_active", false):
		return {"ok": false, "error": "Pas d'élection en cours"}
	
	var votes: Dictionary = election["votes"]
	var max_v = -1
	var winner = city["mayor"]
	
	for c_name in votes:
		var v_count = int(votes[c_name])
		if v_count > max_v:
			max_v = v_count
			winner = c_name
	
	city["mayor"] = winner
	election["is_active"] = false
	election["time_left_s"] = 0.0
	
	election_concluded.emit(city_id, winner)
	return {"ok": true, "city_id": city_id, "new_mayor": winner, "votes": max_v}

# Modification de la fiscalité par le Maire
func set_taxes(city_id: String, actor_name: String, prop_tax: int, inc_tax: int, trav_tax: int) -> Dictionary:
	if not cities.has(city_id):
		return {"ok": false, "error": "Ville introuvable"}
	var city = cities[city_id]
	if city["mayor"] != actor_name:
		return {"ok": false, "error": "Seul le Maire peut modifier les impôts municipaux"}
	
	city["tax_rates"]["property_tax"] = clampi(prop_tax, 0, 500)
	city["tax_rates"]["income_tax"] = clampi(inc_tax, 0, 20)
	city["tax_rates"]["travel_tax"] = clampi(trav_tax, 0, 1000)
	
	return {"ok": true, "tax_rates": city["tax_rates"]}

# Choix de spécialisation civique par le Maire
func set_specialization(city_id: String, actor_name: String, spec_key: String) -> Dictionary:
	if not cities.has(city_id):
		return {"ok": false, "error": "Ville introuvable"}
	var city = cities[city_id]
	if city["mayor"] != actor_name:
		return {"ok": false, "error": "Seul le Maire peut décréter une spécialisation civique"}
	
	if not SPECIALIZATIONS.has(spec_key):
		return {"ok": false, "error": "Spécialisation inconnue"}
	
	city["specialization"] = spec_key
	return {
		"ok": true,
		"specialization": spec_key,
		"details": SPECIALIZATIONS[spec_key]
	}

# Ajout d'une structure civique
func place_civic_structure(city_id: String, actor_name: String, structure_type: String, pos: Array, s_name: String = "") -> Dictionary:
	if not cities.has(city_id):
		return {"ok": false, "error": "Ville introuvable"}
	var city = cities[city_id]
	if city["mayor"] != actor_name:
		return {"ok": false, "error": "Seul le Maire peut implanter des bâtiments civiques"}
	
	var structures: Array = city["civic_structures"]
	var cur_rank: int = int(city["rank"])
	var rank_info = RANKS[cur_rank - 1]
	
	if structures.size() >= rank_info["max_civic"]:
		return {"ok": false, "error": "Capacité maximale de bâtiments civiques atteinte pour ce grade de ville"}
	
	var label = s_name
	if label.is_empty():
		label = "Structure " + structure_type.capitalize()
	
	var new_struct = {
		"type": structure_type,
		"pos": pos,
		"name": label
	}
	structures.append(new_struct)
	civic_structure_placed.emit(city_id, structure_type, Vector3(pos[0], pos[1], pos[2]))
	
	return {"ok": true, "city_id": city_id, "structure": new_struct, "total_civic": structures.size()}

# Tick temporel du système politique et municipal
func tick(delta: float) -> void:
	for cid in cities:
		var city = cities[cid]
		var election: Dictionary = city["election"]
		if election.get("is_active", false):
			var tl: float = election.get("time_left_s", 0.0) - delta
			if tl <= 0.0:
				conclude_election(cid)
			else:
				election["time_left_s"] = tl

# Données d'état complètes d'une ville
func get_city_status(city_id: String) -> Dictionary:
	if not cities.has(city_id):
		return {"ok": false, "error": "Ville introuvable"}
	var c = cities[city_id]
	return {
		"ok": true,
		"city": c,
		"specialization_info": SPECIALIZATIONS.get(c.get("specialization", "none"), {})
	}

# Liste résumée des villes
func get_all_cities() -> Array:
	var res: Array = []
	for cid in cities:
		var c = cities[cid]
		res.append({
			"id": c["id"],
			"name": c["name"],
			"mayor": c["mayor"],
			"rank": c["rank"],
			"rank_name": c["rank_name"],
			"citizens_count": c["citizens"].size(),
			"specialization": c["specialization"],
			"center_pos": c["center_pos"]
		})
	return res

