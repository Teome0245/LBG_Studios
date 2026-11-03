extends RefCounted
class_name HubVendorsFactories
## Système SWG Pre-CU : Marchands Joueurs (Player Vendors), Usines (Factories & Crates)
## et Bazar Public pour l'économie 100% joueur de Lost Heaven (Ticket 3).

const _HubPaths := preload("res://scripts/hub_paths.gd")

const BAZAAR_MAX_PRICE := 20000
const BAZAAR_LISTING_FEE := 20
const VENDOR_TAX_PCT := 5 # 5% de taxe commerciale sur les transactions des vendeurs

var sim = null
var economy = null
var skills = null
var collision = null

var vendors_by_id: Dictionary = {}
var factories_by_id: Dictionary = {}
var bazaar_listings: Dictionary = {}

var _next_vendor_id := 1001
var _next_factory_id := 8001
var _next_sku_id := 2001
var _next_crate_id := 3001
var _next_bazaar_id := 4001


func setup(parent_sim, economy_svc = null, skills_svc = null, collision_svc = null) -> void:
	sim = parent_sim
	economy = economy_svc
	skills = skills_svc
	collision = collision_svc


# ==============================================================================
# SECTION 1 : VENDEURS PNJ DE JOUEURS (PLAYER VENDORS)
# ==============================================================================

func deploy_vendor(
	player: String,
	vendor_name: String,
	x: float,
	z: float,
	appearance: String = "droide_protocole"
) -> Dictionary:
	if economy == null:
		return {"ok": false, "error": "economy_unavailable"}

	var p: Dictionary = economy._player(player)
	var credits := int(p.get("credits", 0))
	var deploy_cost := 100
	if credits < deploy_cost:
		return {
			"ok": false,
			"error": "insufficient_credits",
			"cost": deploy_cost,
			"available": credits,
			"hint": "Il faut 100 crédits de caution pour enregistrer un vendeur."
		}

	# Vérification des compétences (Artisan ou Citoyen)
	if skills != null:
		var has_skill: bool = bool(skills.has_box(player, "artisan_novice") or skills.has_box(player, "citoyen_novice") or skills.has_box(player, "artisan_pieces_01"))
		if not has_skill:
			return {
				"ok": false,
				"error": "skill_required",
				"hint": "Requiert Artisan Novice ou Citoyen de quartier."
			}

	# Vérification de distance avec les autres vendeurs (min 3 mètres)
	for vid in vendors_by_id.keys():
		var existing: Dictionary = vendors_by_id[vid]
		var ep: Vector3 = existing.get("pos", Vector3.ZERO)
		var d := Vector2(ep.x - x, ep.z - z).length()
		if d < 3.0:
			return {
				"ok": false,
				"error": "too_close_to_another_vendor",
				"distance_m": snappedf(d, 0.1),
				"min_m": 3.0
			}

	# Débiter la caution
	p["credits"] = credits - deploy_cost

	var vid := "vendor_p_%d" % _next_vendor_id
	_next_vendor_id += 1

	var entry := {
		"vendor_id": vid,
		"owner": player,
		"name": vendor_name.strip_edges() if not vendor_name.strip_edges().is_empty() else "Boutique de %s" % player,
		"appearance": appearance,
		"pos": Vector3(x, 0.15, z),
		"stock": [], # Array de SKU {sku_id, item_id, item_name, qty, price_credits, stats, description}
		"bank_credits": 0,
		"maintenance_pool": 50, # 50 crédits d'avance d'entretien
		"sales_count": 0,
		"status": "open",
		"created_at": Time.get_unix_time_from_system()
	}
	vendors_by_id[vid] = entry

	# Enregistrement dans les entités du simulateur pour affichage/clic
	if sim != null:
		sim.entities[vid] = {
			"eid": vid,
			"kind": "vendor",
			"name": entry["name"],
			"owner": player,
			"pos": entry["pos"],
			"target": Vector3.ZERO,
			"goal": "vendor_idle",
			"active": true
		}

	if sim != null and sim.has_method("_stream"):
		sim._stream(
			"vendor.deployed",
			"%s a ouvert sa boutique : « %s » à (%.0f, %.0f)." % [player, entry["name"], x, z],
			player,
			"market",
			{"vendor_id": vid, "name": entry["name"]}
		)

	return {
		"ok": true,
		"vendor_id": vid,
		"vendor": entry.duplicate(true),
		"cost_paid": deploy_cost
	}


func get_vendor(vendor_id: String) -> Dictionary:
	var vid := vendor_id.strip_edges()
	if vendors_by_id.has(vid):
		return (vendors_by_id[vid] as Dictionary).duplicate(true)
	return {}


func list_player_vendors(player: String) -> Array:
	var out: Array = []
	for vid in vendors_by_id.keys():
		var v: Dictionary = vendors_by_id[vid]
		if str(v.get("owner", "")) == player:
			out.append(v.duplicate(true))
	return out


func list_all_vendors_near(x: float, z: float, radius_m: float = 80.0) -> Array:
	var out: Array = []
	for vid in vendors_by_id.keys():
		var v: Dictionary = vendors_by_id[vid]
		var p: Vector3 = v.get("pos", Vector3.ZERO)
		var d := Vector2(p.x - x, p.z - z).length()
		if d <= radius_m:
			var copy := v.duplicate(true)
			copy["distance_m"] = snappedf(d, 0.1)
			out.append(copy)
	return out


func stock_item(
	player: String,
	vendor_id: String,
	item_id: String,
	qty: int,
	price_credits: int,
	item_name: String = "",
	description: String = "",
	stats: Dictionary = {}
) -> Dictionary:
	if economy == null:
		return {"ok": false, "error": "economy_unavailable"}

	var vid := vendor_id.strip_edges()
	if not vendors_by_id.has(vid):
		return {"ok": false, "error": "vendor_not_found"}

	var vendor: Dictionary = vendors_by_id[vid]
	if str(vendor.get("owner", "")) != player:
		return {"ok": false, "error": "not_vendor_owner"}

	if qty <= 0 or price_credits <= 0:
		return {"ok": false, "error": "invalid_qty_or_price"}

	var p: Dictionary = economy._player(player)
	var inv_qty: int = int(economy._inv_qty(p, item_id))
	if inv_qty < qty:
		return {
			"ok": false,
			"error": "insufficient_inventory",
			"required": qty,
			"available": inv_qty
		}

	# Consommer de l'inventaire joueur
	economy._consume(p, item_id, qty)

	var sku_id := "sku_%d" % _next_sku_id
	_next_sku_id += 1

	var iname := item_name
	if iname.is_empty():
		iname = item_id.capitalize().replace("_", " ")

	var sku_entry := {
		"sku_id": sku_id,
		"item_id": item_id,
		"item_name": iname,
		"qty": qty,
		"price_credits": price_credits,
		"description": description,
		"stats": stats.duplicate(true),
		"stocked_at": Time.get_unix_time_from_system()
	}

	var stock: Array = vendor.get("stock", [])
	stock.append(sku_entry)
	vendor["stock"] = stock

	return {
		"ok": true,
		"vendor_id": vid,
		"sku_id": sku_id,
		"item_id": item_id,
		"item_name": iname,
		"qty_stocked": qty,
		"price_credits": price_credits
	}


func unstock_item(player: String, vendor_id: String, sku_id: String, qty_to_remove: int = 0) -> Dictionary:
	if economy == null:
		return {"ok": false, "error": "economy_unavailable"}

	var vid := vendor_id.strip_edges()
	if not vendors_by_id.has(vid):
		return {"ok": false, "error": "vendor_not_found"}

	var vendor: Dictionary = vendors_by_id[vid]
	if str(vendor.get("owner", "")) != player:
		return {"ok": false, "error": "not_vendor_owner"}

	var stock: Array = vendor.get("stock", [])
	var target_idx := -1
	var target_sku: Dictionary = {}
	for i in range(stock.size()):
		var s: Dictionary = stock[i]
		if str(s.get("sku_id", "")) == sku_id:
			target_idx = i
			target_sku = s
			break

	if target_idx < 0:
		return {"ok": false, "error": "sku_not_found"}

	var cur_qty := int(target_sku.get("qty", 0))
	var take := qty_to_remove
	if take <= 0 or take >= cur_qty:
		take = cur_qty
		stock.remove_at(target_idx)
	else:
		target_sku["qty"] = cur_qty - take
		stock[target_idx] = target_sku

	vendor["stock"] = stock

	# Rendre les objets à l'inventaire du propriétaire
	var p: Dictionary = economy._player(player)
	economy._add_item(p, str(target_sku.get("item_id", "")), take, str(target_sku.get("item_name", "")))

	return {
		"ok": true,
		"vendor_id": vid,
		"sku_id": sku_id,
		"qty_returned": take,
		"remaining_in_stock": int(target_sku.get("qty", 0)) if target_idx >= 0 else 0
	}


func buy_vendor_item(buyer: String, vendor_id: String, sku_id: String, qty_to_buy: int = 1) -> Dictionary:
	if economy == null:
		return {"ok": false, "error": "economy_unavailable"}

	var vid := vendor_id.strip_edges()
	if not vendors_by_id.has(vid):
		return {"ok": false, "error": "vendor_not_found"}

	var vendor: Dictionary = vendors_by_id[vid]
	var stock: Array = vendor.get("stock", [])
	var target_idx := -1
	var target_sku: Dictionary = {}
	for i in range(stock.size()):
		var s: Dictionary = stock[i]
		if str(s.get("sku_id", "")) == sku_id:
			target_idx = i
			target_sku = s
			break

	if target_idx < 0:
		return {"ok": false, "error": "sku_not_found_in_vendor"}

	var avail_qty := int(target_sku.get("qty", 0))
	var buy_qty := mini(qty_to_buy, avail_qty)
	if buy_qty <= 0:
		return {"ok": false, "error": "out_of_stock"}

	var unit_price := int(target_sku.get("price_credits", 1))
	var total_cost := unit_price * buy_qty

	var buyer_p: Dictionary = economy._player(buyer)
	var buyer_credits := int(buyer_p.get("credits", 0))
	if buyer_credits < total_cost:
		return {
			"ok": false,
			"error": "insufficient_credits",
			"cost": total_cost,
			"available": buyer_credits
		}

	# Débiter l'acheteur
	buyer_p["credits"] = buyer_credits - total_cost

	# Calcul de la taxe et du gain net vendeur
	var tax := maxi(1, int(round(float(total_cost) * (float(VENDOR_TAX_PCT) / 100.0))))
	var vendor_net := total_cost - tax
	vendor["bank_credits"] = int(vendor.get("bank_credits", 0)) + vendor_net
	vendor["sales_count"] = int(vendor.get("sales_count", 0)) + buy_qty

	# Déduire du stock
	var new_qty := avail_qty - buy_qty
	if new_qty <= 0:
		stock.remove_at(target_idx)
	else:
		target_sku["qty"] = new_qty
		stock[target_idx] = target_sku
	vendor["stock"] = stock

	# Livrer les objets à l'acheteur avec leurs stats exactes
	var item_id := str(target_sku.get("item_id", ""))
	var item_name := str(target_sku.get("item_name", ""))
	var stats: Dictionary = target_sku.get("stats", {})
	if not stats.is_empty():
		economy.grant_world_loot(buyer, [{"id": item_id, "name": item_name, "qty": buy_qty, "stats": stats}], 0)
	else:
		economy._add_item(buyer_p, item_id, buy_qty, item_name)

	if sim != null and sim.has_method("_stream"):
		sim._stream(
			"vendor.item_sold",
			"%s a acheté %d× %s à la boutique %s (%d cr)." % [buyer, buy_qty, item_name, str(vendor.get("name", "")), total_cost],
			buyer,
			"market",
			{"vendor_id": vid, "sku_id": sku_id, "total_cost": total_cost, "tax": tax}
		)

	return {
		"ok": true,
		"vendor_id": vid,
		"buyer": buyer,
		"item_id": item_id,
		"item_name": item_name,
		"qty_bought": buy_qty,
		"total_cost": total_cost,
		"tax_paid": tax,
		"remaining_in_stock": new_qty,
		"stats": stats
	}


func withdraw_vendor_credits(player: String, vendor_id: String, amount: int = 0) -> Dictionary:
	if economy == null:
		return {"ok": false, "error": "economy_unavailable"}

	var vid := vendor_id.strip_edges()
	if not vendors_by_id.has(vid):
		return {"ok": false, "error": "vendor_not_found"}

	var vendor: Dictionary = vendors_by_id[vid]
	if str(vendor.get("owner", "")) != player:
		return {"ok": false, "error": "not_vendor_owner"}

	var bank := int(vendor.get("bank_credits", 0))
	if bank <= 0:
		return {"ok": false, "error": "no_credits_to_withdraw"}

	var take := amount
	if take <= 0 or take > bank:
		take = bank

	vendor["bank_credits"] = bank - take
	var p: Dictionary = economy._player(player)
	p["credits"] = int(p.get("credits", 0)) + take

	return {
		"ok": true,
		"vendor_id": vid,
		"withdrawn": take,
		"remaining_bank": int(vendor["bank_credits"]),
		"player_credits": int(p["credits"])
	}


# ==============================================================================
# SECTION 2 : USINES DE FABRICATION EN SÉRIE (FACTORIES & CRATES)
# ==============================================================================

func deploy_factory(player: String, factory_type: String, x: float, z: float) -> Dictionary:
	var ftype := factory_type.strip_edges().to_lower()
	if not ftype in ["equipement", "consommables", "structures"]:
		ftype = "equipement"

	# Vérification des compétences
	if skills != null:
		var has_skill: bool = bool(skills.has_box(player, "artisan_pieces_02") or skills.has_box(player, "artisan_novice"))
		if not has_skill:
			return {
				"ok": false,
				"error": "skill_required",
				"hint": "Requiert Artisan Novice ou Composants Mécatroniques rang 2."
			}

	var fid := "factory_%d" % _next_factory_id
	_next_factory_id += 1

	var entry := {
		"factory_id": fid,
		"owner": player,
		"factory_type": ftype,
		"pos": Vector3(x, 0.15, z),
		"schematic": {}, # Manufacturing schematic figeant la recette et stats
		"input_hopper": {}, # Matériaux déposés {item_id: qty}
		"output_hopper": [], # Caisses de production terminées
		"energy_units": 100, # Énergie de démarrage
		"is_running": false,
		"total_cycles_run": 0,
		"created_at": Time.get_unix_time_from_system()
	}
	factories_by_id[fid] = entry

	return {
		"ok": true,
		"factory_id": fid,
		"factory": entry.duplicate(true)
	}


func get_factory(factory_id: String) -> Dictionary:
	var fid := factory_id.strip_edges()
	if factories_by_id.has(fid):
		return (factories_by_id[fid] as Dictionary).duplicate(true)
	return {}


func load_factory_schematic(player: String, factory_id: String, schematic: Dictionary) -> Dictionary:
	var fid := factory_id.strip_edges()
	if not factories_by_id.has(fid):
		return {"ok": false, "error": "factory_not_found"}

	var factory: Dictionary = factories_by_id[fid]
	if str(factory.get("owner", "")) != player:
		return {"ok": false, "error": "not_factory_owner"}

	if schematic.is_empty() or not schematic.has("output_item_id") or not schematic.has("inputs"):
		return {"ok": false, "error": "invalid_manufacturing_schematic"}

	factory["schematic"] = schematic.duplicate(true)
	factory["is_running"] = true

	return {
		"ok": true,
		"factory_id": fid,
		"schematic_loaded": str(schematic.get("schematic_name", schematic.get("output_item_id", ""))),
		"status": "running"
	}


func deposit_factory_material(player: String, factory_id: String, item_id: String, qty: int) -> Dictionary:
	if economy == null:
		return {"ok": false, "error": "economy_unavailable"}

	var fid := factory_id.strip_edges()
	if not factories_by_id.has(fid):
		return {"ok": false, "error": "factory_not_found"}

	var factory: Dictionary = factories_by_id[fid]
	if str(factory.get("owner", "")) != player:
		return {"ok": false, "error": "not_factory_owner"}

	var p: Dictionary = economy._player(player)
	var inv_qty: int = int(economy._inv_qty(p, item_id))
	if inv_qty < qty:
		return {"ok": false, "error": "insufficient_inventory", "available": inv_qty}

	economy._consume(p, item_id, qty)

	var hopper: Dictionary = factory.get("input_hopper", {})
	hopper[item_id] = int(hopper.get(item_id, 0)) + qty
	factory["input_hopper"] = hopper

	return {
		"ok": true,
		"factory_id": fid,
		"item_id": item_id,
		"qty_deposited": qty,
		"hopper_total": int(hopper[item_id])
	}


func deposit_factory_energy(player: String, factory_id: String, energy_units: int) -> Dictionary:
	var fid := factory_id.strip_edges()
	if not factories_by_id.has(fid):
		return {"ok": false, "error": "factory_not_found"}

	var factory: Dictionary = factories_by_id[fid]
	if str(factory.get("owner", "")) != player:
		return {"ok": false, "error": "not_factory_owner"}

	factory["energy_units"] = int(factory.get("energy_units", 0)) + energy_units
	return {
		"ok": true,
		"factory_id": fid,
		"energy_units": int(factory["energy_units"])
	}


func advance_factory_cycles(factory_id: String, requested_cycles: int = 1) -> Dictionary:
	var fid := factory_id.strip_edges()
	if not factories_by_id.has(fid):
		return {"ok": false, "error": "factory_not_found"}

	var factory: Dictionary = factories_by_id[fid]
	var sch: Dictionary = factory.get("schematic", {})
	if sch.is_empty():
		return {"ok": false, "error": "no_schematic_loaded"}

	var inputs: Dictionary = sch.get("inputs", {}) # {item_id: qty_required}
	var energy_per_cycle := int(sch.get("energy_per_cycle", 5))
	var crate_size := int(sch.get("crate_size", 5)) # Unités par caisse manufacturée
	var output_id := str(sch.get("output_item_id", "produit"))
	var output_name := str(sch.get("output_item_name", "Produit manufacturé"))
	var output_stats: Dictionary = sch.get("output_stats", {})

	var hopper: Dictionary = factory.get("input_hopper", {})
	var energy := int(factory.get("energy_units", 0))

	var cycles_done := 0
	for _c in range(requested_cycles):
		if energy < energy_per_cycle:
			break

		# Vérifier tous les intrants requis
		var can_craft := true
		for in_id in inputs.keys():
			var req_qty := int(inputs[in_id])
			if int(hopper.get(in_id, 0)) < req_qty:
				can_craft = false
				break

		if not can_craft:
			break

		# Déduire les matériaux et l'énergie
		for in_id in inputs.keys():
			hopper[in_id] = int(hopper[in_id]) - int(inputs[in_id])
		energy -= energy_per_cycle
		cycles_done += 1

	factory["energy_units"] = energy
	factory["input_hopper"] = hopper
	factory["total_cycles_run"] = int(factory.get("total_cycles_run", 0)) + cycles_done

	# Assemblage en caisses manufacturées (Crates)
	var crates_created := 0
	if cycles_done > 0:
		var crate_id := "crate_%d" % _next_crate_id
		_next_crate_id += 1

		var crate_entry := {
			"crate_id": crate_id,
			"item_id": output_id,
			"item_name": output_name,
			"units_count": cycles_done,
			"crate_capacity": crate_size,
			"stats": output_stats.duplicate(true),
			"manufactured_by": str(factory.get("owner", "")),
			"manufactured_at": Time.get_unix_time_from_system()
		}
		var out_hopper: Array = factory.get("output_hopper", [])
		out_hopper.append(crate_entry)
		factory["output_hopper"] = out_hopper
		crates_created = 1

	return {
		"ok": true,
		"factory_id": fid,
		"cycles_completed": cycles_done,
		"crates_created": crates_created,
		"remaining_energy": energy,
		"status": "running" if energy > 0 else "out_of_energy"
	}


func collect_factory_crates(player: String, factory_id: String) -> Dictionary:
	var fid := factory_id.strip_edges()
	if not factories_by_id.has(fid):
		return {"ok": false, "error": "factory_not_found"}

	var factory: Dictionary = factories_by_id[fid]
	if str(factory.get("owner", "")) != player:
		return {"ok": false, "error": "not_factory_owner"}

	var out_hopper: Array = factory.get("output_hopper", [])
	if out_hopper.is_empty():
		return {"ok": false, "error": "output_hopper_empty"}

	var collected_crates := out_hopper.duplicate(true)
	factory["output_hopper"] = []

	# Livraison à l'inventaire joueur sous forme de caisses
	if economy != null:
		var p: Dictionary = economy._player(player)
		for crate in collected_crates:
			var c_id := "caisse_%s" % str(crate.get("item_id", "item"))
			var c_name := "Caisse de %s (%d un.)" % [str(crate.get("item_name", "")), int(crate.get("units_count", 1))]
			economy.grant_world_loot(player, [{"id": c_id, "name": c_name, "qty": 1, "crate_data": crate}], 0)

	return {
		"ok": true,
		"factory_id": fid,
		"crates_collected": collected_crates,
		"count": collected_crates.size()
	}


# ==============================================================================
# SECTION 3 : BAZAR PUBLIC & BOURSE MUNICIPALE (PUBLIC BAZAAR)
# ==============================================================================

func post_bazaar_listing(
	player: String,
	item_id: String,
	qty: int,
	price_credits: int,
	item_name: String = "",
	stats: Dictionary = {}
) -> Dictionary:
	if economy == null:
		return {"ok": false, "error": "economy_unavailable"}

	if price_credits > BAZAAR_MAX_PRICE:
		return {
			"ok": false,
			"error": "price_exceeds_bazaar_cap",
			"max_price": BAZAAR_MAX_PRICE,
			"hint": "Au-delà de 20 000 crédits, ouvre un Player Vendor personnel."
		}

	var p: Dictionary = economy._player(player)
	var credits := int(p.get("credits", 0))
	if credits < BAZAAR_LISTING_FEE:
		return {"ok": false, "error": "insufficient_fee_credits", "fee": BAZAAR_LISTING_FEE}

	var inv_qty: int = int(economy._inv_qty(p, item_id))
	if inv_qty < qty:
		return {"ok": false, "error": "insufficient_inventory", "available": inv_qty}

	# Prélèvement des frais de bazar et de l'objet
	p["credits"] = credits - BAZAAR_LISTING_FEE
	economy._consume(p, item_id, qty)

	var lid := "bazaar_%d" % _next_bazaar_id
	_next_bazaar_id += 1

	var iname := item_name
	if iname.is_empty():
		iname = item_id.capitalize().replace("_", " ")

	var listing := {
		"listing_id": lid,
		"seller": player,
		"item_id": item_id,
		"item_name": iname,
		"qty": qty,
		"price_credits": price_credits,
		"stats": stats.duplicate(true),
		"listed_at": Time.get_unix_time_from_system(),
		"expires_at": Time.get_unix_time_from_system() + 86400 # 24 heures
	}
	bazaar_listings[lid] = listing

	return {
		"ok": true,
		"listing_id": lid,
		"listing": listing.duplicate(true),
		"fee_paid": BAZAAR_LISTING_FEE
	}


func list_bazaar() -> Array:
	var out: Array = []
	var now := Time.get_unix_time_from_system()
	for lid in bazaar_listings.keys():
		var l: Dictionary = bazaar_listings[lid]
		if float(l.get("expires_at", 0.0)) > now:
			out.append(l.duplicate(true))
	return out


func buy_bazaar_listing(buyer: String, listing_id: String) -> Dictionary:
	if economy == null:
		return {"ok": false, "error": "economy_unavailable"}

	var lid := listing_id.strip_edges()
	if not bazaar_listings.has(lid):
		return {"ok": false, "error": "listing_not_found"}

	var listing: Dictionary = bazaar_listings[lid]
	var cost := int(listing.get("price_credits", 0))
	var buyer_p: Dictionary = economy._player(buyer)
	var buyer_cr := int(buyer_p.get("credits", 0))
	if buyer_cr < cost:
		return {"ok": false, "error": "insufficient_credits", "cost": cost, "available": buyer_cr}

	# Débiter l'acheteur
	buyer_p["credits"] = buyer_cr - cost

	# Créditer le vendeur
	var seller_name := str(listing.get("seller", ""))
	var seller_p: Dictionary = economy._player(seller_name)
	seller_p["credits"] = int(seller_p.get("credits", 0)) + cost

	# Transférer l'objet à l'acheteur
	var item_id := str(listing.get("item_id", ""))
	var item_name := str(listing.get("item_name", ""))
	var qty := int(listing.get("qty", 1))
	var stats: Dictionary = listing.get("stats", {})
	if not stats.is_empty():
		economy.grant_world_loot(buyer, [{"id": item_id, "name": item_name, "qty": qty, "stats": stats}], 0)
	else:
		economy._add_item(buyer_p, item_id, qty, item_name)

	bazaar_listings.erase(lid)

	return {
		"ok": true,
		"listing_id": lid,
		"buyer": buyer,
		"seller": seller_name,
		"item_id": item_id,
		"item_name": item_name,
		"qty": qty,
		"cost_paid": cost
	}
