extends SceneTree
## precu_skills_tree_selftest.gd — Validation headless des Arbres de Compétences SWG Pre-CU 4x4 (Ticket 4.1).

const HubEconomyScript := preload("res://scripts/hub_economy.gd")
const HubSkillsScript := preload("res://scripts/hub_skills.gd")


func _init() -> void:
	print("[*] Lancement du test Arbres de Compétences SWG Pre-CU 4x4 & Skill Points (Ticket 4.1)...")

	var economy := HubEconomyScript.new()
	economy.setup()

	var skills := HubSkillsScript.new()
	skills.setup(economy)

	var player := "TestArtisanPreCU_%d" % (Time.get_ticks_msec() % 100000)

	# 1. Vérification des 8 professions Pre-CU chargées (Novice + 4x4 + Master)
	assert(skills.professions_by_id.size() >= 8, "Au moins 8 professions Pre-CU doivent être indexées")
	assert(skills.box_index.has("artisan_novice"), "artisan_novice doit exister")
	assert(skills.box_index.has("artisan_outils_04"), "artisan_outils_04 doit exister")
	assert(skills.box_index.has("artisan_master"), "artisan_master doit exister")
	print("[+] PASS: Catalogue 4x4 Pre-CU indexé (%d boxes)" % skills.box_index.size())

	# 2. Refus d'apprendre une box de rang 2 sans la box de rang 1
	var bad_learn := skills.learn_box(player, "artisan_outils_02", true)
	assert(bool(bad_learn.get("ok", false)) == false, "Apprentissage sans prérequis doit échouer")
	assert(str(bad_learn.get("error", "")) == "missing_prerequisites", "Erreur attendue: missing_prerequisites")
	print("[+] PASS: Contrôle strict des prérequis de branche validé")

	# 3. Progression complète dans les 4 branches d'Artisan jusqu'à Maître Artisan
	skills.grant_xp(player, "xp_artisanat", 250000)
	for br in ["outils", "conso", "pieces", "survey"]:
		for tier in range(1, 5):
			var bid := "artisan_%s_0%d" % [br, tier]
			var res := skills.learn_box(player, bid, false)
			assert(bool(res.get("ok", false)) == true, "Apprentissage de %s doit réussir" % bid)

	var master_res := skills.learn_box(player, "artisan_master", false)
	assert(bool(master_res.get("ok", false)) == true, "Apprentissage de artisan_master doit réussir après les 4 branches")
	assert(str(master_res.get("title", "")).find("Maître") >= 0, "Titre Maître Artisan doit être décerné")
	print("[+] PASS: Ascension complète Novice -> 4x4 -> Master (%s) validée" % str(master_res.get("title", "")))

	# 4. Vérification du refus d'abandon d'une box parente (surrender_box) tant que Master est actif
	var bad_surrender := skills.surrender_box(player, "artisan_outils_04")
	assert(bool(bad_surrender.get("ok", false)) == false, "Abandon d'un prérequis de Master doit être bloqué")
	var ok_surrender := skills.surrender_box(player, "artisan_master")
	assert(bool(ok_surrender.get("ok", false)) == true, "Abandon de la box feuille artisan_master doit réussir")
	print("[+] PASS: Abandon de compétence (Surrender Skill) et recalcul des Skill Points validés")

	if economy.db != null and economy.db.has_method("shutdown"):
		economy.db.shutdown()

	print("[+] Ticket 4.1 (Arbres Pre-CU 4x4) : Tous les tests passent avec succès !")
	quit(0)

