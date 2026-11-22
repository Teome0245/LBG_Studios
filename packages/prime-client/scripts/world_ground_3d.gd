# world_ground_3d.gd — Rendu Full 3D Haute Fidélité du Monde Planétaire Lost Heaven
# Intègre la caméra 3ème personne immersive (avec SpringArm3D) et isométrique commutable [V],
# le ciel procédural PBR, les dunes de sable ondulées, les falaises désertiques,
# l'avatar articulé avec animations procédurales (marche/sprint/saut) et les effets atmosphériques.
extends SubViewportContainer
class_name WorldGround3D

signal player_moved_3d(new_pos: Vector3)
signal entity_clicked_3d(entity_id: String, entity_type: String)
signal terrain_clicked_3d(target_pos: Vector3)
signal camera_mode_changed(mode_name: String)

enum CameraMode {
	THIRD_PERSON, # Caméra 3ème personne immersive (Follow-cam / Over-the-shoulder MMO)
	ISOMETRIC     # Caméra isométrique 3/4 classique orbitale (style T4C / RTS)
}

# --- Composants 3D fondamentaux ---
var _viewport: SubViewport = null
var _world_root: Node3D = null
var _camera_rig: Node3D = null
var _spring_arm: SpringArm3D = null
var _camera: Camera3D = null
var _sun_light: DirectionalLight3D = null
var _world_env: WorldEnvironment = null
var _terrain_root: Node3D = null
var _dust_particles: CPUParticles3D = null

# --- Gestion du Joueur 3D et des PNJ ---
var _player_node: CharacterBody3D = null
var _player_mesh: Node3D = null
var _player_torso: MeshInstance3D = null
var _player_head: MeshInstance3D = null
var _player_visor: MeshInstance3D = null
var _player_backpack: MeshInstance3D = null
var _player_arm_l: MeshInstance3D = null
var _player_arm_r: MeshInstance3D = null
var _player_leg_l: MeshInstance3D = null
var _player_leg_r: MeshInstance3D = null
var _target_marker: MeshInstance3D = null
var _active_entities_3d: Dictionary = {} # id -> Node3D

# --- Contrôles de Caméra ---
var current_camera_mode: CameraMode = CameraMode.THIRD_PERSON
var camera_pitch: float = -18.0 # Degrés (-75 vers le sol, +45 vers le ciel)
var camera_yaw: float = 0.0     # Orientation orbitale (degrés)
var camera_zoom: float = 5.5    # Distance au joueur (mètres)
const MIN_ZOOM_3RD: float = 1.8
const MAX_ZOOM_3RD: float = 14.0
const MIN_ZOOM_ISO: float = 12.0
const MAX_ZOOM_ISO: float = 40.0

# --- Physique & Déplacement Joueur ---
var player_speed: float = 7.5      # Vitesse normale
var player_sprint_speed: float = 11.5 # Vitesse sprint (Shift)
var jump_velocity: float = 6.2     # Impulsion de saut
var gravity: float = 18.0          # Gravité Scrapaltai
var is_click_moving: bool = false
var click_target_pos: Vector3 = Vector3.ZERO
var is_orbiting_camera: bool = false
var last_mouse_pos: Vector2 = Vector2.ZERO

# Animation procédurale
var _walk_cycle: float = 0.0
var _is_moving: bool = false


func _init() -> void:
	name = "WorldGround3D"
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_PASS
	_setup_viewport_and_world_3d()
	_setup_pbr_atmosphere_and_sky()
	_setup_desert_environment()
	_setup_detailed_player_avatar()
	_setup_sand_particles()


func _ready() -> void:
	if _viewport == null:
		_setup_viewport_and_world_3d()
		_setup_pbr_atmosphere_and_sky()
		_setup_desert_environment()
		_setup_detailed_player_avatar()
		_setup_sand_particles()


## 1. Initialisation du SubViewport et de la Hiérarchie de Caméra avec SpringArm3D
func _setup_viewport_and_world_3d() -> void:
	_viewport = SubViewport.new()
	_viewport.name = "SubViewport"
	_viewport.size = size if size != Vector2.ZERO else Vector2(1920, 1080)
	_viewport.transparent_bg = false
	_viewport.handle_input_locally = true
	_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	_viewport.msaa_3d = Viewport.MSAA_4X
	_viewport.screen_space_aa = Viewport.SCREEN_SPACE_AA_FXAA
	add_child(_viewport)

	_world_root = Node3D.new()
	_world_root.name = "World3DRoot"
	_viewport.add_child(_world_root)

	# Rig Caméra avec SpringArm3D (évite les collisions de caméra avec le décor)
	_camera_rig = Node3D.new()
	_camera_rig.name = "Camera3DRig"
	_world_root.add_child(_camera_rig)

	_spring_arm = SpringArm3D.new()
	_spring_arm.name = "CameraSpringArm"
	_spring_arm.spring_length = camera_zoom
	_spring_arm.margin = 0.25
	_spring_arm.position = Vector3(0.0, 1.55, 0.0) # Hauteur tête/épaules
	_camera_rig.add_child(_spring_arm)

	_camera = Camera3D.new()
	_camera.name = "MainCamera3D"
	_camera.fov = 65.0
	_camera.near = 0.25
	_camera.far = 1200.0
	_spring_arm.add_child(_camera)

	_update_camera_settings()


## 2. Éclairage PBR, Ciel Procédural Physique & Post-Processing Haute Qualité
func _setup_pbr_atmosphere_and_sky() -> void:
	# Ciel Procédural Physique de Scrapaltai (Teintes oranger, azur profond et soleil chaud)
	_world_env = WorldEnvironment.new()
	_world_env.name = "WorldEnvScrapaltaiPBR"

	var env := Environment.new()
	var sky := Sky.new()
	var sky_mat := ProceduralSkyMaterial.new()
	sky_mat.sky_top_color = Color(0.25, 0.45, 0.72)      # Azur zénith
	sky_mat.sky_horizon_color = Color(0.94, 0.72, 0.46)  # Doré couchant
	sky_mat.sky_curve = 0.12
	sky_mat.ground_bottom_color = Color(0.32, 0.22, 0.16)
	sky_mat.ground_horizon_color = Color(0.88, 0.62, 0.38)
	sky_mat.ground_curve = 0.08
	sky_mat.sun_angle_max = 28.0
	sky_mat.sun_curve = 0.18
	sky.sky_material = sky_mat

	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_color = Color(0.9, 0.82, 0.72)
	env.ambient_light_sky_contribution = 0.65

	# Post-Processing PBR Film / HDR
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.tonemap_exposure = 1.05
	env.ssao_enabled = true
	env.ssao_radius = 1.6
	env.ssao_intensity = 2.2
	env.glow_enabled = true
	env.glow_intensity = 0.35
	env.glow_bloom = 0.18
	env.glow_hdr_threshold = 0.85
	env.fog_enabled = true
	env.fog_light_color = Color(0.86, 0.68, 0.48)
	env.fog_density = 0.0012
	env.fog_sky_affect = 0.4

	_world_env.environment = env
	_world_root.add_child(_world_env)

	# Soleil chaud de Scrapaltai avec ombres PBR nettes
	_sun_light = DirectionalLight3D.new()
	_sun_light.name = "SunScrapaltai"
	_sun_light.rotation_degrees = Vector3(-42.0, 38.0, 0.0)
	_sun_light.light_color = Color(1.0, 0.92, 0.82)
	_sun_light.light_energy = 1.45
	_sun_light.shadow_enabled = true
	_sun_light.shadow_blur = 1.2
	_sun_light.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	_sun_light.directional_shadow_split_1 = 0.08
	_sun_light.directional_shadow_split_2 = 0.22
	_sun_light.directional_shadow_split_3 = 0.55
	_world_root.add_child(_sun_light)


## 3. Environnement Désertique Enrichi : Dunes, Dalles Sci-Fi et Canyons
func _setup_desert_environment() -> void:
	_terrain_root = Node3D.new()
	_terrain_root.name = "TerrainEnvironment"
	_world_root.add_child(_terrain_root)

	# Sol principal 600m x 600m
	var main_ground := MeshInstance3D.new()
	main_ground.name = "MainSandPlane"
	var plane_mesh := PlaneMesh.new()
	plane_mesh.size = Vector2(800.0, 800.0)
	plane_mesh.subdivide_width = 48
	plane_mesh.subdivide_depth = 48
	main_ground.mesh = plane_mesh

	var sand_mat := StandardMaterial3D.new()
	sand_mat.albedo_color = Color(0.78, 0.60, 0.40) # Sable ocre doré
	sand_mat.roughness = 0.94
	sand_mat.metallic = 0.02
	main_ground.material_override = sand_mat

	# Collision physique du sol
	var body := StaticBody3D.new()
	body.name = "GroundStaticBody"
	var col_shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(800.0, 1.0, 800.0)
	col_shape.shape = box
	col_shape.position = Vector3(0.0, -0.5, 0.0)
	body.add_child(col_shape)
	main_ground.add_child(body)
	_terrain_root.add_child(main_ground)

	# Place centrale pavée de Lost Heaven (dalles hexagonales sci-fi métalliques)
	var plaza := MeshInstance3D.new()
	plaza.name = "LostHeavenPlaza"
	var cyl := CylinderMesh.new()
	cyl.top_radius = 28.0
	cyl.bottom_radius = 28.0
	cyl.height = 0.12
	plaza.mesh = cyl
	plaza.position = Vector3(0.0, 0.06, 0.0)
	var plaza_mat := StandardMaterial3D.new()
	plaza_mat.albedo_color = Color(0.24, 0.28, 0.32) # Alliage gris acier
	plaza_mat.metallic = 0.85
	plaza_mat.roughness = 0.4
	plaza.material_override = plaza_mat
	_terrain_root.add_child(plaza)

	# Anneaux d'énergie au centre de la place
	var plaza_ring := MeshInstance3D.new()
	var torus := TorusMesh.new()
	torus.inner_radius = 26.5
	torus.outer_radius = 27.5
	plaza_ring.mesh = torus
	plaza_ring.position = Vector3(0.0, 0.14, 0.0)
	var ring_mat := StandardMaterial3D.new()
	ring_mat.albedo_color = Color(0.0, 0.85, 0.95)
	ring_mat.emission_enabled = true
	ring_mat.emission = Color(0.0, 0.85, 0.95)
	ring_mat.emission_energy_multiplier = 1.2
	plaza_ring.material_override = ring_mat
	_terrain_root.add_child(plaza_ring)

	# Spires rocheuses / Canyons de Scrapaltai en périphérie pour un sentiment d'échelle
	var mesa_positions := [
		Vector3(-140, 12, -180), Vector3(180, 18, -150),
		Vector3(-220, 22, 120), Vector3(190, 15, 210),
		Vector3(-70, 8, 250), Vector3(260, 25, 40)
	]
	var rock_mat := StandardMaterial3D.new()
	rock_mat.albedo_color = Color(0.55, 0.38, 0.28)
	rock_mat.roughness = 0.95

	for i in range(mesa_positions.size()):
		var mesa := MeshInstance3D.new()
		mesa.name = "MesaCliff_%d" % i
		var m_cyl := CylinderMesh.new()
		m_cyl.top_radius = randf_range(16.0, 32.0)
		m_cyl.bottom_radius = m_cyl.top_radius * 1.4
		m_cyl.height = randf_range(24.0, 48.0)
		mesa.mesh = m_cyl
		mesa.position = mesa_positions[i]
		mesa.material_override = rock_mat
		_terrain_root.add_child(mesa)

	# Tour Relais Holographique de Lost Heaven (Antenne Sci-Fi centrale)
	var tower := Node3D.new()
	tower.name = "RelayTower"
	tower.position = Vector3(0.0, 0.0, -18.0)
	var mast := MeshInstance3D.new()
	var mast_cyl := CylinderMesh.new()
	mast_cyl.top_radius = 0.6
	mast_cyl.bottom_radius = 1.4
	mast_cyl.height = 22.0
	mast.mesh = mast_cyl
	mast.position = Vector3(0.0, 11.0, 0.0)
	var mast_mat := StandardMaterial3D.new()
	mast_mat.albedo_color = Color(0.3, 0.35, 0.4)
	mast_mat.metallic = 0.9
	mast.material_override = mast_mat
	tower.add_child(mast)

	# Balise lumineuse clignotante au sommet de la tour
	var beacon := OmniLight3D.new()
	beacon.light_color = Color(0.0, 0.9, 1.0)
	beacon.light_energy = 3.5
	beacon.omni_range = 35.0
	beacon.position = Vector3(0.0, 22.2, 0.0)
	tower.add_child(beacon)
	_terrain_root.add_child(tower)

	# Anneau de ciblage néon au sol
	_target_marker = MeshInstance3D.new()
	_target_marker.name = "TargetCircleMarker"
	var t_mesh := TorusMesh.new()
	t_mesh.inner_radius = 0.8
	t_mesh.outer_radius = 1.05
	_target_marker.mesh = t_mesh
	var tm_mat := StandardMaterial3D.new()
	tm_mat.albedo_color = Color(0.0, 0.95, 0.85, 0.9)
	tm_mat.emission_enabled = true
	tm_mat.emission = Color(0.0, 0.95, 0.85)
	tm_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_target_marker.material_override = tm_mat
	_target_marker.visible = false
	_world_root.add_child(_target_marker)


## 4. Particules de Vent & Poussières de Sable Ambiantes
func _setup_sand_particles() -> void:
	_dust_particles = CPUParticles3D.new()
	_dust_particles.name = "SandDustParticles"
	_dust_particles.amount = 180
	_dust_particles.lifetime = 4.0
	_dust_particles.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	_dust_particles.emission_box_extents = Vector3(35.0, 4.0, 35.0)
	_dust_particles.direction = Vector3(1.0, -0.1, 0.5).normalized()
	_dust_particles.spread = 20.0
	_dust_particles.initial_velocity_min = 3.0
	_dust_particles.initial_velocity_max = 7.5
	_dust_particles.gravity = Vector3(0.0, -0.4, 0.0)
	_dust_particles.scale_amount_min = 0.08
	_dust_particles.scale_amount_max = 0.22

	var p_mesh := SphereMesh.new()
	p_mesh.radius = 0.08
	p_mesh.height = 0.16
	_dust_particles.mesh = p_mesh

	var p_mat := StandardMaterial3D.new()
	p_mat.albedo_color = Color(0.92, 0.78, 0.55, 0.55)
	p_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	p_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_dust_particles.material_override = p_mat
	_world_root.add_child(_dust_particles)


## 5. Avatar Joueur 3D Articulé Haute Définition
func _setup_detailed_player_avatar() -> void:
	_player_node = CharacterBody3D.new()
	_player_node.name = "Player3D"
	_player_node.position = Vector3(0.0, 0.0, 0.0)

	var col := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 0.45
	cap.height = 1.85
	col.shape = cap
	col.position = Vector3(0.0, 0.92, 0.0)
	_player_node.add_child(col)

	_player_mesh = Node3D.new()
	_player_mesh.name = "AvatarVisualRig"

	# Matériaux de l'Armure du Pionnier
	var armor_mat := StandardMaterial3D.new()
	armor_mat.albedo_color = Color(0.16, 0.26, 0.38) # Bleu nuit composite
	armor_mat.metallic = 0.4
	armor_mat.roughness = 0.55

	var metal_mat := StandardMaterial3D.new()
	metal_mat.albedo_color = Color(0.65, 0.68, 0.72) # Plaques d'acier
	metal_mat.metallic = 0.85
	metal_mat.roughness = 0.35

	var glow_mat := StandardMaterial3D.new()
	glow_mat.albedo_color = Color(0.0, 0.95, 0.85) # Visière cyan émissif
	glow_mat.emission_enabled = true
	glow_mat.emission = Color(0.0, 0.95, 0.85)

	# Buste / Plastron
	_player_torso = MeshInstance3D.new()
	var torso_box := BoxMesh.new()
	torso_box.size = Vector3(0.52, 0.65, 0.32)
	_player_torso.mesh = torso_box
	_player_torso.position = Vector3(0.0, 1.05, 0.0)
	_player_torso.material_override = armor_mat
	_player_mesh.add_child(_player_torso)

	# Tête / Casque
	_player_head = MeshInstance3D.new()
	var head_mesh := SphereMesh.new()
	head_mesh.radius = 0.22
	head_mesh.height = 0.44
	_player_head.mesh = head_mesh
	_player_head.position = Vector3(0.0, 1.55, 0.0)
	_player_head.material_override = metal_mat
	_player_mesh.add_child(_player_head)

	# Visière holographique
	_player_visor = MeshInstance3D.new()
	var v_box := BoxMesh.new()
	v_box.size = Vector3(0.32, 0.10, 0.12)
	_player_visor.mesh = v_box
	_player_visor.position = Vector3(0.0, 1.55, 0.18)
	_player_visor.material_override = glow_mat
	_player_mesh.add_child(_player_visor)

	# Backpack / Générateur d'énergie dorsal
	_player_backpack = MeshInstance3D.new()
	var bp_box := BoxMesh.new()
	bp_box.size = Vector3(0.36, 0.44, 0.18)
	_player_backpack.mesh = bp_box
	_player_backpack.position = Vector3(0.0, 1.08, -0.22)
	_player_backpack.material_override = metal_mat
	_player_mesh.add_child(_player_backpack)

	# Bras Gauche et Droit
	_player_arm_l = MeshInstance3D.new()
	var arm_capsule := CapsuleMesh.new()
	arm_capsule.radius = 0.09
	arm_capsule.height = 0.60
	_player_arm_l.mesh = arm_capsule
	_player_arm_l.position = Vector3(-0.35, 1.0, 0.0)
	_player_arm_l.material_override = armor_mat
	_player_mesh.add_child(_player_arm_l)

	_player_arm_r = MeshInstance3D.new()
	_player_arm_r.mesh = arm_capsule
	_player_arm_r.position = Vector3(0.35, 1.0, 0.0)
	_player_arm_r.material_override = armor_mat
	_player_mesh.add_child(_player_arm_r)

	# Jambes Gauche et Droite
	_player_leg_l = MeshInstance3D.new()
	var leg_capsule := CapsuleMesh.new()
	leg_capsule.radius = 0.11
	leg_capsule.height = 0.72
	_player_leg_l.mesh = leg_capsule
	_player_leg_l.position = Vector3(-0.16, 0.42, 0.0)
	_player_leg_l.material_override = armor_mat
	_player_mesh.add_child(_player_leg_l)

	_player_leg_r = MeshInstance3D.new()
	_player_leg_r.mesh = leg_capsule
	_player_leg_r.position = Vector3(0.16, 0.42, 0.0)
	_player_leg_r.material_override = armor_mat
	_player_mesh.add_child(_player_leg_r)

	_player_node.add_child(_player_mesh)
	_world_root.add_child(_player_node)


## 6. Bascule entre Caméra 3ème Personne et Caméra Isométrique 3/4
func toggle_camera_mode() -> void:
	if current_camera_mode == CameraMode.THIRD_PERSON:
		set_camera_mode(CameraMode.ISOMETRIC)
	else:
		set_camera_mode(CameraMode.THIRD_PERSON)


func set_camera_mode(mode: CameraMode) -> void:
	current_camera_mode = mode
	if current_camera_mode == CameraMode.THIRD_PERSON:
		camera_pitch = -16.0
		camera_zoom = 5.5
		if _camera != null:
			_camera.fov = 68.0
		camera_mode_changed.emit("3ème Personne (Over-The-Shoulder)")
	else:
		camera_pitch = -45.0
		camera_zoom = 20.0
		if _camera != null:
			_camera.fov = 48.0
		camera_mode_changed.emit("Isométrique 3/4 (T4C / SWG)")
	_update_camera_settings()


func _update_camera_settings() -> void:
	if _camera_rig == null or _spring_arm == null:
		return
	if _player_node != null:
		_camera_rig.position = _player_node.position

	_camera_rig.rotation_degrees = Vector3(0.0, camera_yaw, 0.0)
	_spring_arm.rotation_degrees = Vector3(camera_pitch, 0.0, 0.0)
	_spring_arm.spring_length = camera_zoom


## 7. Boucle Physique : Gravité, Déplacement ZQSD, Sprint, Saut et Animation Procédurale
func _physics_process(delta: float) -> void:
	if _player_node == null:
		return

	# Application de la gravité
	if not _player_node.is_on_floor():
		_player_node.velocity.y -= gravity * delta
	else:
		_player_node.velocity.y = 0.0

	var move_vec := Vector3.ZERO
	var is_sprinting := Input.is_key_pressed(KEY_SHIFT)
	var cur_speed := player_sprint_speed if is_sprinting else player_speed

	# 1. Déplacement ZQSD
	var input_dir := Vector2.ZERO
	if Input.is_action_pressed("ui_up") or Input.is_key_pressed(KEY_Z) or Input.is_key_pressed(KEY_W):
		input_dir.y -= 1.0
	if Input.is_action_pressed("ui_down") or Input.is_key_pressed(KEY_S):
		input_dir.y += 1.0
	if Input.is_action_pressed("ui_left") or Input.is_key_pressed(KEY_Q) or Input.is_key_pressed(KEY_A):
		input_dir.x -= 1.0
	if Input.is_action_pressed("ui_right") or Input.is_key_pressed(KEY_D):
		input_dir.x += 1.0

	# 2. Saut (Barre d'espace)
	if Input.is_physical_key_pressed(KEY_SPACE) and _player_node.is_on_floor():
		_player_node.velocity.y = jump_velocity

	if input_dir != Vector2.ZERO:
		is_click_moving = false
		input_dir = input_dir.normalized()
		var forward := -_camera_rig.transform.basis.z
		var right := _camera_rig.transform.basis.x
		forward.y = 0.0
		right.y = 0.0
		forward = forward.normalized()
		right = right.normalized()
		move_vec = (forward * -input_dir.y) + (right * input_dir.x)
	elif is_click_moving:
		var to_target := click_target_pos - _player_node.position
		to_target.y = 0.0
		if to_target.length() > 0.4:
			move_vec = to_target.normalized()
		else:
			is_click_moving = false
			if _target_marker != null:
				_target_marker.visible = false

	# Application de la vélocité horizontale
	if move_vec != Vector3.ZERO:
		_is_moving = true
		_player_node.velocity.x = move_vec.x * cur_speed
		_player_node.velocity.z = move_vec.z * cur_speed

		# Orientation fluide de l'avatar dans la direction de la marche
		var target_angle := atan2(move_vec.x, move_vec.z)
		_player_mesh.rotation.y = lerp_angle(_player_mesh.rotation.y, target_angle, delta * 14.0)

		# Animation procédurale de foulée (balancement bras & jambes)
		_walk_cycle += delta * (14.0 if is_sprinting else 9.5)
		var swing := sin(_walk_cycle) * (0.55 if is_sprinting else 0.35)
		if _player_arm_l != null: _player_arm_l.rotation.x = -swing
		if _player_arm_r != null: _player_arm_r.rotation.x = swing
		if _player_leg_l != null: _player_leg_l.rotation.x = swing * 1.1
		if _player_leg_r != null: _player_leg_r.rotation.x = -swing * 1.1
		if _player_torso != null: _player_torso.position.y = 1.05 + abs(sin(_walk_cycle * 2.0)) * 0.04

		player_moved_3d.emit(_player_node.position)
	else:
		_is_moving = false
		_player_node.velocity.x = move_toward(_player_node.velocity.x, 0.0, cur_speed * delta * 8.0)
		_player_node.velocity.z = move_toward(_player_node.velocity.z, 0.0, cur_speed * delta * 8.0)
		# Retour au repos fluide
		if _player_arm_l != null: _player_arm_l.rotation.x = lerp(_player_arm_l.rotation.x, 0.0, delta * 8.0)
		if _player_arm_r != null: _player_arm_r.rotation.x = lerp(_player_arm_r.rotation.x, 0.0, delta * 8.0)
		if _player_leg_l != null: _player_leg_l.rotation.x = lerp(_player_leg_l.rotation.x, 0.0, delta * 8.0)
		if _player_leg_r != null: _player_leg_r.rotation.x = lerp(_player_leg_r.rotation.x, 0.0, delta * 8.0)
		if _player_torso != null: _player_torso.position.y = lerp(_player_torso.position.y, 1.05, delta * 8.0)

	_player_node.move_and_slide()

	# Suivi caméra fluide
	_camera_rig.position = _camera_rig.position.lerp(_player_node.position, delta * 12.0)

	# Le nuage de particules suit le joueur
	if _dust_particles != null:
		_dust_particles.position = _player_node.position


## 8. Contrôles Souris & Clavier : Rotation Caméra, Zoom Molette & Clic au Sol
func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		# Clic droit : orbite caméra mouselook
		if mb.button_index == MOUSE_BUTTON_RIGHT:
			is_orbiting_camera = mb.pressed
			last_mouse_pos = mb.position
		# Clic gauche : click-to-move ou ciblage
		elif mb.button_index == MOUSE_BUTTON_LEFT and mb.pressed:
			_handle_terrain_click(mb.position)
		# Molette : zoom fluide avec transition automatique de mode
		elif mb.button_index == MOUSE_BUTTON_WHEEL_UP:
			_zoom_step(-0.8)
		elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			_zoom_step(0.8)

	elif event is InputEventMouseMotion and is_orbiting_camera:
		var mm := event as InputEventMouseMotion
		camera_yaw -= mm.relative.x * 0.32
		var min_pitch := -78.0 if current_camera_mode == CameraMode.THIRD_PERSON else -65.0
		var max_pitch := 40.0 if current_camera_mode == CameraMode.THIRD_PERSON else -25.0
		camera_pitch = clampf(camera_pitch + mm.relative.y * 0.22, min_pitch, max_pitch)
		_update_camera_settings()


func _zoom_step(step: float) -> void:
	if current_camera_mode == CameraMode.THIRD_PERSON:
		camera_zoom = clampf(camera_zoom + step, MIN_ZOOM_3RD, MAX_ZOOM_3RD)
		# Si zoom au maximum, bascule fluide en isométrique
		if camera_zoom >= MAX_ZOOM_3RD and step > 0:
			set_camera_mode(CameraMode.ISOMETRIC)
			return
	else:
		camera_zoom = clampf(camera_zoom + step * 2.0, MIN_ZOOM_ISO, MAX_ZOOM_ISO)
		# Si zoom au minimum en isométrique, bascule en 3ème personne
		if camera_zoom <= MIN_ZOOM_ISO and step < 0:
			set_camera_mode(CameraMode.THIRD_PERSON)
			return
	_update_camera_settings()


## 9. Raycasting Click-to-Move
func _handle_terrain_click(screen_pos: Vector2) -> void:
	if _camera == null or _world_root == null:
		return

	var from := _camera.project_ray_origin(screen_pos)
	var to := from + _camera.project_ray_normal(screen_pos) * 1000.0

	var space_state := _world_root.get_world_3d().direct_space_state
	var query := PhysicsRayQueryParameters3D.create(from, to)
	var result := space_state.intersect_ray(query)

	if not result.is_empty():
		var hit_pos: Vector3 = result["position"]
		click_target_pos = hit_pos
		is_click_moving = true
		if _target_marker != null:
			_target_marker.position = Vector3(hit_pos.x, hit_pos.y + 0.06, hit_pos.z)
			_target_marker.visible = true
		terrain_clicked_3d.emit(hit_pos)


## 10. API d'Apparition des Entités 3D (Harvesters, Créatures, PNJ)
func spawn_entity_3d(entity_id: String, entity_type: String, world_pos: Vector3, label: String = "") -> Node3D:
	if _world_root == null:
		return null

	var ent_node := Node3D.new()
	ent_node.name = "Entity3D_" + entity_id
	ent_node.position = world_pos

	var mesh_inst := MeshInstance3D.new()
	if entity_type == "harvester":
		# Extracteur SWG industriel imposant avec tête de forage rotative
		var cyl := CylinderMesh.new()
		cyl.top_radius = 2.0
		cyl.bottom_radius = 2.8
		cyl.height = 5.6
		mesh_inst.mesh = cyl
		mesh_inst.position = Vector3(0.0, 2.8, 0.0)
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(0.72, 0.25, 0.18) # Rouge rouille industriel
		mat.metallic = 0.8
		mat.roughness = 0.35
		mesh_inst.material_override = mat

		# Gyrophare d'activité au sommet de l'extracteur
		var rotor_light := OmniLight3D.new()
		rotor_light.light_color = Color(1.0, 0.5, 0.1)
		rotor_light.light_energy = 2.0
		rotor_light.position = Vector3(0.0, 5.8, 0.0)
		ent_node.add_child(rotor_light)

	elif entity_type == "creature":
		# Créature sauvage des dunes (Krayt / Bantha)
		var box := BoxMesh.new()
		box.size = Vector3(2.2, 2.0, 3.8)
		mesh_inst.mesh = box
		mesh_inst.position = Vector3(0.0, 1.0, 0.0)
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(0.48, 0.38, 0.28) # Brun cuir sauvage
		mat.roughness = 0.9
		mesh_inst.material_override = mat
	else:
		# PNJ Humanoïde (Marchand, Médecin, Garde)
		var cap := CapsuleMesh.new()
		cap.radius = 0.42
		cap.height = 1.8
		mesh_inst.mesh = cap
		mesh_inst.position = Vector3(0.0, 0.9, 0.0)
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(0.82, 0.68, 0.30)
		mesh_inst.material_override = mat

	ent_node.add_child(mesh_inst)

	if label != "":
		var lbl := Label3D.new()
		lbl.text = label
		lbl.position = Vector3(0.0, 3.0, 0.0)
		lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		lbl.font_size = 26
		lbl.modulate = Color(1.0, 0.94, 0.78)
		ent_node.add_child(lbl)

	_world_root.add_child(ent_node)
	_active_entities_3d[entity_id] = ent_node
	return ent_node
