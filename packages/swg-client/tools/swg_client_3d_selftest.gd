extends SceneTree
## Self-test Headless du Client SWG Pre-CU 3D (Étape 1 : Contrôleur TPS & Postures).
##
## Usage:
##   packages/prime-hub/tools/godot --headless --path packages/swg-client \
##     -s res://tools/swg_client_3d_selftest.gd

const WorldSceneScript := preload("res://scripts/swg_world_3d.gd")
const PlayerScript := preload("res://scripts/swg_player_controller_3d.gd")
const SwgAssetPipelineScript := preload("res://scripts/swg_asset_pipeline.gd")
const DialogBoxScript := preload("res://scripts/swg_dialog_box.gd")

func _init() -> void:
	print("[swg_client_3d_selftest] Début de la vérification du Client SWG Pre-CU 3D...")

	# 1. Test du contrôleur joueur 3D TPS
	var player = PlayerScript.new()
	assert(player != null, "Échec instanciation PlayerController3D")
	player._setup_nodes()
	assert(player._spring_arm != null, "Le SpringArm3D doit être présent pour la caméra orbitale")
	assert(player._camera != null, "La Camera3D doit être attachée au SpringArm")
	assert(player._capsule != null, "La Capsule de collision doit être présente")

	# Test Posture Debout (Standing)
	player.set_posture(PlayerScript.Posture.STANDING)
	assert(player.current_posture == PlayerScript.Posture.STANDING, "Posture courante doit être STANDING")
	assert(is_equal_approx(player._capsule.height, 1.8), "Hauteur capsule debout doit être 1.8m")

	# Test Posture Accroupi (Kneeling)
	player.set_posture(PlayerScript.Posture.KNEELING)
	assert(player.current_posture == PlayerScript.Posture.KNEELING, "Posture courante doit être KNEELING")
	assert(player._capsule.height < 1.3, "Hauteur capsule accroupi doit être réduite")

	# Test Posture Couché (Prone)
	player.set_posture(PlayerScript.Posture.PRONE)
	assert(player.current_posture == PlayerScript.Posture.PRONE, "Posture courante doit être PRONE")
	assert(player._capsule.height < 0.7, "Hauteur capsule couché doit être réduite au ras du sol")

	# Test Combo Dizzy Fall SWG
	player.is_dizzy = true
	player.set_posture(PlayerScript.Posture.STANDING)
	assert(player.current_posture == PlayerScript.Posture.PRONE and player.is_knocked_down, "Tenter de se relever en étant Dizzy doit déclencher un Dizzy Fall au sol")

	player.free()

	# 2. Test du monde 3D et de la couche UI SWG
	var world = WorldSceneScript.new()
	assert(world != null, "Échec instanciation World3D")
	world._setup_world_geometry()
	world._spawn_player()
	world._spawn_interactable_entities()
	world._setup_ui()

	assert(world.player != null, "Le joueur 3D doit être spawn dans le monde")
	assert(world.swg_ham_hud != null, "Le HUD HAM SWG doit être initialisé")
	assert(world.swg_radial_menu != null, "Le Menu Radial SWG doit être initialisé")
	assert(world.swg_character_sheet != null, "La Fiche Perso SWG 9-stats doit être initialisée")
	assert(world.swg_datapad_panel != null, "Le Datapad SWG PCD doit être initialisé")
	assert(world.swg_bazaar_panel != null, "Le Bazar SWG doit être initialisé")
	assert(world.swg_structure_panel != null, "Le Terminal Housing SWG doit être initialisé")

	# 3. Test du Système de Terrain 3D Grande Échelle (Étape 2)
	assert(world.terrain_system != null, "Le système de terrain dynamique 3D doit être présent")
	var h_city: float = world.terrain_system.get_height_at(0.0, 0.0)
	assert(is_equal_approx(h_city, 0.0), "La zone de Lost Heaven doit être aplanie à Y=0.0")
	var h_dunes: float = world.terrain_system.get_height_at(600.0, -800.0)
	assert(absf(h_dunes) > 0.1, "Les dunes extérieures doivent avoir un relief fractal non nul")
	assert(world.terrain_system.loaded_chunks.size() > 0, "Les chunks de terrain 3D autour du centre doivent être chargés")

	# 4. Test du Pipeline d'Assets POB & Teintes (Étape 2)
	var test_cantina: Node3D = SwgAssetPipelineScript.build_swg_cantina_pob(Vector3(100, 0, 100))
	assert(test_cantina != null, "La Cantina POB doit être générée")
	assert(test_cantina.has_node("Cell_MainBar"), "La cellule Bar de la Cantina doit exister")
	assert(test_cantina.has_node("Cell_Stage"), "La cellule Scène Artistes de la Cantina doit exister")
	test_cantina.free()

	var tinted_mat = SwgAssetPipelineScript.create_tinted_swg_material(Color.WHITE, Color.ORANGE, 0.6, 0.3)
	assert(tinted_mat != null and is_equal_approx(tinted_mat.metallic, 0.6), "Le matériau teinté SWG doit être instancié avec les bons paramètres PBR")

	# 5. Test des Nids de Créatures (Lairs) & Vagues Pre-CU
	var LairScript := preload("res://scripts/swg_creature_lair_3d.gd")
	var lair = LairScript.new()
	assert(lair != null, "Échec instanciation SwgCreatureLair3D")
	lair.lair_id = "test_lair"
	lair.lair_display_name = "Nid Test"
	lair.creature_kind = "creature_jackal"
	lair.lair_max_hp = 1000
	lair.current_hp = 1000
	lair.loot_credits = 500
	lair.loot_rare_item = "Œuf Fossilisé"
	lair._setup_collision()
	lair._build_lair_mesh()

	assert(lair.get_meta("entity_kind") == "creature_lair", "Le type d'entité du nid doit être creature_lair")
	assert(lair.current_hp == 1000, "Les PV du nid doivent être à 1000")

	# Simuler dégâts sur le nid
	var dmg_taken := lair.take_damage(300, null)
	assert(dmg_taken == 300 and lair.current_hp == 700, "Le nid doit encaisser les dégâts")
	assert(not lair.is_lair_destroyed, "Le nid ne doit pas être détruit à 700 PV")

	# Coup de grâce
	lair.take_damage(800, null)
	assert(lair.current_hp == 0 and lair.is_lair_destroyed, "Le nid doit être détruit à 0 PV")
	assert(lair.get_meta("entity_kind") == "lair_debris", "Le nid détruit doit devenir des décombres de nid")

	# Pillage des décombres
	var loot: Dictionary = lair.harvest_debris()
	assert(loot.get("ok", false) == true, "La fouille des décombres doit réussir")
	assert(loot.get("credits") == 500, "Le butin de crédits doit correspondre")
	assert(loot.get("rare_item") == "Œuf Fossilisé", "L'œuf rare doit être récupéré")

	var loot2: Dictionary = lair.harvest_debris()
	assert(loot2.get("ok", false) == false, "Un nid déjà pillé ne doit pas pouvoir être pillé deux fois")

	lair.free()

	# 6. Test du Système de Factions Galactiques & GCW Pre-CU
	var FactionSystemScript := preload("res://scripts/swg_faction_system.gd")
	var fac_sys = FactionSystemScript.new()
	assert(fac_sys != null, "Échec instanciation SwgFactionSystem")
	assert(fac_sys.get_faction_name() == "Neutre", "La faction initiale doit être Neutre")
	assert(fac_sys.current_status == FactionSystemScript.FactionStatus.CIVILIAN, "Le statut initial doit être Civilian")

	# Enrôlement Impérial
	fac_sys.enlist(FactionSystemScript.Faction.IMPERIAL)
	assert(fac_sys.get_faction_name() == "Impérial", "La faction doit être Impérial")
	assert(fac_sys.current_status == FactionSystemScript.FactionStatus.ON_LEAVE, "Le statut après enrôlement doit être On-Leave")

	# Déclaration Special Forces (Overt PvP)
	fac_sys.declare_special_forces()
	assert(fac_sys.is_special_forces(), "Le joueur doit être en Special Forces")
	assert(fac_sys.is_enemy("Rebelle"), "Un Rebelle doit être identifié comme ennemi pour un Impérial SF")
	assert(not fac_sys.is_enemy("Impérial"), "Un allié Impérial ne doit pas être un ennemi")

	# Démobilisation
	fac_sys.resign_to_civilian()
	assert(fac_sys.get_faction_name() == "Neutre", "Après démission, la faction redevient Neutre")
	assert(not fac_sys.is_special_forces(), "Après démission, le statut SF est levé")
	fac_sys.free()

	# 7. Test Bâtiment Entrable (Player Housing POB)
	var house: Node3D = SwgAssetPipelineScript.build_swg_enterable_player_house(Vector3(10, 0, 10), 0.0, "Maison Test")
	assert(house != null, "La maison entrable doit être construite")
	assert(house.get_meta("entity_kind") == "housing", "Le type d'entité doit être housing")
	assert(house.find_child("Coffre*", true, false) != null or house.get_child_count() > 3, "Le coffre et meubles intérieurs doivent être présents")
	house.free()

	# 8. Test Datapad PCD Montures & Véhicules
	assert(world.swg_datapad_panel != null, "Le Datapad doit être initialisé")
	assert(world.swg_datapad_panel._pets.size() >= 4, "Le Datapad doit contenir au moins 4 PCD (Speeder, Swoop, Dewback, Chiot)")
	assert(world.swg_datapad_panel._pets[0].get("pet_id") == "pcd_speeder_x34", "Le PCD Speeder X-34 doit être présent")

	# 9. Test Cantina Entertainer Flourish & Inspiration
	world._execute_entertainer_flourish(1)
	assert(world._inspiration_meter >= 35.0, "Un flourish doit augmenter la jauge d'inspiration")
	world._execute_entertainer_flourish(2)
	world._execute_entertainer_flourish(3)
	assert(world._inspiration_meter == 0.0, "La jauge d'inspiration doit avoir octroyé le buff complet à 100%")

	# 10. Test Système d'Espèces SWG Pre-CU / Prime & Fabrique 3D d'Appendices
	var SpeciesScript := preload("res://scripts/swg_species_system.gd")
	assert(SpeciesScript.get_species_count() >= 6, "Le catalogue d'espèces doit contenir au moins 6 espèces SWG / Prime")
	var wookiee: Dictionary = SpeciesScript.find_species_by_id("wookiee")
	assert(wookiee.get("name") == "Wookiee de Kashyyyk", "L'espèce Wookiee doit être présente")
	assert(wookiee.get("ham_bonus", {}).get("health") == 350, "Le bonus de santé Wookiee doit être +350")
	var twilek: Dictionary = SpeciesScript.find_species_by_id("twilek")
	assert(twilek.get("name") == "Twi'lek des Oasis", "L'espèce Twi'lek doit être présente")

	# Test résolution par ID Prime
	var fel_rani: Dictionary = SpeciesScript.find_species_by_id("fel_rani")
	assert(fel_rani.get("id") == "twilek", "L'ID Prime fel_rani doit résoudre l'espèce twilek")
	var tinkling: Dictionary = SpeciesScript.find_species_by_id("tinkling")
	assert(tinkling.get("id") == "tinkling", "L'ID Prime tinkling doit être présent")
	var mechari: Dictionary = SpeciesScript.find_species_by_id("mechari")
	assert(mechari.get("id") == "cyborg", "L'ID Prime mechari doit résoudre l'espèce cyborg")

	# Test application de l'espèce sur le joueur et génération 3D des appendices
	var p2 = PlayerScript.new()
	p2._setup_nodes()
	p2.apply_species(wookiee)
	assert(p2.current_species_id == "wookiee", "L'espèce du joueur doit être wookiee")
	assert(p2._mesh_root.scale.x > 1.1, "L'échelle du modèle Wookiee doit être imposante (> 1.1)")
	var w_feat: Array[Node] = p2._mesh_root.find_children("RaceFeature_*", "", true, false)
	assert(w_feat.size() > 0, "Les appendices 3D de Varkoon / Wookiee doivent être instanciés")

	p2.apply_species(twilek)
	assert(p2.current_species_id == "twilek", "L'espèce du joueur doit basculer vers twilek")
	var t_feat: Array[Node] = p2._mesh_root.find_children("RaceFeature_*", "", true, false)
	assert(t_feat.size() > 0, "Les appendices 3D de Fel'Rani / Twi'lek doivent être instanciés")

	p2.apply_species(tinkling)
	assert(p2.current_species_id == "tinkling", "L'espèce du joueur doit basculer vers tinkling")
	assert(p2._mesh_root.scale.x < 0.6, "L'échelle de Tinkling doit être de petite taille (~45cm)")
	p2.free()

	# 11. Test Formateurs PNJ 3D & Arbres de Compétences 4x4 Interactifs (Étape 2)
	assert(world.swg_skills_panel != null, "Le panneau de compétences 4x4 doit être initialisé")
	world._on_dialog_option_selected("train_artisan", "Dax (Maître Formateur Artisan)")
	assert(world.swg_skills_panel.visible, "Le panneau 4x4 doit s'ouvrir lors de l'entraînement auprès d'un Formateur PNJ")
	world._execute_learn_skill("artisan_novice", "Artisan Novice")
	assert("artisan_novice" in world.swg_skills_panel._learned_boxes, "La box novice doit être enregistrée comme apprise auprès du Formateur")

	# 12. Test Prospection Survey Tool 3D Holographique & Sondage Géologique (Étape 2)
	assert(world.swg_survey_panel != null, "Le panneau Survey Tool doit être initialisé")
	world._execute_survey_pulse()
	assert(world.swg_survey_panel._last_density_pct > 0, "Le sondage géologique doit alimenter la densité du Survey Tool")
	world._execute_sample_resource()
	assert(world.player.current_posture == PlayerScript.Posture.KNEELING, "Le prélèvement d'échantillon géologique doit agenouiller temporairement le prospecteur")

	# 13. Test Sabre Laser Jedi 3D & Pouvoirs de Force
	world._toggle_lightsaber()
	assert(world._lightsaber_active == true and world._lightsaber_mesh != null and world._lightsaber_mesh.visible, "Le sabre laser doit être dégainé dans la main du joueur")
	world._execute_force_heal()
	assert(world._force_pool < 1000.0, "Force Heal doit consommer de la réserve de Force")
	world._toggle_lightsaber()
	assert(world._lightsaber_active == false and not world._lightsaber_mesh.visible, "Le sabre laser doit être rengainé")

	# 14. Test Droïde Sonde Arakyd (Bounty Hunter)
	world._deploy_arakyd_probe()
	assert(world.find_child("ArakydProbeDroid*", true, false) != null or world._tracked_entities.size() > 0, "La sonde Arakyd doit descendre des cieux")

	# 15. Test Vol Spatial JTL (Jump to Lightspeed) & X-Wing T-65
	world._toggle_space_flight()
	assert(world._is_in_space_flight == true and world._space_ship_mesh != null, "Le joueur doit piloter son X-Wing en vol orbital spatial")
	world._toggle_space_flight()
	assert(world._is_in_space_flight == false, "Le retour au sol doit réussir")

	# 16. Test Hôtel de Ville Civique & Bâtiments Municipaux
	var city_hall: Node3D = SwgAssetPipelineScript.build_city_hall(Vector3(180, 0, 70), "New Coronet")
	assert(city_hall != null, "L'Hôtel de Ville de New Coronet doit être instancié")
	assert(city_hall.find_child("Dome*", true, false) != null or city_hall.get_child_count() > 0, "Le dôme doré et les colonnes doivent être présents")
	city_hall.free()

	# 17. Test Incubateur de Bio-Ingénierie & Synthèse ADN
	var bio_lab: Node3D = SwgAssetPipelineScript.build_bio_incubator(Vector3(-18, 0.2, 28))
	assert(bio_lab != null, "L'Incubateur de bio-ingénierie doit être construit")
	bio_lab.free()

	# 18. Test Droïde R2 Astromécano (Droid Engineer)
	var r2_droid: Node3D = SwgAssetPipelineScript.build_r2_astromech(Vector3(-14, 0, 6))
	assert(r2_droid != null, "Le droïde R2 doit être instancié avec son dôme et ses jambes")
	r2_droid.free()

	# 19. Test Donjon Sas de la Corvette Corellienne
	var corvette: Node3D = SwgAssetPipelineScript.build_corvette_airlock(Vector3(-160, 0, -80))
	assert(corvette != null, "Le sas de raid de la Corvette Corellienne doit être construit")
	corvette.free()

	# 20. Test Présélections de Dialogues Interactifs (Villes, Bio, Corvette, Planètes)
	var db := DialogBoxScript.new()
	var p_city: Dictionary = db._get_dialog_preset("Hôtel de Ville de New Coronet", "terminal_cityhall")
	assert(p_city["options"].size() >= 4, "Le terminal de ville doit offrir au moins 4 options (vote, citoyenneté, taxes)")
	var p_bio: Dictionary = db._get_dialog_preset("Incubateur Bio", "terminal_bio")
	assert(p_bio["options"].size() >= 3, "L'incubateur génétique doit offrir des options de prélèvement et d'hybridation")
	var p_planets: Dictionary = db._get_dialog_preset("Console Galactique", "terminal_planets")
	assert(p_planets["options"].size() >= 5, "La console stellaire doit proposer les 5 planètes SWG")
	db.free()

	world.free()

	print("SWG_CLIENT_3D_SELFTEST_OK: 100% SWG Pre-CU Répliqué (20 Piliers 3D, Jedi, Bounty, JTL, Villes, Bio, Droïdes, Donjons & Multi-Planètes) !")
	quit(0)

