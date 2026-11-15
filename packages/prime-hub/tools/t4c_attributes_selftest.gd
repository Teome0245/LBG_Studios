extends SceneTree
## t4c_attributes_selftest.gd — Validation headless des Attributs Libres (FOR/DEX/END/INT/SAG)
## et du Système de Karma / Alignement (Inspiré de La 4ème Prophétie / T4C).

const HubEconomyScript := preload("res://scripts/hub_economy.gd")
const HubSkillsScript := preload("res://scripts/hub_skills.gd")


func _init() -> void:
	print("[*] Lancement du test Attributs Libres & Karma T4C (Prime Hub)...")

	var economy := HubEconomyScript.new()
	economy.setup()

	var skills := HubSkillsScript.new()
	skills.setup(economy)

	var player := "TestHeroT4C_%d" % (Time.get_ticks_msec() % 100000)

	# 1. Vérification des stats initiales par défaut
	var atts: Dictionary = skills.get_t4c_attributes(player)
	assert(atts.has("strength") and int(atts["strength"]) == 20, "Force initiale doit être de 20")
	assert(atts.has("dexterity") and int(atts["dexterity"]) == 20, "Dextérité initiale doit être de 20")
	assert(atts.has("endurance") and int(atts["endurance"]) == 20, "Endurance initiale doit être de 20")
	assert(atts.has("intelligence") and int(atts["intelligence"]) == 20, "Intelligence initiale doit être de 20")
	assert(atts.has("wisdom") and int(atts["wisdom"]) == 20, "Sagesse initiale doit être de 20")
	assert(int(atts.get("unallocated_points", 0)) == 15, "15 points non alloués attendus")
	assert(int(atts.get("karma", -999)) == 0, "Karma initial neutre à 0")
	assert(str(atts.get("karma_title", "")) == "Citoyen Neutre", "Titre karma initial doit être Citoyen Neutre")
	print("[+] PASS: Initialisation des 5 attributs T4C et points non alloués (15 pts) validée")

	# 2. Refus d'allocation invalide (trop de points ou mauvaise stat)
	var bad_alloc := skills.allocate_t4c_attribute(player, "strength", 20)
	assert(bool(bad_alloc.get("ok", false)) == false, "Allocation de 20 pts avec seulement 15 dispo doit échouer")
	assert(str(bad_alloc.get("error", "")) == "insufficient_unallocated_points", "Erreur attendue: insufficient_unallocated_points")

	var bad_stat := skills.allocate_t4c_attribute(player, "magic_power", 5)
	assert(bool(bad_stat.get("ok", false)) == false, "Attribut inconnu doit échouer")
	print("[+] PASS: Garde-fous d'allocation d'attributs validés")

	# 3. Allocation valide (+5 en force, +10 en endurance)
	var ok_str := skills.allocate_t4c_attribute(player, "strength", 5)
	assert(bool(ok_str.get("ok", false)) == true, "Allocation de 5 pts de force doit réussir")
	assert(int(ok_str.get("new_value", 0)) == 25, "Force doit passer à 25")
	assert(int(ok_str.get("remaining_unallocated", -1)) == 10, "Reste 10 pts non alloués")

	var ok_end := skills.allocate_t4c_attribute(player, "endurance", 10)
	assert(bool(ok_end.get("ok", false)) == true, "Allocation de 10 pts d'endurance doit réussir")
	assert(int(ok_end.get("new_value", 0)) == 30, "Endurance doit passer à 30")
	assert(int(ok_end.get("remaining_unallocated", -1)) == 0, "Reste 0 pts non alloués")
	print("[+] PASS: Attribution effective des caractéristiques (+5 FOR -> 25, +10 END -> 30) validée")

	# 4. Évolution dynamique du Karma (Bien / Mal)
	var k_bien := skills.adjust_karma(player, 250, "Sauvetage de caravane dans les dunes")
	assert(int(k_bien.get("new_karma", 0)) == 250, "Karma doit être 250")
	assert(str(k_bien.get("karma_title", "")) == "Protecteur Bienveillant", "Titre attendu: Protecteur Bienveillant")

	var k_seraph := skills.adjust_karma(player, 400, "Purification de l'oasis sacrée")
	assert(int(k_seraph.get("new_karma", 0)) == 650, "Karma doit être 650")
	assert(str(k_seraph.get("karma_title", "")) == "Séraphin de l'Ordre", "Titre attendu: Séraphin de l'Ordre")

	var k_mal := skills.adjust_karma(player, -1200, "Raid sur un convoi pacifique et trahison")
	assert(int(k_mal.get("new_karma", 0)) == -550, "Karma doit être -550")
	assert(str(k_mal.get("karma_title", "")) == "Hors-la-loi Notifié", "Titre attendu: Hors-la-loi Notifié")

	var k_terreur := skills.adjust_karma(player, -300, "Destruction de ferme d'humidité")
	assert(int(k_terreur.get("new_karma", 0)) == -850, "Karma doit être -850")
	assert(str(k_terreur.get("karma_title", "")) == "Terreur des Sables", "Titre attendu: Terreur des Sables")
	print("[+] PASS: Échelle d'alignement et Karma dynamique (-1000 à +1000) validés")

	# 5. Présence dans le snapshot global
	var snap := skills.player_tree_snapshot(player)
	assert(snap.has("t4c_attributes"), "Snapshot doit contenir t4c_attributes")
	var snap_atts: Dictionary = snap["t4c_attributes"]
	assert(int(snap_atts.get("strength", 0)) == 25, "Snapshot doit refléter la force à 25")
	assert(str(snap_atts.get("karma_title", "")) == "Terreur des Sables", "Snapshot doit refléter le titre Terreur des Sables")
	print("[+] PASS: Intégration complète dans le snapshot de compétences validée")

	if economy.db != null and economy.db.has_method("shutdown"):
		economy.db.shutdown()

	print("[+] TOUS LES TESTS ATTRIBUTS & KARMA T4C ONT RÉUSSI AVEC SUCCÈS !")
	quit(0)
