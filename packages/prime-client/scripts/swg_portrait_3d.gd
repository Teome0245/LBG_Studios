# swg_portrait_3d.gd — Aperçu 3D du Compagnon / Joueur pour le HUD SWG (SubViewport3D)
extends SubViewportContainer
class_name SwgPortrait3D

const VRM_RES_PATH := "res://assets/avatars/Compagnon.vrm"

var _viewport: SubViewport = null
var _world_root: Node3D = null
var _camera: Camera3D = null
var _dir_light: DirectionalLight3D = null
var _rim_light: OmniLight3D = null
var _avatar_node: Node3D = null
var _face_mesh: MeshInstance3D = null
var _head_bone_idx: int = -1
var _skeleton: Skeleton3D = null

# Indices des blendshapes pour les expressions faciales et le clignement
var _bs_eye_close: int = -1
var _bs_eye_close_r: int = -1
var _bs_joy: int = -1
var _bs_sorrow: int = -1
var _bs_surprised: int = -1

# Animation temps réel
var _anim_time: float = 0.0
var _blink_timer: float = 3.0
var _is_blinking: bool = false
var _blink_elapsed: float = 0.0

# État HAM et posture
var _health_ratio: float = 1.0
var _battle_fatigue: int = 0
var _posture: String = "Debout"
var _warning_pulse: float = 0.0


func _init() -> void:
	name = "SwgPortrait3D"
	custom_minimum_size = Vector2(48, 48)
	size = Vector2(48, 48)
	stretch = true
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_setup_viewport_3d()
	_load_or_build_avatar()


func _ready() -> void:
	if _viewport == null:
		_setup_viewport_3d()
		_load_or_build_avatar()


func _setup_viewport_3d() -> void:
	_viewport = SubViewport.new()
	_viewport.name = "Viewport3D"
	_viewport.size = Vector2i(96, 96)
	_viewport.transparent_bg = true
	_viewport.own_world_3d = true
	_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(_viewport)

	_world_root = Node3D.new()
	_world_root.name = "WorldRoot"
	_viewport.add_child(_world_root)

	# 1. Caméra de cadrage buste / 3/4 face
	_camera = Camera3D.new()
	_camera.name = "PortraitCam"
	_camera.current = true
	_camera.position = Vector3(0.045, 1.34, 0.42)
	_camera.rotation_degrees = Vector3(-5.4, 6.1, 0.0)
	_camera.fov = 34.0
	_camera.near = 0.05
	_camera.far = 10.0
	_world_root.add_child(_camera)

	# 1b. Environnement Studio (Lumière ambiante pour déboucher les ombres)
	var env_node := WorldEnvironment.new()
	env_node.name = "PortraitEnv"
	var env := Environment.new()
	env.background_mode = Environment.BG_CLEAR_COLOR
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.20, 0.28, 0.42)
	env.ambient_light_energy = 0.85
	env_node.environment = env
	_world_root.add_child(env_node)

	# 2. Lumière Studio Principale (Key Light)
	_dir_light = DirectionalLight3D.new()
	_dir_light.name = "KeyLight"
	_dir_light.rotation_degrees = Vector3(-18.0, 30.0, 0.0)
	_dir_light.light_color = Color(0.92, 0.96, 1.0)
	_dir_light.light_energy = 1.3
	_world_root.add_child(_dir_light)

	# 3. Rim Light Holographique Cyan (Contre-jour Cyber Scrapaltai)
	_rim_light = OmniLight3D.new()
	_rim_light.name = "RimLight"
	_rim_light.position = Vector3(-0.25, 1.45, -0.20)
	_rim_light.light_color = Color(0.0, 0.96, 0.88)
	_rim_light.light_energy = 2.2
	_rim_light.omni_range = 1.6
	_world_root.add_child(_rim_light)

	# 4. Fill Light chaude d'ambiance
	var fill_light := OmniLight3D.new()
	fill_light.name = "FillLight"
	fill_light.position = Vector3(0.25, 1.15, 0.35)
	fill_light.light_color = Color(0.95, 0.68, 0.38)
	fill_light.light_energy = 0.45
	fill_light.omni_range = 1.2
	_world_root.add_child(fill_light)


func _load_or_build_avatar() -> void:
	var loaded := false
	var global_path := ProjectSettings.globalize_path(VRM_RES_PATH)

	# Chemins candidats du modèle VRM
	var candidate_paths := [
		VRM_RES_PATH,
		global_path,
		"packages/cortex/compagnon_ui/public/vrm/Compagnon.vrm",
		"packages/compagnon-desktop/overlay/vrm/Compagnon.vrm",
		"res://Compagnon.vrm",
	]

	for p in candidate_paths:
		if FileAccess.file_exists(p):
			loaded = _try_load_vrm_file(p)
			if loaded:
				break

	if not loaded:
		_build_procedural_chassis()


func _try_load_vrm_file(path: String) -> bool:
	var gltf_doc := GLTFDocument.new()
	var gltf_state := GLTFState.new()
	var err := gltf_doc.append_from_file(path, gltf_state)
	if err != OK:
		return false

	var scene := gltf_doc.generate_scene(gltf_state)
	if scene == null:
		return false

	_avatar_node = scene
	_avatar_node.name = "VrmAvatar"
	_world_root.add_child(_avatar_node)

	# Récupération du Mesh Visage et détection des blendshapes
	_face_mesh = _avatar_node.find_child("Face", true, false) as MeshInstance3D
	if _face_mesh and _face_mesh.mesh:
		var bs_cnt: int = _face_mesh.mesh.get_blend_shape_count()
		for i in range(bs_cnt):
			var bs_name: String = str(_face_mesh.mesh.get_blend_shape_name(i)).to_lower()
			if bs_name.contains("eye_close") and not bs_name.contains("close_r"):
				_bs_eye_close = i
			elif bs_name.contains("eye_close_r"):
				_bs_eye_close_r = i
			elif bs_name.contains("joy"):
				_bs_joy = i
			elif bs_name.contains("sorrow"):
				_bs_sorrow = i
			elif bs_name.contains("surprised"):
				_bs_surprised = i

	_skeleton = _avatar_node.find_child("Skeleton3D", true, false) as Skeleton3D
	if _skeleton:
		for b in range(_skeleton.get_bone_count()):
			var bname: String = str(_skeleton.get_bone_name(b)).to_lower()
			if bname.contains("head") and not bname.contains("hair"):
				_head_bone_idx = b
				break

	return true


func _build_procedural_chassis() -> void:
	# Buste androïde de secours élégant si aucun binaire VRM n'est déployé
	_avatar_node = Node3D.new()
	_avatar_node.name = "ProceduralAvatar"
	_world_root.add_child(_avatar_node)

	# Torse / plastron
	var chest := MeshInstance3D.new()
	var chest_box := BoxMesh.new()
	chest_box.size = Vector3(0.28, 0.22, 0.16)
	var mat_chest := StandardMaterial3D.new()
	mat_chest.albedo_color = Color(0.14, 0.24, 0.39) # #243d63
	mat_chest.metallic = 0.85
	mat_chest.roughness = 0.3
	chest.mesh = chest_box
	chest.position = Vector3(0.0, 1.10, 0.0)
	chest.set_surface_override_material(0, mat_chest)
	_avatar_node.add_child(chest)

	# Cou mécanique
	var neck := MeshInstance3D.new()
	var neck_cyl := CylinderMesh.new()
	neck_cyl.top_radius = 0.04
	neck_cyl.bottom_radius = 0.045
	neck_cyl.height = 0.08
	var mat_dark := StandardMaterial3D.new()
	mat_dark.albedo_color = Color(0.04, 0.08, 0.12) # #061320
	neck.mesh = neck_cyl
	neck.position = Vector3(0.0, 1.23, 0.0)
	neck.set_surface_override_material(0, mat_dark)
	_avatar_node.add_child(neck)

	# Tête
	var head := MeshInstance3D.new()
	var head_sphere := SphereMesh.new()
	head_sphere.radius = 0.08
	head_sphere.height = 0.17
	head.mesh = head_sphere
	head.position = Vector3(0.0, 1.33, 0.0)
	head.set_surface_override_material(0, mat_chest)
	_avatar_node.add_child(head)

	# Visière / yeux cyan émissifs
	var visor := MeshInstance3D.new()
	var visor_box := BoxMesh.new()
	visor_box.size = Vector3(0.10, 0.025, 0.04)
	var mat_visor := StandardMaterial3D.new()
	mat_visor.albedo_color = Color(0.0, 0.96, 0.83)
	mat_visor.emission_enabled = true
	mat_visor.emission = Color(0.0, 0.96, 0.83)
	mat_visor.emission_energy_multiplier = 2.0
	visor.mesh = visor_box
	visor.position = Vector3(0.0, 1.335, 0.065)
	visor.set_surface_override_material(0, mat_visor)
	_avatar_node.add_child(visor)


func update_ham_state(health_ratio: float, fatigue: int, posture: String) -> void:
	_health_ratio = clampf(health_ratio, 0.0, 1.0)
	_battle_fatigue = maxi(0, fatigue)
	_posture = posture
	queue_redraw()

	# Ajustement de l'expression faciale selon la santé et la fatigue
	if _face_mesh:
		if _health_ratio < 0.35 or _battle_fatigue > 350:
			if _bs_sorrow >= 0:
				_face_mesh.set_blend_shape_value(_bs_sorrow, 0.45)
			if _bs_joy >= 0:
				_face_mesh.set_blend_shape_value(_bs_joy, 0.0)
		elif _health_ratio >= 0.85 and _battle_fatigue < 100:
			if _bs_joy >= 0:
				_face_mesh.set_blend_shape_value(_bs_joy, 0.25)
			if _bs_sorrow >= 0:
				_face_mesh.set_blend_shape_value(_bs_sorrow, 0.0)
		else:
			if _bs_sorrow >= 0:
				_face_mesh.set_blend_shape_value(_bs_sorrow, 0.0)
			if _bs_joy >= 0:
				_face_mesh.set_blend_shape_value(_bs_joy, 0.0)


func _draw() -> void:
	# Cadre holographique cyan autour du portrait 3D
	var rect := Rect2(Vector2.ZERO, size)
	draw_rect(rect, Color(0.24, 0.82, 0.94, 0.92), false, 1.2)

	# Badge posture semi-transparent en bas
	if _posture != "":
		var badge_rect := Rect2(1, size.y - 12, size.x - 2, 11)
		draw_rect(badge_rect, Color(0.01, 0.08, 0.11, 0.85), true)
		draw_rect(badge_rect, Color(0.18, 0.70, 0.82, 0.75), false, 1.0)
		var font := ThemeDB.fallback_font
		if font:
			draw_string(font, Vector2(2, size.y - 3), _posture, HORIZONTAL_ALIGNMENT_CENTER, int(size.x - 4), 8, Color(0.85, 0.97, 1.0, 0.95))


func _process(delta: float) -> void:
	_anim_time += delta

	if _avatar_node == null:
		return

	# 1. Respiration subtile (oscillation en hauteur)
	var breath_speed := 2.2 if _health_ratio >= 0.50 else 3.8 # Respiration plus vive si blessé
	var breath_y := sin(_anim_time * breath_speed) * 0.002
	_avatar_node.position.y = breath_y

	# 2. Balancement subtil du regard / tête en 3/4 face
	var sway := sin(_anim_time * 0.75) * 0.035
	_avatar_node.rotation.y = sway

	# 3. Clignement automatique des yeux toutes les 3 à 5 secondes
	_blink_timer -= delta
	if _blink_timer <= 0.0 and not _is_blinking:
		_is_blinking = true
		_blink_elapsed = 0.0

	if _is_blinking:
		_blink_elapsed += delta
		var blink_progress := _blink_elapsed / 0.16 # Durée clignement : 160ms
		if blink_progress >= 1.0:
			_is_blinking = false
			_blink_timer = randf_range(3.2, 5.5)
			if _face_mesh and _bs_eye_close >= 0:
				_face_mesh.set_blend_shape_value(_bs_eye_close, 0.0)
		else:
			var blink_val := sin(blink_progress * PI)
			if _face_mesh and _bs_eye_close >= 0:
				_face_mesh.set_blend_shape_value(_bs_eye_close, blink_val)

	# 4. Pulsation d'alerte sur la rim light si santé critique
	if _health_ratio < 0.25 and _rim_light:
		_warning_pulse += delta * 6.0
		var pulse := (sin(_warning_pulse) + 1.0) * 0.5
		_rim_light.light_color = Color(0.95, 0.20, 0.25).lerp(Color(0.0, 0.96, 0.88), 0.3)
		_rim_light.light_energy = 1.5 + pulse * 1.5
	elif _rim_light:
		_rim_light.light_color = Color(0.0, 0.96, 0.88)
		_rim_light.light_energy = 2.2
