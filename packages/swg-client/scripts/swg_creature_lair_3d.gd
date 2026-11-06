class_name SwgCreatureLair3D
extends CharacterBody3D
## Nid de Créatures & Lair SWG Pre-CU 3D
## Gère un monticule de bêtes avec points de vie HAM, vagues de défenseurs en riposte,
## aggro de meute coordonné, effondrement à 0 PV et butin de décombres (œufs rares, crédits).

signal lair_damaged(attacker: Node3D, current_hp: int, max_hp: int)
signal wave_spawned(wave_num: int, guardians: Array)
signal lair_destroyed(lair_node: Node3D, killer: Node3D)

@export var lair_id: String = "lair_jackals_1"
@export var lair_display_name: String = "Nid de Chacals des Dunes"
@export var creature_kind: String = "creature_jackal"
@export var guardian_name: String = "Chacal Protecteur du Nid"
@export var lair_max_hp: int = 1500
@export var initial_guardians_count: int = 2
@export var wave_guardians_count: int = 2
@export var loot_credits: int = 850
@export var loot_rare_item: String = "Œuf de Chacal des Sables Fossilisé"

var current_hp: int = 1500
var is_lair_destroyed: bool = false
var guardians: Array[CharacterBody3D] = []
var _waves_done: Array[float] = []
var _visual_mound: Node3D = null
var _debris_node: Node3D = null
var _inner_light: OmniLight3D = null

# Callback de spawn externe injecté par le monde
var spawn_creature_callback: Callable = Callable()


func _init() -> void:
	current_hp = lair_max_hp
	set_meta("display_name", lair_display_name)
	set_meta("entity_kind", "creature_lair")
	set_meta("current_health", current_hp)
	set_meta("max_health", lair_max_hp)
	set_meta("current_action", 1000)
	set_meta("max_action", 1000)
	set_meta("current_mind", 800)
	set_meta("max_mind", 800)
	set_meta("is_dead", false)


func _ready() -> void:
	current_hp = lair_max_hp
	set_meta("current_health", current_hp)
	set_meta("max_health", lair_max_hp)
	_build_lair_mesh()
	_setup_collision()


func _setup_collision() -> void:
	var col_shape := CollisionShape3D.new()
	var cyl := CylinderShape3D.new()
	cyl.radius = 2.4
	cyl.height = 2.0
	col_shape.shape = cyl
	col_shape.position = Vector3(0, 1.0, 0)
	add_child(col_shape)


func _build_lair_mesh() -> void:
	_visual_mound = Node3D.new()
	_visual_mound.name = "VisualMound"
	add_child(_visual_mound)

	# Matériau rocheux/terreux organique
	var mat_mound := StandardMaterial3D.new()
	if creature_kind == "creature_beetle":
		mat_mound.albedo_color = Color(0.22, 0.20, 0.24) # Roche sombre obsidienne
	else:
		mat_mound.albedo_color = Color(0.55, 0.42, 0.28) # Terre ocre des sables
	mat_mound.roughness = 0.9

	# Monticule principal tronconique
	var mound_mesh := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = 1.4
	cyl.bottom_radius = 2.6
	cyl.height = 1.6
	mound_mesh.mesh = cyl
	mound_mesh.position = Vector3(0, 0.8, 0)
	mound_mesh.set_surface_override_material(0, mat_mound)
	_visual_mound.add_child(mound_mesh)

	# Cratère / Cône supérieur évidé
	var crater := MeshInstance3D.new()
	var c_cyl := CylinderMesh.new()
	c_cyl.top_radius = 0.9
	c_cyl.bottom_radius = 1.5
	c_cyl.height = 0.6
	crater.mesh = c_cyl
	crater.position = Vector3(0, 1.4, 0)
	var mat_crater := StandardMaterial3D.new()
	mat_crater.albedo_color = Color(0.15, 0.1, 0.08)
	mat_crater.roughness = 1.0
	crater.set_surface_override_material(0, mat_crater)
	_visual_mound.add_child(crater)

	# Lueur bioluminescente ou fumerolle au centre
	_inner_light = OmniLight3D.new()
	_inner_light.position = Vector3(0, 1.6, 0)
	_inner_light.light_color = Color(1.0, 0.5, 0.2) if creature_kind != "creature_beetle" else Color(0.3, 0.9, 0.4)
	_inner_light.light_energy = 2.5
	_inner_light.omni_range = 4.5
	_visual_mound.add_child(_inner_light)

	# Éperons rocheux et ossements autour du nid
	var mat_bone := StandardMaterial3D.new()
	mat_bone.albedo_color = Color(0.85, 0.82, 0.72)
	mat_bone.roughness = 0.7

	for i in range(6):
		var ang := float(i) * (TAU / 6.0) + randf_range(-0.2, 0.2)
		var rad := randf_range(2.0, 2.7)
		var spire := MeshInstance3D.new()
		var s_mesh := BoxMesh.new()
		s_mesh.size = Vector3(0.4, randf_range(0.9, 1.7), 0.5)
		spire.mesh = s_mesh
		spire.position = Vector3(cos(ang) * rad, 0.6, sin(ang) * rad)
		spire.rotation_degrees = Vector3(randf_range(-15, 15), randf_range(0, 180), randf_range(-15, 15))
		spire.set_surface_override_material(0, mat_bone if i % 2 == 0 else mat_mound)
		_visual_mound.add_child(spire)


## Fait spawner la garde initiale du nid
func init_guardians() -> void:
	if not spawn_creature_callback.is_valid():
		return
	var base_pos := global_position if is_inside_tree() else position
	for i in range(initial_guardians_count):
		var ang := float(i) * (TAU / float(initial_guardians_count))
		var offset := Vector3(cos(ang) * 4.5, 0, sin(ang) * 4.5)
		var g_pos := base_pos + offset
		var g_node = spawn_creature_callback.call(guardian_name, g_pos, creature_kind, self)
		if g_node is CharacterBody3D:
			guardians.append(g_node)


## Reçoit un coup / tir de blaster
func take_damage(dmg: int, attacker: Node3D) -> int:
	if is_lair_destroyed:
		return 0

	current_hp = maxi(0, current_hp - dmg)
	set_meta("current_health", current_hp)
	lair_damaged.emit(attacker, current_hp, lair_max_hp)

	# 1. Alerte tous les gardiens vivants : ils passent en aggro furieuse sur l'attaquant
	_alert_guardians_to_attack(attacker)

	# 2. Vérification des seuils de vagues de renforts (75%, 50%, 25%)
	var ratio := float(current_hp) / float(lair_max_hp)
	for threshold in [0.75, 0.50, 0.25]:
		if ratio <= threshold and not _waves_done.has(threshold):
			_waves_done.append(threshold)
			_spawn_reinforcement_wave(attacker, int(round((1.0 - threshold) * 4)))

	# 3. Mort et effondrement du nid à 0 PV
	if current_hp <= 0:
		_destroy_lair(attacker)

	return dmg


func _alert_guardians_to_attack(attacker: Node3D) -> void:
	if attacker == null:
		return
	for g in guardians:
		if is_instance_valid(g) and not g.get_meta("is_dead", false):
			g.set_meta("aggro_target", attacker)
			g.set_meta("is_aggressive", true)


func _spawn_reinforcement_wave(attacker: Node3D, wave_idx: int) -> void:
	if not spawn_creature_callback.is_valid():
		return

	var base_pos := global_position if is_inside_tree() else position
	var new_guardians: Array = []
	for i in range(wave_guardians_count):
		var ang := randf_range(0, TAU)
		var offset := Vector3(cos(ang) * 2.8, 0, sin(ang) * 2.8)
		var g_pos := base_pos + offset
		var wave_name := "Défenseur Enragé (Vague %d)" % wave_idx
		var g_node = spawn_creature_callback.call(wave_name, g_pos, creature_kind, self)
		if g_node is CharacterBody3D:
			g_node.set_meta("aggro_target", attacker)
			g_node.set_meta("is_aggressive", true)
			guardians.append(g_node)
			new_guardians.append(g_node)

	wave_spawned.emit(wave_idx, new_guardians)


func _destroy_lair(killer: Node3D) -> void:
	is_lair_destroyed = true
	set_meta("is_dead", true)
	set_meta("entity_kind", "lair_debris")
	set_meta("display_name", "[Décombres] %s" % lair_display_name)

	# Animation d'effondrement
	if _visual_mound:
		var tween := create_tween()
		tween.set_parallel(true)
		tween.tween_property(_visual_mound, "scale", Vector3(1.1, 0.25, 1.1), 0.6)
		tween.tween_property(_visual_mound, "position:y", -0.3, 0.6)
		if _inner_light:
			tween.tween_property(_inner_light, "light_energy", 0.0, 0.5)

	lair_destroyed.emit(self, killer)


## Récolte des décombres du nid après destruction
func harvest_debris() -> Dictionary:
	if not is_lair_destroyed:
		return {"ok": false, "reason": "Le nid est encore intact !"}

	if get_meta("already_looted", false):
		return {"ok": false, "reason": "Ces décombres ont déjà été fouillés."}

	set_meta("already_looted", true)
	return {
		"ok": true,
		"credits": loot_credits,
		"rare_item": loot_rare_item,
		"organic_mats": [
			{"id": "egg_organic", "name": loot_rare_item, "count": 1, "quality": 950},
			{"id": "meat_predator", "name": "Viande de Prédateur Alpha", "count": 6, "quality": 920},
			{"id": "hide_rugged", "name": "Peau Rugueuse de Nid", "count": 4, "quality": 890}
		]
	}
