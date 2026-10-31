extends "res://scripts/adapters/agent_environment_adapter.gd"
class_name GodotHubAdapter
## Implémentation concrète de l'adaptateur d'environnement pour le Hub Godot (Ticket 2.1 — O3).
##
## Connecte la boucle décisionnelle des Joueurs IA à la simulation Lost Heaven,
## à l'économie SQLite, aux POIs et aux dials de présence sans couplage dur.

var sim = null
var economy = null
var pois: Dictionary = {}
var dials: Dictionary = {}
var perception_radius: float = 60.0
var partner_pairs: Dictionary = {
	"nix": "lia",
	"lia": "nix",
	"mira": "jax",
	"jax": "mira",
	"soren": "vael",
	"vael": "soren"
}


func register_partner_pair(bot_a: String, bot_b: String) -> void:
	partner_pairs[bot_a.to_lower()] = bot_b.to_lower()
	partner_pairs[bot_b.to_lower()] = bot_a.to_lower()


func get_partner_id(bot_id: String) -> String:
	var clean := bot_id.replace("player:", "").to_lower()
	return str(partner_pairs.get(clean, ""))


func setup(sim_node, economy_svc = null, pois_map: Dictionary = {}, dials_map: Dictionary = {}, p_radius: float = 60.0) -> void:
	sim = sim_node
	economy = economy_svc
	pois = pois_map
	dials = dials_map
	perception_radius = p_radius


func _resolve_entity(bot_id: String) -> Dictionary:
	if sim == null or not (sim.entities is Dictionary):
		return {}
	# Recherche directe par clef EID
	if sim.entities.has(bot_id):
		return sim.entities[bot_id]
	var prefixed := "player:" + bot_id
	if sim.entities.has(prefixed):
		return sim.entities[prefixed]
	# Recherche par champ name
	for eid in sim.entities.keys():
		var e: Dictionary = sim.entities[eid]
		if str(e.get("name", "")).to_lower() == bot_id.to_lower():
			return e
	return {}


func get_observation(bot_id: String) -> Dictionary:
	var ent := _resolve_entity(bot_id)
	if ent.is_empty():
		return make_observation(bot_id, Vector3.ZERO, "scrapaltai", 0, 0, [], [], [], {}, [])

	var pos: Vector3 = ent.get("pos", Vector3.ZERO)
	var bot_name: String = str(ent.get("name", bot_id))
	var zone: String = str(ent.get("zone", "scrapaltai"))
	var health: int = int(ent.get("health", 100))

	# 1. Entités perceptibles dans le rayon de vision
	var nearby_entities: Array = []
	if sim != null and sim.entities is Dictionary:
		for other_eid in sim.entities.keys():
			var other: Dictionary = sim.entities[other_eid]
			if str(other.get("eid", "")) == str(ent.get("eid", "")):
				continue
			var other_pos: Vector3 = other.get("pos", Vector3.ZERO)
			var d := pos.distance_to(other_pos)
			if d <= perception_radius:
				nearby_entities.append({
					"eid": str(other.get("eid", other_eid)),
					"name": str(other.get("name", "")),
					"distance": round(d * 10.0) / 10.0,
					"is_bot": bool(other.get("is_bot", false)),
					"is_boss": bool(other.get("is_boss", false)),
					"is_beast": bool(other.get("is_beast", false)),
				})

	# 2. Points d'intérêt (POIs) remarquables
	var nearby_pois: Array = []
	for poi_key in pois.keys():
		var poi_pos_val = pois[poi_key]
		if poi_pos_val is Vector3:
			var pd := pos.distance_to(poi_pos_val)
			if pd <= perception_radius * 2.5:
				nearby_pois.append({
					"id": str(poi_key),
					"position": [poi_pos_val.x, poi_pos_val.y, poi_pos_val.z],
					"distance": round(pd * 10.0) / 10.0
				})

	# 3. État économique (inventaire et crédits)
	var credits := 0
	var inventory_items: Array = []
	if economy != null and economy.has_method("inventory"):
		var inv_data: Dictionary = economy.inventory(bot_name)
		credits = int(inv_data.get("credits", 0))
		inventory_items = inv_data.get("items", [])

	# 4. Événements de zone
	var active_events: Array = []
	if sim != null and sim.has_method("world_events_payload"):
		active_events = sim.world_events_payload()

	# 5. Dials de présence persona
	var bot_dials: Dictionary = dials.get(bot_name, {})

	# 6. Contexte d'équipe & partenaire d'escorte
	var team_context: Dictionary = {}
	var partner_id := get_partner_id(bot_name)
	if not partner_id.is_empty():
		var p_ent := _resolve_entity(partner_id)
		if not p_ent.is_empty():
			var p_pos: Vector3 = p_ent.get("pos", Vector3.ZERO)
			var p_dist := pos.distance_to(p_pos)
			var p_eid := str(p_ent.get("eid", ""))
			var threatened := false
			var threat_key := ""
			if sim != null and sim.entities is Dictionary:
				for eid in sim.entities.keys():
					var other: Dictionary = sim.entities[eid]
					if str(other.get("kind", "")) == "beast" and bool(other.get("active", true)):
						if str(other.get("aggro_eid", "")) == p_eid:
							threatened = true
							threat_key = eid
							break
			team_context = {
				"has_partner": true,
				"partner_id": partner_id,
				"partner_name": str(p_ent.get("name", partner_id)),
				"partner_pos": [p_pos.x, p_pos.y, p_pos.z],
				"partner_pos_v3": p_pos,
				"partner_distance": round(p_dist * 10.0) / 10.0,
				"partner_under_threat": threatened,
				"threat_eid": threat_key
			}

	var obs := make_observation(
		bot_id,
		pos,
		zone,
		health,
		credits,
		nearby_entities,
		nearby_pois,
		active_events,
		bot_dials,
		inventory_items,
		team_context
	)
	observation_updated.emit(bot_id, obs)
	return obs


func perform_action(bot_id: String, action: Dictionary) -> Dictionary:
	var ent := _resolve_entity(bot_id)
	if ent.is_empty():
		return {
			"ok": false,
			"agent_id": bot_id,
			"error": "entity_not_found",
			"timestamp": Time.get_unix_time_from_system()
		}

	var act_type := str(action.get("type", ACTION_TYPE_IDLE))
	var bot_name: String = str(ent.get("name", bot_id))
	var result := {"ok": true, "action": act_type, "agent_id": bot_id}

	match act_type:
		ACTION_TYPE_MOVE:
			var target_pos: Vector3 = Vector3.ZERO
			if action.has("target_v3") and action["target_v3"] is Vector3:
				target_pos = action["target_v3"]
			elif action.has("target") and action["target"] is Array and action["target"].size() == 3:
				target_pos = Vector3(action["target"][0], action["target"][1], action["target"][2])
			elif action.has("poi_id") and pois.has(str(action["poi_id"])):
				target_pos = pois[str(action["poi_id"])]
			else:
				return {"ok": false, "action": act_type, "error": "invalid_move_target"}

			ent["target"] = target_pos
			ent["moving"] = true
			if action.has("goal"):
				ent["goal"] = str(action["goal"])
			if action.has("play_mode"):
				ent["play_mode"] = str(action["play_mode"])
			result["new_target"] = [target_pos.x, target_pos.y, target_pos.z]

		ACTION_TYPE_SAY:
			var msg := str(action.get("message", action.get("text", ""))).strip_edges()
			if msg.is_empty():
				return {"ok": false, "action": act_type, "error": "empty_message"}
			ent["ambient"] = msg
			if sim != null and sim.has_method("broadcast_say"):
				sim.broadcast_say(bot_name, msg)
			result["message"] = msg

		ACTION_TYPE_EMOTE:
			var emote := str(action.get("emote", "nod")).strip_edges()
			ent["emote"] = emote
			result["emote"] = emote

		ACTION_TYPE_INTERACT:
			var poi_id := str(action.get("poi_id", ""))
			if poi_id.is_empty() or not pois.has(poi_id):
				return {"ok": false, "action": act_type, "error": "poi_not_found"}
			result["poi_id"] = poi_id
			# Si l'économie est disponible, simule l'interaction POI
			if economy != null:
				economy.log_session_event(bot_name, "interact", "Interaction avec POI %s" % poi_id, {"poi": poi_id})

		ACTION_TYPE_TRADE:
			var vendor_id := str(action.get("vendor_id", "npc:core3_barman_jax"))
			var sku_id := str(action.get("sku_id", ""))
			var offer_price := int(action.get("offer_price", 0))
			if economy != null and economy.has_method("trade_offer"):
				var trade_res: Dictionary = economy.trade_offer(bot_name, vendor_id, sku_id, offer_price)
				result["trade_result"] = trade_res
				result["ok"] = bool(trade_res.get("ok", false))
			else:
				return {"ok": false, "action": act_type, "error": "economy_unavailable"}

		ACTION_TYPE_CRAFT:
			var recipe_id := str(action.get("recipe_id", ""))
			if economy != null and economy.has_method("craft_combine"):
				var craft_res: Dictionary = economy.craft_combine(bot_name, recipe_id)
				result["craft_result"] = craft_res
				result["ok"] = bool(craft_res.get("ok", false))
			else:
				return {"ok": false, "action": act_type, "error": "economy_unavailable"}

		ACTION_TYPE_IDLE:
			ent["moving"] = false
			ent["target"] = ent.get("pos", Vector3.ZERO)
			result["idle"] = true

		ACTION_TYPE_FORMATION_FOLLOW:
			var target_partner := str(action.get("target_partner_id", action.get("partner_id", get_partner_id(bot_name))))
			var p_ent := _resolve_entity(target_partner)
			if p_ent.is_empty():
				return {"ok": false, "action": act_type, "error": "partner_not_found"}
			var p_pos: Vector3 = p_ent.get("pos", Vector3.ZERO)
			var offset: Vector3 = Vector3(-3.0, 0.0, -3.0)
			if action.has("formation_offset") and action["formation_offset"] is Vector3:
				offset = action["formation_offset"]
			elif action.has("offset") and action["offset"] is Array and action["offset"].size() == 3:
				offset = Vector3(action["offset"][0], action["offset"][1], action["offset"][2])

			var target_v3 := p_pos + offset
			if sim != null and sim.has_method("_walkable_xz"):
				var wz: Vector2 = sim._walkable_xz(target_v3.x, target_v3.z)
				target_v3 = Vector3(wz.x, p_pos.y, wz.y)

			ent["target"] = target_v3
			ent["moving"] = true
			ent["goal"] = "formation_escort"
			ent["play_mode"] = "escort_follower"
			ent["partner_id"] = target_partner
			result["partner_id"] = target_partner
			result["formation_target"] = [target_v3.x, target_v3.y, target_v3.z]

		ACTION_TYPE_COVER_TARGET:
			var threat_id := str(action.get("threat_eid", action.get("threat_id", "")))
			var target_partner := str(action.get("target_partner_id", action.get("partner_id", get_partner_id(bot_name))))
			var p_ent := _resolve_entity(target_partner)
			var t_ent := _resolve_entity(threat_id)
			if p_ent.is_empty():
				return {"ok": false, "action": act_type, "error": "partner_not_found"}

			var p_pos: Vector3 = p_ent.get("pos", Vector3.ZERO)
			var cover_pos := p_pos
			if not t_ent.is_empty():
				var t_pos: Vector3 = t_ent.get("pos", Vector3.ZERO)
				cover_pos = p_pos.lerp(t_pos, 0.45)
			else:
				cover_pos = p_pos + Vector3(2.0, 0.0, 2.0)

			if sim != null and sim.has_method("_walkable_xz"):
				var wz2: Vector2 = sim._walkable_xz(cover_pos.x, cover_pos.z)
				cover_pos = Vector3(wz2.x, p_pos.y, wz2.y)

			ent["target"] = cover_pos
			ent["moving"] = true
			ent["goal"] = "cover_partner"
			ent["play_mode"] = "defense"
			ent["ambient"] = "Couverture tactique : je couvre les arrières de %s !" % str(p_ent.get("name", target_partner))
			result["threat_eid"] = threat_id
			result["cover_pos"] = [cover_pos.x, cover_pos.y, cover_pos.z]

		ACTION_TYPE_TACTICAL_RETREAT:
			var shelter_poi := str(action.get("shelter_poi", "cantina"))
			var shelter_pos: Vector3 = pois.get(shelter_poi, Vector3(5028.3, 0.15, -784.1))
			ent["target"] = shelter_pos
			ent["moving"] = true
			ent["goal"] = "tactical_retreat"
			ent["play_mode"] = "retreat"
			result["shelter_poi"] = shelter_poi
			result["retreat_target"] = [shelter_pos.x, shelter_pos.y, shelter_pos.z]

		_:
			return {"ok": false, "action": act_type, "error": "unknown_action_type"}

	result["timestamp"] = Time.get_unix_time_from_system()
	action_completed.emit(bot_id, act_type, result)
	return result
