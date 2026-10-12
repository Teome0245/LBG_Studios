extends SceneTree
## Ticket 2.2 — Self-test headless du simulateur HubSim modulaire.
##
## Usage:
##   packages/prime-hub/tools/godot --headless --path packages/prime-hub \
##     -s res://tools/sim_selftest.gd

const HubSimScript := preload("res://scripts/hub_sim.gd")
const HubCollisionScript := preload("res://scripts/hub_collision.gd")
const HubNavScript := preload("res://scripts/hub_nav.gd")

func _init() -> void:
	var collision = HubCollisionScript.new()
	collision.reload()
	var nav = HubNavScript.new()
	nav.build(collision)

	var sim = HubSimScript.new()
	sim.nav = nav
	sim.reset()

	assert(sim.combat != null, "Module combat manquant")
	assert(sim.presence != null, "Module presence manquant")
	assert(sim.ambient != null, "Module ambient manquant")

	var st = sim.zone_state_payload(100001)
	assert(int(st.get("bot_count", 0)) >= 10, "Moins de 10 bots dans zone_state")
	assert(int(st.get("beast_count", 0)) >= 7, "Moins de 7 bêtes dans zone_state")

	var entities = sim.entity_list(true)
	assert(entities.size() >= 25, "Moins de 25 entités simulées")

	# Simulation de 60 ticks (3 secondes virtuelles à 20Hz via sim.step(0.05))
	for i in range(60):
		sim.step(0.05)

	var bots_p = sim.bots_payload()
	assert(bots_p.size() >= 10, "Payload bots invalide")

	if sim.player_store != null:
		sim.player_store.shutdown()

	print("SIM_SELFTEST_OK: entities=%d bots=%d beasts=%d ticks=%d" % [entities.size(), bots_p.size(), sim.beast_count(), sim.tick])
	quit(0)
