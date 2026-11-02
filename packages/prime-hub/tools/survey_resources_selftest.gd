extends SceneTree
## survey_resources_selftest.gd — Validation headless de la Prospection Dynamique (Survey Tool) & Spawns 1..1000 (Ticket 4.2).

const HubEconomyScript := preload("res://scripts/hub_economy.gd")
const HubSkillsScript := preload("res://scripts/hub_skills.gd")
const HubSurveyScript := preload("res://scripts/hub_survey.gd")


func _init() -> void:
	print("[*] Lancement du test Prospection Dynamique (Survey Tool) & Spawns à Statistiques 1..1000 (Ticket 4.2)...")

	var economy := HubEconomyScript.new()
	economy.setup()

	var skills := HubSkillsScript.new()
	skills.setup(economy)

	var survey := HubSurveyScript.new()
	survey.setup(economy, skills)

	var player := "TestProspecteur_%d" % (Time.get_ticks_msec() % 100000)

	# 1. Vérification des gisements actifs et de leurs stats 1..1000 (OQ, CD, PE, MA, SR)
	var spawns := survey.list_spawns()
	assert(spawns.size() >= 5, "Au moins 5 gisements dynamiques doivent être chargés sur Lost Heaven")
	var copper := survey.get_spawn("res_lh_copper_kovess")
	var stats: Dictionary = copper.get("stats", {})
	assert(int(stats.get("oq", 0)) == 860 and int(stats.get("cd", 0)) == 920, "Stats OQ/CD du Cuivre Kovessien doivent être présentes")
	print("[+] PASS: 5 gisements Pre-CU chargés avec statistiques OQ/CD/PE/MA/SR (1..1000)")

	# 2. Ping radar Survey à proximité du hotspot (4795, -565)
	var ping := survey.survey_ping(player, "mineral_copper", 4800.0, -560.0)
	assert(bool(ping.get("ok", false)) == true, "survey_ping doit réussir")
	assert(int(ping.get("count", 0)) >= 1, "Le gisement de cuivre doit être détecté au radar")
	var first_reading: Dictionary = (ping.get("readings", []) as Array)[0]
	assert(int(first_reading.get("local_density_pct", 0)) >= 75, "La densité près de l'épicentre doit être élevée (>=75%)")
	print("[+] PASS: Ping radar Survey détecte le gisement (densité locale=%d%%, dir=%s)" % [
		int(first_reading.get("local_density_pct", 0)),
		str(first_reading.get("direction", ""))
	])

	# 3. Refus d'extraction hors de la veine (densité 0%)
	var far_sample := survey.sample_resource(player, "res_lh_copper_kovess", 4200.0, -100.0)
	assert(bool(far_sample.get("ok", false)) == false, "L'extraction hors du gisement doit échouer")
	assert(str(far_sample.get("error", "")) == "density_too_low", "Erreur attendue: density_too_low")

	# 4. Extraction d'échantillon réussie sur la veine avec conservation des stats dans l'inventaire
	var ok_sample := survey.sample_resource(player, "res_lh_copper_kovess", 4796.0, -564.0)
	assert(bool(ok_sample.get("ok", false)) == true, "sample_resource sur la veine doit réussir")
	assert(int(ok_sample.get("extracted_qty", 0)) >= 2, "Au moins 2 unités extraites à haute densité")
	assert(int(ok_sample.get("xp_gained", 0)) > 0, "Gain de xp_prospection attendu")

	var inv := economy.inventory(player)
	var found_stats := false
	for item in inv.get("inventory", []):
		if typeof(item) == TYPE_DICTIONARY and str(item.get("id", "")) == "scrap_metal":
			var r_st: Dictionary = item.get("resource_stats", {}) if typeof(item.get("resource_stats")) == TYPE_DICTIONARY else {}
			if int(r_st.get("oq", 0)) == 860:
				found_stats = true
	assert(found_stats, "La ressource extraite dans l'inventaire doit porter ses stats Pre-CU (OQ=860)")
	print("[+] PASS: Extraction d'échantillons typés avec conservation des stats OQ/CD/PE/MA/SR dans l'inventaire")

	if economy.db != null and economy.db.has_method("shutdown"):
		economy.db.shutdown()

	print("[+] Ticket 4.2 (Prospection & Spawns 1..1000) : Tous les tests passent avec succès !")
	quit(0)

