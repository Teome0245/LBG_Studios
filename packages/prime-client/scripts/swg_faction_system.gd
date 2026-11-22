class_name SwgFactionSystem
extends Node
## Système des Factions du Multivers & Guerre d'Influence (Prime / Lost Heaven)
## Repose sur le squelette systémique de SWG Pre-CU (Points de faction, On-Leave, Special Forces PvP)
## mais adopte l'âme visuelle et thématique du Multivers LBG :
## - Convergence Synthetika (Gunnm, Cyberpunk, Mechari)
## - Cercle des Arcanes Primordiaux (Avatar, FMA, DBZ, Chi & Alchimie)
## - Coalition des Mondes Brisés (Firefly, Albator, Discworld, Corsaires du Vide)

signal faction_status_changed(faction: String, status: String)
signal faction_points_changed(faction: String, points: int)
signal overt_pvp_warning(is_special_forces: bool)

enum Faction {
	NEUTRAL = 0,
	CONVERGENCE_SYNTHETIKA = 1,
	CERCLE_DES_ARCANES = 2,
	COALITION_MONDES_BRISES = 3,
	# Alias rétro-compatibilité SWG
	IMPERIAL = 1,
	REBEL = 2
}

enum FactionStatus { CIVILIAN, ON_LEAVE, SPECIAL_FORCES }

const FACTION_METADATA := {
	Faction.NEUTRAL: {
		"id": "neutral",
		"name": "Neutre",
		"prime_name": "Sans Allégeance (Indépendant)",
		"motto": "« Libre parmi les mondes. »",
		"color": Color(0.75, 0.75, 0.75),
		"style": "Nomade / Explorateur",
		"refs": ["Nomade", "Marchand Indépendant"]
	},
	Faction.CONVERGENCE_SYNTHETIKA: {
		"id": "synthetika",
		"name": "Impérial",
		"prime_name": "Convergence Synthetika",
		"motto": "« Le silicium sublime la chair. »",
		"color": Color(0.0, 0.9, 1.0),
		"style": "Cyberpunk / Gunnm / Mechari",
		"refs": ["Gunnm", "Cyberpunk 2077", "Ghost in the Shell"]
	},
	Faction.CERCLE_DES_ARCANES: {
		"id": "arcanes",
		"name": "Rebelle",
		"prime_name": "Cercle des Arcanes Primordiaux",
		"motto": "« De la terre au cosmos, l'énergie transmute. »",
		"color": Color(1.0, 0.8, 0.2),
		"style": "Chi / Alchimie / Maîtrise Élémentaire",
		"refs": ["Fullmetal Alchemist", "Avatar", "Dragon Ball Z"]
	},
	Faction.COALITION_MONDES_BRISES: {
		"id": "coalition",
		"name": "Coalition",
		"prime_name": "Coalition des Mondes Brisés",
		"motto": "« Rouille, liberté et cap sur l'inconnu. »",
		"color": Color(0.95, 0.45, 0.2),
		"style": "Corsaires du Vide / Steampunk",
		"refs": ["Firefly", "Albator", "Discworld"]
	}
}

var current_faction: Faction = Faction.NEUTRAL
var current_status: FactionStatus = FactionStatus.CIVILIAN

var synthetika_points: int = 250
var arcanes_points: int = 100
var coalition_points: int = 150

# Rétro-compatibilité pour les propriétés et tests existants SWG
var imperial_points: int:
	get: return synthetika_points
	set(val): synthetika_points = val

var rebel_points: int:
	get: return arcanes_points
	set(val): arcanes_points = val

var imperial_rank: String = "Citoyen Impérial"
var rebel_rank: String = "Sympathisant Rebelle"
var prime_rank: String = "Voyageur Neutre"


func _ready() -> void:
	name = "SwgFactionSystem"
	_update_military_ranks()


func get_faction_name() -> String:
	match current_faction:
		Faction.CONVERGENCE_SYNTHETIKA: return "Impérial"
		Faction.CERCLE_DES_ARCANES: return "Rebelle"
		Faction.COALITION_MONDES_BRISES: return "Coalition"
		_: return "Neutre"


func get_faction_prime_name() -> String:
	var meta: Dictionary = FACTION_METADATA.get(current_faction, {})
	return meta.get("prime_name", "Sans Allégeance")


func get_faction_color() -> Color:
	var meta: Dictionary = FACTION_METADATA.get(current_faction, {})
	return meta.get("color", Color(0.7, 0.7, 0.7))


func get_faction_motto() -> String:
	var meta: Dictionary = FACTION_METADATA.get(current_faction, {})
	return meta.get("motto", "")


func get_faction_style() -> String:
	var meta: Dictionary = FACTION_METADATA.get(current_faction, {})
	return meta.get("style", "")


func get_status_name() -> String:
	match current_status:
		FactionStatus.ON_LEAVE: return "On-Leave (En permission)"
		FactionStatus.SPECIAL_FORCES: return "Special Forces (PvP Actif)"
		_: return "Civilian (Non-Combattant)"


func is_special_forces() -> bool:
	return current_status == FactionStatus.SPECIAL_FORCES


func is_enemy(other_faction: String, other_is_sf: bool = false) -> bool:
	if current_faction == Faction.NEUTRAL:
		return false
	
	var my_legacy := get_faction_name()
	var my_prime := get_faction_prime_name()
	
	if other_faction == my_legacy or other_faction == my_prime or other_faction == "Neutre" or other_faction.begins_with("Sans Allégeance"):
		return false
	
	# En Special Forces : ennemi direct de toutes les autres factions
	if current_status == FactionStatus.SPECIAL_FORCES:
		return true
	
	# En On-Leave : hostile seulement contre les PNJ de faction, pas les joueurs pacifiques
	if current_status == FactionStatus.ON_LEAVE and not other_is_sf:
		return true
		
	return false


## Change d'alignement auprès d'un recruteur
func enlist(faction_type: Faction) -> void:
	current_faction = faction_type
	current_status = FactionStatus.ON_LEAVE
	_update_military_ranks()
	faction_status_changed.emit(get_faction_name(), get_status_name())


## Démission / Retour au statut civil
func resign_to_civilian() -> void:
	current_faction = Faction.NEUTRAL
	current_status = FactionStatus.CIVILIAN
	_update_military_ranks()
	faction_status_changed.emit(get_faction_name(), get_status_name())
	overt_pvp_warning.emit(false)


## Déclaration Special Forces (Overt PvP)
func declare_special_forces() -> void:
	if current_faction == Faction.NEUTRAL:
		return
	current_status = FactionStatus.SPECIAL_FORCES
	faction_status_changed.emit(get_faction_name(), get_status_name())
	overt_pvp_warning.emit(true)


## Repasser en permission (On-Leave)
func go_on_leave() -> void:
	if current_faction == Faction.NEUTRAL:
		return
	current_status = FactionStatus.ON_LEAVE
	faction_status_changed.emit(get_faction_name(), get_status_name())
	overt_pvp_warning.emit(false)


func add_faction_points(faction: Faction, amount: int) -> void:
	match faction:
		Faction.CONVERGENCE_SYNTHETIKA:
			synthetika_points = maxi(0, synthetika_points + amount)
			faction_points_changed.emit("Impérial", synthetika_points)
		Faction.CERCLE_DES_ARCANES:
			arcanes_points = maxi(0, arcanes_points + amount)
			faction_points_changed.emit("Rebelle", arcanes_points)
		Faction.COALITION_MONDES_BRISES:
			coalition_points = maxi(0, coalition_points + amount)
			faction_points_changed.emit("Coalition", coalition_points)
	_update_military_ranks()


func _update_military_ranks() -> void:
	# 1. Synthetika (hérite des points/rangs impériaux)
	if synthetika_points >= 2000:
		imperial_rank = "Colonel Impérial"
		if current_faction == Faction.CONVERGENCE_SYNTHETIKA:
			prime_rank = "Archi-Cyborg de l'Omni-Noyau"
	elif synthetika_points >= 1000:
		imperial_rank = "Major Impérial"
		if current_faction == Faction.CONVERGENCE_SYNTHETIKA:
			prime_rank = "Commandeur Mécatronique"
	elif synthetika_points >= 500:
		imperial_rank = "Lieutenant Impérial"
		if current_faction == Faction.CONVERGENCE_SYNTHETIKA:
			prime_rank = "Ingénieur Prothésiste de Rang I"
	elif synthetika_points >= 200:
		imperial_rank = "Sergent Stormtrooper"
		if current_faction == Faction.CONVERGENCE_SYNTHETIKA:
			prime_rank = "Opérateur Câblé"
	else:
		imperial_rank = "Recrue Impériale"
		if current_faction == Faction.CONVERGENCE_SYNTHETIKA:
			prime_rank = "Initié Mécatronique"

	# 2. Arcanes (hérite des points/rangs rebelles)
	if arcanes_points >= 2000:
		rebel_rank = "Général de l'Alliance"
		if current_faction == Faction.CERCLE_DES_ARCANES:
			prime_rank = "Grand Alchimiste d'Éther"
	elif arcanes_points >= 1000:
		rebel_rank = "Commandant Rebelle"
		if current_faction == Faction.CERCLE_DES_ARCANES:
			prime_rank = "Maître de Transmutation"
	elif arcanes_points >= 500:
		rebel_rank = "Capitaine Rebelle"
		if current_faction == Faction.CERCLE_DES_ARCANES:
			prime_rank = "Canalisateur de Chi"
	elif arcanes_points >= 200:
		rebel_rank = "Éclaireur de l'Alliance"
		if current_faction == Faction.CERCLE_DES_ARCANES:
			prime_rank = "Adepte Élémentaire"
	else:
		rebel_rank = "Volontaire Rebelle"
		if current_faction == Faction.CERCLE_DES_ARCANES:
			prime_rank = "Novice Alchimique"

	# 3. Coalition des Mondes Brisés
	if current_faction == Faction.COALITION_MONDES_BRISES:
		if coalition_points >= 2000:
			prime_rank = "Corsaire Céleste Légendaire"
		elif coalition_points >= 1000:
			prime_rank = "Capitaine de Frégate du Vide"
		elif coalition_points >= 500:
			prime_rank = "Navigateur de Scrapaltai"
		elif coalition_points >= 200:
			prime_rank = "Flibustier de Bord"
		else:
			prime_rank = "Matelot de Rouille"
	elif current_faction == Faction.NEUTRAL:
		prime_rank = "Voyageur Indépendant"
