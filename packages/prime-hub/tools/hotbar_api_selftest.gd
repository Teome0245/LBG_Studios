extends SceneTree
## Self-test API hotbar — use_item + craft cost (D1) + companion escort.
##
##   packages/prime-hub/tools/godot --headless --path packages/prime-hub \
##     -s res://tools/hotbar_api_selftest.gd

const HubSimScript := preload("res://scripts/hub_sim.gd")
const HubCollisionScript := preload("res://scripts/hub_collision.gd")
const HubNavScript := preload("res://scripts/hub_nav.gd")
const HubEconomyScript := preload("res://scripts/hub_economy.gd")

const PLAYER := "HotbarTester"


func _assert_cost(resp: Dictionary, expect_substr: String = "") -> void:
	var cost = resp.get("cost", {})
	assert(typeof(cost) == TYPE_DICTIONARY, "cost missing: %s" % str(resp))
	var summary := str(cost.get("summary", "")).strip_edges()
	assert(summary != "", "cost.summary empty: %s" % str(cost))
	assert(typeof(cost.get("inputs")) == TYPE_ARRAY, "cost.inputs: %s" % str(cost))
	assert(typeof(cost.get("sources")) == TYPE_ARRAY, "cost.sources: %s" % str(cost))
	if expect_substr != "":
		assert(summary.find(expect_substr) >= 0, "summary=%s expect %s" % [summary, expect_substr])


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
		{"id": "scrap_metal", "name": "Ferraille", "qty": 4, "icon": "copper"},
		{"id": "binding_tape", "name": "Ruban de liaison", "qty": 2, "icon": "screw"},
	]
	p["skills"] = ["prospecteur_r1", "artisan_rue_r1", "medecine_camp_r1", "pilotage_shuttle_r1"]
	p["credits"] = 40
	economy._save_players()

	var use1: Dictionary = economy.use_item(PLAYER, "water_capsule")
	assert(bool(use1.get("ok")), "use water: %s" % str(use1))
	assert(int(use1.get("qty_left", -1)) == 1, "qty_left=%s" % str(use1))
	_assert_cost(use1, "water_capsule")

	var use_auto: Dictionary = economy.use_item(PLAYER, "")
	assert(bool(use_auto.get("ok")), "use auto: %s" % str(use_auto))
	assert(str(use_auto.get("item_id", "")) == "water_capsule", str(use_auto))
	_assert_cost(use_auto, "consomme")

	var use_none: Dictionary = economy.use_item(PLAYER, "")
	assert(not bool(use_none.get("ok")), "should fail no consumable: %s" % str(use_none))

	var craft: Dictionary = economy.craft_combine(PLAYER, "kit_reparation")
	assert(bool(craft.get("ok")), "craft kit: %s" % str(craft))
	_assert_cost(craft, "scrap_metal")
	assert(str(craft.get("cost", {}).get("summary", "")).find("kit_reparation") >= 0, str(craft.get("cost")))

	var craft_miss: Dictionary = economy.craft_combine(PLAYER, "kit_reparation")
	# Peut réussir encore (reste scrap/tape) ou échouer missing_inputs — cost toujours présent.
	_assert_cost(craft_miss, "scrap_metal")

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

	print("HOTBAR_API_SELFTEST_OK: use+craft_cost+escort")
	quit(0)
