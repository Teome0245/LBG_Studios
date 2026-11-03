extends SceneTree
## creatures_scout_selftest.gd — Validation headless Faune, Métier Scout & Domptage Creature Handler (Ticket 4).

const HubCollisionScript := preload("res://scripts/hub_collision.gd")
const HubEconomyScript := preload("res://scripts/hub_economy.gd")
const HubSkillsScript := preload("res://scripts/hub_skills.gd")
const HubSurveyScript := preload("res://scripts/hub_survey.gd")
const HubSimScript := preload("res://scripts/hub_sim.gd")
const HubCreaturesScript := preload("res://scripts/hub_creatures.gd")


func _init() -> void:
	print("[*] Lancement du test Faune, Métier Scout & Creature Handler SWG Pre-CU (Ticket 4)...")

	var sim := HubSimScript.new()
	sim.reset()

	var economy := HubEconomyScript.new()
	economy.setup()

	var skills := HubSkillsScript.new()
	skills.setup(economy)

	var survey := HubSurveyScript.new()
	survey.setup(economy, skills)

	var creatures := HubCreaturesScript.new()
	creatures.setup(sim, economy, skills, survey, sim.collision)

	var player := "Scout_Test_%d" % (Time.get_ticks_msec() % 100000)

	# --------------------------------------------------------------------------
	# 1. Bestiaire & Indexation des créatures
	# --------------------------------------------------------------------------
	var bestiary := creatures.list_creatures()
	assert(bestiary.size() >= 8, "Le bestiaire doit contenir au moins 8 créatures de Lost Heaven")
	var c_chacal := creatures.get_creature_def("beast:chacal_dore")
	assert(not c_chacal.is_empty(), "Chacal doré doit être défini")
	assert(c_chacal.has("harvest"), "Chacal doré doit avoir une table de harvest")
	print("[+] PASS: Bestiaire indexé (%d espèces identifiées avec tables organiques)" % bestiary.size())

	# --------------------------------------------------------------------------
	# 2. Dépeçage Scout (Harvesting Viande / Peau / Os)
	# --------------------------------------------------------------------------
	# Création d'un cadavre de bête vaincue à l'est
	var corpse_entry := creatures.create_corpse("beast:chacal_dore", "Chacal Doré", Vector3(5985.0, 0.15, -1120.0), player, "zone:hunt_chacal")
	var cid := str(corpse_entry.get("corpse_id", ""))
	assert(not cid.is_empty(), "Cadavre de chacal doit avoir un identifiant généré")

	# Récolte de base (sans compétence spécifique) : Viande
	var harvest_res := creatures.harvest_corpse(player, cid, "meat")
	assert(bool(harvest_res.get("ok", false)) == true, "Dépeçage de viande sur cadavre frais doit réussir")
	assert(str(harvest_res.get("resource_id", "")) == "viande_chacal", "Ressource récoltée doit être viande_chacal")
	assert(int(harvest_res.get("qty", 0)) >= 4, "Quantité de base de viande >= 4")
	print("[+] PASS: Dépeçage initial : %d× %s (OQ=%d, Nutrition=%d)" % [
		int(harvest_res.get("qty", 0)),
		str(harvest_res.get("resource_name", "")),
		int(harvest_res.get("stats", {}).get("oq", 0)),
		int(harvest_res.get("stats", {}).get("nutrition", 0))
	])

	# Tentative de re-dépecer le cadavre déjà exploité -> doit échouer
	var reharvest := creatures.harvest_corpse(player, cid, "hide")
	assert(bool(reharvest.get("ok", false)) == false, "Un cadavre déjà dépecé ne peut être récolté une 2e fois")
	assert(str(reharvest.get("error", "")) == "corpse_already_harvested", "Erreur attendue: corpse_already_harvested")
	print("[+] PASS: Sécurité anti-duplication de récolte sur cadavre validée")

	# Cadavre 2 avec compétence Scout / Prélèvement Faunique rang 3 (multiplicateur x2)
	var corpse_entry2 := creatures.create_corpse("beast:chacal_dore", "Chacal Doré", Vector3(6000.0, 0.15, -1100.0), player, "zone:hunt_chacal")
	var cid2 := str(corpse_entry2.get("corpse_id", ""))
	# Apprentissage de la compétence faune (mode test bypass_xp)
	skills.learn_box(player, "prospecteur_novice", true)
	skills.learn_box(player, "prospecteur_faune_01", true)
	skills.learn_box(player, "prospecteur_faune_02", true)
	skills.learn_box(player, "prospecteur_faune_03", true)

	var harvest_scout := creatures.harvest_corpse(player, cid2, "hide")
	assert(bool(harvest_scout.get("ok", false)) == true, "Dépeçage qualifié Scout doit réussir")
	# Base 3 * 2.0 = 6
	assert(int(harvest_scout.get("qty", 0)) == 6, "Multiplicateur Scout Faune rang 3 doit donner 6 peaux")
	assert(int(harvest_scout.get("xp_gained", 0)) >= 50, "XP de prospection reçue >= 50")
	print("[+] PASS: Multiplicateur Scout Prélèvement Faunique validé : %d× Fourrures dorées (XP=%d)" % [
		int(harvest_scout.get("qty", 0)),
		int(harvest_scout.get("xp_gained", 0))
	])

	# --------------------------------------------------------------------------
	# 3. Camps de Survie (Scout Wilderness Camps)
	# --------------------------------------------------------------------------
	# Refus en centre-ville
	var camp_city := creatures.deploy_camp(player, 5100.0, -800.0, "abri_toile")
	assert(bool(camp_city.get("ok", false)) == false, "Camping en place publique intra-muros doit être interdit")
	assert(str(camp_city.get("error", "")) == "too_close_to_city", "Erreur attendue: too_close_to_city")

	# Pose autorisée dans les dunes
	var camp_wild := creatures.deploy_camp(player, 5600.0, -1300.0, "abri_toile")
	assert(bool(camp_wild.get("ok", false)) == true, "Pose de campement dans les dunes doit réussir")
	var camp_id := str(camp_wild.get("camp_id", ""))
	assert(not camp_id.is_empty(), "camp_id doit être généré")

	# Détection de zone de camp
	var camp_detected := creatures.get_active_camp_at(5605.0, -1305.0)
	assert(not camp_detected.is_empty(), "Le campement doit couvrir un rayon de 15m")
	assert(float(camp_detected.get("ham_regen_mult", 1.0)) == 1.5, "Le campement de base octroie 1.5x regen HAM")
	print("[+] PASS: Camp de survie %s déployé (R=%.0fm, Regen HAM=×%.1f)" % [
		camp_id,
		float(camp_wild.get("radius", 0.0)),
		float(camp_wild.get("ham_regen_mult", 0.0))
	])

	# --------------------------------------------------------------------------
	# 4. Camouflage d'odeur (Mask Scent)
	# --------------------------------------------------------------------------
	skills.learn_box(player, "prospecteur_piste_01", true)
	var mask := creatures.mask_scent(player)
	assert(bool(mask.get("ok", false)) == true, "Masquage d'odeur doit réussir")
	assert(creatures.is_scent_masked(player) == true, "Le joueur doit être sous effet camouflage d'odeur")
	print("[+] PASS: Camouflage d'odeur actif (durée=%.0fs)" % float(mask.get("duration_s", 0.0)))

	# --------------------------------------------------------------------------
	# 5. Creature Handler : Domptage, Familiers & Ordres
	# --------------------------------------------------------------------------
	# Création d'une créature sauvage juvénile dans sim.entities
	var wild_chiot_eid := "wild_chiot_test"
	sim.entities[wild_chiot_eid] = {
		"eid": wild_chiot_eid,
		"kind": "beast",
		"beast_id": "beast:chacal_dore_chiot",
		"name": "Chiot de Chacal Doré",
		"pos": Vector3(5105.0, 0.15, -805.0),
		"active": true
	}

	# Tentative de dompter un marcheur adulte (non domptable)
	var wild_marcheur_eid := "wild_marcheur_test"
	sim.entities[wild_marcheur_eid] = {
		"eid": wild_marcheur_eid,
		"kind": "beast",
		"beast_id": "beast:marcheur_dunes",
		"name": "Marcheur des Dunes",
		"pos": Vector3(5104.0, 0.15, -804.0),
		"active": true
	}
	var tame_fail := creatures.tame_creature(player, wild_marcheur_eid)
	assert(bool(tame_fail.get("ok", false)) == false, "Domptage d'un marcheur adulte géant doit être refusé")
	assert(str(tame_fail.get("error", "")) == "creature_not_tameable", "Erreur attendue: creature_not_tameable")

	# Domptage du chiot (avec force_success pour test unitaire déterministe)
	var tame_success := creatures.tame_creature(player, wild_chiot_eid, true)
	assert(bool(tame_success.get("ok", false)) == true, "Domptage du chiot de chacal doit réussir")
	var pet_info: Dictionary = tame_success.get("pet", {})
	var pet_id := str(pet_info.get("pet_id", ""))
	assert(not pet_id.is_empty(), "pet_id doit être généré")
	assert(not sim.entities.has(wild_chiot_eid), "La bête sauvage doit être retirée du monde après domptage")
	print("[+] PASS: Domptage Creature Handler réussi (%s apprivoisé -> %s)" % [
		str(pet_info.get("name", "")),
		pet_id
	])

	# Invoquer le familier sur le terrain (/call)
	var call_res := creatures.call_pet(player, pet_id, 5102.0, -802.0)
	assert(bool(call_res.get("ok", false)) == true, "Invocation du familier doit réussir")
	var pet_eid := str(call_res.get("eid", ""))
	assert(sim.entities.has(pet_eid), "L'entité familier doit apparaître dans sim.entities")
	assert(str(sim.entities[pet_eid].get("kind", "")) == "pet", "kind doit être 'pet'")

	# Ordres : /stay puis /follow
	var stay_res := creatures.command_pet(player, pet_id, "stay")
	assert(bool(stay_res.get("ok", false)) == true and str(stay_res.get("command", "")) == "stay")

	var follow_res := creatures.command_pet(player, pet_id, "follow")
	assert(bool(follow_res.get("ok", false)) == true and str(follow_res.get("command", "")) == "follow")

	# Nourrissage (/feed)
	var feed_res := creatures.feed_pet(player, pet_id, "viande_chacal")
	assert(bool(feed_res.get("ok", false)) == true, "Nourrir le familier doit réussir")
	assert(int(feed_res.get("loyalty", 0)) >= 85, "La loyauté doit augmenter")
	print("[+] PASS: Cycle de vie du familier (Invocation, Ordres /stay /follow, Nourrissage & Loyauté=%d) validé" % int(feed_res.get("loyalty", 0)))

	# Rangement du familier (/store)
	var store_res := creatures.store_pet(player, pet_id)
	assert(bool(store_res.get("ok", false)) == true, "Ranger le familier doit réussir")
	assert(not sim.entities.has(pet_eid), "L'entité du familier doit disparaître du monde après rangement")

	if sim.player_store != null and sim.player_store.has_method("shutdown"):
		sim.player_store.shutdown()
	if economy.db != null and economy.db.has_method("shutdown"):
		economy.db.shutdown()

	print("[+] Ticket 4 (Faune, Métier Scout & Creature Handler) : Tous les tests passent avec succès !")
	quit(0)
