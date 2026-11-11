# swg_space_flight_3d.gd — Extension Spatiale Jump to Lightspeed (JTL) 3D pour Prime Client
# Rendu cinématographique Godot 4 PBR style "Road to Vostok" & "PVKK: Planetenverteidigungskanonenkommandant"
# Double caméra : Vue Cockpit Immersive Première Personne PVKK & Vue Extérieure 3e personne [V].
# Répartiteur d'énergie Tri-Voie, Dogfight contre chasseurs TIE, Astéroïdes PBR et Saut Hyperspatial.
extends SubViewportContainer
class_name SwgSpaceFlight3D

signal space_flight_exited()
signal lasers_fired(ship_id: String, target_id: String)
signal hyperspace_jumped(destination: String)

# Vue et Scène 3D
var _viewport: SubViewport = null
var _space_world: Node3D = null
var _camera: Camera3D = null
var _player_ship: Node3D = null
var _cockpit_rig: Node3D = null
var _enemy_ties: Array[Node3D] = []
var _asteroids: Array[Node3D] = []
var _engine_plumes: Array[MeshInstance3D] = []
var _crt_radar_label: Label3D = null
var _throttle_lever: Node3D = null

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
var _view_mode_btn: Button = null

# Modes de Caméra : 0 = Cockpit Tactile PVKK (1ère personne), 1 = Vue Extérieure 3e personne
var camera_mode: int = 0

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

	# Post-Processing Réaliste style "Road to Vostok" & "PVKK" (Godot 4 ACES + Glow Bloom + Fog Nébulaire)
	var env_node := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.008, 0.010, 0.022)

	# Tonemapping ACES pour contraste cinématographique doux
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.tonemap_exposure = 1.15
	env.tonemap_white = 1.25

	# Glow / Bloom chaud style tubes cathodiques CRT et voyants PVKK
	env.glow_enabled = true
	env.glow_intensity = 0.85
	env.glow_bloom = 0.35
	env.glow_hdr_threshold = 0.9
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SCREEN

	# Nébuleuse spatiale cosmique (Brouillard de profondeur)
	env.fog_enabled = true
	env.fog_light_color = Color(0.03, 0.05, 0.11)
	env.fog_density = 0.0012
	env_node.environment = env
	_space_world.add_child(env_node)

	# Éclairage Solaire Principal (DirectionalLight3D dorée avec ombres PBR)
	var sun_light := DirectionalLight3D.new()
	sun_light.rotation_degrees = Vector3(-42, 58, 0)
	sun_light.light_color = Color(1.0, 0.96, 0.88)
	sun_light.light_energy = 1.65
	sun_light.shadow_enabled = true
	sun_light.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	_space_world.add_child(sun_light)

	# Éclairage Cosmique Secondaire (Contre-jour bleuté nébulaire style Road to Vostok)
	var rim_light := DirectionalLight3D.new()
	rim_light.rotation_degrees = Vector3(35, -120, 0)
	rim_light.light_color = Color(0.3, 0.65, 1.0)
	rim_light.light_energy = 0.45
	_space_world.add_child(rim_light)

	# Champ d'étoiles cosmique et poussières
	_spawn_starfield()

	# Champ d'astéroïdes et roches PBR (Road to Vostok style)
	_spawn_asteroid_field()

	# X-Wing du joueur (extérieur)
	_player_ship = _build_xwing_mesh()
	_player_ship.position = Vector3(0, 0, 0)
	_space_world.add_child(_player_ship)

	# Cockpit tactile immersif PVKK (première personne)
	_cockpit_rig = _build_pvkk_cockpit()
	_player_ship.add_child(_cockpit_rig)

	# Caméra 3D
	_camera = Camera3D.new()
	_camera.current = true
	_space_world.add_child(_camera)
	_update_camera_mode()

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

	# Armes [F1] / [1]
	var hb_w := HBoxContainer.new()
	var lbl_w := Label.new()
	lbl_w.text = "Armes [F1/1]: "
	lbl_w.custom_minimum_size = Vector2(85, 20)
	hb_w.add_child(lbl_w)
	_pwr_weapons_bar = ProgressBar.new()
	_pwr_weapons_bar.custom_minimum_size = Vector2(105, 16)
	_pwr_weapons_bar.value = power_weapons
	hb_w.add_child(_pwr_weapons_bar)
	vb.add_child(hb_w)

	# Boucliers [F2] / [2]
	var hb_s := HBoxContainer.new()
	var lbl_s := Label.new()
	lbl_s.text = "Boucliers [F2/2]: "
	lbl_s.custom_minimum_size = Vector2(85, 20)
	hb_s.add_child(lbl_s)
	_pwr_shields_bar = ProgressBar.new()
	_pwr_shields_bar.custom_minimum_size = Vector2(105, 16)
	_pwr_shields_bar.value = power_shields
	hb_s.add_child(_pwr_shields_bar)
	vb.add_child(hb_s)

	# Moteurs [F3] / [3]
	var hb_e := HBoxContainer.new()
	var lbl_e := Label.new()
	lbl_e.text = "Moteurs [F3/3]: "
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

	# Bouton Bascule Vue Caméra [V] (Haut-Droit)
	_view_mode_btn = Button.new()
	_view_mode_btn.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	_view_mode_btn.position = Vector2(-220, 16)
	_view_mode_btn.size = Vector2(204, 32)
	_view_mode_btn.text = "🎥 Vue : Cockpit PVKK [V]"
	_view_mode_btn.focus_mode = Control.FOCUS_NONE
	_view_mode_btn.pressed.connect(toggle_camera_mode)
	_hud_overlay.add_child(_view_mode_btn)

	# Bannière d'aide & commandes (Haut-Centre)
	var banner := Label.new()
	banner.text = "✦ JUMP TO LIGHTSPEED — X-WING T-65B [Style PVKK & Road to Vostok] ✦\n[Souris / ZQSD] Pilotage  |  [Clic Gche / ESPACE] Canons Lasers  |  [Molette / Z-S] Poussée  |  [V] Vue Cockpit/Extérieur  |  [H] Hyper-espace  |  [F8/ÉCHAP] Atterrir"
	banner.set_anchors_preset(Control.PRESET_TOP_WIDE)
	banner.position = Vector2(0, 16)
	banner.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	banner.add_theme_color_override("font_color", Color(1.0, 0.9, 0.4))
	_hud_overlay.add_child(banner)

func _spawn_starfield() -> void:
	for i in range(160):
		var star := MeshInstance3D.new()
		var s_sph := SphereMesh.new()
		s_sph.radius = 0.35
		s_sph.height = 0.7
		star.mesh = s_sph
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(1.0, 1.0, 1.0)
		mat.emission_enabled = true
		mat.emission = Color(0.85, 0.92, 1.0)
		mat.emission_energy_multiplier = 3.5
		star.set_surface_override_material(0, mat)
		var rx = randf_range(-350.0, 350.0)
		var ry = randf_range(-180.0, 180.0)
		var rz = randf_range(-600.0, 120.0)
		star.position = Vector3(rx, ry, rz)
		_space_world.add_child(star)

func _spawn_asteroid_field() -> void:
	# Astéroïdes volumétriques PBR style "Road to Vostok"
	var mat_rock := StandardMaterial3D.new()
	mat_rock.albedo_color = Color(0.42, 0.40, 0.38)
	mat_rock.metallic = 0.15
	mat_rock.roughness = 0.92

	for i in range(18):
		var ast := MeshInstance3D.new()
		var b := BoxMesh.new()
		var s := randf_range(4.0, 14.0)
		b.size = Vector3(s, s * randf_range(0.7, 1.3), s * randf_range(0.8, 1.2))
		ast.mesh = b
		ast.set_surface_override_material(0, mat_rock)
		var ax := randf_range(-120.0, 120.0)
		var ay := randf_range(-40.0, 40.0)
		var az := randf_range(-300.0, -40.0)
		ast.position = Vector3(ax, ay, az)
		ast.rotation_degrees = Vector3(randf_range(0, 360), randf_range(0, 360), randf_range(0, 360))
		_space_world.add_child(ast)
		_asteroids.append(ast)

func _build_xwing_mesh() -> Node3D:
	var ship := Node3D.new()
	ship.name = "XWing_Player"

	var mat_white := StandardMaterial3D.new()
	mat_white.albedo_color = Color(0.88, 0.88, 0.90)
	mat_white.roughness = 0.45
	mat_white.metallic = 0.25

	var mat_red := StandardMaterial3D.new()
	mat_red.albedo_color = Color(0.85, 0.15, 0.15)
	mat_red.roughness = 0.5

	# Fuselage principal fuselé
	var body := MeshInstance3D.new()
	var b_box := BoxMesh.new()
	b_box.size = Vector3(1.2, 0.9, 8.5)
	body.mesh = b_box
	body.position = Vector3(0, 0.45, 0)
	body.set_surface_override_material(0, mat_white)
	ship.add_child(body)

	# Nez effilé
	var nose := MeshInstance3D.new()
	var n_box := BoxMesh.new()
	n_box.size = Vector3(0.9, 0.65, 3.0)
	nose.mesh = n_box
	nose.position = Vector3(0, 0.4, -4.5)
	nose.set_surface_override_material(0, mat_white)
	ship.add_child(nose)

	# Bandes rouges Escadron Rogue sur le nez
	var stripe := MeshInstance3D.new()
	var s_box := BoxMesh.new()
	s_box.size = Vector3(0.95, 0.1, 1.8)
	stripe.mesh = s_box
	stripe.position = Vector3(0, 0.72, -4.2)
	stripe.set_surface_override_material(0, mat_red)
	ship.add_child(stripe)

	# Verrière extérieure teintée
	var glass := MeshInstance3D.new()
	var g_box := BoxMesh.new()
	g_box.size = Vector3(0.72, 0.48, 2.2)
	glass.mesh = g_box
	glass.position = Vector3(0, 0.85, 0.5)
	var mat_glass := StandardMaterial3D.new()
	mat_glass.albedo_color = Color(0.12, 0.18, 0.25)
	mat_glass.metallic = 0.8
	mat_glass.roughness = 0.2
	glass.set_surface_override_material(0, mat_glass)
	ship.add_child(glass)

	# 4 Ailes en X avec canons laser et tuyères de réacteurs
	var wing_configs = [
		{"x": -2.2, "y": 0.8, "rot": 12.0, "eng_x": -0.85, "eng_y": 0.65},
		{"x": 2.2, "y": 0.8, "rot": -12.0, "eng_x": 0.85, "eng_y": 0.65},
		{"x": -2.2, "y": 0.1, "rot": -12.0, "eng_x": -0.85, "eng_y": 0.25},
		{"x": 2.2, "y": 0.1, "rot": 12.0, "eng_x": 0.85, "eng_y": 0.25}
	]

	var mat_engine_metal := StandardMaterial3D.new()
	mat_engine_metal.albedo_color = Color(0.25, 0.27, 0.3)
	mat_engine_metal.metallic = 0.7
	mat_engine_metal.roughness = 0.35

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
		mat_gun.metallic = 0.8
		gun.set_surface_override_material(0, mat_gun)
		ship.add_child(gun)

		# Tuyère de réacteur ionique 4x
		var engine := MeshInstance3D.new()
		var e_cyl := CylinderMesh.new()
		e_cyl.top_radius = 0.28
		e_cyl.bottom_radius = 0.32
		e_cyl.height = 2.4
		engine.mesh = e_cyl
		engine.rotation_degrees = Vector3(90, 0, 0)
		engine.position = Vector3(cfg["eng_x"], cfg["eng_y"], 2.2)
		engine.set_surface_override_material(0, mat_engine_metal)
		ship.add_child(engine)

		# Flamme de plasma ionique émissif rose/rouge (s'étire avec la vitesse)
		var plume := MeshInstance3D.new()
		var p_cyl := CylinderMesh.new()
		p_cyl.top_radius = 0.22
		p_cyl.bottom_radius = 0.05
		p_cyl.height = 1.4
		plume.mesh = p_cyl
		plume.rotation_degrees = Vector3(90, 0, 0)
		plume.position = Vector3(cfg["eng_x"], cfg["eng_y"], 3.8)

		var mat_plume := StandardMaterial3D.new()
		mat_plume.albedo_color = Color(1.0, 0.3, 0.4)
		mat_plume.emission_enabled = true
		mat_plume.emission = Color(1.0, 0.35, 0.45)
		mat_plume.emission_energy_multiplier = 4.5
		plume.set_surface_override_material(0, mat_plume)
		ship.add_child(plume)
		_engine_plumes.append(plume)

	return ship

func _build_pvkk_cockpit() -> Node3D:
	# Poste de pilotage immersif tactile style "PVKK"
	var cockpit := Node3D.new()
	cockpit.name = "PVKK_CockpitRig"
	cockpit.position = Vector3(0, 0.70, 0.35)

	# Matériaux industriels PVKK (Acier riveté, noir mat, console métallique)
	var mat_frame := StandardMaterial3D.new()
	mat_frame.albedo_color = Color(0.18, 0.20, 0.22)
	mat_frame.metallic = 0.75
	mat_frame.roughness = 0.65

	var mat_dash := StandardMaterial3D.new()
	mat_dash.albedo_color = Color(0.12, 0.13, 0.15)
	mat_dash.roughness = 0.85

	# Cadre de verrière - Montants métalliques triangulaires de cockpit
	var frame_left := MeshInstance3D.new()
	var b_left := BoxMesh.new()
	b_left.size = Vector3(0.08, 0.9, 1.4)
	frame_left.mesh = b_left
	frame_left.position = Vector3(-0.38, 0.2, -0.4)
	frame_left.rotation_degrees = Vector3(-20, 15, -10)
	frame_left.set_surface_override_material(0, mat_frame)
	cockpit.add_child(frame_left)

	var frame_right := MeshInstance3D.new()
	var b_right := BoxMesh.new()
	b_right.size = Vector3(0.08, 0.9, 1.4)
	frame_right.mesh = b_right
	frame_right.position = Vector3(0.38, 0.2, -0.4)
	frame_right.rotation_degrees = Vector3(-20, -15, 10)
	frame_right.set_surface_override_material(0, mat_frame)
	cockpit.add_child(frame_right)

	var frame_top := MeshInstance3D.new()
	var b_top := BoxMesh.new()
	b_top.size = Vector3(0.85, 0.08, 0.12)
	frame_top.mesh = b_top
	frame_top.position = Vector3(0, 0.62, -0.55)
	frame_top.set_surface_override_material(0, mat_frame)
	cockpit.add_child(frame_top)

	# Console de bord inclinée (Dashboard)
	var dash := MeshInstance3D.new()
	var d_box := BoxMesh.new()
	d_box.size = Vector3(0.85, 0.35, 0.6)
	dash.mesh = d_box
	dash.position = Vector3(0, -0.22, -0.5)
	dash.rotation_degrees.x = -25.0
	dash.set_surface_override_material(0, mat_dash)
	cockpit.add_child(dash)

	# Moniteur CRT Rétro avec affichage vectoriel vert émissif
	var crt_screen := MeshInstance3D.new()
	var c_box := BoxMesh.new()
	c_box.size = Vector3(0.32, 0.24, 0.05)
	crt_screen.mesh = c_box
	crt_screen.position = Vector3(0, -0.12, -0.65)
	crt_screen.rotation_degrees.x = -25.0

	var mat_crt := StandardMaterial3D.new()
	mat_crt.albedo_color = Color(0.02, 0.18, 0.06)
	mat_crt.emission_enabled = true
	mat_crt.emission = Color(0.12, 0.95, 0.25)
	mat_crt.emission_energy_multiplier = 2.2
	crt_screen.set_surface_override_material(0, mat_crt)
	cockpit.add_child(crt_screen)

	# Texte vectoriel 3D sur le moniteur CRT
	_crt_radar_label = Label3D.new()
	_crt_radar_label.text = "[RADAR JTL]\nCIBLE: TIE-LN\nDIST: 85m\nSTATUT: LOCK"
	_crt_radar_label.font_size = 14
	_crt_radar_label.modulate = Color(0.3, 1.0, 0.4)
	_crt_radar_label.position = Vector3(0, -0.11, -0.62)
	_crt_radar_label.rotation_degrees.x = -25.0
	cockpit.add_child(_crt_radar_label)

	# Voyants lumineux émissifs PVKK (Système, Boucliers, Hyperdrive)
	var lights_data = [
		{"pos": Vector3(-0.25, -0.15, -0.58), "color": Color(0.2, 0.95, 0.3), "name": "SYS_NOMINAL"},
		{"pos": Vector3(-0.18, -0.15, -0.58), "color": Color(0.1, 0.75, 1.0), "name": "SHIELDS_OK"},
		{"pos": Vector3(0.18, -0.15, -0.58), "color": Color(1.0, 0.65, 0.1), "name": "WEAPONS_HOT"},
		{"pos": Vector3(0.25, -0.15, -0.58), "color": Color(1.0, 0.2, 0.2), "name": "WARN_RADAR"}
	]

	for l_cfg in lights_data:
		var led := MeshInstance3D.new()
		var sph := SphereMesh.new()
		sph.radius = 0.022
		sph.height = 0.044
		led.mesh = sph
		led.position = l_cfg["pos"]
		var mat_led := StandardMaterial3D.new()
		mat_led.albedo_color = l_cfg["color"]
		mat_led.emission_enabled = true
		mat_led.emission = l_cfg["color"]
		mat_led.emission_energy_multiplier = 3.5
		led.set_surface_override_material(0, mat_led)
		cockpit.add_child(led)

	# Levier de throttle à gauche (Manette des gaz métallique)
	_throttle_lever = Node3D.new()
	_throttle_lever.position = Vector3(-0.32, -0.22, -0.45)
	var t_cyl := CylinderMesh.new()
	t_cyl.top_radius = 0.015
	t_cyl.bottom_radius = 0.015
	t_cyl.height = 0.2
	var t_mesh := MeshInstance3D.new()
	t_mesh.mesh = t_cyl
	t_mesh.position = Vector3(0, 0.1, 0)
	t_mesh.set_surface_override_material(0, mat_frame)
	_throttle_lever.add_child(t_mesh)

	var knob := MeshInstance3D.new()
	var k_sph := SphereMesh.new()
	k_sph.radius = 0.035
	k_sph.height = 0.07
	knob.mesh = k_sph
	knob.position = Vector3(0, 0.2, 0)
	var mat_knob := StandardMaterial3D.new()
	mat_knob.albedo_color = Color(0.85, 0.25, 0.2)
	mat_knob.metallic = 0.6
	knob.set_surface_override_material(0, mat_knob)
	_throttle_lever.add_child(knob)
	cockpit.add_child(_throttle_lever)

	return cockpit

func _build_tie_mesh() -> Node3D:
	var tie := Node3D.new()
	tie.name = "TIEFighter_Target"

	var mat_hull := StandardMaterial3D.new()
	mat_hull.albedo_color = Color(0.68, 0.70, 0.75)
	mat_hull.metallic = 0.8
	mat_hull.roughness = 0.35

	var mat_panel := StandardMaterial3D.new()
	mat_panel.albedo_color = Color(0.06, 0.07, 0.08)
	mat_panel.roughness = 0.6

	# Capsule sphérique
	var pod := MeshInstance3D.new()
	var p_sph := SphereMesh.new()
	p_sph.radius = 1.0
	p_sph.height = 2.0
	pod.mesh = p_sph
	pod.position = Vector3(0, 1.0, 0)
	pod.set_surface_override_material(0, mat_hull)
	tie.add_child(pod)

	# Hublot frontal octogonal émissif rouge
	var window := MeshInstance3D.new()
	var w_cyl := CylinderMesh.new()
	w_cyl.top_radius = 0.45
	w_cyl.bottom_radius = 0.45
	w_cyl.height = 0.1
	window.mesh = w_cyl
	window.rotation_degrees.x = 90.0
	window.position = Vector3(0, 1.0, -0.95)
	var mat_win := StandardMaterial3D.new()
	mat_win.albedo_color = Color(0.8, 0.1, 0.1)
	mat_win.emission_enabled = true
	mat_win.emission = Color(0.9, 0.15, 0.15)
	mat_win.emission_energy_multiplier = 2.0
	window.set_surface_override_material(0, mat_win)
	tie.add_child(window)

	# Deux grands panneaux solaires hexagonaux
	for side in [-1, 1]:
		var wing := MeshInstance3D.new()
		var w_box := BoxMesh.new()
		w_box.size = Vector3(0.12, 5.5, 4.5)
		wing.mesh = w_box
		wing.position = Vector3(side * 2.8, 1.0, 0)
		wing.set_surface_override_material(0, mat_panel)
		tie.add_child(wing)

		var pylon := MeshInstance3D.new()
		var pyl_cyl := CylinderMesh.new()
		pyl_cyl.top_radius = 0.18
		pyl_cyl.bottom_radius = 0.18
		pyl_cyl.height = 2.8
		pylon.mesh = pyl_cyl
		pylon.rotation_degrees.z = 90.0
		pylon.position = Vector3(side * 1.4, 1.0, 0)
		pylon.set_surface_override_material(0, mat_hull)
		tie.add_child(pylon)

	return tie

# Bascule caméra Vue Cockpit PVKK vs Vue Extérieure 3e personne
func toggle_camera_mode() -> void:
	camera_mode = 1 if camera_mode == 0 else 0
	_update_camera_mode()

func _update_camera_mode() -> void:
	if _camera == null or _player_ship == null:
		return
	if camera_mode == 0:
		# Vue Cockpit PVKK Immersive
		if _view_mode_btn: _view_mode_btn.text = "🎥 Vue : Cockpit PVKK [V]"
		if _cockpit_rig: _cockpit_rig.visible = true
	else:
		# Vue Extérieure 3e personne
		if _view_mode_btn: _view_mode_btn.text = "🎥 Vue : Extérieure 3D [V]"
		if _cockpit_rig: _cockpit_rig.visible = false

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
	for offset_x in [-3.5, 3.5]:
		var bolt := MeshInstance3D.new()
		var b_cyl := CylinderMesh.new()
		b_cyl.top_radius = 0.08
		b_cyl.bottom_radius = 0.08
		b_cyl.height = 4.8
		bolt.mesh = b_cyl
		bolt.rotation_degrees = Vector3(90, 0, 0)
		bolt.position = _player_ship.position + _player_ship.transform.basis * Vector3(offset_x, 0.4, -3.8)

		var mat_laser := StandardMaterial3D.new()
		mat_laser.albedo_color = Color(1.0, 0.15, 0.15)
		mat_laser.emission_enabled = true
		mat_laser.emission = Color(1.0, 0.2, 0.2)
		mat_laser.emission_energy_multiplier = 4.5
		bolt.set_surface_override_material(0, mat_laser)
		_space_world.add_child(bolt)

		var tw := create_tween()
		var forward := -_player_ship.transform.basis.z
		tw.tween_property(bolt, "position", bolt.position + forward * 220.0, 0.4)
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

		# Redressement automatique progressif du roulis
		_player_ship.rotation_degrees.z = lerpf(_player_ship.rotation_degrees.z, 0.0, 4.0 * delta)

		# Animation de la caméra selon le mode sélectionné
		if _camera != null:
			if camera_mode == 0:
				# Vue Cockpit PVKK (1ère personne centrée dans le cockpit)
				_camera.global_position = _player_ship.global_position + _player_ship.transform.basis * Vector3(0, 0.72, 0.45)
				_camera.global_rotation = _player_ship.global_rotation
			else:
				# Vue Poursuite Extérieure 3e personne
				var target_cam_pos := _player_ship.position + _player_ship.transform.basis * Vector3(0, 3.2, 9.5)
				_camera.position = _camera.position.lerp(target_cam_pos, 8.0 * delta)
				_camera.look_at(_player_ship.position + forward * 10.0, Vector3.UP)

		# Animation des tuyères de plasma des 4 réacteurs ioniques
		var speed_ratio := current_speed / max_speed
		for plume in _engine_plumes:
			if plume:
				plume.scale = Vector3(1.0, 0.8 + speed_ratio * 1.5, 1.0)

		# Animation du levier de throttle PVKK
		if _throttle_lever:
			_throttle_lever.rotation_degrees.x = -20.0 + speed_ratio * 40.0

		# Rotation lente des astéroïdes PBR (Road to Vostok style)
		for ast in _asteroids:
			ast.rotation_degrees.y += 6.0 * delta
			ast.rotation_degrees.x += 3.0 * delta

		# Déplacement relatif des chasseurs ennemis
		for tie in _enemy_ties:
			tie.position.z += 12.0 * delta
			if tie.position.z > 30.0:
				tie.position.z = -160.0
				tie.position.x = randf_range(-45.0, 45.0)

	# Télémétrie HUD
	if _speed_label != null:
		_speed_label.text = "🚀 VITESSE : %d / %d MGLT" % [int(current_speed), int(max_speed)]

	# Mise à jour radar CRT PVKK
	if _crt_radar_label != null:
		var tie_dist: int = int(_enemy_ties[0].position.distance_to(_player_ship.position)) if _enemy_ties.size() > 0 else 99
		_crt_radar_label.text = "[RADAR JTL]\nCIBLE: TIE-LN\nDIST: %dm\nSTATUT: %s" % [
			tie_dist,
			"LOCK" if tie_dist < 90 else "SCAN"
		]

	# Gestion Hyperspace
	if is_hyperspace:
		hyperspace_timer -= delta
		if hyperspace_timer <= 0.0:
			is_hyperspace = false

func _unhandled_input(event: InputEvent) -> void:
	if not visible:
		return

	# Contrôle Souris (Tir, Molette d'accélération et Orientation)
	if event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_LEFT:
			fire_lasers()
			get_viewport().set_input_as_handled()
			return
		elif event.button_index == MOUSE_BUTTON_WHEEL_UP:
			current_speed = minf(current_speed + 10.0, max_speed)
			get_viewport().set_input_as_handled()
			return
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			current_speed = maxf(current_speed - 10.0, 0.0)
			get_viewport().set_input_as_handled()
			return

	if event is InputEventMouseMotion:
		if _player_ship != null:
			_player_ship.rotation_degrees.y -= event.relative.x * 0.25
			_player_ship.rotation_degrees.x = clampf(_player_ship.rotation_degrees.x - event.relative.y * 0.25, -60.0, 60.0)
			_player_ship.rotation_degrees.z = clampf(-event.relative.x * 0.45, -35.0, 35.0)
			get_viewport().set_input_as_handled()
			return

	if event is InputEventKey and event.pressed:
		match event.keycode:
			KEY_V:
				toggle_camera_mode()
				get_viewport().set_input_as_handled()
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
