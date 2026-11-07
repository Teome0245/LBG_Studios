extends SceneTree
## Test de validation SWG Pre-CU Prime Hub : Factions GCW & Nids de Créatures (Lairs)

const HubCreaturesScript = preload("res://scripts/hub_creatures.gd")
const HubFactionScript = preload("res://scripts/hub_faction.gd")
const HubHttpScript = preload("res://scripts/hub_http.gd")
const HubEconomyScript = preload("res://scripts/hub_economy.gd")
const HubSimScript = preload("res://scripts/hub_sim.gd")


func _init() -> void:
	print("[*] Lancement du test Factions GCW & Nids de Créatures SWG Pre-CU (Prime Hub)...")

	var economy = HubEconomyScript.new()
	economy.setup()

	# 1. Validation des Nids de Créatures (Lairs)
	var creatures = HubCreaturesScript.new()
	creatures.setup(null, economy)

	var lairs: Array = creatures.list_lairs()
	assert(lairs.size() >= 2, "Au moins 2 nids de créatures doivent être initialisés (Chacals et Scarabées)")
	print("[+] PASS: 2 nids canoniques initialisés (Tumulus Ouest et Nid Est)")

	var lair_jackal: Dictionary = creatures.get_lair("lair_jackals_west")
	assert(lair_jackal.get("max_health") == 1400, "PV max du nid de chacals doit être 1400")

	# Attaque et déclenchement de la vague 1 (seuil 75%)
	var atk1: Dictionary = creatures.attack_lair("Soldat_Test", "lair_jackals_west", 400)
	assert(atk1.get("ok") == true, "L'attaque du nid doit réussir")
	assert(atk1.get("wave_triggered") == 1, "La vague 1 de défenseurs doit être déclenchée sous 75% PV")
	assert(atk1.get("remaining_hp") == 1000, "Les PV restants doivent être 1000")
	print("[+] PASS: Seuil de riposte 75% et vague de défenseurs déclenchés")

	# Attaque fatale menant à l'effondrement
	var atk_fatal: Dictionary = creatures.attack_lair("Soldat_Test", "lair_jackals_west", 1000)
	assert(atk_fatal.get("is_destroyed") == true, "Le nid doit être détruit à 0 PV")
	assert(atk_fatal.get("debris_ready") == true, "Les décombres doivent être pillables")
	print("[+] PASS: Effondrement du nid en décombres à 0 PV validé")

	# Pillage des décombres
	var loot: Dictionary = creatures.harvest_debris("Soldat_Test", "lair_jackals_west")
	assert(loot.get("ok") == true, "Le pillage des décombres doit réussir")
	assert(loot.get("credits") == 950, "950 crédits doivent être octroyés")
	assert(loot.get("rare_item") == "oeuf_chacal_fossile", "L'œuf fossilisé doit être pillé")

	var loot_again: Dictionary = creatures.harvest_debris("Soldat_Test", "lair_jackals_west")
	assert(loot_again.get("ok") == false, "Un nid déjà fouillé ne doit pas être réutilisable")
	print("[+] PASS: Pillage des décombres avec crédits et œuf rare validé (anti-duplication OK)")

	# 2. Validation du Système de Factions GCW
	var factions = HubFactionScript.new()
	factions.setup(null, null, economy)

	var recruiters: Array = factions.list_recruiters()
	assert(recruiters.size() >= 2, "Au moins 2 recruteurs (Impérial Lt Kren et Rebelle Cap Vao) doivent exister")
	print("[+] PASS: Recruteurs de faction déployés sur Lost Heaven")

	var data_init: Dictionary = factions.get_faction_data("Pilote_Rebel")
	assert(data_init.get("faction") == "neutral" and data_init.get("status") == "civilian", "Statut initial doit être civil neutre")

	# Enrôlement Rebelle
	var enl_reb: Dictionary = factions.enlist("Pilote_Rebel", "rebel")
	assert(enl_reb.get("ok") == true and enl_reb.get("status") == "on_leave", "Enrôlement en permission (On-Leave)")

	# Enrôlement Impérial
	var enl_imp: Dictionary = factions.enlist("Soldat_Empire", "imperial")
	assert(enl_imp.get("ok") == true and enl_imp.get("status") == "on_leave", "Enrôlement Impérial validé")

	# Vérification non-ennemi tant qu'en permission (On-Leave)
	assert(not factions.is_enemy("Pilote_Rebel", "Soldat_Empire"), "Deux soldats en permission ne sont pas engagés en PvP")

	# Déclaration Special Forces (Overt PvP)
	factions.declare_special_forces("Pilote_Rebel")
	factions.declare_special_forces("Soldat_Empire")
	assert(factions.is_enemy("Pilote_Rebel", "Soldat_Empire"), "Deux belligérants opposés Special Forces sont mutuellement ennemis")
	print("[+] PASS: Déclaration Special Forces et engagement PvP GCW validés")

	# Démobilisation (Retour au civil)
	var resign_res: Dictionary = factions.resign_to_civilian("Pilote_Rebel")
	assert(resign_res.get("faction") == "neutral", "Retour au statut civil neutre")
	assert(not factions.is_enemy("Pilote_Rebel", "Soldat_Empire"), "Le civil n'est plus un ennemi militaire")
	print("[+] PASS: Démobilisation et amnistie civile validées")

	# 3. Validation des Routes HTTP
	var sim := HubSimScript.new()
	sim.reset()
	var http_router = HubHttpScript.new()
	http_router.setup_services(null, economy, null, null, null)
	http_router.faction = factions
	http_router.sim = sim

	var res_lairs: Dictionary = http_router.handle_raw_request("GET", "/v1/creatures/lairs", "", "")
	assert(res_lairs.get("code") == 200, "Route GET /v1/creatures/lairs doit répondre 200")

	var res_recs: Dictionary = http_router.handle_raw_request("GET", "/v1/factions/recruiters", "", "")
	assert(res_recs.get("code") == 200, "Route GET /v1/factions/recruiters doit répondre 200")

	var res_specs: Dictionary = http_router.handle_raw_request("GET", "/v1/species/catalog", "", "")
	assert(res_specs.get("code") == 200, "Route GET /v1/species/catalog doit répondre 200")
	print("[+] PASS: Routes HTTP (/v1/creatures/lairs, /v1/factions/recruiters, /v1/species/catalog) validées")

	if sim.player_store != null:
		sim.player_store.shutdown()

	print("[+] Factions GCW & Nids de Créatures SWG Pre-CU (Prime Hub) : Tous les tests passent avec succès !")
	quit(0)
