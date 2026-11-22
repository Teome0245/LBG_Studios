# world_ground_3d.gd — Rendu Full 3D du Monde Planétaire Lost Heaven (Scrapaltai)
# Intègre la caméra isométrique 3/4 orbitale (T4C / SWG), le terrain 3D PBR,
# les entités 3D (joueur, PNJ, extracteurs Harvesters) et l'interfaçage avec le HUD 2D.
extends SubViewportContainer
class_name WorldGround3D

signal player_moved_3d(new_pos: Vector3)
signal entity_clicked_3d(entity_id: String, entity_type: String)
signal terrain_clicked_3d(target_pos: Vector3)

# Composants 3D fondamentaux
var _viewport: SubViewport = null
var _world_root: Node3D = null
var _camera_rig: Node3D = null
var _camera: Camera3D = null
var _sun_light: DirectionalLight3D = null
var _world_env: WorldEnvironment = null
var _terrain_mesh: MeshInstance3D = null

# Gestion du Joueur 3D et des PNJ
var _player_node: CharacterBody3D = null
var _player_mesh: Node3D = null
var _target_marker: MeshInstance3D = null
var _active_entities_3d: Dictionary = {} # id -> Node3D

# Contrôles de Caméra Isométrique 3/4 Orbitale
var camera_pitch: float = -42.0 # Angle de plongée isométrique (degrés)
var camera_yaw: float = 45.0   # Angle d'orientation orbital (degrés)
var camera_zoom: float = 16.0  # Distance au joueur (mètres)
const MIN_ZOOM: float = 6.0
const MAX_ZOOM: float = 38.0

# Paramètres de déplacement joueur
var player_speed: float = 7.5 # m/s
var is_click_moving: bool = false
var click_target_pos: Vector3 = Vector3.ZERO
var is_orbiting_camera: bool = false
var last_mouse_pos: Vector2 = Vector2.ZERO


func _init() -> void:
	name = "WorldGround3D"
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_PASS
	_setup_viewport_and_world_3d()
	_setup_lighting_and_atmosphere()
	_setup_terrain_mesh()
	_setup_player_avatar_3d()


func _ready() -> void:
	if _viewport == null:
		_setup_viewport_and_world_3d()
		_setup_lighting_and_atmosphere()
		_setup_terrain_mesh()
		_setup_player_avatar_3d()


## 1. Initialisation du SubViewport et de la Hiérarchie 3D
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

	# Rig Caméra Orbitale articulé
	_camera_rig = Node3D.new()
	_camera_rig.name = "CameraIsometricRig"
	_world_root.add_child(_camera_rig)

	_camera = Camera3D.new()
	_camera.name = "CameraIsometric3D"
	_camera.fov = 50.0
	_camera.near = 0.5
	_camera.far = 800.0
	_camera_rig.add_child(_camera)
	_update_camera_transform()


## 2. Éclairage PBR & Ambiance Atmosphérique de Scrapaltai (Teintes cuivrées / oranger)
func _setup_lighting_and_atmosphere() -> void:
	# Soleil désertique à double composante (lumière chaude rasante)
	_sun_light = DirectionalLight3D.new()
	_sun_light.name = "SunLightScrapaltai"
	_sun_light.rotation_degrees = Vector3(-50.0, 35.0, 0.0)
	_sun_light.light_color = Color(1.0, 0.88, 0.72) # Éclat chaud
	_sun_light.light_energy = 1.3
	_sun_light.shadow_enabled = true
	_sun_light.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	_world_root.add_child(_sun_light)

	# Environnement ciel et brume des sables
	_world_env = WorldEnvironment.new()
	_world_env.name = "WorldEnvScrapaltai"
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.85, 0.65, 0.45) # Brume chaude d'horizon
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.55, 0.42, 0.32)
	env.ambient_light_energy = 0.65
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.glow_enabled = true
	env.glow_intensity = 0.25
	env.fog_enabled = true
	env.fog_light_color = Color(0.82, 0.62, 0.42)
	env.fog_density = 0.0018
	_world_env.environment = env
	_world_root.add_child(_world_env)


## 3. Génération du Sol 3D de Lost Heaven (Grand plateau désertique et dunes)
func _setup_terrain_mesh() -> void:
	_terrain_mesh = MeshInstance3D.new()
	_terrain_mesh.name = "GroundTerrain3D"

	# Plan de 600m x 600m autour de la ville
	var plane_mesh := PlaneMesh.new()
	plane_mesh.size = Vector2(600.0, 600.0)
	plane_mesh.subdivide_width = 32
	plane_mesh.subdivide_depth = 32
	_terrain_mesh.mesh = plane_mesh

	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.76, 0.58, 0.38) # Ocre désertique
	mat.roughness = 0.92
	mat.metallic = 0.05
	_terrain_mesh.material_override = mat

	# Collision du sol pour le raycasting et click-to-move T4C
	var body := StaticBody3D.new()
	body.name = "TerrainStaticBody"
	var col_shape := CollisionShape3D.new()
	var box_shape := BoxShape3D.new()
	box_shape.size = Vector3(600.0, 1.0, 600.0)
	col_shape.shape = box_shape
	col_shape.position = Vector3(0.0, -0.5, 0.0)
	body.add_child(col_shape)
	_terrain_mesh.add_child(body)

	_world_root.add_child(_terrain_mesh)

	# Anneau de ciblage au sol (vert néon / cyan)
	_target_marker = MeshInstance3D.new()
	_target_marker.name = "TargetCircleMarker"
	var torus := TorusMesh.new()
	torus.inner_radius = 0.75
	torus.outer_radius = 0.95
	_target_marker.mesh = torus
	var torus_mat := StandardMaterial3D.new()
	torus_mat.albedo_color = Color(0.0, 0.95, 0.82, 0.85)
	torus_mat.emission_enabled = true
	torus_mat.emission = Color(0.0, 0.95, 0.82)
	torus_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_target_marker.material_override = torus_mat
	_target_marker.visible = false
	_world_root.add_child(_target_marker)


## 4. Initialisation de l'Avatar Joueur 3D (Standard Humanoid)
func _setup_player_avatar_3d() -> void:
	_player_node = CharacterBody3D.new()
	_player_node.name = "Player3D"
	_player_node.position = Vector3(0.0, 0.0, 0.0)

	var col := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = 0.45
	capsule.height = 1.85
	col.shape = capsule
	col.position = Vector3(0.0, 0.92, 0.0)
	_player_node.add_child(col)

	# Modèle visuel du joueur (silhouette Humanoid stylisée aux couleurs de Lost Heaven)
	_player_mesh = Node3D.new()
	_player_mesh.name = "VisualModel"
	var body_mesh := MeshInstance3D.new()
	var body_capsule := CapsuleMesh.new()
	body_capsule.radius = 0.38
	body_capsule.height = 1.6
	body_mesh.mesh = body_capsule
	body_mesh.position = Vector3(0.0, 0.95, 0.0)
	var player_mat := StandardMaterial3D.new()
	player_mat.albedo_color = Color(0.18, 0.32, 0.48) # Bleu sombre aventurier
	player_mat.roughness = 0.6
	body_mesh.material_override = player_mat
	_player_mesh.add_child(body_mesh)

	# Visière / Yeux dorés (indique l'orientation du regard)
	var visor := MeshInstance3D.new()
	var visor_box := BoxMesh.new()
	visor_box.size = Vector3(0.35, 0.12, 0.18)
	visor.mesh = visor_box
	visor.position = Vector3(0.0, 1.48, 0.28)
	var visor_mat := StandardMaterial3D.new()
	visor_mat.albedo_color = Color(0.0, 0.95, 0.85)
	visor_mat.emission_enabled = true
	visor_mat.emission = Color(0.0, 0.95, 0.85)
	visor.material_override = visor_mat
	_player_mesh.add_child(visor)

	_player_node.add_child(_player_mesh)
	_world_root.add_child(_player_node)


## 5. Mise à jour de la Caméra Orbitale Isométrique
func _update_camera_transform() -> void:
	if _camera_rig == null or _camera == null:
		return
	if _player_node != null:
		_camera_rig.position = _player_node.position

	_camera_rig.rotation_degrees = Vector3(0.0, camera_yaw, 0.0)
	var pitch_rad := deg_to_rad(camera_pitch)
	var offset_y := -sin(pitch_rad) * camera_zoom
	var offset_z := cos(pitch_rad) * camera_zoom
	_camera.position = Vector3(0.0, offset_y, offset_z)
	_camera.rotation_degrees = Vector3(camera_pitch, 0.0, 0.0)


## 6. Boucle de Rendu & Physique Temps Réel
func _physics_process(delta: float) -> void:
	if _player_node == null:
		return

	var move_vec := Vector3.ZERO

	# 1. Déplacement ZQSD (relativement à l'angle de la caméra orbitale)
	var input_dir := Vector2.ZERO
	if Input.is_action_pressed("ui_up") or Input.is_key_pressed(KEY_Z) or Input.is_key_pressed(KEY_W):
		input_dir.y -= 1.0
	if Input.is_action_pressed("ui_down") or Input.is_key_pressed(KEY_S):
		input_dir.y += 1.0
	if Input.is_action_pressed("ui_left") or Input.is_key_pressed(KEY_Q) or Input.is_key_pressed(KEY_A):
		input_dir.x -= 1.0
	if Input.is_action_pressed("ui_right") or Input.is_key_pressed(KEY_D):
		input_dir.x += 1.0

	if input_dir != Vector2.ZERO:
		is_click_moving = false # Interrompt le click-to-move si touche clavier pressée
		input_dir = input_dir.normalized()
		var forward := -_camera_rig.transform.basis.z
		var right := _camera_rig.transform.basis.x
		forward.y = 0.0
		right.y = 0.0
		forward = forward.normalized()
		right = right.normalized()
		move_vec = (forward * -input_dir.y) + (right * input_dir.x)

	# 2. Click-to-Move style T4C
	elif is_click_moving:
		var to_target := click_target_pos - _player_node.position
		to_target.y = 0.0
		if to_target.length() > 0.4:
			move_vec = to_target.normalized()
		else:
			is_click_moving = false
			if _target_marker != null:
				_target_marker.visible = false

	# Application du déplacement
	if move_vec != Vector3.ZERO:
		_player_node.velocity = move_vec * player_speed
		_player_node.move_and_slide()
		# Oriente doucement le mesh dans la direction de la marche
		var target_angle := atan2(move_vec.x, move_vec.z)
		_player_mesh.rotation.y = lerp_angle(_player_mesh.rotation.y, target_angle, delta * 12.0)
		player_moved_3d.emit(_player_node.position)

	# La caméra suit le joueur
	_camera_rig.position = _camera_rig.position.lerp(_player_node.position, delta * 10.0)


## 7. Gestion des Événements Souris : Rotation Caméra & Click-to-Move
func _gui_input(event: InputEvent) -> void:
	# Clic droit enfoncé pour pivoter la caméra en orbite
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_RIGHT:
			is_orbiting_camera = mb.pressed
			last_mouse_pos = mb.position
		elif mb.button_index == MOUSE_BUTTON_LEFT and mb.pressed:
			_handle_terrain_click(mb.position)
		elif mb.button_index == MOUSE_BUTTON_WHEEL_UP:
			camera_zoom = clampf(camera_zoom - 1.5, MIN_ZOOM, MAX_ZOOM)
			_update_camera_transform()
		elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			camera_zoom = clampf(camera_zoom + 1.5, MIN_ZOOM, MAX_ZOOM)
			_update_camera_transform()

	elif event is InputEventMouseMotion and is_orbiting_camera:
		var mm := event as InputEventMouseMotion
		camera_yaw -= mm.relative.x * 0.35
		camera_pitch = clampf(camera_pitch + mm.relative.y * 0.25, -75.0, -15.0)
		_update_camera_transform()


## 8. Raycast depuis la caméra vers le sol 3D pour le Click-to-Move
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
			_target_marker.position = Vector3(hit_pos.x, 0.05, hit_pos.z)
			_target_marker.visible = true
		terrain_clicked_3d.emit(hit_pos)


## 9. API Externe pour faire apparaître des PNJ / Harvesters 3D dans le monde
func spawn_entity_3d(entity_id: String, entity_type: String, world_pos: Vector3, label: String = "") -> Node3D:
	if _world_root == null:
		return null

	var ent_node := Node3D.new()
	ent_node.name = "Entity3D_" + entity_id
	ent_node.position = world_pos

	var mesh_inst := MeshInstance3D.new()
	if entity_type == "harvester":
		# Extracteur SWG : Structure cylindrique imposante avec tête de forage
		var cyl := CylinderMesh.new()
		cyl.top_radius = 1.8
		cyl.bottom_radius = 2.4
		cyl.height = 5.0
		mesh_inst.mesh = cyl
		mesh_inst.position = Vector3(0.0, 2.5, 0.0)
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(0.65, 0.22, 0.15) # Rouge rouille industriel
		mat.metallic = 0.8
		mat.roughness = 0.35
		mesh_inst.material_override = mat
	elif entity_type == "creature":
		# Créature sauvage (Krayt / Bantha)
		var box := BoxMesh.new()
		box.size = Vector3(2.0, 1.8, 3.5)
		mesh_inst.mesh = box
		mesh_inst.position = Vector3(0.0, 0.9, 0.0)
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(0.42, 0.35, 0.25)
		mesh_inst.material_override = mat
	else:
		# PNJ Humanoïde (Marchand, Garde, Médecin)
		var cap := CapsuleMesh.new()
		cap.radius = 0.4
		cap.height = 1.75
		mesh_inst.mesh = cap
		mesh_inst.position = Vector3(0.0, 0.88, 0.0)
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(0.75, 0.65, 0.25)
		mesh_inst.material_override = mat

	ent_node.add_child(mesh_inst)

	if label != "":
		var lbl := Label3D.new()
		lbl.text = label
		lbl.position = Vector3(0.0, 2.6, 0.0)
		lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		lbl.font_size = 24
		lbl.modulate = Color(1.0, 0.92, 0.75)
		ent_node.add_child(lbl)

	_world_root.add_child(ent_node)
	_active_entities_3d[entity_id] = ent_node
	return ent_node
