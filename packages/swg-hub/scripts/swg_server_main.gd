extends Node
## Serveur Autoritaire SWG Pre-CU 3D (Godot 4 Headless)
## Coordonne les entités en 3D (X, Y, Z, Yaw), le combat HAM, le housing libre et l'économie.

const HubSwgCombatScript := preload("res://scripts/hub_swg_combat.gd")
const HubCreaturesScript := preload("res://scripts/hub_creatures.gd")
const HubHousingScript := preload("res://scripts/hub_housing_cities.gd")
const HubVendorsScript := preload("res://scripts/hub_vendors_factories.gd")
const SwgProfessionsScript := preload("res://scripts/swg_professions_service.gd")

var combat_service: RefCounted = null
var creature_service: RefCounted = null
var housing_service: RefCounted = null
var vendor_service: RefCounted = null
var professions_service: RefCounted = null

# Registre d'état des joueurs en 3D
var active_players: Dictionary = {}
var tick_count: int = 0

# Générateur de terrain autoritaire (même formule que le client pour cohérence absolue)
var _noise: FastNoiseLite = null
var city_flatten_zones: Array = [
	{"center": Vector2(0, 0), "radius": 120.0, "blend_dist": 40.0, "height": 0.0},
	{"center": Vector2(150, -200), "radius": 60.0, "blend_dist": 30.0, "height": 2.0}
]


func _ready() -> void:
	print("[SWG-Hub] Démarrage du serveur autoritaire SWG Pre-CU 3D...")
	_init_services()


func _init_services() -> void:
	combat_service = HubSwgCombatScript.new()
	combat_service.setup(self)

	creature_service = HubCreaturesScript.new()
	creature_service.setup(self)

	housing_service = HubHousingScript.new()
	housing_service.setup(self)

	vendor_service = HubVendorsScript.new()
	vendor_service.setup(self)

	professions_service = SwgProfessionsScript.new()
	professions_service.setup("res://data/swg_precu_professions.json")

	print("[SWG-Hub] 5 Services SWG Pre-CU initialisés avec succès (Combat HAM, Faune/Scout, Housing/Villes, Commerce/Usines, 32 Professions).")


func register_player_3d(player_id: String, init_pos: Vector3, yaw: float = 0.0) -> Dictionary:
	var state := {
		"id": player_id,
		"pos": [init_pos.x, init_pos.y, init_pos.z],
		"yaw": yaw,
		"posture": "standing",
		"ham": {
			"health": {"current": 1000, "base_max": 1000, "wounds": 0},
			"action": {"current": 1000, "base_max": 1000, "wounds": 0},
			"mind": {"current": 1000, "base_max": 1000, "wounds": 0},
			"battle_fatigue": 0
		},
		"last_tick": tick_count
	}
	active_players[player_id] = state
	return state


func update_player_transform(player_id: String, pos: Vector3, yaw: float, posture_str: String) -> void:
	if active_players.has(player_id):
		var p: Dictionary = active_players[player_id]
		p["pos"] = [pos.x, pos.y, pos.z]
		p["yaw"] = yaw
		p["posture"] = posture_str
		p["last_tick"] = tick_count


func simulate_tick() -> void:
	tick_count += 1


func get_terrain_height_at(world_x: float, world_z: float) -> float:
	if _noise == null:
		_noise = FastNoiseLite.new()
		_noise.noise_type = FastNoiseLite.TYPE_SIMPLEX
		_noise.seed = 1977
		_noise.frequency = 0.005
		_noise.fractal_type = FastNoiseLite.FRACTAL_FBM
		_noise.fractal_octaves = 4
		_noise.fractal_gain = 0.45

	var base_h: float = _noise.get_noise_2d(world_x, world_z) * 18.0
	var final_h: float = base_h

	for zone in city_flatten_zones:
		var d: Dictionary = zone
		var center: Vector2 = d["center"]
		var radius: float = float(d["radius"])
		var blend: float = float(d["blend_dist"])
		var target_h: float = float(d["height"])

		var dist: float = Vector2(world_x, world_z).distance_to(center)
		if dist < radius:
			final_h = target_h
			break
		elif dist < radius + blend:
			var factor: float = (dist - radius) / blend
			final_h = lerpf(target_h, base_h, factor)

	return final_h

