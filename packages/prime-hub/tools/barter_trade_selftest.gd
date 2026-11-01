extends SceneTree
## barter_trade_selftest.gd — Validation headless de l'Économie de Troc P2P & Négociations entre Joueurs IA (Ticket 3.2 O3 Phase 3).
##
## Usage:
##   packages/prime-hub/tools/Godot_v4.6.3-stable_linux.x86_64 --headless \
##     --path packages/prime-hub -s res://tools/barter_trade_selftest.gd

const HubEconomyScript := preload("res://scripts/hub_economy.gd")
const HubBotAutonomyScript := preload("res://scripts/hub_bot_autonomy.gd")
const HubTradeScript := preload("res://scripts/hub_trade.gd")
const HubWikiScript := preload("res://scripts/hub_wiki.gd")


func _init() -> void:
	print("[*] Lancement du test Économie de Troc P2P & Négociations d'Échanges (Ticket 3.2 O3)...")

	HubWikiScript.clear_rumors()

	var economy := HubEconomyScript.new()
	economy.setup()

	var autonomy := HubBotAutonomyScript.new()
	autonomy.setup(economy, null, {})

	var trade := HubTradeScript.new()
	trade.setup(economy, autonomy)

	# Test 1 : Matrice de valeur relative bornée (2 ferrailles = 1 capsule d'eau)
	assert(trade.get_item_value("scrap_metal") == 1, "La ferraille vaut 1")
	assert(trade.get_item_value("water_capsule") == 2, "La capsule d'eau vaut 2")
	assert(trade.is_fair_exchange("scrap_metal", 2, "water_capsule", 1) == true, "2 ferrailles contre 1 eau est équitable")
	assert(trade.is_fair_exchange("scrap_metal", 1, "regulated_scrap_battery", 3) == false, "1 ferraille contre 3 batteries doit être refusé")
	print("[+] PASS: Matrice de valeur relative bornée et garde-fou anti-déséquilibre validés")

	# Test 2 : Préparation de deux bots avec besoins complémentaires
	# BotA (Nix_Barter) : excédent de ferraille (8), déficit en eau (1 seule capsule après consommation)
	# BotB (Lia_Barter) : excédent d'eau (5 capsules), déficit en ferraille
	var bot_a := "Nix_BarterTest"
	var bot_b := "Lia_BarterTest"

	# Réinitialise / ajuste leurs stocks pour le scénario déterministe
	var cur_water_a := economy.item_quantity(bot_a, "water_capsule")
	while cur_water_a > 1:
		economy.use_item(bot_a, "water_capsule")
		cur_water_a = economy.item_quantity(bot_a, "water_capsule")
	var cur_scrap_a := economy.item_quantity(bot_a, "scrap_metal")
	if cur_scrap_a < 7:
		economy.grant_world_loot(bot_a, [{"id": "scrap_metal", "qty": 7 - cur_scrap_a, "name": "Ferraille"}], 0)

	var cur_water_b := economy.item_quantity(bot_b, "water_capsule")
	if cur_water_b < 5:
		economy.grant_world_loot(bot_b, [{"id": "water_capsule", "qty": 5 - cur_water_b, "name": "Capsule d'eau"}], 0)

	var needs_a := autonomy.evaluate_barter_needs(bot_a)
	var needs_b := autonomy.evaluate_barter_needs(bot_b)
	assert(needs_a["surplus"].size() >= 1, "Bot A doit avoir un surplus de ferraille")
	assert(needs_a["deficits"].size() >= 1, "Bot A doit avoir un déficit en eau")
	assert(needs_b["surplus"].size() >= 1, "Bot B doit avoir un surplus d'eau")
	print("[+] PASS: Estimation autonome des surplus et déficits d'inventaire validée")

	# Test 3 : Négociation et exécution atomique du troc P2P
	var scrap_a_before := economy.item_quantity(bot_a, "scrap_metal")
	var water_a_before := economy.item_quantity(bot_a, "water_capsule")
	var scrap_b_before := economy.item_quantity(bot_b, "scrap_metal")
	var water_b_before := economy.item_quantity(bot_b, "water_capsule")

	var res := trade.negotiate_auto_barter(bot_a, bot_b, "Cantina La Perle")
	assert(res.get("ok") == true, "La négociation automatique de troc P2P doit aboutir")

	var scrap_a_after := economy.item_quantity(bot_a, "scrap_metal")
	var water_a_after := economy.item_quantity(bot_a, "water_capsule")
	var scrap_b_after := economy.item_quantity(bot_b, "scrap_metal")
	var water_b_after := economy.item_quantity(bot_b, "water_capsule")

	assert(scrap_a_after == scrap_a_before - 2, "Bot A doit avoir cédé 2 ferrailles")
	assert(water_a_after == water_a_before + 1, "Bot A doit avoir reçu 1 capsule d'eau")
	assert(scrap_b_after == scrap_b_before + 2, "Bot B doit avoir reçu 2 ferrailles")
	assert(water_b_after == water_b_before - 1, "Bot B doit avoir cédé 1 capsule d'eau")
	print("[+] PASS: Échange atomique bilatéral (2 Ferrailles <-> 1 Capsule d'eau) vérifié sans duplication")

	# Test 4 : Vérification de la rumeur générée dans HubWiki
	var latest_rumor := HubWikiScript.get_latest_rumor("hub_cantina")
	assert(not latest_rumor.is_empty(), "Une rumeur de troc doit être consignée dans HubWiki")
	assert(str(latest_rumor.get("topic", "")) == "barter", "Le topic de la rumeur doit être 'barter'")
	print("  - Rumeur consignée : %s" % str(latest_rumor.get("text", "")))
	print("[+] PASS: Intégration rumeur de troc dans HubWiki validée")

	if economy.db != null and economy.db.has_method("shutdown"):
		economy.db.shutdown()

	print("[+] Économie de Troc P2P & Négociations (Ticket 3.2 O3) : Tous les tests passent avec succès !")
	quit(0)

