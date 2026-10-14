extends RefCounted
class_name HubSimViews
## Formatage et sérialisation des états d'entités, filtres WS et payloads réseau — Ticket 2.2.

const ZONE := "scrapaltai"
const HubActivityScript := preload("res://scripts/hub_activity.gd")


static func entity_list(entities: Dictionary, slim: bool = false, economy = null) -> Array:
	var out: Array = []
	for eid in entities.keys():
		var e: Dictionary = entities[eid]
		if str(e.get("kind", "")) in ["npc", "beast"] and not bool(e.get("active", true)):
			continue
		var p: Vector3 = e["pos"]
		if slim:
			var slim_row := {
				"id": int(e["oid"]),
				"entity_key": str(e["eid"]),
				"kind": str(e["kind"]),
				"name": str(e["name"]),
				"pos": [snappedf(p.x, 0.01), snappedf(p.y, 0.01), snappedf(p.z, 0.01)],
				"is_bot": bool(e.get("is_bot", false)),
			}
			var kind := str(e.get("kind", ""))
			if kind == "player":
				# C2 — activité lisible (humain = IA), pas de tag espèce
				var act: Dictionary = HubActivityScript.describe_with_economy(e, economy)
				var status := str(act.get("status", "idle"))
				var activity := str(act.get("activity", "")).strip_edges()
				slim_row["status"] = status
				if activity != "":
					slim_row["activity"] = activity
				var g := str(act.get("goal", "")).strip_edges()
				if g != "" and status != "idle":
					slim_row["goal"] = g
			elif kind == "beast":
				var bg := str(e.get("goal", "")).strip_edges()
				if not bg.is_empty() and bg != "wander":
					slim_row["goal"] = bg
				if bool(e.get("is_boss", false)):
					slim_row["is_boss"] = true
			out.append(slim_row)
		else:
			var row := {
				"id": int(e["oid"]),
				"entity_key": str(e["eid"]),
				"kind": str(e["kind"]),
				"name": str(e["name"]),
				"pos": [p.x, p.y, p.z],
				"source": "prime_hub",
				"goal": str(e.get("goal", "")),
				"play_mode": str(e.get("play_mode", "")),
				"quest_id": str(e.get("quest_id", "")),
				"is_bot": bool(e.get("is_bot", false)),
				"life_phase": str(e.get("life_phase", "")),
			}
			if str(e.get("kind", "")) == "player":
				var act2: Dictionary = HubActivityScript.describe_with_economy(e, economy)
				row["status"] = str(act2.get("status", "idle"))
				row["activity"] = str(act2.get("activity", ""))
			var amb := str(e.get("ambient", "")).strip_edges()
			if not amb.is_empty():
				row["ambient"] = amb
			if bool(e.get("is_boss", false)):
				row["is_boss"] = true
			out.append(row)
	return out


static func bots_payload(entities: Dictionary) -> Array:
	var out: Array = []
	for eid in entities.keys():
		var e: Dictionary = entities[eid]
		if not bool(e.get("is_bot", false)):
			continue
		var p: Vector3 = e["pos"]
		var t: Vector3 = e["target"]
		out.append({
			"id": int(e["oid"]),
			"entity_key": str(e["eid"]),
			"name": str(e["name"]),
			"pos": [p.x, p.y, p.z],
			"target": [t.x, t.y, t.z],
			"goal": str(e.get("goal", "")),
			"play_mode": str(e.get("play_mode", "")),
			"quest_id": str(e.get("quest_id", "")),
			"admin_level": int(e.get("admin_level", 0)),
			"account_login": str(e.get("account_login", "")),
			"agent_id": str(e.get("agent_id", "")),
			"linked_studio_agent_id": str(e.get("linked_studio_agent_id", "")),
			"linked_studio_display": str(e.get("linked_studio_display", "")),
		})
	return out


static func online_players(entities: Dictionary) -> Array:
	var out: Array = []
	for eid in entities.keys():
		var e: Dictionary = entities[eid]
		if str(e.get("kind", "")) != "player" or bool(e.get("is_bot", false)):
			continue
		out.append({"id": int(e["oid"]), "name": str(e["name"])})
	return out


static func bot_count(entities: Dictionary) -> int:
	var n := 0
	for eid in entities.keys():
		if bool(entities[eid].get("is_bot", false)):
			n += 1
	return n


static func npc_count(entities: Dictionary) -> int:
	var n := 0
	for eid in entities.keys():
		var e: Dictionary = entities[eid]
		if str(e.get("kind", "")) == "npc" and bool(e.get("active", true)):
			n += 1
	return n


static func zone_state_payload(sim, your_oid: int) -> Dictionary:
	var online := online_players(sim.entities)
	var collision_blocks: int = sim.collision.blocks.size() if (sim != null and sim.collision != null) else 0
	var eco = sim.economy if (sim != null and "economy" in sim) else null
	var payload := {
		"type": "zone_state",
		"proto": "lbg-ws/2",
		"zone": ZONE,
		"tick": sim.tick if sim != null else 0,
		"server_time_ms": int(Time.get_unix_time_from_system() * 1000.0),
		"entities": entity_list(sim.entities, true, eco),
		"your_character_id": your_oid,
		"session_policy": "prime_hub_g4u",
		"collision_blocks": collision_blocks,
		"online_players": online,
		"online_count": online.size(),
		"bot_count": bot_count(sim.entities),
		"npc_count": npc_count(sim.entities),
		"beast_count": sim.beast_count() if (sim != null and sim.has_method("beast_count")) else 0,
	}
	var eid := "player:%d" % your_oid
	if sim != null and sim.entities.has(eid):
		var p: Vector3 = sim.entities[eid]["pos"]
		payload["position"] = [p.x, p.y, p.z]
	return payload


static func enter_world_payload(sim, your_oid: int) -> Dictionary:
	if sim != null:
		sim.ensure_human(your_oid, "Voyageur")
	var base := zone_state_payload(sim, your_oid)
	base["type"] = "enter_world"
	var eid := "player:%d" % your_oid
	if sim != null and sim.entities.has(eid):
		var p: Vector3 = sim.entities[eid]["pos"]
		base["position"] = [p.x, p.y, p.z]
	return base
