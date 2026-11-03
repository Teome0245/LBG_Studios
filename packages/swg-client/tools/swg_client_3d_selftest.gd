extends SceneTree
## Self-test Headless du Client SWG Pre-CU 3D (Étape 1 : Contrôleur TPS & Postures).
##
## Usage:
##   packages/prime-hub/tools/godot --headless --path packages/swg-client \
##     -s res://tools/swg_client_3d_selftest.gd

const WorldSceneScript := preload("res://scripts/swg_world_3d.gd")
const PlayerScript := preload("res://scripts/swg_player_controller_3d.gd")

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
	var SwgAssetPipelineScript := preload("res://scripts/swg_asset_pipeline.gd")
	var test_cantina: Node3D = SwgAssetPipelineScript.build_swg_cantina_pob(Vector3(100, 0, 100))
	assert(test_cantina != null, "La Cantina POB doit être générée")
	assert(test_cantina.has_node("Cell_MainBar"), "La cellule Bar de la Cantina doit exister")
	assert(test_cantina.has_node("Cell_Stage"), "La cellule Scène Artistes de la Cantina doit exister")
	test_cantina.free()

	var tinted_mat = SwgAssetPipelineScript.create_tinted_swg_material(Color.WHITE, Color.ORANGE, 0.6, 0.3)
	assert(tinted_mat != null and is_equal_approx(tinted_mat.metallic, 0.6), "Le matériau teinté SWG doit être instancié avec les bons paramètres PBR")

	world.free()

	print("SWG_CLIENT_3D_SELFTEST_OK: Étape 1 (Contrôleur TPS & Postures) + Étape 2 (Terrain 3D 16x16km & Pipeline POB/Assets) 100% validées !")
	quit(0)

