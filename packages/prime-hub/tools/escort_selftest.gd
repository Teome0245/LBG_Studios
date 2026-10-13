extends SceneTree
## Self-test headless — escorte civil `lh_escort_gate_clinic`.
##
## Usage:
##   packages/prime-hub/tools/godot --headless --path packages/prime-hub \
##     -s res://tools/escort_selftest.gd

const HubSimScript := preload("res://scripts/hub_sim.gd")
const HubCollisionScript := preload("res://scripts/hub_collision.gd")
const HubNavScript := preload("res://scripts/hub_nav.gd")
const HubEconomyScript := preload("res://scripts/hub_economy.gd")
const HubEscortScript := preload("res://scripts/hub_escort.gd")

const PLAYER := "EscortTester"
const QUEST := "lh_escort_gate_clinic"
const GATE := Vector3(5813.6, 0.15, -982.5)
const CLINIC := Vector3(4679.0, 0.15, -672.0)


func _init() -> void:
	var collision = HubCollisionScript.new()
	collision.reload()
	var nav = HubNavScript.new()
	nav.build(collision)

	var economy = HubEconomyScript.new()
	economy.setup()
	# État propre pour le joueur de test.
	var pstate: Dictionary = economy._player(PLAYER)
	pstate["active"] = []
	if QUEST in (pstate["completed"] as Array):
		(pstate["completed"] as Array).erase(QUEST)
	economy._save_players()

	var sim = HubSimScript.new()
	sim.nav = nav
	sim.collision = collision
	sim.attach_economy(economy)
	sim.reset()

	assert(sim.escort != null, "Module escort manquant")
	sim.ensure_human(100777, PLAYER)
	# Place le joueur à la porte.
	sim.set_human_pos(100777, GATE.x, GATE.y, GATE.z)

	var acc: Dictionary = economy.accept(PLAYER, QUEST, "npc:core3_daan_oth")
	assert(bool(acc.get("ok")), "accept failed: %s" % acc)
	var spawned: Dictionary = sim.escort.on_accept(sim, PLAYER)
	assert(bool(spawned.get("ok")), "spawn failed: %s" % spawned)
	var sess: Dictionary = sim.escort.session_for(PLAYER)
	assert(str(sess.get("phase", "")) == "waiting_pickup", "phase wait: %s" % sess)
	var eid := str(sess.get("eid", ""))
	assert(sim.entities.has(eid), "civil absent")

	# Dropoff trop tôt → civil pas encore en route / pas à la clinique.
	var early: Dictionary = sim.escort.on_progress(sim, PLAYER, "dropoff")
	assert(not bool(early.get("ok")), "dropoff should fail before escort: %s" % early)

	var pick: Dictionary = economy.progress(PLAYER, QUEST, "pickup")
	assert(bool(pick.get("ok")), "pickup progress: %s" % pick)
	var fol: Dictionary = sim.escort.on_progress(sim, PLAYER, "pickup")
	assert(str(fol.get("phase", "")) == "escorting", "phase escorting: %s" % fol)

	# Suivi court : avancer le joueur de ~25 m depuis la porte, le civil doit rattraper.
	var mid := Vector3(GATE.x - 25.0, GATE.y, GATE.z + 10.0)
	sim.set_human_pos(100777, mid.x, mid.y, mid.z)
	for _i in range(200):
		sim.step(0.05)
	var civil: Dictionary = sim.entities[eid]
	var cp: Vector3 = civil["pos"]
	var pp: Vector3 = sim.entities["player:100777"]["pos"]
	var sep := Vector2(pp.x - cp.x, pp.z - cp.z).length()
	assert(sep <= HubEscortScript.FAIL_RADIUS_M, "civil not following sep=%.1f (player=%s civil=%s)" % [sep, pp, cp])
	# Le civil a bougé depuis le spawn porte.
	var moved := Vector2(cp.x - GATE.x, cp.z - GATE.z).length()
	assert(moved > 5.0, "civil did not move from gate (moved=%.1f)" % moved)

	# Amener civil + joueur à la clinique (téléport test — dropoff serveur).
	sim.set_human_pos(100777, CLINIC.x + 2.0, CLINIC.y, CLINIC.z + 2.0)
	civil["pos"] = Vector3(CLINIC.x + 1.0, CLINIC.y, CLINIC.z + 1.0)
	for _j in range(10):
		sim.step(0.05)

	var drop_gate: Dictionary = sim.escort.on_progress(sim, PLAYER, "dropoff")
	assert(bool(drop_gate.get("ok")), "dropoff gate: %s" % drop_gate)
	var drop: Dictionary = economy.progress(PLAYER, QUEST, "dropoff")
	assert(bool(drop.get("ok")), "dropoff progress: %s" % drop)
	assert(bool(drop.get("ready_to_turn_in", false)) or ("dropoff" in drop.get("steps_done", [])), "ready: %s" % drop)

	var done: Dictionary = economy.complete(PLAYER, QUEST)
	assert(bool(done.get("ok")), "complete: %s" % done)
	sim.escort.on_complete(sim, PLAYER)
	assert(sim.escort.session_for(PLAYER).is_empty(), "session should clear")
	assert(not sim.entities.has(eid), "civil should despawn")

	# --- Fail path : séparation ---
	pstate = economy._player(PLAYER)
	pstate["active"] = []
	if QUEST in (pstate["completed"] as Array):
		(pstate["completed"] as Array).erase(QUEST)
	economy._save_players()
	economy.accept(PLAYER, QUEST, "npc:core3_daan_oth")
	sim.escort.on_accept(sim, PLAYER)
	sim.escort.on_progress(sim, PLAYER, "pickup")
	economy.progress(PLAYER, QUEST, "pickup")
	sim.set_human_pos(100777, CLINIC.x, CLINIC.y, CLINIC.z)
	# Civil reste à la porte → séparation >> 40 m
	var eid2 := str(sim.escort.session_for(PLAYER).get("eid", ""))
	# 8 s de grâce @ 0.05 → 160 ticks + marge
	for _k in range(200):
		sim.step(0.05)
	assert(sim.escort.session_for(PLAYER).is_empty(), "fail should clear session")
	assert(not sim.entities.has(eid2), "civil despawn on fail")
	var st_fail: Dictionary = economy.status(PLAYER)
	var still := false
	for a in st_fail.get("active", []):
		if typeof(a) == TYPE_DICTIONARY and str(a.get("id", "")) == QUEST:
			still = true
	assert(not still, "quest should be abandoned after separation")

	if sim.player_store != null:
		sim.player_store.shutdown()

	print("ESCORT_SELFTEST_OK: follow+dropoff+fail")
	quit(0)
