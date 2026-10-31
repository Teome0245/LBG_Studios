extends SceneTree
## Ticket 2.1 — Self-test headless du contrat d'environnement universel (O3 Joueurs IA).
##
## Valide le découplage strict entre l'agent et la simulation :
##   1. Contrat abstrait de base (AgentEnvironmentAdapter)
##   2. Adaptateur mock découplé (portabilité hors Godot)
##   3. Adaptateur d'intégration GodotHubAdapter (Lost Heaven)
##
## Usage:
##   packages/prime-hub/tools/Godot_v4.6.3-stable_linux.x86_64 --headless \
##     --path packages/prime-hub -s res://tools/agent_adapter_selftest.gd

const _BaseAdapter = preload("res://scripts/adapters/agent_environment_adapter.gd")
const _GodotHubAdapter = preload("res://scripts/adapters/godot_hub_adapter.gd")
const _HubSim = preload("res://scripts/hub_sim.gd")
const _HubCollision = preload("res://scripts/hub_collision.gd")
const _HubNav = preload("res://scripts/hub_nav.gd")


func _init() -> void:
	print("[*] Lancement du test AgentEnvironmentAdapter (Ticket 2.1 O3)...")

	# --- 1. Test du contrat de base abstrait ---
	var base_adapter = _BaseAdapter.new()
	var base_obs = base_adapter.get_observation("test_agent_01")
	assert(base_obs.has("agent_id") and base_obs["agent_id"] == "test_agent_01", "ID agent manquant dans l'observation")
	assert(base_obs.has("position") and base_obs.has("zone_id"), "Champs spatiaux manquants")
	assert(base_obs.has("nearby_entities") and base_obs.has("nearby_pois"), "Champs perceptuels manquants")
	assert(base_obs.has("timestamp"), "Timestamp manquant")

	var idle_act = _BaseAdapter.make_action(_BaseAdapter.ACTION_TYPE_IDLE)
	var base_res = base_adapter.perform_action("test_agent_01", idle_act)
	assert(not base_res.get("ok", true), "L'adaptateur abstrait ne doit pas exécuter d'action concrète")
	print("[+] PASS: Contrat d'environnement de base validé.")

	# --- 2. Test du découplage via Mock Adapter (portabilité O3) ---
	var mock_state := {
		"pos": Vector3(100.0, 0.0, 200.0),
		"entities": [{"name": "Drone_A", "distance": 12.5}],
		"last_action": ""
	}
	# Création d'un mock autonome
	var mock_adapter = _BaseAdapter.new()
	var custom_obs = _BaseAdapter.make_observation(
		"portable_bot",
		mock_state["pos"],
		"external_simulation",
		95,
		250,
		mock_state["entities"],
		[{"id": "checkpoint_1", "distance": 18.0}],
		["sandstorm_warning"],
		{"warmth": 0.8, "humor": 0.6},
		[{"id": "repair_kit", "qty": 2}]
	)
	assert(custom_obs["agent_id"] == "portable_bot", "ID mock incorrect")
	assert(custom_obs["health"] == 95 and custom_obs["credits"] == 250, "Stats mock incorrectes")
	assert(custom_obs["presence_dials"]["warmth"] == 0.8, "Dials de présence mock non transmises")
	assert(custom_obs["inventory"].size() == 1, "Inventaire mock incomplet")
	print("[+] PASS: Adaptateur mock découplé (Portabilité O3) validé.")

	# --- 3. Test de l'adaptateur concret GodotHubAdapter ---
	var collision = _HubCollision.new()
	collision.reload()
	var nav = _HubNav.new()
	nav.build(collision)

	var sim = _HubSim.new()
	sim.nav = nav
	sim.reset()

	var test_pois: Dictionary = {
		"plaza": Vector3(4749.0, 0.15, -737.0),
		"cantina": Vector3(4939.0, 0.15, -802.0),
		"market": Vector3(4809.0, 0.15, -932.0),
	}
	var test_dials: Dictionary = {
		"Nix": {"warmth": 0.85, "initiative": 0.70},
		"Lia": {"warmth": 0.40, "initiative": 0.30},
	}

	var hub_adapter = _GodotHubAdapter.new()
	hub_adapter.setup(sim, null, test_pois, test_dials)

	# Observation de l'agent Nix
	var nix_obs = hub_adapter.get_observation("Nix")
	assert(nix_obs.get("agent_id") == "Nix", "Observation Nix incorrecte")
	assert(nix_obs["presence_dials"].get("warmth") == 0.85, "Dials de Nix non résolues")
	assert(nix_obs["nearby_entities"].size() > 0, "Aucune entité perçue par Nix")
	assert(nix_obs["nearby_pois"].size() > 0, "Aucun POI perçu par Nix")

	# Action MOVE vers un POI (cantina)
	var move_act = _BaseAdapter.make_action(_BaseAdapter.ACTION_TYPE_MOVE, {
		"poi_id": "cantina",
		"goal": "boire un verre à La Perle",
		"play_mode": "hub"
	})
	var move_res = hub_adapter.perform_action("Nix", move_act)
	assert(move_res.get("ok", false), "Échec de l'action MOVE")
	var nix_ent = hub_adapter._resolve_entity("Nix")
	assert(nix_ent.get("moving") == true, "Nix n'a pas été marqué moving")
	assert(nix_ent.get("goal") == "boire un verre à La Perle", "Objectif de Nix non mis à jour")
	assert(nix_ent.get("target") == test_pois["cantina"], "Cible de déplacement de Nix incorrecte")

	# Action SAY
	var say_act = _BaseAdapter.make_action(_BaseAdapter.ACTION_TYPE_SAY, {
		"message": "Salut la cantina, Jax sers-moi la spéciale de Scrapaltai !"
	})
	var say_res = hub_adapter.perform_action("Nix", say_act)
	assert(say_res.get("ok", false), "Échec de l'action SAY")
	assert(nix_ent.get("ambient") == "Salut la cantina, Jax sers-moi la spéciale de Scrapaltai !", "Message ambient non appliqué")

	# Action EMOTE
	var emote_act = _BaseAdapter.make_action(_BaseAdapter.ACTION_TYPE_EMOTE, {
		"emote": "wave"
	})
	var emote_res = hub_adapter.perform_action("Nix", emote_act)
	assert(emote_res.get("ok", false), "Échec de l'action EMOTE")
	assert(nix_ent.get("emote") == "wave", "Emote non appliquée sur l'entité")

	# Action INTERACT_POI
	var interact_act = _BaseAdapter.make_action(_BaseAdapter.ACTION_TYPE_INTERACT, {
		"poi_id": "plaza"
	})
	var interact_res = hub_adapter.perform_action("Nix", interact_act)
	assert(interact_res.get("ok", false), "Échec de l'action INTERACT_POI")

	# Action IDLE
	var idle_res = hub_adapter.perform_action("Nix", {"type": _BaseAdapter.ACTION_TYPE_IDLE})
	assert(idle_res.get("ok", false), "Échec de l'action IDLE")
	assert(nix_ent.get("moving") == false, "Nix devrait être arrêté en IDLE")

	# Action invalide (cible inexistante)
	var bad_move = _BaseAdapter.make_action(_BaseAdapter.ACTION_TYPE_MOVE, {"poi_id": "inexistant_poi"})
	var bad_res = hub_adapter.perform_action("Nix", bad_move)
	assert(not bad_res.get("ok", true), "Une cible invalide ne doit pas être validée")

	if sim.player_store != null:
		sim.player_store.shutdown()

	print("[+] PASS: GodotHubAdapter (Intégration Lost Heaven) validé avec succès.")
	print("[+] AGENT_ADAPTER_SELFTEST_OK: 3/3 suites d'adaptateurs validées.")
	quit(0)
