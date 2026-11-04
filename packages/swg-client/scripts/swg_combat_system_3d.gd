extends Node3D
## Système de Combat 3D, Projectiles Blaster, Dépeçage & Cycle Jour/Nuit SWG Pre-CU
## 1. Projectiles laser (Blaster Bolts) avec traînée lumineuse et impact d'étincelles.
## 2. Textes de dégâts flottants 3D (Floating Combat Text).
## 3. Gestion des points de vie (HAM) des créatures avec mort et cadavre dépeçable.
## 4. Onde de sondage minier (Survey Pulse 3D).
## 5. Cycle Jour/Nuit dynamique avec rotation du double soleil binaire.

signal creature_slain(creature_node: Node3D, creature_name: String)
signal combat_action_resolved(action_name: String, damage: int, target_name: String)

var _sun_primary: DirectionalLight3D = null
var _sun_secondary: DirectionalLight3D = null
var _world_env: WorldEnvironment = null

var day_night_cycle_enabled: bool = true
var time_of_day: float = 0.25 # 0.0 = Minuit, 0.25 = Matin, 0.5 = Midi, 0.75 = Crépuscule
var day_speed: float = 0.004 # Vitesse de rotation du cycle


func _ready() -> void:
	name = "SwgCombatSystem3D"


func setup_environment_refs(sun1: DirectionalLight3D, sun2: DirectionalLight3D, w_env: WorldEnvironment) -> void:
	_sun_primary = sun1
	_sun_secondary = sun2
	_world_env = w_env


func _process(delta: float) -> void:
	if day_night_cycle_enabled and _sun_primary != null:
		_update_day_night(delta)


func _update_day_night(delta: float) -> void:
	time_of_day = fmod(time_of_day + day_speed * delta, 1.0)
	var sun_angle: float = (time_of_day * TAU) - (PI * 0.5)

	# Rotation du soleil principal
	_sun_primary.rotation_degrees.x = rad_to_deg(sin(sun_angle)) * 0.85
	_sun_primary.rotation_degrees.y = rad_to_deg(cos(sun_angle)) * 0.6 + 30.0

	# Intensité lumineuse selon la hauteur du soleil
	var elev: float = sin(sun_angle)
	if elev > 0.0:
		_sun_primary.light_energy = clampf(elev * 1.3, 0.05, 1.3)
		if _sun_secondary:
			_sun_secondary.light_energy = clampf(elev * 0.5, 0.0, 0.5)
	else:
		# Nuit : très faible lueur lunaire
		_sun_primary.light_energy = 0.04
		if _sun_secondary:
			_sun_secondary.light_energy = 0.01


## Tire un bolt de blaster laser rouge/vert vers une cible 3D
func fire_blaster_bolt(from_pos: Vector3, target_pos: Vector3, is_aim_shot: bool = false) -> void:
	var bolt := Node3D.new()
	bolt.name = "BlasterBolt"
	bolt.position = from_pos + Vector3(0, 1.2, 0) # Hauteur arme

	var mesh_inst := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = 0.06 if not is_aim_shot else 0.12
	cyl.bottom_radius = 0.06 if not is_aim_shot else 0.12
	cyl.height = 1.4 if not is_aim_shot else 2.2
	mesh_inst.mesh = cyl
	mesh_inst.rotation_degrees = Vector3(90, 0, 0)

	var mat := StandardMaterial3D.new()
	var bolt_color := Color(1.0, 0.2, 0.1) if not is_aim_shot else Color(0.2, 0.9, 1.0)
	mat.albedo_color = bolt_color
	mat.emission_enabled = true
	mat.emission = bolt_color
	mat.emission_energy_multiplier = 5.0
	mesh_inst.set_surface_override_material(0, mat)
	bolt.add_child(mesh_inst)

	var light := OmniLight3D.new()
	light.light_color = bolt_color
	light.light_energy = 2.0
	light.omni_range = 3.5
	bolt.add_child(light)

	add_child(bolt)

	# Orientation vers la cible
	var aim_dir := (target_pos + Vector3(0, 1.0, 0) - bolt.position).normalized()
	if aim_dir.length_squared() > 0.001:
		bolt.look_at(target_pos + Vector3(0, 1.0, 0), Vector3.UP)

	# Animation de trajectoire à grande vitesse (50 m/s)
	var tween := create_tween()
	var dist: float = bolt.position.distance_to(target_pos + Vector3(0, 1.0, 0))
	var duration: float = clampf(dist / 48.0, 0.05, 1.2)
	tween.tween_property(bolt, "position", target_pos + Vector3(0, 1.0, 0), duration)
	tween.tween_callback(func() -> void:
		_spawn_impact_sparks(target_pos + Vector3(0, 1.0, 0), bolt_color)
		bolt.queue_free()
	)


## Crée des étincelles d'impact à la destination du bolt
func _spawn_impact_sparks(impact_pos: Vector3, col: Color) -> void:
	var flash := OmniLight3D.new()
	flash.position = impact_pos
	flash.light_color = col
	flash.light_energy = 4.0
	flash.omni_range = 3.0
	add_child(flash)

	var tween := create_tween()
	tween.tween_property(flash, "light_energy", 0.0, 0.25)
	tween.tween_callback(flash.queue_free)


## Affiche un chiffre de dégâts flottant en 3D au-dessus de la cible
func spawn_damage_number(at_pos: Vector3, dmg: int, col: Color = Color(1.0, 0.3, 0.2)) -> void:
	var lbl := Label3D.new()
	lbl.text = "-%d S" % dmg
	lbl.position = at_pos + Vector3(0, 2.4, 0)
	lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lbl.font_size = 20
	lbl.modulate = col
	lbl.outline_modulate = Color(0, 0, 0, 1.0)
	lbl.outline_size = 4
	add_child(lbl)

	var tween := create_tween()
	tween.set_parallel(true)
	tween.tween_property(lbl, "position:y", lbl.position.y + 1.2, 0.8)
	tween.tween_property(lbl, "modulate:a", 0.0, 0.8)
	tween.chain().tween_callback(lbl.queue_free)


## Onde de prospection minière (Survey Pulse) s'élargissant au sol
func trigger_survey_pulse(origin: Vector3) -> void:
	var pulse := MeshInstance3D.new()
	var tor := TorusMesh.new()
	tor.inner_radius = 0.5
	tor.outer_radius = 0.8
	pulse.mesh = tor
	pulse.position = origin + Vector3(0, 0.15, 0)
	pulse.rotation_degrees = Vector3(90, 0, 0)

	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.2, 0.9, 1.0, 0.8)
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.emission_enabled = true
	mat.emission = Color(0.2, 0.9, 1.0)
	mat.emission_energy_multiplier = 3.0
	pulse.set_surface_override_material(0, mat)
	add_child(pulse)

	var tween := create_tween()
	tween.set_parallel(true)
	tween.tween_property(pulse, "scale", Vector3(25.0, 25.0, 25.0), 1.5)
	tween.tween_property(mat, "albedo_color:a", 0.0, 1.5)
	tween.chain().tween_callback(pulse.queue_free)

