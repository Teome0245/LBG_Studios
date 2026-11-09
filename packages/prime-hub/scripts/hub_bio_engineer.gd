# hub_bio_engineer.gd — Système de Bio-Ingénierie & Échantillonnage ADN SWG Pre-CU
# Permet aux joueurs de prélever des brins d'ADN sur la faune sauvage, d'analyser les profils génétiques,
# d'incuber des embryons de créatures mutées (pour Creature Handlers) et de synthétiser des enzymes biomédicales.
class_name HubBioEngineer
extends RefCounted

signal dna_sampled(player_name: String, creature_type: String, quality: int, dna_id: String)
signal creature_incubated(player_name: String, embryo_name: String, stats: Dictionary)

# Qualité des profils d'ADN
const DNA_PROFILES: Dictionary = {
	"chacal_des_dunes": {
		"label": "Chacal des Dunes",
		"base_prowess": 45,
		"base_hardiness": 40,
		"base_courage": 60,
		"special_attack": "Bite Flurry",
		"preferred_diet": "carnivore"
	},
	"bantha_sauvage": {
		"label": "Bantha Sauvage",
		"base_prowess": 75,
		"base_hardiness": 90,
		"base_courage": 50,
		"special_attack": "Trample",
		"preferred_diet": "herbivore"
	},
	"dewback_cuirasse": {
		"label": "Dewback Cuirassé",
		"base_prowess": 80,
		"base_hardiness": 85,
		"base_courage": 70,
		"special_attack": "Tail Swipe",
		"preferred_diet": "carnivore"
	},
	"krayt_dragon": {
		"label": "Dragon Krayt Ancien",
		"base_prowess": 99,
		"base_hardiness": 98,
		"base_courage": 95,
		"special_attack": "Acid Breath",
		"preferred_diet": "apex_predator"
	}
}

# Registre des échantillons prélevés par joueur : player_name -> Array[Dictionary]
var player_dna_vault: Dictionary = {}
# Registre des embryons / créatures incubées : player_name -> Array[Dictionary]
var player_incubator: Dictionary = {}

var next_dna_id: int = 1001
var next_embryo_id: int = 2001

# Prélèvement d'ADN sur une créature vivante
func sample_dna(player_name: String, creature_type: String, distance_to_target_m: float = 4.0) -> Dictionary:
	var clean_type = creature_type.to_lower().strip_edges()
	if not DNA_PROFILES.has(clean_type):
		return {"ok": false, "error": "Espèce inconnue ou incompatible avec l'échantillonneur d'ADN"}
	
	if distance_to_target_m > 7.0:
		return {"ok": false, "error": "Cible trop éloignée pour la sonde d'échantillonnage (portée max 7m)"}
	
	var profile = DNA_PROFILES[clean_type]
	# Calcul de qualité d'échantillonnage (dépend d'une variance génétique 50..100)
	var rng = randf()
	var quality = int(lerp(55.0, 99.0, rng))
	
	var dna_id = "dna_" + str(next_dna_id)
	next_dna_id += 1
	
	var dna_sample = {
		"id": dna_id,
		"creature_type": clean_type,
		"label": profile["label"],
		"quality": quality,
		"prowess": int(float(profile["base_prowess"]) * (float(quality) / 100.0)),
		"hardiness": int(float(profile["base_hardiness"]) * (float(quality) / 100.0)),
		"courage": int(float(profile["base_courage"]) * (float(quality) / 100.0)),
		"special_attack": profile["special_attack"],
		"timestamp": Time.get_unix_time_from_system()
	}
	
	if not player_dna_vault.has(player_name):
		player_dna_vault[player_name] = []
	player_dna_vault[player_name].append(dna_sample)
	
	dna_sampled.emit(player_name, clean_type, quality, dna_id)
	return {"ok": true, "sample": dna_sample}

# Incubation en laboratoire génétique : fusion de 2 échantillons pour forger un embryon hybride
func incubate_creature(player_name: String, dna_id_1: String, dna_id_2: String, custom_name: String = "") -> Dictionary:
	if not player_dna_vault.has(player_name):
		return {"ok": false, "error": "Aucun échantillon d'ADN disponible"}
	
	var vault: Array = player_dna_vault[player_name]
	var s1 = null
	var s2 = null
	
	for s in vault:
		if s["id"] == dna_id_1:
			s1 = s
		elif s["id"] == dna_id_2:
			s2 = s
	
	if s1 == null or s2 == null:
		return {"ok": false, "error": "Un ou deux échantillons d'ADN sont introuvables"}
	
	# Consommer les échantillons
	vault.erase(s1)
	vault.erase(s2)
	
	var embryo_id = "embryo_" + str(next_embryo_id)
	next_embryo_id += 1
	
	var default_label = "Chimère " + s1["label"] + "-" + s2["label"]
	if not custom_name.strip_edges().is_empty():
		default_label = custom_name.strip_edges()
	
	var avg_prowess = int((float(s1["prowess"]) + float(s2["prowess"])) / 2.0 * 1.1) # 10% bonus d'hybridation
	var avg_hardiness = int((float(s1["hardiness"]) + float(s2["hardiness"])) / 2.0 * 1.1)
	var avg_courage = int((float(s1["courage"]) + float(s2["courage"])) / 2.0)
	var hybrid_quality = int((float(s1["quality"]) + float(s2["quality"])) / 2.0)
	
	var embryo = {
		"id": embryo_id,
		"name": default_label,
		"creator": player_name,
		"hybrid_quality": hybrid_quality,
		"stats": {
			"health": avg_hardiness * 120,
			"attack_power": avg_prowess * 15,
			"courage": avg_courage,
			"special_attack": s1["special_attack"] if randf() > 0.5 else s2["special_attack"]
		},
		"growth_stage": "embryo_ready", # Prêt à éclore via Creature Handler
		"created_at": Time.get_unix_time_from_system()
	}
	
	if not player_incubator.has(player_name):
		player_incubator[player_name] = []
	player_incubator[player_name].append(embryo)
	
	creature_incubated.emit(player_name, default_label, embryo["stats"])
	return {"ok": true, "embryo": embryo}

# Synthèse d'enzymes biomédicales (pour Médecins / Chefs cuisiniers)
func synthesize_enzyme(player_name: String, dna_id: String) -> Dictionary:
	if not player_dna_vault.has(player_name):
		return {"ok": false, "error": "Aucun échantillon disponible"}
	
	var vault: Array = player_dna_vault[player_name]
	var target_sample = null
	for s in vault:
		if s["id"] == dna_id:
			target_sample = s
			break
	
	if target_sample == null:
		return {"ok": false, "error": "Échantillon introuvable"}
	
	vault.erase(target_sample)
	var enzyme = {
		"id": "enzyme_" + str(next_embryo_id),
		"type": "stimulant_mutagene",
		"potency": int(target_sample["quality"]),
		"bonus_regen_ham": int(target_sample["hardiness"] / 2),
		"creator": player_name
	}
	next_embryo_id += 1
	return {"ok": true, "enzyme": enzyme}

# Obtenir les échantillons et embryons d'un joueur
func get_bio_status(player_name: String) -> Dictionary:
	return {
		"ok": true,
		"dna_samples": player_dna_vault.get(player_name, []),
		"incubated_embryos": player_incubator.get(player_name, []),
		"supported_creatures": DNA_PROFILES.keys()
	}

