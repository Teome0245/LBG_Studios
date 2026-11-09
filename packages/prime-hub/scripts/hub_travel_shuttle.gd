extends RefCounted
class_name HubTravelShuttle
## Système SWG Pre-CU : Spatioports, Rotation Réelle de Navettes Galactiques,
## Billetterie de Transport, Embarquement & Voyages Inter-Zones.

const _HubPaths := preload("res://scripts/hub_paths.gd")

const CYCLE_DURATIONS := {
	"boarding": 60.0,
	"takeoff": 15.0,
	"in_orbit": 90.0,
	"landing": 15.0
}

const TRAVEL_ROUTES := {
	"lh_eisley": {
		"id": "lh_eisley",
		"destination": "Mos Eisley (Spatioport Principal)",
		"planet": "Tatooine",
		"cost_credits": 100,
		"arrival_coords": [3520.0, 0.15, -4800.0]
	},
	"lh_theed": {
		"id": "lh_theed",
		"destination": "Theed (Capitale Royale)",
		"planet": "Naboo",
		"cost_credits": 350,
		"arrival_coords": [-4850.0, 0.15, 4120.0]
	},
	"lh_coronet": {
		"id": "lh_coronet",
		"destination": "Coronet (Cité Marchande)",
		"planet": "Corellia",
		"cost_credits": 350,
		"arrival_coords": [120.0, 0.15, -3150.0]
	},
	"lh_mining_outpost": {
		"id": "lh_mining_outpost",
		"destination": "Avant-Poste Minier de Scrapaltai",
		"planet": "Tatooine",
		"cost_credits": 50,
		"arrival_coords": [1850.0, 0.15, -1450.0]
	}
}

var sim = null
var economy = null

var current_phase: String = "boarding"
var phase_start_ts: float = 0.0
var boarded_passengers: Dictionary = {} # player_name -> route_id


func setup(sim_svc = null, economy_svc = null) -> void:
	sim = sim_svc
	economy = economy_svc
	phase_start_ts = Time.get_unix_time_from_system()


func get_shuttle_status() -> Dictionary:
	_update_cycle()
	var elapsed := float(Time.get_unix_time_from_system() - phase_start_ts)
	var max_dur: float = CYCLE_DURATIONS.get(current_phase, 60.0)
	var remaining := maxf(0.0, max_dur - elapsed)

	return {
		"ok": true,
		"current_phase": current_phase, # boarding, takeoff, in_orbit, landing
		"is_docked": (current_phase == "boarding"),
		"seconds_to_departure": snappedf(remaining if current_phase == "boarding" else (remaining + CYCLE_DURATIONS["boarding"]), 0.1),
		"phase_time_left_s": snappedf(remaining, 0.1),
		"passenger_count": boarded_passengers.size()
	}


func _update_cycle() -> void:
	var now := Time.get_unix_time_from_system()
	var elapsed := float(now - phase_start_ts)
	var dur: float = CYCLE_DURATIONS.get(current_phase, 60.0)

	if elapsed >= dur:
		phase_start_ts = now
		match current_phase:
			"boarding":
				current_phase = "takeoff"
				_process_takeoff()
			"takeoff":
				current_phase = "in_orbit"
			"in_orbit":
				current_phase = "landing"
			"landing":
				current_phase = "boarding"
				_process_docking()


func _process_takeoff() -> void:
	if sim != null and sim.has_method("_stream"):
		sim._stream("shuttle.takeoff", "« La Navette de transport Lambda met plein gaz et s'élève vers l'orbite avec %d passagers à bord ! »" % boarded_passengers.size(), "Spatioport", "travel", {"passengers": boarded_passengers.keys()})


func _process_docking() -> void:
	boarded_passengers.clear()
	if sim != null and sim.has_method("_stream"):
		sim._stream("shuttle.docked", "« La Navette spatiale vient d'atterrir sur la piste de Lost Heaven. Embarquement ouvert pour 60 secondes ! »", "Spatioport", "travel", {})


func list_routes() -> Array:
	return TRAVEL_ROUTES.values().duplicate(true)


func purchase_ticket(player: String, route_id: String) -> Dictionary:
	if not TRAVEL_ROUTES.has(route_id):
		return {"ok": false, "error": "unknown_route"}

	var r: Dictionary = TRAVEL_ROUTES[route_id]
	var cost := int(r.get("cost_credits", 100))

	if economy != null:
		var st: Dictionary = economy.status(player) if economy.has_method("status") else {}
		var creds := int(st.get("credits", 1000))
		if creds < cost:
			return {"ok": false, "error": "insufficient_credits", "cost": cost, "credits": creds}
		# Débit
		if economy.has_method("_consume_credits"):
			economy._consume_credits(player, cost)

	return {
		"ok": true,
		"player": player,
		"route": r.duplicate(true),
		"ticket_id": "ticket_%s_%d" % [route_id, randi_range(1000, 9999)],
		"cost_paid": cost
	}


func board_shuttle(player: String, route_id: String) -> Dictionary:
	_update_cycle()
	if current_phase != "boarding":
		return {
			"ok": false,
			"error": "shuttle_not_boarding",
			"current_phase": current_phase,
			"message": "La navette n'est pas à quai. Attends son prochain atterrissage."
		}

	if not TRAVEL_ROUTES.has(route_id):
		return {"ok": false, "error": "unknown_route"}

	boarded_passengers[player] = route_id
	var r: Dictionary = TRAVEL_ROUTES[route_id]

	return {
		"ok": true,
		"player": player,
		"route": r.duplicate(true),
		"message": "Vous avez embarqué à bord de la navette à destination de : %s." % r["destination"]
	}

