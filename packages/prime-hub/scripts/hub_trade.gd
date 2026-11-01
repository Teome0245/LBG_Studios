extends RefCounted
class_name HubTrade
## Ticket 3.2 (O3 Phase 3) — Économie de Troc P2P & Négociations d'Échanges entre Joueurs IA.
## Autorité serveur Godot Hub : matrice de valeur relative bornée, protocole d'offre/acceptation,
## échange bilatéral atomique dans HubEconomy (SQLite) et génération de rumeurs HubWiki.

const HubWikiScript := preload("res://scripts/hub_wiki.gd")

## Valeur relative unitaire bornée (ex: 2 ferrailles légères = 1 capsule d'eau)
const ITEM_RELATIVE_VALUES: Dictionary = {
	"scrap_metal": 1,
	"dried_grain": 1,
	"binding_tape": 2,
	"water_capsule": 2,
	"used_capacitor": 3,
	"oasis_condensate_filter": 4,
	"night_prospecting_torch": 4,
	"kit_reparation": 5,
	"mechatronic_repair_kit": 6,
	"regulated_scrap_battery": 8,
}

const ITEM_LABELS: Dictionary = {
	"scrap_metal": "Ferraille",
	"dried_grain": "Grain séché",
	"binding_tape": "Ruban de liaison",
	"water_capsule": "Capsule d'eau",
	"used_capacitor": "Condensateur usé",
	"oasis_condensate_filter": "Filtre à condensat d'oasis",
	"night_prospecting_torch": "Torche de prospection nocturne",
	"kit_reparation": "Kit de réparation",
	"mechatronic_repair_kit": "Kit de réparation mécatronique",
	"regulated_scrap_battery": "Batterie régulée de ferraille",
}

var economy = null
var autonomy = null
var pending_offers: Dictionary = {}  # offer_id -> Dictionary
var trade_history: Array = []
var _seq: int = 0


func setup(economy_svc, autonomy_svc = null) -> void:
	economy = economy_svc
	autonomy = autonomy_svc


func get_item_value(item_id: String) -> int:
	return int(ITEM_RELATIVE_VALUES.get(item_id.strip_edges(), 1))


func is_fair_exchange(give_id: String, give_qty: int, recv_id: String, recv_qty: int) -> bool:
	if give_qty <= 0 or recv_qty <= 0:
		return false
	var give_val := get_item_value(give_id) * give_qty
	var recv_val := get_item_value(recv_id) * recv_qty
	# Tolérance de négociation bornée : ratio entre 0.5 et 2.0
	var ratio := float(give_val) / float(maxi(1, recv_val))
	return ratio >= 0.5 and ratio <= 2.0


func create_offer(
	sender: String,
	receiver: String,
	give_item_id: String,
	give_qty: int,
	receive_item_id: String,
	receive_qty: int,
	location_label: String = "Cantina La Perle"
) -> Dictionary:
	var s_name := sender.strip_edges()
	var r_name := receiver.strip_edges()
	var g_id := give_item_id.strip_edges()
	var r_id := receive_item_id.strip_edges()

	if s_name.is_empty() or r_name.is_empty() or s_name == r_name:
		return {"ok": false, "error": "invalid_participants"}
	if not is_fair_exchange(g_id, give_qty, r_id, receive_qty):
		return {
			"ok": false,
			"error": "unfair_exchange_ratio",
			"give_value": get_item_value(g_id) * give_qty,
			"receive_value": get_item_value(r_id) * receive_qty,
		}
	if economy != null and economy.item_quantity(s_name, g_id) < give_qty:
		return {
			"ok": false,
			"error": "sender_insufficient_items",
			"item_id": g_id,
		}

	_seq += 1
	var offer_id := "offer_%d_%d" % [int(Time.get_unix_time_from_system()), _seq]
	var offer := {
		"offer_id": offer_id,
		"sender": s_name,
		"receiver": r_name,
		"give_item_id": g_id,
		"give_qty": give_qty,
		"give_label": str(ITEM_LABELS.get(g_id, g_id)),
		"receive_item_id": r_id,
		"receive_qty": receive_qty,
		"receive_label": str(ITEM_LABELS.get(r_id, r_id)),
		"location_label": location_label,
		"status": "pending",
		"created_at": Time.get_unix_time_from_system(),
	}
	pending_offers[offer_id] = offer
	return {"ok": true, "offer": offer.duplicate(true)}


func accept_offer(offer_id: String) -> Dictionary:
	if not pending_offers.has(offer_id):
		return {"ok": false, "error": "offer_not_found"}
	var offer: Dictionary = pending_offers[offer_id]
	if str(offer.get("status", "")) != "pending":
		return {"ok": false, "error": "offer_not_pending"}
	if economy == null:
		return {"ok": false, "error": "economy_unavailable"}

	var swap_res: Dictionary = economy.atomic_barter_swap(
		str(offer["sender"]),
		str(offer["receiver"]),
		str(offer["give_item_id"]),
		int(offer["give_qty"]),
		str(offer["receive_item_id"]),
		int(offer["receive_qty"]),
		str(offer["give_label"]),
		str(offer["receive_label"])
	)
	if not bool(swap_res.get("ok", false)):
		offer["status"] = "failed"
		return swap_res

	offer["status"] = "completed"
	offer["completed_at"] = Time.get_unix_time_from_system()
	pending_offers.erase(offer_id)

	var rumor := HubWikiScript.record_barter_rumor(
		str(offer["sender"]),
		str(offer["receiver"]),
		str(offer["give_label"]),
		int(offer["give_qty"]),
		str(offer["receive_label"]),
		int(offer["receive_qty"]),
		str(offer.get("location_label", "Cantina La Perle"))
	)

	var record := offer.duplicate(true)
	record["rumor"] = rumor
	trade_history.append(record)
	while trade_history.size() > 50:
		trade_history.pop_front()

	var out := swap_res.duplicate(true)
	out["offer_id"] = offer_id
	out["rumor"] = rumor
	return out


func negotiate_auto_barter(bot_a: String, bot_b: String, location_label: String = "Cantina La Perle") -> Dictionary:
	## Négociation P2P autonome entre deux Joueurs IA basée sur leurs surplus et déficits.
	if autonomy == null or economy == null:
		return {"ok": false, "error": "services_unavailable"}
	var needs_a: Dictionary = autonomy.evaluate_barter_needs(bot_a)
	var needs_b: Dictionary = autonomy.evaluate_barter_needs(bot_b)
	var surplus_a: Array = needs_a.get("surplus", [])
	var deficits_a: Array = needs_a.get("deficits", [])
	var surplus_b: Array = needs_b.get("surplus", [])

	for def_a in deficits_a:
		var want_id := str(def_a.get("id", ""))
		# Cherche si B a un surplus de want_id
		var b_has_surplus := false
		for sup_b in surplus_b:
			if str(sup_b.get("id", "")) == want_id and int(sup_b.get("qty", 0)) >= 1:
				b_has_surplus = true
				break
		if not b_has_surplus:
			continue

		# Cherche un surplus chez A pour équilibrer la valeur de 1 unité de want_id
		var target_val := get_item_value(want_id)
		for sup_a in surplus_a:
			var give_id := str(sup_a.get("id", ""))
			if give_id == want_id:
				continue
			var unit_val := get_item_value(give_id)
			var give_qty := maxi(1, int(round(float(target_val) / float(maxi(1, unit_val)))))
			if int(sup_a.get("qty", 0)) >= give_qty:
				var off_res := create_offer(bot_a, bot_b, give_id, give_qty, want_id, 1, location_label)
				if bool(off_res.get("ok", false)):
					var oid := str(off_res["offer"]["offer_id"])
					return accept_offer(oid)

	return {"ok": false, "error": "no_complementary_needs"}

