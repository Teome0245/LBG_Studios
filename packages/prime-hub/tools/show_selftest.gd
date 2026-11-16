extends SceneTree
## Self-test headless — show live La Perle + tip + formation Talen.
##
##   packages/prime-hub/tools/godot --headless --path packages/prime-hub \
##     -s res://tools/show_selftest.gd

const HubSimScript := preload("res://scripts/hub_sim.gd")
const HubCollisionScript := preload("res://scripts/hub_collision.gd")
const HubNavScript := preload("res://scripts/hub_nav.gd")
const HubEconomyScript := preload("res://scripts/hub_economy.gd")
const HubShowScript := preload("res://scripts/hub_show.gd")

const PLAYER := "ShowTester"
const CANTINA := HubShowScript.CANTINA
const INN := HubShowScript.INN


func _init() -> void:
	var collision = HubCollisionScript.new()
	collision.reload()
	var nav = HubNavScript.new()
	nav.build(collision)

	var economy = HubEconomyScript.new()
	economy.setup()
	var p: Dictionary = economy._player(PLAYER)
	p["credits"] = 100
	p["active"] = []
	economy._save_players()

	var sim = HubSimScript.new()
	sim.nav = nav
	sim.collision = collision
	sim.attach_economy(economy)
	sim.reset()
	assert(sim.show != null, "show module missing")
	assert(str(sim.show.phase) == "idle", "boot idle")

	# Force live immédiat.
	sim.show.phase = "live"
	sim.show.phase_until = Time.get_unix_time_from_system() + 60.0
	sim.show.show_id = 1
	sim.show._ensure_artiste(sim, true)
	assert(sim.entities.has(HubShowScript.ARTISTE_EID), "artiste on stage")
	assert(sim.show.is_live(), "live")

	sim.ensure_human(100888, PLAYER)
	sim.set_human_pos(100888, CANTINA.x + 2.0, CANTINA.y, CANTINA.z + 2.0)

	var ok_live: Dictionary = sim.show.validate_tip(sim, PLAYER, 2)
	assert(bool(ok_live.get("ok")), "tip should ok while live near stage: %s" % str(ok_live))

	sim.show.phase = "idle"
	var gated: Dictionary = sim.show.validate_tip(sim, PLAYER, 2)
	assert(not bool(gated.get("ok")), "tip blocked when idle: %s" % str(gated))
	assert(str(gated.get("error", "")) == "show_not_live", "err=%s" % str(gated))

	sim.show.phase = "live"
	sim.show.phase_until = Time.get_unix_time_from_system() + 60.0
	var tip: Dictionary = economy.tip(PLAYER, "lh_show_perle", 2)
	assert(bool(tip.get("ok")), "tip economy: %s" % str(tip))
	var meta: Dictionary = sim.show.on_tip_ok(PLAYER, 2)
	assert(int(meta.get("tips_this_show", 0)) >= 1, "tips meta=%s" % str(meta))

	# Formation trop loin (encore à la cantina).
	var far: Dictionary = sim.show.train(sim, economy, PLAYER)
	assert(not bool(far.get("ok")), "train far: %s" % str(far))

	sim.set_human_pos(100888, INN.x + 1.0, INN.y, INN.z + 1.0)
	var train: Dictionary = sim.show.train(sim, economy, PLAYER)
	assert(bool(train.get("ok")), "train: %s" % str(train))
	assert(str(train.get("trainer", "")) == "Talen Ress", "trainer=%s" % str(train))

	var again: Dictionary = sim.show.train(sim, economy, PLAYER)
	assert(not bool(again.get("ok")), "cooldown: %s" % str(again))

	# Cycle idle→live via tick time jump.
	sim.show.phase = "idle"
	sim.show.phase_until = Time.get_unix_time_from_system() - 1.0
	sim.show.tick(sim, 0.05)
	assert(sim.show.phase == "live", "advance to live got %s" % sim.show.phase)

	if sim.player_store != null:
		sim.player_store.shutdown()

	print("SHOW_SELFTEST_OK: live+tip+train+cycle")
	quit(0)
