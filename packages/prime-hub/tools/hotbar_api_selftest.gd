extends SceneTree
## Self-test API hotbar — use_item + companion escort.
##
##   packages/prime-hub/tools/godot --headless --path packages/prime-hub \
##     -s res://tools/hotbar_api_selftest.gd

const HubSimScript := preload("res://scripts/hub_sim.gd")
const HubCollisionScript := preload("res://scripts/hub_collision.gd")
const HubNavScript := preload("res://scripts/hub_nav.gd")
const HubEconomyScript := preload("res://scripts/hub_economy.gd")

const PLAYER := "HotbarTester"


func _init() -> void:
	var collision = HubCollisionScript.new()
	collision.reload()
	var nav = HubNavScript.new()
	nav.build(collision)

	var economy = HubEconomyScript.new()
	economy.setup()
	var p: Dictionary = economy._player(PLAYER)
	p["inventory"] = [
		{"id": "water_capsule", "name": "Capsule d'eau", "qty": 2, "icon": "kit"},
		{"id": "scrap_metal", "name": "Ferraille", "qty": 3, "icon": "copper"},
	]
	p["credits"] = 40
	economy._save_players()

	var use1: Dictionary = economy.use_item(PLAYER, "water_capsule")
	assert(bool(use1.get("ok")), "use water: %s" % str(use1))
	assert(int(use1.get("qty_left", -1)) == 1, "qty_left=%s" % str(use1))

	var use_auto: Dictionary = economy.use_item(PLAYER, "")
	assert(bool(use_auto.get("ok")), "use auto: %s" % str(use_auto))
	assert(str(use_auto.get("item_id", "")) == "water_capsule", str(use_auto))

	var use_none: Dictionary = economy.use_item(PLAYER, "")
	assert(not bool(use_none.get("ok")), "should fail no consumable: %s" % str(use_none))

	var sim = HubSimScript.new()
	sim.nav = nav
	sim.collision = collision
	sim.attach_economy(economy)
	sim.reset()
	sim.ensure_human(100999, PLAYER)
	var esc: Dictionary = sim.start_companion_escort_for(PLAYER, 20.0)
	assert(bool(esc.get("ok")), "escort: %s" % str(esc))
	assert(str(esc.get("companion", "")) != "", str(esc))

	if sim.player_store != null:
		sim.player_store.shutdown()

	print("HOTBAR_API_SELFTEST_OK: use+escort")
	quit(0)
