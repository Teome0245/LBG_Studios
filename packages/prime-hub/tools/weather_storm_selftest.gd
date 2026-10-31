extends SceneTree
## weather_storm_selftest.gd — Validation headless de la météo dynamique et du repli des bots (Ticket 3.2).
##
## Usage:
##   packages/prime-hub/tools/Godot_v4.6.3-stable_linux.x86_64 --headless \
##     --path packages/prime-hub -s res://tools/weather_storm_selftest.gd

const HubEventsScript := preload("res://scripts/hub_events.gd")
const HubBotAutonomyScript := preload("res://scripts/hub_bot_autonomy.gd")
const HubSimScript := preload("res://scripts/hub_sim.gd")
const HubSimDefsScript := preload("res://scripts/hub_sim_defs.gd")
const HubCollisionScript := preload("res://scripts/hub_collision.gd")
const HubNavScript := preload("res://scripts/hub_nav.gd")


func _init() -> void:
	print("[*] Lancement du test Météo Dynamique & Repli (Ticket 3.2)...")

	# Test 1 : Initialisation des événements et état météo par défaut
	var events = HubEventsScript.new()
	events.setup()

	var w0: Dictionary = events.get_weather_state()
	print("  - État météo initial: %s (intensité=%.1f)" % [w0.get("phase"), float(w0.get("intensity"))])
	assert(w0.get("phase") == "calm", "La météo initiale doit être calm")
	assert(not events.is_weather_shelter_active(), "Aucun abri ne doit être requis en temps calme")
	print("[+] PASS: État météo initial au calme validé")

	# Test 2 : Déclenchement de la tempête de sable et cycle complet des phases
	var now := Time.get_unix_time_from_system()
	events.trigger_sandstorm(10.0, 30.0, 10.0, now)

	var w_warn: Dictionary = events.get_weather_state()
	assert(w_warn.get("phase") == "warning", "La phase doit être warning après déclenchement")
	assert(events.is_weather_shelter_active(), "L'alerte météo doit exiger un abri")
	print("[+] PASS: Phase warning (avis de tempête) validée")

	# Avance vers la phase de tempête active (warning expiré après 10s)
	events.tick(now + 11.0)
	var w_storm: Dictionary = events.get_weather_state()
	assert(w_storm.get("phase") == "storm", "La phase doit être storm")
	assert(is_equal_approx(float(w_storm.get("intensity")), 1.0), "L'intensité de tempête doit être maximale (1.0)")
	assert(events.is_weather_shelter_active(), "L'abri doit rester obligatoire pendant la tempête")
	print("[+] PASS: Phase storm (tempête maximale) validée")

	# Avance vers l'accalmie (tempête expirée après 30s supplémentaires)
	events.tick(now + 42.0)
	var w_clear: Dictionary = events.get_weather_state()
	assert(w_clear.get("phase") == "clearing", "La phase doit être clearing")
	assert(not events.is_weather_shelter_active(), "L'accalmie lève l'obligation d'abri")
	print("[+] PASS: Phase clearing (accalmie) validée")

	# Fin de l'événement et retour au calme
	events.tick(now + 55.0)
	var w_end: Dictionary = events.get_weather_state()
	assert(w_end.get("phase") == "calm", "La phase doit être revenue à calm")
	assert(is_equal_approx(float(w_end.get("intensity")), 0.0), "L'intensité doit être revenue à 0")
	print("[+] PASS: Retour complet au calme validé")

	# Test 3 : Réaction autonome d'urgence des Joueurs IA
	var autonomy = HubBotAutonomyScript.new()
	var test_pois := HubSimDefsScript.POIS
	autonomy.setup(null, null, test_pois, events)

	var test_bot := {
		"name": "Nix",
		"pos": Vector3(5800.0, 0.15, -1100.0), # Dehors dans les dunes à l'est
		"goal": "hunt",
		"play_mode": "explore",
	}

	# Par temps calme : explore normal
	var g_calm: Dictionary = autonomy.assign_goal(test_bot)
	assert(g_calm.get("play_mode") != "shelter", "Le bot ne doit pas chercher d'abri par temps calme")
	print("[+] PASS: Comportement exploratoire normal par temps calme validé")

	# Déclenchement d'une alerte tempête : le bot doit obligatoirement chercher un abri
	events.trigger_sandstorm(15.0, 60.0, 15.0)
	assert(events.is_weather_shelter_active(), "Abri requis suite à l'alerte")

	var g_storm: Dictionary = autonomy.assign_goal(test_bot)
	print("  - Objectif assigné sous tempête: %s (%s) vers cible %s" % [
		g_storm.get("goal_label"),
		g_storm.get("play_mode"),
		g_storm.get("target")
	])
	assert(g_storm.get("play_mode") == "shelter", "Le bot DOIT passer en play_mode shelter")
	assert(g_storm.get("goal_id") == "shelter_storm", "L'identifiant d'objectif doit être shelter_storm")

	var shelter_pos: Vector3 = g_storm.get("target")
	var cantina_pos: Vector3 = test_pois["cantina"]
	# La cantina ou le hall est l'abri le plus proche
	assert(shelter_pos.distance_to(test_bot["pos"]) < 1500.0, "L'abri doit être un bâtiment du plateau")
	print("[+] PASS: Réflexe d'urgence des Joueurs IA validé (repli sous bâtiment abrité)")

	# Test 4 : Intégration HubSim
	var collision = HubCollisionScript.new()
	collision.reload()
	var nav = HubNavScript.new()
	nav.build(collision)

	var sim = HubSimScript.new()
	sim.nav = nav
	sim.reset()
	sim.attach_events(events)

	# Vérifier que le simulateur transmet les événements à l'autonomie
	assert(sim.autonomy != null and sim.autonomy.events == events, "HubSim doit lier events à l'autonomie")

	# Trouver un bot extérieur
	var bot_eid := ""
	for eid in sim.entities.keys():
		var ent: Dictionary = sim.entities[eid]
		if bool(ent.get("is_bot", false)):
			bot_eid = eid
			break

	assert(not bot_eid.is_empty(), "Au moins un bot doit exister dans HubSim")
	var sim_bot: Dictionary = sim.entities[bot_eid]
	sim_bot["play_mode"] = "explore"
	sim_bot["goal"] = "ring_sample"

	# Simule un pas de simulation sous tempête
	sim._step_bot(sim_bot, 0.1)
	assert(sim_bot.get("play_mode") == "shelter" or sim_bot.get("goal") == "shelter_storm", "HubSim doit router le bot vers un abri sous tempête")

	# Test 5 : Payload zone_state météo unifiée
	var zs := sim.zone_state_payload(100001)
	assert(zs.has("weather"), "Le payload zone_state doit inclure le bloc météo")
	var zsw: Dictionary = zs.get("weather", {})
	assert(bool(zsw.get("shelter_required", false)) == true, "Le repli doit être requis dans zone_state")
	assert(zsw.get("phase") == "warning" or zsw.get("phase") == "storm", "La phase météo doit être warning ou storm")
	print("[+] PASS: Diffusion du bloc météo dans zone_state validée")
	print("[+] PASS: Intégration HubSim et redirection automatique des bots validées")

	print("[+] Météo Dynamique & Repli (Ticket 3.2) : Tous les tests passent avec succès !")
	if sim.player_store != null:
		sim.player_store.shutdown()
	quit(0)
