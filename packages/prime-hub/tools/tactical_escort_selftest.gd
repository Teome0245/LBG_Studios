extends SceneTree
## tactical_escort_selftest.gd — Validation headless de l'escorte tactique et coordination en binôme (Ticket 3.1 O3 Phase 3).
##
## Usage:
##   packages/prime-hub/tools/Godot_v4.6.3-stable_linux.x86_64 --headless \
##     --path packages/prime-hub -s res://tools/tactical_escort_selftest.gd

const AgentEnvironmentAdapterScript := preload("res://scripts/adapters/agent_environment_adapter.gd")
const GodotHubAdapterScript := preload("res://scripts/adapters/godot_hub_adapter.gd")
const HubSimScript := preload("res://scripts/hub_sim.gd")
const HubCollisionScript := preload("res://scripts/hub_collision.gd")
const HubNavScript := preload("res://scripts/hub_nav.gd")


func _init() -> void:
	print("[*] Lancement du test Coordination Tactique & Escorte en Binôme (Ticket 3.1 O3)...")

	# Test 1 : Validation des nouveaux types d'actions dans le contrat universel
	var act_follow := AgentEnvironmentAdapterScript.make_action(
		AgentEnvironmentAdapterScript.ACTION_TYPE_FORMATION_FOLLOW,
		{"target_partner_id": "Lia", "formation_offset": Vector3(-3.0, 0.0, -3.0)}
	)
	assert(act_follow["type"] == AgentEnvironmentAdapterScript.ACTION_TYPE_FORMATION_FOLLOW)
	assert(act_follow["target_partner_id"] == "Lia")

	var act_cover := AgentEnvironmentAdapterScript.make_action(
		AgentEnvironmentAdapterScript.ACTION_TYPE_COVER_TARGET,
		{"threat_eid": "beast:test_stalker", "target_partner_id": "Lia"}
	)
	assert(act_cover["type"] == AgentEnvironmentAdapterScript.ACTION_TYPE_COVER_TARGET)

	var act_retreat := AgentEnvironmentAdapterScript.make_action(
		AgentEnvironmentAdapterScript.ACTION_TYPE_TACTICAL_RETREAT,
		{"shelter_poi": "cantina"}
	)
	assert(act_retreat["type"] == AgentEnvironmentAdapterScript.ACTION_TYPE_TACTICAL_RETREAT)
	print("[+] PASS: Contrat universel d'actions tactiques validé (FORMATION, COVER, RETREAT)")

	# Test 2 : Initialisation de l'environnement de simulation et du GodotHubAdapter
	var collision = HubCollisionScript.new()
	collision.reload()
	var nav = HubNavScript.new()
	nav.build(collision)

	var sim = HubSimScript.new()
	sim.collision = collision
	sim.nav = nav
	sim.reset()

	var adapter = GodotHubAdapterScript.new()
	adapter.setup(sim, null, sim.POIS)
	adapter.register_partner_pair("Nix", "Lia")

	# Positionnement du binôme Nix (Leader) et Lia (Suiveuse / Ailier)
	var nix_pos := Vector3(4800.0, 0.15, -700.0)
	var lia_pos := Vector3(4795.0, 0.15, -705.0)

	sim.entities["player:Nix"]["pos"] = nix_pos
	sim.entities["player:Lia"]["pos"] = lia_pos

	# Test 3 : Exécution de l'action de formation (FORMATION_FOLLOW)
	var follow_res: Dictionary = adapter.perform_action("Lia", {
		"type": AgentEnvironmentAdapterScript.ACTION_TYPE_FORMATION_FOLLOW,
		"target_partner_id": "Nix",
		"formation_offset": Vector3(-4.0, 0.0, -3.0)
	})
	assert(follow_res.get("ok") == true, "L'action de formation doit réussir")
	var target_arr: Array = follow_res.get("formation_target", [])
	assert(target_arr.size() == 3, "La cible de formation doit être un triplet x,y,z")
	var computed_target := Vector3(target_arr[0], target_arr[1], target_arr[2])
	var dist_to_expected := computed_target.distance_to(nix_pos + Vector3(-4.0, 0.0, -3.0))
	assert(dist_to_expected < 2.0, "La position de formation doit correspondre à l'offset derrière le leader")
	assert(str(sim.entities["player:Lia"].get("goal", "")) == "formation_escort", "Le goal de Lia doit être formation_escort")
	print("  - Cible de formation Lia calculée: %s (distance au leader Nix: %.1fm)" % [
		computed_target, computed_target.distance_to(nix_pos)
	])
	print("[+] PASS: Formation dynamique en binôme et calcul spatial d'escorte validés")

	# Test 4 : Conscience tactique d'équipe et perception de la menace
	var obs_lia_calm: Dictionary = adapter.get_observation("Lia")
	var team_ctx_calm: Dictionary = obs_lia_calm.get("team_context", {})
	assert(team_ctx_calm.get("has_partner") == true, "Lia doit avoir un partenaire enregistré")
	assert(team_ctx_calm.get("partner_id") == "nix", "Le partenaire doit être Nix")
	assert(team_ctx_calm.get("partner_under_threat") == false, "Nix ne doit pas être menacé initialement")

	# Simulation de l'apparition d'un prédateur hostile ciblant le leader Nix
	var beast_eid := "beast:stalker_99"
	sim.entities[beast_eid] = {
		"eid": beast_eid,
		"name": "Rôdeur des Dunes",
		"kind": "beast",
		"active": true,
		"pos": Vector3(4815.0, 0.15, -690.0),
		"aggro_eid": "player:Nix", # Le rôdeur cible directement Nix
		"goal": "aggro",
	}

	var obs_lia_alert: Dictionary = adapter.get_observation("Lia")
	var team_ctx_alert: Dictionary = obs_lia_alert.get("team_context", {})
	assert(team_ctx_alert.get("partner_under_threat") == true, "Lia doit détecter que Nix est sous menace")
	assert(team_ctx_alert.get("threat_eid") == beast_eid, "L'identifiant de la menace doit être détecté")
	print("  - Menace détectée par Lia : %s ciblant son binôme Nix" % beast_eid)
	print("[+] PASS: Télémétrie d'équipe et détection de menace partagée validées")

	# Test 5 : Réaction de couverture tactique (COVER_TARGET)
	var cover_res: Dictionary = adapter.perform_action("Lia", {
		"type": AgentEnvironmentAdapterScript.ACTION_TYPE_COVER_TARGET,
		"target_partner_id": "Nix",
		"threat_eid": beast_eid
	})
	assert(cover_res.get("ok") == true, "L'action de couverture doit réussir")
	var cover_target: Array = cover_res.get("cover_pos", [])
	assert(cover_target.size() == 3, "La position de couverture doit être un vecteur 3D")
	var cover_v3 := Vector3(cover_target[0], cover_target[1], cover_target[2])
	# Vérifie que la position d'interposition se situe entre Nix et le rôdeur
	var d_nix := cover_v3.distance_to(nix_pos)
	var d_beast := cover_v3.distance_to(sim.entities[beast_eid]["pos"])
	assert(d_nix < nix_pos.distance_to(sim.entities[beast_eid]["pos"]), "La couverture doit s'interposer devant Nix")
	assert(str(sim.entities["player:Lia"].get("goal", "")) == "cover_partner", "Le goal de Lia doit basculer en cover_partner")
	assert(str(sim.entities["player:Lia"].get("play_mode", "")) == "defense", "Le play_mode de Lia doit basculer en defense")
	print("  - Interposition tactique de Lia à (%.1f, %.1f) entre Nix et la bête" % [cover_v3.x, cover_v3.z])
	print("[+] PASS: Action d'interposition et couverture tactique (COVER_TARGET) validée")

	# Test 6 : Repli coordonné synchronisé (TACTICAL_RETREAT)
	var retreat_nix: Dictionary = adapter.perform_action("Nix", {
		"type": AgentEnvironmentAdapterScript.ACTION_TYPE_TACTICAL_RETREAT,
		"shelter_poi": "cantina"
	})
	var retreat_lia: Dictionary = adapter.perform_action("Lia", {
		"type": AgentEnvironmentAdapterScript.ACTION_TYPE_TACTICAL_RETREAT,
		"shelter_poi": "cantina"
	})
	assert(retreat_nix.get("ok") == true and retreat_lia.get("ok") == true, "Les actions de repli doivent réussir")
	var cantina_pos: Vector3 = sim.POIS["cantina"]
	assert(sim.entities["player:Nix"]["target"].distance_to(cantina_pos) < 2.0, "Nix doit se replier vers le Cantina")
	assert(sim.entities["player:Lia"]["target"].distance_to(cantina_pos) < 2.0, "Lia doit se replier vers le même Cantina")
	print("[+] PASS: Repli tactique synchronisé sous abri (TACTICAL_RETREAT) validé")

	# Nettoyage propre
	if sim.player_store != null:
		sim.player_store.shutdown()

	print("[+] Coordination Tactique & Escorte en Binôme (Ticket 3.1 O3) : Tous les tests passent avec succès !")
	quit(0)
