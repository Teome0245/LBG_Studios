# hub_droid_engineer.gd — Système d'Ingénierie Droïde SWG Pre-CU
# Permet de fabriquer des châssis de droïdes modulaires (R2, 3PO, Probot, MSE, Droïde de Combat),
# d'installer des modules fonctionnels (stockage, atelier ambulant, soin médical, scan défensif),
# et de leur adresser des commandes tactiques (/follow, /patrol, /store, /craft_station).
class_name HubDroidEngineer
extends RefCounted

signal droid_crafted(owner_name: String, droid_id: String, chassis_type: String)
signal module_installed(droid_id: String, module_type: String)
signal droid_commanded(droid_id: String, command: String)

const CHASSIS_TYPES: Dictionary = {
	"r2_astromech": {
		"label": "Droïde Astromécano Série R2",
		"base_armor": 1500,
		"max_modules": 4,
		"power_drain": 15,
		"allowed_modules": ["storage", "crafting_station", "sonar_scanner", "music_playback"]
	},
	"protocol_3po": {
		"label": "Droïde de Protocole Série 3PO",
		"base_armor": 800,
		"max_modules": 3,
		"power_drain": 10,
		"allowed_modules": ["storage", "translator", "music_playback"]
	},
	"probot_recon": {
		"label": "Droïde Sonde d'Exploration Probot",
		"base_armor": 2200,
		"max_modules": 5,
		"power_drain": 25,
		"allowed_modules": ["storage", "combat_blaster", "sonar_scanner", "stealth_sensor"]
	},
	"mouse_mse": {
		"label": "Droïde Souris MSE-6",
		"base_armor": 400,
		"max_modules": 2,
		"power_drain": 5,
		"allowed_modules": ["storage", "repair_assist"]
	},
	"combat_battledroid": {
		"label": "Droïde de Combat Série IG-Lourd",
		"base_armor": 3500,
		"max_modules": 4,
		"power_drain": 30,
		"allowed_modules": ["combat_blaster", "shield_projector", "sonar_scanner"]
	}
}

const MODULE_REGISTRY: Dictionary = {
	"storage": {"name": "Module d'Extension de Soute", "desc": "+25 slots de stockage ambulant", "slot_bonus": 25},
	"crafting_station": {"name": "Atelier Mobile de Confection", "desc": "+10% vitesse et qualité de craft nomade", "craft_bonus": 10},
	"medical_unit": {"name": "Module Dispensaire Médical", "desc": "Soin automatique 150 HAM/min au propriétaire", "heal_rate": 150},
	"sonar_scanner": {"name": "Radar Télémétrique Sonar", "desc": "Révèle ennemis et gisements à 100m", "scan_range": 100},
	"combat_blaster": {"name": "Tourelle Blaster E-Web Légère", "desc": "Attaque les agresseurs à portée", "damage": 220},
	"music_playback": {"name": "Amplificateur de Musique Holo", "desc": "Diffuse des mélodies de cantina", "buff_duration": 600}
}

# Registre des droïdes : droid_id -> Dictionary
var droids: Dictionary = {}
var next_droid_id: int = 5001

# Confection d'un droïde par un Droid Engineer
func craft_droid(owner_name: String, chassis_type: String, custom_name: String = "", custom_color: String = "white") -> Dictionary:
	var clean_chassis = chassis_type.to_lower().strip_edges()
	if not CHASSIS_TYPES.has(clean_chassis):
		return {"ok": false, "error": "Type de châssis droïde non répertorié"}
	
	var c_info = CHASSIS_TYPES[clean_chassis]
	var d_id = "droid_" + str(next_droid_id)
	next_droid_id += 1
	
	var d_name = custom_name.strip_edges()
	if d_name.is_empty():
		d_name = c_info["label"]
	
	var droid_obj = {
		"id": d_id,
		"name": d_name,
		"owner": owner_name,
		"chassis": clean_chassis,
		"chassis_label": c_info["label"],
		"color": custom_color,
		"condition_hp": c_info["base_armor"],
		"max_hp": c_info["base_armor"],
		"battery_power": 100.0, # 0..100%
		"power_drain_rate": c_info["power_drain"],
		"installed_modules": [],
		"current_command": "stay",
		"inventory": [],
		"pos": [0.0, 0.0, 0.0],
		"is_active": true,
		"created_at": Time.get_unix_time_from_system()
	}
	
	droids[d_id] = droid_obj
	droid_crafted.emit(owner_name, d_id, clean_chassis)
	return {"ok": true, "droid": droid_obj}

# Installation d'un module fonctionnel
func install_module(droid_id: String, module_type: String) -> Dictionary:
	if not droids.has(droid_id):
		return {"ok": false, "error": "Droïde introuvable"}
	
	var droid = droids[droid_id]
	var chassis_info = CHASSIS_TYPES[droid["chassis"]]
	var installed: Array = droid["installed_modules"]
	
	if installed.size() >= chassis_info["max_modules"]:
		return {"ok": false, "error": "Capacité maximale de modules atteinte pour ce châssis"}
	
	if not MODULE_REGISTRY.has(module_type):
		return {"ok": false, "error": "Module inconnu"}
	
	if installed.has(module_type):
		return {"ok": false, "error": "Ce module est déjà monté sur le châssis"}
	
	installed.append(module_type)
	module_installed.emit(droid_id, module_type)
	return {"ok": true, "droid_id": droid_id, "modules": installed}

# Envoi d'une commande tactique au droïde
func issue_command(droid_id: String, owner_name: String, command: String, target_param = null) -> Dictionary:
	if not droids.has(droid_id):
		return {"ok": false, "error": "Droïde introuvable"}
	
	var droid = droids[droid_id]
	if droid["owner"] != owner_name:
		return {"ok": false, "error": "Vous n'êtes pas le propriétaire de cette unité droïde"}
	
	var clean_cmd = command.to_lower().strip_edges()
	var valid_cmds = ["follow", "stay", "patrol", "store_item", "dispense_meds", "play_music"]
	if not valid_cmds.has(clean_cmd):
		return {"ok": false, "error": "Commande droïde inconnue (valides: follow, stay, patrol, store_item, dispense_meds, play_music)"}
	
	droid["current_command"] = clean_cmd
	
	# Exécution spécifique
	if clean_cmd == "store_item" and target_param != null:
		var inv: Array = droid["inventory"]
		inv.append(target_param)
	
	droid_commanded.emit(droid_id, clean_cmd)
	return {"ok": true, "droid_id": droid_id, "command": clean_cmd, "battery": droid["battery_power"]}

# Mise à jour continue (tick)
func tick(delta: float) -> void:
	for d_id in droids:
		var d = droids[d_id]
		if d["is_active"]:
			# Drain de batterie lent
			var drain = (float(d["power_drain_rate"]) / 3600.0) * delta
			d["battery_power"] = maxf(0.0, float(d["battery_power"]) - drain)

# Liste des droïdes d'un joueur
func get_player_droids(owner_name: String) -> Array:
	var res: Array = []
	for d_id in droids:
		var d = droids[d_id]
		if d["owner"] == owner_name:
			res.append(d)
	return res

