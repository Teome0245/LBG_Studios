# hub_theme_parks.gd — Parcs à Thèmes Galactiques & Donjons SWG Pre-CU
# Gère les quêtes scénarisées d'allégeance de haut rang (Palais de Jabba, Retraite de l'Empereur),
# l'instance chronométrée de la Corvette Corellienne et l'Antre de raid du Dragon Krayt.
class_name HubThemeParks
extends RefCounted

signal theme_park_progressed(player_name: String, park_id: String, mission_index: int)
signal theme_park_completed(player_name: String, park_id: String, badge: String)
signal dungeon_event(player_name: String, dungeon_id: String, status: String)

const THEME_PARKS: Dictionary = {
	"jabba_palace": {
		"title": "Palais de Jabba le Hutt",
		"location": "Tatooine - Mer de Dunes",
		"npc_hosts": ["Bib Fortuna", "Reelo Baruk", "Jabba le Hutt"],
		"missions": [
			{"id": "jp_01", "host": "Bib Fortuna", "title": "Racket de marchands", "desc": "Récupérer le tribut de crédits à Mos Eisley", "reward_credits": 2500},
			{"id": "jp_02", "host": "Reelo Baruk", "title": "Élimination de mouchard", "desc": "Neutraliser l'espion Valarian dans les canyons", "reward_credits": 5000},
			{"id": "jp_03", "host": "Jabba le Hutt", "title": "L'honneur du Parrain", "desc": "Éliminer le chef des pirates rivaux et rapporter son crâne", "reward_credits": 15000, "badge": "badge_jabba_enforcer", "item_reward": "jabba_vibro_axe"}
		]
	},
	"emperor_retreat": {
		"title": "Retraite de l'Empereur",
		"location": "Naboo - Pics des Cascades",
		"npc_hosts": ["Kren Blista-Vanth", "Dark Vador", "Empereur Palpatine"],
		"missions": [
			{"id": "er_01", "host": "Kren Blista-Vanth", "title": "Purge de la garde", "desc": "Intercepter les transmissions de contrebandiers locaux", "reward_credits": 3000},
			{"id": "er_02", "host": "Dark Vador", "title": "La Poigne Noire", "desc": "Éliminer une cellule de sympathisants rebelles retranchés", "reward_credits": 8000},
			{"id": "er_03", "host": "Empereur Palpatine", "title": "Volonté Impériale", "desc": "Détruire la station relais rebelle et subjuguer le secteur", "reward_credits": 25000, "badge": "badge_imperial_inquisitor", "item_reward": "imperial_master_cloak"}
		]
	}
}

# Donjon 1 : Instance de la Corvette Corellienne
var corvette_instance: Dictionary = {
	"active": false,
	"time_left_s": 0.0,
	"current_deck": "airlock", # airlock -> engine_room -> bridge
	"sabotage_progress": 0,
	"hostages_rescued": 0,
	"players_inside": []
}

# Donjon 2 : Raid Ancien Dragon Krayt
var krayt_dragon_boss: Dictionary = {
	"name": "Dragon Krayt Millénaire",
	"max_hp": 95000,
	"current_hp": 95000,
	"is_alive": true,
	"pos": [1200.0, 0.15, -1500.0],
	"slayers": []
}

# Registre d'avancement des parcs : player_name -> { "jabba_palace": 0..3, "emperor_retreat": 0..3, badges: [] }
var player_parks_state: Dictionary = {}

# Récupère l'avancement d'un joueur
func get_player_progress(player_name: String) -> Dictionary:
	if not player_parks_state.has(player_name):
		player_parks_state[player_name] = {
			"jabba_palace": 0,
			"emperor_retreat": 0,
			"badges": [],
			"inventory_rewards": []
		}
	return player_parks_state[player_name]

# Accepte ou progresse la mission active d'un parc
func complete_theme_park_mission(player_name: String, park_id: String) -> Dictionary:
	if not THEME_PARKS.has(park_id):
		return {"ok": false, "error": "Parc à thème inconnu"}
	
	var park = THEME_PARKS[park_id]
	var p_data = get_player_progress(player_name)
	var cur_step: int = int(p_data[park_id])
	var missions: Array = park["missions"]
	
	if cur_step >= missions.size():
		return {"ok": false, "error": "Toutes les missions de ce parc sont déjà accomplies"}
	
	var m = missions[cur_step]
	p_data[park_id] = cur_step + 1
	theme_park_progressed.emit(player_name, park_id, cur_step + 1)
	
	var is_final = (cur_step + 1 >= missions.size())
	if is_final:
		var badge = m.get("badge", "")
		if not badge.is_empty() and not p_data["badges"].has(badge):
			p_data["badges"].append(badge)
		var itm = m.get("item_reward", "")
		if not itm.is_empty():
			p_data["inventory_rewards"].append(itm)
		theme_park_completed.emit(player_name, park_id, badge)
	
	return {
		"ok": true,
		"park_id": park_id,
		"completed_mission": m["title"],
		"credits_awarded": m["reward_credits"],
		"is_grand_finale": is_final,
		"next_step": p_data[park_id]
	}

# Entrée dans l'instance de la Corvette Corellienne
func launch_corvette_instance(player_name: String) -> Dictionary:
	corvette_instance["active"] = true
	corvette_instance["time_left_s"] = 3600.0 # 60 minutes
	corvette_instance["current_deck"] = "airlock"
	corvette_instance["sabotage_progress"] = 0
	corvette_instance["hostages_rescued"] = 0
	if not corvette_instance["players_inside"].has(player_name):
		corvette_instance["players_inside"].append(player_name)
	
	dungeon_event.emit(player_name, "corvette", "instance_started")
	return {
		"ok": true,
		"dungeon": "Corvette Corellienne",
		"time_limit_s": 3600.0,
		"deck": "airlock"
	}

# Progression dans la Corvette (franchissement de portes, sabotage, etc.)
func advance_corvette(player_name: String, action_type: String) -> Dictionary:
	if not corvette_instance["active"]:
		return {"ok": false, "error": "Aucune instance de Corvette active"}
	
	if action_type == "clear_deck":
		if corvette_instance["current_deck"] == "airlock":
			corvette_instance["current_deck"] = "engine_room"
		elif corvette_instance["current_deck"] == "engine_room":
			corvette_instance["current_deck"] = "bridge"
		dungeon_event.emit(player_name, "corvette", "deck_advanced:" + corvette_instance["current_deck"])
	elif action_type == "sabotage_engines":
		corvette_instance["sabotage_progress"] = 100
		dungeon_event.emit(player_name, "corvette", "engines_sabotaged")
	elif action_type == "rescue_hostages":
		corvette_instance["hostages_rescued"] += 3
		dungeon_event.emit(player_name, "corvette", "hostages_rescued")
	
	return {"ok": true, "instance_state": corvette_instance}

# Attaque du Dragon Krayt de raid
func attack_krayt_dragon(player_name: String, damage: int) -> Dictionary:
	if not krayt_dragon_boss["is_alive"]:
		return {"ok": false, "error": "Le Dragon Krayt a déjà été vaincu dans ce cycle"}
	
	krayt_dragon_boss["current_hp"] = clampi(krayt_dragon_boss["current_hp"] - damage, 0, krayt_dragon_boss["max_hp"])
	if not krayt_dragon_boss["slayers"].has(player_name):
		krayt_dragon_boss["slayers"].append(player_name)
	
	if krayt_dragon_boss["current_hp"] <= 0:
		krayt_dragon_boss["is_alive"] = false
		dungeon_event.emit(player_name, "krayt_graveyard", "dragon_slain")
		return {
			"ok": true,
			"dragon_slain": true,
			"loot": {
				"krayt_dragon_pearl": {"quality": 98, "damage_bonus": 125, "rarity": "legendary"},
				"krayt_dragon_scales": {"qty": 12, "armor_rating": 850, "rarity": "epic"}
			}
		}
	
	return {
		"ok": true,
		"current_hp": krayt_dragon_boss["current_hp"],
		"max_hp": krayt_dragon_boss["max_hp"]
	}

# Tick des donjons
func tick(delta: float) -> void:
	if corvette_instance["active"]:
		corvette_instance["time_left_s"] = maxf(0.0, corvette_instance["time_left_s"] - delta)
		if corvette_instance["time_left_s"] <= 0.0:
			corvette_instance["active"] = false
			corvette_instance["players_inside"].clear()

