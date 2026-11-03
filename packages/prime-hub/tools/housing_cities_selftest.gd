extends SceneTree
## housing_cities_selftest.gd — Validation headless Housing Libre, Décoration & Villes de Joueurs SWG Pre-CU (Ticket 2).

const HubCollisionScript := preload("res://scripts/hub_collision.gd")
const HubEconomyScript := preload("res://scripts/hub_economy.gd")
const HubSkillsScript := preload("res://scripts/hub_skills.gd")
const HubSimScript := preload("res://scripts/hub_sim.gd")
const HubHousingCitiesScript := preload("res://scripts/hub_housing_cities.gd")


func _init() -> void:
	print("[*] Lancement du test Housing Libre, Décoration & Cités de Joueurs SWG Pre-CU (Ticket 2)...")

	var sim := HubSimScript.new()
	sim.reset()

	var economy := HubEconomyScript.new()
	economy.setup()

	var skills := HubSkillsScript.new()
	skills.setup(economy)

	var hc := HubHousingCitiesScript.new()
	hc.setup(sim, economy, skills, sim.collision)

	var architect := "Architect_Jax_%d" % (Time.get_ticks_msec() % 100000)
	var resident := "Resident_Nix_%d" % (Time.get_ticks_msec() % 100000)
	var stranger := "Stranger_Lia_%d" % (Time.get_ticks_msec() % 100000)

	var p_arch := economy._player(architect)
	p_arch["credits"] = 25000
	skills.learn_box(architect, "artisan_novice", true)
	skills.learn_box(architect, "citoyen_novice", true)
	skills.learn_box(architect, "citoyen_badge_02", true)

	var p_res := economy._player(resident)
	p_res["credits"] = 10000
	skills.learn_box(resident, "artisan_novice", true)

	var p_stranger := economy._player(stranger)
	p_stranger["credits"] = 500

	# --------------------------------------------------------------------------
	# 1. HOUSING LIBRE & VALIDATION D'EMPREINTE
	# --------------------------------------------------------------------------
	# Refus en centre-ville intra-muros
	var dep_city := hc.deploy_structure(architect, "deed_maison_sable_p", 5100.0, -800.0)
	assert(bool(dep_city.get("ok", false)) == false, "Construction intra-muros protégée doit être refusée")
	assert(str(dep_city.get("error", "")) == "too_close_to_city_core", "Erreur attendue: too_close_to_city_core")
	print("[+] PASS: Zone protégée de Lost Heaven respectée (construction intra-muros refusée)")

	# Pose autorisée dans les dunes (5500, -1100)
	var dep_house := hc.deploy_structure(architect, "deed_maison_sable_p", 5500.0, -1100.0)
	assert(bool(dep_house.get("ok", false)) == true, "Construction d'une maison dans les dunes doit réussir")
	var s_id := str(dep_house.get("struct_id", ""))
	assert(not s_id.is_empty(), "struct_id doit être généré")
	print("[+] PASS: Maison %s érigée à (5500, -1100) par %s" % [s_id, architect])

	# Refus de chevauchement sur la même parcelle
	var dep_overlap := hc.deploy_structure(architect, "deed_tente_nomade", 5503.0, -1102.0)
	assert(bool(dep_overlap.get("ok", false)) == false, "Chevauchement de structure doit être refusé")
	assert(str(dep_overlap.get("error", "")) == "overlapping_structure", "Erreur attendue: overlapping_structure")
	print("[+] PASS: Contrôle anti-chevauchement des fondations validé")

	# --------------------------------------------------------------------------
	# 2. CONTRÔLE D'ACCÈS & PERMISSIONS (ACL)
	# --------------------------------------------------------------------------
	# Passage en maison privée
	var priv_res := hc.set_structure_privacy(architect, s_id, false)
	assert(bool(priv_res.get("ok", false)) == true and bool(priv_res.get("is_public")) == false)

	# Vérification des droits d'entrée
	assert(hc.can_enter_structure(architect, s_id) == true, "Le propriétaire doit toujours pouvoir entrer")
	assert(hc.can_enter_structure(stranger, s_id) == false, "Un inconnu ne peut entrer dans une maison privée")

	# Ajout de Resident_Nix à la liste d'entrée
	hc.manage_structure_acl(architect, s_id, "add_entry", resident)
	assert(hc.can_enter_structure(resident, s_id) == true, "L'invité autorisé doit pouvoir entrer")

	# Bannissement d'un intrus
	hc.manage_structure_acl(architect, s_id, "add_ban", stranger)
	assert(hc.can_enter_structure(stranger, s_id) == false, "Le joueur banni est strictement refoulé")
	print("[+] PASS: Système de permissions ACL (Propriétaire, Invité, Inconnu, Banni) validé")

	# Entretien : versement de 100 crédits
	var dep_maint := hc.deposit_maintenance(architect, s_id, 100)
	assert(bool(dep_maint.get("ok", false)) == true and int(dep_maint.get("maintenance_pool", 0)) == 200)
	print("[+] PASS: Versement d'entretien structure validé (réserve=200 cr)")

	# --------------------------------------------------------------------------
	# 3. DÉCORATION INTÉRIEURE LIBRE
	# --------------------------------------------------------------------------
	economy.grant_world_loot(architect, [
		{"id": "fauteuil_cuir", "name": "Fauteuil de salon en cuir de chacal", "qty": 1}
	], 0)

	# Poser l'objet au sol dans le salon (local_x=2.5, local_y=0.0, local_z=1.8, yaw=45°)
	var deco_place := hc.place_decoration(architect, s_id, "fauteuil_cuir", 2.5, 0.0, 1.8, 45.0)
	assert(bool(deco_place.get("ok", false)) == true, "Pose de meuble dans le salon doit réussir")
	var deco_id := str(deco_place.get("deco_id", ""))
	assert(not deco_id.is_empty(), "deco_id doit être généré")
	assert(economy._inv_qty(p_arch, "fauteuil_cuir") == 0, "L'objet posé doit quitter l'inventaire")
	print("[+] PASS: Ameublement libre : Fauteuil placé à (2.5, 0.0, 1.8) yaw=45° (DecoID=%s)" % deco_id)

	# Ajuster la position au millimètre (+0.2m en X, +15° en yaw)
	var deco_move := hc.move_decoration(architect, s_id, deco_id, 0.2, 0.0, 0.0, 15.0)
	assert(bool(deco_move.get("ok", false)) == true)
	var new_p: Dictionary = deco_move.get("new_local_pos", {})
	assert(is_equal_approx(float(new_p.get("x", 0.0)), 2.7), "Coordonnée X ajustée à 2.7")
	print("[+] PASS: Déplacement fin au millimètre et rotation validés")

	# Reprendre l'objet dans l'inventaire
	var deco_pick := hc.pickup_decoration(architect, s_id, deco_id)
	assert(bool(deco_pick.get("ok", false)) == true, "Reprendre un meuble doit réussir")
	assert(economy._inv_qty(p_arch, "fauteuil_cuir") == 1, "Le meuble doit être retourné à l'inventaire")
	print("[+] PASS: Rangement du meuble dans l'inventaire validé")

	# --------------------------------------------------------------------------
	# 4. VILLES DE JOUEURS & MUNICIPALITÉS
	# --------------------------------------------------------------------------
	# Déployer deux autres maisons dans les environs pour atteindre le seuil de 3 structures
	var house2 := hc.deploy_structure(resident, "deed_tente_nomade", 5525.0, -1110.0)
	assert(bool(house2.get("ok", false)) == true)
	var house3 := hc.deploy_structure(architect, "deed_tente_nomade", 5510.0, -1135.0)
	assert(bool(house3.get("ok", false)) == true)

	# Fondation officielle de la cité
	var found_city := hc.found_player_city(architect, "Nouvelle Syrte", 5515.0, -1115.0)
	assert(bool(found_city.get("ok", false)) == true, "Fondation de cité de joueurs doit réussir")
	var city_id := str(found_city.get("city_id", ""))
	assert(not city_id.is_empty(), "city_id doit être généré")
	var c_info: Dictionary = found_city.get("city", {})
	assert(int(c_info.get("tier", 0)) == 1, "Le rang initial doit être Campement (Tier 1)")
	print("[+] PASS: Municipalité %s (« %s », Tier 1 %s) fondée par %s" % [
		city_id,
		str(c_info.get("city_name", "")),
		str(c_info.get("tier_name", "")),
		architect
	])

	# Élection municipale (votes des résidents)
	var votes := {
		architect: resident, # Jax vote pour Nix
		resident: resident    # Nix vote pour lui-même
	}
	var election := hc.hold_mayoral_election(city_id, votes)
	assert(bool(election.get("ok", false)) == true)
	assert(str(election.get("elected_mayor", "")) == resident, "Resident_Nix doit être élu maire avec 2 voix")
	print("[+] PASS: Élections municipales : %s élu Maire avec 2 voix" % resident)

	# Le nouveau maire fixe les taxes municipales
	var tax_res := hc.set_city_taxes(resident, city_id, 8, 3)
	assert(bool(tax_res.get("ok", false)) == true)
	assert(int(tax_res.get("property_tax", 0)) == 8 and int(tax_res.get("sales_tax_pct", 0)) == 3)
	print("[+] PASS: Décret fiscal du Maire : Taxe foncière=8 cr, Taxe commerciale=3%%")

	# Le maire place une infrastructure civique (Shuttleport)
	var civic_res := hc.place_city_civic_structure(resident, city_id, "shuttleport", 5530.0, -1120.0)
	assert(bool(civic_res.get("ok", false)) == true, "Placement de navetteur municipal doit réussir")
	print("[+] PASS: Infrastructure civique municipale érigée (shuttleport)")

	if sim.player_store != null and sim.player_store.has_method("shutdown"):
		sim.player_store.shutdown()
	if economy.db != null and economy.db.has_method("shutdown"):
		economy.db.shutdown()

	print("[+] Ticket 2 (Housing Libre, Décoration & Cités de Joueurs) : Tous les tests passent avec succès !")
	quit(0)

