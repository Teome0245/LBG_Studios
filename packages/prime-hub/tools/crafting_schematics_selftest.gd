extends SceneTree
## crafting_schematics_selftest.gd — Validation headless du Métier Récupérateur & Établis Mécatroniques (Ticket 2.2 O2 Phase 3).
##
## Usage:
##   packages/prime-hub/tools/Godot_v4.6.3-stable_linux.x86_64 --headless \
##     --path packages/prime-hub -s res://tools/crafting_schematics_selftest.gd

const HubCollisionScript := preload("res://scripts/hub_collision.gd")
const HubEconomyScript := preload("res://scripts/hub_economy.gd")
const HubCraftingScript := preload("res://scripts/hub_crafting.gd")


func _init() -> void:
	print("[*] Lancement du test Établis d'Assemblage Mécatronique & Recettes de Terrain (Ticket 2.2 O2)...")

	var collision := HubCollisionScript.new()
	collision.reload()

	var economy := HubEconomyScript.new()
	economy.setup()

	var crafting := HubCraftingScript.new()
	crafting.setup(economy, collision)

	# Test 1 : Vérification des 4 recettes canoniques
	var list := crafting.list_schematics()
	assert(list.size() == 4, "4 recettes canoniques de récupération doivent être chargées")
	assert( not crafting.get_schematic("mechatronic_repair_kit").is_empty(), "mechatronic_repair_kit doit exister")
	assert( not crafting.get_schematic("oasis_condensate_filter").is_empty(), "oasis_condensate_filter doit exister")
	assert( not crafting.get_schematic("regulated_scrap_battery").is_empty(), "regulated_scrap_battery doit exister")
	assert( not crafting.get_schematic("night_prospecting_torch").is_empty(), "night_prospecting_torch doit exister")
	print("[+] PASS: 4 recettes canoniques du métier Récupérateur chargées")

	# Test 2 : Détection de l'ancrage d'établi CAO (`craft`) au Hangar Dépôt Nord
	var craft_anchors := collision.get_furniture_anchors("craft")
	assert(craft_anchors.size() >= 1, "Au moins 1 établi d'assemblage CAO (`craft`) doit être indexé")
	var bench_anchor: Dictionary = craft_anchors[0]
	var bench_pos: Vector3 = bench_anchor.get("pos", Vector3.ZERO)
	print("  - Établi CAO détecté : id=%s label='%s' pos=%s" % [
		str(bench_anchor.get("id", "")),
		str(bench_anchor.get("label", "")),
		str(bench_pos)
	])

	# Test 3 : Refus d'assemblage si trop éloigné de l'établi
	var far_pos := bench_pos + Vector3(65.0, 0.0, 65.0)
	var res_far := crafting.assemble_at_bench("TestRecuperateur", "mechatronic_repair_kit", far_pos, 8.0)
	assert(res_far.get("ok") == false, "L'assemblage sur établi doit échouer à distance")
	assert(str(res_far.get("error", "")) == "not_near_craft_bench", "L'erreur doit être not_near_craft_bench")
	print("[+] PASS: Validation stricte de proximité d'ancrage `craft` vérifiée")

	# Test 4 : Assemblage réussi à proximité de l'établi avec 3 ferrailles + 1 condensateur usé
	var player := "TestRecuperateurBench"
	economy.grant_world_loot(player, [
		{"id": "scrap_metal", "qty": 3, "name": "Ferraille"},
		{"id": "used_capacitor", "qty": 1, "name": "Condensateur usé"},
	], 0)

	var near_pos := bench_pos + Vector3(1.2, 0.0, -0.8)
	var res_ok := crafting.assemble_at_bench(player, "mechatronic_repair_kit", near_pos, 8.0)
	assert(res_ok.get("ok") == true, "L'assemblage près de l'établi avec les ingrédients requis doit réussir")
	assert(str(res_ok.get("posture", "")) == "craft", "La posture Triplon doit être 'craft'")
	assert(str(res_ok.get("bench_anchor_id", "")) == str(bench_anchor.get("id", "")), "L'ancrage d'établi doit correspondre")

	# Vérification de l'inventaire après craft
	var inv_after: Array = res_ok.get("inventory", [])
	var found_kit := false
	for item in inv_after:
		if typeof(item) == TYPE_DICTIONARY and str(item.get("id", "")) == "mechatronic_repair_kit":
			assert(int(item.get("qty", 0)) >= 1, "Au moins 1 Kit de réparation mécatronique doit être produit")
			found_kit = true
	assert(found_kit, "Le Kit de réparation mécatronique doit figurer dans l'inventaire")
	print("[+] PASS: Assemblage de mechatronic_repair_kit (3 ferrailles + 1 condensateur usé) et snap posture Triplon validés")

	if economy.db != null and economy.db.has_method("shutdown"):
		economy.db.shutdown()

	print("[+] Métier de Récupérateur & Établis Mécatroniques (Ticket 2.2 O2) : Tous les tests passent avec succès !")
	quit(0)
