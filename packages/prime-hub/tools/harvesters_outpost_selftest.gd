extends SceneTree
## harvesters_outpost_selftest.gd — Validation headless des Extracteurs de Terrain (Harvesters) & Boucle O3 (Ticket 4.5).

const HubCollisionScript := preload("res://scripts/hub_collision.gd")
const HubEconomyScript := preload("res://scripts/hub_economy.gd")
const HubSkillsScript := preload("res://scripts/hub_skills.gd")
const HubSurveyScript := preload("res://scripts/hub_survey.gd")
const HubHamMedicalScript := preload("res://scripts/hub_ham_medical.gd")
const HubHarvestersScript := preload("res://scripts/hub_harvesters.gd")
const HubBotAutonomyScript := preload("res://scripts/hub_bot_autonomy.gd")


func _init() -> void:
	print("[*] Lancement du test Extracteurs de Terrain (Harvesters) & Autonomie O3 SWG Pre-CU (Ticket 4.5)...")

	var collision := HubCollisionScript.new()
	collision.reload()

	var economy := HubEconomyScript.new()
	economy.setup()

	var skills := HubSkillsScript.new()
	skills.setup(economy)

	var survey := HubSurveyScript.new()
	survey.setup(economy, skills)

	var ham_med := HubHamMedicalScript.new()
	ham_med.setup(economy, skills)

	var harvesters := HubHarvestersScript.new()
	harvesters.setup(economy, survey, skills, collision)

	var autonomy := HubBotAutonomyScript.new()
	autonomy.setup(economy, null, {}, null)

	var player := "Nix_HarvesterBot_%d" % (Time.get_ticks_msec() % 100000)

	# 1. Déploiement d'un extracteur sur la veine d'Oris (Silice cristalline, 4842, -612)
	var dep := harvesters.deploy_harvester(player, "res_lh_silica_oris", 4840.0, -610.0, 15.0)
	assert(bool(dep.get("ok", false)) == true, "Déploiement d'extracteur sur gisement dense doit réussir")
	var h_info: Dictionary = dep.get("harvester", {})
	var hid := str(h_info.get("harvester_id", ""))
	assert(not hid.is_empty(), "harvester_id doit être généré")
	print("[+] PASS: Extracteur %s déployé sur %s (densité=%d%%, BER=%.1f)" % [
		hid,
		str(h_info.get("spawn_name", "")),
		int(h_info.get("local_density_pct", 0)),
		float(h_info.get("ber", 0.0))
	])

	# 2. Refus de dépasser le plafond de slots d'extracteur (1 slot de base avant Citoyen/Master)
	var dep_excess := harvesters.deploy_harvester(player, "res_lh_copper_kovess", 4795.0, -565.0, 12.0)
	assert(bool(dep_excess.get("ok", false)) == false, "Second extracteur sans slot supplémentaire doit être refusé")
	assert(str(dep_excess.get("error", "")) == "max_harvester_slots_reached", "Erreur attendue: max_harvester_slots_reached")

	# 3. Simulation de 5 cycles d'extraction -> remplissage du Hopper et arbitrage autonome O3
	harvesters.advance_cycles(5)
	var prio := autonomy.evaluate_swg_precu_priority(player, ham_med, harvesters)
	assert(str(prio.get("decision", "")) == "collect_harvester_hopper", "Le bot O3 doit décider de vidanger son Hopper plein")
	print("[+] PASS: Arbitrage autonome O3 détecte le Hopper prêt (%d unités -> %s)" % [
		int(prio.get("hopper_ready_qty", 0)),
		str(prio.get("decision", ""))
	])

	# 4. Collecte du Hopper dans l'inventaire du joueur avec conservation des stats (OQ=910)
	var col := harvesters.collect_hopper(player, hid)
	assert(bool(col.get("ok", false)) == true, "collect_hopper doit réussir")
	assert(int(col.get("collected_qty", 0)) >= 40, "Au moins 40 unités de Silice d'Oris récoltées")
	var r_stats: Dictionary = col.get("resource_stats", {})
	assert(int(r_stats.get("oq", 0)) == 910, "La ressource collectée doit conserver son OQ=910")
	print("[+] PASS: Vidange du Hopper (%d unités de Silice d'Oris OQ=910 transférées à l'inventaire)" % int(col.get("collected_qty", 0)))

	if economy.db != null and economy.db.has_method("shutdown"):
		economy.db.shutdown()

	print("[+] Ticket 4.5 (Extracteurs Harvesters & Boucle O3) : Tous les tests passent avec succès !")
	quit(0)

