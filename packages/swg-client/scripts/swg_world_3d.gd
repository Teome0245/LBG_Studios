extends Node3D
## Scène Principale du Monde 3D SWG Pre-CU (Lost Heaven)
## 1. Environnement 3D : Ciel atmosphérique, soleil directionnel, sol désertique 3D et bâtiments témoins.
## 2. Joueur 3D TPS : Contrôleur avec caméra orbitale, physique des 3 postures et raycasting d'interaction.
## 3. PNJ & Entités 3D : Lia (Cantina), Odo Merr (Maire), Vendeur Auto, Chiot des Sables.
## 4. Couche UI 2D (CanvasLayer) : HUD HAM, Menu Radial, Datapad PCD, Fiche HAM 9-stats, Bazar, Housing.

const _PlayerController3DScript = preload("res://scripts/swg_player_controller_3d.gd")
const _SwgTerrainSystemScript = preload("res://scripts/swg_terrain_system_3d.gd")
const _SwgAssetPipelineScript = preload("res://scripts/swg_asset_pipeline.gd")
const _SwgHamHudScript = preload("res://scripts/swg_ham_hud.gd")
const _SwgRadialMenuScript = preload("res://scripts/swg_radial_menu.gd")
const _SwgCharacterSheetScript = preload("res://scripts/swg_character_sheet.gd")
const _SwgDatapadPanelScript = preload("res://scripts/swg_datapad_panel.gd")
const _SwgBazaarPanelScript = preload("res://scripts/swg_bazaar_panel.gd")
const _SwgStructurePanelScript = preload("res://scripts/swg_structure_panel.gd")
const _SwgSkillsPanelScript = preload("res://scripts/swg_skills_panel.gd")
const _SwgSurveyPanelScript = preload("res://scripts/swg_survey_panel.gd")
const _SwgExperimentPanelScript = preload("res://scripts/swg_experiment_panel.gd")

var player: CharacterBody3D = null
var terrain_system: Node3D = null

# Interface UI CanvasLayer
var ui_layer: CanvasLayer = null
var swg_ham_hud: Node = null
var swg_radial_menu: Node = null
var swg_character_sheet: Node = null
var swg_datapad_panel: Node = null
var swg_bazaar_panel: Node = null
var swg_structure_panel: Node = null
var swg_skills_panel: Node = null
var swg_survey_panel: Node = null
var swg_experiment_panel: Node = null

var _hud_prompt: Label = null


func _ready() -> void:
	_setup_environment()
	_setup_world_geometry()
	_spawn_player()
	_spawn_interactable_entities()
	_setup_ui()


func _setup_environment() -> void:
	# Ciel & Lumière Ambiante
	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	var sky_mat := ProceduralSkyMaterial.new()
	sky_mat.sky_top_color = Color(0.25, 0.50, 0.85, 1.0)
	sky_mat.sky_horizon_color = Color(0.85, 0.70, 0.55, 1.0)
	sky_mat.ground_bottom_color = Color(0.40, 0.30, 0.20, 1.0)
	sky_mat.ground_horizon_color = Color(0.75, 0.60, 0.45, 1.0)
	sky.sky_material = sky_mat
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = 0.8

	var world_env := WorldEnvironment.new()
	world_env.environment = env
	add_child(world_env)

	# Soleil Directionnel avec Ombres
	var sun := DirectionalLight3D.new()
	sun.position = Vector3(0, 50, 0)
	sun.rotation_degrees = Vector3(-45, 30, 0)
	sun.light_color = Color(1.0, 0.95, 0.88, 1.0)
	sun.light_energy = 1.2
	sun.shadow_enabled = true
	add_child(sun)


func _setup_world_geometry() -> void:
	# 1. Système de Terrain Dynamique 3D SWG (Chunks fractals 64m avec affecteurs urbains)
	terrain_system = _SwgTerrainSystemScript.new()
	terrain_system.name = "SwgTerrainSystem3D"
	add_child(terrain_system)
	terrain_system.update_chunks_around_position(Vector3(0, 0, 0))

	# 2. Cantina La Perle POB Authentique (Multi-cellules : Bar, Scène Artistes, Alcôves)
	var cantina_pob: Node3D = _SwgAssetPipelineScript.build_swg_cantina_pob(Vector3(15, 0, -20), 0.0)
	add_child(cantina_pob)

	# 3. Structure 3D Témoin : Bazar Public
	_spawn_building("Bazar Public de Lost Heaven", Vector3(-18, 0, -15), Vector3(10, 4, 10), Color(0.45, 0.40, 0.35))
	# 4. Structure 3D Témoin : Centre Médical
	_spawn_building("Centre Médical d'Odo", Vector3(-25, 0, 15), Vector3(12, 5, 12), Color(0.70, 0.72, 0.75))


func _spawn_building(b_name: String, pos: Vector3, size: Vector3, col: Color) -> void:
	var sb := StaticBody3D.new()
	sb.name = b_name
	sb.position = pos

	var col_shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = size
	col_shape.shape = box
	col_shape.position = Vector3(0, size.y * 0.5, 0)
	sb.add_child(col_shape)

	var mesh_inst := MeshInstance3D.new()
	var box_m := BoxMesh.new()
	box_m.size = size
	mesh_inst.mesh = box_m
	mesh_inst.position = Vector3(0, size.y * 0.5, 0)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = col
	mesh_inst.set_surface_override_material(0, mat)
	sb.add_child(mesh_inst)

	var lbl := Label3D.new()
	lbl.text = "◈ %s ◈" % b_name
	lbl.position = Vector3(0, size.y + 0.8, 0)
	lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lbl.font_size = 18
	lbl.modulate = Color(0.96, 0.86, 0.38, 1.0)
	sb.add_child(lbl)

	add_child(sb)


func _spawn_player() -> void:
	player = _PlayerController3DScript.new()
	player.name = "SwgPlayer3D"
	player.position = Vector3(0, 0.5, 0)
	player.posture_changed.connect(_on_player_posture_changed)
	add_child(player)
	if terrain_system != null:
		terrain_system.player_node = player


func _spawn_interactable_entities() -> void:
	# PNJ : Lia (Artiste Cantina)
	_spawn_npc("Lia (Artiste Cantina)", Vector3(15, 0, -12), Color(0.9, 0.4, 0.7), "npc_entertainer")
	# PNJ : Odo Merr (Maire)
	_spawn_npc("Odo Merr (Maire de Lost Heaven)", Vector3(0, 0, -10), Color(0.3, 0.7, 0.9), "npc_mayor")
	# Créature : Chiot des Sables (Faune domptable)
	_spawn_npc("Chiot des Sables (Juvénile)", Vector3(-6, 0, 8), Color(0.85, 0.55, 0.2), "creature_juvenile")


func _spawn_npc(n_name: String, pos: Vector3, col: Color, kind_id: String) -> void:
	var body := CharacterBody3D.new()
	body.name = n_name
	body.position = pos
	body.set_meta("entity_kind", kind_id)
	body.set_meta("display_name", n_name)

	var col_shape := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 0.45
	cap.height = 1.7
	col_shape.shape = cap
	col_shape.position = Vector3(0, 0.85, 0)
	body.add_child(col_shape)

	var mesh_inst := MeshInstance3D.new()
	var cap_m := CapsuleMesh.new()
	cap_m.radius = 0.45
	cap_m.height = 1.7
	mesh_inst.mesh = cap_m
	mesh_inst.position = Vector3(0, 0.85, 0)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = col
	mesh_inst.set_surface_override_material(0, mat)
	body.add_child(mesh_inst)

	var lbl := Label3D.new()
	lbl.text = n_name
	lbl.position = Vector3(0, 2.1, 0)
	lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lbl.font_size = 13
	lbl.modulate = Color(0.85, 0.98, 1.0, 1.0)
	body.add_child(lbl)

	add_child(body)


func _setup_ui() -> void:
	ui_layer = CanvasLayer.new()
	ui_layer.name = "SwgUiLayer"
	add_child(ui_layer)

	# 1. HUD HAM SWG (Haut-Gauche + Dock Bas-Droite)
	swg_ham_hud = _SwgHamHudScript.new()
	swg_ham_hud.name = "SwgHamHud"
	swg_ham_hud.position = Vector2(12, 12)
	swg_ham_hud.quick_panel_requested.connect(_on_quick_panel_requested)
	ui_layer.add_child(swg_ham_hud)

	# 2. Menu Radial SWG
	swg_radial_menu = _SwgRadialMenuScript.new()
	swg_radial_menu.name = "SwgRadialMenu"
	swg_radial_menu.radial_action_selected.connect(_on_radial_action_selected)
	ui_layer.add_child(swg_radial_menu)

	# 3. Fiche Perso HAM 9-stats
	swg_character_sheet = _SwgCharacterSheetScript.new()
	swg_character_sheet.name = "SwgCharacterSheet"
	ui_layer.add_child(swg_character_sheet)

	# 4. Datapad SWG
	swg_datapad_panel = _SwgDatapadPanelScript.new()
	swg_datapad_panel.name = "SwgDatapadPanel"
	ui_layer.add_child(swg_datapad_panel)

	# 5. Bazar SWG
	swg_bazaar_panel = _SwgBazaarPanelScript.new()
	swg_bazaar_panel.name = "SwgBazaarPanel"
	ui_layer.add_child(swg_bazaar_panel)

	# 6. Housing & Cités
	swg_structure_panel = _SwgStructurePanelScript.new()
	swg_structure_panel.name = "SwgStructurePanel"
	ui_layer.add_child(swg_structure_panel)

	# 7. Compétences 4x4
	swg_skills_panel = _SwgSkillsPanelScript.new()
	swg_skills_panel.name = "SwgSkillsPanel"
	ui_layer.add_child(swg_skills_panel)

	# 8. Survey & Expérimentation
	swg_survey_panel = _SwgSurveyPanelScript.new()
	swg_survey_panel.name = "SwgSurveyPanel"
	ui_layer.add_child(swg_survey_panel)

	swg_experiment_panel = _SwgExperimentPanelScript.new()
	swg_experiment_panel.name = "SwgExperimentPanel"
	ui_layer.add_child(swg_experiment_panel)

	# Bandeau d'aide aux commandes
	_hud_prompt = Label.new()
	_hud_prompt.text = "◈ SWG PRE-CU 3D : ZQSD=Déplacement | Maintenir Clic-Droit=Mouselook | Molette=Zoom Caméra | X=Accroupi | Z=Couché | Espace=Saut | Clic-Droit Entité=Menu Radial | C=Fiche Perso | D=Datapad | B=Bazar | H=Housing"
	_hud_prompt.position = Vector2(16, 680)
	_hud_prompt.add_theme_font_size_override("font_size", 10)
	_hud_prompt.add_theme_color_override("font_color", Color(0.85, 0.95, 1.0, 0.85))
	ui_layer.add_child(_hud_prompt)


func _unhandled_input(event: InputEvent) -> void:
	# Clic Droit dans le monde 3D : Raycasting vers l'entité pour ouvrir le Menu Radial SWG
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_RIGHT and not event.pressed:
		# Si on était en mode mouselook, relâcher désactive mouselook
		pass

	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_C:
				if swg_character_sheet: swg_character_sheet.toggle()
			KEY_D:
				if swg_datapad_panel: swg_datapad_panel.toggle()
			KEY_B:
				if swg_bazaar_panel: swg_bazaar_panel.toggle()
			KEY_H:
				if swg_structure_panel: swg_structure_panel.toggle()
			KEY_K:
				if swg_skills_panel: swg_skills_panel.toggle()
			KEY_U:
				if swg_survey_panel: swg_survey_panel.toggle()
			KEY_ESCAPE:
				_close_all_modals()


func _on_player_posture_changed(p_lbl: String) -> void:
	if swg_ham_hud:
		swg_ham_hud.set_posture(p_lbl)


func _on_quick_panel_requested(k: String) -> void:
	match k:
		"character": if swg_character_sheet: swg_character_sheet.toggle()
		"datapad": if swg_datapad_panel: swg_datapad_panel.toggle()
		"skills": if swg_skills_panel: swg_skills_panel.toggle()
		"survey": if swg_survey_panel: swg_survey_panel.toggle()
		"experiment": if swg_experiment_panel: swg_experiment_panel.toggle()
		"vendors": if swg_bazaar_panel: swg_bazaar_panel.toggle()
		"housing": if swg_structure_panel: swg_structure_panel.toggle()


func _on_radial_action_selected(act: String, ctx: Dictionary) -> void:
	print("[SWG 3D] Action radiale déclenchée : %s sur %s" % [act, ctx.get("name", "cible")])
	if act == "vendor_browse" and swg_bazaar_panel:
		swg_bazaar_panel.open_panel()
	elif (act == "house_manage" or act == "house_maintenance") and swg_structure_panel:
		swg_structure_panel.open_panel()


func _close_all_modals() -> void:
	if swg_radial_menu and swg_radial_menu.visible: swg_radial_menu.close_menu()
	if swg_character_sheet and swg_character_sheet.visible: swg_character_sheet.close_panel()
	if swg_datapad_panel and swg_datapad_panel.visible: swg_datapad_panel.close_panel()
	if swg_bazaar_panel and swg_bazaar_panel.visible: swg_bazaar_panel.close_panel()
	if swg_structure_panel and swg_structure_panel.visible: swg_structure_panel.close_panel()
	if swg_skills_panel and swg_skills_panel.visible: swg_skills_panel.close_panel()
	if swg_survey_panel and swg_survey_panel.visible: swg_survey_panel.close_panel()
	if swg_experiment_panel and swg_experiment_panel.visible: swg_experiment_panel.close_panel()

