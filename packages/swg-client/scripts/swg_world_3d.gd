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
const _SwgDialogBoxScript = preload("res://scripts/swg_dialog_box.gd")
const _SwgMissionsDialogScript = preload("res://scripts/swg_missions_terminal_dialog.gd")
const _SwgBankDialogScript = preload("res://scripts/swg_bank_terminal_dialog.gd")
const _SwgCombatSystemScript = preload("res://scripts/swg_combat_system_3d.gd")
const _SwgActionHotbarScript = preload("res://scripts/swg_action_hotbar.gd")
const _SwgInventoryScript = preload("res://scripts/swg_inventory_paperdoll.gd")
const _SwgCraftingScript = preload("res://scripts/swg_crafting_panel.gd")
const _SwgPlanetaryMapScript = preload("res://scripts/swg_planetary_map.gd")
const _SwgSkinSystemScript = preload("res://scripts/swg_skin_system.gd")
const _SwgAudioSynthesizerScript = preload("res://scripts/swg_audio_synthesizer.gd")
const _SwgTravelDialogScript = preload("res://scripts/swg_travel_dialog.gd")
const _SwgTargetFrameScript = preload("res://scripts/swg_target_frame.gd")
const _SwgChatBoxScript = preload("res://scripts/swg_chat_box.gd")
const _SwgCreatureLairScript = preload("res://scripts/swg_creature_lair_3d.gd")
const _SwgFactionSystemScript = preload("res://scripts/swg_faction_system.gd")
const _SwgFactionDialogScript = preload("res://scripts/swg_faction_dialog.gd")
const _SwgSpeciesDialogScript = preload("res://scripts/swg_species_dialog.gd")

var player: CharacterBody3D = null
var terrain_system: Node3D = null
var swg_combat_system: Node3D = null
var swg_audio: Node = null
var swg_faction_system: Node = null

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
var swg_dialog_box: Node = null
var swg_missions_dialog: Node = null
var swg_bank_dialog: Node = null
var swg_travel_dialog: Node = null
var swg_action_hotbar: Control = null
var swg_inventory_panel: Node = null
var swg_crafting_panel: Node = null
var swg_planetary_map: Node = null
var swg_target_frame: Node = null
var swg_chat_box: Node = null
var swg_faction_dialog: Control = null
var swg_species_dialog: Control = null

var _sun_primary: DirectionalLight3D = null
var _sun_secondary: DirectionalLight3D = null
var _world_environment: WorldEnvironment = null
var _tracked_entities: Array = []

var _hud_prompt: Label = null
var _interaction_prompt: PanelContainer = null
var _interaction_label: Label = null
var _current_target_entity: Node = null
var _is_riding_speeder: bool = false
var _mounted_speeder_visual: Node3D = null
var _is_riding_dewback: bool = false
var _mounted_dewback_visual: Node3D = null
var _shuttle_visual_ref: Node3D = null
var _hyperspace_overlay: Panel = null
var _notify_label: Label = null
var _notify_timer: float = 0.0
var _active_missions: Array = []
var _active_waypoints: Dictionary = {}
var _lairs: Array = []
var _cantina_buff_timer: float = 0.0
var _player_fatigue: int = 0
var _camouflage_active: bool = false
var _caravan_root: Node3D = null
var _caravan_dir: float = 1.0
var _is_watching_entertainer: bool = false
var _watch_target_name: String = "Lia"
var _inspiration_meter: float = 0.0


func _ready() -> void:
	_setup_environment()
	_setup_world_geometry()
	_spawn_player()
	_spawn_interactable_entities()
	_setup_ui()


func _setup_environment() -> void:
	# Ciel & Atmosphère Désertique SWG
	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	var sky_mat := ProceduralSkyMaterial.new()
	sky_mat.sky_top_color = Color(0.20, 0.45, 0.80, 1.0)
	sky_mat.sky_horizon_color = Color(0.88, 0.72, 0.52, 1.0)
	sky_mat.ground_bottom_color = Color(0.35, 0.25, 0.15, 1.0)
	sky_mat.ground_horizon_color = Color(0.80, 0.65, 0.45, 1.0)
	sky.sky_material = sky_mat
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = 0.85

	# Brume Atmosphérique Chaude (Distance Fog SWG) pour lisser les dunes à l'horizon
	env.fog_enabled = true
	env.fog_light_color = Color(0.85, 0.72, 0.54, 1.0)
	env.fog_density = 0.0018
	env.fog_sky_affect = 0.4

	# Améliorations Graphiques Avancées PBR (Glow/Bloom, SSAO, SSIL, ACES Tonemapping)
	env.glow_enabled = true
	env.glow_bloom = 0.22
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SCREEN
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.tonemap_exposure = 1.08
	env.tonemap_white = 1.2
	env.ssao_enabled = true
	env.ssao_radius = 1.8
	env.ssao_intensity = 2.4
	env.ssil_enabled = true
	env.ssr_enabled = true

	var world_env := WorldEnvironment.new()
	world_env.environment = env
	add_child(world_env)
	_world_environment = world_env

	# 1. Soleil Principal Éclatant (Tatooine Sun 1)
	var sun1 := DirectionalLight3D.new()
	sun1.name = "Sun_Primary"
	sun1.position = Vector3(0, 60, 0)
	sun1.rotation_degrees = Vector3(-42, 35, 0)
	sun1.light_color = Color(1.0, 0.96, 0.88, 1.0)
	sun1.light_energy = 1.25
	sun1.shadow_enabled = true
	sun1.shadow_blur = 1.6
	add_child(sun1)
	_sun_primary = sun1

	# 2. Soleil Binaire Nain Orangé (Tatooine Sun 2)
	var sun2 := DirectionalLight3D.new()
	sun2.name = "Sun_Secondary"
	sun2.position = Vector3(0, 45, 0)
	sun2.rotation_degrees = Vector3(-32, 55, 0)
	sun2.light_color = Color(1.0, 0.65, 0.40, 1.0)
	sun2.light_energy = 0.45
	sun2.shadow_enabled = false
	add_child(sun2)
	_sun_secondary = sun2


func _setup_world_geometry() -> void:
	# 0. Système de Combat 3D, Projectiles & Cycle Jour/Nuit SWG
	swg_combat_system = _SwgCombatSystemScript.new()
	add_child(swg_combat_system)
	swg_combat_system.setup_environment_refs(_sun_primary, _sun_secondary, _world_environment)

	# 1. Système de Terrain Dynamique 3D SWG (Chunks fractals 64m avec affecteurs urbains)
	terrain_system = _SwgTerrainSystemScript.new()
	terrain_system.name = "SwgTerrainSystem3D"
	add_child(terrain_system)
	terrain_system.update_chunks_around_position(Vector3(0, 0, 0))

	# ==========================================================================
	# A. HUB URBAIN DE LOST HEAVEN (Architecture Bâtiments Majeurs)
	# ==========================================================================

	# 2. Cantina La Perle POB Authentique (Multi-cellules : Bar en fer à cheval, Scène, Alcôves)
	var cantina_pob: Node3D = _SwgAssetPipelineScript.build_swg_cantina_pob(Vector3(25, 0, -22), 0.0)
	add_child(cantina_pob)

	# 3. Spatioport de Lost Heaven (Shuttleport) avec Navette Spatiale posée et tour de contrôle
	var shuttleport: Node3D = _SwgAssetPipelineScript.build_swg_shuttleport(Vector3(-42, 0, -28), 15.0)
	add_child(shuttleport)
	_shuttle_visual_ref = shuttleport.find_child("SWG_Shuttle_Craft", true, false) as Node3D

	# 4. Hôtel de Ville / Grand Hall Municipal de Lost Heaven
	var town_hall: Node3D = _SwgAssetPipelineScript.build_swg_town_hall(Vector3(0, 0, -45), 0.0)
	add_child(town_hall)

	# 5. Centre Médical & Clonerie avec cuves de Bacta lumineuses (Entrée franchissable face au Sud)
	var medcenter: Node3D = _SwgAssetPipelineScript.build_swg_medcenter(Vector3(-28, 0, 22), 0.0)
	add_child(medcenter)

	# 6. Quartier Résidentiel : Maisons Citadines & POB Entrable avec Vendeur Personnel
	add_child(_SwgAssetPipelineScript.build_swg_enterable_player_house(Vector3(22, 0, 16), 180.0, "Résidence de Voyageur"))
	add_child(_SwgAssetPipelineScript.build_swg_tatooine_house(Vector3(38, 0, 12), -20.0, 1))
	add_child(_SwgAssetPipelineScript.build_swg_tatooine_house(Vector3(18, 0, 36), 45.0, 2))
	add_child(_SwgAssetPipelineScript.build_swg_tatooine_house(Vector3(-14, 0, 42), -15.0, 0))
	add_child(_SwgAssetPipelineScript.build_swg_tatooine_house(Vector3(-36, 0, 45), 30.0, 1))

	# 7. Remparts & Portes Fortifiées de la Cité (Porte Ouest & Porte Est)
	add_child(_SwgAssetPipelineScript.build_swg_city_wall_and_gate(Vector3(-65, 0, 0), 90.0, "Porte Ouest"))
	add_child(_SwgAssetPipelineScript.build_swg_city_wall_and_gate(Vector3(65, 0, 0), -90.0, "Porte Est"))

	# ==========================================================================
	# B. MOBILIER URBAIN, TERMINAUX & PROPS SWG AUTHENTIQUES
	# ==========================================================================

	# 8. Esplanade Centrale : Terminaux Interactifs SWG
	add_child(_SwgAssetPipelineScript.build_mission_terminal(Vector3(-4, 0, -7), 0.0))
	add_child(_SwgAssetPipelineScript.build_bank_terminal(Vector3(4, 0, -7), 0.0))
	add_child(_SwgAssetPipelineScript.build_bazaar_terminal(Vector3(-8, 0, -3), 45.0))
	add_child(_SwgAssetPipelineScript.build_cloning_terminal(Vector3(-22, 0, 18), 30.0))

	# 9. Véhicule : Landspeeder X-34 stationné sur la place
	add_child(_SwgAssetPipelineScript.build_landspeeder(Vector3(8, 0, 6), -35.0))

	# 10. Vaporisateurs d'Humidité (Moisture Vaporators GX-8)
	add_child(_SwgAssetPipelineScript.build_moisture_vaporator(Vector3(12, 0, -10)))
	add_child(_SwgAssetPipelineScript.build_moisture_vaporator(Vector3(-15, 0, -8)))
	add_child(_SwgAssetPipelineScript.build_moisture_vaporator(Vector3(-22, 0, 35)))
	add_child(_SwgAssetPipelineScript.build_moisture_vaporator(Vector3(30, 0, 28)))

	# 11. Amas de Fret Cargo et Barils de Carburant
	add_child(_SwgAssetPipelineScript.build_cargo_cluster(Vector3(-12, 0, -18)))
	add_child(_SwgAssetPipelineScript.build_cargo_cluster(Vector3(12, 0, 18)))
	add_child(_SwgAssetPipelineScript.build_cargo_cluster(Vector3(-26, 0, -12)))

	# 12. Lampadaires de Rue le long des allées
	for lz in [-30, -15, 0, 15, 30]:
		add_child(_SwgAssetPipelineScript.build_street_lamp(Vector3(-12, 0, lz)))
		add_child(_SwgAssetPipelineScript.build_street_lamp(Vector3(12, 0, lz)))

	# ==========================================================================
	# C. WILDERNESS, RELIEF & CAMPS SAUVAGES DANS LES DUNES
	# ==========================================================================

	# 13. Campement de Scout Nomade avec feu de camp dans les dunes à l'Ouest
	add_child(_SwgAssetPipelineScript.build_scout_camp(Vector3(-95, 0, -45)))

	# 14. Extracteur Minier Industriel (Mining Harvester) au Nord-Est
	add_child(_SwgAssetPipelineScript.build_mining_harvester(Vector3(90, 0, -55), -45.0))

	# 15. Éperons Rocheux / Mesas de Grès Rouge
	add_child(_SwgAssetPipelineScript.build_rock_outcrop(Vector3(-110, 0, 65), Vector3(1.4, 1.6, 1.2)))
	add_child(_SwgAssetPipelineScript.build_rock_outcrop(Vector3(115, 0, -35), Vector3(1.8, 2.0, 1.5)))
	add_child(_SwgAssetPipelineScript.build_rock_outcrop(Vector3(85, 0, 85), Vector3(1.2, 1.4, 1.1)))

	# 16. Flore Xérophile du Désert (Cactus cierges et buissons secs)
	for fx in [-105, -85, 75, 95, 120, -50]:
		for fz in [-75, 55, -45, 95, 20]:
			add_child(_SwgAssetPipelineScript.build_desert_flora(Vector3(fx, 0, fz)))


func _spawn_player() -> void:
	player = _PlayerController3DScript.new()
	player.name = "SwgPlayer3D"
	player.position = Vector3(0, 0.5, 0)
	player.posture_changed.connect(_on_player_posture_changed)
	add_child(player)
	if terrain_system != null:
		terrain_system.player_node = player


func _spawn_interactable_entities() -> void:
	# 1. PNJ de la Ville de Lost Heaven (Modèles VRM Humanoid 3D)
	# Lia : Élevée sur la scène de spectacle de la Cantina sous les projecteurs
	_spawn_npc("Lia (Artiste Cantina)", Vector3(32.5, 0.6, -22), Color(0.9, 0.4, 0.7), "npc_entertainer")
	# Barman Jax Moro : Au centre de son comptoir en U, face aux clients
	_spawn_npc("Barman Jax Moro", Vector3(21, 0, -22.3), Color(0.85, 0.65, 0.35), "npc_bartender")
	_spawn_npc("Barkeep Patron (Client du Bar)", Vector3(21, 0, -19.2), Color(0.5, 0.7, 0.5), "npc_citizen")
	# Odo Merr : Sur l'estrade municipale à l'intérieur de l'Hôtel de Ville
	_spawn_npc("Odo Merr (Maire de Lost Heaven)", Vector3(0, 0.65, -49.5), Color(0.3, 0.7, 0.9), "npc_mayor")
	# Docteur Vane : Dans son cabinet clinique au Centre Médical près des cuves de Bacta
	_spawn_npc("Docteur Vane (Médecin Chef)", Vector3(-28, 0.2, 18.2), Color(0.2, 0.9, 0.9), "npc_doctor")
	_spawn_npc("Miran Sael (Apothicaire Nomade)", Vector3(14, 0, -12), Color(0.4, 0.8, 0.5), "npc_merchant")
	_spawn_npc("Soren Kray (Armurier de Rue)", Vector3(-14, 0, -10), Color(0.8, 0.5, 0.2), "npc_armorer")
	_spawn_npc("Kaelen (Marchand de Droïdes)", Vector3(-9, 0, 2), Color(0.3, 0.5, 0.7), "npc_merchant")
	_spawn_npc("Torin (Mécanicien Landspeeder)", Vector3(6, 0, 8), Color(0.7, 0.4, 0.2), "npc_engineer")
	_spawn_npc("Pilote de Navette Corran", Vector3(-35, 0, -25), Color(0.85, 0.7, 0.9), "npc_pilot")
	_spawn_npc("Voyageur des Dunes", Vector3(5, 0, -2), Color(0.6, 0.6, 0.6), "npc_citizen")
	_spawn_npc("Garde de la Milice Porte Ouest", Vector3(-62, 0, -2), Color(0.75, 0.25, 0.2), "npc_guard")
	_spawn_npc("Garde de la Milice Porte Est", Vector3(62, 0, 2), Color(0.75, 0.25, 0.2), "npc_guard")
	_spawn_npc("Nix (Éclaireur Vétéran)", Vector3(-90, 0, -42), Color(0.3, 0.6, 0.8), "npc_scout")
	_spawn_npc("Mira Tarek (Prospectrice)", Vector3(85, 0, -50), Color(0.7, 0.7, 0.3), "npc_miner")
	_spawn_npc("Daran (Vendeur Personnel)", Vector3(24.4, 0.1, 14.8), Color(0.3, 0.8, 0.95), "npc_vendor")

	# 2. Droïdes Urbains
	add_child(_SwgAssetPipelineScript.build_astromech_droid(Vector3(-38, 0, -18)))

	# 3. Faune Vivante des Dunes (Quadrupèdes & Bêtes des Sables)
	# Marcheurs des Dunes Géants (Herbivores / Domptables)
	add_child(_SwgAssetPipelineScript.build_dune_walker_creature(Vector3(-45, 0, 68)))
	add_child(_SwgAssetPipelineScript.build_dune_walker_creature(Vector3(120, 0, -80)))

	# Bêtes & Prédateurs
	_spawn_npc("Chiot des Sables (Juvénile)", Vector3(-8, 0, 8), Color(0.85, 0.55, 0.2), "creature_juvenile")
	_spawn_npc("Chacal Doré (Sauvage)", Vector3(-92, 0, -38), Color(0.95, 0.65, 0.15), "creature_jackal")
	_spawn_npc("Chacal Alpha (Sauvage)", Vector3(-105, 0, -55), Color(0.98, 0.6, 0.1), "creature_jackal")
	_spawn_npc("Fennec Mirage (Furtif)", Vector3(45, 0, -75), Color(0.9, 0.75, 0.4), "creature_juvenile")
	_spawn_npc("Scarabée Obsidien Géant", Vector3(88, 0, 78), Color(0.2, 0.2, 0.25), "creature_beetle")

	# 4. Campement Hostile des Pillards des Sables (Tuskens)
	add_child(_SwgAssetPipelineScript.build_tusken_camp(Vector3(-140, 0, 85)))
	_spawn_npc("Pillard Tusken Chasseur", Vector3(-134, 0, 82), Color(0.75, 0.6, 0.45), "npc_tusken")
	_spawn_npc("Guerrier Tusken d'Élite", Vector3(-143, 0, 88), Color(0.65, 0.5, 0.35), "npc_tusken")
	_spawn_npc("Gaffi Master Tusken", Vector3(-138, 0, 78), Color(0.8, 0.4, 0.3), "npc_tusken")

	# 5. Caravane Marchande Itinérante de Lost Heaven
	_spawn_merchant_caravan()

	# 6. Nids de Créatures (Lairs) & Tumulus Sauvages Pre-CU
	_spawn_creature_lairs()

	# 7. Garnisons & Postes Avancés de la Guerre Civile Galactique (GCW)
	_spawn_faction_outposts()


func _spawn_merchant_caravan() -> void:
	var c_root := Node3D.new()
	c_root.name = "Merchant_Caravan"
	c_root.position = Vector3(-35, 0, 0)

	var bantha := _SwgAssetPipelineScript.build_caravan_bantha(Vector3(0, 0, 0))
	c_root.add_child(bantha)

	# Marchand Ambulant Doran Karr
	var merch := CharacterBody3D.new()
	merch.name = "Doran Karr (Marchand Ambulant)"
	merch.position = Vector3(2.5, 0, 1.0)
	merch.set_meta("entity_kind", "npc_merchant")
	merch.set_meta("display_name", "Doran Karr (Marchand Ambulant)")
	var col_s := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 0.45
	cap.height = 1.7
	col_s.shape = cap
	col_s.position = Vector3(0, 0.85, 0)
	merch.add_child(col_s)
	var v_merch := _SwgAssetPipelineScript.load_humanoid_vrm("Compagnon.vrm", false)
	merch.add_child(v_merch)
	_SwgSkinSystemScript.apply_npc_role_skin(merch, "npc_merchant")
	var lbl_m := Label3D.new()
	lbl_m.text = "Doran Karr (Marchand Ambulant)\n« Ravitaillement & Caravane »"
	lbl_m.position = Vector3(0, 2.2, 0)
	lbl_m.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lbl_m.font_size = 13
	lbl_m.modulate = Color(0.95, 0.85, 0.35)
	merch.add_child(lbl_m)
	c_root.add_child(merch)

	# Garde d'escorte de caravane
	var guard := CharacterBody3D.new()
	guard.name = "Garde de Caravane (Escorte)"
	guard.position = Vector3(-2.5, 0, -1.0)
	guard.set_meta("entity_kind", "npc_guard")
	guard.set_meta("display_name", "Garde de Caravane (Escorte)")
	var col_g := CollisionShape3D.new()
	col_g.shape = cap.duplicate()
	col_g.position = Vector3(0, 0.85, 0)
	guard.add_child(col_g)
	var v_guard := _SwgAssetPipelineScript.load_humanoid_vrm("Compagnon.vrm", false)
	guard.add_child(v_guard)
	_SwgSkinSystemScript.apply_npc_role_skin(guard, "npc_guard")
	var lbl_g := Label3D.new()
	lbl_g.text = "Garde de Caravane (Escorte)"
	lbl_g.position = Vector3(0, 2.2, 0)
	lbl_g.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lbl_g.font_size = 13
	lbl_g.modulate = Color(0.85, 0.95, 1.0)
	guard.add_child(lbl_g)
	c_root.add_child(guard)

	add_child(c_root)
	_caravan_root = c_root


func _spawn_npc(n_name: String, pos: Vector3, col: Color, kind_id: String) -> CharacterBody3D:
	var body := CharacterBody3D.new()
	body.name = n_name
	body.position = pos
	body.set_meta("entity_kind", kind_id)
	body.set_meta("display_name", n_name)
	body.set_meta("home_pos", pos)
	body.set_meta("attack_cooldown", 0.0)
	body.set_meta("aggro_state", "idle")

	var base_hp: int = 350 if ("Élite" in n_name or "Master" in n_name) else (220 if kind_id.begins_with("creature_") else 250)
	body.set_meta("max_health", base_hp)
	body.set_meta("current_health", base_hp)

	var col_shape := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 0.45
	cap.height = 1.7
	col_shape.shape = cap
	col_shape.position = Vector3(0, 0.85, 0)
	body.add_child(col_shape)

	var visual_node: Node3D = null

	# A1. Stormtroopers & Officiers Impériaux (GCW)
	if kind_id in ["npc_stormtrooper", "npc_imperial_officer"]:
		visual_node = _SwgAssetPipelineScript.build_stormtrooper_visual(kind_id == "npc_imperial_officer")

	# A2. Soldats de l'Alliance Rebelle (GCW)
	elif kind_id in ["npc_rebel_soldier", "npc_rebel_commando"]:
		visual_node = _SwgAssetPipelineScript.build_rebel_soldier_visual(kind_id == "npc_rebel_commando")

	# A3. Hommes des Sables Tuskens (Modèle Bâton Gaffi et Masque Respirateur)
	elif kind_id == "npc_tusken":
		visual_node = _SwgAssetPipelineScript.build_tusken_raider_visual(col)

	# B. PNJ Humanoïdes (Lia, Jax, Odo, Vane, Gardes, Citoyens) -> Modèles VRM 3D
	elif kind_id.begins_with("npc_"):
		var vrm_choice := "Compagnon.vrm"
		var is_ent := false
		if "Lia" in n_name or "Artiste" in n_name:
			vrm_choice = "LadyKoi.vrm"
			is_ent = true
		elif "Docteur" in n_name or "Médecin" in n_name or "Vane" in n_name:
			vrm_choice = "Anna.vrm"
		elif "Maire" in n_name or "Odo" in n_name:
			vrm_choice = "Aurora.vrm"
			body.rotation_degrees.y = 180.0
		elif "Barman" in n_name or "Jax" in n_name:
			vrm_choice = "Compagnon.vrm"
			body.rotation_degrees.y = 180.0

		visual_node = _SwgAssetPipelineScript.load_humanoid_vrm(vrm_choice, is_ent)

	# C. Faune Sauvage Quadrupède (Chacal, Chiot) -> Modèle Canin Articulé
	elif kind_id in ["creature_juvenile", "creature_jackal"]:
		var s_fac := 0.65 if kind_id == "creature_juvenile" else 1.05
		visual_node = _SwgAssetPipelineScript.build_quadruped_creature(Vector3.ZERO, col, s_fac)

	# D. Faune Sauvage : Scarabée Obsidien Géant -> Carapace Dôme
	elif kind_id == "creature_beetle":
		visual_node = _SwgAssetPipelineScript.build_beetle_creature(Vector3.ZERO)

	# E. Fallback propre si modèle absent
	if visual_node != null:
		body.add_child(visual_node)
		if kind_id != "npc_entertainer" and kind_id != "npc_tusken" and not ("Lia" in n_name):
			_SwgSkinSystemScript.apply_npc_role_skin(body, kind_id)
	else:
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
	lbl.position = Vector3(0, 2.15, 0)
	lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lbl.font_size = 13
	lbl.modulate = Color(1.0, 0.4, 0.3) if kind_id == "npc_tusken" else Color(0.85, 0.98, 1.0, 1.0)
	body.add_child(lbl)

	add_child(body)
	return body


func _spawn_creature_lairs() -> void:
	# A. Tumulus / Nid de Chacals des Dunes (Ouest, près des crêtes rocheuses)
	var lair_jackals := _create_creature_lair(
		"lair_jackals_west",
		"Tumulus des Chacals des Dunes",
		"creature_jackal",
		"Chacal Gardien du Nid",
		Vector3(-130, 0, -65),
		1400,
		"Œuf de Chacal des Sables Fossilisé",
		950
	)
	_lairs.append(lair_jackals)

	# B. Nid Souterrain de Scarabées Obsidiens (Est, vers les mines et extracteurs)
	var lair_beetles := _create_creature_lair(
		"lair_beetles_east",
		"Nid de Scarabées Obsidiens",
		"creature_beetle",
		"Scarabée Ouvrier Défenseur",
		Vector3(140, 0, 95),
		1800,
		"Chitine Pure de Reine Scarabée",
		1250
	)
	_lairs.append(lair_beetles)


func _create_creature_lair(l_id: String, l_name: String, c_kind: String, g_name: String, pos: Vector3, hp: int, rare_item: String, creds: int) -> CharacterBody3D:
	var lair: CharacterBody3D = _SwgCreatureLairScript.new()
	lair.name = l_name
	lair.lair_id = l_id
	lair.lair_display_name = l_name
	lair.creature_kind = c_kind
	lair.guardian_name = g_name
	lair.lair_max_hp = hp
	lair.loot_rare_item = rare_item
	lair.loot_credits = creds
	lair.position = pos

	# Callback de spawn de gardiens rattachés
	lair.spawn_creature_callback = func(guard_name: String, g_pos: Vector3, g_kind: String, _lair_ref: Node3D) -> CharacterBody3D:
		var col := Color(0.95, 0.65, 0.15) if g_kind == "creature_jackal" else Color(0.2, 0.2, 0.25)
		var g_body := _spawn_npc(guard_name, g_pos, col, g_kind)
		g_body.set_meta("lair_parent", lair)
		return g_body

	add_child(lair)
	lair.init_guardians()
	return lair


func _spawn_faction_outposts() -> void:
	# A. Poste Avancé & Garnison Impériale (Porte Est / Dunes Est)
	add_child(_SwgAssetPipelineScript.build_faction_turret(Vector3(75, 0, 15), "imperial"))
	_spawn_npc("Lieutenant Kren (Recruteur Impérial)", Vector3(72, 0, 12), Color(0.95, 0.95, 1.0), "npc_imperial_officer")
	_spawn_npc("Stormtrooper de Patrouille Alpha", Vector3(74, 0, 18), Color(0.96, 0.96, 0.98), "npc_stormtrooper")
	_spawn_npc("Stormtrooper de Patrouille Bêta", Vector3(78, 0, 10), Color(0.96, 0.96, 0.98), "npc_stormtrooper")

	# B. Campement Clandestin de l'Alliance Rebelle (Sud-Ouest, vers les mesas)
	add_child(_SwgAssetPipelineScript.build_faction_turret(Vector3(-115, 0, -20), "rebel"))
	_spawn_npc("Capitaine Vao (Recruteur Rebelle)", Vector3(-110, 0, -18), Color(0.4, 0.5, 0.35), "npc_rebel_commando")
	_spawn_npc("Soldat de l'Alliance Rebelle", Vector3(-112, 0, -24), Color(0.4, 0.45, 0.35), "npc_rebel_soldier")
	_spawn_npc("Sentinelle de l'Alliance", Vector3(-118, 0, -16), Color(0.4, 0.45, 0.35), "npc_rebel_soldier")


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
	swg_datapad_panel.pet_action_requested.connect(_on_datapad_pet_action)
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

	# 9. Boîte de Dialogue Interactive SWG
	swg_dialog_box = _SwgDialogBoxScript.new()
	swg_dialog_box.name = "SwgDialogBox"
	swg_dialog_box.option_selected.connect(_on_dialog_option_selected)
	ui_layer.add_child(swg_dialog_box)

	# 10. Terminal de Missions SWG
	swg_missions_dialog = _SwgMissionsDialogScript.new()
	swg_missions_dialog.name = "SwgMissionsDialog"
	swg_missions_dialog.mission_accepted.connect(_on_mission_accepted)
	ui_layer.add_child(swg_missions_dialog)

	# 11. Terminal Bancaire Galactique
	swg_bank_dialog = _SwgBankDialogScript.new()
	swg_bank_dialog.name = "SwgBankDialog"
	swg_bank_dialog.balance_updated.connect(_on_bank_balance_updated)
	ui_layer.add_child(swg_bank_dialog)

	# 11b. Terminal de Transport Galactique & Navettes
	swg_travel_dialog = _SwgTravelDialogScript.new()
	swg_travel_dialog.name = "SwgTravelDialog"
	swg_travel_dialog.travel_ticket_purchased.connect(_on_travel_ticket_purchased)
	ui_layer.add_child(swg_travel_dialog)

	# 11c. Synthétiseur Audio Galactique (Sons blasters, speeder, navette)
	swg_audio = _SwgAudioSynthesizerScript.new()
	swg_audio.name = "SwgAudioSynthesizer"
	add_child(swg_audio)

	# 11d. Overlay de Saut Hyperspatial Cinématique
	_hyperspace_overlay = Panel.new()
	_hyperspace_overlay.name = "HyperspaceOverlay"
	_hyperspace_overlay.size = Vector2(1280, 720)
	var sb_hyper := StyleBoxFlat.new()
	sb_hyper.bg_color = Color(0.01, 0.03, 0.08, 0.96)
	_hyperspace_overlay.add_theme_stylebox_override("panel", sb_hyper)
	var hyper_lbl := Label.new()
	hyper_lbl.text = "◈ ENTRÉE EN HYPERESPACE • TRANSIT NAVETTE EN COURS ◈\n« Saut matriciel calculé par l'ordinateur de navigation »"
	hyper_lbl.position = Vector2(0, 320)
	hyper_lbl.size = Vector2(1280, 80)
	hyper_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hyper_lbl.add_theme_font_size_override("font_size", 16)
	hyper_lbl.add_theme_color_override("font_color", Color(0.3, 0.95, 1.0))
	_hyperspace_overlay.add_child(hyper_lbl)
	_hyperspace_overlay.visible = false
	ui_layer.add_child(_hyperspace_overlay)

	# 12. Prompt d'Interaction Flottant Dynamique [E]
	_interaction_prompt = PanelContainer.new()
	_interaction_prompt.name = "InteractionPrompt"
	_interaction_prompt.position = Vector2(420, 620)
	_interaction_prompt.size = Vector2(440, 38)
	var p_sb := StyleBoxFlat.new()
	p_sb.bg_color = Color(0.02, 0.14, 0.18, 0.92)
	p_sb.set_border_width_all(2)
	p_sb.border_color = Color(0.96, 0.86, 0.35, 1.0)
	p_sb.set_corner_radius_all(18)
	p_sb.content_margin_left = 16
	p_sb.content_margin_right = 16
	p_sb.content_margin_top = 8
	p_sb.content_margin_bottom = 8
	_interaction_prompt.add_theme_stylebox_override("panel", p_sb)

	_interaction_label = Label.new()
	_interaction_label.text = "◈ [E] Interagir ◈"
	_interaction_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_interaction_label.add_theme_font_size_override("font_size", 12)
	_interaction_label.add_theme_color_override("font_color", Color(0.98, 0.92, 0.65, 1.0))
	_interaction_prompt.add_child(_interaction_label)
	_interaction_prompt.visible = false
	ui_layer.add_child(_interaction_prompt)

	# 13. Notification Toast In-Game
	_notify_label = Label.new()
	_notify_label.position = Vector2(360, 100)
	_notify_label.size = Vector2(560, 32)
	_notify_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_notify_label.add_theme_font_size_override("font_size", 14)
	_notify_label.add_theme_color_override("font_color", Color(0.2, 1.0, 0.5, 1.0))
	_notify_label.visible = false
	ui_layer.add_child(_notify_label)

	# 14. Hotbar d'Action Tactique SWG & Radar Boussole
	swg_action_hotbar = _SwgActionHotbarScript.new()
	swg_action_hotbar.name = "SwgActionHotbar"
	swg_action_hotbar.tracked_player = player
	swg_action_hotbar.tracked_entities = _tracked_entities
	swg_action_hotbar.hotbar_slot_triggered.connect(_on_hotbar_action_triggered)
	ui_layer.add_child(swg_action_hotbar)

	# 15. Inventaire & Équipement Papier-Doll SWG [I]
	swg_inventory_panel = _SwgInventoryScript.new()
	swg_inventory_panel.name = "SwgInventoryPanel"
	swg_inventory_panel.item_used.connect(_on_inventory_item_used)
	ui_layer.add_child(swg_inventory_panel)

	# 16. Atelier d'Artisanat Expérimental SWG [T]
	swg_crafting_panel = _SwgCraftingScript.new()
	swg_crafting_panel.name = "SwgCraftingPanel"
	swg_crafting_panel.inventory_ref = swg_inventory_panel
	ui_layer.add_child(swg_crafting_panel)

	# 17. Carte Planétaire Tactique SWG [M]
	swg_planetary_map = _SwgPlanetaryMapScript.new()
	swg_planetary_map.name = "SwgPlanetaryMap"
	swg_planetary_map.add_waypoint(Vector2(-140, 85), "☠ Campement Tusken")
	swg_planetary_map.add_waypoint(Vector2(0, 0), "Place de Lost Heaven")
	swg_planetary_map.add_waypoint(Vector2(-35, -25), "Spatioport Navette")
	ui_layer.add_child(swg_planetary_map)

	# 18. Cadre de Ciblage Tactique & Jauges HAM Cible
	swg_target_frame = _SwgTargetFrameScript.new()
	swg_target_frame.name = "SwgTargetFrame"
	swg_target_frame.target_cleared.connect(func() -> void:
		_current_target_entity = null
	)
	ui_layer.add_child(swg_target_frame)

	# 19. Boîte de Chat Spatial & Commandes Galactiques [Entrée]
	swg_chat_box = _SwgChatBoxScript.new()
	swg_chat_box.name = "SwgChatBox"
	swg_chat_box.command_executed.connect(_on_chat_command_executed)
	ui_layer.add_child(swg_chat_box)

	# 20. Système de Factions & Bureau de Recrutement GCW
	swg_faction_system = _SwgFactionSystemScript.new()
	swg_faction_system.name = "SwgFactionSystem"
	add_child(swg_faction_system)

	swg_faction_dialog = _SwgFactionDialogScript.new()
	swg_faction_dialog.name = "SwgFactionDialog"
	swg_faction_dialog.set_faction_system(swg_faction_system)
	swg_faction_dialog.faction_action_executed.connect(_on_faction_action_executed)
	ui_layer.add_child(swg_faction_dialog)

	swg_faction_system.overt_pvp_warning.connect(func(is_sf: bool) -> void:
		if is_sf:
			_show_notification("⚡ ALERTE SPECIAL FORCES : PvP MONDIAL ACTIF ! Vous êtes attaquable à vue !", Color(1.0, 0.2, 0.1))
			if swg_chat_box:
				swg_chat_box.add_log("[color=#ff2222]⚡ STATUT SPECIAL FORCES DÉCLARÉ : Les troupes et joueurs ennemis ouvriront le feu à vue ![/color]", "system")
		else:
			_show_notification("🛡 Vous êtes repassé en permission (On-Leave). Statut PvP désactivé.", Color(0.3, 0.9, 0.5))
	)

	# 21. Salon d'Image Designer & Sélection d'Espèces SWG
	swg_species_dialog = _SwgSpeciesDialogScript.new()
	swg_species_dialog.name = "SwgSpeciesDialog"
	swg_species_dialog.species_selected.connect(_on_species_selected)
	ui_layer.add_child(swg_species_dialog)

	# 22. Bandeau d'aide aux commandes
	_hud_prompt = Label.new()
	_hud_prompt.text = "◈ COMMANDES SWG PRE-CU : ZQSD=Déplacement | Tab=Cible | Entrée=Chat | E=Interagir | 1..8=Hotbar | I=Inventaire | T=Artisanat | M=Carte | K=Compétences | F6=Espèces | F5=Clonage"
	_hud_prompt.position = Vector2(16, 684)
	_hud_prompt.add_theme_font_size_override("font_size", 10)
	_hud_prompt.add_theme_color_override("font_color", Color(0.85, 0.95, 1.0, 0.85))
	ui_layer.add_child(_hud_prompt)


func _process(delta: float) -> void:
	# Gestion du timer de notification
	if _notify_timer > 0.0:
		_notify_timer -= delta
		if _notify_timer <= 0.0:
			_notify_label.visible = false

	# Détection de l'entité interactive la plus proche du joueur (portée 6.0m)
	_detect_nearby_interaction()

	# Mise à jour continue de la position du joueur sur la carte planétaire
	if swg_planetary_map and player:
		swg_planetary_map.update_player_position(player.global_position)

	# Ambiance Cantina & Dissipation de Fatigue
	if player != null:
		var lia_pos := Vector3(32.5, 0.6, -22)
		var dist_to_lia := player.global_position.distance_to(lia_pos)
		if dist_to_lia <= 14.0:
			if _player_fatigue > 0:
				_player_fatigue = maxi(0, _player_fatigue - int(delta * 8.0))
				if swg_ham_hud and swg_ham_hud.has_method("set_battle_fatigue"):
					swg_ham_hud.set_battle_fatigue(_player_fatigue)
			_cantina_buff_timer += delta
			if _cantina_buff_timer >= 12.0:
				_cantina_buff_timer = 0.0
				_show_notification("♫ Ambiance de Cantina : La danse de Lia dissipe votre fatigue et régénère votre esprit !", Color(0.95, 0.55, 0.95))

		if _is_watching_entertainer:
			_inspiration_meter += delta * 12.0
			if _inspiration_meter >= 100.0:
				_inspiration_meter = 0.0
				_grant_cantina_inspiration_buff()

	# Vérification des objectifs de missions actives
	_check_active_missions(delta)

	# Déplacement de la Caravane Marchande itinérante
	_update_merchant_caravan(delta)

	# IA active & gestion de l'aggro des prédateurs et Tuskens
	_update_ai_and_aggro(delta)


func _update_merchant_caravan(delta: float) -> void:
	if _caravan_root == null:
		return
	var speed: float = 1.8
	_caravan_root.position.x += _caravan_dir * speed * delta
	if _caravan_root.position.x > 58.0:
		_caravan_dir = -1.0
		_caravan_root.rotation_degrees.y = 180.0
	elif _caravan_root.position.x < -58.0:
		_caravan_dir = 1.0
		_caravan_root.rotation_degrees.y = 0.0


func _update_ai_and_aggro(delta: float) -> void:
	if player == null:
		return
	var p_pos: Vector3 = player.global_position

	for child in get_children():
		if not (child is CharacterBody3D) or child == player:
			continue
		var ent := child as CharacterBody3D
		if ent.get_meta("is_dead", false):
			continue

		var kind: String = str(ent.get_meta("entity_kind", ""))
		var is_faction_enemy: bool = false
		if swg_faction_system != null:
			var my_f: int = int(swg_faction_system.get("current_faction"))
			var is_sf: bool = bool(swg_faction_system.call("is_special_forces"))
			if is_sf:
				if (kind == "npc_stormtrooper" or kind == "npc_imperial_officer") and my_f == 2: # REBEL
					is_faction_enemy = true
				elif (kind == "npc_rebel_soldier" or kind == "npc_rebel_commando") and my_f == 1: # IMPERIAL
					is_faction_enemy = true

		var is_hostile: bool = (kind == "npc_tusken" or kind == "creature_jackal" or kind == "creature_beetle" or is_faction_enemy)
		if not is_hostile:
			continue

		var e_pos: Vector3 = ent.global_position
		var dist_to_p: float = e_pos.distance_to(p_pos)
		var ent_name: String = str(ent.get_meta("display_name", ent.name))

		# Rayon d'aggro : fortement atténué si camouflage d'odeur Scout actif [6]
		var aggro_radius: float = 3.5 if _camouflage_active else 18.0
		var current_state: String = str(ent.get_meta("aggro_state", "idle"))
		var is_aggro_forced: bool = bool(ent.get_meta("is_aggressive", false))

		if dist_to_p <= aggro_radius or is_aggro_forced or is_faction_enemy:
			if current_state != "chase":
				ent.set_meta("aggro_state", "chase")
				if is_faction_enemy:
					if swg_audio: swg_audio.play_blaster()
					_show_notification("⚔ COMBAT GCW : %s a détecté un agent Special Forces et engage le tir !" % ent_name, Color(1.0, 0.2, 0.2))
				elif is_aggro_forced:
					_show_notification("⚡ ALERTE NID : %s fonce sur vous pour défendre le tumulus !" % ent_name, Color(1.0, 0.4, 0.2))
				elif kind == "npc_tusken":
					if swg_audio: swg_audio.play_tusken_roar()
					_show_notification("⚠ ALERTE HOSTILE : %s brandit son Gaffi Stick et vous attaque !" % ent_name, Color(1.0, 0.3, 0.2))
				else:
					_show_notification("⚠ ATTENTION : %s s'élance sur vous en rugissant !" % ent_name, Color(1.0, 0.5, 0.2))

			# Poursuite : orientation vers le joueur et avancée
			ent.look_at(Vector3(p_pos.x, e_pos.y, p_pos.z), Vector3.UP)
			var move_speed: float = 4.0 if kind == "creature_jackal" else 3.2
			var dir := (p_pos - e_pos).normalized()
			dir.y = 0.0

			if dist_to_p > 1.9:
				ent.position += dir * move_speed * delta
			else:
				# Frappe de mêlée au corps à corps
				var atk_cd: float = float(ent.get_meta("attack_cooldown", 0.0)) - delta
				if atk_cd <= 0.0:
					atk_cd = 1.8
					ent.set_meta("attack_cooldown", atk_cd)
					var dmg_hp: int = randi_range(35, 65)
					var dmg_act: int = randi_range(20, 40)
					if swg_ham_hud:
						swg_ham_hud.damage_pool("health", dmg_hp)
						swg_ham_hud.damage_pool("action", dmg_act)
					if swg_combat_system:
						swg_combat_system.spawn_damage_number(p_pos, dmg_hp, Color(1.0, 0.2, 0.1))
					_show_notification("⚔ Frappe reçue de %s ! (-%d Santé, -%d Action)" % [ent_name, dmg_hp, dmg_act], Color(1.0, 0.25, 0.25))
					if swg_chat_box:
						swg_chat_box.add_log("[color=#ff5555]⚔ %s vous inflige %d dégâts de Santé et %d d'Action ![/color]" % [ent_name, dmg_hp, dmg_act], "combat")
				else:
					ent.set_meta("attack_cooldown", atk_cd)

		elif dist_to_p > 32.0 and current_state == "chase":
			ent.set_meta("aggro_state", "return")
			var home_pos: Vector3 = ent.get_meta("home_pos", e_pos)
			ent.look_at(Vector3(home_pos.x, e_pos.y, home_pos.z), Vector3.UP)
			_show_notification("✓ Vous avez distancé %s dans les dunes !" % ent_name, Color(0.3, 0.9, 0.5))


func _check_active_missions(_delta: float) -> void:
	if player == null:
		return
	var p_pos: Vector3 = player.global_position
	var completed_list: Array = []

	for m in _active_missions:
		if m.get("completed", false):
			continue
		var t_pos: Vector3 = m["target"]
		var dist: float = p_pos.distance_to(t_pos)

		var is_done := false
		if m["kind"] in ["recon", "delivery"]:
			if dist <= 8.0:
				is_done = true
		elif m["kind"] == "destroy":
			for child in get_children():
				if child is CharacterBody3D and child.get_meta("is_dead", false):
					if child.global_position.distance_to(t_pos) <= 25.0:
						is_done = true
						break
		elif m["kind"] == "lair_destroy":
			for lair in _lairs:
				if is_instance_valid(lair) and lair.is_lair_destroyed:
					if lair.global_position.distance_to(t_pos) <= 35.0:
						is_done = true
						break

		if is_done:
			m["completed"] = true
			completed_list.append(m)

	for m in completed_list:
		_complete_mission(m)


func _complete_mission(m: Dictionary) -> void:
	var m_id: String = m["id"]
	var m_title: String = m["title"]
	var rew: int = int(m["reward"])

	if _active_waypoints.has(m_id):
		var wp_node: Node3D = _active_waypoints[m_id]
		_tracked_entities.erase(wp_node)
		wp_node.queue_free()
		_active_waypoints.erase(m_id)

	if swg_planetary_map:
		swg_planetary_map.remove_waypoint(m_title)

	if swg_audio:
		swg_audio.play_mission_complete()

	_show_notification("🏆 MISSION RÉUSSIE : [%s] ! +%d Crédits Galactiques versés au compte !" % [m_title, rew], Color(0.2, 1.0, 0.4))
	_active_missions.erase(m)


func _check_lair_missions_completion(lair: Node3D) -> void:
	if lair == null:
		return
	var completed: Array = []
	for m in _active_missions:
		if m.get("completed", false):
			continue
		if m.get("kind") == "lair_destroy":
			var t_pos: Vector3 = m.get("target", Vector3.ZERO)
			if lair.global_position.distance_to(t_pos) <= 35.0:
				m["completed"] = true
				completed.append(m)
	for m in completed:
		_complete_mission(m)


func _detect_nearby_interaction() -> void:
	if player == null:
		return

	var p_pos: Vector3 = player.global_position
	var closest_node: Node = null
	var closest_dist: float = 6.0
	var closest_name: String = ""

	for child in get_children():
		if child == player or child == terrain_system or child is CanvasLayer or child is WorldEnvironment or child is DirectionalLight3D:
			continue
		if not (child is Node3D):
			continue

		var child_3d := child as Node3D
		var d: float = p_pos.distance_to(child_3d.global_position)
		if d < closest_dist:
			var d_name: String = ""
			if child_3d.has_meta("display_name"):
				d_name = str(child_3d.get_meta("display_name"))
			else:
				var c_name := child_3d.name.replace("_", " ")
				if "Terminal" in c_name or "Landspeeder" in c_name or "Vaporator" in c_name or "Camp" in c_name or "Harvester" in c_name or "Cantina" in c_name or "Shuttleport" in c_name or "Medical" in c_name:
					d_name = c_name

			if not d_name.is_empty():
				closest_dist = d
				closest_node = child_3d
				closest_name = d_name

	if closest_node != null:
		_current_target_entity = closest_node
		_interaction_prompt.visible = true
		_interaction_label.text = "◈ [E] ou [Clic-Droit] : %s ◈" % closest_name
	else:
		_current_target_entity = null
		_interaction_prompt.visible = false


func _unhandled_input(event: InputEvent) -> void:
	# Clic-Droit dans le monde 3D : Raycasting vers l'entité pour ouvrir le Menu Radial SWG
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_RIGHT and not event.pressed:
		_handle_mouse_radial_click(event.position)

	# Touche E : Interaction directe avec l'entité proche
	if event is InputEventKey and event.pressed and not event.echo:
		if swg_chat_box and swg_chat_box.is_chat_focused():
			return

		if event.keycode == KEY_E:
			if _current_target_entity != null:
				_interact_with_entity(_current_target_entity)
			else:
				_show_notification("Aucune entité à portée d'interaction immédiate.", Color(1.0, 0.7, 0.3))

		match event.keycode:
			KEY_TAB:
				_cycle_next_target()
			KEY_ENTER:
				if swg_chat_box:
					swg_chat_box.grab_chat_focus()
			KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, KEY_6, KEY_7, KEY_8:
				var slot_num := int(event.keycode) - int(KEY_1) + 1
				if swg_action_hotbar:
					swg_action_hotbar.trigger_slot(slot_num)
			KEY_F5:
				respawn_all_entities()
			KEY_F6:
				if swg_species_dialog: swg_species_dialog.toggle()
			KEY_C:
				if swg_character_sheet: swg_character_sheet.toggle()
			KEY_D, KEY_P:
				if swg_datapad_panel: swg_datapad_panel.toggle()
			KEY_B:
				if swg_bazaar_panel: swg_bazaar_panel.toggle()
			KEY_H:
				if swg_structure_panel: swg_structure_panel.toggle()
			KEY_K:
				if swg_skills_panel: swg_skills_panel.toggle()
			KEY_U:
				if swg_survey_panel: swg_survey_panel.toggle()
			KEY_I:
				if swg_inventory_panel: swg_inventory_panel.toggle()
			KEY_T:
				if swg_crafting_panel: swg_crafting_panel.toggle()
			KEY_M:
				if swg_planetary_map: swg_planetary_map.toggle()
			KEY_J:
				if swg_missions_dialog:
					if swg_missions_dialog.visible: swg_missions_dialog.close_panel()
					else: swg_missions_dialog.open_panel()
			KEY_F6:
				if player != null and player.has_method("cycle_skin"):
					var s_name: String = str(player.call("cycle_skin"))
					_show_notification("🎨 Apparence Joueur modifiée : %s" % s_name, Color(0.3, 0.95, 1.0))
			KEY_ESCAPE:
				_close_all_modals()
				if swg_target_frame:
					swg_target_frame.clear_target()


func _handle_mouse_radial_click(mouse_pos: Vector2) -> void:
	if _current_target_entity != null:
		var kind: String = "npc"
		if _current_target_entity.has_meta("entity_kind"):
			kind = str(_current_target_entity.get_meta("entity_kind"))
		elif "terminal" in _current_target_entity.name.to_lower():
			kind = "vendor"
		elif "dewback" in _current_target_entity.name.to_lower() or "chacal" in _current_target_entity.name.to_lower() or "creature" in _current_target_entity.name.to_lower():
			kind = "beast"
		elif "landspeeder" in _current_target_entity.name.to_lower():
			kind = "pet"
		elif "camp" in _current_target_entity.name.to_lower() or "house" in _current_target_entity.name.to_lower() or "cantina" in _current_target_entity.name.to_lower():
			kind = "structure"

		var display_name: String = str(_current_target_entity.get_meta("display_name", _current_target_entity.name))
		var ctx := {
			"name": display_name,
			"kind": kind,
			"node": _current_target_entity
		}
		if swg_radial_menu:
			swg_radial_menu.open_at(mouse_pos, ctx)
	else:
		# Menu radial générique de terrain
		var ctx := {
			"name": "Désert de Lost Heaven",
			"kind": "ground"
		}
		if swg_radial_menu:
			swg_radial_menu.open_at(mouse_pos, ctx)


func _interact_with_entity(ent: Node) -> void:
	var ent_name: String = ent.name
	var ent_kind: String = ""
	if ent.has_meta("entity_kind"):
		ent_kind = str(ent.get_meta("entity_kind"))
	var display_name: String = str(ent.get_meta("display_name", ent_name))

	# 1. PNJ Humains & Droïdes ➔ Boîte de Dialogue
	if ent_kind.begins_with("npc_"):
		if swg_dialog_box:
			swg_dialog_box.open_dialog(display_name, ent_kind)
		return

	# 2. Terminal de Missions
	if "Mission" in display_name or ent_kind == "term_mission":
		if swg_missions_dialog:
			swg_missions_dialog.open_panel()
		return

	# 3. Terminal Bancaire
	if "Bancaire" in display_name or "Bank" in ent_name or ent_kind == "term_bank":
		if swg_bank_dialog:
			swg_bank_dialog.open_panel()
		return

	# 4. Terminal de Bazar
	if "Bazar" in display_name or ent_kind == "term_bazaar":
		if swg_bazaar_panel:
			swg_bazaar_panel.open_panel()
		return

	# 5. Borne de Clonage & Assurance
	if "Clonage" in display_name or ent_kind == "term_clone":
		_show_notification("✓ Empreinte génétique enregistrée au Centre de Clonage de Lost Heaven (Assurance active) !", Color(0.2, 0.9, 1.0))
		return

	# 5b. Navette Spatiale & Terminal de Transport
	if "Shuttle" in ent_name or "Navette" in display_name or "Spatioport" in display_name or ent_kind == "term_travel":
		if swg_travel_dialog:
			swg_travel_dialog.open_panel()
		return

	# 5c. Extracteur Minier Harvester (Vidange Trémie)
	if "Harvester" in ent_name or ent_kind == "structure_harvester":
		var ore_amount: int = int(ent.get_meta("hopper_ore", 45))
		if ore_amount <= 0:
			ore_amount = randi_range(20, 50)
		_show_notification("⛏️ Trémie de l'extracteur vidée : +%d unités de Silice d'Oris & Minerai de Fer récoltées !" % ore_amount, Color(0.2, 1.0, 0.5))
		ent.set_meta("hopper_ore", 0)
		return

	# 6. Landspeeder X-34 (Monture / Véhicule)
	if "Landspeeder" in ent_name:
		_toggle_landspeeder_pilot()
		return

	# 6b. Monture Vivante Dewback des sables
	if "Dewback" in ent_name or ent_kind == "creature_dewback":
		_toggle_dewback_mount()
		return

	# 7. Campement de Scout Nomade (Feu de camp)
	if "Camp" in ent_name or ent_kind == "structure_camp":
		_show_notification("⛺ Repos au coin du feu de camp nomade : Fatigue dissipée & HAM régénéré !", Color(1.0, 0.8, 0.3))
		return

	# 8. Faune Sauvage (Créatures)
	if ent_kind.begins_with("creature_") or "Dewback" in ent_name or "Chacal" in ent_name:
		var ctx := {
			"name": display_name,
			"kind": "beast",
			"node": ent
		}
		if swg_radial_menu:
			swg_radial_menu.open_at(Vector2(640, 360), ctx)
		return

	# Cas générique : Ouvre le Menu Radial sur l'entité
	var ctx := {
		"name": display_name,
		"kind": "structure",
		"node": ent
	}
	if swg_radial_menu:
		swg_radial_menu.open_at(Vector2(640, 360), ctx)


func _toggle_landspeeder_pilot() -> void:
	_is_riding_speeder = not _is_riding_speeder
	if _is_riding_speeder and _is_riding_dewback:
		_toggle_dewback_mount()
	if player:
		if _is_riding_speeder:
			player.SPEED_SPRINT = 18.0
			player.SPEED_WALK = 10.0
			if _mounted_speeder_visual == null:
				_mounted_speeder_visual = _SwgAssetPipelineScript.build_landspeeder(Vector3(0, 0.0, 0), 180.0)
				_mounted_speeder_visual.name = "MountedLandspeederX34"
				player.add_child(_mounted_speeder_visual)
			else:
				_mounted_speeder_visual.visible = true
			if swg_audio:
				swg_audio.set_speeder_sound(true)
			_show_notification("🚀 Landspeeder X-34 engagé ! Vitesse maximale propulsée (Touche [8] pour ranger).", Color(0.3, 1.0, 0.6))
		else:
			player.SPEED_SPRINT = 6.2
			player.SPEED_WALK = 3.6
			if _mounted_speeder_visual != null:
				_mounted_speeder_visual.visible = false
			if swg_audio:
				swg_audio.set_speeder_sound(false)
			_show_notification("🚶 Vous avez rangé le Landspeeder dans votre Datapad.", Color(0.9, 0.95, 1.0))


func _toggle_dewback_mount() -> void:
	_is_riding_dewback = not _is_riding_dewback
	if _is_riding_dewback and _is_riding_speeder:
		_toggle_landspeeder_pilot()
	if player:
		if _is_riding_dewback:
			player.SPEED_SPRINT = 10.5
			player.SPEED_WALK = 6.5
			if _mounted_dewback_visual == null:
				_mounted_dewback_visual = _SwgAssetPipelineScript.build_dewback_mount_visual(180.0)
				player.add_child(_mounted_dewback_visual)
			else:
				_mounted_dewback_visual.visible = true
			_show_notification("🦎 Vous êtes monté sur le dos du grand Dewback des sables ! (Touche E pour descendre).", Color(0.4, 1.0, 0.5))
		else:
			player.SPEED_SPRINT = 6.2
			player.SPEED_WALK = 3.6
			if _mounted_dewback_visual != null:
				_mounted_dewback_visual.visible = false
			_show_notification("🚶 Vous descendez du Dewback.", Color(0.9, 0.95, 1.0))


func _on_travel_ticket_purchased(dest_id: String, dest_name: String, cost_cr: int, world_pos: Vector3) -> void:
	if swg_audio:
		swg_audio.play_shuttle_takeoff()

	_show_notification("🚀 EMBARQUEMENT NAVETTE : Vol vers %s (Coût : %d cr)" % [dest_name, cost_cr], Color(0.2, 0.9, 1.0))

	if _hyperspace_overlay:
		_hyperspace_overlay.visible = true

	# Ascension animée de la navette Lambda
	if _shuttle_visual_ref:
		var tween := create_tween()
		tween.tween_property(_shuttle_visual_ref, "position:y", 45.0, 1.8).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)

	await get_tree().create_timer(2.0).timeout

	if player:
		player.global_position = world_pos + Vector3(0, 1.0, 0)

	if _shuttle_visual_ref:
		_shuttle_visual_ref.position.y = 0.8

	if _hyperspace_overlay:
		_hyperspace_overlay.visible = false

	if swg_audio:
		swg_audio.play_droid()

	_show_notification("✨ ARRIVÉE À %s ! Atterrissage navette réussi." % dest_name.to_upper(), Color(0.3, 1.0, 0.5))


func _on_hotbar_action_triggered(slot_idx: int, action_id: String) -> void:
	match action_id:
		"blaster_shot":
			_execute_blaster_attack(false)
		"aim_shot":
			_execute_blaster_attack(true)
		"dizzy_shot":
			_execute_dizzy_shot()
		"bacta_stim":
			_execute_bacta_stim()
		"survey_tool":
			_execute_survey_pulse()
		"mask_scent":
			_camouflage_active = not _camouflage_active
			if _camouflage_active:
				_show_notification("🌿 Camouflage d'odeur Scout ACTIVÉ : Rayon de détection ennemis réduit à 3.5m !", Color(0.3, 1.0, 0.6))
			else:
				_show_notification("🌿 Camouflage d'odeur Scout DÉSACTIVÉ.", Color(0.9, 0.8, 0.4))
		"pet_command":
			_show_notification("🐾 Ordre au familier transmis : Couverture défensive engagée.", Color(0.9, 0.45, 0.7))
		"speeder_mount":
			_toggle_landspeeder_pilot()


func _execute_blaster_attack(is_aim: bool) -> void:
	if player == null or swg_combat_system == null:
		return

	var p_pos: Vector3 = player.global_position
	var target_node: Node3D = _current_target_entity as Node3D
	var t_pos: Vector3 = p_pos - player.global_transform.basis.z * 25.0 # Direction regard par défaut

	# Si aucune cible sélectionnée, recherche de la créature ou bête la plus proche (rayon 35m)
	if target_node == null:
		var best_dist := 35.0
		for child in get_children():
			if child is CharacterBody3D and child != player:
				var d: float = p_pos.distance_to(child.global_position)
				if d < best_dist:
					best_dist = d
					target_node = child
					break

	if target_node != null:
		t_pos = target_node.global_position

	if swg_audio:
		swg_audio.play_blaster()

	swg_combat_system.fire_blaster_bolt(p_pos, t_pos, is_aim)

	var dmg: int = 160 if is_aim else 85
	var col: Color = Color(0.2, 0.9, 1.0) if is_aim else Color(1.0, 0.3, 0.2)
	swg_combat_system.spawn_damage_number(t_pos, dmg, col)

	if target_node != null:
		var t_name: String = str(target_node.get_meta("display_name", target_node.name))

		# Cas particulier : Nid de Créatures (Lair Pre-CU)
		if target_node.has_method("harvest_debris"):
			target_node.call("take_damage", dmg, player)
			var hp: int = int(target_node.get("current_hp"))
			if hp <= 0:
				_show_notification("💥 NID ÉRADIQUÉ : %s détruit ! Décombres disponibles pour pillage d'œufs rares." % t_name, Color(1.0, 0.85, 0.2))
				if swg_chat_box:
					swg_chat_box.add_log("[color=#ffcc00]💥 VICTOIRE : Le nid %s s'est effondré ! Butin rare déverrouillé.[/color]" % t_name, "combat")
				if swg_audio:
					swg_audio.play_mission_complete()
				_check_lair_missions_completion(target_node)
			else:
				_show_notification("💥 Nid touché : %d dégâts (PV restants : %d) ! ALERTE DE MEUTE !" % [dmg, hp], col)
				if swg_chat_box:
					swg_chat_box.add_log("[color=#ff6633]💥 Blaster ➔ %s : -%d PV (Santé : %d). Les bêtes du nid contre-attaquent ![/color]" % [t_name, dmg, hp], "combat")
			if swg_target_frame:
				swg_target_frame.set_target(target_node, player)
			return

		var hp: int = int(target_node.get_meta("current_health", 250)) - dmg
		target_node.set_meta("current_health", hp)

		if hp <= 0:
			var orig_name: String = str(target_node.get_meta("original_name", t_name))
			var orig_kind: String = str(target_node.get_meta("original_kind", target_node.get_meta("entity_kind", "npc")))
			target_node.set_meta("original_name", orig_name)
			target_node.set_meta("original_kind", orig_kind)
			target_node.set_meta("is_dead", true)
			target_node.set_meta("entity_kind", "corpse")
			target_node.set_meta("display_name", "[Cadavre] %s" % orig_name)
			target_node.rotation_degrees.z = 90.0 # Bête/PNJ couché au sol

			var is_npc: bool = orig_kind.begins_with("npc_")
			var delay: float = 8.0 if is_npc else 18.0
			_show_notification("☠ %s abattu ! (Respawn clonage dans %ds, ou touche F5)" % [orig_name, int(delay)], Color(1.0, 0.8, 0.2))
			if swg_chat_box:
				swg_chat_box.add_log("[color=#ff3333]☠ %s a été abattu ! Dépouille disponible pour fouille ou dépeçage.[/color]" % orig_name, "combat")

			if is_inside_tree() and get_tree():
				get_tree().create_timer(delay).timeout.connect(func() -> void:
					if is_instance_valid(target_node) and target_node.get_meta("is_dead", false):
						_respawn_entity(target_node as CharacterBody3D)
				)
		else:
			_show_notification("⚔ %s touché : %d dégâts HAM (PV restants : %d) !" % [t_name, dmg, hp], col)
			if swg_chat_box:
				swg_chat_box.add_log("[color=#ff9944]⚔ Blaster ➔ %s : -%d Santé (PV : %d)[/color]" % [t_name, dmg, hp], "combat")

		if swg_target_frame:
			swg_target_frame.set_target(target_node, player)
	else:
		_show_notification("⚔ Tir de blaster dans les dunes de Lost Heaven !", col)


## Réanime instantanément toutes les entités abattues via le protocole de clonage
func respawn_all_entities() -> void:
	var count := 0
	for child in get_children():
		if child is CharacterBody3D and child != player:
			if child.get_meta("is_dead", false) or child.rotation_degrees.z != 0.0:
				_respawn_entity(child as CharacterBody3D)
				count += 1
	_show_notification("✨ PROTOCOLE DE CLONAGE D'URGENCE : %d citoyen(s) et créature(s) réanimé(s) !" % count, Color(0.2, 1.0, 0.6))


func _respawn_entity(ent: CharacterBody3D) -> void:
	if not is_instance_valid(ent):
		return
	var orig_name: String = str(ent.get_meta("original_name", ent.name))
	var orig_kind: String = str(ent.get_meta("original_kind", "npc"))
	ent.set_meta("is_dead", false)
	ent.set_meta("entity_kind", orig_kind)
	ent.set_meta("display_name", orig_name)
	ent.set_meta("current_health", int(ent.get_meta("max_health", 300)))
	ent.rotation_degrees.z = 0.0 # Remis debout
	_show_notification("✨ %s s'est relevé(e) et a été réanimé(e) !" % orig_name, Color(0.2, 0.9, 1.0))


func _execute_dizzy_shot() -> void:
	if player == null or swg_combat_system == null:
		return
	var p_pos: Vector3 = player.global_position
	var t_pos: Vector3 = p_pos - player.global_transform.basis.z * 20.0
	if _current_target_entity is Node3D:
		t_pos = _current_target_entity.global_position
	swg_combat_system.fire_blaster_bolt(p_pos, t_pos, false)
	swg_combat_system.spawn_damage_number(t_pos, 45, Color(1.0, 0.85, 0.2))
	_show_notification("💫 Tir Étourdissant porté ! Cible affectée par l'état Dizzy (Perte d'équilibre).", Color(1.0, 0.85, 0.2))


func _execute_bacta_stim() -> void:
	_show_notification("💉 Stimpack Bacta d'urgence consommé : +250 Santé et +250 Action restaurées !", Color(0.2, 1.0, 0.5))


func _execute_survey_pulse() -> void:
	if player == null or swg_combat_system == null:
		return
	swg_combat_system.trigger_survey_pulse(player.global_position)
	_show_notification("📡 Sonde Géologique : Filon Ferrique Détecté (Pureté 94%) ! Échantillon de minerai brut extrait.", Color(0.2, 0.85, 1.0))


func _show_notification(msg: String, col: Color = Color(0.2, 1.0, 0.5)) -> void:
	if _notify_label:
		_notify_label.text = "◈ %s ◈" % msg
		_notify_label.add_theme_color_override("font_color", col)
		_notify_label.visible = true
		_notify_timer = 4.0


func _on_dialog_option_selected(opt_id: String, npc_name: String) -> void:
	match opt_id:
		"watch_dance":
			_show_notification("♫ Lia danse sous les spots de la cantina : 50 Fatigue dissipée !", Color(0.9, 0.5, 0.9))
		"listen_music":
			_show_notification("🎷 L'orchestre Bith joue un ragtime de cantina : Buff de Mental accordé !", Color(0.3, 0.85, 1.0))
		"buy_drink":
			_show_notification("🍺 Vous buvez un grand verre de Lait Bleu frais : 300 Action restaurée !", Color(0.2, 1.0, 0.4))
		"buy_rations":
			_show_notification("🍖 Achat de 5 Rations de survie à Jax Moro (50 crédits débités).", Color(0.95, 0.8, 0.2))
		"heal_ham":
			_show_notification("💉 Docteur Vane applique un stimulant bacta : Barres HAM restaurées à 100% !", Color(0.1, 0.95, 0.9))
		"bacta_bath":
			_show_notification("💧 Bain en cuve de Bacta : Tous les traumatismes et poisons sont guéris !", Color(0.2, 1.0, 0.8))
		"open_housing":
			if swg_structure_panel: swg_structure_panel.open_panel()
		"open_skills":
			if swg_skills_panel: swg_skills_panel.open_panel()
		"open_bazaar":
			if swg_bazaar_panel: swg_bazaar_panel.open_panel()
		"open_missions":
			if swg_missions_dialog: swg_missions_dialog.open_panel()
		"open_travel":
			if swg_travel_dialog: swg_travel_dialog.open_panel()
		"shuttle_status":
			_show_notification("🚀 Corran : « Navette Lambda en phase d'embarquement sur la piste, départ imminent ! »", Color(0.2, 0.95, 1.0))
		"droid_scan":
			if swg_audio: swg_audio.play_droid()
			_show_notification("🔍 R2-T8 analyse le sous-sol : Gisement de fer repéré à 120m au Nord-Est.", Color(0.2, 0.8, 1.0))
		"droid_whistle":
			if swg_audio: swg_audio.play_droid()
			_show_notification("🤖 R2-T8 émet un gazouillis joyeux et fait tourner son dôme !", Color(0.2, 0.95, 1.0))
		_:
			_show_notification("Action exécutée : %s avec %s." % [opt_id, npc_name])


func _on_mission_accepted(mission_id: String, reward_cr: int) -> void:
	var m_target := Vector3.ZERO
	var m_title := "Contrat de Mission"
	var m_kind := "delivery"

	match mission_id:
		"mis_lair_chacals":
			m_target = Vector3(-130, 0, -65)
			m_title = "Destruction de Nid : Chacals des Dunes"
			m_kind = "lair_destroy"
		"mis_lair_scarabees":
			m_target = Vector3(140, 0, 95)
			m_title = "Extermination : Nid de Scarabées"
			m_kind = "lair_destroy"
		"mis_chacals_ouest":
			m_target = Vector3(-92, 0, -38)
			m_title = "Chasse : Meute de Chacals Dorés"
			m_kind = "destroy"
			_spawn_npc("Chacal Doré Alpha", m_target, Color(0.85, 0.6, 0.2), "creature_jackal")
		"mis_recon_ksar":
			m_target = Vector3(-65, 0, 0)
			m_title = "Patrouille : Porte Ouest & Ksar"
			m_kind = "recon"
		"mis_livraison_eau":
			m_target = Vector3(-95, 0, -45)
			m_title = "Ravitaillement : Eau Pure Nomade"
			m_kind = "delivery"
		"mis_scarabee_obsidien":
			m_target = Vector3(88, 0, 78)
			m_title = "Élimination : Scarabée Obsidien"
			m_kind = "destroy"
			_spawn_npc("Scarabée Obsidien Géant", m_target, Color(0.2, 0.2, 0.25), "creature_juvenile")
		_:
			m_target = Vector3(randf_range(-60, 60), 0, randf_range(-60, 60))
			m_title = "Mission Galactique %s" % mission_id

	var mission_data := {
		"id": mission_id,
		"title": m_title,
		"target": m_target,
		"reward": reward_cr,
		"kind": m_kind,
		"completed": false
	}
	_active_missions.append(mission_data)

	_spawn_waypoint_beacon(mission_id, m_target, m_title)

	if swg_planetary_map and swg_planetary_map.has_method("add_waypoint"):
		swg_planetary_map.add_waypoint(Vector2(m_target.x, m_target.z), m_title)

	_show_notification("📜 Contrat [%s] accepté ! Balise Waypoint GPS activée à (%dm, %dm)." % [m_title, int(m_target.x), int(m_target.z)], Color(1.0, 0.85, 0.2))


func _spawn_waypoint_beacon(wp_id: String, pos: Vector3, label_text: String) -> void:
	if _active_waypoints.has(wp_id):
		return
	var root := Node3D.new()
	root.name = "WaypointBeacon_" + wp_id
	root.position = pos

	var beam := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = 0.18
	cyl.bottom_radius = 0.28
	cyl.height = 28.0
	beam.mesh = cyl
	beam.position = Vector3(0, 14.0, 0)

	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.2, 0.95, 1.0, 0.65)
	mat.emission_enabled = true
	mat.emission = Color(0.2, 0.95, 1.0)
	mat.emission_energy_multiplier = 3.5
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	beam.set_surface_override_material(0, mat)
	root.add_child(beam)

	var ring := MeshInstance3D.new()
	var torus := TorusMesh.new()
	torus.inner_radius = 1.8
	torus.outer_radius = 2.2
	ring.mesh = torus
	ring.position = Vector3(0, 0.1, 0)
	ring.set_surface_override_material(0, mat)
	root.add_child(ring)

	var lbl := Label3D.new()
	lbl.text = "★ WAYPOINT MISSION ★\n%s" % label_text
	lbl.position = Vector3(0, 3.2, 0)
	lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lbl.font_size = 18
	lbl.modulate = Color(0.3, 1.0, 0.9)
	root.add_child(lbl)

	add_child(root)
	_active_waypoints[wp_id] = root
	_tracked_entities.append(root)


func _on_bank_balance_updated(new_bal: int) -> void:
	_show_notification("💰 Solde Bancaire Galactique mis à jour : %d crédits." % new_bal, Color(0.2, 1.0, 0.4))


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
		"inventory": if swg_inventory_panel: swg_inventory_panel.toggle()
		"talents": if swg_crafting_panel: swg_crafting_panel.toggle()
		"vendors": if swg_bazaar_panel: swg_bazaar_panel.toggle()
		"housing": if swg_structure_panel: swg_structure_panel.toggle()
		"missions":
			if swg_missions_dialog:
				if swg_missions_dialog.visible: swg_missions_dialog.close_panel()
				else: swg_missions_dialog.open_panel()
		"map": if swg_planetary_map: swg_planetary_map.toggle()


func _on_radial_action_selected(act: String, ctx: Dictionary) -> void:
	var t_name: String = str(ctx.get("name", "Cible"))
	print("[SWG 3D] Action radiale : %s sur %s" % [act, t_name])

	match act:
		"open_faction_recruiter":
			if swg_faction_dialog: swg_faction_dialog.open_panel()
		"attack_lair":
			_execute_blaster_attack(false)
		"loot_lair":
			var t_node: Node = ctx.get("node")
			if t_node != null and t_node.has_method("harvest_debris"):
				var res: Dictionary = t_node.call("harvest_debris")
				if res.get("ok", false):
					var cr: int = int(res.get("credits", 0))
					var rare_name: String = str(res.get("rare_item", "Œuf Rare"))
					if swg_inventory_panel and swg_inventory_panel.has_method("add_item"):
						swg_inventory_panel.add_item({
							"id": "creature_egg",
							"name": rare_name,
							"icon": "🥚",
							"slot": "crafting",
							"qty": 1,
							"desc": "Œuf rare de bête des dunes (Qualité OQ 950). Ingrédient très recherché des bio-ingénieurs."
						})
						swg_inventory_panel.add_item({
							"id": "predator_meat_alpha",
							"name": "Viande de Prédateur Alpha",
							"icon": "🥩",
							"slot": "crafting",
							"qty": 6,
							"desc": "Viande musculaire pure extraite du nid détruit."
						})
					if swg_audio: swg_audio.play_harvest()
					_show_notification("💰 BUTIN DE NID RÉCOLTÉ : +%d Crédits et [%s] ajoutés au Sac à Dos [I] !" % [cr, rare_name], Color(1.0, 0.9, 0.2))
					if swg_chat_box:
						swg_chat_box.add_log("[color=#ffff33]💰 Vous avez fouillé les décombres du nid : +%d crédits, 1x %s, 6x Viande Alpha.[/color]" % [cr, rare_name], "spatial")
				else:
					_show_notification("⚠ %s" % res.get("reason", "Impossible de fouiller"), Color(1.0, 0.4, 0.4))
		"converse":
			if swg_dialog_box:
				swg_dialog_box.open_dialog(t_name, str(ctx.get("kind", "npc")))
		"vendor_browse":
			if swg_bazaar_panel: swg_bazaar_panel.open_panel()
		"house_manage", "house_maintenance":
			if swg_structure_panel: swg_structure_panel.open_panel()
		"house_enter":
			if player:
				var t_node: Node = ctx.get("node")
				var t_pos: Vector3 = (t_node as Node3D).global_position if t_node is Node3D else (_current_target_entity.global_position if _current_target_entity is Node3D else player.global_position)
				player.global_position = t_pos + Vector3(0, 0.2, 0)
				if swg_audio: swg_audio.play_shuttle_land()
				_show_notification("🚪 Vous franchissez la porte et entrez dans le salon de la maison !", Color(0.3, 0.95, 1.0))
				if swg_chat_box:
					swg_chat_box.add_log("[color=#33ccff]🚪 Vous êtes entré à l'intérieur du bâtiment.[/color]", "spatial")
		"house_decorate":
			_show_notification("🎨 Mode Décoration 3D : Ouvrez le Sac à Dos [I] pour poser un meuble ou objet !", Color(0.95, 0.75, 0.3))
		"watch_entertainer":
			_show_notification("♫ Vous admirez la prestation de %s : Fatigue dissipée !" % t_name, Color(0.9, 0.5, 0.9))
		"treat_wounds":
			_show_notification("💉 Soins appliqués à %s : Blessures HAM stabilisées !" % t_name, Color(0.2, 0.9, 0.9))
		"open_skills":
			if swg_skills_panel: swg_skills_panel.open_panel()
		"tame_creature":
			_show_notification("🐾 Domptage Creature Handler réussi ! %s est maintenant votre familier loyal !" % t_name, Color(0.2, 1.0, 0.5))
		"harvest_meat":
			var t_node: Node = ctx.get("node")
			var q := randi_range(30, 50)
			if swg_inventory_panel and swg_inventory_panel.has_method("add_item"):
				swg_inventory_panel.add_item({
					"id": "meat_wild",
					"name": "Viande Carnée Sauvage",
					"icon": "🥩",
					"slot": "crafting",
					"qty": q,
					"desc": "Viande fraîche de bête des dunes (Qualité OQ 780, PE 650)"
				})
			if swg_audio: swg_audio.play_harvest()
			_mark_corpse_harvested(t_node)
			_show_notification("🥩 Dépeçage Scout : +%d Viande Carnée ajoutée dans le Sac à Dos [I] !" % q, Color(0.95, 0.75, 0.2))
		"harvest_hide":
			var t_node: Node = ctx.get("node")
			var q := randi_range(20, 40)
			if swg_inventory_panel and swg_inventory_panel.has_method("add_item"):
				swg_inventory_panel.add_item({
					"id": "hide_coarse",
					"name": "Cuir Brut des Sables",
					"icon": "🥋",
					"slot": "crafting",
					"qty": q,
					"desc": "Peau tannée pour armures et sellerie (Qualité OQ 820, DR 710)"
				})
			if swg_audio: swg_audio.play_harvest()
			_mark_corpse_harvested(t_node)
			_show_notification("🥋 Dépeçage Scout : +%d Cuir Brut ajouté dans le Sac à Dos [I] !" % q, Color(0.95, 0.75, 0.2))
		"harvest_bone", "harvest_fauna":
			var t_node: Node = ctx.get("node")
			var q := randi_range(15, 30)
			if swg_inventory_panel and swg_inventory_panel.has_method("add_item"):
				swg_inventory_panel.add_item({
					"id": "bone_dense",
					"name": "Os Squelettique Dense",
					"icon": "🦴",
					"slot": "crafting",
					"qty": q,
					"desc": "Structure osseuse minéralisée pour bio-ingénierie (Qualité OQ 890)"
				})
			if swg_audio: swg_audio.play_harvest()
			_mark_corpse_harvested(t_node)
			_show_notification("🦴 Dépeçage Scout : +%d Os Minéralisé ajouté dans le Sac à Dos [I] !" % q, Color(0.95, 0.75, 0.2))
		"loot_corpse":
			var t_node: Node = ctx.get("node")
			if swg_inventory_panel and swg_inventory_panel.has_method("add_item"):
				swg_inventory_panel.add_item({
					"id": "credits_pouch",
					"name": "Bourse de Crédits Tuskens",
					"icon": "💰",
					"slot": "usable",
					"qty": 1,
					"desc": "Bourse en cuir contenant 125 crédits galactiques"
				})
				swg_inventory_panel.add_item({
					"id": "medpack_a",
					"name": "Stimpack Médical A",
					"icon": "💉",
					"slot": "usable",
					"qty": 2,
					"desc": "Restaure 250 Santé et 250 Action"
				})
			if swg_audio: swg_audio.play_harvest()
			_mark_corpse_harvested(t_node)
			_show_notification("💰 Butin pillé : Bourse de crédits & 2 Stimpacks Bacta transférés dans l'Inventaire [I] !", Color(1.0, 0.85, 0.2))
		"tactical_strike":
			_show_notification("⚔ Attaque tactique HAM portée sur %s !" % t_name, Color(1.0, 0.3, 0.3))
		"deploy_camp":
			if player:
				var camp_node: Node3D = _SwgAssetPipelineScript.build_scout_camp(player.global_position)
				camp_node.name = "Player_Scout_Camp_%d" % randi_range(100, 999)
				camp_node.set_meta("display_name", "Mon Bivouac de Scout")
				camp_node.set_meta("entity_kind", "structure_camp")
				add_child(camp_node)
				_tracked_entities.append(camp_node)
				if swg_planetary_map:
					swg_planetary_map.add_waypoint(Vector2(player.global_position.x, player.global_position.z), "Mon Bivouac")
				_show_notification("⛺ Bivouac de Scout déployé avec succès ! Regen HAM boostée & feu allumé.", Color(1.0, 0.85, 0.3))
		"deploy_harvester":
			if player:
				var harv_node: Node3D = _SwgAssetPipelineScript.build_mining_harvester(player.global_position, 0.0)
				harv_node.name = "Player_Personal_Harvester_%d" % randi_range(100, 999)
				harv_node.set_meta("display_name", "Mon Extracteur Minier Personnel")
				harv_node.set_meta("entity_kind", "structure_harvester")
				harv_node.set_meta("hopper_ore", 35)
				add_child(harv_node)
				_tracked_entities.append(harv_node)
				if swg_planetary_map:
					swg_planetary_map.add_waypoint(Vector2(player.global_position.x, player.global_position.z), "Mon Extracteur")
				_show_notification("⛏️ Extracteur Minier personnel déployé ! Trémie active en forage.", Color(0.2, 0.9, 1.0))
		"mount_dewback":
			_toggle_dewback_mount()
		"examine":
			_show_notification("🔍 Examen détaillé : %s (État optimal, intégrité 100%%)." % t_name, Color(0.85, 0.95, 1.0))
		_:
			_show_notification("Action %s effectuée sur %s." % [act, t_name])


func _close_all_modals() -> void:
	if swg_radial_menu and swg_radial_menu.visible: swg_radial_menu.close_menu()
	if swg_dialog_box and swg_dialog_box.visible: swg_dialog_box.close_dialog()
	if swg_missions_dialog and swg_missions_dialog.visible: swg_missions_dialog.close_panel()
	if swg_travel_dialog and swg_travel_dialog.visible: swg_travel_dialog.close_panel()
	if swg_bank_dialog and swg_bank_dialog.visible: swg_bank_dialog.close_panel()
	if swg_character_sheet and swg_character_sheet.visible: swg_character_sheet.close_panel()
	if swg_datapad_panel and swg_datapad_panel.visible: swg_datapad_panel.close_panel()
	if swg_bazaar_panel and swg_bazaar_panel.visible: swg_bazaar_panel.close_panel()
	if swg_structure_panel and swg_structure_panel.visible: swg_structure_panel.close_panel()
	if swg_skills_panel and swg_skills_panel.visible: swg_skills_panel.close_panel()
	if swg_survey_panel and swg_survey_panel.visible: swg_survey_panel.close_panel()
	if swg_experiment_panel and swg_experiment_panel.visible: swg_experiment_panel.close_panel()
	if swg_inventory_panel and swg_inventory_panel.visible: swg_inventory_panel.close_panel()
	if swg_crafting_panel and swg_crafting_panel.visible: swg_crafting_panel.close_panel()
	if swg_planetary_map and swg_planetary_map.visible: swg_planetary_map.close_panel()


func _mark_corpse_harvested(node: Node) -> void:
	if node and is_instance_valid(node):
		node.set_meta("is_harvested", true)
		var d_name: String = str(node.get_meta("display_name", node.name))
		node.set_meta("display_name", "[Vidé] " + d_name.replace("[Cadavre] ", ""))
		for ch in node.get_children():
			if ch is Label3D:
				ch.text = "[Vidé] Dépouille récoltée"
				ch.modulate = Color(0.5, 0.5, 0.5, 0.6)


func _on_inventory_item_used(item_id: String) -> void:
	match item_id:
		"medpack_a":
			if swg_ham_hud:
				swg_ham_hud.heal_pool("health", 250)
				swg_ham_hud.heal_pool("action", 250)
			if swg_audio:
				swg_audio.play_consume()
			_show_notification("💉 Stimpack Bacta appliqué : +250 Santé et +250 Action restaurées !", Color(0.2, 1.0, 0.6))
		"ration_lh":
			if swg_ham_hud:
				swg_ham_hud.heal_pool("health", 150)
				swg_ham_hud.heal_pool("mind", 200)
			_player_fatigue = maxi(0, _player_fatigue - 20)
			if swg_ham_hud and swg_ham_hud.has_method("set_battle_fatigue"):
				swg_ham_hud.set_battle_fatigue(_player_fatigue)
			if swg_audio:
				swg_audio.play_consume()
			_show_notification("🍖 Ration des Dunes consommée : +150 Santé, +200 Mental & Fatigue dissipée !", Color(1.0, 0.85, 0.3))
		"blue_milk":
			if swg_ham_hud:
				swg_ham_hud.heal_pool("action", 300)
				swg_ham_hud.heal_pool("mind", 300)
			_player_fatigue = maxi(0, _player_fatigue - 30)
			if swg_ham_hud and swg_ham_hud.has_method("set_battle_fatigue"):
				swg_ham_hud.set_battle_fatigue(_player_fatigue)
			if swg_audio:
				swg_audio.play_consume()
			_show_notification("🥛 Grand verre de Lait Bleu frais : +300 Action, +300 Mental & Réconfort total !", Color(0.3, 0.85, 1.0))
		"credits_pouch":
			if swg_audio:
				swg_audio.play_mission_complete()
			_show_notification("💰 Bourse de crédits ouverte : +125 Crédits Galactiques crédités !", Color(1.0, 0.85, 0.2))
		_:
			_show_notification("Objet [%s] utilisé avec succès." % item_id, Color(0.85, 0.95, 1.0))


var _target_cycle_index: int = 0

func _cycle_next_target() -> void:
	if player == null:
		return
	var p_pos: Vector3 = player.global_position
	var candidates: Array = []

	for child in get_children():
		if child is CharacterBody3D and child != player:
			var d: float = p_pos.distance_to(child.global_position)
			if d <= 45.0:
				candidates.append({"node": child, "dist": d})

	if candidates.is_empty():
		_show_notification("Aucune cible vivante dans un rayon de 45m.", Color(0.8, 0.8, 0.8))
		return

	candidates.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		return float(a["dist"]) < float(b["dist"])
	)

	_target_cycle_index = (_target_cycle_index + 1) % candidates.size()
	var chosen_node: Node = candidates[_target_cycle_index]["node"]
	_current_target_entity = chosen_node
	var t_name: String = str(chosen_node.get_meta("display_name", chosen_node.name))

	if swg_target_frame:
		swg_target_frame.set_target(chosen_node, player)

	if swg_audio:
		swg_audio.play_droid()

	_show_notification("🎯 Cible verrouillée [Tab] : %s (%.1fm)" % [t_name, candidates[_target_cycle_index]["dist"]], Color(0.25, 0.95, 1.0))


func _on_chat_command_executed(cmd: String, _args: String) -> void:
	match cmd:
		"dance":
			_show_notification("♫ Vous esquissez les pas de danse de la cantina !", Color(0.9, 0.5, 0.9))
			if swg_chat_box: swg_chat_box.add_log("[color=#ff77ee]♫ Vous dansez avec grâce ![/color]", "spatial")
		"kneel":
			if player and player.has_method("set_posture"):
				player.call("set_posture", "kneeling")
				_show_notification("🧎 Posture: Accroupi (Kneeling)", Color(0.3, 0.9, 1.0))
		"prone":
			if player and player.has_method("set_posture"):
				player.call("set_posture", "prone")
				_show_notification("🛌 Posture: Couché (Prone)", Color(0.3, 0.9, 1.0))
		"stand":
			if player and player.has_method("set_posture"):
				player.call("set_posture", "standing")
				_show_notification("🧍 Posture: Debout (Standing)", Color(0.3, 0.9, 1.0))
		"camp":
			_on_radial_action_selected("deploy_camp", {})
		"harvester":
			_on_radial_action_selected("deploy_harvester", {})
		"speeder":
			_toggle_landspeeder_pilot()
		"dewback":
			_toggle_dewback_mount()
		"clone", "suicide":
			if player:
				player.global_position = Vector3(-28, 0.2, 18.2)
				_show_notification("🏥 Rapatriement d'urgence au Centre Médical !", Color(0.2, 1.0, 0.8))
				if swg_chat_box: swg_chat_box.add_log("[color=#44ffcc]🏥 Transfert d'urgence au Centre de Clonage.[/color]", "system")
		"skin":
			if player and player.has_method("cycle_skin"):
				var s_name: String = str(player.call("cycle_skin"))
				_show_notification("🎨 Apparence Joueur modifiée : %s" % s_name, Color(0.3, 0.95, 1.0))
		"pvp", "faction":
			if swg_faction_dialog: swg_faction_dialog.toggle()
		"overt":
			if swg_faction_system: swg_faction_system.declare_special_forces()
		"watch":
			_start_watching_entertainer(_args)
		"listen":
			_start_listening_music(_args)
		"flourish":
			var f_idx: int = int(_args.strip_edges()) if _args.strip_edges().is_valid_int() else randi_range(1, 8)
			_execute_entertainer_flourish(f_idx)
		"house", "placehouse":
			_place_player_house_at_current_pos()
		"species", "race":
			if swg_species_dialog: swg_species_dialog.toggle()
		_:
			if swg_chat_box:
				swg_chat_box.add_log("[color=#ff9999]Commande inconnue : /%s. Tapez /help pour l'aide.[/color]" % cmd, "system")


func _on_faction_action_executed(act: String, _payload: Dictionary) -> void:
	match act:
		"enlist":
			if swg_audio: swg_audio.play_mission_complete()
			_show_notification("🎖 Engagement Militaire Actif ! Vous servez désormais votre faction.", Color(0.2, 1.0, 0.5))
		"declare_sf":
			if swg_audio: swg_audio.play_tusken_roar()
		"go_leave":
			if swg_audio: swg_audio.play_droid()
		"resign":
			_show_notification("🕊 Démobilisation effectuée : Vous êtes redevenu un simple citoyen civil.", Color(0.8, 0.9, 1.0))
		"buy_supplies":
			if swg_inventory_panel and swg_inventory_panel.has_method("add_item"):
				swg_inventory_panel.add_item({
					"id": "military_stimpack",
					"name": "Stimpack Militaire Factionnel",
					"icon": "💉",
					"slot": "usable",
					"qty": 3,
					"desc": "Injecteur d'urgence de combat de haute technologie (+400 HAM)."
				})
			if swg_audio: swg_audio.play_harvest()
			_show_notification("📦 Ravitaillement Militaire distribué dans votre Sac à Dos [I] !", Color(0.2, 1.0, 0.6))


func _on_species_selected(sp: Dictionary) -> void:
	if player and player.has_method("apply_species"):
		player.call("apply_species", sp)

	var s_name: String = str(sp.get("name", "Espèce"))
	var ham: Dictionary = sp.get("ham_bonus", {})
	var bonus_hp: int = int(ham.get("health", 0))

	if swg_ham_hud and swg_ham_hud.has_method("damage_pool"):
		swg_ham_hud.damage_pool("health", -bonus_hp)

	if swg_audio: swg_audio.play_mission_complete()
	_show_notification("🧬 IMAGE DESIGNER : Morphologie adaptée en [%s] !" % s_name, Color(0.2, 1.0, 0.6))
	if swg_chat_box:
		swg_chat_box.add_log("[color=#33ffaa]🧬 [Image Designer] Votre espèce a été modifiée : %s (%s).[/color]" % [s_name, str(sp.get("title"))], "system")


func _start_watching_entertainer(artist_name: String) -> void:
	_is_watching_entertainer = true
	_watch_target_name = artist_name if not artist_name.is_empty() else "Lia"
	_show_notification("👁 Vous commencez à observer attentivement le spectacle de %s..." % _watch_target_name, Color(0.95, 0.6, 0.95))
	if swg_chat_box:
		swg_chat_box.add_log("[color=#ff77ee]👁 Vous observez %s. Jauge d'inspiration en progression...[/color]" % _watch_target_name, "spatial")


func _start_listening_music(artist_name: String) -> void:
	_is_watching_entertainer = true
	_watch_target_name = artist_name if not artist_name.is_empty() else "L'Orchestre de la Cantina"
	if swg_audio: swg_audio.play_droid()
	_show_notification("🎷 Vous écoutez le concert de %s : Sérénité et calme mental..." % _watch_target_name, Color(0.3, 0.9, 1.0))
	if swg_chat_box:
		swg_chat_box.add_log("[color=#44ddee]🎷 Vous écoutez %s. Vos blessures de l'esprit se referment.[/color]" % _watch_target_name, "spatial")


func _execute_entertainer_flourish(num: int) -> void:
	var clamped_num := clampi(num, 1, 8)
	if swg_audio: swg_audio.play_mission_complete()

	var spark := OmniLight3D.new()
	var col_table := [
		Color(1.0, 0.2, 0.5), Color(0.2, 0.9, 1.0), Color(1.0, 0.85, 0.2), Color(0.4, 1.0, 0.4),
		Color(0.8, 0.3, 1.0), Color(1.0, 0.5, 0.1), Color(0.2, 0.6, 1.0), Color(1.0, 1.0, 1.0)
	]
	var col: Color = col_table[(clamped_num - 1) % col_table.size()]
	spark.light_color = col
	spark.light_energy = 4.0
	spark.omni_range = 8.0
	var p_pos := (player.global_position if (player and player.is_inside_tree()) else (player.position if player else Vector3.ZERO))
	spark.position = p_pos + Vector3(0, 2.2, 0)
	if is_inside_tree():
		add_child(spark)
		var tween := create_tween()
		tween.tween_property(spark, "light_energy", 0.0, 1.2)
		tween.tween_callback(spark.queue_free)
	else:
		spark.free()

	_show_notification("✨ FLOURISH %d RÉUSSI : Mouvement d'artiste spectaculaire sous les spots !" % clamped_num, col)
	if swg_chat_box:
		swg_chat_box.add_log("[color=#ffcc33]✨ [Flourish %d] L'artiste enchaîne une figure magistrale ! +35 XP Entertainer.[/color]" % clamped_num, "spatial")

	_inspiration_meter = minf(100.0, _inspiration_meter + 35.0)
	if _inspiration_meter >= 100.0:
		_inspiration_meter = 0.0
		_grant_cantina_inspiration_buff()


func _grant_cantina_inspiration_buff() -> void:
	if swg_audio: swg_audio.play_mission_complete()
	if swg_ham_hud and swg_ham_hud.has_method("damage_pool"):
		swg_ham_hud.damage_pool("mind", -250)
	_show_notification("🌟 INSPIRATION DE CANTINA COMPLÈTE : +250 Mental & Sérénité retrouvée !", Color(1.0, 0.9, 0.2))
	if swg_chat_box:
		swg_chat_box.add_log("[color=#ffff44]🌟 Le spectacle vous a galvanisé ! Vous bénéficiez d'une clarté mentale absolue.[/color]", "system")


func _on_datapad_pet_action(act: String, pcd_id: String) -> void:
	print("[SWG 3D] Action Datapad PCD : %s sur %s" % [act, pcd_id])

	match act:
		"call":
			if "speeder" in pcd_id or "swoop" in pcd_id:
				if swg_audio: swg_audio.play_shuttle_land()
				if not _is_riding_speeder:
					_toggle_landspeeder_pilot()
				_show_notification("🚀 PCD VÉHICULE : Engin à répulseurs matérialisé ! Commandes actives.", Color(0.2, 0.9, 1.0))
				if swg_chat_box:
					swg_chat_box.add_log("[color=#33ccff]🚀 [PCD] Votre véhicule à sustentation magnétique a été invoqué.[/color]", "spatial")
			elif "dewback" in pcd_id:
				if swg_audio: swg_audio.play_tusken_roar()
				if not _is_riding_dewback:
					_toggle_dewback_mount()
				_show_notification("🦎 PCD MONTURE : Dewback dressé matérialisé ! Vous êtes en selle.", Color(0.3, 1.0, 0.5))
				if swg_chat_box:
					swg_chat_box.add_log("[color=#55ff77]🦎 [PCD] Votre Dewback sellé a répondu à votre appel.[/color]", "spatial")
			elif "chacal" in pcd_id:
				if swg_audio: swg_audio.play_droid()
				_show_notification("🐾 PCD FAMILIER : Chiot des Sables invoqué à vos côtés !", Color(0.95, 0.7, 0.2))
				if swg_chat_box:
					swg_chat_box.add_log("[color=#ffaa33]🐾 [PCD] Votre compagnon animal est à vos côtés et monte la garde.[/color]", "spatial")
		"store":
			if _is_riding_speeder:
				_toggle_landspeeder_pilot()
			if _is_riding_dewback:
				_toggle_dewback_mount()
			if swg_audio: swg_audio.play_droid()
			_show_notification("📦 PCD DATAPAD : Engin / Monture rangé avec succès dans le Datapad [P].", Color(0.8, 0.9, 1.0))
			if swg_chat_box:
				swg_chat_box.add_log("[color=#88ccff]📦 [PCD] Dispositif de contrôle rangé dans votre banque de données.[/color]", "system")
		"follow":
			_show_notification("🐾 Familier en mode SUIVRE : Votre compagnon marche sur vos talons.", Color(0.3, 1.0, 0.6))
		"stay":
			_show_notification("🛑 Familier en mode HALTE : Votre compagnon garde la position.", Color(1.0, 0.8, 0.2))
		"feed":
			if swg_audio: swg_audio.play_drink()
			_show_notification("🍖 Vous nourrissez votre compagnon avec des rations : Loyauté maximale !", Color(0.2, 1.0, 0.4))
		"trick1":
			if swg_audio: swg_audio.play_droid()
			_show_notification("🎪 Votre compagnon exécute une pirouette joyeuse dans le sable !", Color(0.9, 0.6, 1.0))


func _place_player_house_at_current_pos() -> void:
	if player == null:
		return
	var forward: Vector3 = -player.global_transform.basis.z.normalized()
	var spawn_pos: Vector3 = player.global_position + forward * 8.0
	spawn_pos.y = 0.0
	var new_house: Node3D = _SwgAssetPipelineScript.build_swg_enterable_player_house(spawn_pos, player.rotation_degrees.y, "Maison de %s" % player.name)
	add_child(new_house)
	if swg_audio: swg_audio.play_mission_complete()
	_show_notification("🏗 ACTE DE PROPRIÉTÉ VALIDÉ : Maison posée à (%dm, %dm) !" % [int(spawn_pos.x), int(spawn_pos.z)], Color(0.2, 1.0, 0.5))
	if swg_chat_box:
		swg_chat_box.add_log("[color=#44ff88]🏗 BÂTIMENT DE JOUEUR ÉRIGÉ : Entrée franchissable, salon meublé et coffre actif.[/color]", "system")


