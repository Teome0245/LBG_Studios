# world_ground_3d.gd — Rendu Full 3D Haute Fidélité du Monde Planétaire Lost Heaven
# Rapproche l'esthétique 3D de l'esprit Star Wars Galaxies (SWG Pre-CU / Tatooine / Mos Eisley)
# Génère la ville complète de Lost Heaven (15+ bâtiments architecturés, dômes, cantina, spatioport,
# remparts d'enceinte, voies pavées, évaporateurs d'humidité) à partir des fichiers JSON de la carte.
# Charge le modèle 3D du Compagnon (Compagnon.vrm) pour l'avatar joueur avec caméra 3ème personne.
extends SubViewportContainer
class_name WorldGround3D

signal player_moved_3d(new_pos: Vector3)
signal entity_clicked_3d(entity_id: String, entity_type: String)
signal terrain_clicked_3d(target_pos: Vector3)
signal terrain_right_clicked_3d(screen_pos: Vector2, target_pos: Vector3)
signal camera_mode_changed(mode_name: String)

enum CameraMode {
	THIRD_PERSON, # Caméra 3ème personne immersive (Over-the-shoulder MMO style SWG)
	ISOMETRIC     # Caméra isométrique 3/4 classique orbitale (style T4C / RTS)
}

const BUILDINGS_PATH := "res://assets/maps/lost_heaven_buildings.json"
const PROPS_PATH := "res://assets/maps/lost_heaven_props.json"
const VRM_AVATAR_PATH := "res://assets/avatars/Compagnon.vrm"

# Ancre géographique de Lost Heaven dans le monde de Scrapaltai
const LH_ANCHOR_X: float = 4749.0
const LH_ANCHOR_Z: float = -737.0

# --- Composants 3D fondamentaux ---
var _viewport: SubViewport = null
var _world_root: Node3D = null
var _camera_rig: Node3D = null
var _spring_arm: SpringArm3D = null
var _camera: Camera3D = null
var _sun_light: DirectionalLight3D = null
var _world_env: WorldEnvironment = null
var _terrain_root: Node3D = null
var _city_root: Node3D = null
var _dust_particles: CPUParticles3D = null

# --- Gestion du Joueur 3D et du Modèle Compagnon ---
var _player_node: CharacterBody3D = null
var _player_mesh: Node3D = null
var _vrm_avatar: Node3D = null
var _vrm_skeleton: Skeleton3D = null
var _bone_l_arm: int = -1
var _bone_r_arm: int = -1
var _bone_l_forearm: int = -1
var _bone_r_forearm: int = -1
var _bone_l_leg: int = -1
var _bone_r_leg: int = -1
var _bone_l_knee: int = -1
var _bone_r_knee: int = -1
var _bone_spine: int = -1
var _procedural_avatar_nodes: Array = []
var _target_marker: MeshInstance3D = null
var _entities_root: Node3D = null
var _active_entities_3d: Dictionary = {}

# --- Contrôles de Caméra ---
var current_camera_mode: CameraMode = CameraMode.THIRD_PERSON
var camera_pitch: float = -18.0
var camera_yaw: float = 0.0
var camera_zoom: float = 5.5
const MIN_ZOOM_3RD: float = 1.8
const MAX_ZOOM_3RD: float = 14.0
const MIN_ZOOM_ISO: float = 12.0
const MAX_ZOOM_ISO: float = 40.0

# --- Physique & Déplacement Joueur ---
var player_speed: float = 7.5
var player_sprint_speed: float = 11.5
var jump_velocity: float = 6.2
var gravity: float = 18.0
var is_click_moving: bool = false
var click_target_pos: Vector3 = Vector3.ZERO
var is_orbiting_camera: bool = false
var last_mouse_pos: Vector2 = Vector2.ZERO

var _is_left_down: bool = false
var _left_down_pos: Vector2 = Vector2.ZERO
var _left_dragged: bool = false
var _is_right_down: bool = false
var _right_down_pos: Vector2 = Vector2.ZERO
var _right_dragged: bool = false

# Animation procédurale
var _walk_cycle: float = 0.0
var _idle_timer: float = 0.0
var _is_moving: bool = false


func _init() -> void:
	name = "WorldGround3D"
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_PASS
	_setup_viewport_and_world_3d()
	_setup_pbr_atmosphere_and_sky()
	_setup_desert_environment()
	_setup_lost_heaven_city()
	_setup_player_avatar()
	_setup_sand_particles()
	_entities_root = Node3D.new()
	_entities_root.name = "Entities3D"
	_world_root.add_child(_entities_root)


func _ready() -> void:
	if _viewport == null:
		_setup_viewport_and_world_3d()
		_setup_pbr_atmosphere_and_sky()
		_setup_desert_environment()
		_setup_lost_heaven_city()
		_setup_player_avatar()
		_setup_sand_particles()
	_entities_root = Node3D.new()
	_entities_root.name = "Entities3D"
	_world_root.add_child(_entities_root)


## 1. Initialisation du SubViewport et de la Hiérarchie Caméra
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

	_camera_rig = Node3D.new()
	_camera_rig.name = "Camera3DRig"
	_world_root.add_child(_camera_rig)

	_spring_arm = SpringArm3D.new()
	_spring_arm.name = "CameraSpringArm"
	_spring_arm.spring_length = camera_zoom
	_spring_arm.margin = 0.25
	_spring_arm.position = Vector3(0.0, 1.55, 0.0)
	_camera_rig.add_child(_spring_arm)

	_camera = Camera3D.new()
	_camera.name = "MainCamera3D"
	_camera.fov = 65.0
	_camera.near = 0.25
	_camera.far = 2500.0
	_spring_arm.add_child(_camera)

	_update_camera_settings()


## 2. Éclairage PBR & Ciel Procédural de Scrapaltai
func _setup_pbr_atmosphere_and_sky() -> void:
	_world_env = WorldEnvironment.new()
	_world_env.name = "WorldEnvScrapaltaiPBR"

	var env := Environment.new()
	var sky := Sky.new()
	var sky_mat := ProceduralSkyMaterial.new()
	sky_mat.sky_top_color = Color(0.24, 0.44, 0.70)
	sky_mat.sky_horizon_color = Color(0.95, 0.72, 0.46)
	sky_mat.sky_curve = 0.12
	sky_mat.ground_bottom_color = Color(0.32, 0.22, 0.16)
	sky_mat.ground_horizon_color = Color(0.88, 0.62, 0.38)
	sky_mat.ground_curve = 0.08
	sky.sky_material = sky_mat

	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = 0.50

	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.tonemap_exposure = 0.92
	env.ssao_enabled = true
	env.ssao_radius = 1.8
	env.ssao_intensity = 2.0
	env.glow_enabled = true
	env.glow_intensity = 0.45
	env.glow_bloom = 0.10

	env.volumetric_fog_enabled = true
	env.volumetric_fog_density = 0.00035
	env.volumetric_fog_albedo = Color(0.92, 0.78, 0.58)

	_world_env.environment = env
	_world_root.add_child(_world_env)

	_sun_light = DirectionalLight3D.new()
	_sun_light.name = "ScrapaltaiSun"
	_sun_light.rotation_degrees = Vector3(-42.0, 38.0, 0.0)
	_sun_light.light_color = Color(1.0, 0.94, 0.84)
	_sun_light.light_energy = 1.15
	_sun_light.shadow_enabled = true
	_sun_light.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	_world_root.add_child(_sun_light)


## 3. Relief Désertique & Grande Étendue Sablonneuse
func _setup_desert_environment() -> void:
	_terrain_root = Node3D.new()
	_terrain_root.name = "TerrainEnvironment"
	_world_root.add_child(_terrain_root)

	# Sol planétaire étendu à 3200m x 3200m pour englober toute la vallée de Lost Heaven
	var main_ground := MeshInstance3D.new()
	main_ground.name = "MainSandPlane"
	var plane_mesh := PlaneMesh.new()
	plane_mesh.size = Vector2(3200.0, 3200.0)
	plane_mesh.subdivide_width = 64
	plane_mesh.subdivide_depth = 64
	main_ground.mesh = plane_mesh

	var sand_mat := StandardMaterial3D.new()
	sand_mat.albedo_color = Color(0.76, 0.61, 0.44)
	sand_mat.roughness = 0.98
	sand_mat.metallic = 0.01
	main_ground.material_override = sand_mat

	var body := StaticBody3D.new()
	body.name = "GroundStaticBody"
	var col_shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(3200.0, 1.0, 3200.0)
	col_shape.shape = box
	col_shape.position = Vector3(0.0, -0.5, 0.0)
	body.add_child(col_shape)
	main_ground.add_child(body)
	_terrain_root.add_child(main_ground)

	# Placette centrale sci-fi d'accueil (Lost Heaven Nexus)
	var plaza := MeshInstance3D.new()
	plaza.name = "LostHeavenPlaza"
	var cyl := CylinderMesh.new()
	cyl.top_radius = 35.0
	cyl.bottom_radius = 35.0
	cyl.height = 0.15
	plaza.mesh = cyl
	plaza.position = Vector3(0.0, 0.08, 0.0)
	var plaza_mat := StandardMaterial3D.new()
	plaza_mat.albedo_color = Color(0.25, 0.28, 0.33)
	plaza_mat.metallic = 0.85
	plaza_mat.roughness = 0.4
	plaza.material_override = plaza_mat
	_terrain_root.add_child(plaza)

	# Anneaux d'énergie néon cyan au centre
	var plaza_ring := MeshInstance3D.new()
	var torus := TorusMesh.new()
	torus.inner_radius = 33.5
	torus.outer_radius = 34.5
	plaza_ring.mesh = torus
	plaza_ring.position = Vector3(0.0, 0.16, 0.0)
	var ring_mat := StandardMaterial3D.new()
	ring_mat.albedo_color = Color(0.0, 0.88, 0.96)
	ring_mat.emission_enabled = true
	ring_mat.emission = Color(0.0, 0.88, 0.96)
	ring_mat.emission_energy_multiplier = 1.3
	plaza_ring.material_override = ring_mat
	_terrain_root.add_child(plaza_ring)

	# Tour Relais Holographique centrale
	var tower := Node3D.new()
	tower.name = "CentralRelayMast"
	tower.position = Vector3(0.0, 0.0, -22.0)
	var mast := MeshInstance3D.new()
	var mast_cyl := CylinderMesh.new()
	mast_cyl.top_radius = 0.7
	mast_cyl.bottom_radius = 1.6
	mast_cyl.height = 24.0
	mast.mesh = mast_cyl
	mast.position = Vector3(0.0, 12.0, 0.0)
	var mast_mat := StandardMaterial3D.new()
	mast_mat.albedo_color = Color(0.32, 0.36, 0.42)
	mast_mat.metallic = 0.9
	mast.material_override = mast_mat
	tower.add_child(mast)

	var beacon := OmniLight3D.new()
	beacon.light_color = Color(0.0, 0.9, 1.0)
	beacon.light_energy = 3.5
	beacon.omni_range = 40.0
	beacon.position = Vector3(0.0, 24.2, 0.0)
	tower.add_child(beacon)
	_terrain_root.add_child(tower)

	# Canyons et falaises lointaines
	var mesa_positions := [
		Vector3(-750, 25, -950), Vector3(850, 32, -800),
		Vector3(-1100, 38, 650), Vector3(980, 28, 920),
		Vector3(-450, 20, 1250), Vector3(1200, 42, 200)
	]
	var rock_mat := StandardMaterial3D.new()
	rock_mat.albedo_color = Color(0.58, 0.40, 0.28)
	rock_mat.roughness = 0.96

	for i in range(mesa_positions.size()):
		var mesa := MeshInstance3D.new()
		mesa.name = "Mesa_%d" % i
		var m_cyl := CylinderMesh.new()
		m_cyl.top_radius = randf_range(60.0, 110.0)
		m_cyl.bottom_radius = m_cyl.top_radius * 1.35
		m_cyl.height = randf_range(45.0, 95.0)
		mesa.mesh = m_cyl
		mesa.position = mesa_positions[i]
		mesa.material_override = rock_mat
		_terrain_root.add_child(mesa)


## 4. Génération de la Ville Complète de Lost Heaven (Style SWG Mos Eisley / Tatooine)
func _setup_lost_heaven_city() -> void:
	_city_root = Node3D.new()
	_city_root.name = "LostHeavenCity3D"
	_world_root.add_child(_city_root)

	# Matériaux architecturaux SWG Pre-CU
	var mat_adobe := StandardMaterial3D.new()
	mat_adobe.albedo_color = Color(0.82, 0.70, 0.54) # Grès d'adobe Tatooine
	mat_adobe.roughness = 0.92
	mat_adobe.metallic = 0.05

	var mat_dome := StandardMaterial3D.new()
	mat_dome.albedo_color = Color(0.88, 0.84, 0.76) # Dôme crépi blanc sable
	mat_dome.roughness = 0.85
	mat_dome.metallic = 0.08

	var mat_metal := StandardMaterial3D.new()
	mat_metal.albedo_color = Color(0.38, 0.42, 0.46) # Duracier cuivré
	mat_metal.roughness = 0.45
	mat_metal.metallic = 0.8

	var mat_banner := StandardMaterial3D.new()
	mat_banner.albedo_color = Color(0.72, 0.22, 0.16) # Toile bordeaux
	mat_banner.roughness = 0.9

	# 1. Chargement et génération des bâtiments depuis lost_heaven_buildings.json
	if FileAccess.file_exists(BUILDINGS_PATH):
		var f := FileAccess.open(BUILDINGS_PATH, FileAccess.READ)
		var raw: Variant = JSON.parse_string(f.get_as_text())
		f.close()
		if raw is Dictionary and (raw as Dictionary).has("buildings"):
			for b_raw in (raw as Dictionary)["buildings"]:
				if b_raw is Dictionary:
					_spawn_swg_building(b_raw as Dictionary, mat_adobe, mat_dome, mat_metal, mat_banner)

	# 2. Rues pavées et allées marchandes
	_spawn_streets_and_paths()

	# 3. Éléments de décor SWG (Props, caisses, étals, lanternes, évaporateurs)
	_spawn_swg_props(mat_adobe, mat_metal, mat_banner)

	# 4. Chargement de l'enceinte / remparts depuis lost_heaven_props.json
	_spawn_perimeter_fence(mat_adobe, mat_metal)


## Crée un bâtiment complet typé SWG selon son type (Cantina, Spatioport, Marché, Clinique, Banque, etc.)
func _spawn_swg_building(b: Dictionary, mat_adobe: Material, mat_dome: Material, mat_metal: Material, mat_banner: Material) -> void:
	var kind := str(b.get("kind", ""))
	if kind == "hunt_yard" or kind == "salvage_scrap" or kind == "city_gate":
		return

	var bx := float(b.get("x", LH_ANCHOR_X))
	var bz := float(b.get("z", LH_ANCHOR_Z))
	# Normalisation de l'emprise des bâtiments à l'échelle humaine (environ 35% de l'empreinte 2D de zone)
	var raw_size := float(b.get("size_m", 60.0))
	var size_m := clampf(raw_size * 0.35, 18.0, 50.0)
	var label := str(b.get("label", b.get("id", "Bâtiment")))
	var bid := str(b.get("id", ""))

	# Conversion en coordonnées relatives au centre de Lost Heaven
	# Core3: +X=Est, +Z=Nord -> Godot 3D: +X=Est, -Z=Nord
	var pos_3d := Vector3(bx - LH_ANCHOR_X, 0.0, -(bz - LH_ANCHOR_Z))
	if pos_3d.length() > 1800.0:
		return

	var b_node := Node3D.new()
	b_node.name = "Building_%s" % bid.replace("poi:", "")
	b_node.position = pos_3d
	_city_root.add_child(b_node)

	# Socle de fondation en dalle surélevée
	var slab := MeshInstance3D.new()
	var slab_box := BoxMesh.new()
	slab_box.size = Vector3(size_m * 0.92, 0.4, size_m * 0.92)
	slab.mesh = slab_box
	slab.position = Vector3(0.0, 0.2, 0.0)
	slab.material_override = mat_metal
	b_node.add_child(slab)

	# Collision physique (évite d'obstruer l'entrée des bâtiments ou l'intérieur du marché)
	if kind != "shops" and kind != "market":
		var body := StaticBody3D.new()
		var col := CollisionShape3D.new()
		var cbox := BoxShape3D.new()
		cbox.size = Vector3(size_m * 0.65, 8.0, size_m * 0.65)
		col.shape = cbox
		col.position = Vector3(0.0, 4.0, 0.0)
		body.add_child(col)
		b_node.add_child(body)

	# Architecture spécifique selon le rôle SWG
	match kind:
		"cantina": # La Perle de Scrapaltai (Cantina de Tatooine avec grande rotonde et dôme)
			var rotunda := MeshInstance3D.new()
			var cyl := CylinderMesh.new()
			cyl.top_radius = size_m * 0.38
			cyl.bottom_radius = size_m * 0.42
			cyl.height = 9.5
			rotunda.mesh = cyl
			rotunda.position = Vector3(0.0, 4.75, 0.0)
			rotunda.material_override = mat_adobe
			b_node.add_child(rotunda)

			var dome := MeshInstance3D.new()
			var sph := SphereMesh.new()
			sph.radius = size_m * 0.34
			sph.height = size_m * 0.30
			dome.mesh = sph
			dome.position = Vector3(0.0, 9.2, 0.0)
			dome.material_override = mat_dome
			b_node.add_child(dome)

			_add_building_door(b_node, Vector3(0.0, 0.0, size_m * 0.42), mat_metal, Color(1.0, 0.75, 0.2))
			_add_building_label(b_node, "✦ CANTINA LA PERLE ✦", Color(1.0, 0.8, 0.3), 13.5)

		"starport_shuttle": # Terminal Spatioport (Grand hangar courbé avec piste d'atterrissage)
			var hangar := MeshInstance3D.new()
			var hbox := BoxMesh.new()
			hbox.size = Vector3(size_m * 0.75, 14.0, size_m * 0.55)
			hangar.mesh = hbox
			hangar.position = Vector3(0.0, 7.0, 0.0)
			hangar.material_override = mat_metal
			b_node.add_child(hangar)

			# Tour de vigie du spatioport
			var c_tower := MeshInstance3D.new()
			var t_cyl := CylinderMesh.new()
			t_cyl.top_radius = 5.0
			t_cyl.bottom_radius = 6.0
			t_cyl.height = 22.0
			c_tower.mesh = t_cyl
			c_tower.position = Vector3(size_m * 0.30, 11.0, -size_m * 0.20)
			c_tower.material_override = mat_adobe
			b_node.add_child(c_tower)

			_add_building_door(b_node, Vector3(0.0, 0.0, size_m * 0.28), mat_metal, Color(0.0, 0.9, 1.0))
			_add_building_label(b_node, "✈ TERMINAL SPATIOPORT ✈", Color(0.0, 0.95, 1.0), 16.5)

		"clinic": # Centre Médical / Dispensaire
			var clinic_body := MeshInstance3D.new()
			var c_box := BoxMesh.new()
			c_box.size = Vector3(size_m * 0.70, 8.5, size_m * 0.70)
			clinic_body.mesh = c_box
			clinic_body.position = Vector3(0.0, 4.25, 0.0)
			clinic_body.material_override = mat_dome
			b_node.add_child(clinic_body)

			_add_building_door(b_node, Vector3(0.0, 0.0, size_m * 0.35), mat_metal, Color(0.0, 0.95, 0.85))
			_add_building_label(b_node, "✚ CENTRE MÉDICAL ✚", Color(0.0, 0.95, 0.85), 11.0)

		"bank": # Banque de Crédits / Coffre blindé
			var bank_body := MeshInstance3D.new()
			var b_box := BoxMesh.new()
			b_box.size = Vector3(size_m * 0.65, 9.0, size_m * 0.65)
			bank_body.mesh = b_box
			bank_body.position = Vector3(0.0, 4.5, 0.0)
			bank_body.material_override = mat_adobe
			b_node.add_child(bank_body)

			_add_building_door(b_node, Vector3(0.0, 0.0, size_m * 0.33), mat_metal, Color(1.0, 0.85, 0.2))
			_add_building_label(b_node, "⬡ BANQUE DE SCRAPALTAI ⬡", Color(1.0, 0.85, 0.2), 11.5)

		"shops", "market": # Grand Marché & Bazar ouvert
			var market_roof := MeshInstance3D.new()
			var m_box := BoxMesh.new()
			m_box.size = Vector3(size_m * 0.75, 1.2, size_m * 0.75)
			market_roof.mesh = m_box
			market_roof.position = Vector3(0.0, 7.5, 0.0)
			market_roof.material_override = mat_banner
			b_node.add_child(market_roof)

			# Piliers d'angle soutenant la toiture
			var corners := [
				Vector3(-size_m * 0.34, 3.75, -size_m * 0.34),
				Vector3(size_m * 0.34, 3.75, -size_m * 0.34),
				Vector3(-size_m * 0.34, 3.75, size_m * 0.34),
				Vector3(size_m * 0.34, 3.75, size_m * 0.34)
			]
			for c_pos in corners:
				var pil := MeshInstance3D.new()
				var pcyl := CylinderMesh.new()
				pcyl.top_radius = 1.0
				pcyl.bottom_radius = 1.0
				pcyl.height = 7.5
				pil.mesh = pcyl
				pil.position = c_pos
				pil.material_override = mat_adobe
				b_node.add_child(pil)

				var p_body := StaticBody3D.new()
				var p_col := CollisionShape3D.new()
				var p_cshape := CylinderShape3D.new()
				p_cshape.radius = 1.0
				p_cshape.height = 7.5
				p_col.shape = p_cshape
				p_body.position = c_pos
				p_body.add_child(p_col)
				b_node.add_child(p_body)

			_add_building_label(b_node, "◈ GRAND MARCHÉ & BAZAR ◈", Color(1.0, 0.65, 0.2), 10.0)

		"town_hall": # Mairie / Quartier Général Administratif
			var th_body := MeshInstance3D.new()
			var th_box := BoxMesh.new()
			th_box.size = Vector3(size_m * 0.72, 11.0, size_m * 0.72)
			th_body.mesh = th_box
			th_body.position = Vector3(0.0, 5.5, 0.0)
			th_body.material_override = mat_adobe
			b_node.add_child(th_body)

			_add_building_door(b_node, Vector3(0.0, 0.0, size_m * 0.36), mat_metal, Color(0.9, 0.5, 0.2))
			_add_building_label(b_node, "🏛 MAIRIE DE LOST HEAVEN 🏛", Color(0.95, 0.8, 0.4), 13.0)

		"trainer_artisan", "workshop": # Atelier Mécanique & Fonderie
			var w_body := MeshInstance3D.new()
			var w_box := BoxMesh.new()
			w_box.size = Vector3(size_m * 0.68, 8.0, size_m * 0.68)
			w_body.mesh = w_box
			w_body.position = Vector3(0.0, 4.0, 0.0)
			w_body.material_override = mat_metal
			b_node.add_child(w_body)

			# Tuyaux de vapeur / cheminée industrielle
			var pipe := MeshInstance3D.new()
			var pcyl := CylinderMesh.new()
			pcyl.top_radius = 1.4
			pcyl.bottom_radius = 1.4
			pcyl.height = 14.0
			pipe.mesh = pcyl
			pipe.position = Vector3(size_m * 0.22, 7.0, -size_m * 0.22)
			pipe.material_override = mat_metal
			b_node.add_child(pipe)

			_add_building_door(b_node, Vector3(0.0, 0.0, size_m * 0.34), mat_metal, Color(1.0, 0.45, 0.1))
			_add_building_label(b_node, "⚙ ATELIER MÉCANIQUE ⚙", Color(1.0, 0.55, 0.2), 10.5)

		_: # Logements & autres blocs d'habitation (Dômes modulaires Mos Eisley)
			var h_body := MeshInstance3D.new()
			var h_box := BoxMesh.new()
			h_box.size = Vector3(size_m * 0.60, 6.5, size_m * 0.60)
			h_body.mesh = h_box
			h_body.position = Vector3(0.0, 3.25, 0.0)
			h_body.material_override = mat_adobe
			b_node.add_child(h_body)

			var h_dome := MeshInstance3D.new()
			var dsph := SphereMesh.new()
			dsph.radius = size_m * 0.24
			dsph.height = size_m * 0.20
			h_dome.mesh = dsph
			h_dome.position = Vector3(0.0, 6.2, 0.0)
			h_dome.material_override = mat_dome
			b_node.add_child(h_dome)

			_add_building_door(b_node, Vector3(0.0, 0.0, size_m * 0.30), mat_metal, Color(0.8, 0.7, 0.5))
			if label != "":
				_add_building_label(b_node, label, Color(0.85, 0.85, 0.85), 8.5)


func _add_building_door(parent: Node3D, pos: Vector3, mat: Material, lamp_col: Color) -> void:
	var door := MeshInstance3D.new()
	var dbox := BoxMesh.new()
	dbox.size = Vector3(3.5, 5.0, 1.2)
	door.mesh = dbox
	door.position = pos
	door.material_override = mat
	parent.add_child(door)

	# Lanterne ambrée / cyan au-dessus de l'entrée
	var lamp := OmniLight3D.new()
	lamp.light_color = lamp_col
	lamp.light_energy = 2.2
	lamp.omni_range = 10.0
	lamp.position = pos + Vector3(0.0, 3.6, 0.8)
	parent.add_child(lamp)


func _add_building_label(parent: Node3D, text: String, col: Color, height_y: float) -> void:
	var lbl := Label3D.new()
	lbl.text = text
	lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lbl.modulate = col
	lbl.outline_modulate = Color(0.02, 0.04, 0.08, 0.9)
	lbl.font_size = 28
	lbl.outline_size = 6
	lbl.position = Vector3(0.0, height_y, 0.0)
	parent.add_child(lbl)


## 5. Construction de l'Enceinte Fortifiée & Remparts de Lost Heaven
func _spawn_perimeter_fence(mat_adobe: Material, mat_metal: Material) -> void:
	# Enceinte Extérieure / Remparts d'Horizon depuis lost_heaven_props.json
	# (Pas de remparts intérieurs artificiels : le centre urbain reste ouvert et accessible comme en 2D)
	if not FileAccess.file_exists(PROPS_PATH):
		return
	var f := FileAccess.open(PROPS_PATH, FileAccess.READ)
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if not raw is Dictionary:
		return

	for item in (raw as Dictionary).get("paths", []):
		if not item is Dictionary:
			continue
		var p: Dictionary = item
		if str(p.get("id", "")) != "path:lh_perimeter_fence":
			continue

		var pts: Array = p.get("points", [])
		if pts.size() < 2:
			continue

		var fence_root := Node3D.new()
		fence_root.name = "PerimeterFence3D"
		_city_root.add_child(fence_root)

		# Indices des segments de portes ouvertes selon gate_exits (Est, Ouest, Sud)
		var gate_indices := [7, 13, 14, 22]

		for i in range(pts.size()):
			var p1: Dictionary = pts[i]
			var p2: Dictionary = pts[(i + 1) % pts.size()] # Bouclage

			var v1 := Vector3(float(p1.get("x", 0.0)) - LH_ANCHOR_X, 0.0, -(float(p1.get("z", 0.0)) - LH_ANCHOR_Z))
			var v2 := Vector3(float(p2.get("x", 0.0)) - LH_ANCHOR_X, 0.0, -(float(p2.get("z", 0.0)) - LH_ANCHOR_Z))

			var mid := (v1 + v2) * 0.5
			var dist := v1.distance_to(v2)
			if dist <= 0.1 or dist > 350.0:
				continue

			var diff_seg := (v2 - v1).normalized()
			var seg_rot_y := atan2(diff_seg.x, diff_seg.z)

			if i in gate_indices:
				# Arche monumentale de porte ouverte (passage entièrement dégagé)
				var gate_arch := Node3D.new()
				gate_arch.position = mid
				gate_arch.rotation.y = seg_rot_y

				# Poteaux latéraux métalliques
				for offset_x in [-4.5, 4.5]:
					var post := MeshInstance3D.new()
					var pcyl := CylinderMesh.new()
					pcyl.top_radius = 1.0
					pcyl.bottom_radius = 1.2
					pcyl.height = 6.0
					post.mesh = pcyl
					post.position = Vector3(offset_x, 3.0, 0.0)
					post.material_override = mat_metal
					gate_arch.add_child(post)

				# Linteau supérieur
				var lintel := MeshInstance3D.new()
				var lbox := BoxMesh.new()
				lbox.size = Vector3(11.0, 1.2, 2.2)
				lintel.mesh = lbox
				lintel.position = Vector3(0.0, 6.0, 0.0)
				lintel.material_override = mat_adobe
				gate_arch.add_child(lintel)

				fence_root.add_child(gate_arch)
				continue

			# Segment de rempart SWG Tatooine (hauteur mesurée de 3.8m, laissant respirer l'horizon)
			var wall_seg := MeshInstance3D.new()
			var w_box := BoxMesh.new()
			w_box.size = Vector3(2.4, 3.8, dist)
			wall_seg.mesh = w_box
			wall_seg.position = Vector3(mid.x, 1.9, mid.z)
			wall_seg.rotation.y = seg_rot_y
			wall_seg.material_override = mat_adobe
			fence_root.add_child(wall_seg)

			# Collision murale physique fine sur le segment de rempart
			var w_body := StaticBody3D.new()
			var w_col := CollisionShape3D.new()
			var w_cbox := BoxShape3D.new()
			w_cbox.size = Vector3(2.4, 4.5, dist)
			w_col.shape = w_cbox
			w_body.position = Vector3(mid.x, 2.25, mid.z)
			w_body.rotation.y = seg_rot_y
			w_body.add_child(w_col)
			fence_root.add_child(w_body)

			# Bastion / Tourelle d'angle cylindrique
			var bastion := MeshInstance3D.new()
			var b_cyl := CylinderMesh.new()
			b_cyl.top_radius = 1.6
			b_cyl.bottom_radius = 2.0
			b_cyl.height = 4.8
			bastion.mesh = b_cyl
			bastion.position = Vector3(v1.x, 2.4, v1.z)
			bastion.material_override = mat_metal
			fence_root.add_child(bastion)
		break


## 5bis. Construction des Rues Pavées et Voies de Circulation
func _spawn_streets_and_paths() -> void:
	if not FileAccess.file_exists(PROPS_PATH):
		return
	var f := FileAccess.open(PROPS_PATH, FileAccess.READ)
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if not raw is Dictionary:
		return

	var streets_root := Node3D.new()
	streets_root.name = "CityStreets3D"
	_city_root.add_child(streets_root)

	var road_mat := StandardMaterial3D.new()
	road_mat.albedo_color = Color(0.68, 0.58, 0.45) # Dalles de grès usées
	road_mat.roughness = 0.95
	road_mat.metallic = 0.05

	for item in (raw as Dictionary).get("paths", []):
		if not item is Dictionary:
			continue
		var p: Dictionary = item
		var pid := str(p.get("id", ""))
		if not ("street" in pid or "door" in pid or "plaza_to" in pid):
			continue

		var pts: Array = p.get("points", [])
		if pts.size() < 2:
			continue

		for i in range(pts.size() - 1):
			var p1: Dictionary = pts[i]
			var p2: Dictionary = pts[i + 1]
			var v1 := Vector3(float(p1.get("x", 0.0)) - LH_ANCHOR_X, 0.03, -(float(p1.get("z", 0.0)) - LH_ANCHOR_Z))
			var v2 := Vector3(float(p2.get("x", 0.0)) - LH_ANCHOR_X, 0.03, -(float(p2.get("z", 0.0)) - LH_ANCHOR_Z))
			var dist := v1.distance_to(v2)
			if dist <= 0.2 or dist > 200.0:
				continue

			var mid := (v1 + v2) * 0.5
			var r_box := BoxMesh.new()
			r_box.size = Vector3(8.0, 0.06, dist)
			var road_mesh := MeshInstance3D.new()
			road_mesh.mesh = r_box
			road_mesh.position = mid
			var diff := (v2 - v1).normalized()
			road_mesh.rotation.y = atan2(diff.x, diff.z)
			road_mesh.material_override = road_mat
			streets_root.add_child(road_mesh)


## 5ter. Éléments de Décor SWG (Caisses, Évapo-condenseurs, Étals, Lanternes)
func _spawn_swg_props(mat_adobe: Material, mat_metal: Material, mat_banner: Material) -> void:
	if not FileAccess.file_exists(PROPS_PATH):
		return
	var f := FileAccess.open(PROPS_PATH, FileAccess.READ)
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if not raw is Dictionary:
		return

	var props_root := Node3D.new()
	props_root.name = "CityProps3D"
	_city_root.add_child(props_root)

	var lamp_mat := StandardMaterial3D.new()
	lamp_mat.albedo_color = Color(0.9, 0.8, 0.4)
	lamp_mat.emission_enabled = true
	lamp_mat.emission = Color(1.0, 0.85, 0.3)

	for item in (raw as Dictionary).get("props", []):
		if not item is Dictionary:
			continue
		var p: Dictionary = item
		var pid := str(p.get("id", ""))
		var kind := str(p.get("kind", ""))
		var px := float(p.get("x", 0.0))
		var pz := float(p.get("z", 0.0))
		var p_pos := Vector3(px - LH_ANCHOR_X, 0.0, -(pz - LH_ANCHOR_Z))

		# Ignorer les props trop lointains (> 400m du centre)
		if p_pos.length() > 400.0 and not ("lh_" in pid):
			continue

		match kind:
			"lamp", "lamp_post":
				var post := MeshInstance3D.new()
				var pcyl := CylinderMesh.new()
				pcyl.top_radius = 0.15
				pcyl.bottom_radius = 0.25
				pcyl.height = 4.5
				post.mesh = pcyl
				post.position = p_pos + Vector3(0.0, 2.25, 0.0)
				post.material_override = mat_metal
				props_root.add_child(post)

				var lantern := MeshInstance3D.new()
				var sph := SphereMesh.new()
				sph.radius = 0.35
				sph.height = 0.5
				lantern.mesh = sph
				lantern.position = p_pos + Vector3(0.0, 4.3, 0.0)
				lantern.material_override = lamp_mat
				props_root.add_child(lantern)

				var light := OmniLight3D.new()
				light.light_color = Color(1.0, 0.85, 0.4)
				light.light_energy = 1.8
				light.omni_range = 10.0
				light.position = p_pos + Vector3(0.0, 4.2, 0.0)
				props_root.add_child(light)

			"crate_stack":
				# Empilement de conteneurs cargo SWG
				for ci in range(3):
					var crate := MeshInstance3D.new()
					var c_mesh := BoxMesh.new()
					c_mesh.size = Vector3(2.2, 1.8, 2.2)
					crate.mesh = c_mesh
					var c_offset := Vector3((ci % 2) * 1.5 - 0.75, 0.9 + (ci / 2) * 1.8, ci * 0.4)
					crate.position = p_pos + c_offset
					crate.material_override = mat_metal
					props_root.add_child(crate)

			"stall":
				# Étal de marchand avec auvent en toile
				var stall := Node3D.new()
				stall.position = p_pos
				var table := MeshInstance3D.new()
				var tbox := BoxMesh.new()
				tbox.size = Vector3(4.0, 1.0, 2.5)
				table.mesh = tbox
				table.position = Vector3(0.0, 0.5, 0.0)
				table.material_override = mat_adobe
				stall.add_child(table)

				var awning := MeshInstance3D.new()
				var abox := BoxMesh.new()
				abox.size = Vector3(4.4, 0.15, 2.8)
				awning.mesh = abox
				awning.position = Vector3(0.0, 2.8, 0.0)
				awning.material_override = mat_banner
				stall.add_child(awning)
				props_root.add_child(stall)

			"moisture_vaporator", _:
				if "vaporator" in pid:
					# Évaporateur d'humidité Tatooine
					var vap := Node3D.new()
					vap.position = p_pos
					var mast := MeshInstance3D.new()
					var mcyl := CylinderMesh.new()
					mcyl.top_radius = 0.2
					mcyl.bottom_radius = 0.5
					mcyl.height = 9.0
					mast.mesh = mcyl
					mast.position = Vector3(0.0, 4.5, 0.0)
					mast.material_override = mat_metal
					vap.add_child(mast)

					# Disques de condensation
					for di in range(3):
						var disc := MeshInstance3D.new()
						var dcyl := CylinderMesh.new()
						dcyl.top_radius = 1.6 - di * 0.3
						dcyl.bottom_radius = 1.6 - di * 0.3
						dcyl.height = 0.2
						disc.mesh = dcyl
						disc.position = Vector3(0.0, 3.5 + di * 2.0, 0.0)
						disc.material_override = mat_adobe
						vap.add_child(disc)
					props_root.add_child(vap)

	# 6 Évaporateurs d'humidité périphériques pour le cachet SWG Tatooine
	var vaporator_coords := [
		Vector3(-45.0, 0.0, -35.0),
		Vector3(55.0, 0.0, -40.0),
		Vector3(-50.0, 0.0, 45.0),
		Vector3(60.0, 0.0, 50.0),
		Vector3(0.0, 0.0, -75.0),
		Vector3(0.0, 0.0, 75.0)
	]
	for vc in vaporator_coords:
		var vap := Node3D.new()
		vap.position = vc
		var mast := MeshInstance3D.new()
		var mcyl := CylinderMesh.new()
		mcyl.top_radius = 0.2
		mcyl.bottom_radius = 0.45
		mcyl.height = 8.5
		mast.mesh = mcyl
		mast.position = Vector3(0.0, 4.25, 0.0)
		mast.material_override = mat_metal
		vap.add_child(mast)
		for di in range(3):
			var disc := MeshInstance3D.new()
			var dcyl := CylinderMesh.new()
			dcyl.top_radius = 1.5 - di * 0.25
			dcyl.bottom_radius = 1.5 - di * 0.25
			dcyl.height = 0.18
			disc.mesh = dcyl
			disc.position = Vector3(0.0, 3.2 + di * 1.8, 0.0)
			disc.material_override = mat_adobe
			vap.add_child(disc)
		props_root.add_child(vap)


## 6. Avatar Joueur 3D (Chargement Direct du Modèle Compagnon.vrm via GLTF)
func _setup_player_avatar() -> void:
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
	_player_node.add_child(_player_mesh)

	# Tentative de chargement du modèle VRM officiel du Compagnon
	var loaded_vrm := false
	if FileAccess.file_exists(VRM_AVATAR_PATH):
		var doc := GLTFDocument.new()
		var state := GLTFState.new()
		if doc.append_from_file(VRM_AVATAR_PATH, state) == OK:
			var scn := doc.generate_scene(state)
			if scn != null:
				_vrm_avatar = scn
				_vrm_avatar.name = "CompagnonModel"
				# Orientation et mise à l'échelle naturelle
				_vrm_avatar.scale = Vector3(1.0, 1.0, 1.0)
				_vrm_avatar.rotation_degrees = Vector3(0.0, 180.0, 0.0)
				_player_mesh.add_child(_vrm_avatar)
				loaded_vrm = true

				# Recherche du squelette et liaison des os principaux pour l'animation procédurale
				_vrm_skeleton = _vrm_avatar.find_child("*Skeleton3D*", true, false) as Skeleton3D
				if _vrm_skeleton != null:
					_bone_l_arm = _vrm_skeleton.find_bone("J_Bip_L_UpperArm")
					_bone_r_arm = _vrm_skeleton.find_bone("J_Bip_R_UpperArm")
					_bone_l_forearm = _vrm_skeleton.find_bone("J_Bip_L_LowerArm")
					_bone_r_forearm = _vrm_skeleton.find_bone("J_Bip_R_LowerArm")
					_bone_l_leg = _vrm_skeleton.find_bone("J_Bip_L_UpperLeg")
					_bone_r_leg = _vrm_skeleton.find_bone("J_Bip_R_UpperLeg")
					_bone_l_knee = _vrm_skeleton.find_bone("J_Bip_L_LowerLeg")
					_bone_r_knee = _vrm_skeleton.find_bone("J_Bip_R_LowerLeg")
					_bone_spine = _vrm_skeleton.find_bone("J_Bip_C_Spine")
					# Poser immédiatement les bras le long du corps au repos (sort de la T-pose)
					_apply_avatar_idle_pose(0.0)

	# Fallback : Châssis humanoïde mécatronique stylisé si le VRM est absent
	if not loaded_vrm:
		_build_stylized_fallback_avatar()

	_world_root.add_child(_player_node)

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


func _build_stylized_fallback_avatar() -> void:
	var armor_mat := StandardMaterial3D.new()
	armor_mat.albedo_color = Color(0.18, 0.28, 0.40)
	armor_mat.metallic = 0.5
	armor_mat.roughness = 0.45

	var torso := MeshInstance3D.new()
	var tbox := BoxMesh.new()
	tbox.size = Vector3(0.65, 0.75, 0.35)
	torso.mesh = tbox
	torso.position = Vector3(0.0, 1.05, 0.0)
	torso.material_override = armor_mat
	_player_mesh.add_child(torso)
	_procedural_avatar_nodes.append(torso)


## 7. Particules de Vent & Poussières de Sable Ambiantes
func _setup_sand_particles() -> void:
	_dust_particles = CPUParticles3D.new()
	_dust_particles.name = "SandDustParticles"
	_dust_particles.amount = 220
	_dust_particles.lifetime = 4.5
	_dust_particles.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	_dust_particles.emission_box_extents = Vector3(45.0, 5.0, 45.0)
	_dust_particles.direction = Vector3(1.0, -0.1, 0.4).normalized()
	_dust_particles.spread = 22.0
	_dust_particles.initial_velocity_min = 3.5
	_dust_particles.initial_velocity_max = 8.5
	_dust_particles.gravity = Vector3(0.0, -0.3, 0.0)

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


## Positionnement du joueur aux coordonnées monde de Lost Heaven (X, Z absolus)
func set_player_world_position(world_x: float, world_z: float) -> void:
	if _player_node == null:
		return
	var lx := world_x - LH_ANCHOR_X
	var lz := -(world_z - LH_ANCHOR_Z)
	_player_node.position = Vector3(lx, 0.0, lz)
	if _camera_rig != null:
		_camera_rig.position = _player_node.position


func get_player_world_position() -> Vector2:
	if _player_node == null:
		return Vector2(LH_ANCHOR_X, LH_ANCHOR_Z)
	return Vector2(LH_ANCHOR_X + _player_node.position.x, LH_ANCHOR_Z - _player_node.position.z)


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
		camera_zoom = 22.0
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


## 8. Boucle Physique : Gravité, Déplacement ZQSD, Sprint, Saut et Animation
func _physics_process(delta: float) -> void:
	if _player_node == null:
		return

	if not _player_node.is_on_floor():
		_player_node.velocity.y -= gravity * delta
	else:
		_player_node.velocity.y = 0.0

	var move_vec := Vector3.ZERO
	var is_sprinting := Input.is_key_pressed(KEY_SHIFT)
	var cur_speed := player_sprint_speed if is_sprinting else player_speed

	var input_dir := Vector2.ZERO
	if Input.is_action_pressed("ui_up") or Input.is_key_pressed(KEY_Z) or Input.is_key_pressed(KEY_W):
		input_dir.y -= 1.0
	if Input.is_action_pressed("ui_down") or Input.is_key_pressed(KEY_S):
		input_dir.y += 1.0
	if Input.is_action_pressed("ui_left") or Input.is_key_pressed(KEY_Q) or Input.is_key_pressed(KEY_A):
		input_dir.x -= 1.0
	if Input.is_action_pressed("ui_right") or Input.is_key_pressed(KEY_D):
		input_dir.x += 1.0

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

	if move_vec != Vector3.ZERO:
		_is_moving = true
		_player_node.velocity.x = move_vec.x * cur_speed
		_player_node.velocity.z = move_vec.z * cur_speed

		var target_angle := atan2(move_vec.x, move_vec.z)
		_player_mesh.rotation.y = lerp_angle(_player_mesh.rotation.y, target_angle, delta * 14.0)

		_walk_cycle += delta * (14.0 if is_sprinting else 9.5)

		# Animation dynamique de l'avatar du Compagnon (foulée et rebond)
		if _vrm_avatar != null:
			_vrm_avatar.position.y = abs(sin(_walk_cycle * 2.0)) * 0.05
			_vrm_avatar.rotation.z = sin(_walk_cycle) * 0.035
			_apply_avatar_walk_pose(_walk_cycle)
	else:
		_is_moving = false
		_idle_timer += delta
		_player_node.velocity.x = move_toward(_player_node.velocity.x, 0.0, cur_speed * delta * 8.0)
		_player_node.velocity.z = move_toward(_player_node.velocity.z, 0.0, cur_speed * delta * 8.0)

		if _vrm_avatar != null:
			_vrm_avatar.position.y = lerp(_vrm_avatar.position.y, sin(_idle_timer * 1.6) * 0.012, delta * 6.0)
			_vrm_avatar.rotation.z = lerp(_vrm_avatar.rotation.z, 0.0, delta * 8.0)
			_apply_avatar_idle_pose(_idle_timer)

	_player_node.move_and_slide()
	player_moved_3d.emit(_player_node.position)
	_camera_rig.position = _camera_rig.position.lerp(_player_node.position, delta * 12.0)

	if _dust_particles != null:
		_dust_particles.position = _player_node.position


## Pose Procédurale au Repos (Bras le long du corps, respiration naturelle — Fin de la T-Pose)
func _apply_avatar_idle_pose(time: float) -> void:
	if _vrm_skeleton == null:
		return
	var breathe := sin(time * 1.8) * 0.025
	# Bras gauche et droit abaissés le long du corps (~72° autour de Z)
	if _bone_l_arm >= 0:
		var q_l := Quaternion(Vector3(0, 0, 1), -deg_to_rad(70.0 + breathe * 40.0)) * Quaternion(Vector3(1, 0, 0), deg_to_rad(5.0))
		_vrm_skeleton.set_bone_pose_rotation(_bone_l_arm, q_l)
	if _bone_r_arm >= 0:
		var q_r := Quaternion(Vector3(0, 0, 1), deg_to_rad(70.0 + breathe * 40.0)) * Quaternion(Vector3(1, 0, 0), deg_to_rad(5.0))
		_vrm_skeleton.set_bone_pose_rotation(_bone_r_arm, q_r)
	# Avant-bras légèrement fléchis
	if _bone_l_forearm >= 0:
		_vrm_skeleton.set_bone_pose_rotation(_bone_l_forearm, Quaternion(Vector3(1, 0, 0), deg_to_rad(12.0)))
	if _bone_r_forearm >= 0:
		_vrm_skeleton.set_bone_pose_rotation(_bone_r_forearm, Quaternion(Vector3(1, 0, 0), deg_to_rad(12.0)))
	# Jambes droites
	if _bone_l_leg >= 0:
		_vrm_skeleton.set_bone_pose_rotation(_bone_l_leg, Quaternion.IDENTITY)
	if _bone_r_leg >= 0:
		_vrm_skeleton.set_bone_pose_rotation(_bone_r_leg, Quaternion.IDENTITY)
	if _bone_l_knee >= 0:
		_vrm_skeleton.set_bone_pose_rotation(_bone_l_knee, Quaternion.IDENTITY)
	if _bone_r_knee >= 0:
		_vrm_skeleton.set_bone_pose_rotation(_bone_r_knee, Quaternion.IDENTITY)
	# Légère inclinaison colonne vertébrale
	if _bone_spine >= 0:
		_vrm_skeleton.set_bone_pose_rotation(_bone_spine, Quaternion(Vector3(1, 0, 0), deg_to_rad(breathe * 15.0)))


## Pose Procédurale de Course / Marche (Balancement des bras et des jambes)
func _apply_avatar_walk_pose(cycle: float) -> void:
	if _vrm_skeleton == null:
		return
	var arm_swing := sin(cycle) * 0.45
	var leg_swing := sin(cycle) * 0.55

	# Bras en opposition de phase avec les jambes
	if _bone_l_arm >= 0:
		var q_l := Quaternion(Vector3(0, 0, 1), -deg_to_rad(68.0)) * Quaternion(Vector3(1, 0, 0), arm_swing)
		_vrm_skeleton.set_bone_pose_rotation(_bone_l_arm, q_l)
	if _bone_r_arm >= 0:
		var q_r := Quaternion(Vector3(0, 0, 1), deg_to_rad(68.0)) * Quaternion(Vector3(1, 0, 0), -arm_swing)
		_vrm_skeleton.set_bone_pose_rotation(_bone_r_arm, q_r)

	# Avant-bras fléchis pendant la course
	if _bone_l_forearm >= 0:
		_vrm_skeleton.set_bone_pose_rotation(_bone_l_forearm, Quaternion(Vector3(1, 0, 0), deg_to_rad(25.0) + abs(arm_swing) * 0.2))
	if _bone_r_forearm >= 0:
		_vrm_skeleton.set_bone_pose_rotation(_bone_r_forearm, Quaternion(Vector3(1, 0, 0), deg_to_rad(25.0) + abs(arm_swing) * 0.2))

	# Jambes alternées
	if _bone_l_leg >= 0:
		_vrm_skeleton.set_bone_pose_rotation(_bone_l_leg, Quaternion(Vector3(1, 0, 0), -leg_swing))
	if _bone_r_leg >= 0:
		_vrm_skeleton.set_bone_pose_rotation(_bone_r_leg, Quaternion(Vector3(1, 0, 0), leg_swing))

	# Genoux pliés vers l'arrière
	if _bone_l_knee >= 0:
		var k_l := maxf(0.0, leg_swing) * 0.65
		_vrm_skeleton.set_bone_pose_rotation(_bone_l_knee, Quaternion(Vector3(1, 0, 0), k_l))
	if _bone_r_knee >= 0:
		var k_r := maxf(0.0, -leg_swing) * 0.65
		_vrm_skeleton.set_bone_pose_rotation(_bone_r_knee, Quaternion(Vector3(1, 0, 0), k_r))

	if _bone_spine >= 0:
		_vrm_skeleton.set_bone_pose_rotation(_bone_spine, Quaternion(Vector3(1, 0, 0), deg_to_rad(6.0)))


## 9. Contrôles Souris & Clavier : Clic Gauche Orientation/Marche, Clic Droit Menu Radial, Zoom Molette
func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_LEFT:
			if mb.pressed:
				_is_left_down = true
				_left_down_pos = mb.position
				_left_dragged = false
			else:
				_is_left_down = false
				if not _left_dragged:
					# Clic gauche franc (< 6px de mouvement) : déplacement vers le point cliqué
					_handle_left_click(mb.position)
		elif mb.button_index == MOUSE_BUTTON_RIGHT:
			if mb.pressed:
				_is_right_down = true
				_right_down_pos = mb.position
				_right_dragged = false
			else:
				_is_right_down = false
				if not _right_dragged:
					# Clic droit franc (< 6px de mouvement) : ouverture du menu radial SWG
					_handle_right_click(mb.position)
		elif mb.button_index == MOUSE_BUTTON_WHEEL_UP and mb.pressed:
			_zoom_camera(-1.0)
		elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN and mb.pressed:
			_zoom_camera(1.0)
	elif event is InputEventMouseMotion:
		var mm := event as InputEventMouseMotion
		var delta_rot: Vector2 = mm.relative
		if _is_left_down:
			if (mm.position - _left_down_pos).length() > 6.0:
				_left_dragged = true
			# Clic gauche glissé : Orbite de caméra libre (Free-look sans faire tourner le corps du personnage)
			camera_yaw -= delta_rot.x * 0.32
			camera_pitch = clampf(camera_pitch - delta_rot.y * 0.25, -78.0, 42.0)
			_update_camera_settings()
		elif _is_right_down:
			if (mm.position - _right_down_pos).length() > 6.0:
				_right_dragged = true
			# Clic droit glissé : Orientation du personnage + caméra dans la direction de visée
			camera_yaw -= delta_rot.x * 0.32
			camera_pitch = clampf(camera_pitch - delta_rot.y * 0.25, -78.0, 42.0)
			_update_camera_settings()
			if _player_mesh != null:
				var look_yaw := deg_to_rad(camera_yaw + 180.0)
				_player_mesh.rotation.y = look_yaw


func _zoom_camera(dir: float) -> void:
	var step := 0.6 if current_camera_mode == CameraMode.THIRD_PERSON else 2.5
	camera_zoom += dir * step
	if current_camera_mode == CameraMode.THIRD_PERSON:
		camera_zoom = clampf(camera_zoom, MIN_ZOOM_3RD, MAX_ZOOM_3RD)
	else:
		camera_zoom = clampf(camera_zoom, MIN_ZOOM_ISO, MAX_ZOOM_ISO)
	_update_camera_settings()


func _handle_left_click(screen_pos: Vector2) -> void:
	if _camera == null:
		return
	var from := _camera.project_ray_origin(screen_pos)
	var dir := _camera.project_ray_normal(screen_pos)

	if abs(dir.y) > 0.0001:
		var t := -from.y / dir.y
		if t > 0.0:
			var hit_pos := from + dir * t
			click_target_pos = hit_pos
			is_click_moving = true
			if _target_marker != null:
				_target_marker.position = Vector3(hit_pos.x, 0.08, hit_pos.z)
				_target_marker.visible = true
			# Aligner immédiatement l'orientation vers le point de marche
			if _player_mesh != null and _player_node != null:
				var to_pt := hit_pos - _player_node.position
				to_pt.y = 0.0
				if to_pt.length() > 0.2:
					_player_mesh.rotation.y = atan2(to_pt.x, to_pt.z)
			terrain_clicked_3d.emit(hit_pos)


func _handle_right_click(screen_pos: Vector2) -> void:
	if _camera == null:
		return
	var from := _camera.project_ray_origin(screen_pos)
	var dir := _camera.project_ray_normal(screen_pos)
	var hit_pos := Vector3.ZERO
	if abs(dir.y) > 0.0001:
		var t := -from.y / dir.y
		if t > 0.0:
			hit_pos = from + dir * t
	# Émission vers main.gd pour ouvrir le menu radial SWG
	terrain_right_clicked_3d.emit(screen_pos, hit_pos)


## 10. Synchronisation Dynamique des Entités Monde (PNJ, Joueurs, Drones, Bêtes) en 3D
func sync_entities_from_manager(entity_mgr: Node, local_possessed_id: int) -> void:
	if entity_mgr == null or not entity_mgr.has_method("get_all_entities"):
		return
	if _entities_root == null:
		return

	var all_ents: Array = entity_mgr.get_all_entities()
	var current_ids: Dictionary = {}

	for e_node in all_ents:
		if e_node == null or not is_instance_valid(e_node):
			continue
		var oid: int = int(e_node.get("object_id"))
		if oid <= 0 or oid == local_possessed_id:
			continue # Ignorer son propre avatar local déjà géré par _player_node

		current_ids[oid] = true
		var world_pos: Vector3 = e_node.get_world_pos_3d() if e_node.has_method("get_world_pos_3d") else (e_node.get("core3_pos") if e_node.get("core3_pos") != null else Vector3.ZERO)
		var pos_3d := Vector3(world_pos.x - LH_ANCHOR_X, 0.0, -(world_pos.z - LH_ANCHOR_Z))
		var kind: String = str(e_node.get("kind"))
		var d_name: String = str(e_node.get_display_name()) if e_node.has_method("get_display_name") else str(e_node.get("label_text"))

		if not _active_entities_3d.has(oid):
			var ent_3d := _create_entity_3d_node(oid, kind, d_name, pos_3d)
			_entities_root.add_child(ent_3d)
			_active_entities_3d[oid] = ent_3d
		else:
			var ent_node: Node3D = _active_entities_3d[oid]
			if ent_node != null and is_instance_valid(ent_node):
				ent_node.position = ent_node.position.lerp(pos_3d, 0.25)

	# Nettoyage des entités disparues
	var to_remove: Array = []
	for oid in _active_entities_3d.keys():
		if not current_ids.has(oid):
			to_remove.append(oid)
	for oid in to_remove:
		var n: Node = _active_entities_3d[oid]
		if n != null and is_instance_valid(n):
			n.queue_free()
		_active_entities_3d.erase(oid)


func _create_entity_3d_node(oid: int, kind: String, label: String, pos_3d: Vector3) -> Node3D:
	var root := Node3D.new()
	root.name = "Ent3D_%d" % oid
	root.position = pos_3d

	var body := MeshInstance3D.new()
	var col_mat := StandardMaterial3D.new()

	if kind == "player":
		# Joueur / Bot humanoïde (bleu cyber)
		var cap := CapsuleMesh.new()
		cap.radius = 0.4
		cap.height = 1.75
		body.mesh = cap
		body.position = Vector3(0.0, 0.88, 0.0)
		col_mat.albedo_color = Color(0.2, 0.55, 1.0)
		col_mat.roughness = 0.4
	elif kind == "npc":
		# PNJ citadin / marchand / cantina (ambre/or)
		var cap := CapsuleMesh.new()
		cap.radius = 0.42
		cap.height = 1.8
		body.mesh = cap
		body.position = Vector3(0.0, 0.9, 0.0)
		col_mat.albedo_color = Color(1.0, 0.65, 0.15)
		col_mat.roughness = 0.5
	else:
		# Objet / Créature / Véhicule
		var box := BoxMesh.new()
		box.size = Vector3(0.9, 0.9, 0.9)
		body.mesh = box
		body.position = Vector3(0.0, 0.45, 0.0)
		col_mat.albedo_color = Color(0.5, 0.5, 0.55)
		col_mat.roughness = 0.7

	body.material_override = col_mat
	root.add_child(body)

	# Label 3D au-dessus de la tête
	if label != "":
		var lbl := Label3D.new()
		lbl.text = label
		lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		lbl.no_depth_test = true
		lbl.font_size = 22
		lbl.outline_size = 5
		lbl.outline_modulate = Color(0.05, 0.05, 0.05, 0.95)
		lbl.position = Vector3(0.0, 2.15, 0.0)
		if kind == "player":
			lbl.modulate = Color(0.4, 0.85, 1.0)
		elif kind == "npc":
			lbl.modulate = Color(1.0, 0.82, 0.35)
		else:
			lbl.modulate = Color(0.85, 0.85, 0.85)
		root.add_child(lbl)

	return root


func get_entity_3d_count() -> int:
	return _active_entities_3d.size()
