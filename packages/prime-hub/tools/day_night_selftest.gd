extends SceneTree
## day_night_selftest.gd — Validation headless du cycle jour/nuit circadien et des lanternes (Ticket 2.1 O2 Phase 3).
##
## Usage:
##   packages/prime-hub/tools/Godot_v4.6.3-stable_linux.x86_64 --headless \
##     --path packages/prime-hub -s res://tools/day_night_selftest.gd

const HubWorldClockScript := preload("res://scripts/hub_world_clock.gd")
const HubSimScript := preload("res://scripts/hub_sim.gd")
const HubSimDefsScript := preload("res://scripts/hub_sim_defs.gd")
const HubCollisionScript := preload("res://scripts/hub_collision.gd")
const HubNavScript := preload("res://scripts/hub_nav.gd")
const HubSimViewsScript := preload("res://scripts/hub_sim_views.gd")


func _init() -> void:
	print("[*] Lancement du test Cycle Jour/Nuit Circadien & Lanternes (Ticket 2.1 O2)...")

	# Test 1 : Initialisation de HubWorldClock et état par défaut
	var clock = HubWorldClockScript.new()
	clock.setup(10.0, 60.0)

	var s0: Dictionary = clock.get_time_state()
	print("  - Heure initiale: %s (phase=%s, lanternes=%s, mult_bêtes=%.2f)" % [
		s0.get("time_string"), s0.get("day_phase"), s0.get("night_lanterns_active"), float(s0.get("beast_aggro_mult"))
	])
	assert(clock.get_time_string() == "10:00", "L'heure initiale doit être 10:00")
	assert(s0.get("day_phase") == "day", "La phase par défaut doit être day")
	assert(not clock.is_night_time(), "10:00 n'est pas la nuit")
	assert(not clock.are_lanterns_active(), "Les lanternes doivent être éteintes en plein jour")
	assert(is_equal_approx(clock.get_beast_aggro_mult(), 1.0), "Le multiplicateur d'agressivité de jour doit être 1.0")
	assert(is_equal_approx(clock.get_light_ambient(), 1.0), "La lumière ambiante de plein jour doit être 1.0")
	print("[+] PASS: État initial de plein jour (10:00) validé")

	# Test 2 : Transition vers le crépuscule et allumage précoce des lanternes (19:00)
	clock.set_time(19.0)
	var s_dusk: Dictionary = clock.get_time_state()
	print("  - Crépuscule (19:00): phase=%s, lanternes=%s, aggro=%.2f" % [
		s_dusk.get("day_phase"), s_dusk.get("night_lanterns_active"), float(s_dusk.get("beast_aggro_mult"))
	])
	assert(s_dusk.get("day_phase") == "dusk", "19:00 doit être la phase dusk")
	assert(clock.are_lanterns_active(), "Les lanternes doivent être allumées au crépuscule dès 18h30")
	assert(clock.get_beast_aggro_mult() > 1.0, "L'agressivité des bêtes doit augmenter au crépuscule")
	print("[+] PASS: Phase crépuscule (dusk) et activation des lanternes validées")

	# Test 3 : Nuit profonde (23:00) avec agressivité bêtes accrue et faible luminosité
	clock.set_time(23.0)
	var s_night: Dictionary = clock.get_time_state()
	print("  - Nuit profonde (23:00): phase=%s, is_night=%s, aggro=%.2f, lum=%.2f" % [
		s_night.get("day_phase"), s_night.get("is_night"), float(s_night.get("beast_aggro_mult")), float(s_night.get("light_ambient"))
	])
	assert(s_night.get("day_phase") == "night", "23:00 doit être la phase night")
	assert(clock.is_night_time(), "is_night doit être vrai à 23:00")
	assert(clock.are_lanterns_active(), "Les lanternes doivent rester allumées la nuit")
	assert(is_equal_approx(clock.get_beast_aggro_mult(), 1.60), "L'agressivité des bêtes doit être maximale (1.60)")
	assert(clock.get_light_ambient() <= 0.30, "La lumière ambiante nocturne doit être tamisée (<=0.30)")
	print("[+] PASS: Phase nuit profonde (night) et modificateurs de danger validés")

	# Test 4 : Transition vers l'aube (05:30 puis 07:00)
	clock.set_time(5.5)
	assert(clock.get_day_phase() == "dawn", "05:30 doit être l'aube")
	assert(clock.are_lanterns_active(), "Les lanternes restent allumées au début de l'aube (avant 06h30)")
	clock.set_time(7.0)
	assert(clock.get_day_phase() == "dawn", "07:00 doit toujours être l'aube")
	assert(not clock.are_lanterns_active(), "Les lanternes doivent s'éteindre après 06h30")
	print("[+] PASS: Phase aube (dawn) et extinction matinale des lanternes validées")

	# Test 5 : Écoulement continu du temps via tick()
	clock.set_time(10.0) # 10:00:00
	# Dilation = 60.0 -> 60s réelles = 3600s en jeu = 1h
	clock.tick(60.0)
	assert(is_equal_approx(clock.get_game_hour(), 11.0), "Après 60s réelles à dilation 60x, il doit être 11:00")
	assert(clock.get_time_string() == "11:00", "L'affichage doit être 11:00")
	print("[+] PASS: Écoulement dynamique et dilution du temps validés (60x)")

	# Test 6 : Intégration dans la simulation HubSim et diffusion réseau zone_state
	var collision = HubCollisionScript.new()
	collision.reload()
	var nav = HubNavScript.new()
	nav.build(collision)

	var sim = HubSimScript.new()
	sim.collision = collision
	sim.nav = nav
	sim.reset()

	assert(sim.world_clock != null, "HubSim doit instancier world_clock")
	assert(sim.world_clock.get_game_hour() >= 0.0, "world_clock doit être initialisé dans sim")

	var payload: Dictionary = HubSimViewsScript.zone_state_payload(sim, 900001)
	assert(payload.has("world_clock"), "zone_state_payload doit contenir le bloc world_clock")
	var wc_payload: Dictionary = payload["world_clock"]
	assert(wc_payload.has("day_phase"), "world_clock doit exposer day_phase")
	assert(wc_payload.has("night_lanterns_active"), "world_clock doit exposer night_lanterns_active")
	assert(wc_payload.has("beast_aggro_mult"), "world_clock doit exposer beast_aggro_mult")
	print("[+] PASS: Intégration HubSim et diffusion payload zone_state validées")

	# Test 7 : Impact du cycle nuit sur l'agressivité bêtes de HubCombat
	sim.world_clock.set_time(23.0) # Nuit
	var test_beast: Dictionary = {
		"eid": "beast:test_hyena",
		"name": "Hyène de Scrapaltai",
		"kind": "beast",
		"active": true,
		"pos": Vector3(5000.0, 0.15, -700.0),
		"home_x": 5000.0,
		"home_z": -700.0,
		"speed": 6.0,
		"aggro_r": 20.0,
		"leash_r": 50.0,
		"goal": "wander",
	}
	# En pleine nuit, aggro_r effectif = 20.0 * 1.6 = 32.0m
	var mult: float = sim.world_clock.get_beast_aggro_mult()
	assert(is_equal_approx(mult, 1.60), "Le multiplicateur nocturne doit être 1.60")
	print("  - Rayon aggro hyène de nuit: %.1fm (base=%.1fm, mult=%.2f)" % [test_beast["aggro_r"] * mult, test_beast["aggro_r"], mult])
	print("[+] PASS: Amplification de l'agressivité des prédateurs nocturnes validée")

	# Nettoyage propre
	if sim.player_store != null:
		sim.player_store.shutdown()

	print("[+] Cycle Jour/Nuit Circadien & Lanternes (Ticket 2.1) : Tous les tests passent avec succès !")
	quit(0)
