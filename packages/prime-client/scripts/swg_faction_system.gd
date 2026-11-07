class_name SwgFactionSystem
extends Node
## Système de Factions & Guerre Civile Galactique (GCW) SWG Pre-CU
## Gère l'alignement (Neutre, Impérial, Rebelle), les statuts (Civilian, On-Leave, Special Forces),
## les points de faction (FP), les rangs militaires et les règles d'engagement PvP.

signal faction_status_changed(faction: String, status: String)
signal faction_points_changed(faction: String, points: int)
signal overt_pvp_warning(is_special_forces: bool)

enum Faction { NEUTRAL, IMPERIAL, REBEL }
enum FactionStatus { CIVILIAN, ON_LEAVE, SPECIAL_FORCES }

var current_faction: Faction = Faction.NEUTRAL
var current_status: FactionStatus = FactionStatus.CIVILIAN

var imperial_points: int = 250
var rebel_points: int = 100

var imperial_rank: String = "Citoyen Impérial"
var rebel_rank: String = "Sympathisant Rebelle"


func _ready() -> void:
	name = "SwgFactionSystem"
	_update_military_ranks()


func get_faction_name() -> String:
	match current_faction:
		Faction.IMPERIAL: return "Impérial"
		Faction.REBEL: return "Rebelle"
		_: return "Neutre"


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
	
	var my_f_str := get_faction_name()
	if other_faction == my_f_str or other_faction == "Neutre":
		return false
	
	# Si je suis Special Forces ou si l'autre est une cible ennemie de faction
	if current_status == FactionStatus.SPECIAL_FORCES:
		return true
	
	# En mode On-Leave, agressif uniquement contre les PNJ ennemis, pas les joueurs normaux
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
	if faction == Faction.IMPERIAL:
		imperial_points = maxi(0, imperial_points + amount)
		faction_points_changed.emit("Impérial", imperial_points)
	elif faction == Faction.REBEL:
		rebel_points = maxi(0, rebel_points + amount)
		faction_points_changed.emit("Rebelle", rebel_points)
	_update_military_ranks()


func _update_military_ranks() -> void:
	if imperial_points >= 2000:
		imperial_rank = "Colonel Impérial"
	elif imperial_points >= 1000:
		imperial_rank = "Major Impérial"
	elif imperial_points >= 500:
		imperial_rank = "Lieutenant Impérial"
	elif imperial_points >= 200:
		imperial_rank = "Sergent Stormtrooper"
	else:
		imperial_rank = "Recrue Impériale"

	if rebel_points >= 2000:
		rebel_rank = "Général de l'Alliance"
	elif rebel_points >= 1000:
		rebel_rank = "Commandant Rebelle"
	elif rebel_points >= 500:
		rebel_rank = "Capitaine Rebelle"
	elif rebel_points >= 200:
		rebel_rank = "Éclaireur de l'Alliance"
	else:
		rebel_rank = "Volontaire Rebelle"

