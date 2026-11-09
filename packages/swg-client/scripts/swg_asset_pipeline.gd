extends RefCounted
const _SwgVrmAnimatorScript := preload("res://scripts/swg_vrm_animator.gd")
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

	# Grand comptoir en U authentique de Cantina SWG (Espace intérieur dégagé pour le barman)
	var mat_metal := StandardMaterial3D.new()
	mat_metal.albedo_color = Color(0.28, 0.32, 0.36, 1.0)
	mat_metal.metallic = 0.85
	mat_metal.roughness = 0.25

	# 1. Pan frontal (face aux clients au Sud)
	var counter_front := MeshInstance3D.new()
	var box_front := BoxMesh.new()
	box_front.size = Vector3(5.6, 1.1, 0.7)
	counter_front.mesh = box_front
	counter_front.position = Vector3(-4.0, 0.55, 1.8)
	counter_front.set_surface_override_material(0, mat_metal)
	var sb_f := StaticBody3D.new()
	var col_f := CollisionShape3D.new()
	var box_shape_f := BoxShape3D.new()
	box_shape_f.size = Vector3(5.6, 1.1, 0.7)
	col_f.shape = box_shape_f
	sb_f.add_child(col_f)
	counter_front.add_child(sb_f)
	bar_cell_node.add_child(counter_front)

	# 2. Aile gauche (Ouest)
	var counter_left := MeshInstance3D.new()
	var box_l := BoxMesh.new()
	box_l.size = Vector3(0.7, 1.1, 3.2)
	counter_left.mesh = box_l
	counter_left.position = Vector3(-6.45, 0.55, 0.2)
	counter_left.set_surface_override_material(0, mat_metal)
	var sb_l := StaticBody3D.new()
	var col_l := CollisionShape3D.new()
	var box_shape_l := BoxShape3D.new()
	box_shape_l.size = Vector3(0.7, 1.1, 3.2)
	col_l.shape = box_shape_l
	sb_l.add_child(col_l)
	counter_left.add_child(sb_l)
	bar_cell_node.add_child(counter_left)

	# 3. Aile droite (Est)
	var counter_right := MeshInstance3D.new()
	var box_r := BoxMesh.new()
	box_r.size = Vector3(0.7, 1.1, 3.2)
	counter_right.mesh = box_r
	counter_right.position = Vector3(-1.55, 0.55, 0.2)
	counter_right.set_surface_override_material(0, mat_metal)
	var sb_r := StaticBody3D.new()
	var col_r := CollisionShape3D.new()
	var box_shape_r := BoxShape3D.new()
	box_shape_r.size = Vector3(0.7, 1.1, 3.2)
	col_r.shape = box_shape_r
	sb_r.add_child(col_r)
	counter_right.add_child(sb_r)
	bar_cell_node.add_child(counter_right)

	# 4. Étagère arrière-bar & Distributeurs de boissons de Jax Moro
	var backbar := MeshInstance3D.new()
	var bb_box := BoxMesh.new()
	bb_box.size = Vector3(5.2, 2.4, 0.6)
	backbar.mesh = bb_box
	backbar.position = Vector3(-4.0, 1.2, -2.4)
	backbar.set_surface_override_material(0, mat_metal)
	var sb_bb := StaticBody3D.new()
	var col_bb := CollisionShape3D.new()
	var box_shape_bb := BoxShape3D.new()
	box_shape_bb.size = Vector3(5.2, 2.4, 0.6)
	col_bb.shape = box_shape_bb
	sb_bb.add_child(col_bb)
	backbar.add_child(sb_bb)
	bar_cell_node.add_child(backbar)

	# Bouteilles & Carafes de lait bleu luminescentes sur l'étagère
	for bx in [-1.8, -0.6, 0.6, 1.8]:
		var bottle := MeshInstance3D.new()
		var bot_cyl := CylinderMesh.new()
		bot_cyl.top_radius = 0.08
		bot_cyl.bottom_radius = 0.12
		bot_cyl.height = 0.55
		bottle.mesh = bot_cyl
		bottle.position = Vector3(-4.0 + bx, 1.8, -2.0)
		var mat_bot := StandardMaterial3D.new()
		mat_bot.albedo_color = Color(0.2, 0.85, 1.0, 0.9)
		mat_bot.emission_enabled = true
		mat_bot.emission = Color(0.2, 0.85, 1.0)
		mat_bot.emission_energy_multiplier = 1.5
		bottle.set_surface_override_material(0, mat_bot)
		bar_cell_node.add_child(bottle)

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


# ==============================================================================
#  BÂTIMENTS PUBLICS SWG PRE-CU (Spatioport, Clinique, Mairie, Habitations)
# ==============================================================================

## 1. Spatioport de Lost Heaven (Shuttleport SWG) avec piste d'atterrissage et Navette Spatiale posée
static func build_swg_shuttleport(pos: Vector3, yaw_deg: float = 0.0) -> Node3D:
	var root := Node3D.new()
	root.name = "Shuttleport_Lost_Heaven"
	root.position = pos
	root.rotation_degrees.y = yaw_deg

	# Matériaux
	var mat_pad := StandardMaterial3D.new()
	mat_pad.albedo_color = Color(0.22, 0.24, 0.26, 1.0)
	mat_pad.roughness = 0.7
	mat_pad.metallic = 0.4

	var mat_stripes := StandardMaterial3D.new()
	mat_stripes.albedo_color = Color(0.95, 0.82, 0.15, 1.0)
	mat_stripes.emission_enabled = true
	mat_stripes.emission = Color(0.95, 0.82, 0.15, 1.0)
	mat_stripes.emission_energy_multiplier = 0.6

	var mat_tower := StandardMaterial3D.new()
	mat_tower.albedo_color = Color(0.65, 0.58, 0.50, 1.0)
	mat_tower.roughness = 0.85

	var mat_glass := StandardMaterial3D.new()
	mat_glass.albedo_color = Color(0.15, 0.45, 0.65, 0.8)
	mat_glass.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat_glass.roughness = 0.1
	mat_glass.metallic = 0.9

	# A. Piste d'atterrissage surélevée hexagonale/octogonale (24m x 24m)
	var pad_sb := StaticBody3D.new()
	var pad_mesh := MeshInstance3D.new()
	var pad_cyl := CylinderMesh.new()
	pad_cyl.top_radius = 14.0
	pad_cyl.bottom_radius = 15.0
	pad_cyl.height = 0.8
	pad_mesh.mesh = pad_cyl
	pad_mesh.position = Vector3(0, 0.4, 0)
	pad_mesh.set_surface_override_material(0, mat_pad)
	pad_sb.add_child(pad_mesh)

	var pad_col := CollisionShape3D.new()
	var pad_cshape := CylinderShape3D.new()
	pad_cshape.radius = 14.0
	pad_cshape.height = 0.8
	pad_col.shape = pad_cshape
	pad_col.position = Vector3(0, 0.4, 0)
	pad_sb.add_child(pad_col)
	root.add_child(pad_sb)

	# Liseré circulaire d'atterrissage
	var ring_mesh := MeshInstance3D.new()
	var ring_torus := TorusMesh.new()
	ring_torus.inner_radius = 11.5
	ring_torus.outer_radius = 12.0
	ring_mesh.mesh = ring_torus
	ring_mesh.position = Vector3(0, 0.82, 0)
	ring_mesh.set_surface_override_material(0, mat_stripes)
	root.add_child(ring_mesh)

	# Balises lumineuses de piste (Vert / Rouge clignotant aux 4 coins)
	for i in range(4):
		var angle: float = i * PI * 0.5 + PI * 0.25
		var bx: float = cos(angle) * 12.5
		var bz: float = sin(angle) * 12.5
		var beacon := OmniLight3D.new()
		beacon.position = Vector3(bx, 1.2, bz)
		beacon.light_color = Color(0.1, 0.9, 0.3) if i % 2 == 0 else Color(0.9, 0.2, 0.1)
		beacon.light_energy = 1.5
		beacon.omni_range = 5.0
		root.add_child(beacon)

	# B. Tour de Contrôle Spatiale (Terminal de Transit)
	var tower_sb := StaticBody3D.new()
	tower_sb.position = Vector3(-18.0, 0, 0)

	var t_base := MeshInstance3D.new()
	var t_box := BoxMesh.new()
	t_box.size = Vector3(10.0, 7.0, 10.0)
	t_base.mesh = t_box
	t_base.position = Vector3(0, 3.5, 0)
	t_base.set_surface_override_material(0, mat_tower)
	tower_sb.add_child(t_base)

	var t_glass_mesh := MeshInstance3D.new()
	var t_glass_box := CylinderMesh.new()
	t_glass_box.top_radius = 5.5
	t_glass_box.bottom_radius = 4.8
	t_glass_box.height = 3.2
	t_glass_mesh.mesh = t_glass_box
	t_glass_mesh.position = Vector3(0, 8.6, 0)
	t_glass_mesh.set_surface_override_material(0, mat_glass)
	tower_sb.add_child(t_glass_mesh)

	# Antenne Radar Parabolique au sommet de la tour
	var radar_dish := MeshInstance3D.new()
	var dish_mesh := SphereMesh.new()
	dish_mesh.radius = 2.0
	dish_mesh.height = 1.0
	dish_mesh.is_hemisphere = true
	radar_dish.mesh = dish_mesh
	radar_dish.position = Vector3(0, 11.2, 0)
	radar_dish.rotation_degrees = Vector3(-35, 45, 0)
	var mat_metal_dish := StandardMaterial3D.new()
	mat_metal_dish.albedo_color = Color(0.8, 0.85, 0.9)
	mat_metal_dish.metallic = 0.95
	radar_dish.set_surface_override_material(0, mat_metal_dish)
	tower_sb.add_child(radar_dish)

	var t_col := CollisionShape3D.new()
	var t_col_box := BoxShape3D.new()
	t_col_box.size = Vector3(10.0, 10.0, 10.0)
	t_col.shape = t_col_box
	t_col.position = Vector3(0, 5.0, 0)
	tower_sb.add_child(t_col)
	root.add_child(tower_sb)

	# C. Navette Spatiale SWG (Shuttle Lambda-Style posée au centre de la piste)
	var shuttle := Node3D.new()
	shuttle.name = "SWG_Shuttle_Craft"
	shuttle.position = Vector3(0, 0.8, 0)

	var mat_shuttle := StandardMaterial3D.new()
	mat_shuttle.albedo_color = Color(0.88, 0.90, 0.92, 1.0)
	mat_shuttle.roughness = 0.4
	mat_shuttle.metallic = 0.5

	var mat_engine := StandardMaterial3D.new()
	mat_engine.albedo_color = Color(0.2, 0.6, 1.0)
	mat_engine.emission_enabled = true
	mat_engine.emission = Color(0.2, 0.7, 1.0)
	mat_engine.emission_energy_multiplier = 3.0

	# Fuselage principal
	var fuselage := MeshInstance3D.new()
	var f_box := BoxMesh.new()
	f_box.size = Vector3(5.5, 3.2, 12.0)
	fuselage.mesh = f_box
	fuselage.position = Vector3(0, 2.8, 0)
	fuselage.set_surface_override_material(0, mat_shuttle)
	shuttle.add_child(fuselage)

	# Cockpit biseauté avant
	var nose := MeshInstance3D.new()
	var n_prism := PrismMesh.new()
	n_prism.size = Vector3(4.8, 2.4, 4.0)
	nose.mesh = n_prism
	nose.position = Vector3(0, 2.4, -7.5)
	nose.rotation_degrees = Vector3(-90, 0, 0)
	nose.set_surface_override_material(0, mat_shuttle)
	shuttle.add_child(nose)

	# Grande Aile Dorsale Verticale (Iconique SWG Lambda / Shuttle)
	var dorsal_fin := MeshInstance3D.new()
	var d_prism := PrismMesh.new()
	d_prism.size = Vector3(0.5, 8.5, 9.0)
	dorsal_fin.mesh = d_prism
	dorsal_fin.position = Vector3(0, 8.6, -0.5)
	dorsal_fin.rotation_degrees = Vector3(0, 0, 0)
	dorsal_fin.set_surface_override_material(0, mat_shuttle)
	shuttle.add_child(dorsal_fin)

	# Aile latérale Gauche (repliée vers le haut à 45°)
	var left_wing := MeshInstance3D.new()
	var w_mesh := BoxMesh.new()
	w_mesh.size = Vector3(0.4, 7.5, 6.0)
	left_wing.mesh = w_mesh
	left_wing.position = Vector3(-4.0, 6.0, 0)
	left_wing.rotation_degrees = Vector3(0, 0, -35)
	left_wing.set_surface_override_material(0, mat_shuttle)
	shuttle.add_child(left_wing)

	# Aile latérale Droite (repliée vers le haut à 45°)
	var right_wing := MeshInstance3D.new()
	right_wing.mesh = w_mesh
	right_wing.position = Vector3(4.0, 6.0, 0)
	right_wing.rotation_degrees = Vector3(0, 0, 35)
	right_wing.set_surface_override_material(0, mat_shuttle)
	shuttle.add_child(right_wing)

	# Tuyères de réacteur arrière
	for rx in [-1.5, 1.5]:
		var engine := MeshInstance3D.new()
		var eng_cyl := CylinderMesh.new()
		eng_cyl.top_radius = 0.9
		eng_cyl.bottom_radius = 1.1
		eng_cyl.height = 1.6
		engine.mesh = eng_cyl
		engine.position = Vector3(rx, 2.5, 6.2)
		engine.rotation_degrees = Vector3(90, 0, 0)
		engine.set_surface_override_material(0, mat_engine)
		shuttle.add_child(engine)

	# Passerelle d'accès déployée vers le sol
	var ramp := MeshInstance3D.new()
	var ramp_mesh := BoxMesh.new()
	ramp_mesh.size = Vector3(2.2, 0.2, 4.5)
	ramp.mesh = ramp_mesh
	ramp.position = Vector3(0, 1.0, 3.5)
	ramp.rotation_degrees = Vector3(22, 0, 0)
	var mat_ramp := StandardMaterial3D.new()
	mat_ramp.albedo_color = Color(0.3, 0.3, 0.32)
	ramp.set_surface_override_material(0, mat_ramp)
	shuttle.add_child(ramp)

	root.add_child(shuttle)

	# Enseigne Holo Spatioport
	var lp_lbl := Label3D.new()
	lp_lbl.text = "◈ SPATIOPORT DE LOST HEAVEN ◈\n« Navettes vers Anchorhead & Mos Eisley »"
	lp_lbl.position = Vector3(-18.0, 11.5, 5.2)
	lp_lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lp_lbl.font_size = 18
	lp_lbl.modulate = Color(0.2, 0.9, 1.0, 1.0)
	root.add_child(lp_lbl)

	return root


## 2. Centre Médical & Clonerie SWG (Medical Center & Cloning Facility)
static func build_swg_medcenter(pos: Vector3, yaw_deg: float = 0.0) -> Node3D:
	var root := Node3D.new()
	root.name = "Medical_Center_Lost_Heaven"
	root.position = pos
	root.rotation_degrees.y = yaw_deg

	var mat_white := StandardMaterial3D.new()
	mat_white.albedo_color = Color(0.85, 0.88, 0.90, 1.0)
	mat_white.roughness = 0.4

	var mat_blue_cross := StandardMaterial3D.new()
	mat_blue_cross.albedo_color = Color(0.1, 0.75, 1.0, 1.0)
	mat_blue_cross.emission_enabled = true
	mat_blue_cross.emission = Color(0.1, 0.75, 1.0, 1.0)
	mat_blue_cross.emission_energy_multiplier = 2.5

	var mat_bacta := StandardMaterial3D.new()
	mat_bacta.albedo_color = Color(0.1, 0.85, 0.75, 0.55)
	mat_bacta.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat_bacta.roughness = 0.1
	mat_bacta.emission_enabled = true
	mat_bacta.emission = Color(0.1, 0.85, 0.75, 1.0)
	mat_bacta.emission_energy_multiplier = 1.2

	var sb := StaticBody3D.new()

	# Structure Creuse POB Médicale Franchissable (Hall clinique accessible)
	# 1. Sol carrelé stérile
	var fl_mesh := MeshInstance3D.new()
	var fl_box := BoxMesh.new()
	fl_box.size = Vector3(16.0, 0.4, 14.0)
	fl_mesh.mesh = fl_box
	fl_mesh.position = Vector3(0, 0.2, 0)
	fl_mesh.set_surface_override_material(0, mat_white)
	sb.add_child(fl_mesh)
	var fl_col := CollisionShape3D.new()
	var fl_cshape := BoxShape3D.new()
	fl_cshape.size = Vector3(16.0, 0.4, 14.0)
	fl_col.shape = fl_cshape
	fl_col.position = Vector3(0, 0.2, 0)
	sb.add_child(fl_col)

	# 2. Toit clinique
	var rf_mesh := MeshInstance3D.new()
	var rf_box := BoxMesh.new()
	rf_box.size = Vector3(16.0, 0.6, 14.0)
	rf_mesh.mesh = rf_box
	rf_mesh.position = Vector3(0, 6.0, 0)
	rf_mesh.set_surface_override_material(0, mat_white)
	sb.add_child(rf_mesh)

	# 3. Mur arrière Nord
	var bk_mesh := MeshInstance3D.new()
	var bkb_box := BoxMesh.new()
	bkb_box.size = Vector3(16.0, 6.0, 0.8)
	bk_mesh.mesh = bkb_box
	bk_mesh.position = Vector3(0, 3.0, -6.6)
	bk_mesh.set_surface_override_material(0, mat_white)
	sb.add_child(bk_mesh)
	var bk_col := CollisionShape3D.new()
	var bk_cshape := BoxShape3D.new()
	bk_cshape.size = Vector3(16.0, 6.0, 0.8)
	bk_col.shape = bk_cshape
	bk_col.position = Vector3(0, 3.0, -6.6)
	sb.add_child(bk_col)

	# 4. Murs latéraux Ouest & Est
	for wx in [-7.6, 7.6]:
		var wl_mesh := MeshInstance3D.new()
		var wlb_box := BoxMesh.new()
		wlb_box.size = Vector3(0.8, 6.0, 14.0)
		wl_mesh.mesh = wlb_box
		wl_mesh.position = Vector3(wx, 3.0, 0)
		wl_mesh.set_surface_override_material(0, mat_white)
		sb.add_child(wl_mesh)
		var wl_col := CollisionShape3D.new()
		var wl_cshape := BoxShape3D.new()
		wl_cshape.size = Vector3(0.8, 6.0, 14.0)
		wl_col.shape = wl_cshape
		wl_col.position = Vector3(wx, 3.0, 0)
		sb.add_child(wl_col)

	# 5. Mur frontal Sud avec GRANDE PORTE D'ACCÈS CLINIQUE (4.2m de passage libre)
	for fx in [-5.4, 5.4]:
		var fr_mesh := MeshInstance3D.new()
		var frb_box := BoxMesh.new()
		frb_box.size = Vector3(5.2, 6.0, 0.8)
		fr_mesh.mesh = frb_box
		fr_mesh.position = Vector3(fx, 3.0, 6.6)
		fr_mesh.set_surface_override_material(0, mat_white)
		sb.add_child(fr_mesh)
		var fr_col := CollisionShape3D.new()
		var fr_cshape := BoxShape3D.new()
		fr_cshape.size = Vector3(5.2, 6.0, 0.8)
		fr_col.shape = fr_cshape
		fr_col.position = Vector3(fx, 3.0, 6.6)
		sb.add_child(fr_col)

	# Linteau de porte vitrée médicale
	var l_mesh := MeshInstance3D.new()
	var lb_box := BoxMesh.new()
	lb_box.size = Vector3(5.6, 2.2, 0.8)
	l_mesh.mesh = lb_box
	l_mesh.position = Vector3(0, 4.9, 6.6)
	l_mesh.set_surface_override_material(0, mat_white)
	sb.add_child(l_mesh)

	# Intérieur : Éclairage clinique néon turquoise
	var med_omni := OmniLight3D.new()
	med_omni.position = Vector3(0, 4.8, 0)
	med_omni.light_color = Color(0.6, 0.95, 1.0)
	med_omni.light_energy = 2.4
	med_omni.omni_range = 10.0
	sb.add_child(med_omni)

	# Intérieur : Bureau de diagnostic du Docteur Vane
	var desk := MeshInstance3D.new()
	var d_box := BoxMesh.new()
	d_box.size = Vector3(3.2, 0.9, 1.4)
	desk.mesh = d_box
	desk.position = Vector3(0, 0.65, -3.8)
	var mat_desk := StandardMaterial3D.new()
	mat_desk.albedo_color = Color(0.2, 0.25, 0.3)
	desk.set_surface_override_material(0, mat_desk)
	sb.add_child(desk)

	# Intérieur : 2 Lits d'examen médical
	for lx in [-4.5, 4.5]:
		var bed := MeshInstance3D.new()
		var b_mesh := BoxMesh.new()
		b_mesh.size = Vector3(1.6, 0.7, 3.0)
		bed.mesh = b_mesh
		bed.position = Vector3(lx, 0.55, -2.0)
		var mat_bed := StandardMaterial3D.new()
		mat_bed.albedo_color = Color(0.9, 0.92, 0.95)
		bed.set_surface_override_material(0, mat_bed)
		sb.add_child(bed)

	# Dôme médical supérieur
	var dome := MeshInstance3D.new()
	var sp := SphereMesh.new()
	sp.radius = 5.0
	sp.height = 3.5
	sp.is_hemisphere = true
	dome.mesh = sp
	dome.position = Vector3(0, 6.0, 0)
	dome.set_surface_override_material(0, mat_white)
	sb.add_child(dome)

	# Croix Caducée Holographique en façade
	var cross_h := MeshInstance3D.new()
	var ch_box := BoxMesh.new()
	ch_box.size = Vector3(3.2, 0.8, 0.2)
	cross_h.mesh = ch_box
	cross_h.position = Vector3(0, 4.5, 7.1)
	cross_h.set_surface_override_material(0, mat_blue_cross)
	sb.add_child(cross_h)

	var cross_v := MeshInstance3D.new()
	var cv_box := BoxMesh.new()
	cv_box.size = Vector3(0.8, 3.2, 0.2)
	cross_v.mesh = cv_box
	cross_v.position = Vector3(0, 4.5, 7.1)
	cross_v.set_surface_override_material(0, mat_blue_cross)
	sb.add_child(cross_v)

	# 2 Cuves de Bacta (Bacta Tanks) visibles devant le centre
	for bx in [-5.0, 5.0]:
		var tank := MeshInstance3D.new()
		var cyl := CylinderMesh.new()
		cyl.top_radius = 1.1
		cyl.bottom_radius = 1.1
		cyl.height = 3.2
		tank.mesh = cyl
		tank.position = Vector3(bx, 1.8, 7.8)
		tank.set_surface_override_material(0, mat_bacta)
		sb.add_child(tank)

		var bacta_light := OmniLight3D.new()
		bacta_light.position = Vector3(bx, 1.8, 7.8)
		bacta_light.light_color = Color(0.1, 0.9, 0.8)
		bacta_light.light_energy = 1.8
		bacta_light.omni_range = 4.0
		sb.add_child(bacta_light)

	root.add_child(sb)

	var lbl := Label3D.new()
	lbl.text = "◈ CENTRE MÉDICAL DE LOST HEAVEN ◈\n« Soins HAM, Dissipation Fatigue & Enregistrement Clone »"
	lbl.position = Vector3(0, 8.5, 7.2)
	lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lbl.font_size = 18
	lbl.modulate = Color(0.2, 0.95, 1.0, 1.0)
	root.add_child(lbl)

	return root


## 3. Hôtel de Ville / Hall de Guilde de Lost Heaven (Town Hall)
static func build_swg_town_hall(pos: Vector3, yaw_deg: float = 0.0) -> Node3D:
	var root := Node3D.new()
	root.name = "Town_Hall_Lost_Heaven"
	root.position = pos
	root.rotation_degrees.y = yaw_deg

	var mat_stone := StandardMaterial3D.new()
	mat_stone.albedo_color = Color(0.72, 0.62, 0.50, 1.0)
	mat_stone.roughness = 0.8

	var mat_gold := StandardMaterial3D.new()
	mat_gold.albedo_color = Color(0.95, 0.78, 0.25, 1.0)
	mat_gold.metallic = 0.8
	mat_gold.roughness = 0.3

	var mat_banner := StandardMaterial3D.new()
	mat_banner.albedo_color = Color(0.55, 0.15, 0.20, 1.0) # Pourpre royal
	mat_banner.roughness = 0.7

	var sb := StaticBody3D.new()

	# Structure Creuse POB Franchissable (Murs périphériques, Sol, Toit et Porte Ouverte)
	# 1. Sol intérieur carrelé
	var floor_m := MeshInstance3D.new()
	var f_box := BoxMesh.new()
	f_box.size = Vector3(22.0, 0.4, 16.0)
	floor_m.mesh = f_box
	floor_m.position = Vector3(0, 0.2, 0)
	floor_m.set_surface_override_material(0, mat_stone)
	sb.add_child(floor_m)
	var f_col := CollisionShape3D.new()
	var f_cshape := BoxShape3D.new()
	f_cshape.size = Vector3(22.0, 0.4, 16.0)
	f_col.shape = f_cshape
	f_col.position = Vector3(0, 0.2, 0)
	sb.add_child(f_col)

	# 2. Toit / Plafond supérieur
	var roof_m := MeshInstance3D.new()
	var r_box := BoxMesh.new()
	r_box.size = Vector3(22.0, 0.6, 16.0)
	roof_m.mesh = r_box
	roof_m.position = Vector3(0, 8.0, 0)
	roof_m.set_surface_override_material(0, mat_stone)
	sb.add_child(roof_m)

	# 3. Mur arrière Nord
	var back_m := MeshInstance3D.new()
	var bk_box := BoxMesh.new()
	bk_box.size = Vector3(22.0, 8.0, 0.8)
	back_m.mesh = bk_box
	back_m.position = Vector3(0, 4.0, -7.6)
	back_m.set_surface_override_material(0, mat_stone)
	sb.add_child(back_m)
	var bk_col := CollisionShape3D.new()
	var bk_cshape := BoxShape3D.new()
	bk_cshape.size = Vector3(22.0, 8.0, 0.8)
	bk_col.shape = bk_cshape
	bk_col.position = Vector3(0, 4.0, -7.6)
	sb.add_child(bk_col)

	# 4. Murs latéraux Ouest & Est
	for wx in [-10.6, 10.6]:
		var wall_m := MeshInstance3D.new()
		var w_box := BoxMesh.new()
		w_box.size = Vector3(0.8, 8.0, 16.0)
		wall_m.mesh = w_box
		wall_m.position = Vector3(wx, 4.0, 0)
		wall_m.set_surface_override_material(0, mat_stone)
		sb.add_child(wall_m)
		var w_col := CollisionShape3D.new()
		var w_cshape := BoxShape3D.new()
		w_cshape.size = Vector3(0.8, 8.0, 16.0)
		w_col.shape = w_cshape
		w_col.position = Vector3(wx, 4.0, 0)
		sb.add_child(w_col)

	# 5. Mur frontal Sud avec GRANDE PORTE D'ENTRÉE FRANCHISSABLE (5.2m de passage libre)
	for fx in [-7.2, 7.2]:
		var front_m := MeshInstance3D.new()
		var fr_box := BoxMesh.new()
		fr_box.size = Vector3(7.6, 8.0, 0.8)
		front_m.mesh = fr_box
		front_m.position = Vector3(fx, 4.0, 7.6)
		front_m.set_surface_override_material(0, mat_stone)
		sb.add_child(front_m)
		var fr_col := CollisionShape3D.new()
		var fr_cshape := BoxShape3D.new()
		fr_cshape.size = Vector3(7.6, 8.0, 0.8)
		fr_col.shape = fr_cshape
		fr_col.position = Vector3(fx, 4.0, 7.6)
		sb.add_child(fr_col)

	# Linteau supérieur de porte
	var lintel := MeshInstance3D.new()
	var l_box := BoxMesh.new()
	l_box.size = Vector3(6.8, 2.5, 0.8)
	lintel.mesh = l_box
	lintel.position = Vector3(0, 6.75, 7.6)
	lintel.set_surface_override_material(0, mat_stone)
	sb.add_child(lintel)

	# Intérieur : Tapis d'honneur rouge menant à l'estrade du Maire
	var carpet := MeshInstance3D.new()
	var cp_box := BoxMesh.new()
	cp_box.size = Vector3(4.0, 0.05, 12.0)
	carpet.mesh = cp_box
	carpet.position = Vector3(0, 0.43, 0.5)
	var mat_carpet := StandardMaterial3D.new()
	mat_carpet.albedo_color = Color(0.65, 0.12, 0.18)
	carpet.set_surface_override_material(0, mat_carpet)
	sb.add_child(carpet)

	# Intérieur : Estrade du Maire Odo Merr
	var dais := MeshInstance3D.new()
	var d_box := BoxMesh.new()
	d_box.size = Vector3(7.0, 0.6, 3.5)
	dais.mesh = d_box
	dais.position = Vector3(0, 0.65, -4.5)
	dais.set_surface_override_material(0, mat_gold)
	sb.add_child(dais)

	# Intérieur : Éclairage lustre monumental
	var hall_light := OmniLight3D.new()
	hall_light.position = Vector3(0, 6.5, 0)
	hall_light.light_color = Color(1.0, 0.9, 0.7)
	hall_light.light_energy = 2.8
	hall_light.omni_range = 14.0
	sb.add_child(hall_light)

	# Grand Escalier d'accès frontal (4 marches étagées)
	for i in range(4):
		var step := MeshInstance3D.new()
		var step_box := BoxMesh.new()
		step_box.size = Vector3(16.0 - i * 1.5, 0.35, 1.2)
		step.mesh = step_box
		step.position = Vector3(0, i * 0.35 + 0.17, 8.6 + (3 - i) * 1.0)
		step.set_surface_override_material(0, mat_stone)
		sb.add_child(step)

	# 4 Colonnes monumentales en façade
	for cx in [-7.5, -2.5, 2.5, 7.5]:
		var col_mesh := MeshInstance3D.new()
		var col_cyl := CylinderMesh.new()
		col_cyl.top_radius = 0.8
		col_cyl.bottom_radius = 0.9
		col_cyl.height = 7.6
		col_mesh.mesh = col_cyl
		col_mesh.position = Vector3(cx, 4.2, 8.6)
		col_mesh.set_surface_override_material(0, mat_stone)
		sb.add_child(col_mesh)

	# Fronton supérieur & Corniche dorée
	var pediment := MeshInstance3D.new()
	var ped_prism := PrismMesh.new()
	ped_prism.size = Vector3(22.0, 4.0, 2.5)
	pediment.mesh = ped_prism
	pediment.position = Vector3(0, 10.0, 8.0)
	pediment.set_surface_override_material(0, mat_stone)
	sb.add_child(pediment)

	# Bannières municipales pourpres
	for bx in [-6.0, 6.0]:
		var banner := MeshInstance3D.new()
		var b_mesh := BoxMesh.new()
		b_mesh.size = Vector3(1.8, 5.5, 0.08)
		banner.mesh = b_mesh
		banner.position = Vector3(bx, 5.0, 8.1)
		banner.set_surface_override_material(0, mat_banner)
		sb.add_child(banner)

	root.add_child(sb)

	var lbl := Label3D.new()
	lbl.text = "◈ HÔTEL DE VILLE DE LOST HEAVEN ◈\n« Bureau du Maire Odo Merr • Élections & Registre Foncier »"
	lbl.position = Vector3(0, 12.8, 8.4)
	lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lbl.font_size = 20
	lbl.modulate = Color(0.96, 0.86, 0.35, 1.0)
	root.add_child(lbl)

	return root


## 4. Maison Citadine en Pisé (Style Tatooine SWG Pre-CU)
static func build_swg_tatooine_house(pos: Vector3, yaw_deg: float = 0.0, variant: int = 0) -> Node3D:
	var root := Node3D.new()
	root.name = "House_Pise_SWG_%d" % variant
	root.position = pos
	root.rotation_degrees.y = yaw_deg

	var mat_pise := StandardMaterial3D.new()
	mat_pise.albedo_color = Color(0.70 + (variant % 3) * 0.03, 0.60, 0.48, 1.0)
	mat_pise.roughness = 0.9

	var mat_awning := StandardMaterial3D.new()
	mat_awning.albedo_color = Color(0.82, 0.72, 0.58) # Toile tendue beige
	mat_awning.roughness = 0.95

	var sb := StaticBody3D.new()

	# Bâtiment principal cubique
	var house := MeshInstance3D.new()
	var h_mesh := BoxMesh.new()
	h_mesh.size = Vector3(8.0, 4.2, 7.5)
	house.mesh = h_mesh
	house.position = Vector3(0, 2.1, 0)
	house.set_surface_override_material(0, mat_pise)
	sb.add_child(house)

	var col := CollisionShape3D.new()
	var c_box := BoxShape3D.new()
	c_box.size = Vector3(8.0, 4.2, 7.5)
	col.shape = c_box
	col.position = Vector3(0, 2.1, 0)
	sb.add_child(col)

	# Dôme d'aération sur le toit
	var dome := MeshInstance3D.new()
	var sp := SphereMesh.new()
	sp.radius = 1.8
	sp.height = 1.6
	sp.is_hemisphere = true
	dome.mesh = sp
	dome.position = Vector3(-1.5, 4.2, 0)
	dome.set_surface_override_material(0, mat_pise)
	sb.add_child(dome)

	# Escalier extérieur montant sur le toit-terrasse
	for i in range(5):
		var step := MeshInstance3D.new()
		var s_box := BoxMesh.new()
		s_box.size = Vector3(1.2, 0.4, 0.7)
		step.mesh = s_box
		step.position = Vector3(4.5, i * 0.4 + 0.2, -2.5 + i * 0.7)
		step.set_surface_override_material(0, mat_pise)
		sb.add_child(step)

	# Auvent de toile ombragé au-dessus de la porte
	var awning := MeshInstance3D.new()
	var a_mesh := BoxMesh.new()
	a_mesh.size = Vector3(2.8, 0.1, 2.0)
	awning.mesh = a_mesh
	awning.position = Vector3(0, 3.2, 4.4)
	awning.rotation_degrees = Vector3(15, 0, 0)
	awning.set_surface_override_material(0, mat_awning)
	sb.add_child(awning)

	root.add_child(sb)
	return root


## Bâtiment Ouvert Entrable (POB) — Maison de Joueur Meublée & Vendeur Personnel SWG Pre-CU
static func build_swg_enterable_player_house(pos: Vector3, yaw_deg: float = 0.0, house_name: String = "Maison de Voyageur") -> Node3D:
	var root := Node3D.new()
	root.name = "Enterable_House_" + house_name.replace(" ", "_")
	root.position = pos
	root.rotation_degrees.y = yaw_deg
	root.set_meta("display_name", house_name)
	root.set_meta("entity_kind", "housing")

	var mat_wall := StandardMaterial3D.new()
	mat_wall.albedo_color = Color(0.76, 0.64, 0.50) # Pisé chaud
	mat_wall.roughness = 0.9

	var mat_floor := StandardMaterial3D.new()
	mat_floor.albedo_color = Color(0.45, 0.35, 0.28) # Dalles cuites
	mat_floor.roughness = 0.8

	var mat_couch := StandardMaterial3D.new()
	mat_couch.albedo_color = Color(0.65, 0.25, 0.2) # Cuir pourpre

	var mat_table := StandardMaterial3D.new()
	mat_table.albedo_color = Color(0.25, 0.22, 0.20)
	mat_table.metallic = 0.5

	var sb := StaticBody3D.new()

	# 1. Sol intérieur carrelé (8m x 8m)
	var floor_mesh := MeshInstance3D.new()
	var f_box := BoxMesh.new()
	f_box.size = Vector3(8.2, 0.2, 8.2)
	floor_mesh.mesh = f_box
	floor_mesh.position = Vector3(0, 0.1, 0)
	floor_mesh.set_surface_override_material(0, mat_floor)
	sb.add_child(floor_mesh)

	var f_col := CollisionShape3D.new()
	var fc_box := BoxShape3D.new()
	fc_box.size = Vector3(8.2, 0.2, 8.2)
	f_col.shape = fc_box
	f_col.position = Vector3(0, 0.1, 0)
	sb.add_child(f_col)

	# 2. Toit / Plafond (Hauteur 3.8m)
	var roof_mesh := MeshInstance3D.new()
	var r_box := BoxMesh.new()
	r_box.size = Vector3(8.6, 0.3, 8.6)
	roof_mesh.mesh = r_box
	roof_mesh.position = Vector3(0, 3.8, 0)
	roof_mesh.set_surface_override_material(0, mat_wall)
	sb.add_child(roof_mesh)

	# 3. Murs avec ouverture de porte franchissable à Z = +4.0
	_add_wall_segment(sb, Vector3(0, 1.9, -4.0), Vector3(8.4, 3.6, 0.4), mat_wall)
	_add_wall_segment(sb, Vector3(-4.0, 1.9, 0), Vector3(0.4, 3.6, 8.0), mat_wall)
	_add_wall_segment(sb, Vector3(4.0, 1.9, 0), Vector3(0.4, 3.6, 8.0), mat_wall)
	_add_wall_segment(sb, Vector3(-2.6, 1.9, 4.0), Vector3(2.8, 3.6, 0.4), mat_wall)
	_add_wall_segment(sb, Vector3(2.6, 1.9, 4.0), Vector3(2.8, 3.6, 0.4), mat_wall)
	_add_wall_segment(sb, Vector3(0, 3.2, 4.0), Vector3(2.4, 1.2, 0.4), mat_wall)

	# 4. Éclairage chaleureux intérieur
	var in_light := OmniLight3D.new()
	in_light.position = Vector3(0, 3.2, 0)
	in_light.light_color = Color(1.0, 0.85, 0.65)
	in_light.light_energy = 2.8
	in_light.omni_range = 7.5
	root.add_child(in_light)

	# 5. Mobilier Intérieur : Table basse, banquettes, coffre de maison
	var table := MeshInstance3D.new()
	var t_cyl := CylinderMesh.new()
	t_cyl.top_radius = 0.9
	t_cyl.bottom_radius = 0.9
	t_cyl.height = 0.55
	table.mesh = t_cyl
	table.position = Vector3(-1.2, 0.45, -1.0)
	table.set_surface_override_material(0, mat_table)
	root.add_child(table)

	var couch := MeshInstance3D.new()
	var c_box := BoxMesh.new()
	c_box.size = Vector3(2.2, 0.5, 0.8)
	couch.mesh = c_box
	couch.position = Vector3(-1.2, 0.4, -2.4)
	couch.set_surface_override_material(0, mat_couch)
	root.add_child(couch)

	# Coffre de Stockage de Maison
	var chest := MeshInstance3D.new()
	var ch_box := BoxMesh.new()
	ch_box.size = Vector3(1.2, 0.8, 0.7)
	chest.mesh = ch_box
	chest.position = Vector3(2.8, 0.5, -2.8)
	var mat_chest := StandardMaterial3D.new()
	mat_chest.albedo_color = Color(0.2, 0.6, 0.7)
	chest.set_surface_override_material(0, mat_chest)
	root.add_child(chest)

	var chest_lbl := Label3D.new()
	chest_lbl.text = "◈ Coffre Sécurisé de Maison ◈"
	chest_lbl.position = Vector3(2.8, 1.2, -2.8)
	chest_lbl.font_size = 11
	chest_lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	chest_lbl.modulate = Color(0.4, 0.9, 1.0)
	root.add_child(chest_lbl)

	# 6. Comptoir et Vendeur PNJ Personnel (Player Vendor)
	var bar_counter := MeshInstance3D.new()
	var b_box := BoxMesh.new()
	b_box.size = Vector3(2.2, 1.0, 0.7)
	bar_counter.mesh = b_box
	bar_counter.position = Vector3(2.4, 0.6, 1.2)
	bar_counter.set_surface_override_material(0, mat_table)
	root.add_child(bar_counter)

	root.add_child(sb)
	return root


static func _add_wall_segment(parent: Node3D, pos: Vector3, size_vec: Vector3, mat: Material) -> void:
	var mesh_inst := MeshInstance3D.new()
	var b_mesh := BoxMesh.new()
	b_mesh.size = size_vec
	mesh_inst.mesh = b_mesh
	mesh_inst.position = pos
	mesh_inst.set_surface_override_material(0, mat)
	parent.add_child(mesh_inst)

	var col_inst := CollisionShape3D.new()
	var b_shape := BoxShape3D.new()
	b_shape.size = size_vec
	col_inst.shape = b_shape
	col_inst.position = pos
	parent.add_child(col_inst)


## 5. Porte Fortifiée de Ville & Mur d'Enceinte (City Wall & Gate)
static func build_swg_city_wall_and_gate(pos: Vector3, yaw_deg: float = 0.0, gate_name: String = "Porte Ouest") -> Node3D:
	var root := Node3D.new()
	root.name = "City_Gate_" + gate_name
	root.position = pos
	root.rotation_degrees.y = yaw_deg

	var mat_wall := StandardMaterial3D.new()
	mat_wall.albedo_color = Color(0.58, 0.50, 0.40, 1.0)
	mat_wall.roughness = 0.9

	var sb := StaticBody3D.new()

	# Bastion Gauche
	var left_tower := MeshInstance3D.new()
	var b_box := BoxMesh.new()
	b_box.size = Vector3(6.0, 9.0, 6.0)
	left_tower.mesh = b_box
	left_tower.position = Vector3(-6.5, 4.5, 0)
	left_tower.set_surface_override_material(0, mat_wall)
	sb.add_child(left_tower)

	# Bastion Droit
	var right_tower := MeshInstance3D.new()
	right_tower.mesh = b_box
	right_tower.position = Vector3(6.5, 4.5, 0)
	right_tower.set_surface_override_material(0, mat_wall)
	sb.add_child(right_tower)

	# Arche supérieure de passage
	var arch := MeshInstance3D.new()
	var a_box := BoxMesh.new()
	a_box.size = Vector3(8.0, 3.0, 4.0)
	arch.mesh = a_box
	arch.position = Vector3(0, 7.5, 0)
	arch.set_surface_override_material(0, mat_wall)
	sb.add_child(arch)

	# Murs d'enceinte prolongeant chaque côté (15m de chaque côté)
	for side in [-1, 1]:
		var wall_ext := MeshInstance3D.new()
		var w_box := BoxMesh.new()
		w_box.size = Vector3(18.0, 6.0, 3.0)
		wall_ext.mesh = w_box
		wall_ext.position = Vector3(side * 18.0, 3.0, 0)
		wall_ext.set_surface_override_material(0, mat_wall)
		sb.add_child(wall_ext)

	# Collisions
	var col_l := CollisionShape3D.new()
	var c_box := BoxShape3D.new()
	c_box.size = Vector3(22.0, 9.0, 6.0)
	col_l.shape = c_box
	col_l.position = Vector3(-14.0, 4.5, 0)
	sb.add_child(col_l)

	var col_r := CollisionShape3D.new()
	col_r.shape = c_box
	col_r.position = Vector3(14.0, 4.5, 0)
	sb.add_child(col_r)

	root.add_child(sb)

	var lbl := Label3D.new()
	lbl.text = "◈ LOST HEAVEN • %s ◈\n« Zone Sous Protection de la Milice »" % gate_name.to_upper()
	lbl.position = Vector3(0, 9.5, 2.2)
	lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lbl.font_size = 18
	lbl.modulate = Color(0.95, 0.85, 0.3, 1.0)
	root.add_child(lbl)

	return root


# ==============================================================================
#  MOBILIER URBAIN, TERMINAUX & PROPS SWG AUTHENTIQUES
# ==============================================================================

## 6. Vaporisateur d'Humidité SWG (Moisture Vaporator GX-8)
static func build_moisture_vaporator(pos: Vector3) -> Node3D:
	var root := Node3D.new()
	root.name = "Moisture_Vaporator"
	root.position = pos

	var mat_metal := StandardMaterial3D.new()
	mat_metal.albedo_color = Color(0.65, 0.68, 0.70, 1.0)
	mat_metal.metallic = 0.8
	mat_metal.roughness = 0.35

	var mat_light := StandardMaterial3D.new()
	mat_light.albedo_color = Color(0.2, 0.9, 1.0)
	mat_light.emission_enabled = true
	mat_light.emission = Color(0.2, 0.9, 1.0)
	mat_light.emission_energy_multiplier = 2.0

	var sb := StaticBody3D.new()

	# Mât central élancé (6.5m)
	var mast := MeshInstance3D.new()
	var m_cyl := CylinderMesh.new()
	m_cyl.top_radius = 0.22
	m_cyl.bottom_radius = 0.35
	m_cyl.height = 6.5
	mast.mesh = m_cyl
	mast.position = Vector3(0, 3.25, 0)
	mast.set_surface_override_material(0, mat_metal)
	sb.add_child(mast)

	# Trépied à la base
	for i in range(3):
		var leg := MeshInstance3D.new()
		var l_box := BoxMesh.new()
		l_box.size = Vector3(0.2, 0.2, 1.8)
		leg.mesh = l_box
		var angle: float = i * PI * 2.0 / 3.0
		leg.position = Vector3(cos(angle) * 0.9, 0.4, sin(angle) * 0.9)
		leg.rotation = Vector3(0, -angle, 0.4)
		leg.set_surface_override_material(0, mat_metal)
		sb.add_child(leg)

	# Anneaux de condensation au milieu
	var ring := MeshInstance3D.new()
	var tor := TorusMesh.new()
	tor.inner_radius = 0.6
	tor.outer_radius = 0.9
	ring.mesh = tor
	ring.position = Vector3(0, 4.0, 0)
	ring.set_surface_override_material(0, mat_metal)
	sb.add_child(ring)

	# Tête de captage au sommet avec voyant cyan
	var beacon := MeshInstance3D.new()
	var b_sp := SphereMesh.new()
	b_sp.radius = 0.35
	b_sp.height = 0.7
	beacon.mesh = b_sp
	beacon.position = Vector3(0, 6.7, 0)
	beacon.set_surface_override_material(0, mat_light)
	sb.add_child(beacon)

	var omni := OmniLight3D.new()
	omni.position = Vector3(0, 6.7, 0)
	omni.light_color = Color(0.2, 0.9, 1.0)
	omni.light_energy = 1.0
	omni.omni_range = 3.5
	sb.add_child(omni)

	var col := CollisionShape3D.new()
	var c_cyl := CylinderShape3D.new()
	c_cyl.radius = 0.8
	c_cyl.height = 6.5
	col.shape = c_cyl
	col.position = Vector3(0, 3.25, 0)
	sb.add_child(col)

	root.add_child(sb)
	return root


## 7. Borne de Terminal de Mission SWG (Mission Terminal)
static func build_mission_terminal(pos: Vector3, yaw_deg: float = 0.0) -> Node3D:
	return _build_generic_terminal(pos, yaw_deg, "Terminal de Missions", Color(0.2, 0.8, 1.0), "term_mission")


## 8. Borne de Terminal de Marché / Bazar (Bazaar Terminal)
static func build_bazaar_terminal(pos: Vector3, yaw_deg: float = 0.0) -> Node3D:
	return _build_generic_terminal(pos, yaw_deg, "Terminal du Bazar Public", Color(0.95, 0.8, 0.2), "term_bazaar")


## 9. Borne Bancaire SWG (Bank Terminal)
static func build_bank_terminal(pos: Vector3, yaw_deg: float = 0.0) -> Node3D:
	return _build_generic_terminal(pos, yaw_deg, "Terminal Bancaire Galactique", Color(0.2, 1.0, 0.4), "term_bank")


## 10. Borne d'Assurance & Clonage (Cloning Terminal)
static func build_cloning_terminal(pos: Vector3, yaw_deg: float = 0.0) -> Node3D:
	return _build_generic_terminal(pos, yaw_deg, "Borne d'Assurance Clonage", Color(0.9, 0.3, 0.9), "term_clone")


static func _build_generic_terminal(pos: Vector3, yaw_deg: float, term_name: String, screen_col: Color, kind_id: String) -> Node3D:
	var root := Node3D.new()
	root.name = term_name.replace(" ", "_")
	root.position = pos
	root.rotation_degrees.y = yaw_deg
	root.set_meta("entity_kind", kind_id)
	root.set_meta("display_name", term_name)

	var mat_body := StandardMaterial3D.new()
	mat_body.albedo_color = Color(0.28, 0.30, 0.32, 1.0)
	mat_body.metallic = 0.85
	mat_body.roughness = 0.3

	var mat_screen := StandardMaterial3D.new()
	mat_screen.albedo_color = screen_col
	mat_screen.emission_enabled = true
	mat_screen.emission = screen_col
	mat_screen.emission_energy_multiplier = 2.2

	var sb := StaticBody3D.new()

	# Piédestal
	var base := MeshInstance3D.new()
	var b_box := BoxMesh.new()
	b_box.size = Vector3(0.9, 1.4, 0.7)
	base.mesh = b_box
	base.position = Vector3(0, 0.7, 0)
	base.set_surface_override_material(0, mat_body)
	sb.add_child(base)

	# Écran vertical holographique incliné
	var screen := MeshInstance3D.new()
	var s_box := BoxMesh.new()
	s_box.size = Vector3(0.75, 0.65, 0.05)
	screen.mesh = s_box
	screen.position = Vector3(0, 1.5, 0.1)
	screen.rotation_degrees = Vector3(-18, 0, 0)
	screen.set_surface_override_material(0, mat_screen)
	sb.add_child(screen)

	var light := OmniLight3D.new()
	light.position = Vector3(0, 1.6, 0.35)
	light.light_color = screen_col
	light.light_energy = 1.2
	light.omni_range = 2.5
	sb.add_child(light)

	var col := CollisionShape3D.new()
	var c_shape := BoxShape3D.new()
	c_shape.size = Vector3(0.9, 1.8, 0.7)
	col.shape = c_shape
	col.position = Vector3(0, 0.9, 0)
	sb.add_child(col)

	root.add_child(sb)

	var lbl := Label3D.new()
	lbl.text = "◈ %s ◈" % term_name
	lbl.position = Vector3(0, 2.2, 0)
	lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lbl.font_size = 14
	lbl.modulate = screen_col
	root.add_child(lbl)

	return root


## 11. Landspeeder SWG (Style X-34 garé en lévitation)
static func build_landspeeder(pos: Vector3, yaw_deg: float = 0.0) -> Node3D:
	var root := Node3D.new()
	root.name = "Landspeeder_X34"
	root.position = pos
	root.rotation_degrees.y = yaw_deg

	var mat_body := StandardMaterial3D.new()
	mat_body.albedo_color = Color(0.75, 0.25, 0.22, 1.0) # Bordeaux délavé
	mat_body.roughness = 0.4
	mat_body.metallic = 0.6

	var mat_windshield := StandardMaterial3D.new()
	mat_windshield.albedo_color = Color(0.2, 0.5, 0.7, 0.6)
	mat_windshield.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat_windshield.roughness = 0.1

	var mat_turbine := StandardMaterial3D.new()
	mat_turbine.albedo_color = Color(0.3, 0.35, 0.38)
	mat_turbine.metallic = 0.9

	var sb := StaticBody3D.new()

	# Châssis caréné en lévitation à 0.4m du sol
	var body := MeshInstance3D.new()
	var b_box := BoxMesh.new()
	b_box.size = Vector3(2.4, 0.65, 4.8)
	body.mesh = b_box
	body.position = Vector3(0, 0.75, 0)
	body.set_surface_override_material(0, mat_body)
	sb.add_child(body)

	# 3 Turbines réacteurs cylindriques (G / D / C)
	for tx in [-1.3, 0.0, 1.3]:
		var turb := MeshInstance3D.new()
		var t_cyl := CylinderMesh.new()
		t_cyl.top_radius = 0.35
		t_cyl.bottom_radius = 0.35
		t_cyl.height = 2.2
		turb.mesh = t_cyl
		turb.position = Vector3(tx, 1.2 if tx == 0.0 else 0.8, -1.2)
		turb.rotation_degrees = Vector3(90, 0, 0)
		turb.set_surface_override_material(0, mat_turbine)
		sb.add_child(turb)

	# Pare-brise cockpit courbé
	var windshield := MeshInstance3D.new()
	var w_mesh := BoxMesh.new()
	w_mesh.size = Vector3(1.8, 0.5, 0.1)
	windshield.mesh = w_mesh
	windshield.position = Vector3(0, 1.25, 0.6)
	windshield.rotation_degrees = Vector3(25, 0, 0)
	windshield.set_surface_override_material(0, mat_windshield)
	sb.add_child(windshield)

	var col := CollisionShape3D.new()
	var c_box := BoxShape3D.new()
	c_box.size = Vector3(2.8, 1.2, 5.0)
	col.shape = c_box
	col.position = Vector3(0, 0.8, 0)
	sb.add_child(col)

	root.add_child(sb)

	var lbl := Label3D.new()
	lbl.text = "◈ Landspeeder X-34 ◈"
	lbl.position = Vector3(0, 2.0, 0)
	lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lbl.font_size = 14
	lbl.modulate = Color(0.9, 0.95, 1.0)
	root.add_child(lbl)

	return root


## 12. Amas de Fret Cargo & Conteneurs Industriels (Cargo Cluster)
static func build_cargo_cluster(pos: Vector3) -> Node3D:
	var root := Node3D.new()
	root.name = "Cargo_Cluster"
	root.position = pos

	var mat_crate1 := StandardMaterial3D.new()
	mat_crate1.albedo_color = Color(0.35, 0.45, 0.55, 1.0)
	mat_crate1.roughness = 0.6

	var mat_crate2 := StandardMaterial3D.new()
	mat_crate2.albedo_color = Color(0.65, 0.45, 0.25, 1.0)
	mat_crate2.roughness = 0.8

	var mat_barrel := StandardMaterial3D.new()
	mat_barrel.albedo_color = Color(0.85, 0.35, 0.15, 1.0)
	mat_barrel.metallic = 0.7

	var sb := StaticBody3D.new()

	# Caisse 1 (Grande)
	var c1 := MeshInstance3D.new()
	var b1 := BoxMesh.new()
	b1.size = Vector3(2.0, 1.6, 2.0)
	c1.mesh = b1
	c1.position = Vector3(0, 0.8, 0)
	c1.set_surface_override_material(0, mat_crate1)
	sb.add_child(c1)

	# Caisse 2 empilée
	var c2 := MeshInstance3D.new()
	var b2 := BoxMesh.new()
	b2.size = Vector3(1.4, 1.2, 1.4)
	c2.mesh = b2
	c2.position = Vector3(0.2, 2.2, 0.1)
	c2.rotation_degrees.y = 15.0
	c2.set_surface_override_material(0, mat_crate2)
	sb.add_child(c2)

	# Barils de carburant
	for bx in [-1.5, 1.6]:
		var barrel := MeshInstance3D.new()
		var b_cyl := CylinderMesh.new()
		b_cyl.top_radius = 0.45
		b_cyl.bottom_radius = 0.45
		b_cyl.height = 1.3
		barrel.mesh = b_cyl
		barrel.position = Vector3(bx, 0.65, 0.5)
		barrel.set_surface_override_material(0, mat_barrel)
		sb.add_child(barrel)

	var col := CollisionShape3D.new()
	var c_shape := BoxShape3D.new()
	c_shape.size = Vector3(3.8, 2.8, 2.8)
	col.shape = c_shape
	col.position = Vector3(0, 1.4, 0)
	sb.add_child(col)

	root.add_child(sb)
	return root


## 13. Lampadaire de Rue (Street Lamp)
static func build_street_lamp(pos: Vector3) -> Node3D:
	var root := Node3D.new()
	root.name = "Street_Lamp"
	root.position = pos

	var mat_pole := StandardMaterial3D.new()
	mat_pole.albedo_color = Color(0.3, 0.35, 0.4)
	mat_pole.metallic = 0.85

	var mat_lamp := StandardMaterial3D.new()
	mat_lamp.albedo_color = Color(1.0, 0.9, 0.6)
	mat_lamp.emission_enabled = true
	mat_lamp.emission = Color(1.0, 0.9, 0.6)
	mat_lamp.emission_energy_multiplier = 3.0

	var pole := MeshInstance3D.new()
	var p_cyl := CylinderMesh.new()
	p_cyl.top_radius = 0.08
	p_cyl.bottom_radius = 0.12
	p_cyl.height = 4.2
	pole.mesh = p_cyl
	pole.position = Vector3(0, 2.1, 0)
	pole.set_surface_override_material(0, mat_pole)
	root.add_child(pole)

	var lantern := MeshInstance3D.new()
	var l_box := BoxMesh.new()
	l_box.size = Vector3(0.5, 0.35, 0.5)
	lantern.mesh = l_box
	lantern.position = Vector3(0, 4.3, 0)
	lantern.set_surface_override_material(0, mat_lamp)
	root.add_child(lantern)

	var light := OmniLight3D.new()
	light.position = Vector3(0, 4.2, 0)
	light.light_color = Color(1.0, 0.92, 0.7)
	light.light_energy = 1.8
	light.omni_range = 9.0
	root.add_child(light)

	return root


# ==============================================================================
#  WILDERNESS, RELIEF & CAMPS DE SCOUT NOMADES
# ==============================================================================

## 14. Campement de Scout Nomade (Scout Survival Camp)
static func build_scout_camp(pos: Vector3) -> Node3D:
	var root := Node3D.new()
	root.name = "Scout_Camp"
	root.position = pos

	var mat_canvas := StandardMaterial3D.new()
	mat_canvas.albedo_color = Color(0.85, 0.78, 0.65, 1.0)
	mat_canvas.roughness = 0.95

	var mat_fire := StandardMaterial3D.new()
	mat_fire.albedo_color = Color(1.0, 0.4, 0.1, 1.0)
	mat_fire.emission_enabled = true
	mat_fire.emission = Color(1.0, 0.4, 0.1, 1.0)
	mat_fire.emission_energy_multiplier = 4.0

	# Tente igloo en toile
	var tent := MeshInstance3D.new()
	var t_dome := SphereMesh.new()
	t_dome.radius = 2.4
	t_dome.height = 2.2
	t_dome.is_hemisphere = true
	tent.mesh = t_dome
	tent.position = Vector3(0, 0, 0)
	tent.set_surface_override_material(0, mat_canvas)
	root.add_child(tent)

	# Foyer de camp avec braises incandescentes
	var fire := MeshInstance3D.new()
	var f_cone := CylinderMesh.new()
	f_cone.top_radius = 0.1
	f_cone.bottom_radius = 0.6
	f_cone.height = 0.5
	fire.mesh = f_cone
	fire.position = Vector3(0, 0.25, 3.8)
	fire.set_surface_override_material(0, mat_fire)
	root.add_child(fire)

	# Lumière vacillante du feu de camp
	var fire_light := OmniLight3D.new()
	fire_light.position = Vector3(0, 0.8, 3.8)
	fire_light.light_color = Color(1.0, 0.55, 0.2)
	fire_light.light_energy = 2.5
	fire_light.omni_range = 8.0
	root.add_child(fire_light)

	var lbl := Label3D.new()
	lbl.text = "◈ Bivouac de Scout Nomade ◈\n« Zone de Récupération HAM & Camouflage »"
	lbl.position = Vector3(0, 2.8, 0)
	lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lbl.font_size = 14
	lbl.modulate = Color(1.0, 0.8, 0.3)
	root.add_child(lbl)

	return root


## 15. Extracteur Minier Industriel SWG (Mining Harvester)
static func build_mining_harvester(pos: Vector3, yaw_deg: float = 0.0) -> Node3D:
	var root := Node3D.new()
	root.name = "Mining_Harvester"
	root.position = pos
	root.rotation_degrees.y = yaw_deg

	var mat_indus := StandardMaterial3D.new()
	mat_indus.albedo_color = Color(0.78, 0.52, 0.15, 1.0) # Jaune/Orange industriel
	mat_indus.roughness = 0.6
	mat_indus.metallic = 0.7

	var mat_drill := StandardMaterial3D.new()
	mat_drill.albedo_color = Color(0.25, 0.28, 0.30)
	mat_drill.metallic = 0.95

	var sb := StaticBody3D.new()

	# Trémie cylindrique principale
	var hopper := MeshInstance3D.new()
	var h_cyl := CylinderMesh.new()
	h_cyl.top_radius = 2.2
	h_cyl.bottom_radius = 2.2
	h_cyl.height = 5.5
	hopper.mesh = h_cyl
	hopper.position = Vector3(0, 4.2, 0)
	hopper.set_surface_override_material(0, mat_indus)
	sb.add_child(hopper)

	# 4 Pieds hydrauliques articulés
	for i in range(4):
		var leg := MeshInstance3D.new()
		var l_cyl := CylinderMesh.new()
		l_cyl.top_radius = 0.25
		l_cyl.bottom_radius = 0.35
		l_cyl.height = 4.2
		leg.mesh = l_cyl
		var angle: float = i * PI * 0.5 + PI * 0.25
		leg.position = Vector3(cos(angle) * 2.8, 2.1, sin(angle) * 2.8)
		leg.rotation = Vector3(cos(angle) * 0.3, 0, sin(angle) * 0.3)
		leg.set_surface_override_material(0, mat_drill)
		sb.add_child(leg)

	# Piston central de forage
	var drill := MeshInstance3D.new()
	var d_cyl := CylinderMesh.new()
	d_cyl.top_radius = 0.7
	d_cyl.bottom_radius = 0.4
	d_cyl.height = 3.5
	drill.mesh = d_cyl
	drill.position = Vector3(0, 1.2, 0)
	drill.set_surface_override_material(0, mat_drill)
	sb.add_child(drill)

	var col := CollisionShape3D.new()
	var c_cyl := CylinderShape3D.new()
	c_cyl.radius = 3.2
	c_cyl.height = 7.0
	col.shape = c_cyl
	col.position = Vector3(0, 3.5, 0)
	sb.add_child(col)

	root.add_child(sb)

	var lbl := Label3D.new()
	lbl.text = "◈ Extracteur Minier Lourd ◈\n« Gisement de Minerai Ferrique (92% Pureté) »"
	lbl.position = Vector3(0, 7.5, 0)
	lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lbl.font_size = 16
	lbl.modulate = Color(1.0, 0.75, 0.2)
	root.add_child(lbl)

	return root


## 16. Éperon Rocheux / Mesa Géologique du Désert (Rock Outcrop)
static func build_rock_outcrop(pos: Vector3, scale_vec: Vector3 = Vector3.ONE) -> Node3D:
	var root := Node3D.new()
	root.name = "Rock_Outcrop"
	root.position = pos
	root.scale = scale_vec

	var mat_rock := StandardMaterial3D.new()
	mat_rock.albedo_color = Color(0.62, 0.38, 0.28, 1.0) # Grès ocre-rouge stratifié
	mat_rock.roughness = 0.95

	var sb := StaticBody3D.new()

	var mesh_inst := MeshInstance3D.new()
	var prism := PrismMesh.new()
	prism.size = Vector3(12.0, 8.0, 10.0)
	mesh_inst.mesh = prism
	mesh_inst.position = Vector3(0, 4.0, 0)
	mesh_inst.set_surface_override_material(0, mat_rock)
	sb.add_child(mesh_inst)

	var col := CollisionShape3D.new()
	var c_shape := BoxShape3D.new()
	c_shape.size = Vector3(12.0, 8.0, 10.0)
	col.shape = c_shape
	col.position = Vector3(0, 4.0, 0)
	sb.add_child(col)

	root.add_child(sb)
	return root


## 17. Flore Xérophile du Désert (Cactus cierges & Buissons secs)
static func build_desert_flora(pos: Vector3) -> Node3D:
	var root := Node3D.new()
	root.name = "Desert_Flora"
	root.position = pos

	var mat_cactus := StandardMaterial3D.new()
	mat_cactus.albedo_color = Color(0.28, 0.48, 0.32, 1.0)
	mat_cactus.roughness = 0.85

	# Tronc central du cactus
	var stem := MeshInstance3D.new()
	var s_cyl := CylinderMesh.new()
	s_cyl.top_radius = 0.28
	s_cyl.bottom_radius = 0.32
	s_cyl.height = 3.2
	stem.mesh = s_cyl
	stem.position = Vector3(0, 1.6, 0)
	stem.set_surface_override_material(0, mat_cactus)
	root.add_child(stem)

	# Bras latéraux
	for side in [-1, 1]:
		var arm := MeshInstance3D.new()
		var a_cyl := CylinderMesh.new()
		a_cyl.top_radius = 0.2
		a_cyl.bottom_radius = 0.22
		a_cyl.height = 1.4
		arm.mesh = a_cyl
		arm.position = Vector3(side * 0.65, 2.2, 0)
		arm.set_surface_override_material(0, mat_cactus)
		root.add_child(arm)

	return root


# ==============================================================================
#  PNJ & BESTIAIRE VIVANT 3D (Droïdes, Faune Dewback / Bantha, Chacal, Fennec)
# ==============================================================================

## 18. Droïde Astromécano (R2 Style)
static func build_astromech_droid(pos: Vector3) -> CharacterBody3D:
	var body := CharacterBody3D.new()
	body.name = "Droid_R2_Astromech"
	body.position = pos
	body.set_meta("entity_kind", "npc_droid_astromech")
	body.set_meta("display_name", "Droïde Astromécano R2-T8")

	var mat_white := StandardMaterial3D.new()
	mat_white.albedo_color = Color(0.9, 0.92, 0.95)
	mat_white.roughness = 0.3
	mat_white.metallic = 0.5

	var mat_blue := StandardMaterial3D.new()
	mat_blue.albedo_color = Color(0.1, 0.4, 0.85)
	mat_blue.metallic = 0.7

	# Corps cylindrique
	var torso := MeshInstance3D.new()
	var t_cyl := CylinderMesh.new()
	t_cyl.top_radius = 0.4
	t_cyl.bottom_radius = 0.4
	t_cyl.height = 0.75
	torso.mesh = t_cyl
	torso.position = Vector3(0, 0.65, 0)
	torso.set_surface_override_material(0, mat_white)
	body.add_child(torso)

	# Dôme supérieur bleu
	var dome := MeshInstance3D.new()
	var d_sp := SphereMesh.new()
	d_sp.radius = 0.4
	d_sp.height = 0.4
	d_sp.is_hemisphere = true
	dome.mesh = d_sp
	dome.position = Vector3(0, 1.02, 0)
	dome.set_surface_override_material(0, mat_blue)
	body.add_child(dome)

	# 2 Jambes latérales
	for jx in [-0.5, 0.5]:
		var leg := MeshInstance3D.new()
		var l_box := BoxMesh.new()
		l_box.size = Vector3(0.15, 0.8, 0.25)
		leg.mesh = l_box
		leg.position = Vector3(jx, 0.45, 0)
		leg.set_surface_override_material(0, mat_white)
		body.add_child(leg)

	var col := CollisionShape3D.new()
	var c_cap := CapsuleShape3D.new()
	c_cap.radius = 0.45
	c_cap.height = 1.1
	col.shape = c_cap
	col.position = Vector3(0, 0.55, 0)
	body.add_child(col)

	var lbl := Label3D.new()
	lbl.text = "◈ Droïde R2-T8 ◈"
	lbl.position = Vector3(0, 1.45, 0)
	lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lbl.font_size = 12
	lbl.modulate = Color(0.2, 0.8, 1.0)
	body.add_child(lbl)

	return body


## 16. Chargement d'Avatar VRM Humanoid avec Animateur Procédural (Suppression T-Pose)
static func load_humanoid_vrm(vrm_name: String, is_entertainer: bool = false) -> Node3D:
	var candidate_paths := [
		"res://assets/avatars/" + vrm_name,
		"packages/compagnon-desktop/overlay/vrm/" + vrm_name,
		"C:/Agent_IA/compagnon-desktop/overlay/vrm/" + vrm_name,
		"J:/swgemu/clients/swg-client/assets/avatars/" + vrm_name,
		"res://assets/avatars/Compagnon.vrm",
		"res://assets/avatars/LadyKoi.vrm"
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
					scene.rotation_degrees.y = 180.0
					scene.scale = Vector3(0.92, 0.92, 0.92)
					var sk: Skeleton3D = _SwgVrmAnimatorScript.find_skeleton_in_tree(scene)
					if sk != null:
						var anim := _SwgVrmAnimatorScript.new()
						anim.name = "VrmAnimator"
						scene.add_child(anim)
						anim.setup(sk, is_entertainer)
					return scene
	return null


## 17. Faune Sauvage : Chacal Doré / Chiot des Sables (Quadrupède Articulé)
static func build_quadruped_creature(pos: Vector3, col: Color, scale_factor: float = 1.0) -> Node3D:
	var root := Node3D.new()
	root.position = pos

	var mat_fur := StandardMaterial3D.new()
	mat_fur.albedo_color = col
	mat_fur.roughness = 0.85

	# Tronc / Torse
	var body_mesh := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = Vector3(0.55, 0.45, 1.2) * scale_factor
	body_mesh.mesh = box
	body_mesh.position = Vector3(0, 0.55 * scale_factor, 0)
	body_mesh.set_surface_override_material(0, mat_fur)
	root.add_child(body_mesh)

	# Tête avec museau canin
	var head := MeshInstance3D.new()
	var h_box := BoxMesh.new()
	h_box.size = Vector3(0.35, 0.35, 0.5) * scale_factor
	head.mesh = h_box
	head.position = Vector3(0, 0.8 * scale_factor, -0.65 * scale_factor)
	head.set_surface_override_material(0, mat_fur)
	root.add_child(head)

	# Oreilles pointues
	for ex in [-0.14, 0.14]:
		var ear := MeshInstance3D.new()
		var p_mesh := PrismMesh.new()
		p_mesh.size = Vector3(0.12, 0.25, 0.08) * scale_factor
		ear.mesh = p_mesh
		ear.position = Vector3(ex * scale_factor, 1.05 * scale_factor, -0.6 * scale_factor)
		ear.set_surface_override_material(0, mat_fur)
		root.add_child(ear)

	# 4 Pattes
	for px in [-0.22, 0.22]:
		for pz in [-0.4, 0.4]:
			var leg := MeshInstance3D.new()
			var l_cyl := CylinderMesh.new()
			l_cyl.top_radius = 0.08 * scale_factor
			l_cyl.bottom_radius = 0.06 * scale_factor
			l_cyl.height = 0.55 * scale_factor
			leg.mesh = l_cyl
			leg.position = Vector3(px * scale_factor, 0.28 * scale_factor, pz * scale_factor)
			leg.set_surface_override_material(0, mat_fur)
			root.add_child(leg)

	# Queue
	var tail := MeshInstance3D.new()
	var t_cyl := CylinderMesh.new()
	t_cyl.top_radius = 0.08 * scale_factor
	t_cyl.bottom_radius = 0.02 * scale_factor
	t_cyl.height = 0.65 * scale_factor
	tail.mesh = t_cyl
	tail.position = Vector3(0, 0.65 * scale_factor, 0.75 * scale_factor)
	tail.rotation_degrees = Vector3(-40, 0, 0)
	tail.set_surface_override_material(0, mat_fur)
	root.add_child(tail)

	return root


## 18. Faune Sauvage : Scarabée Obsidien Géant (Carapace Dôme & Mandibules)
static func build_beetle_creature(pos: Vector3) -> Node3D:
	var root := Node3D.new()
	root.position = pos

	var mat_shell := StandardMaterial3D.new()
	mat_shell.albedo_color = Color(0.12, 0.12, 0.14)
	mat_shell.metallic = 0.75
	mat_shell.roughness = 0.3

	# Carapace bombée
	var shell := MeshInstance3D.new()
	var sph := SphereMesh.new()
	sph.radius = 1.1
	sph.height = 1.0
	shell.mesh = sph
	shell.position = Vector3(0, 0.6, 0)
	shell.scale = Vector3(1.0, 0.7, 1.4)
	shell.set_surface_override_material(0, mat_shell)
	root.add_child(shell)

	# Mandibules dorées
	var mat_mand := StandardMaterial3D.new()
	mat_mand.albedo_color = Color(0.85, 0.65, 0.15)
	for mx in [-0.35, 0.35]:
		var mand := MeshInstance3D.new()
		var p_mesh := PrismMesh.new()
		p_mesh.size = Vector3(0.2, 0.5, 0.1)
		mand.mesh = p_mesh
		mand.position = Vector3(mx, 0.45, -1.35)
		mand.rotation_degrees = Vector3(70, mx * -30.0, 0)
		mand.set_surface_override_material(0, mat_mand)
		root.add_child(mand)

	# 6 Pattes arquées
	for lx in [-0.9, 0.9]:
		for lz in [-0.6, 0.0, 0.6]:
			var leg := MeshInstance3D.new()
			var l_cyl := CylinderMesh.new()
			l_cyl.top_radius = 0.08
			l_cyl.bottom_radius = 0.04
			l_cyl.height = 0.85
			leg.mesh = l_cyl
			leg.position = Vector3(lx, 0.35, lz)
			leg.rotation_degrees = Vector3(0, 0, 45.0 if lx > 0 else -45.0)
			leg.set_surface_override_material(0, mat_shell)
			root.add_child(leg)

	return root


## 19. Marcheur des Dunes Géant (Faune Dewback / Bantha quadrupède herbivore)
static func build_dune_walker_creature(pos: Vector3) -> CharacterBody3D:
	var body := CharacterBody3D.new()
	body.name = "Dune_Walker_Dewback"
	body.position = pos
	body.set_meta("entity_kind", "creature_dewback")
	body.set_meta("display_name", "Marcheur des Dunes (Herbivore)")

	var mat_skin := StandardMaterial3D.new()
	mat_skin.albedo_color = Color(0.48, 0.52, 0.35, 1.0) # Vert écailleux désertique
	mat_skin.roughness = 0.9

	var mat_saddle := StandardMaterial3D.new()
	mat_saddle.albedo_color = Color(0.45, 0.28, 0.18) # Cuir brun

	# Corps massif
	var torso := MeshInstance3D.new()
	var t_box := BoxMesh.new()
	t_box.size = Vector3(2.2, 1.8, 4.5)
	torso.mesh = t_box
	torso.position = Vector3(0, 1.8, 0)
	torso.set_surface_override_material(0, mat_skin)
	body.add_child(torso)

	# Tête basse
	var head := MeshInstance3D.new()
	var h_box := BoxMesh.new()
	h_box.size = Vector3(1.4, 1.2, 2.0)
	head.mesh = h_box
	head.position = Vector3(0, 1.5, -2.8)
	head.set_surface_override_material(0, mat_skin)
	body.add_child(head)

	# Selle de monture sur le dos
	var saddle := MeshInstance3D.new()
	var s_box := BoxMesh.new()
	s_box.size = Vector3(1.8, 0.3, 2.2)
	s_box.size = Vector3(1.8, 0.3, 2.2)
	saddle.mesh = s_box
	saddle.position = Vector3(0, 2.8, -0.2)
	saddle.set_surface_override_material(0, mat_saddle)
	body.add_child(saddle)

	# 4 Pattes massives
	for lz in [-1.5, 1.5]:
		for lx in [-1.0, 1.0]:
			var leg := MeshInstance3D.new()
			var l_cyl := CylinderMesh.new()
			l_cyl.top_radius = 0.35
			l_cyl.bottom_radius = 0.45
			l_cyl.height = 1.6
			leg.mesh = l_cyl
			leg.position = Vector3(lx, 0.8, lz)
			leg.set_surface_override_material(0, mat_skin)
			body.add_child(leg)

	# Queue
	var tail := MeshInstance3D.new()
	var tl_cyl := CylinderMesh.new()
	tl_cyl.top_radius = 0.25
	tl_cyl.bottom_radius = 0.05
	tl_cyl.height = 2.4
	tail.mesh = tl_cyl
	tail.position = Vector3(0, 1.2, 3.2)
	tail.rotation_degrees = Vector3(-35, 0, 0)
	tail.set_surface_override_material(0, mat_skin)
	body.add_child(tail)

	var col := CollisionShape3D.new()
	var c_box := BoxShape3D.new()
	c_box.size = Vector3(2.5, 2.5, 5.0)
	col.shape = c_box
	col.position = Vector3(0, 1.8, 0)
	body.add_child(col)

	var lbl := Label3D.new()
	lbl.text = "◈ Marcheur des Dunes (Adulte) ◈\n« Faune Sauvage Domptable • Creature Handler »"
	lbl.position = Vector3(0, 3.4, 0)
	lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lbl.font_size = 14
	lbl.modulate = Color(0.85, 0.95, 0.7)
	body.add_child(lbl)

	return body


## 20. Modèle visuel de Monture Dewback pour le Joueur (attachable sous le contrôleur)
static func build_dewback_mount_visual(yaw_deg: float = 0.0) -> Node3D:
	var root := Node3D.new()
	root.name = "MountedDewbackVisual"
	root.rotation_degrees.y = yaw_deg
	root.position = Vector3(0, -2.5, 0.2) # Aligne le joueur sur la selle

	var mat_skin := StandardMaterial3D.new()
	mat_skin.albedo_color = Color(0.48, 0.52, 0.35, 1.0)
	mat_skin.roughness = 0.9

	var mat_saddle := StandardMaterial3D.new()
	mat_saddle.albedo_color = Color(0.45, 0.28, 0.18)

	var torso := MeshInstance3D.new()
	var t_box := BoxMesh.new()
	t_box.size = Vector3(2.2, 1.8, 4.5)
	torso.mesh = t_box
	torso.position = Vector3(0, 1.8, 0)
	torso.set_surface_override_material(0, mat_skin)
	root.add_child(torso)

	var head := MeshInstance3D.new()
	var h_box := BoxMesh.new()
	h_box.size = Vector3(1.4, 1.2, 2.0)
	head.mesh = h_box
	head.position = Vector3(0, 1.5, -2.8)
	head.set_surface_override_material(0, mat_skin)
	root.add_child(head)

	var saddle := MeshInstance3D.new()
	var s_box := BoxMesh.new()
	s_box.size = Vector3(1.8, 0.3, 2.2)
	saddle.mesh = s_box
	saddle.position = Vector3(0, 2.8, -0.2)
	saddle.set_surface_override_material(0, mat_saddle)
	root.add_child(saddle)

	for lz in [-1.5, 1.5]:
		for lx in [-1.0, 1.0]:
			var leg := MeshInstance3D.new()
			var l_cyl := CylinderMesh.new()
			l_cyl.top_radius = 0.35
			l_cyl.bottom_radius = 0.45
			l_cyl.height = 1.6
			leg.mesh = l_cyl
			leg.position = Vector3(lx, 0.8, lz)
			leg.set_surface_override_material(0, mat_skin)
			root.add_child(leg)

	var tail := MeshInstance3D.new()
	var tl_cyl := CylinderMesh.new()
	tl_cyl.top_radius = 0.25
	tl_cyl.bottom_radius = 0.05
	tl_cyl.height = 2.4
	tail.mesh = tl_cyl
	tail.position = Vector3(0, 1.2, 3.2)
	tail.rotation_degrees = Vector3(-35, 0, 0)
	tail.set_surface_override_material(0, mat_skin)
	root.add_child(tail)

	return root


## Construit un Campement de Nomades Tuskens (Pillards des Sables SWG)
static func build_tusken_camp(pos: Vector3) -> Node3D:
	var camp := Node3D.new()
	camp.name = "Camp_Tusken_Nomade"
	camp.position = pos

	var mat_leather := StandardMaterial3D.new()
	mat_leather.albedo_color = Color(0.48, 0.38, 0.28)
	mat_leather.roughness = 0.95

	var mat_wood := StandardMaterial3D.new()
	mat_wood.albedo_color = Color(0.32, 0.24, 0.16)

	var mat_fire := StandardMaterial3D.new()
	mat_fire.albedo_color = Color(1.0, 0.45, 0.1)
	mat_fire.emission_enabled = true
	mat_fire.emission = Color(1.0, 0.45, 0.1)
	mat_fire.emission_energy_multiplier = 4.0

	# 1. Hutte principale conique en cuir
	for offset_h in [Vector3(-4.5, 0, -3.0), Vector3(4.0, 0, 3.5)]:
		var hut := MeshInstance3D.new()
		var cone := CylinderMesh.new()
		cone.top_radius = 0.2
		cone.bottom_radius = 3.2
		cone.height = 3.6
		hut.mesh = cone
		hut.position = offset_h + Vector3(0, 1.8, 0)
		hut.set_surface_override_material(0, mat_leather)
		camp.add_child(hut)

	# 2. Feu de camp central du clan
	var fire := MeshInstance3D.new()
	var fc := CylinderMesh.new()
	fc.top_radius = 0.1
	fc.bottom_radius = 0.8
	fc.height = 0.6
	fire.mesh = fc
	fire.position = Vector3(0, 0.3, 0)
	fire.set_surface_override_material(0, mat_fire)
	camp.add_child(fire)

	var fire_light := OmniLight3D.new()
	fire_light.position = Vector3(0, 1.2, 0)
	fire_light.light_color = Color(1.0, 0.5, 0.15)
	fire_light.light_energy = 3.0
	fire_light.omni_range = 10.0
	camp.add_child(fire_light)

	# 3. Totems de guerre Gaffi
	for tx in [-6.0, 6.0]:
		var totem := MeshInstance3D.new()
		var cyl := CylinderMesh.new()
		cyl.top_radius = 0.1
		cyl.bottom_radius = 0.15
		cyl.height = 3.8
		totem.mesh = cyl
		totem.position = Vector3(tx, 1.9, 0)
		totem.set_surface_override_material(0, mat_wood)
		camp.add_child(totem)

	var lbl := Label3D.new()
	lbl.text = "☠ CAMPEMENT TUSKEN NOMADE ☠\n« Territoire Hostile des Pillards des Sables »"
	lbl.position = Vector3(0, 4.2, 0)
	lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lbl.font_size = 14
	lbl.modulate = Color(1.0, 0.35, 0.25)
	camp.add_child(lbl)

	return camp


## Modèle visuel 3D d'un Pillard Tusken (Masque respirateur, robe et bâton Gaffi)
static func build_tusken_raider_visual(_col_accent: Color = Color(0.75, 0.6, 0.45)) -> Node3D:
	var root := Node3D.new()
	root.name = "Tusken_Visual"

	var mat_robe := StandardMaterial3D.new()
	mat_robe.albedo_color = Color(0.68, 0.58, 0.45)
	mat_robe.roughness = 0.9

	var mat_metal := StandardMaterial3D.new()
	mat_metal.albedo_color = Color(0.35, 0.35, 0.38)
	mat_metal.metallic = 0.8
	mat_metal.roughness = 0.4

	# Robe / Corps principal
	var body := MeshInstance3D.new()
	var b_cap := CapsuleMesh.new()
	b_cap.radius = 0.42
	b_cap.height = 1.6
	body.mesh = b_cap
	body.position = Vector3(0, 0.8, 0)
	body.set_surface_override_material(0, mat_robe)
	root.add_child(body)

	# Tête avec bandelettes
	var head := MeshInstance3D.new()
	var h_sph := SphereMesh.new()
	h_sph.radius = 0.26
	h_sph.height = 0.52
	head.mesh = h_sph
	head.position = Vector3(0, 1.6, 0)
	head.set_surface_override_material(0, mat_robe)
	root.add_child(head)

	# Yeux cylindriques métalliques (Optiques de vision Tusken)
	for ex in [-0.09, 0.09]:
		var eye := MeshInstance3D.new()
		var eye_cyl := CylinderMesh.new()
		eye_cyl.top_radius = 0.04
		eye_cyl.bottom_radius = 0.04
		eye_cyl.height = 0.15
		eye.mesh = eye_cyl
		eye.position = Vector3(ex, 1.65, -0.22)
		eye.rotation_degrees = Vector3(90, 0, 0)
		eye.set_surface_override_material(0, mat_metal)
		root.add_child(eye)

	# Buse respirateur centrale de bouche
	var resp := MeshInstance3D.new()
	var r_cyl := CylinderMesh.new()
	r_cyl.top_radius = 0.05
	r_cyl.bottom_radius = 0.07
	r_cyl.height = 0.18
	resp.mesh = r_cyl
	resp.position = Vector3(0, 1.5, -0.24)
	resp.rotation_degrees = Vector3(90, 0, 0)
	resp.set_surface_override_material(0, mat_metal)
	root.add_child(resp)

	# Bâton Gaffi (Gaderffii) en main
	var gaffi := MeshInstance3D.new()
	var g_cyl := CylinderMesh.new()
	g_cyl.top_radius = 0.03
	g_cyl.bottom_radius = 0.03
	g_cyl.height = 1.9
	gaffi.mesh = g_cyl
	gaffi.position = Vector3(0.55, 0.95, -0.2)
	gaffi.rotation_degrees = Vector3(25, 0, -15)
	gaffi.set_surface_override_material(0, mat_metal)
	root.add_child(gaffi)

	return root


## Construit un Bantha à cornes géantes pour la Caravane de bât marchande
static func build_caravan_bantha(pos: Vector3) -> Node3D:
	var bantha := Node3D.new()
	bantha.name = "Bantha_Caravane"
	bantha.position = pos

	var mat_fur := StandardMaterial3D.new()
	mat_fur.albedo_color = Color(0.38, 0.28, 0.2)
	mat_fur.roughness = 1.0

	var mat_horn := StandardMaterial3D.new()
	mat_horn.albedo_color = Color(0.75, 0.72, 0.6)
	mat_horn.roughness = 0.6

	var mat_cargo := StandardMaterial3D.new()
	mat_cargo.albedo_color = Color(0.55, 0.42, 0.25)

	# Corps massif et velu
	var body := MeshInstance3D.new()
	var b_box := BoxMesh.new()
	b_box.size = Vector3(3.2, 2.4, 4.8)
	body.mesh = b_box
	body.position = Vector3(0, 2.0, 0)
	body.set_surface_override_material(0, mat_fur)
	bantha.add_child(body)

	# Tête lourde
	var head := MeshInstance3D.new()
	var h_box := BoxMesh.new()
	h_box.size = Vector3(2.0, 1.8, 2.2)
	head.mesh = h_box
	head.position = Vector3(0, 1.8, -3.0)
	head.set_surface_override_material(0, mat_fur)
	bantha.add_child(head)

	# Deux grandes cornes incurvées en spirale
	for hx in [-1.4, 1.4]:
		var horn := MeshInstance3D.new()
		var tor := TorusMesh.new()
		tor.inner_radius = 0.8
		tor.outer_radius = 1.2
		horn.mesh = tor
		horn.position = Vector3(hx, 2.4, -2.8)
		horn.rotation_degrees = Vector3(0, 90, 45 if hx > 0 else -45)
		horn.set_surface_override_material(0, mat_horn)
		bantha.add_child(horn)

	# Caisses de bât de marchandises sur le dos
	var cargo := MeshInstance3D.new()
	var c_box := BoxMesh.new()
	c_box.size = Vector3(2.4, 1.2, 2.6)
	cargo.mesh = c_box
	cargo.position = Vector3(0, 3.6, 0)
	cargo.set_surface_override_material(0, mat_cargo)
	bantha.add_child(cargo)

	# 4 pattes massives
	for lz in [-1.5, 1.5]:
		for lx in [-1.2, 1.2]:
			var leg := MeshInstance3D.new()
			var l_cyl := CylinderMesh.new()
			l_cyl.top_radius = 0.45
			l_cyl.bottom_radius = 0.55
			l_cyl.height = 1.8
			leg.mesh = l_cyl
			leg.position = Vector3(lx, 0.9, lz)
			leg.set_surface_override_material(0, mat_fur)
			bantha.add_child(leg)

	return bantha


## Modèle 3D de Stormtrooper Impérial SWG Pre-CU
static func build_stormtrooper_visual(is_officer: bool = false) -> Node3D:
	var trooper := Node3D.new()
	trooper.name = "Stormtrooper_Visual"

	var mat_armor := StandardMaterial3D.new()
	mat_armor.albedo_color = Color(0.96, 0.96, 0.98) # Plastron blanc
	mat_armor.roughness = 0.25
	mat_armor.metallic = 0.15

	var mat_black := StandardMaterial3D.new()
	mat_black.albedo_color = Color(0.08, 0.08, 0.1) # Combinaison sous-armure
	mat_black.roughness = 0.8

	# Corps / Plastron
	var torso := MeshInstance3D.new()
	var t_box := BoxMesh.new()
	t_box.size = Vector3(0.5, 0.65, 0.3)
	torso.mesh = t_box
	torso.position = Vector3(0, 1.15, 0)
	torso.set_surface_override_material(0, mat_armor)
	trooper.add_child(torso)

	# Casque emblématique
	var helmet := MeshInstance3D.new()
	var h_mesh := BoxMesh.new()
	h_mesh.size = Vector3(0.32, 0.35, 0.32)
	helmet.mesh = h_mesh
	helmet.position = Vector3(0, 1.62, 0)
	helmet.set_surface_override_material(0, mat_armor)
	trooper.add_child(helmet)

	# Visière sombre
	var visor := MeshInstance3D.new()
	var v_box := BoxMesh.new()
	v_box.size = Vector3(0.24, 0.08, 0.05)
	visor.mesh = v_box
	visor.position = Vector3(0, 1.62, 0.16)
	var mat_vis := StandardMaterial3D.new()
	mat_vis.albedo_color = Color(0.02, 0.02, 0.04)
	visor.set_surface_override_material(0, mat_vis)
	trooper.add_child(visor)

	# Épaulière d'officier orange si applicable
	if is_officer:
		var pldrn := MeshInstance3D.new()
		var p_box := BoxMesh.new()
		p_box.size = Vector3(0.18, 0.15, 0.22)
		pldrn.mesh = p_box
		pldrn.position = Vector3(-0.32, 1.45, 0)
		var mat_p := StandardMaterial3D.new()
		mat_p.albedo_color = Color(0.95, 0.45, 0.1) # Orange Commandant
		pldrn.set_surface_override_material(0, mat_p)
		trooper.add_child(pldrn)

	# Bras et Blaster E-11
	for sx in [-0.28, 0.28]:
		var arm := MeshInstance3D.new()
		var a_cyl := CylinderMesh.new()
		a_cyl.top_radius = 0.08
		a_cyl.bottom_radius = 0.07
		a_cyl.height = 0.6
		arm.mesh = a_cyl
		arm.position = Vector3(sx, 1.15, 0)
		arm.set_surface_override_material(0, mat_black)
		trooper.add_child(arm)

	# Blaster E-11 braqué en avant
	var blaster := MeshInstance3D.new()
	var b_box := BoxMesh.new()
	b_box.size = Vector3(0.08, 0.12, 0.5)
	blaster.mesh = b_box
	blaster.position = Vector3(0.2, 1.1, 0.35)
	blaster.set_surface_override_material(0, mat_black)
	trooper.add_child(blaster)

	# Jambes protégées
	for lx in [-0.14, 0.14]:
		var leg := MeshInstance3D.new()
		var l_cyl := CylinderMesh.new()
		l_cyl.top_radius = 0.1
		l_cyl.bottom_radius = 0.09
		l_cyl.height = 0.8
		leg.mesh = l_cyl
		leg.position = Vector3(lx, 0.4, 0)
		leg.set_surface_override_material(0, mat_armor)
		trooper.add_child(leg)

	return trooper


## Modèle 3D de Soldat de l'Alliance Rebelle SWG Pre-CU
static func build_rebel_soldier_visual(is_commando: bool = false) -> Node3D:
	var rebel := Node3D.new()
	rebel.name = "RebelSoldier_Visual"

	var mat_vest := StandardMaterial3D.new()
	mat_vest.albedo_color = Color(0.38, 0.44, 0.32) if not is_commando else Color(0.25, 0.28, 0.32) # Treillis kaki/gris
	mat_vest.roughness = 0.8

	var mat_helmet := StandardMaterial3D.new()
	mat_helmet.albedo_color = Color(0.85, 0.82, 0.72) # Casque beige / blanc de l'Alliance
	mat_helmet.roughness = 0.5

	var mat_pants := StandardMaterial3D.new()
	mat_pants.albedo_color = Color(0.48, 0.42, 0.34)

	# Torse
	var torso := MeshInstance3D.new()
	var t_box := BoxMesh.new()
	t_box.size = Vector3(0.48, 0.65, 0.28)
	torso.mesh = t_box
	torso.position = Vector3(0, 1.15, 0)
	torso.set_surface_override_material(0, mat_vest)
	rebel.add_child(torso)

	# Casque de combat à visière évasée
	var helm := MeshInstance3D.new()
	var h_cyl := CylinderMesh.new()
	h_cyl.top_radius = 0.18
	h_cyl.bottom_radius = 0.26
	h_cyl.height = 0.25
	helm.mesh = h_cyl
	helm.position = Vector3(0, 1.65, 0)
	helm.set_surface_override_material(0, mat_helmet)
	rebel.add_child(helm)

	# Fusil blaster DH-17
	var rifle := MeshInstance3D.new()
	var r_box := BoxMesh.new()
	r_box.size = Vector3(0.08, 0.14, 0.65)
	rifle.mesh = r_box
	rifle.position = Vector3(0.22, 1.15, 0.38)
	var mat_gun := StandardMaterial3D.new()
	mat_gun.albedo_color = Color(0.12, 0.12, 0.15)
	mat_gun.metallic = 0.8
	rifle.set_surface_override_material(0, mat_gun)
	rebel.add_child(rifle)

	# Jambes
	for lx in [-0.14, 0.14]:
		var leg := MeshInstance3D.new()
		var l_cyl := CylinderMesh.new()
		l_cyl.top_radius = 0.1
		l_cyl.bottom_radius = 0.08
		l_cyl.height = 0.8
		leg.mesh = l_cyl
		leg.position = Vector3(lx, 0.4, 0)
		leg.set_surface_override_material(0, mat_pants)
		rebel.add_child(leg)

	return rebel


## Tourelle de Défense Factionnelle Automatique (Turret) SWG Pre-CU
static func build_faction_turret(pos: Vector3, faction_type: String = "imperial") -> Node3D:
	var turret := Node3D.new()
	turret.name = "FactionTurret_%s" % faction_type
	turret.position = pos

	var col_base := Color(0.85, 0.85, 0.9) if faction_type == "imperial" else Color(0.4, 0.45, 0.38)
	var mat_t := StandardMaterial3D.new()
	mat_t.albedo_color = col_base
	mat_t.metallic = 0.8
	mat_t.roughness = 0.3

	# Base pyramidale
	var base := MeshInstance3D.new()
	var b_cyl := CylinderMesh.new()
	b_cyl.top_radius = 0.9
	b_cyl.bottom_radius = 1.4
	b_cyl.height = 1.2
	base.mesh = b_cyl
	base.position = Vector3(0, 0.6, 0)
	base.set_surface_override_material(0, mat_t)
	turret.add_child(base)

	# Dôme rotatif de visée
	var dome := MeshInstance3D.new()
	var d_sph := SphereMesh.new()
	d_sph.radius = 0.75
	d_sph.height = 0.9
	dome.mesh = d_sph
	dome.position = Vector3(0, 1.4, 0)
	dome.set_surface_override_material(0, mat_t)
	turret.add_child(dome)

	# Double canon laser
	for cx in [-0.25, 0.25]:
		var barrel := MeshInstance3D.new()
		var b_mesh := CylinderMesh.new()
		b_mesh.top_radius = 0.08
		b_mesh.bottom_radius = 0.09
		b_mesh.height = 1.8
		barrel.mesh = b_mesh
		barrel.rotation_degrees = Vector3(90, 0, 0)
		barrel.position = Vector3(cx, 1.4, 0.9)
		var mat_b := StandardMaterial3D.new()
		mat_b.albedo_color = Color(0.1, 0.1, 0.12)
		mat_b.metallic = 0.9
		barrel.set_surface_override_material(0, mat_b)
		turret.add_child(barrel)

	# Voyant radar de détection
	var light := OmniLight3D.new()
	light.position = Vector3(0, 1.8, 0)
	light.light_color = Color(1.0, 0.2, 0.1) if faction_type == "imperial" else Color(0.2, 0.9, 0.3)
	light.light_energy = 2.0
	light.omni_range = 5.0
	turret.add_child(light)

	return turret


## Modèle 3D de Sabre Laser déployable (Lightsaber)
static func build_lightsaber_mesh(blade_color: String = "blue") -> Node3D:
	var saber := Node3D.new()
	saber.name = "Lightsaber"

	# Manche métallique chromé
	var hilt := MeshInstance3D.new()
	var h_cyl := CylinderMesh.new()
	h_cyl.top_radius = 0.035
	h_cyl.bottom_radius = 0.035
	h_cyl.height = 0.32
	hilt.mesh = h_cyl
	hilt.position = Vector3(0, 0.16, 0)
	var mat_hilt := StandardMaterial3D.new()
	mat_hilt.albedo_color = Color(0.85, 0.88, 0.92)
	mat_hilt.metallic = 0.95
	mat_hilt.roughness = 0.2
	hilt.set_surface_override_material(0, mat_hilt)
	saber.add_child(hilt)

	# Anneaux noirs antidérapants
	for ry in [0.08, 0.14, 0.20]:
		var ring := MeshInstance3D.new()
		var r_tor := TorusMesh.new()
		r_tor.inner_radius = 0.036
		r_tor.outer_radius = 0.042
		ring.mesh = r_tor
		ring.position = Vector3(0, ry, 0)
		var mat_r := StandardMaterial3D.new()
		mat_r.albedo_color = Color(0.12, 0.12, 0.15)
		ring.set_surface_override_material(0, mat_r)
		saber.add_child(ring)

	# Lame d'énergie pure émissive
	var blade := MeshInstance3D.new()
	blade.name = "EnergyBlade"
	var b_cyl := CylinderMesh.new()
	b_cyl.top_radius = 0.025
	b_cyl.bottom_radius = 0.028
	b_cyl.height = 1.25
	blade.mesh = b_cyl
	blade.position = Vector3(0, 0.32 + 0.625, 0)

	var col := Color(0.15, 0.6, 1.0)
	match blade_color.to_lower():
		"green": col = Color(0.2, 1.0, 0.35)
		"red": col = Color(1.0, 0.15, 0.15)
		"purple": col = Color(0.85, 0.25, 1.0)
		"yellow": col = Color(1.0, 0.9, 0.2)

	var mat_b := StandardMaterial3D.new()
	mat_b.albedo_color = Color.WHITE
	mat_b.emission_enabled = true
	mat_b.emission = col
	mat_b.emission_energy_multiplier = 6.0
	blade.set_surface_override_material(0, mat_b)
	saber.add_child(blade)

	# Lumière dynamique projetée par la lame
	var light := OmniLight3D.new()
	light.position = Vector3(0, 0.95, 0)
	light.light_color = col
	light.light_energy = 3.5
	light.omni_range = 6.0
	saber.add_child(light)

	return saber


## Modèle 3D de Droïde Sonde Impérial Arakyd (Arakyd Probe Droid)
static func build_arakyd_probe_droid(pos: Vector3) -> Node3D:
	var droid := Node3D.new()
	droid.name = "ArakydProbeDroid"
	droid.position = pos

	var mat_dark := StandardMaterial3D.new()
	mat_dark.albedo_color = Color(0.12, 0.13, 0.15)
	mat_dark.metallic = 0.85
	mat_dark.roughness = 0.35

	# Tête sphérique principale
	var head := MeshInstance3D.new()
	var h_sph := SphereMesh.new()
	h_sph.radius = 0.6
	h_sph.height = 1.1
	head.mesh = h_sph
	head.position = Vector3(0, 2.2, 0)
	head.set_surface_override_material(0, mat_dark)
	droid.add_child(head)

	# Capteurs et photorécepteurs rouges lumineux
	var eye := MeshInstance3D.new()
	var e_sph := SphereMesh.new()
	e_sph.radius = 0.14
	e_sph.height = 0.18
	eye.mesh = e_sph
	eye.position = Vector3(0, 2.3, 0.55)
	var mat_eye := StandardMaterial3D.new()
	mat_eye.albedo_color = Color(1.0, 0.1, 0.1)
	mat_eye.emission_enabled = true
	mat_eye.emission = Color(1.0, 0.1, 0.1)
	mat_eye.emission_energy_multiplier = 4.0
	eye.set_surface_override_material(0, mat_eye)
	droid.add_child(eye)

	# 3 Bras articulés inférieurs
	for angle_deg in [0, 120, 240]:
		var arm := MeshInstance3D.new()
		var a_cyl := CylinderMesh.new()
		a_cyl.top_radius = 0.05
		a_cyl.bottom_radius = 0.04
		a_cyl.height = 0.9
		arm.mesh = a_cyl
		var rad := deg_to_rad(angle_deg)
		arm.position = Vector3(cos(rad) * 0.35, 1.4, sin(rad) * 0.35)
		arm.rotation_degrees = Vector3(15 * sin(rad), 0, -15 * cos(rad))
		arm.set_surface_override_material(0, mat_dark)
		droid.add_child(arm)

	# Antenne de transmission hyperspatiale
	var ant := MeshInstance3D.new()
	var a_mesh := CylinderMesh.new()
	a_mesh.top_radius = 0.02
	a_mesh.bottom_radius = 0.03
	a_mesh.height = 1.2
	ant.mesh = a_mesh
	ant.position = Vector3(0.25, 3.2, -0.2)
	ant.set_surface_override_material(0, mat_dark)
	droid.add_child(ant)

	return droid


## Modèle 3D de Chasseur Incom T-65B X-Wing (JTL)
static func build_xwing_starfighter(pos: Vector3, yaw_deg: float = 0.0) -> Node3D:
	var ship := Node3D.new()
	ship.name = "XWing_T65"
	ship.position = pos
	ship.rotation_degrees.y = yaw_deg

	var mat_white := StandardMaterial3D.new()
	mat_white.albedo_color = Color(0.88, 0.90, 0.92)
	mat_white.metallic = 0.4
	mat_white.roughness = 0.4

	var mat_red := StandardMaterial3D.new()
	mat_red.albedo_color = Color(0.85, 0.15, 0.12)

	# Fuselage principal allongé
	var body := MeshInstance3D.new()
	var b_box := BoxMesh.new()
	b_box.size = Vector3(1.6, 1.2, 9.5)
	body.mesh = b_box
	body.position = Vector3(0, 0.6, 0)
	body.set_surface_override_material(0, mat_white)
	ship.add_child(body)

	# Nez pointu
	var nose := MeshInstance3D.new()
	var n_box := BoxMesh.new()
	n_box.size = Vector3(1.1, 0.8, 3.2)
	nose.mesh = n_box
	nose.position = Vector3(0, 0.5, -5.5)
	nose.set_surface_override_material(0, mat_white)
	ship.add_child(nose)

	# Bandes rouges d'escadron (Red Five)
	var stripe := MeshInstance3D.new()
	var s_box := BoxMesh.new()
	s_box.size = Vector3(1.65, 0.2, 1.4)
	stripe.mesh = s_box
	stripe.position = Vector3(0, 1.15, -2.0)
	stripe.set_surface_override_material(0, mat_red)
	ship.add_child(stripe)

	# 4 Ailes en configuration d'attaque en X (S-Foils deployed)
	for side in [-1, 1]:
		for vertical in [-1, 1]:
			var wing := MeshInstance3D.new()
			var w_box := BoxMesh.new()
			w_box.size = Vector3(4.8, 0.12, 2.2)
			wing.mesh = w_box
			wing.position = Vector3(side * 2.8, 0.6 + vertical * 0.75, 1.0)
			wing.rotation_degrees.z = side * vertical * 14.0 # Angle S-Foil en X
			wing.set_surface_override_material(0, mat_white)
			ship.add_child(wing)

			# Canon laser au bout de chaque aile
			var cannon := MeshInstance3D.new()
			var c_cyl := CylinderMesh.new()
			c_cyl.top_radius = 0.06
			c_cyl.bottom_radius = 0.08
			c_cyl.height = 4.2
			cannon.mesh = c_cyl
			cannon.rotation_degrees = Vector3(90, 0, 0)
			cannon.position = Vector3(side * 5.2, 0.6 + vertical * 1.35, -0.6)
			var mat_c := StandardMaterial3D.new()
			mat_c.albedo_color = Color(0.2, 0.22, 0.25)
			mat_c.metallic = 0.9
			cannon.set_surface_override_material(0, mat_c)
			ship.add_child(cannon)

	# 4 Moteurs à sub-illumination ioniques avec lueur rose/rouge
	for ex in [-0.75, 0.75]:
		for ey in [0.25, 0.95]:
			var engine := MeshInstance3D.new()
			var e_cyl := CylinderMesh.new()
			e_cyl.top_radius = 0.35
			e_cyl.bottom_radius = 0.35
			e_cyl.height = 2.4
			engine.mesh = e_cyl
			engine.rotation_degrees = Vector3(90, 0, 0)
			engine.position = Vector3(ex, ey, 3.8)
			engine.set_surface_override_material(0, mat_white)
			ship.add_child(engine)

			var glow := OmniLight3D.new()
			glow.position = Vector3(ex, ey, 5.1)
			glow.light_color = Color(1.0, 0.4, 0.6)
			glow.light_energy = 2.5
			glow.omni_range = 4.0
			ship.add_child(glow)

	return ship


## Modèle 3D de Chasseur TIE/ln Sienar (JTL)
static func build_tiefighter_starfighter(pos: Vector3, yaw_deg: float = 0.0) -> Node3D:
	var tie := Node3D.new()
	tie.name = "TIEFighter_LN"
	tie.position = pos
	tie.rotation_degrees.y = yaw_deg

	var mat_hull := StandardMaterial3D.new()
	mat_hull.albedo_color = Color(0.65, 0.68, 0.72)
	mat_hull.metallic = 0.8
	mat_hull.roughness = 0.3

	var mat_panel := StandardMaterial3D.new()
	mat_panel.albedo_color = Color(0.08, 0.09, 0.1)
	mat_panel.roughness = 0.8

	# Cockpit sphérique central
	var pod := MeshInstance3D.new()
	var p_sph := SphereMesh.new()
	p_sph.radius = 1.1
	p_sph.height = 2.2
	pod.mesh = p_sph
	pod.position = Vector3(0, 1.2, 0)
	pod.set_surface_override_material(0, mat_hull)
	tie.add_child(pod)

	# Hublot avant polygonal
	var glass := MeshInstance3D.new()
	var g_cyl := CylinderMesh.new()
	g_cyl.top_radius = 0.55
	g_cyl.bottom_radius = 0.55
	g_cyl.height = 0.25
	glass.mesh = g_cyl
	glass.rotation_degrees = Vector3(90, 0, 0)
	glass.position = Vector3(0, 1.2, -1.05)
	var mat_g := StandardMaterial3D.new()
	mat_g.albedo_color = Color(0.1, 0.12, 0.15)
	mat_g.roughness = 0.1
	glass.set_surface_override_material(0, mat_g)
	tie.add_child(glass)

	# 2 Pylônes d'ailes et 2 Grands Panneaux Solaires Hexagonaux
	for side in [-1, 1]:
		var pylon := MeshInstance3D.new()
		var py_cyl := CylinderMesh.new()
		py_cyl.top_radius = 0.22
		py_cyl.bottom_radius = 0.22
		py_cyl.height = 2.8
		pylon.mesh = py_cyl
		pylon.rotation_degrees = Vector3(0, 0, 90)
		pylon.position = Vector3(side * 2.2, 1.2, 0)
		pylon.set_surface_override_material(0, mat_hull)
		tie.add_child(pylon)

		# Panneau hexagonal
		var wing := MeshInstance3D.new()
		var w_box := BoxMesh.new()
		w_box.size = Vector3(0.15, 6.5, 5.5)
		wing.mesh = w_box
		wing.position = Vector3(side * 3.6, 1.2, 0)
		wing.set_surface_override_material(0, mat_panel)
		tie.add_child(wing)

	# 2 Canons laser mentonniers verts
	for cx in [-0.22, 0.22]:
		var gun := MeshInstance3D.new()
		var g_mesh := CylinderMesh.new()
		g_mesh.top_radius = 0.05
		g_mesh.bottom_radius = 0.06
		g_mesh.height = 0.6
		gun.mesh = g_mesh
		gun.rotation_degrees = Vector3(90, 0, 0)
		gun.position = Vector3(cx, 0.5, -1.1)
		var mat_gun := StandardMaterial3D.new()
		mat_gun.albedo_color = Color(0.2, 1.0, 0.3)
		mat_gun.emission_enabled = true
		mat_gun.emission = Color(0.2, 1.0, 0.3)
		gun.set_surface_override_material(0, mat_gun)
		tie.add_child(gun)

	return tie


## 16. Hôtel de Ville Civique (Player City Hall SWG)
static func build_city_hall(pos: Vector3, city_name: String = "New Coronet", yaw_deg: float = 0.0) -> Node3D:
	var hall := Node3D.new()
	hall.name = "CityHall_" + city_name.replace(" ", "_")
	hall.position = pos
	hall.rotation_degrees.y = yaw_deg

	var mat_marble := StandardMaterial3D.new()
	mat_marble.albedo_color = Color(0.85, 0.83, 0.78)
	mat_marble.roughness = 0.35

	var mat_gold := StandardMaterial3D.new()
	mat_gold.albedo_color = Color(0.9, 0.75, 0.2)
	mat_gold.metallic = 0.9
	mat_gold.roughness = 0.2

	var sb := StaticBody3D.new()

	# Base surélevée et perron
	var base := MeshInstance3D.new()
	var b_box := BoxMesh.new()
	b_box.size = Vector3(22.0, 1.2, 16.0)
	base.mesh = b_box
	base.position = Vector3(0, 0.6, 0)
	base.set_surface_override_material(0, mat_marble)
	sb.add_child(base)

	# Bâtiment principal avec hall d'assemblée
	var body := MeshInstance3D.new()
	var body_box := BoxMesh.new()
	body_box.size = Vector3(18.0, 7.0, 12.0)
	body.mesh = body_box
	body.position = Vector3(0, 4.7, 1.0)
	body.set_surface_override_material(0, mat_marble)
	sb.add_child(body)

	# Dôme doré central du Sénat municipal
	var dome := MeshInstance3D.new()
	var d_sph := SphereMesh.new()
	d_sph.radius = 4.0
	d_sph.height = 4.5
	dome.mesh = d_sph
	dome.position = Vector3(0, 8.8, 1.0)
	dome.set_surface_override_material(0, mat_gold)
	sb.add_child(dome)

	# 6 Colonnes majestueuses en façade
	for cx in [-7.5, -4.5, -1.5, 1.5, 4.5, 7.5]:
		var col := MeshInstance3D.new()
		var c_cyl := CylinderMesh.new()
		c_cyl.top_radius = 0.55
		c_cyl.bottom_radius = 0.65
		c_cyl.height = 6.2
		col.mesh = c_cyl
		col.position = Vector3(cx, 4.3, -5.8)
		col.set_surface_override_material(0, mat_marble)
		sb.add_child(col)

	hall.add_child(sb)

	# Enseigne municipale et terminal électoral
	var sign := Label3D.new()
	sign.text = "🏛 HÔTEL DE VILLE CIVIQUE 🏛\n« %s »\n[E] Voter pour le Maire & Consulter les Taxes" % city_name
	sign.position = Vector3(0, 6.8, -6.2)
	sign.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	sign.font_size = 20
	sign.modulate = Color(1.0, 0.85, 0.3)
	hall.add_child(sign)

	return hall


## 17. Incubateur de Bio-Ingénierie & Laboratoire Génétique
static func build_bio_incubator(pos: Vector3, yaw_deg: float = 0.0) -> Node3D:
	var lab := Node3D.new()
	lab.name = "Bio_Incubator_Lab"
	lab.position = pos
	lab.rotation_degrees.y = yaw_deg

	var mat_metal := StandardMaterial3D.new()
	mat_metal.albedo_color = Color(0.3, 0.35, 0.4)
	mat_metal.metallic = 0.8

	var mat_fluid := StandardMaterial3D.new()
	mat_fluid.albedo_color = Color(0.1, 0.95, 0.3, 0.6)
	mat_fluid.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat_fluid.emission_enabled = true
	mat_fluid.emission = Color(0.1, 0.95, 0.3)
	mat_fluid.emission_energy_multiplier = 2.0

	var sb := StaticBody3D.new()

	# Socle circulaire en acier lourd
	var base := MeshInstance3D.new()
	var b_cyl := CylinderMesh.new()
	b_cyl.top_radius = 1.4
	b_cyl.bottom_radius = 1.6
	b_cyl.height = 0.6
	base.mesh = b_cyl
	base.position = Vector3(0, 0.3, 0)
	base.set_surface_override_material(0, mat_metal)
	sb.add_child(base)

	# Cuve cylindrique en verre de confinement génétique
	var vat := MeshInstance3D.new()
	var v_cyl := CylinderMesh.new()
	v_cyl.top_radius = 1.1
	v_cyl.bottom_radius = 1.1
	v_cyl.height = 2.4
	vat.mesh = v_cyl
	vat.position = Vector3(0, 1.8, 0)
	vat.set_surface_override_material(0, mat_fluid)
	sb.add_child(vat)

	# Chapeau supérieur avec anneau de stimulation biochimique
	var cap := MeshInstance3D.new()
	var c_cyl := CylinderMesh.new()
	c_cyl.top_radius = 1.5
	c_cyl.bottom_radius = 1.3
	c_cyl.height = 0.5
	cap.mesh = c_cyl
	cap.position = Vector3(0, 3.2, 0)
	cap.set_surface_override_material(0, mat_metal)
	sb.add_child(cap)

	var light := OmniLight3D.new()
	light.position = Vector3(0, 1.8, 0)
	light.light_color = Color(0.1, 0.95, 0.3)
	light.light_energy = 3.0
	light.omni_range = 5.0
	sb.add_child(light)

	lab.add_child(sb)

	var label := Label3D.new()
	label.text = "🧪 INCUBATEUR BIO-INGÉNIEUR 🧪\n« Synthèse ADN & Chimères »"
	label.position = Vector3(0, 4.0, 0)
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.font_size = 18
	label.modulate = Color(0.3, 1.0, 0.4)
	lab.add_child(label)

	return lab


## 18. Droïde Astromécano Série R2 (Droid Engineer)
static func build_r2_astromech(pos: Vector3, yaw_deg: float = 0.0) -> Node3D:
	var r2 := Node3D.new()
	r2.name = "R2_Astromech_Droid"
	r2.position = pos
	r2.rotation_degrees.y = yaw_deg

	var mat_white := StandardMaterial3D.new()
	mat_white.albedo_color = Color(0.92, 0.93, 0.95)
	mat_white.roughness = 0.3

	var mat_blue := StandardMaterial3D.new()
	mat_blue.albedo_color = Color(0.1, 0.3, 0.8)
	mat_blue.metallic = 0.7

	# Corps cylindrique
	var body := MeshInstance3D.new()
	var b_cyl := CylinderMesh.new()
	b_cyl.top_radius = 0.42
	b_cyl.bottom_radius = 0.42
	b_cyl.height = 0.75
	body.mesh = b_cyl
	body.position = Vector3(0, 0.65, 0)
	body.set_surface_override_material(0, mat_white)
	r2.add_child(body)

	# Dôme pivotant semi-sphérique
	var dome := MeshInstance3D.new()
	var d_sph := SphereMesh.new()
	d_sph.radius = 0.42
	d_sph.height = 0.5
	dome.mesh = d_sph
	dome.position = Vector3(0, 1.05, 0)
	dome.set_surface_override_material(0, mat_blue)
	r2.add_child(dome)

	# Œil projecteur holographique rougeoyant
	var eye := MeshInstance3D.new()
	var e_cyl := CylinderMesh.new()
	e_cyl.top_radius = 0.08
	e_cyl.bottom_radius = 0.08
	e_cyl.height = 0.12
	eye.mesh = e_cyl
	eye.rotation_degrees = Vector3(90, 0, 0)
	eye.position = Vector3(0, 1.15, -0.4)
	var mat_eye := StandardMaterial3D.new()
	mat_eye.albedo_color = Color(1.0, 0.1, 0.1)
	mat_eye.emission_enabled = true
	mat_eye.emission = Color(1.0, 0.1, 0.1)
	eye.set_surface_override_material(0, mat_eye)
	r2.add_child(eye)

	# 2 Jambes latérales avec pieds montés sur roulettes
	for sx in [-0.55, 0.55]:
		var leg := MeshInstance3D.new()
		var l_box := BoxMesh.new()
		l_box.size = Vector3(0.14, 0.9, 0.22)
		leg.mesh = l_box
		leg.position = Vector3(sx, 0.55, 0)
		leg.set_surface_override_material(0, mat_white)
		r2.add_child(leg)

	# Petite roulette avant centrale
	var front_wheel := MeshInstance3D.new()
	var fw_sph := SphereMesh.new()
	fw_sph.radius = 0.12
	fw_sph.height = 0.24
	front_wheel.mesh = fw_sph
	front_wheel.position = Vector3(0, 0.12, -0.2)
	front_wheel.set_surface_override_material(0, mat_blue)
	r2.add_child(front_wheel)

	var label := Label3D.new()
	label.text = "🤖 R2-D2 (Astromécano)\n« Module Soute & Atelier Mobile »"
	label.position = Vector3(0, 1.5, 0)
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.font_size = 14
	label.modulate = Color(0.4, 0.8, 1.0)
	r2.add_child(label)

	return r2


## 19. Donjon de la Corvette Corellienne (Sas & Gyrophares)
static func build_corvette_airlock(pos: Vector3, yaw_deg: float = 0.0) -> Node3D:
	var airlock := Node3D.new()
	airlock.name = "Corvette_Airlock_Dungeon"
	airlock.position = pos
	airlock.rotation_degrees.y = yaw_deg

	var mat_armor := StandardMaterial3D.new()
	mat_armor.albedo_color = Color(0.7, 0.15, 0.15) # Rouge Corellien
	mat_armor.roughness = 0.5

	var mat_blastdoor := StandardMaterial3D.new()
	mat_blastdoor.albedo_color = Color(0.2, 0.22, 0.25)
	mat_blastdoor.metallic = 0.9

	var sb := StaticBody3D.new()

	# Cadre de sas pressurisé blindé
	var frame := MeshInstance3D.new()
	var f_box := BoxMesh.new()
	f_box.size = Vector3(6.5, 5.5, 3.0)
	frame.mesh = f_box
	frame.position = Vector3(0, 2.75, 0)
	frame.set_surface_override_material(0, mat_armor)
	sb.add_child(frame)

	# Porte de sas hermétique
	var door := MeshInstance3D.new()
	var d_box := BoxMesh.new()
	d_box.size = Vector3(3.5, 4.2, 0.3)
	door.mesh = d_box
	door.position = Vector3(0, 2.1, -1.4)
	door.set_surface_override_material(0, mat_blastdoor)
	sb.add_child(door)

	# Gyrophare d'alerte rouge
	var siren := OmniLight3D.new()
	siren.position = Vector3(0, 5.2, -1.6)
	siren.light_color = Color(1.0, 0.1, 0.1)
	siren.light_energy = 4.0
	siren.omni_range = 8.0
	sb.add_child(siren)

	airlock.add_child(sb)

	var label := Label3D.new()
	label.text = "🚨 CORVETTE CORELLIENNE (DONJON) 🚨\n« Instance Raid Chronométrée : 60 min »\n[E] Pénétrer dans le Sas Pressurisé"
	label.position = Vector3(0, 6.2, -1.6)
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.font_size = 18
	label.modulate = Color(1.0, 0.3, 0.3)
	airlock.add_child(label)

	return airlock



