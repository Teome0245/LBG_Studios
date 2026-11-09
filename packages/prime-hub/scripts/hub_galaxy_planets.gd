# hub_galaxy_planets.gd — Système Multi-Planètes & Biomes Stellaires SWG Pre-CU
# Définit les 5 planètes majeures de SWG (Tatooine, Naboo, Endor, Dathomir, Corellia)
# avec leurs atmosphères, biomes, faunes locales, profils d'éclairage et transit inter-mondes.
class_name HubGalaxyPlanets
extends RefCounted

signal planet_transitioned(player_name: String, source_planet: String, dest_planet: String)

const PLANETS: Dictionary = {
	"tatooine": {
		"name": "Tatooine",
		"zone_id": "scrapaltai",
		"description": "Monde désertique aride balayé par les vents et baigné par un soleil binaire.",
		"biome": "desert_dunes",
		"ambient_color": "#fff6d6",
		"sky_color": "#e0cda7",
		"fog_density": 0.0008,
		"gravity_m_s2": 9.8,
		"weather_types": ["clear", "heat_shimmer", "sandstorm"],
		"capital": "Mos Eisley / Lost Heaven",
		"dominant_fauna": ["chacal_des_dunes", "bantha_sauvage", "dewback_cuirasse", "krayt_dragon"],
		"shuttle_ticket_cost": 250
	},
	"naboo": {
		"name": "Naboo",
		"zone_id": "theed_valleys",
		"description": "Joyau verdoyant parsemé de plaines luxuriantes, cascades royales et marécages profonds.",
		"biome": "lush_plains_wetlands",
		"ambient_color": "#d0f4e6",
		"sky_color": "#87ceeb",
		"fog_density": 0.0012,
		"gravity_m_s2": 9.8,
		"weather_types": ["clear", "light_rain", "morning_mist"],
		"capital": "Theed",
		"dominant_fauna": ["fambaa", "kaadu", "peeko_peeko"],
		"shuttle_ticket_cost": 350
	},
	"endor": {
		"name": "Endor (Lune Forestière)",
		"zone_id": "endor_forest",
		"description": "Canopée colossale de séquoias géants, villages suspendus et sous-bois humides.",
		"biome": "primeval_redwood_forest",
		"ambient_color": "#a8cfa8",
		"sky_color": "#5f8575",
		"fog_density": 0.0035,
		"gravity_m_s2": 8.3,
		"weather_types": ["drizzle", "dense_canopy_fog", "thunderstorm"],
		"capital": "Village Arboricole Ewok",
		"dominant_fauna": ["boar_wolf", "gorax", "forest_mite"],
		"shuttle_ticket_cost": 450
	},
	"dathomir": {
		"name": "Dathomir",
		"zone_id": "dathomir_wastes",
		"description": "Monde hostile et brumeux au ciel carmin, repaire des Sœurs de la Nuit et de Rancors féroces.",
		"biome": "toxic_quarantine_badlands",
		"ambient_color": "#e27878",
		"sky_color": "#5b1414",
		"fog_density": 0.0045,
		"gravity_m_s2": 10.2,
		"weather_types": ["blood_mist", "acid_rain", "spectral_glow"],
		"capital": "Avant-poste Scientifique Impérial",
		"dominant_fauna": ["rancor_sauvage", "nightsister_spider", "mutant_gurreck"],
		"shuttle_ticket_cost": 600
	},
	"corellia": {
		"name": "Corellia",
		"zone_id": "coronet_city",
		"description": "Berceau de l'ingénierie navale, collines tempérées et ports côtiers effervescents.",
		"biome": "temperate_coastal_industrial",
		"ambient_color": "#e0e4eb",
		"sky_color": "#7ba7cc",
		"fog_density": 0.0010,
		"gravity_m_s2": 9.8,
		"weather_types": ["coastal_breeze", "overcast", "industrial_haze"],
		"capital": "Coronet City",
		"dominant_fauna": ["corellian_sand_panther", "durni", "carrion_spat"],
		"shuttle_ticket_cost": 300
	}
}

# Localisation des joueurs : player_name -> planet_id
var player_locations: Dictionary = {}

func _init() -> void:
	pass

# Déplace un joueur vers une planète donnée
func travel_to_planet(player_name: String, dest_planet_id: String) -> Dictionary:
	var clean_dest = dest_planet_id.to_lower().strip_edges()
	if not PLANETS.has(clean_dest):
		return {"ok": false, "error": "Planète de destination inconnue"}
	
	var src_planet = player_locations.get(player_name, "tatooine")
	if src_planet == clean_dest:
		return {"ok": false, "error": "Le joueur est déjà sur " + PLANETS[clean_dest]["name"]}
	
	player_locations[player_name] = clean_dest
	planet_transitioned.emit(player_name, src_planet, clean_dest)
	
	var p_info = PLANETS[clean_dest]
	return {
		"ok": true,
		"player": player_name,
		"previous_planet": src_planet,
		"current_planet": clean_dest,
		"planet_name": p_info["name"],
		"capital": p_info["capital"],
		"ambient": {
			"ambient_color": p_info["ambient_color"],
			"sky_color": p_info["sky_color"],
			"fog_density": p_info["fog_density"]
		}
	}

# Profil d'ambiance et météo d'une planète
func get_ambient_profile(planet_id: String) -> Dictionary:
	var clean_id = planet_id.to_lower().strip_edges()
	if not PLANETS.has(clean_id):
		return {"ok": false, "error": "Planète inconnue"}
	
	var p = PLANETS[clean_id]
	return {
		"ok": true,
		"planet_id": clean_id,
		"name": p["name"],
		"biome": p["biome"],
		"weather_pool": p["weather_types"],
		"lighting": {
			"ambient_color": p["ambient_color"],
			"sky_color": p["sky_color"],
			"fog_density": p["fog_density"]
		},
		"fauna": p["dominant_fauna"]
	}

# Liste de toutes les planètes
func get_all_planets() -> Array:
	var res: Array = []
	for p_id in PLANETS:
		var p = PLANETS[p_id]
		res.append({
			"id": p_id,
			"name": p["name"],
			"biome": p["biome"],
			"capital": p["capital"],
			"shuttle_ticket_cost": p["shuttle_ticket_cost"]
		})
	return res

