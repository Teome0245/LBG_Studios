# swg_space_flight_3d.gd — Extension Spatiale Jump to Lightspeed (JTL) 3D pour Prime Client
# Incruste un SubViewport 3D plein écran permettant le vol libre, le dogfight laser spatial
# contre des chasseurs TIE, la gestion du répartiteur d'énergie Tri-Voie et les sauts hyperspatiaux.
extends SubViewportContainer
class_name SwgSpaceFlight3D

signal space_flight_exited()
signal lasers_fired(ship_id: String, target_id: String)
signal hyperspace_jumped(destination: String)

var _viewport: SubViewport = null
var _space_world: Node3D = null
var _camera: Camera3D = null
var _player_ship: Node3D = null
var _enemy_ties: Array[Node3D] = []

# HUD 2D de vol spatial
var _hud_overlay: Control = null
var _pwr_weapons_bar: ProgressBar = null
var _pwr_shields_bar: ProgressBar = null
var _pwr_engines_bar: ProgressBar = null
var _speed_label: Label = null
var _shields_fwd_label: Label = null
var _shields_aft_label: Label = null
var _hull_label: Label = null
var _crosshair: Control = null

# Paramètres de simulation spatiale
var current_speed: float = 0.0
var max_speed: float = 120.0 # MGLT
var pitch_rate: float = 0.0
var yaw_rate: float = 0.0
var roll_angle: float = 0.0

# Répartiteur Tri-Voie
var power_weapons: int = 33
var power_shields: int = 33
var power_engines: int = 34

# État du vaisseau
var shield_fwd: int = 1000
var shield_aft: int = 1000
var hull_hp: int = 1500
var is_hyperspace: bool = false
var hyperspace_timer: float = 0.0

func _init() -> void:
	name = "SwgSpaceFlight3D"
	set_anchors_preset(Control.PRESET_FULL_RECT)
	stretch = true
	visible = false
	_setup_3d_viewport()
	_setup_flight_hud()

func _ready() -> void:
	if _viewport == null:
		_setup_3d_viewport()
	if _hud_overlay == null:
		_setup_flight_hud()

func _setup_3d_viewport() -> void:
	_viewport = SubViewport.new()
	_viewport.name = "SpaceViewport3D"
	_viewport.size = Vector2i(1280, 720)
	_viewport.own_world_3d = true
	_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(_viewport)

	_space_world = Node3D.new()
	_space_world.name = "SpaceWorld"
	_viewport.add_child(_space_world)

	# Environnement stellaire (Espace sombre + étoiles)
	var env_node := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.01, 0.01, 0.025)
	env.glow_enabled = true
	env.glow_intensity = 0.8
	env.glow_bloom = 0.3
	env_node.environment = env
	_space_world.add_child(env_node)

	var dir_light := DirectionalLight3D.new()
	dir_light.rotation_degrees = Vector3(-45, 60, 0)
	dir_light.light_color = Color(1.0, 0.95, 0.85)
	dir_light.light_energy = 1.4
	_space_world.add_child(dir_light)

	# Champ d'étoiles procédural
	_spawn_starfield()

	# X-Wing du joueur
	_player_ship = _build_xwing_mesh()
	_player_ship.position = Vector3(0, 0, 0)
	_space_world.add_child(_player_ship)

	# Caméra de poursuite 3D
	_camera = Camera3D.new()
	_camera.position = Vector3(0, 3.2, 9.5)
	_camera.rotation_degrees = Vector3(-12, 0, 0)
	_camera.current = true
	_space_world.add_child(_camera)

	# Ennemi de dogfight : Chasseur TIE
	var tie := _build_tie_mesh()
	tie.position = Vector3(15.0, 5.0, -80.0)
	_space_world.add_child(tie)
	_enemy_ties.append(tie)

func _setup_flight_hud() -> void:
	_hud_overlay = Control.new()
	_hud_overlay.name = "SpaceHudOverlay"
	_hud_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	_hud_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_hud_overlay)

	# Viseur Réticule Holographique central
	_crosshair = Control.new()
	_crosshair.set_anchors_preset(Control.PRESET_CENTER)
	_crosshair.custom_minimum_size = Vector2(40, 40)
	_hud_overlay.add_child(_crosshair)

	# Panneau Répartiteur Tri-Voie (Bas-Gauche)
	var pwr_panel := Panel.new()
	pwr_panel.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	pwr_panel.position = Vector2(24, -160)
	pwr_panel.size = Vector2(220, 136)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.04, 0.12, 0.18, 0.85)
	sb.set_border_width_all(1)
	sb.border_color = Color(0.2, 0.8, 0.9, 0.9)
	sb.set_corner_radius_all(6)
	pwr_panel.add_theme_stylebox_override("panel", sb)
	_hud_overlay.add_child(pwr_panel)

	var pwr_title := Label.new()
	pwr_title.text = "⚡ RÉPARTITEUR D'ÉNERGIE JTL"
	pwr_title.position = Vector2(10, 8)
	pwr_title.add_theme_font_size_override("font_size", 12)
	pwr_title.add_theme_color_override("font_color", Color(0.9, 0.95, 1.0))
	pwr_panel.add_child(pwr_title)

	var vb := VBoxContainer.new()
	vb.position = Vector2(10, 32)
	vb.size = Vector2(200, 90)
	pwr_panel.add_child(vb)

	# Armes [F5]
	var hb_w := HBoxContainer.new()
	var lbl_w := Label.new()
	lbl_w.text = "Armes [F5]: "
	lbl_w.custom_minimum_size = Vector2(85, 20)
	hb_w.add_child(lbl_w)
	_pwr_weapons_bar = ProgressBar.new()
	_pwr_weapons_bar.custom_minimum_size = Vector2(105, 16)
	_pwr_weapons_bar.value = power_weapons
	hb_w.add_child(_pwr_weapons_bar)
	vb.add_child(hb_w)

	# Boucliers [F6]
	var hb_s := HBoxContainer.new()
	var lbl_s := Label.new()
	lbl_s.text = "Boucliers [F6]: "
	lbl_s.custom_minimum_size = Vector2(85, 20)
	hb_s.add_child(lbl_s)
	_pwr_shields_bar = ProgressBar.new()
	_pwr_shields_bar.custom_minimum_size = Vector2(105, 16)
	_pwr_shields_bar.value = power_shields
	hb_s.add_child(_pwr_shields_bar)
	vb.add_child(hb_s)

	# Moteurs [F7]
	var hb_e := HBoxContainer.new()
	var lbl_e := Label.new()
	lbl_e.text = "Moteurs [F7]: "
	lbl_e.custom_minimum_size = Vector2(85, 20)
	hb_e.add_child(lbl_e)
	_pwr_engines_bar = ProgressBar.new()
	_pwr_engines_bar.custom_minimum_size = Vector2(105, 16)
	_pwr_engines_bar.value = power_engines
	hb_e.add_child(_pwr_engines_bar)
	vb.add_child(hb_e)

	# Télémétrie Vitesse & Boucliers (Bas-Droite)
	var stat_panel := Panel.new()
	stat_panel.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	stat_panel.position = Vector2(-244, -160)
	stat_panel.size = Vector2(220, 136)
	stat_panel.add_theme_stylebox_override("panel", sb)
	_hud_overlay.add_child(stat_panel)

	_speed_label = Label.new()
	_speed_label.text = "🚀 VITESSE : 0 / 120 MGLT"
	_speed_label.position = Vector2(12, 12)
	_speed_label.add_theme_color_override("font_color", Color(0.3, 0.95, 0.4))
	stat_panel.add_child(_speed_label)

	_shields_fwd_label = Label.new()
	_shields_fwd_label.text = "🛡 BOUCLIER AVANT : 1000/1000"
	_shields_fwd_label.position = Vector2(12, 38)
	_shields_fwd_label.add_theme_color_override("font_color", Color(0.2, 0.8, 1.0))
	stat_panel.add_child(_shields_fwd_label)

	_shields_aft_label = Label.new()
	_shields_aft_label.text = "🛡 BOUCLIER ARRIÈRE : 1000/1000"
	_shields_aft_label.position = Vector2(12, 64)
	_shields_aft_label.add_theme_color_override("font_color", Color(0.2, 0.8, 1.0))
	stat_panel.add_child(_shields_aft_label)

	_hull_label = Label.new()
	_hull_label.text = "⚙ COQUE X-WING : 1500/1500"
	_hull_label.position = Vector2(12, 90)
	_hull_label.add_theme_color_override("font_color", Color(1.0, 0.85, 0.2))
	stat_panel.add_child(_hull_label)

	# Bannière d'aide & commandes (Haut-Centre)
	var banner := Label.new()
	banner.text = "✦ JUMP TO LIGHTSPEED — X-WING T-65B ✦\n[Z/S] Poussée Moteurs  |  [Q/D] Roulis/Lacet  |  [ESPACE] Canons Lasers  |  [H] Hyper-espace  |  [F9] Atterrir"
	banner.set_anchors_preset(Control.PRESET_TOP_WIDE)
	banner.position = Vector2(0, 16)
	banner.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	banner.add_theme_color_override("font_color", Color(1.0, 0.9, 0.4))
	_hud_overlay.add_child(banner)

func _spawn_starfield() -> void:
	for i in range(120):
		var star := MeshInstance3D.new()
		var s_sph := SphereMesh.new()
		s_sph.radius = 0.4
		s_sph.height = 0.8
		star.mesh = s_sph
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(1.0, 1.0, 1.0)
		mat.emission_enabled = true
		mat.emission = Color(0.8, 0.9, 1.0)
		mat.emission_energy_multiplier = 3.0
		star.set_surface_override_material(0, mat)
		var rx = randf_range(-300.0, 300.0)
		var ry = randf_range(-150.0, 150.0)
		var rz = randf_range(-500.0, 100.0)
		star.position = Vector3(rx, ry, rz)
		_space_world.add_child(star)

func _build_xwing_mesh() -> Node3D:
	var ship := Node3D.new()
	ship.name = "XWing_Player"

	var mat_white := StandardMaterial3D.new()
	mat_white.albedo_color = Color(0.85, 0.85, 0.88)
	mat_white.roughness = 0.4

	# Fuselage fuselé
	var body := MeshInstance3D.new()
	var b_box := BoxMesh.new()
	b_box.size = Vector3(1.2, 0.9, 8.5)
	body.mesh = b_box
	body.position = Vector3(0, 0.45, 0)
	body.set_surface_override_material(0, mat_white)
	ship.add_child(body)

	# Cockpit avec verrière
	var glass := MeshInstance3D.new()
	var g_box := BoxMesh.new()
	g_box.size = Vector3(0.7, 0.45, 2.2)
	glass.mesh = g_box
	glass.position = Vector3(0, 0.85, 0.5)
	var mat_glass := StandardMaterial3D.new()
	mat_glass.albedo_color = Color(0.1, 0.2, 0.3)
	glass.set_surface_override_material(0, mat_glass)
	ship.add_child(glass)

	# 4 Ailes en X avec canons laser
	var wing_configs = [
		{"x": -2.2, "y": 0.8, "rot": 12.0},
		{"x": 2.2, "y": 0.8, "rot": -12.0},
		{"x": -2.2, "y": 0.1, "rot": -12.0},
		{"x": 2.2, "y": 0.1, "rot": 12.0}
	]

	for cfg in wing_configs:
		var wing := MeshInstance3D.new()
		var w_box := BoxMesh.new()
		w_box.size = Vector3(3.8, 0.1, 1.8)
		wing.mesh = w_box
		wing.position = Vector3(cfg["x"], cfg["y"], 0.8)
		wing.rotation_degrees.z = cfg["rot"]
		wing.set_surface_override_material(0, mat_white)
		ship.add_child(wing)

		# Canon laser au bout de chaque aile
		var gun := MeshInstance3D.new()
		var g_cyl := CylinderMesh.new()
		g_cyl.top_radius = 0.06
		g_cyl.bottom_radius = 0.08
		g_cyl.height = 3.6
		gun.mesh = g_cyl
		gun.rotation_degrees = Vector3(90, 0, 0)
		gun.position = Vector3(cfg["x"] * 1.7, cfg["y"], -1.2)
		var mat_gun := StandardMaterial3D.new()
		mat_gun.albedo_color = Color(0.2, 0.22, 0.25)
		gun.set_surface_override_material(0, mat_gun)
		ship.add_child(gun)

	return ship

func _build_tie_mesh() -> Node3D:
	var tie := Node3D.new()
	tie.name = "TIEFighter_Target"

	var mat_hull := StandardMaterial3D.new()
	mat_hull.albedo_color = Color(0.65, 0.68, 0.72)
	mat_hull.metallic = 0.8

	var mat_panel := StandardMaterial3D.new()
	mat_panel.albedo_color = Color(0.08, 0.09, 0.1)

	var pod := MeshInstance3D.new()
	var p_sph := SphereMesh.new()
	p_sph.radius = 1.0
	p_sph.height = 2.0
	pod.mesh = p_sph
	pod.position = Vector3(0, 1.0, 0)
	pod.set_surface_override_material(0, mat_hull)
	tie.add_child(pod)

	for side in [-1, 1]:
		var wing := MeshInstance3D.new()
		var w_box := BoxMesh.new()
		w_box.size = Vector3(0.12, 5.5, 4.5)
		wing.mesh = w_box
		wing.position = Vector3(side * 2.8, 1.0, 0)
		wing.set_surface_override_material(0, mat_panel)
		tie.add_child(wing)

	return tie

# Bascule d'affichage du vol spatial JTL
func toggle_space_flight() -> void:
	visible = not visible
	if visible:
		current_speed = 35.0
		Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
	else:
		space_flight_exited.emit()

func enter_space() -> void:
	visible = true
	current_speed = 35.0

func exit_space() -> void:
	visible = false
	space_flight_exited.emit()

# Répartiteur Tri-Voie
func set_power_distribution(w: int, s: int, e: int) -> void:
	var tot = w + s + e
	if tot <= 0: return
	power_weapons = int(float(w) / float(tot) * 100.0)
	power_shields = int(float(s) / float(tot) * 100.0)
	power_engines = 100 - power_weapons - power_shields
	if _pwr_weapons_bar: _pwr_weapons_bar.value = power_weapons
	if _pwr_shields_bar: _pwr_shields_bar.value = power_shields
	if _pwr_engines_bar: _pwr_engines_bar.value = power_engines
	max_speed = 60.0 + float(power_engines) * 1.5

# Tir de canons lasers 3D
func fire_lasers() -> void:
	if _player_ship == null: return
	var bolt := MeshInstance3D.new()
	var b_cyl := CylinderMesh.new()
	b_cyl.top_radius = 0.08
	b_cyl.bottom_radius = 0.08
	b_cyl.height = 4.5
	bolt.mesh = b_cyl
	bolt.rotation_degrees = Vector3(90, 0, 0)
	bolt.position = _player_ship.position + Vector3(0, 0.4, -4.0)

	var mat_laser := StandardMaterial3D.new()
	mat_laser.albedo_color = Color(1.0, 0.1, 0.1)
	mat_laser.emission_enabled = true
	mat_laser.emission = Color(1.0, 0.15, 0.15)
	mat_laser.emission_energy_multiplier = 4.0
	bolt.set_surface_override_material(0, mat_laser)
	_space_world.add_child(bolt)

	# Animation / déplacement du projectile laser
	var tw := create_tween()
	tw.tween_property(bolt, "position:z", bolt.position.z - 180.0, 0.4)
	tw.tween_callback(bolt.queue_free)

	lasers_fired.emit("xwing_player", "target_tie")

# Saut hyperspatial
func trigger_hyperspace(dest: String = "Secteur Corellien") -> void:
	is_hyperspace = true
	hyperspace_timer = 2.5
	hyperspace_jumped.emit(dest)

func _process(delta: float) -> void:
	if not visible:
		return

	# Déplacement du vaisseau joueur
	if _player_ship != null:
		var forward := -_player_ship.transform.basis.z
		_player_ship.position += forward * current_speed * delta

		# Suivi caméra
		if _camera != null:
			_camera.position = _player_ship.position + Vector3(0, 3.2, 9.5)

		# Déplacement relatif des chasseurs ennemis
		for tie in _enemy_ties:
			tie.position.z += 12.0 * delta
			if tie.position.z > 30.0:
				tie.position.z = -150.0
				tie.position.x = randf_range(-40.0, 40.0)

	# Télémétrie HUD
	if _speed_label != null:
		_speed_label.text = "🚀 VITESSE : %d / %d MGLT" % [int(current_speed), int(max_speed)]

	# Gestion Hyperspace
	if is_hyperspace:
		hyperspace_timer -= delta
		if hyperspace_timer <= 0.0:
			is_hyperspace = false

func _unhandled_input(event: InputEvent) -> void:
	if not visible:
		return

	if event is InputEventKey and event.pressed:
		match event.keycode:
			KEY_Z, KEY_W, KEY_UP:
				current_speed = minf(current_speed + 15.0, max_speed)
				get_viewport().set_input_as_handled()
			KEY_S, KEY_DOWN:
				current_speed = maxf(current_speed - 15.0, 0.0)
				get_viewport().set_input_as_handled()
			KEY_Q, KEY_A, KEY_LEFT:
				if _player_ship: _player_ship.rotation_degrees.y += 10.0
				get_viewport().set_input_as_handled()
			KEY_D, KEY_RIGHT:
				if _player_ship: _player_ship.rotation_degrees.y -= 10.0
				get_viewport().set_input_as_handled()
			KEY_SPACE:
				fire_lasers()
				get_viewport().set_input_as_handled()
			KEY_H:
				trigger_hyperspace()
				get_viewport().set_input_as_handled()
			KEY_F1, KEY_1:
				set_power_distribution(60, 20, 20)
				get_viewport().set_input_as_handled()
			KEY_F2, KEY_2:
				set_power_distribution(20, 60, 20)
				get_viewport().set_input_as_handled()
			KEY_F3, KEY_3:
				set_power_distribution(20, 20, 60)
				get_viewport().set_input_as_handled()
			KEY_ESCAPE, KEY_F8:
				exit_space()
				get_viewport().set_input_as_handled()

