extends SceneTree
## craft_experimentation_selftest.gd — Validation headless de l'Artisanat Pondéré & Phase d'Expérimentation (Ticket 4.3).

const HubCollisionScript := preload("res://scripts/hub_collision.gd")
const HubEconomyScript := preload("res://scripts/hub_economy.gd")
const HubSkillsScript := preload("res://scripts/hub_skills.gd")
const HubSurveyScript := preload("res://scripts/hub_survey.gd")
const HubCraftingScript := preload("res://scripts/hub_crafting.gd")


func _init() -> void:
	print("[*] Lancement du test Artisanat Pondéré & Phase d'Expérimentation SWG Pre-CU (Ticket 4.3)...")

	var collision := HubCollisionScript.new()
	collision.reload()

	var economy := HubEconomyScript.new()
	economy.setup()

	var skills := HubSkillsScript.new()
	skills.setup(economy)

	var survey := HubSurveyScript.new()
	survey.setup(economy, skills)

	var crafting := HubCraftingScript.new()
	crafting.setup(economy, collision, skills)

	var player := "TestMasterCrafter_%d" % (Time.get_ticks_msec() % 100000)
	skills.learn_box(player, "artisan_outils_01", true)
	skills.learn_box(player, "artisan_outils_02", true)

	# 1. Extraction de Cuivre Kovessien haute qualité (OQ 860, CD 920) + ajout d'un condensateur
	survey.sample_resource(player, "res_lh_copper_kovess", 4795.0, -565.0)
	economy.grant_world_loot(player, [
		{"id": "used_capacitor", "qty": 2, "name": "Condensateur usé"},
	], 0)

	var craft_anchors := collision.get_furniture_anchors("craft")
	var bench_pos: Vector3 = (craft_anchors[0] as Dictionary).get("pos", Vector3.ZERO)

	# 2. Assemblage sur l'établi CAO -> Ouverture d'une session d'expérimentation
	var assemble_res := crafting.assemble_at_bench(player, "mechatronic_repair_kit", bench_pos + Vector3(1.0, 0.0, 0.0), 8.0)
	assert(bool(assemble_res.get("ok", false)) == true, "Assemblage sur établi doit réussir")
	var exp_sess: Dictionary = assemble_res.get("experiment_session", {})
	var sess_id := str(exp_sess.get("session_id", ""))
	assert(not sess_id.is_empty(), "Une session d'expérimentation doit être créée")
	var init_stats: Dictionary = assemble_res.get("item_stats", {})
	var init_power := int(init_stats.get("power", 0))
	var init_qual := float(init_stats.get("quality_pct", 0.0))
	assert(init_qual > 50.0, "La qualité initiale pondérée par OQ=860 doit dépasser 50%")
	print("[+] PASS: Assemblage pondéré initial : serial=%s, quality=%.1f%%, power=%d, points_exp=%d" % [
		str(assemble_res.get("serial", "")),
		init_qual,
		init_power,
		int(exp_sess.get("remaining_points", 0))
	])

	# 3. Expérimentation (Amazing Success roll = 0.92) sur l'attribut 'power'
	var exp_res := crafting.experiment(player, sess_id, "power", 2, 0.92)
	assert(bool(exp_res.get("ok", false)) == true, "L'expérimentation doit réussir")
	assert(str(exp_res.get("outcome", "")) == "amazing_success", "Jet 0.92 doit produire amazing_success")
	var updated_stats: Dictionary = exp_res.get("item_stats", {})
	assert(int(updated_stats.get("power", 0)) > init_power, "La puissance de l'objet doit avoir augmenté après expérimentation")
	print("[+] PASS: Expérimentation Amazing Success : power %d -> %d (points restants=%d)" % [
		init_power,
		int(updated_stats.get("power", 0)),
		int(exp_res.get("remaining_points", 0))
	])

	if economy.db != null and economy.db.has_method("shutdown"):
		economy.db.shutdown()

	print("[+] Ticket 4.3 (Artisanat Pondéré & Expérimentation) : Tous les tests passent avec succès !")
	quit(0)

