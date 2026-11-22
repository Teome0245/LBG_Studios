extends SceneTree

## Selftest Automatisé du Defeat System (Mécaniques Matures / Capture RPG)
## Valide l'interception de l'incapacitation, la lutte QTE, la rançon et la soumission.

const HubEconomyScript = preload("res://scripts/hub_economy.gd")
const HubSkillsScript = preload("res://scripts/hub_skills.gd")
const HubHamMedicalScript = preload("res://scripts/hub_ham_medical.gd")
const HubSimScript = preload("res://scripts/hub_sim.gd")
const HubSwgCombatScript = preload("res://scripts/hub_swg_combat.gd")
const HubDefeatSystemScript = preload("res://scripts/hub_defeat_system.gd")

func _init() -> void:
	print("[*] Lancement du selftest Defeat System (Capture & Mécaniques Matures)...")

	var sim = HubSimScript.new()
	var eco = HubEconomyScript.new()
	var skills = HubSkillsScript.new()
	var ham_med = HubHamMedicalScript.new()
	var combat = HubSwgCombatScript.new()
	var defeat = HubDefeatSystemScript.new()

	skills.setup(eco)
	ham_med.setup(eco, skills, null)
	combat.setup(sim, eco, skills, ham_med)
	defeat.setup(sim, eco, combat, ham_med)
	sim.swg_combat = combat
	sim.defeat_system = defeat

	var player_name := "Aventuriere_Test"
	var bandit_captor := "Bandit_Pillard_01"

	# Initialisation joueur et profil économique
	var p_eco := eco._player(player_name)
	p_eco["credits"] = 500
	var p_ham: Dictionary = ham_med._ensure_ham(player_name)
	assert(p_ham.has("health") and p_ham.has("mind"), "Le HAM du joueur doit être initialisé")

	# 1. Vérification de l'éligibilité du ravisseur
	assert(defeat.is_captor_eligible(bandit_captor) == true, "Le bandit doit être éligible à la capture")
	assert(defeat.is_captor_eligible("Citoyen_Ordinaire") == false, "Un citoyen ne doit pas être un ravisseur")
	print("[+] PASS: Éligibilité des types d'ennemis ravisseurs vérifiée.")

	# 2. Déclenchement de la capture lors d'une défaite au combat (Mind à 0 face au bandit)
	p_ham["mind"]["current"] = 20
	var fatal_strike: Dictionary = combat.execute_tactical_strike(bandit_captor, player_name, "head_shot", true)
	assert(bool(fatal_strike.get("is_incapacitated", false)) == true, "Le joueur doit être mis KO")
	assert(bool(fatal_strike.get("defeat_triggered", false)) == true, "Le Defeat System doit s'être déclenché")
	print("[+] PASS: Incapacitation convertie en événement de capture (Defeat System déclenché).")

	# 3. Vérification de l'état captif
	var state_res: Dictionary = defeat.get_defeat_state(player_name)
	assert(bool(state_res.get("active", false)) == true, "La session de capture doit être active")
	var session: Dictionary = state_res.get("session", {})
	assert(str(session.get("state", "")) == "downed", "L'état initial doit être 'downed'")
	assert(int(session.get("ransom_cost", 0)) > 0, "Une rançon doit être proposée")
	print("[+] PASS: État initial DOWNED et paramètres de rançon validés.")

	# 4. Test du QTE de lutte (Struggle)
	var str1: Dictionary = defeat.struggle(player_name, 30.0)
	assert(bool(str1.get("ok", false)) == true, "L'action de lutte doit réussir")
	assert(float(str1.get("progress", 0.0)) == 30.0, "La progression de lutte doit être de 30%")
	
	# Continuer à lutter jusqu'à l'évasion
	var str2: Dictionary = defeat.struggle(player_name, 75.0)
	assert(str2.get("outcome") == "escaped", "Le joueur doit réussir à s'échapper à 100% de lutte")
	print("[+] PASS: QTE de lutte et libération par résistance validés.")

	# 5. Test de soumission (Capture complète + transfert au camp + perte de crédits)
	var player2 := "Captive_Test2"
	var p2_eco := eco._player(player2)
	p2_eco["credits"] = 200
	ham_med._ensure_ham(player2)
	defeat.on_player_incapacitated(player2, bandit_captor)
	
	var sub_res: Dictionary = defeat.submit(player2, false)
	assert(bool(sub_res.get("ok", false)) == true, "La soumission doit être traitée")
	assert(sub_res.get("outcome") == "submitted", "L'issue doit être 'submitted'")
	assert(int(sub_res.get("lost_credits", 0)) == 50, "50 crédits doivent avoir été confisqués par les pillards")
	print("[+] PASS: Soumission, téléportation au camp et pillage de crédits validés.")

	# 6. Test du paiement de rançon
	var player3 := "Ransom_Test3"
	var p3_eco := eco._player(player3)
	p3_eco["credits"] = 300
	ham_med._ensure_ham(player3)
	defeat.on_player_incapacitated(player3, bandit_captor)
	
	var ran_res: Dictionary = defeat.pay_ransom(player3)
	assert(bool(ran_res.get("ok", false)) == true, "Le rachat de rançon doit réussir")
	assert(ran_res.get("outcome") == "ransomed", "L'issue doit être 'ransomed'")
	assert(int(eco._player(player3).get("credits", 0)) == 150, "Le coût de la rançon (150) doit être déduit")
	print("[+] PASS: Paiement de rançon et libération immédiate validés.")

	# Nettoyage
	if sim.player_store != null and sim.player_store.has_method("shutdown"):
		sim.player_store.shutdown()
	if eco.db != null and eco.db.has_method("shutdown"):
		eco.db.shutdown()

	print("[+] TOUS LES TESTS DU DEFEAT SYSTEM SONT VERTS (100% SUCCÈS) !")
	quit(0)
