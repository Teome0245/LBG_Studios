extends SceneTree
## Self-test C2 — activité joueur (status + label) humain = IA.
##
##   packages/prime-hub/tools/godot --headless --path packages/prime-hub \
##     -s res://tools/activity_selftest.gd

const HubActivityScript := preload("res://scripts/hub_activity.gd")
const HubSimViewsScript := preload("res://scripts/hub_sim_views.gd")


func _init() -> void:
	var escort := HubActivityScript.describe({
		"kind": "player",
		"name": "Nix",
		"goal": "companion_escort",
		"play_mode": "hub",
		"quest_id": "",
		"is_bot": true,
	})
	assert(str(escort.get("status")) == "busy", str(escort))
	assert(str(escort.get("activity")) == "escorte", str(escort))

	var quest := HubActivityScript.describe({
		"kind": "player",
		"name": "Mira",
		"goal": "quest:lh_escort_gate_clinic:pickup",
		"play_mode": "quest",
		"quest_id": "lh_escort_gate_clinic",
		"is_bot": true,
	})
	assert(str(quest.get("status")) == "quest", str(quest))
	assert(str(quest.get("activity")) != "", str(quest))

	var idle := HubActivityScript.describe({
		"kind": "player",
		"name": "Voyageur",
		"goal": "",
		"play_mode": "",
		"quest_id": "",
		"is_bot": false,
	})
	assert(str(idle.get("status")) == "idle", str(idle))
	assert(str(idle.get("activity")) == "", str(idle))

	# Slim zone_state : joueurs exposent status/activity (pas seulement les bêtes)
	var entities := {
		"player:Nix": {
			"eid": "player:Nix",
			"oid": 900002,
			"kind": "player",
			"name": "Nix",
			"pos": Vector3(4000, 0.15, -1000),
			"goal": "companion_escort",
			"play_mode": "hub",
			"quest_id": "",
			"is_bot": true,
			"active": true,
		},
		"player:1": {
			"eid": "player:1",
			"oid": 1,
			"kind": "player",
			"name": "Voyageur",
			"pos": Vector3(4010, 0.15, -1000),
			"goal": "",
			"play_mode": "",
			"quest_id": "",
			"is_bot": false,
			"active": true,
		},
	}
	var list: Array = HubSimViewsScript.entity_list(entities, true, null)
	assert(list.size() == 2, "entities=%s" % str(list.size()))
	var nix_row = null
	var hum_row = null
	for row in list:
		if str(row.get("name")) == "Nix":
			nix_row = row
		elif str(row.get("name")) == "Voyageur":
			hum_row = row
	assert(nix_row != null and hum_row != null, str(list))
	assert(str(nix_row.get("activity")) == "escorte", str(nix_row))
	assert(str(nix_row.get("status")) == "busy", str(nix_row))
	assert(str(hum_row.get("status")) == "idle", str(hum_row))
	# Homogène : mêmes clés status pour humain et IA
	assert(hum_row.has("status") and nix_row.has("status"), "status manquant")

	print("ACTIVITY_SELFTEST_OK: escort+quest+idle+slim")
	quit(0)
