extends CharacterBody3D
## Contrôleur Joueur 3D Authentique Star Wars Galaxies (Pre-CU)
## 1. Caméra TPS 3ème personne orbitale avec SpringArm3D (anti-collision décor) et zoom molette (1ère à 3ème personne).
## 2. Double mode de contrôle SWG : Curseur libre (interaction UI/monde) ou Mouselook (maintien Clic-Droit).
## 3. Postures 3D physiques : Debout (1.8m), Accroupi (1.1m), Couché / Prone (0.5m) avec redimensionnement dynamique de capsule.
## 4. Intégration directe des 9 attributs HAM, des états de combat et de la vitesse selon la posture.

signal posture_changed(new_posture: String)
signal target_selected(target_node: Node3D)

const _SwgVrmAnimatorScript := preload("res://scripts/swg_vrm_animator.gd")
const _SwgSkinSystemScript := preload("res://scripts/swg_skin_system.gd")

var current_skin_index: int = 0
var current_species_id: String = "human"

const SPEED_WALK: float = 3.5
const SPEED_RUN: float = 7.0
const SPEED_SPRINT: float = 10.0
const SPEED_KNEEL: float = 2.4
const SPEED_PRONE: float = 1.2
const JUMP_VELOCITY: float = 4.8
const GRAVITY: float = 14.0

const MOUSE_SENSITIVITY: float = 0.003
const ZOOM_SPEED: float = 0.6
const ZOOM_MIN: float = 0.8
const ZOOM_MAX: float = 16.0

# 3 Postures SWG
enum Posture { STANDING, KNEELING, PRONE }
var current_posture: Posture = Posture.STANDING

# Caméra & Visée
var _cam_yaw: float = 0.0
var _cam_pitch: float = -0.2
var _target_zoom: float = 5.5
var _is_mouselook: bool = false
var _is_running: bool = true

# Références Nœuds 3D
var _spring_arm: SpringArm3D = null
var _camera: Camera3D = null
var _collision_shape: CollisionShape3D = null
var _capsule: CapsuleShape3D = null
var _mesh_root: Node3D = null
var _nameplate_label: Label3D = null

# États de combat SWG
var is_knocked_down: bool = false
var is_dizzy: bool = false
var is_stunned: bool = false


func _ready() -> void:
	_setup_nodes()
	_apply_posture_dimensions(current_posture)


func _setup_nodes() -> void:
	# Capsule de collision
	_collision_shape = CollisionShape3D.new()
	_capsule = CapsuleShape3D.new()
	_capsule.radius = 0.45
	_capsule.height = 1.8
	_collision_shape.shape = _capsule
	_collision_shape.position = Vector3(0, 0.9, 0)
	add_child(_collision_shape)

	# Modèle visuel de base (VRM Compagnon ou Fallback Procédural)
	_mesh_root = Node3D.new()
	_mesh_root.name = "AvatarVisual"
	add_child(_mesh_root)
	_load_vrm_or_procedural_avatar()

	# Nameplate 3D au-dessus de la tête
	_nameplate_label = Label3D.new()
	_nameplate_label.text = "Voyageur de Lost Heaven\n« Pionnier des Sables »"
	_nameplate_label.position = Vector3(0, 2.2, 0)
	_nameplate_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_nameplate_label.font_size = 14
	_nameplate_label.modulate = Color(0.85, 0.95, 1.0, 0.95)
	add_child(_nameplate_label)

	# Bras de caméra SpringArm3D (anti-collision murs SWG)
	_spring_arm = SpringArm3D.new()
	_spring_arm.name = "CameraSpringArm"
	_spring_arm.position = Vector3(0, 1.45, 0)
	_spring_arm.spring_length = _target_zoom
	_spring_arm.margin = 0.2
	add_child(_spring_arm)

	# Caméra 3D
	_camera = Camera3D.new()
	_camera.name = "PlayerCamera3D"
	_camera.current = true
	_camera.fov = 72.0
	_spring_arm.add_child(_camera)


func _load_vrm_or_procedural_avatar() -> void:
	_load_vrm_model("Compagnon.vrm")


func _load_vrm_model(vrm_name: String) -> bool:
	# Nettoie tout animateur ou modèle résiduel
	for c in _mesh_root.get_children():
		c.queue_free()
	var old_anim := find_child("VrmAnimator", true, false)
	if old_anim: old_anim.queue_free()

	var candidate_paths := [
		"res://assets/avatars/" + vrm_name,
		"packages/compagnon-desktop/overlay/vrm/" + vrm_name,
		"C:/Agent_IA/compagnon-desktop/overlay/vrm/" + vrm_name,
		"J:/swgemu/clients/swg-client/assets/avatars/" + vrm_name,
		"res://assets/avatars/Compagnon.vrm"
	]

	for p in candidate_paths:
		var full_p := ProjectSettings.globalize_path(p)
		if FileAccess.file_exists(full_p):
			var gltf := GLTFDocument.new()
			var state := GLTFState.new()
			var err := gltf.append_from_file(full_p, state)
			if err == OK:
				var scene := gltf.generate_scene(state)
				if scene != null:
					scene.name = "SpeciesModel3D"
					scene.rotation_degrees.y = 180.0
					scene.scale = Vector3(0.95, 0.95, 0.95)
					_mesh_root.add_child(scene)

					var sk: Skeleton3D = _SwgVrmAnimatorScript.find_skeleton_in_tree(scene)
					if sk != null:
						var anim := _SwgVrmAnimatorScript.new()
						anim.name = "VrmAnimator"
						add_child(anim)
						anim.setup(sk)
					return true

	_build_procedural_avatar()
	return false


func apply_species(sp: Dictionary) -> void:
	current_species_id = str(sp.get("id", "human"))
	var vrm_file: String = str(sp.get("vrm_model", "Compagnon.vrm"))
	var scale_vec: Vector3 = sp.get("scale_vec", Vector3(0.95, 0.95, 0.95))
	var s_title: String = str(sp.get("title", "« Voyageur »"))
	var tint: Color = sp.get("skin_tint", Color.WHITE)

	_load_vrm_model(vrm_file)
	if _mesh_root:
		_mesh_root.scale = scale_vec

	# Teinte cutanée / fourrure
	_SwgSkinSystemScript.apply_skin(_mesh_root, {
		"primary": tint,
		"secondary": Color(0.85, 0.85, 0.9),
		"hair": tint * 0.8,
		"metallic": 0.2,
		"roughness": 0.7
	})

	if _nameplate_label:
		_nameplate_label.text = "Voyageur de Lost Heaven\n%s" % s_title
		_nameplate_label.position.y = 2.2 * scale_vec.y


func _build_procedural_avatar() -> void:
	var body_mesh := MeshInstance3D.new()
	var capsule_mesh := CapsuleMesh.new()
	capsule_mesh.radius = 0.45
	capsule_mesh.height = 1.8
	body_mesh.mesh = capsule_mesh
	body_mesh.position = Vector3(0, 0.9, 0)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.15, 0.55, 0.75, 1.0)
	mat.roughness = 0.4
	mat.metallic = 0.3
	body_mesh.set_surface_override_material(0, mat)
	_mesh_root.add_child(body_mesh)

	# Visière / Face avant pour repérer l'orientation
	var visor := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = Vector3(0.35, 0.15, 0.25)
	visor.mesh = box
	visor.position = Vector3(0, 1.5, -0.38)
	var mat_vis := StandardMaterial3D.new()
	mat_vis.albedo_color = Color(0.95, 0.85, 0.2, 1.0)
	mat_vis.emission_enabled = true
	mat_vis.emission = Color(0.95, 0.85, 0.2, 1.0)
	mat_vis.emission_energy_multiplier = 1.5
	visor.set_surface_override_material(0, mat_vis)
	_mesh_root.add_child(visor)


func _unhandled_input(event: InputEvent) -> void:
	# Maintien clic droit : Mouselook actif (caméra tourne avec la souris)
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_RIGHT:
			_is_mouselook = event.pressed
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED if _is_mouselook else Input.MOUSE_MODE_VISIBLE
		elif event.button_index == MOUSE_BUTTON_WHEEL_UP and event.pressed:
			_target_zoom = clampf(_target_zoom - ZOOM_SPEED, ZOOM_MIN, ZOOM_MAX)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN and event.pressed:
			_target_zoom = clampf(_target_zoom + ZOOM_SPEED, ZOOM_MIN, ZOOM_MAX)

	# Rotation de caméra à la souris
	if event is InputEventMouseMotion and _is_mouselook:
		_cam_yaw -= event.relative.x * MOUSE_SENSITIVITY
		_cam_pitch = clampf(_cam_pitch - event.relative.y * MOUSE_SENSITIVITY, -deg_to_rad(75.0), deg_to_rad(60.0))

	# Gestion des touches de postures SWG
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_X:
				# Bascule Accroupi (Kneeling)
				if current_posture == Posture.KNEELING:
					set_posture(Posture.STANDING)
				else:
					set_posture(Posture.KNEELING)
			KEY_Z:
				# Bascule Couché (Prone)
				if current_posture == Posture.PRONE:
					set_posture(Posture.STANDING)
				else:
					set_posture(Posture.PRONE)
			KEY_V:
				_is_running = not _is_running
			KEY_F6:
				cycle_skin()


func cycle_skin() -> String:
	current_skin_index = (current_skin_index + 1) % _SwgSkinSystemScript.PLAYER_SKIN_PRESETS.size()
	apply_player_skin(current_skin_index)
	var s_name: String = str(_SwgSkinSystemScript.PLAYER_SKIN_PRESETS[current_skin_index]["name"])
	return s_name


func apply_player_skin(idx: int) -> void:
	if _mesh_root != null:
		var preset: Dictionary = _SwgSkinSystemScript.PLAYER_SKIN_PRESETS[idx]
		_SwgSkinSystemScript.apply_skin(_mesh_root, preset)


func _physics_process(delta: float) -> void:
	# Application de la gravité
	if not is_on_floor():
		velocity.y -= GRAVITY * delta

	# Mise à jour de la caméra orbitale
	_update_camera(delta)

	# Si renversé à terre (Knockdown), immobilisation temporaire
	if is_knocked_down:
		velocity.x = move_toward(velocity.x, 0.0, 10.0 * delta)
		velocity.z = move_toward(velocity.z, 0.0, 10.0 * delta)
		move_and_slide()
		return

	# Lecture des entrées de mouvement (ZQSD / WASD / Flèches)
	var input_dir := Vector2.ZERO
	if Input.is_action_pressed("move_forward"):
		input_dir.y += 1.0
	if Input.is_action_pressed("move_backward"):
		input_dir.y -= 1.0
	if Input.is_action_pressed("move_left"):
		input_dir.x -= 1.0
	if Input.is_action_pressed("move_right"):
		input_dir.x += 1.0
	input_dir = input_dir.normalized()

	# Saut SWG (autorisé uniquement debout)
	if Input.is_action_just_pressed("jump") and is_on_floor() and current_posture == Posture.STANDING:
		velocity.y = JUMP_VELOCITY

	# Calcul de la vitesse selon la posture SWG
	var target_speed := SPEED_RUN if _is_running else SPEED_WALK
	match current_posture:
		Posture.KNEELING:
			target_speed = SPEED_KNEEL
		Posture.PRONE:
			target_speed = SPEED_PRONE

	if is_stunned:
		target_speed *= 0.6

	# Direction relative à la caméra 3D
	var forward: Vector3 = -_camera.global_transform.basis.z
	forward.y = 0.0
	forward = forward.normalized()
	var right: Vector3 = _camera.global_transform.basis.x
	right.y = 0.0
	right = right.normalized()

	var move_vec: Vector3 = (forward * input_dir.y + right * input_dir.x).normalized()

	if move_vec.length() > 0.01:
		velocity.x = move_toward(velocity.x, move_vec.x * target_speed, 18.0 * delta)
		velocity.z = move_toward(velocity.z, move_vec.z * target_speed, 18.0 * delta)

		# Rotation du personnage vers la direction de course
		var target_rot_y := atan2(-move_vec.x, -move_vec.z)
		_mesh_root.rotation.y = lerp_angle(_mesh_root.rotation.y, target_rot_y, 12.0 * delta)
	else:
		velocity.x = move_toward(velocity.x, 0.0, 24.0 * delta)
		velocity.z = move_toward(velocity.z, 0.0, 24.0 * delta)

	move_and_slide()


func _update_camera(delta: float) -> void:
	if _spring_arm == null:
		return
	_spring_arm.rotation.y = _cam_yaw
	_spring_arm.rotation.x = _cam_pitch
	_spring_arm.spring_length = lerpf(_spring_arm.spring_length, _target_zoom, 10.0 * delta)


func set_posture(p: Posture) -> void:
	# Si étourdi (Dizzy) et qu'on essaie de se relever depuis prone ou knockdown
	if is_dizzy and (current_posture == Posture.PRONE or is_knocked_down) and p == Posture.STANDING:
		is_knocked_down = true
		_dizzy_fall()
		return

	current_posture = p
	_apply_posture_dimensions(current_posture)

	var p_str := "Debout"
	match current_posture:
		Posture.KNEELING: p_str = "Accroupi"
		Posture.PRONE: p_str = "Couché"

	posture_changed.emit(p_str)


func _apply_posture_dimensions(p: Posture) -> void:
	if _capsule == null or _collision_shape == null or _mesh_root == null:
		return

	match p:
		Posture.STANDING:
			_capsule.height = 1.8
			_collision_shape.position.y = 0.9
			_mesh_root.scale = Vector3(1.0, 1.0, 1.0)
			_mesh_root.position = Vector3.ZERO
			if _nameplate_label: _nameplate_label.position.y = 2.2
		Posture.KNEELING:
			_capsule.height = 1.15
			_collision_shape.position.y = 0.58
			_mesh_root.scale = Vector3(1.0, 0.65, 1.0)
			_mesh_root.position = Vector3(0, -0.32, 0)
			if _nameplate_label: _nameplate_label.position.y = 1.6
		Posture.PRONE:
			_capsule.height = 0.55
			_collision_shape.position.y = 0.28
			_mesh_root.scale = Vector3(1.2, 0.3, 1.4)
			_mesh_root.position = Vector3(0, -0.62, 0)
			if _nameplate_label: _nameplate_label.position.y = 1.0


func _dizzy_fall() -> void:
	# Combo fatal SWG : chute immédiate au sol
	current_posture = Posture.PRONE
	_apply_posture_dimensions(Posture.PRONE)
	posture_changed.emit("Chute Vertige (Dizzy Fall)")
	if is_inside_tree() and get_tree():
		await get_tree().create_timer(3.0).timeout
		is_knocked_down = false
