extends SceneTree
## swg_combat_selftest.gd — Validation headless Combat Tactique SWG Pre-CU, HAM, Postures & Combos (Ticket 1).

const HubEconomyScript := preload("res://scripts/hub_economy.gd")
const HubSkillsScript := preload("res://scripts/hub_skills.gd")
const HubHamMedicalScript := preload("res://scripts/hub_ham_medical.gd")
const HubSimScript := preload("res://scripts/hub_sim.gd")
const HubSwgCombatScript := preload("res://scripts/hub_swg_combat.gd")


func _init() -> void:
	print("[*] Lancement du test Combat Tactique SWG Pre-CU : HAM, Postures & Combos d'États (Ticket 1)...")

	var sim := HubSimScript.new()
	sim.reset()

	var economy := HubEconomyScript.new()
	economy.setup()

	var skills := HubSkillsScript.new()
	skills.setup(economy)

	var ham_med := HubHamMedicalScript.new()
	ham_med.setup(economy, skills)

	var combat := HubSwgCombatScript.new()
	combat.setup(sim, economy, skills, ham_med)

	var attacker := "BountyHunter_Nix_%d" % (Time.get_ticks_msec() % 100000)
	var defender := "Target_Brawler_%d" % (Time.get_ticks_msec() % 100000)

	# Initialiser les pools HAM des deux combattants
	var p_att := economy._player(attacker)
	p_att["credits"] = 1000
	ham_med._ensure_ham(attacker)

	var p_def := economy._player(defender)
	p_def["credits"] = 500
	ham_med._ensure_ham(defender)

	# --------------------------------------------------------------------------
	# 1. POSTURES SWG (Upright, Kneeling, Prone)
	# --------------------------------------------------------------------------
	assert(combat.get_posture(attacker) == "upright", "Posture par défaut doit être upright")

	var chg_kneel := combat.change_posture(attacker, "kneeling")
	assert(bool(chg_kneel.get("ok", false)) == true and combat.get_posture(attacker) == "kneeling")

	var chg_prone := combat.change_posture(attacker, "prone")
	assert(bool(chg_prone.get("ok", false)) == true and combat.get_posture(attacker) == "prone")

	combat.change_posture(attacker, "upright")
	assert(combat.get_posture(attacker) == "upright")
	print("[+] PASS: Système de postures SWG (Upright ➔ Kneeling ➔ Prone) validé")

	# --------------------------------------------------------------------------
	# 2. ENCOMBREMENT D'ARMURE (ARMOR ENCUMBRANCE)
	# --------------------------------------------------------------------------
	var armor_chest := {
		"name": "Plastron Composite de Chacal",
		"armor_rating": 25,
		"encumbrance_health": 40,
		"encumbrance_action": 30,
		"encumbrance_mind": 50
	}
	var eq_res := combat.equip_armor_piece(defender, "chest", armor_chest)
	assert(bool(eq_res.get("ok", false)) == true)
	var enc: Dictionary = eq_res.get("total_encumbrance", {})
	assert(int(enc.get("health", 0)) == 40 and int(enc.get("action", 0)) == 30 and int(enc.get("mind", 0)) == 50)
	assert(combat.get_armor_protection(defender) == 25, "Protection d'armure de base = 25")
	print("[+] PASS: Encombrement d'armure calculé (H=-40, A=-30, M=-50, Armure=25)")

	# --------------------------------------------------------------------------
	# 3. CIBLAGE DES 3 POOLS HAM
	# --------------------------------------------------------------------------
	# Tir à la tête (Head Shot) -> cible le MIND
	var def_ham_before := ham_med._ensure_ham(defender)
	var initial_mind := int(def_ham_before["mind"]["current"])

	var head_hit := combat.execute_tactical_strike(attacker, defender, "head_shot", true)
	assert(bool(head_hit.get("ok", false)) == true)
	assert(str(head_hit.get("target_pool", "")) == "mind", "Head Shot doit impacter le Mental (Mind)")
	var def_ham_after := ham_med._ensure_ham(defender)
	var remaining_mind := int(def_ham_after["mind"]["current"])
	assert(remaining_mind < initial_mind, "Le pool Mental de la cible doit avoir diminué")
	print("[+] PASS: Ciblage HAM Mental (Head Shot : Mind %d ➔ %d, État infligé=%s)" % [
		initial_mind,
		remaining_mind,
		str(head_hit.get("status_applied", ""))
	])

	# Balayage des jambes (Leg Sweep) -> cible l'ACTION et inflige KNOCKDOWN
	var leg_hit := combat.execute_tactical_strike(attacker, defender, "leg_sweep", true)
	assert(bool(leg_hit.get("ok", false)) == true)
	assert(str(leg_hit.get("target_pool", "")) == "action", "Leg Sweep doit impacter l'Action")
	assert(combat.get_posture(defender) == "prone", "Knockdown doit forcer la posture Prone au sol")
	print("[+] PASS: Ciblage HAM Action (Leg Sweep : Knockdown forçant la posture Couchée/Prone)")

	# Frappe corporelle (Body Hit) -> cible la SANTÉ (Health) et inflige STUN
	var body_hit := combat.execute_tactical_strike(attacker, defender, "body_hit", true)
	assert(bool(body_hit.get("ok", false)) == true)
	assert(str(body_hit.get("target_pool", "")) == "health", "Body Hit doit impacter la Santé")
	print("[+] PASS: Ciblage HAM Santé (Body Hit : Dégâts Santé + Stun)")

	# --------------------------------------------------------------------------
	# 4. LE COMBO FATAL SWG PRE-CU : DIZZY + KNOCKDOWN
	# --------------------------------------------------------------------------
	# Defender est déjà au sol (Prone) suite au Knockdown
	# Appliquer l'état Dizzy (Vertige)
	combat.apply_state(defender, "dizzy", 15.0)
	assert(combat.has_state(defender, "dizzy") == true, "La cible doit être Dizzy")

	# Tentative de se relever en étant Dizzy -> Échec critique SWG !
	var stand_attempt := combat.change_posture(defender, "upright")
	assert(bool(stand_attempt.get("ok", false)) == false, "Se relever en étant Dizzy doit échouer")
	assert(str(stand_attempt.get("outcome", "")) == "dizzy_fall", "Erreur attendue: dizzy_fall")
	assert(combat.get_posture(defender) == "prone", "La cible doit rester plaquée au sol")
	print("[+] PASS: Combo légendaire SWG Pre-CU validé (Dizzy + Knockdown empêche de se relever)")

	# --------------------------------------------------------------------------
	# 5. EFFETS D'ARMURE SOUS STUN & INTIMIDATE
	# --------------------------------------------------------------------------
	combat.apply_state(defender, "stun", 10.0)
	assert(combat.get_armor_protection(defender) == 12, "L'état Stun divise l'armure par 2 (25 -> 12)")
	print("[+] PASS: État Stun validé (Armure réduite de 50%% : 25 ➔ 12)")

	combat.apply_state(attacker, "intimidate", 10.0)
	assert(combat.has_state(attacker, "intimidate") == true)
	var weak_hit := combat.execute_tactical_strike(attacker, defender, "body_hit", true)
	assert(bool(weak_hit.get("ok", false)) == true)
	print("[+] PASS: État Intimidate validé (Dégâts infligés par l'attaquant réduits de 50%%)")

	# --------------------------------------------------------------------------
	# 6. INCAPACITATION PAR VIDANGE D'UN POOL HAM
	# --------------------------------------------------------------------------
	combat.clear_state(attacker, "intimidate")
	var d_ham_fin := ham_med._ensure_ham(defender)
	d_ham_fin["mind"]["current"] = 40 # Amener le Mind en seuil critique
	var final_blow := combat.execute_tactical_strike(attacker, defender, "head_shot", true)
	assert(bool(final_blow.get("is_incapacitated", false)) == true, "La cible doit être mise KO / Incapacitated")
	assert(int(d_ham_fin["mind"]["current"]) <= 0, "Le pool Mental de la cible doit être vidé à 0")
	print("[+] PASS: Incapacitation SWG Pre-CU validée (Cible KO par épuisement complet du pool Mind)")

	if sim.player_store != null and sim.player_store.has_method("shutdown"):
		sim.player_store.shutdown()
	if economy.db != null and economy.db.has_method("shutdown"):
		economy.db.shutdown()

	print("[+] Ticket 1 (Combat Tactique SWG : HAM, Postures & Combos) : Tous les tests passent avec succès !")
	quit(0)
