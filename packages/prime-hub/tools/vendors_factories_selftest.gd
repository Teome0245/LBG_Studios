extends SceneTree
## vendors_factories_selftest.gd — Validation headless Commerce, Player Vendors, Usines & Bazar SWG Pre-CU (Ticket 3).

const HubCollisionScript := preload("res://scripts/hub_collision.gd")
const HubEconomyScript := preload("res://scripts/hub_economy.gd")
const HubSkillsScript := preload("res://scripts/hub_skills.gd")
const HubSimScript := preload("res://scripts/hub_sim.gd")
const HubVendorsFactoriesScript := preload("res://scripts/hub_vendors_factories.gd")


func _init() -> void:
	print("[*] Lancement du test Commerce SWG Pre-CU : Vendeurs Joueurs, Usines & Bazar (Ticket 3)...")

	var sim := HubSimScript.new()
	sim.reset()

	var economy := HubEconomyScript.new()
	economy.setup()

	var skills := HubSkillsScript.new()
	skills.setup(economy)

	var vf := HubVendorsFactoriesScript.new()
	vf.setup(sim, economy, skills, sim.collision)

	var merchant := "Merchant_Nix_%d" % (Time.get_ticks_msec() % 100000)
	var buyer := "Buyer_Lia_%d" % (Time.get_ticks_msec() % 100000)

	# Seed initial des crédits et compétences
	var p_merch := economy._player(merchant)
	p_merch["credits"] = 500
	skills.learn_box(merchant, "artisan_novice", true)
	skills.learn_box(merchant, "artisan_pieces_02", true)

	var p_buyer := economy._player(buyer)
	p_buyer["credits"] = 1000

	# --------------------------------------------------------------------------
	# 1. PLAYER VENDOR (Marchand PNJ Personnel)
	# --------------------------------------------------------------------------
	# Déploiement d'un vendeur PNJ par Merchant_Nix
	var dep_v := vf.deploy_vendor(merchant, "Armurerie de Nix", 5110.0, -810.0, "droide_protocole")
	assert(bool(dep_v.get("ok", false)) == true, "Déploiement du vendeur doit réussir")
	var vid := str(dep_v.get("vendor_id", ""))
	assert(not vid.is_empty(), "vendor_id doit être généré")
	assert(int(p_merch["credits"]) == 400, "100 crédits de caution doivent être débités (solde=400)")
	print("[+] PASS: Vendeur PNJ %s (« %s ») déployé par %s (caution=100 cr)" % [vid, str(dep_v.get("vendor", {}).get("name", "")), merchant])

	# Refus de poser un 2e vendeur à moins de 3m
	var dep_too_close := vf.deploy_vendor(merchant, "Boutique Bis", 5111.0, -810.5)
	assert(bool(dep_too_close.get("ok", false)) == false, "Vendeur trop proche doit être refusé")
	assert(str(dep_too_close.get("error", "")) == "too_close_to_another_vendor", "Erreur attendue: too_close_to_another_vendor")
	print("[+] PASS: Contrôle d'espacement urbain entre vendeurs validé (< 3m refusé)")

	# Donner des objets de craft à Merchant_Nix pour les mettre en vente
	economy.grant_world_loot(merchant, [
		{"id": "lame_obsidienne", "name": "Lame en obsidienne renforcée", "qty": 3, "stats": {"oq": 850, "power": 115}}
	], 0)

	# Mise en stock de 2 lames à 150 crédits chacune
	var stock_res := vf.stock_item(
		merchant, vid, "lame_obsidienne", 2, 150,
		"Lame en obsidienne renforcée",
		"Forgée sur mesure avec obsidienne pure.",
		{"oq": 850, "power": 115}
	)
	assert(bool(stock_res.get("ok", false)) == true, "Mise en stock du vendeur doit réussir")
	var sku_id := str(stock_res.get("sku_id", ""))
	assert(not sku_id.is_empty(), "sku_id doit être généré")
	assert(economy._inv_qty(p_merch, "lame_obsidienne") == 1, "Il doit rester 1 lame dans l'inventaire du marchand")
	print("[+] PASS: Mise en rayon : 2× Lames d'obsidienne (SKU=%s, Prix=150 cr, OQ=850, Power=115)" % sku_id)

	# Achat par Buyer_Lia (1 lame pour 150 crédits)
	var buy_res := vf.buy_vendor_item(buyer, vid, sku_id, 1)
	assert(bool(buy_res.get("ok", false)) == true, "Achat chez le vendeur joueur doit réussir")
	assert(int(p_buyer["credits"]) == 850, "Buyer_Lia doit avoir 850 crédits (1000 - 150)")
	# Taxe 5% de 150 = 8 cr, net vendeur = 142 cr
	var vendor_info := vf.get_vendor(vid)
	assert(int(vendor_info.get("bank_credits", 0)) == 142, "Banque vendeur doit contenir 142 cr (150 - 5%% taxe)")
	assert(economy._inv_qty(p_buyer, "lame_obsidienne") == 1, "Buyer_Lia doit avoir reçu 1 lame d'obsidienne")
	print("[+] PASS: Transaction client validée : 1× acheté à 150 cr (Taxe=8 cr, Net banque vendeur=142 cr)")

	# Retrait des crédits de la banque du vendeur par Merchant_Nix
	var with_res := vf.withdraw_vendor_credits(merchant, vid, 142)
	assert(bool(with_res.get("ok", false)) == true, "Retrait des crédits vendeur doit réussir")
	assert(int(p_merch["credits"]) == 542, "Merchant_Nix doit avoir 542 crédits (400 + 142)")
	print("[+] PASS: Encaissement du marchand validé : 142 cr transférés au portefeuille")

	# --------------------------------------------------------------------------
	# 2. USINES DE PRODUCTION EN SÉRIE (FACTORIES & CRATES)
	# --------------------------------------------------------------------------
	var dep_fac := vf.deploy_factory(merchant, "equipement", 5220.0, -780.0)
	assert(bool(dep_fac.get("ok", false)) == true, "Déploiement d'usine d'équipement doit réussir")
	var fid := str(dep_fac.get("factory_id", ""))
	assert(not fid.is_empty(), "factory_id doit être généré")

	# Définition d'un Manufacturing Schematic (Schéma de production en série)
	var schematic := {
		"schematic_name": "Série Plaques Carapace Renforcées",
		"output_item_id": "plaque_carapace",
		"output_item_name": "Plaque de Carapace Lourde",
		"crate_size": 5,
		"energy_per_cycle": 5,
		"inputs": {
			"ferraille": 2,
			"carapace_obsidienne": 1
		},
		"output_stats": {
			"armor_rating": 85,
			"quality": 88.0,
			"oq": 780
		}
	}
	var load_sch := vf.load_factory_schematic(merchant, fid, schematic)
	assert(bool(load_sch.get("ok", false)) == true, "Chargement du schéma d'usine doit réussir")

	# Dépôt des matériaux dans la trémie d'entrée
	economy.grant_world_loot(merchant, [
		{"id": "ferraille", "name": "Ferraille", "qty": 20},
		{"id": "carapace_obsidienne", "name": "Carapace d'obsidienne", "qty": 10}
	], 0)
	vf.deposit_factory_material(merchant, fid, "ferraille", 10)
	vf.deposit_factory_material(merchant, fid, "carapace_obsidienne", 5)

	# Lancer 5 cycles de fabrication (consomme 10 ferrailles + 5 carapaces + 25 énergie)
	var run_fac := vf.advance_factory_cycles(fid, 5)
	assert(bool(run_fac.get("ok", false)) == true, "Exécution des cycles d'usine doit réussir")
	assert(int(run_fac.get("cycles_completed", 0)) == 5, "5 cycles complets doivent être exécutés")
	assert(int(run_fac.get("crates_created", 0)) == 1, "1 caisse manufacturée doit être créée")
	print("[+] PASS: Usine %s : 5 cycles complétés -> 1 Caisse de 5× Plaques Carapace générée" % fid)

	# Collecte de la caisse dans l'inventaire
	var col_crates := vf.collect_factory_crates(merchant, fid)
	assert(bool(col_crates.get("ok", false)) == true, "Collecte des caisses doit réussir")
	assert(int(col_crates.get("count", 0)) == 1, "1 caisse collectée")
	assert(economy._inv_qty(p_merch, "caisse_plaque_carapace") == 1, "La caisse doit être dans l'inventaire du marchand")
	print("[+] PASS: Caisse manufacturée transférée à l'inventaire (caisse_plaque_carapace)")

	# --------------------------------------------------------------------------
	# 3. BAZAR PUBLIC & BOURSE MUNICIPALE
	# --------------------------------------------------------------------------
	# Mise en vente au bazar d'une ration compacte à 80 crédits
	economy.grant_world_loot(merchant, [{"id": "ration_compacte", "name": "Ration Compacte", "qty": 1}], 0)
	var baz_post := vf.post_bazaar_listing(merchant, "ration_compacte", 1, 80, "Ration Compacte Énergétique")
	assert(bool(baz_post.get("ok", false)) == true, "Mise en vente au bazar public doit réussir")
	var lid := str(baz_post.get("listing_id", ""))
	assert(not lid.is_empty(), "listing_id doit être généré")
	assert(int(p_merch["credits"]) == 522, "20 crédits de frais de bazar déduits (542 - 20 = 522)")
	print("[+] PASS: Annonce Bazar %s postée (Frais=20 cr déduits)" % lid)

	# Contrôle plafond bazar (max 20 000 cr)
	var baz_cap_test := vf.post_bazaar_listing(merchant, "lame_obsidienne", 1, 25000)
	assert(bool(baz_cap_test.get("ok", false)) == false, "Annonce > 20 000 cr sur le bazar doit être refusée")
	assert(str(baz_cap_test.get("error", "")) == "price_exceeds_bazaar_cap", "Erreur attendue: price_exceeds_bazaar_cap")
	print("[+] PASS: Règle de plafond du Bazar public validée (max 20 000 cr, au-delà requiert Player Vendor)")

	# Achat au bazar par Buyer_Lia
	var baz_buy := vf.buy_bazaar_listing(buyer, lid)
	assert(bool(baz_buy.get("ok", false)) == true, "Achat au bazar doit réussir")
	assert(int(p_buyer["credits"]) == 770, "Buyer_Lia débitée de 80 cr (850 - 80 = 770)")
	assert(int(p_merch["credits"]) == 602, "Merchant_Nix crédité de 80 cr (522 + 80 = 602)")
	assert(economy._inv_qty(p_buyer, "ration_compacte") == 1, "Buyer_Lia a reçu la ration")
	print("[+] PASS: Achat au Bazar public validé (80 cr virés à Merchant_Nix, objet remis à Buyer_Lia)")

	if sim.player_store != null and sim.player_store.has_method("shutdown"):
		sim.player_store.shutdown()
	if economy.db != null and economy.db.has_method("shutdown"):
		economy.db.shutdown()

	print("[+] Ticket 3 (Commerce, Player Vendors, Usines & Bazar) : Tous les tests passent avec succès !")
	quit(0)

