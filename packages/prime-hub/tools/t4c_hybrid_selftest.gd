extends SceneTree
## t4c_hybrid_selftest.gd — Validation Headless de la Fusion T4C & SWG
## Vérifie :
## 1. Dérivation des pools HAM (Health/Action/Mind) depuis les 5 stats T4C
## 2. Prérequis d'équipement stricts (armes/armures)
## 3. Grimoire de Sorts (coût en Mind, conditions d'Intelligence, Sagesse et Karma)
## 4. Renaissance Séraphin (Ailes & attribution de stats bonus)

const HubEconomyScript := preload("res://scripts/hub_economy.gd")
const HubSkillsScript := preload("res://scripts/hub_skills.gd")
const HubHamMedicalScript := preload("res://scripts/hub_ham_medical.gd")
const HubT4cSystemScript := preload("res://scripts/hub_t4c_system.gd")


func _init() -> void:
	print("[*] Lancement du test Fusion T4C & SWG (Prime Hub)...")

	var economy := HubEconomyScript.new()
	economy.setup()

	var skills := HubSkillsScript.new()
	skills.setup(economy)

	var ham := HubHamMedicalScript.new()
	ham.setup(economy, skills)

	var t4c := HubT4cSystemScript.new()
	t4c.setup(economy, skills, ham)

	var player := "Paladin_T4C_%d" % (Time.get_ticks_msec() % 100000)

	# 1. Calcul des dérivés HAM avec stats de base (20 partout)
	var derived: Dictionary = t4c.calculate_ham_derived_pools(player)
	assert(derived["max_health"] == 1000 + (20 * 10) + (20 * 18), "Health dérivée incorrecte")
	assert(derived["max_action"] == 1000 + (20 * 15) + (20 * 8), "Action dérivée incorrecte")
	assert(derived["max_mind"] == 1000 + (20 * 16) + (20 * 16), "Mind dérivé incorrect")
	print("[+] PASS: 1. Dérivation des jauges HAM depuis stats T4C (Health/Action/Mind) validée")

	# 2. Test prérequis équipement : Épée bâtarde (40 FOR, 25 END)
	var check_sword_fail := t4c.can_equip_item(player, "epee_batarde_acier")
	assert(check_sword_fail["can_equip"] == false, "Épée bâtarde ne doit pas être équipable avec 20 FOR")
	assert(check_sword_fail["missing"].has("strength"), "Manque de Force attendu")
	assert(check_sword_fail["missing"].has("endurance"), "Manque d'Endurance attendu")

	# Allocation des points pour remplir les prérequis
	# On alloue +20 en Force (20 -> 40) et +5 en Endurance (20 -> 25)
	# On simule un gain de points d'XP
	var p: Dictionary = economy._player(player)
	p["t4c_attributes"]["unallocated_points"] = 30
	skills.allocate_t4c_attribute(player, "strength", 20)
	skills.allocate_t4c_attribute(player, "endurance", 5)

	var check_sword_ok := t4c.can_equip_item(player, "epee_batarde_acier")
	assert(check_sword_ok["can_equip"] == true, "Épée bâtarde doit être équipable après allocation")
	print("[+] PASS: 2. Prérequis stricts d'équipement T4C (Force/Endurance) validés")

	# 3. Grimoire de sorts & Conditions
	# Le joueur a FOR:40, END:25, DEX:20, INT:20, SAG:20, Karma:0
	var book := t4c.get_spellbook(player)
	assert(book["ok"] == true, "Le grimoire doit répondre")
	var spells: Array = book["spells"]
	assert(spells.size() >= 5, "Au moins 5 sorts catalogués")

	# Étincelle demande 20 INT -> doit être lançable
	var cast_spark := t4c.cast_spell(player, "etincelle")
	assert(cast_spark["ok"] == true, "Lancement Étincelle doit réussir")
	assert(cast_spark["mind_consumed"] == 30, "Coût 30 Mind attendu")

	# Prière Séraphin demande 50 SAG et Karma >= 200 -> doit échouer
	var cast_seraph_fail := t4c.cast_spell(player, "priere_seraphin")
	assert(cast_seraph_fail["ok"] == false, "Prière Séraphin doit échouer sans Sagesse et Karma")

	# Ajustement Karma et Sagesse pour devenir Séraphin
	skills.adjust_karma(player, 350, "Bénédiction du Temple")
	p["t4c_attributes"]["unallocated_points"] = 40
	skills.allocate_t4c_attribute(player, "wisdom", 30) # 20 -> 50

	var cast_seraph_ok := t4c.cast_spell(player, "priere_seraphin")
	assert(cast_seraph_ok["ok"] == true, "Prière Séraphin doit réussir avec 50 SAG et 350 Karma")
	assert(cast_seraph_ok["effect_type"] == "heal", "Effet de soin attendu")
	print("[+] PASS: 3. Grimoire, coûts en Mind et sorts conditionnels (Karma/Stats) validés")

	# 4. Renaissance Séraphin
	var seraph_res := t4c.renaissance_seraph(player)
	assert(seraph_res["ok"] == true, "Renaissance Séraphin doit réussir")
	assert(seraph_res["wing_type"] == "céleste", "Ailes célestes attendues pour Karma positif")
	assert(seraph_res["bonus_points"] == 25, "25 points bonus attendus")
	print("[+] PASS: 4. Cérémonie de Renaissance T4C (Ailes & Bonus Stats) validée")

	if economy.db != null and economy.db.has_method("shutdown"):
		economy.db.shutdown()

	print("[+] TOUS LES TESTS FUSION T4C / SWG (SYSTEME & GRIMOIRE) SONT VALIDÉS AVEC SUCCÈS !")
	quit(0)
