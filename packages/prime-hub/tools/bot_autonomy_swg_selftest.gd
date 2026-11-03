extends SceneTree

const HubSimScript := preload("res://scripts/hub_sim.gd")
const HubBotAutonomyScript := preload("res://scripts/hub_bot_autonomy.gd")
const HubCreaturesScript := preload("res://scripts/hub_creatures.gd")
const HubVendorsFactoriesScript := preload("res://scripts/hub_vendors_factories.gd")
const HubHousingCitiesScript := preload("res://scripts/hub_housing_cities.gd")
const HubSwgCombatScript := preload("res://scripts/hub_swg_combat.gd")
const HubSkillsScript := preload("res://scripts/hub_skills.gd")
const HubEconomyScript := preload("res://scripts/hub_economy.gd")


class MockMedicalService extends RefCounted:
	var _status: Dictionary = {}

	func set_status_for(p: String, ham_data: Dictionary) -> void:
		_status[p] = {"ok": true, "ham": ham_data}

	func status(p: String) -> Dictionary:
		return _status.get(p, {
			"ok": true,
			"ham": {
				"health": {"base_max": 1000, "wounds": 0, "effective_max": 1000, "current": 1000},
				"action": {"base_max": 1000, "wounds": 0, "effective_max": 1000, "current": 1000},
				"mind": {"base_max": 1000, "wounds": 0, "effective_max": 1000, "current": 1000},
				"battle_fatigue": 0,
			}
		})


func _init() -> void:
	print("[*] Lancement du test HubBotAutonomy SWG Pre-CU (O3 Arbitrage & Combat)...")

	var economy = HubEconomyScript.new()
	economy.setup()

	var skills = HubSkillsScript.new()
	skills.setup(economy)

	var creatures = HubCreaturesScript.new()
	creatures.setup(null, economy, skills)

	var vendors = HubVendorsFactoriesScript.new()
	vendors.setup(null, economy, skills)

	var housing = HubHousingCitiesScript.new()
	housing.setup(null, economy, skills)

	var combat = HubSwgCombatScript.new()
	combat.setup(null, economy, skills)

	var med = MockMedicalService.new()

	var autonomy = HubBotAutonomyScript.new()
	autonomy.setup(economy, null, {"plaza": Vector3(4749.0, 0.15, -737.0)})
	autonomy.setup_swg_services(creatures, vendors, housing, combat, med)

	# --- TEST 1 : Priorité Fatigue Cantina ---
	med.set_status_for("BotFatigue", {
		"health": {"base_max": 1000, "wounds": 0, "effective_max": 1000, "current": 1000},
		"battle_fatigue": 250,
	})
	var p1: Dictionary = autonomy.evaluate_swg_precu_priority("BotFatigue")
	assert(p1.get("decision") == "visit_cantina_perle", "Priorité 1 doit être Cantina si BF >= 200")
	print("[+] PASS: Priorité Cantina sur Battle Fatigue validée")

	# --- TEST 2 : Priorité Blessures Medcenter ---
	med.set_status_for("BotWoundedCity", {
		"health": {"base_max": 1000, "wounds": 140, "effective_max": 860, "current": 700},
		"battle_fatigue": 50,
	})
	var p2: Dictionary = autonomy.evaluate_swg_precu_priority("BotWoundedCity")
	assert(p2.get("decision") == "visit_medcenter_odo", "Priorité 2 doit être Medcenter si Wounds >= 120 en ville")
	print("[+] PASS: Priorité Medcenter sur blessures lourdes validée")

	# --- TEST 3 : Survie en milieu hostile / Camp Scout ---
	med.set_status_for("BotWilderness", {
		"health": {"base_max": 1000, "wounds": 60, "effective_max": 940, "current": 400},
		"battle_fatigue": 30,
	})
	var dune_pos := Vector3(6000.0, 0.15, -1200.0) # > 1000m du centre
	var p3: Dictionary = autonomy.evaluate_swg_precu_priority("BotWilderness", null, null, null, null, null, dune_pos)
	assert(p3.get("decision") == "deploy_wilderness_camp", "Priorité 3 doit être deploy_wilderness_camp si blessé dans le désert")
	var exec_camp: Dictionary = autonomy.execute_autonomous_action({"name": "BotWilderness"}, p3)
	assert(bool(exec_camp.get("ok", false)) == true, "Le camp scout autonome doit être posé avec succès")
	print("[+] PASS: Survie autonome & déploiement de camp en milieu sauvage validés")

	# --- TEST 4 : Dépeçage autonome de cadavres de bêtes (Harvesting Scout) ---
	var spawn_corpse: Dictionary = creatures.create_corpse("beast:chacal_dore", "Chacal Doré", Vector3(4800, 0, -700))
	var cid: String = str(spawn_corpse.get("corpse_id", ""))
	assert(not cid.is_empty(), "Cadavre de test doit être créé")
	var p4: Dictionary = autonomy.evaluate_swg_precu_priority("BotScout")
	assert(p4.get("decision") == "harvest_beast_corpse", "Priorité 4 doit être le dépeçage d'une bête morte")
	var exec_harvest: Dictionary = autonomy.execute_autonomous_action({"name": "BotScout"}, p4)
	assert(bool(exec_harvest.get("ok", false)) == true and int(exec_harvest.get("qty", 0)) > 0, "Dépeçage autonome doit récolter des ressources")
	print("[+] PASS: Dépeçage autonome de cadavres de faune validé")

	# --- TEST 5 : Retrait bancaire vendeur autonome ---
	economy.grant_world_loot("BotMerchant", [], 1000)
	skills.learn_box("BotMerchant", "artisan_novice", true)
	var v_res: Dictionary = vendors.deploy_vendor("BotMerchant", "Boutique Nomade", 4760.0, -740.0)
	var vid: String = str(v_res.get("vendor_id", ""))
	assert(not vid.is_empty(), "Le vendeur doit être déployé")
	# Injecte des fonds dans la caisse du vendeur
	vendors.vendors_by_id[vid]["bank_credits"] = 450
	var p5: Dictionary = autonomy.evaluate_swg_precu_priority("BotMerchant")
	assert(p5.get("decision") == "collect_vendor_revenue", "Priorité 5 doit être le retrait de la caisse du vendeur si >= 300cr")
	var exec_vendor: Dictionary = autonomy.execute_autonomous_action({"name": "BotMerchant"}, p5)
	assert(bool(exec_vendor.get("ok", false)) == true, "Le retrait bancaire de la boutique doit réussir")
	print("[+] PASS: Retrait bancaire autonome sur boutique de bot validé")

	# --- TEST 6 : Maintenance structure urgente ---
	economy.grant_world_loot("BotCitizen", [], 2000)
	skills.learn_box("BotCitizen", "citoyen_novice", true)
	var h_res: Dictionary = housing.deploy_structure("BotCitizen", "deed_tente_nomade", 5500.0, -1100.0)
	var sid: String = str(h_res.get("struct_id", ""))
	assert(not sid.is_empty(), "La tente doit être déployée hors de la zone protégée")
	housing.structures_by_id[sid]["maintenance_pool"] = 120 # Solde critique (< 200)
	var p6: Dictionary = autonomy.evaluate_swg_precu_priority("BotCitizen")
	assert(p6.get("decision") == "deposit_structure_maintenance", "Priorité 6 doit être le dépôt de maintenance pour éviter la dégradation")
	var exec_house: Dictionary = autonomy.execute_autonomous_action({"name": "BotCitizen"}, p6)
	assert(bool(exec_house.get("ok", false)) == true, "Le dépôt de maintenance autonome doit réussir")
	assert(int(housing.structures_by_id[sid]["maintenance_pool"]) >= 400, "Le solde maintenance doit être réapprovisionné")
	print("[+] PASS: Entretien autonome du housing de bot validé")

	# --- TEST 7 : Prise de décision de Combat Tactique SWG Pre-CU ---
	# Cible debout -> Leg Sweep (Knockdown)
	combat.change_posture("Ennemi1", "upright")
	var combat_step1: Dictionary = autonomy.evaluate_tactical_combat_step("BotFighter", "Ennemi1", combat, med)
	assert(combat_step1.get("chosen_strike") == "leg_sweep", "Contre une cible debout, le bot doit tenter leg_sweep")
	print("[+] PASS: IA Combat - Tentative de balayage tactique (Leg Sweep) validée")

	# Cible au sol (Knockdown) -> Head Shot (Mind) + posture kneeling
	combat.change_posture("EnnemiAuSol", "prone")
	combat.apply_state("EnnemiAuSol", "knockdown", 5.0)
	var combat_step2: Dictionary = autonomy.evaluate_tactical_combat_step("BotFighter", "EnnemiAuSol", combat, med)
	assert(combat_step2.get("chosen_strike") == "head_shot", "Contre une cible au sol, le bot doit tenter head_shot")
	assert(combat_step2.get("chosen_posture") == "kneeling", "Contre une cible au sol, le bot doit s'accroupir pour maximiser sa précision")
	print("[+] PASS: IA Combat - Exploitation combo Head Shot sur cible au sol validée")

	# Bot très blessé (< 25% HP) -> Posture prone défensive
	med.set_status_for("BotAgonisant", {
		"health": {"base_max": 1000, "wounds": 0, "effective_max": 1000, "current": 180},
		"battle_fatigue": 0,
	})
	var combat_step3: Dictionary = autonomy.evaluate_tactical_combat_step("BotAgonisant", "Ennemi1", combat, med)
	assert(combat_step3.get("chosen_posture") == "prone", "Un bot agonisant doit adopter la posture couchée pour réduire les dégâts de 50%")
	print("[+] PASS: IA Combat - Posture défensive prone en cas de danger mortel validée")

	if economy != null and economy.db != null and economy.db.has_method("shutdown"):
		economy.db.shutdown()

	print("BOT_AUTONOMY_SWG_SELFTEST_OK: Tous les comportements O3 SWG Pre-CU des Joueurs IA sont validés avec succès !")
	quit(0)
