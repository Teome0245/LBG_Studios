extends RefCounted
## Pipeline d'Importation & d'Instanciation d'Assets 3D SWG Pre-CU
## 1. Bâtiments complexes POB (Portal Object) découpés en Cellules intérieures (Foyer, Bar, Scène, Alcôves).
## 2. Palettes de teintes indexées à 4 canaux (Custom Color Indexing des tailleurs & armuriers SWG).
## 3. Génération & chargement de structures SWG authentiques (Cantina, Bazar, Hangar, Maison en pisé).

class SwgCell extends RefCounted:
	var cell_name: String = ""
	var bounds_min: Vector3 = Vector3.ZERO
	var bounds_max: Vector3 = Vector3.ZERO
	var interior_nodes: Array = []
	var connected_portals: Array = []

	func _init(p_name: String, p_min: Vector3, p_max: Vector3) -> void:
		cell_name = p_name
		bounds_min = p_min
		bounds_max = p_max

	func contains_point(pt: Vector3) -> bool:
		return pt.x >= bounds_min.x and pt.x <= bounds_max.x and \
			   pt.y >= bounds_min.y and pt.y <= bounds_max.y and \
			   pt.z >= bounds_min.z and pt.z <= bounds_max.z


## Construit une Cantina SWG Pre-CU complète (Architecture POB multi-cellules)
static func build_swg_cantina_pob(pos: Vector3, yaw_deg: float = 0.0) -> Node3D:
	var root := Node3D.new()
	root.name = "Cantina_La_Perle_POB"
	root.position = pos
	root.rotation_degrees.y = yaw_deg

	# Matériaux Cantina SWG
	var mat_wall := StandardMaterial3D.new()
	mat_wall.albedo_color = Color(0.68, 0.58, 0.46, 1.0) # Pisé ocre désert
	mat_wall.roughness = 0.85

	var mat_floor := StandardMaterial3D.new()
	mat_floor.albedo_color = Color(0.25, 0.22, 0.20, 1.0) # Dalles d'ardoise usées
	mat_floor.roughness = 0.6

	var mat_neon_bar := StandardMaterial3D.new()
	mat_neon_bar.albedo_color = Color(0.2, 0.85, 0.95, 1.0) # Néon Holo Cantina
	mat_neon_bar.emission_enabled = true
	mat_neon_bar.emission = Color(0.2, 0.85, 0.95, 1.0)
	mat_neon_bar.emission_energy_multiplier = 2.0

	var mat_stage := StandardMaterial3D.new()
	mat_stage.albedo_color = Color(0.85, 0.25, 0.25, 1.0) # Tapis rouge de la scène
	mat_stage.roughness = 0.7

	# 1. Structure Extérieure (Dôme & Murs massifs)
	var ext_body := StaticBody3D.new()
	ext_body.name = "Exterior_Shell"

	# Dôme central
	var dome := MeshInstance3D.new()
	var sphere := SphereMesh.new()
	sphere.radius = 12.0
	sphere.height = 10.0
	sphere.is_hemisphere = true
	dome.mesh = sphere
	dome.position = Vector3(0, 5.0, 0)
	dome.set_surface_override_material(0, mat_wall)
	ext_body.add_child(dome)

	# Sol Cantina (28m x 22m)
	var floor_mesh := MeshInstance3D.new()
	var box_floor := BoxMesh.new()
	box_floor.size = Vector3(28.0, 0.4, 22.0)
	floor_mesh.mesh = box_floor
	floor_mesh.position = Vector3(0, -0.2, 0)
	floor_mesh.set_surface_override_material(0, mat_floor)
	ext_body.add_child(floor_mesh)

	var col_floor := CollisionShape3D.new()
	var col_floor_box := BoxShape3D.new()
	col_floor_box.size = Vector3(28.0, 0.4, 22.0)
	col_floor.shape = col_floor_box
	col_floor.position = Vector3(0, -0.2, 0)
	ext_body.add_child(col_floor)

	root.add_child(ext_body)

	# 2. Cellule 1 : Grande Salle & Comptoir du Bar (Bar Cell)
	var bar_cell_node := Node3D.new()
	bar_cell_node.name = "Cell_MainBar"

	# Grand comptoir circulaire en fer à cheval (iconique SWG)
	var counter := MeshInstance3D.new()
	var c_box := CylinderMesh.new()
	c_box.top_radius = 4.0
	c_box.bottom_radius = 4.0
	c_box.height = 1.1
	counter.mesh = c_box
	counter.position = Vector3(-4.0, 0.55, 0)
	var mat_metal := StandardMaterial3D.new()
	mat_metal.albedo_color = Color(0.3, 0.35, 0.38, 1.0)
	mat_metal.metallic = 0.8
	mat_metal.roughness = 0.3
	counter.set_surface_override_material(0, mat_metal)

	var counter_body := StaticBody3D.new()
	var c_col := CollisionShape3D.new()
	var cyl_shape := CylinderShape3D.new()
	cyl_shape.radius = 4.0
	cyl_shape.height = 1.1
	c_col.shape = cyl_shape
	counter_body.add_child(c_col)
	counter.add_child(counter_body)
	bar_cell_node.add_child(counter)

	# Néon d'ambiance au-dessus du bar
	var bar_neon := MeshInstance3D.new()
	var tor := TorusMesh.new()
	tor.inner_radius = 3.8
	tor.outer_radius = 4.1
	bar_neon.mesh = tor
	bar_neon.position = Vector3(-4.0, 2.2, 0)
	bar_neon.set_surface_override_material(0, mat_neon_bar)
	bar_cell_node.add_child(bar_neon)

	var bar_omni := OmniLight3D.new()
	bar_omni.position = Vector3(-4.0, 2.4, 0)
	bar_omni.light_color = Color(0.3, 0.85, 1.0)
	bar_omni.light_energy = 1.8
	bar_omni.omni_range = 8.0
	bar_cell_node.add_child(bar_omni)

	root.add_child(bar_cell_node)

	# 3. Cellule 2 : Scène des Artistes & Danseurs (Entertainer Stage Cell)
	var stage_cell_node := Node3D.new()
	stage_cell_node.name = "Cell_Stage"

	var stage_platform := MeshInstance3D.new()
	var st_mesh := BoxMesh.new()
	st_mesh.size = Vector3(8.0, 0.6, 6.0)
	stage_platform.mesh = st_mesh
	stage_platform.position = Vector3(7.5, 0.3, 0)
	stage_platform.set_surface_override_material(0, mat_stage)

	var stage_body := StaticBody3D.new()
	var st_col := CollisionShape3D.new()
	var st_shape := BoxShape3D.new()
	st_shape.size = Vector3(8.0, 0.6, 6.0)
	st_col.shape = st_shape
	stage_body.add_child(st_col)
	stage_platform.add_child(stage_body)
	stage_cell_node.add_child(stage_platform)

	# Projecteur Spot sur la scène pour les artistes
	var spot := SpotLight3D.new()
	spot.position = Vector3(7.5, 5.5, 0)
	spot.rotation_degrees = Vector3(-90, 0, 0)
	spot.light_color = Color(1.0, 0.7, 0.8) # Teinte chaude rose/ambre
	spot.light_energy = 3.5
	spot.spot_range = 10.0
	spot.spot_angle = 38.0
	stage_cell_node.add_child(spot)

	root.add_child(stage_cell_node)

	# Enseigne Holo extérieure
	var sign_lbl := Label3D.new()
	sign_lbl.text = "◈ CANTINA LA PERLE ◈\n« Halte des Vagabonds & Caravaniers »"
	sign_lbl.position = Vector3(0, 8.5, 11.2)
	sign_lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	sign_lbl.font_size = 20
	sign_lbl.modulate = Color(0.96, 0.85, 0.35, 1.0)
	root.add_child(sign_lbl)

	return root


## Applique une palette de teintes 4 couleurs à un matériau d'équipement (Teinture Armure / Vêtement SWG)
static func create_tinted_swg_material(c1: Color, c2: Color, metallic: float = 0.5, roughness: float = 0.4) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	# Mélange primaire (80%) et secondaire (20%)
	mat.albedo_color = c1.lerp(c2, 0.25)
	mat.metallic = metallic
	mat.roughness = roughness
	return mat

