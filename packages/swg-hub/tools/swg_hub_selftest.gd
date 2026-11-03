extends SceneTree
## Self-test Headless du Serveur Autoritaire SWG Pre-CU 3D.
##
## Usage:
##   packages/prime-hub/tools/godot --headless --path packages/swg-hub \
##     -s res://tools/swg_hub_selftest.gd

const ServerMainScript := preload("res://scripts/swg_server_main.gd")

func _init() -> void:
	print("[swg_hub_selftest] Début de la vérification du Serveur SWG Pre-CU 3D...")

	var srv = ServerMainScript.new()
	assert(srv != null, "Échec instanciation SwgServerMain")
	srv._init_services()

	assert(srv.combat_service != null, "Le service de combat HAM doit être initialisé")
	assert(srv.creature_service != null, "Le service faune & créatures doit être initialisé")
	assert(srv.housing_service != null, "Le service housing & villes doit être initialisé")
	assert(srv.vendor_service != null, "Le service vendeurs & usines doit être initialisé")

	# Test Enregistrement Joueur 3D
	var p_state := srv.register_player_3d("Pionnier_01", Vector3(12.5, 0.15, -45.0), 1.57)
	assert(srv.active_players.size() == 1, "Un joueur doit être enregistré")
	assert(p_state["posture"] == "standing", "La posture par défaut doit être standing")

	# Test Mise à jour Transform & Posture 3D
	srv.update_player_transform("Pionnier_01", Vector3(14.0, 0.15, -42.0), 2.1, "kneeling")
	var updated: Dictionary = srv.active_players["Pionnier_01"]
	assert(updated["posture"] == "kneeling", "La posture doit être mise à jour à kneeling")
	assert(is_equal_approx(float(updated["pos"][0]), 14.0), "La coordonnée X doit être 14.0")

	# Test Tick Simulation
	srv.simulate_tick()
	assert(srv.tick_count == 1, "Le compteur de ticks doit s'incrémenter")

	# Test Altitudes Terrain Autoritaire (Étape 2)
	var h_city: float = srv.get_terrain_height_at(0.0, 0.0)
	assert(is_equal_approx(h_city, 0.0), "La zone Lost Heaven doit être aplanie à Y=0.0")
	var h_wild: float = srv.get_terrain_height_at(500.0, -700.0)
	assert(absf(h_wild) > 0.1, "Le relief sauvage doit être calculé de façon déterministe")

	srv.free()

	print("SWG_HUB_SELFTEST_OK: Serveur autoritaire SWG Pre-CU 3D, 4 services et suivi des positions 3D validés avec succès !")
	quit(0)

