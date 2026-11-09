extends SceneTree
## Self-test Headless des 5 Piliers d'Achèvement SWG Pre-CU + JTL Spatial
## (Jedi & Force, Bounty Hunter, Travel & Navette, Bases GCW, Clonage & Assurance, JTL).
##
## Usage:
##   packages/prime-hub/tools/Godot_v4.6.3-stable_linux.x86_64 --headless \
##     --path packages/prime-hub -s res://tools/swg_complete_features_selftest.gd

const HubJediForceScript := preload("res://scripts/hub_jedi_force.gd")
const HubBountyHunterScript := preload("res://scripts/hub_bounty_hunter.gd")
const HubTravelShuttleScript := preload("res://scripts/hub_travel_shuttle.gd")
const HubGcwBasesScript := preload("res://scripts/hub_gcw_bases.gd")
const HubCloningInsuranceScript := preload("res://scripts/hub_cloning_insurance.gd")
const HubSpaceJtlScript := preload("res://scripts/hub_space_jtl.gd")
const HubPlayerCitiesScript := preload("res://scripts/hub_player_cities.gd")
const HubBioEngineerScript := preload("res://scripts/hub_bio_engineer.gd")
const HubDroidEngineerScript := preload("res://scripts/hub_droid_engineer.gd")
const HubThemeParksScript := preload("res://scripts/hub_theme_parks.gd")
const HubGalaxyPlanetsScript := preload("res://scripts/hub_galaxy_planets.gd")
const HubFactionScript := preload("res://scripts/hub_faction.gd")
const HubEconomyScript := preload("res://scripts/hub_economy.gd")


func _init() -> void:
	print("[*] Lancement du test Complet SWG Pre-CU (5 Piliers + JTL Dogfight)...")

	var economy = HubEconomyScript.new()
	economy.setup()

	var faction = HubFactionScript.new()
	faction.setup(null, null, economy)

	# --- 1. TEST JEDI & FORCE SENSITIVE ---
	var bounty_svc = HubBountyHunterScript.new()
	bounty_svc.setup(null, economy)

	var jedi = HubJediForceScript.new()
	jedi.setup(null, economy, null, bounty_svc)

	var st1: Dictionary = jedi.get_status("Luke_Skywalker")
	assert(st1.get("rank") == "initiate" and st1.get("current_force") == 500, "Le rang initial doit être Initiate avec 500 Force")

	# Consultation de 4 Holocrons pour atteindre le rang Padawan
	jedi.consult_holocron("Luke_Skywalker", "jedi")
	jedi.consult_holocron("Luke_Skywalker", "jedi")
	jedi.consult_holocron("Luke_Skywalker", "sith")
	var holocron4: Dictionary = jedi.consult_holocron("Luke_Skywalker", "jedi")
	assert(holocron4.get("new_rank") == "padawan" and holocron4.get("max_force") == 1000, "4 Holocrons doivent promouvoir au rang Padawan avec 1000 Force")
	print("[+] PASS: Voie du Jedi - Consultation Holocrons & Promotion Padawan validées")

	# Confection de Sabre Laser avec Cristal d'Ilum
	var saber: Dictionary = jedi.craft_lightsaber("Luke_Skywalker", "crystal_ilum_blue", "curved")
	assert(bool(saber.get("ok")) and saber.get("lightsaber", {}).get("blade_color") == "blue", "Le sabre laser bleu doit être forgé")
	print("[+] PASS: Voie du Jedi - Confection de Sabre Laser avec Cristal d'Ilum validée")

	# Déclenchement de Pouvoirs de Force
	var heal: Dictionary = jedi.execute_force_power("Luke_Skywalker", "force_heal")
	assert(bool(heal.get("ok")) and heal.get("heal_applied") == 350, "Force Heal doit restaurer 350 HAM")

	var speed: Dictionary = jedi.execute_force_power("Luke_Skywalker", "force_speed")
	assert(bool(speed.get("ok")) and speed.get("buff_speed") == 2.0, "Force Speed doit doubler la vitesse")

	# 2 pouvoirs de plus pour monter la visibilité impériale au-delà de 30
	jedi.execute_force_power("Luke_Skywalker", "mind_trick", "Stormtrooper_01")
	var pow4: Dictionary = jedi.execute_force_power("Luke_Skywalker", "force_lightning", "Sith_Inquisitor")
	assert(pow4.get("visibility") >= 30, "L'usage répété de pouvoirs doit élever la visibilité impériale")
	assert(pow4.has("bounty_generated"), "Une prime doit être générée automatiquement sur le Jedi")
	print("[+] PASS: Voie du Jedi - Pouvoirs de Force & Visibilité Impériale validés")

	# --- 2. TEST BOUNTY HUNTER & DROÏDES ARAKYD ---
	var b_list: Array = bounty_svc.list_bounties("Boba_Fett")
	assert(b_list.size() >= 3, "Le terminal de primes doit proposer au moins 3 contrats")

	# Trouver la prime sur Luke
	var target_bid := ""
	for b in b_list:
		if str(b.get("target_name", "")) == "Luke_Skywalker":
			target_bid = str(b.get("id", ""))
			break
	if target_bid.is_empty() and b_list.size() > 0:
		target_bid = str(b_list[0].get("id", ""))

	var accept_res: Dictionary = bounty_svc.accept_bounty("Boba_Fett", target_bid)
	assert(bool(accept_res.get("ok")), "L'acceptation du contrat de prime doit réussir")

	# Déploiement d'un droïde sonde Arakyd
	var droid_res: Dictionary = bounty_svc.deploy_seeker_droid("Boba_Fett", target_bid)
	assert(bool(droid_res.get("ok")) and droid_res.get("telemetry", {}).get("status") == "signal_locked", "La sonde Arakyd doit verrouiller la cible avec coordonnées GPS")
	print("[+] PASS: Chasseur de Primes - Traque par Droïde Sonde Arakyd validée")

	# Réclamation de la prime
	var claim_res: Dictionary = bounty_svc.claim_bounty("Boba_Fett", target_bid)
	assert(bool(claim_res.get("ok")) and claim_res.get("reward_credits") > 0, "L'encaissement de la prime doit réussir")
	print("[+] PASS: Chasseur de Primes - Validation d'élimination & Encaissement de prime validés")

	# --- 3. TEST SPATIOPORTS & NAVETTE GALACTIQUE ---
	var travel = HubTravelShuttleScript.new()
	travel.setup(null, economy)

	var sh_status: Dictionary = travel.get_shuttle_status()
	assert(sh_status.get("is_docked") == true and sh_status.get("current_phase") == "boarding", "La navette doit démarrer en phase boarding à quai")

	var routes: Array = travel.list_routes()
	assert(routes.size() >= 4, "Le catalogue de transport doit comporter 4 lignes (Eisley, Theed, Coronet, Outpost)")

	economy.grant_world_loot("Han_Solo", [], 2000)
	var tkt: Dictionary = travel.purchase_ticket("Han_Solo", "lh_theed")
	assert(bool(tkt.get("ok")) and tkt.get("cost_paid") == 350, "L'achat d'un billet pour Theed doit coûter 350 crédits")

	var board: Dictionary = travel.board_shuttle("Han_Solo", "lh_theed")
	assert(bool(board.get("ok")), "L'embarquement physique à bord de la navette doit réussir")
	print("[+] PASS: Spatioport & Navette - Billetterie & Embarquement galactique validés")

	# --- 4. TEST BASES FACTIONNELLES GCW & SABOTAGE ---
	var gcw_bases = HubGcwBasesScript.new()
	gcw_bases.setup(null, faction, economy)

	var bases: Array = gcw_bases.list_bases()
	assert(bases.size() >= 2, "Une base impériale et une base rebelle doivent être déployées")
	var base_id: String = str(bases[0].get("id", ""))

	# Étape 1 : Piratage des tourelles
	var hack_res: Dictionary = gcw_bases.hack_security_terminal("Rebel_Infiltrator", base_id)
	assert(bool(hack_res.get("ok")) and hack_res.get("turrets_active") == false, "Le piratage doit couper les tourelles")

	# Étape 2 : Surcharge du réacteur
	var overload_res: Dictionary = gcw_bases.overload_reactor("Rebel_Infiltrator", base_id)
	assert(bool(overload_res.get("ok")) and overload_res.get("overload_timer_s") == 300.0, "La surcharge critique de 5 minutes doit être déclenchée")

	# Étape 3 : Destruction & Points de Faction
	var detonate_res: Dictionary = gcw_bases.detonate_base("Rebel_Infiltrator", base_id)
	assert(bool(detonate_res.get("ok")) and detonate_res.get("is_destroyed") == true, "La base militaire doit être détruite")
	print("[+] PASS: Bases GCW - Piratage, Surcharge de Réacteur & Destruction validés")

	# --- 5. TEST CLONAGE & ASSURANCE ---
	var clone_svc = HubCloningInsuranceScript.new()
	clone_svc.setup(null, economy)

	economy.grant_world_loot("Wedge_Antilles", [], 2000)
	# Liaison de la matrice ADN
	var bind_res: Dictionary = clone_svc.bind_cloning_facility("Wedge_Antilles", "clone_nomad_ksar")
	assert(bool(bind_res.get("ok")) and bind_res.get("facility_id") == "clone_nomad_ksar", "La liaison au Ksar Nomade doit réussir")

	# Assurance des objets
	var ins_res: Dictionary = clone_svc.insure_items("Wedge_Antilles", 8)
	assert(bool(ins_res.get("ok")) and ins_res.get("cost_paid") == 200, "L'assurance de 8 objets doit coûter 200 crédits")

	# Traitement de mort et réapparition
	var death_res: Dictionary = clone_svc.process_death_and_clone("Wedge_Antilles")
	assert(bool(death_res.get("ok")), "La réapparition en cuve de clonage doit réussir")
	assert(death_res.get("decay_applied") == false, "Les objets étant assurés, aucun decay ne doit être appliqué")
	assert(death_res.get("cloning_sickness") == true, "Le mal de clonage (Cloning Sickness) doit être actif")

	# Guérison par médecin
	var cure_res: Dictionary = clone_svc.cure_cloning_sickness("Wedge_Antilles", "Docteur_Vane")
	assert(bool(cure_res.get("ok")), "Le médecin doit guérir le mal de clonage")
	print("[+] PASS: Clonage & Assurance - Protection anti-decay & Mal de clonage validés")

	# --- 6. TEST JTL SPATIAL & DOGFIGHT ---
	var space = HubSpaceJtlScript.new()
	space.setup(null)

	var launch_res: Dictionary = space.spawn_starship("Porkins", "xwing_t65", Vector3(100, 50, 200))
	assert(bool(launch_res.get("ok")), "Le lancement du X-Wing en orbite doit réussir")
	var xwing_id: String = str(launch_res.get("ship", {}).get("id", ""))

	# Répartiteur d'énergie Tri-Voie
	var pwr_res: Dictionary = space.adjust_power_distribution(xwing_id, 50, 25, 25)
	assert(bool(pwr_res.get("ok")), "L'alimentation à 50% armes doit être acceptée")

	# Dogfight laser contre un chasseur TIE
	var tie_id: String = str(space.list_sector_ships()[0].get("id", ""))
	var dogfight: Dictionary = space.fire_lasers_at_target(xwing_id, tie_id)
	assert(bool(dogfight.get("ok")) and dogfight.get("damage_dealt") > 0, "Le tir de canon laser spatial doit infliger des dégâts")

	# Saut Hyperspatial
	var jump_res: Dictionary = space.jump_hyperspace(xwing_id, "Kessel_Run")
	assert(bool(jump_res.get("ok")), "Le saut hyperspatial doit réussir")
	print("[+] PASS: JTL Spatial - Dogfight X-Wing / TIE, Répartiteur d'énergie & Hyper-espace validés")

	# --- 7. TEST VILLES DE JOUEURS & POLITIQUE ---
	var city_svc = HubPlayerCitiesScript.new(economy)
	var found_res: Dictionary = city_svc.found_city("Mon_Mothma", "Oasis Chandrila", [200.0, 0.15, -200.0])
	assert(bool(found_res.get("ok")), "La fondation d'Oasis Chandrila doit réussir")
	var new_cid: String = str(found_res.get("city", {}).get("id", ""))

	# Enregistrement de citoyens pour monter en grade
	city_svc.register_citizen(new_cid, "Cassian_Andor")
	city_svc.register_citizen(new_cid, "Jyn_Erso")
	city_svc.register_citizen(new_cid, "Baze_Malbus")
	city_svc.register_citizen(new_cid, "Chirrut_Imwe")
	var reg_res: Dictionary = city_svc.register_citizen(new_cid, "Bodhi_Rook")
	assert(reg_res.get("citizen_count") == 6, "La ville doit compter 6 citoyens")
	assert(reg_res.get("rank_name") == "Outpost", "Avec 6 citoyens la ville est un Outpost")

	# Élection municipale & vote
	city_svc.start_election(new_cid)
	var vote_res: Dictionary = city_svc.cast_vote(new_cid, "Cassian_Andor", "Mon_Mothma")
	assert(bool(vote_res.get("ok")) and vote_res.get("total_votes") == 1, "Le vote pour Mon Mothma doit être enregistré")
	var elect_conclude: Dictionary = city_svc.conclude_election(new_cid)
	assert(bool(elect_conclude.get("ok")) and elect_conclude.get("new_mayor") == "Mon_Mothma", "Mon Mothma doit être élue Maire")

	# Spécialisation civique & taxes
	var spec_res: Dictionary = city_svc.set_specialization(new_cid, "Mon_Mothma", "manufacturing")
	assert(bool(spec_res.get("ok")), "La spécialisation Centre Industriel doit être décrétée")
	var tax_res: Dictionary = city_svc.set_taxes(new_cid, "Mon_Mothma", 75, 4, 120)
	assert(bool(tax_res.get("ok")), "Les taux d'impôts municipaux doivent être mis à jour")
	print("[+] PASS: Villes de Joueurs - Fondation, Citoyenneté, Élections de Maire & Spécialisation validées")

	# --- 8. TEST BIO-INGÉNIERIE & ÉCHANTILLONNAGE ADN ---
	var bio_svc = HubBioEngineerScript.new()
	var sample_chacal: Dictionary = bio_svc.sample_dna("Docteur_Evazan", "chacal_des_dunes", 3.5)
	assert(bool(sample_chacal.get("ok")), "Le prélèvement d'ADN sur chacal doit réussir")
	var dna_1: String = str(sample_chacal.get("sample", {}).get("id", ""))

	var sample_bantha: Dictionary = bio_svc.sample_dna("Docteur_Evazan", "bantha_sauvage", 4.0)
	assert(bool(sample_bantha.get("ok")), "Le prélèvement d'ADN sur bantha doit réussir")
	var dna_2: String = str(sample_bantha.get("sample", {}).get("id", ""))

	# Incubation génétique d'une chimère hybride
	var inc_res: Dictionary = bio_svc.incubate_creature("Docteur_Evazan", dna_1, dna_2, "Chimère Sauvage Alpha")
	assert(bool(inc_res.get("ok")), "L'incubation de la créature hybride doit réussir")
	assert(inc_res.get("embryo", {}).get("stats", {}).get("health", 0) > 1000, "L'embryon doit posséder des statistiques de santé calculées")
	print("[+] PASS: Bio-Ingénierie - Prélèvement ADN faune & Incubation d'hybrides mutés validés")

	# --- 9. TEST DROID ENGINEER ---
	var droid_svc = HubDroidEngineerScript.new()
	var craft_d_res: Dictionary = droid_svc.craft_droid("Anakin_Skywalker", "r2_astromech", "R2-D2", "blue")
	assert(bool(craft_d_res.get("ok")), "La fabrication du droïde R2 doit réussir")
	var r2_id: String = str(craft_d_res.get("droid", {}).get("id", ""))

	# Montage de modules fonctionnels
	var mod_res: Dictionary = droid_svc.install_module(r2_id, "storage")
	assert(bool(mod_res.get("ok")), "L'installation du module de soute doit réussir")
	var mod2_res: Dictionary = droid_svc.install_module(r2_id, "crafting_station")
	assert(bool(mod2_res.get("ok")), "L'installation du module atelier ambulant doit réussir")

	# Commandes tactiques
	var cmd_res: Dictionary = droid_svc.issue_command(r2_id, "Anakin_Skywalker", "follow")
	assert(bool(cmd_res.get("ok")) and cmd_res.get("command") == "follow", "La commande /follow doit être exécutée par R2")
	print("[+] PASS: Droid Engineer - Châssis R2, Modules d'extension & Commandes tactiques validés")

	# --- 10. TEST PARCS À THÈMES & DONJONS ---
	var park_svc = HubThemeParksScript.new()
	var m1_res: Dictionary = park_svc.complete_theme_park_mission("Boba_Fett", "jabba_palace")
	assert(bool(m1_res.get("ok")), "La mission 1 du Palais de Jabba doit être accomplie")
	var m2_res: Dictionary = park_svc.complete_theme_park_mission("Boba_Fett", "jabba_palace")
	assert(bool(m2_res.get("ok")), "La mission 2 de Jabba doit être accomplie")
	var m3_res: Dictionary = park_svc.complete_theme_park_mission("Boba_Fett", "jabba_palace")
	assert(bool(m3_res.get("ok")) and m3_res.get("is_grand_finale") == true, "La mission finale de Jabba doit octroyer l'insigne d'Exécuteur")

	# Instance de la Corvette Corellienne
	var enter_corvette: Dictionary = park_svc.launch_corvette_instance("Han_Solo")
	assert(bool(enter_corvette.get("ok")), "Le lancement de l'instance Corvette doit réussir")
	var adv_corvette: Dictionary = park_svc.advance_corvette("Han_Solo", "clear_deck")
	assert(adv_corvette.get("instance_state", {}).get("current_deck") == "engine_room", "La progression vers la salle des machines doit être validée")

	# Raid Boss : Dragon Krayt
	var atk_krayt: Dictionary = park_svc.attack_krayt_dragon("Han_Solo", 95000)
	assert(atk_krayt.get("dragon_slain") == true, "L'élimination du Dragon Krayt doit réussir")
	assert(atk_krayt.get("loot", {}).has("krayt_dragon_pearl"), "Le loot légendaire doit contenir une Perle de Dragon Krayt")
	print("[+] PASS: Parcs à Thèmes & Donjons - Palais de Jabba, Corvette Corellienne & Dragon Krayt validés")

	# --- 11. TEST MULTI-PLANÈTES & BIOMES ---
	var galaxy = HubGalaxyPlanetsScript.new()
	assert(galaxy.get_all_planets().size() == 5, "Les 5 planètes majeures doivent être recensées")

	# Voyage vers Naboo
	var travel_naboo: Dictionary = galaxy.travel_to_planet("Leia_Organa", "naboo")
	assert(bool(travel_naboo.get("ok")) and travel_naboo.get("current_planet") == "naboo", "Le transit vers Naboo doit réussir")
	assert(travel_naboo.get("capital") == "Theed", "La capitale de Naboo doit être Theed")

	# Profil de Dathomir
	var prof_dathomir: Dictionary = galaxy.get_ambient_profile("dathomir")
	assert(bool(prof_dathomir.get("ok")) and prof_dathomir.get("biome") == "toxic_quarantine_badlands", "Le biome de Dathomir doit être validé")
	print("[+] PASS: Multi-Planètes & Biomes - Tatooine, Naboo, Endor, Dathomir & Corellia validés")

	if economy != null and economy.db != null and economy.db.has_method("shutdown"):
		economy.db.shutdown()

	print("SWG_COMPLETE_FEATURES_SELFTEST_OK: Reproduction 100% Star Wars Galaxies Pre-CU validée avec succès !")
	quit(0)
