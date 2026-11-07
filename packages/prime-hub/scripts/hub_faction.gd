extends RefCounted
class_name HubFaction
## Système Serveur SWG Pre-CU de Factions & GCW (Guerre Civile Galactique)
## Gère l'alignement joueur (Neutre, Impérial, Rebelle), les statuts militaires,
## les points de faction, les règles de combat PvP (Special Forces) et les recruteurs.

var sim = null
var db = null
var economy = null

var player_factions: Dictionary = {}

const DEFAULT_RECRUITERS: Array = [
	{
		"id": "recruiter_imperial_kren",
		"name": "Lieutenant Kren",
		"title": "Recruteur des Forces Impériales",
		"faction": "imperial",
		"position": Vector3(5380.0, 0.15, -730.0), # Porte Est de Lost Heaven
		"available_ranks": [
			{"name": "Soldat de Deuxième Classe", "cost_fp": 100},
			{"name": "Caporal Impérial", "cost_fp": 500},
			{"name": "Sergent de Patrouille", "cost_fp": 1200},
			{"name": "Sous-Lieutenant", "cost_fp": 2500}
		]
	},
	{
		"id": "recruiter_rebel_vao",
		"name": "Capitaine Vao",
		"title": "Recruteur de l'Alliance Rebelle",
		"faction": "rebel",
		"position": Vector3(4520.0, 0.15, -760.0), # Avant-poste des dunes Ouest
		"available_ranks": [
			{"name": "Recrue Volontaire", "cost_fp": 100},
			{"name": "Éclaireur de l'Alliance", "cost_fp": 500},
			{"name": "Caporal Commando", "cost_fp": 1200},
			{"name": "Lieutenant Rebelle", "cost_fp": 2500}
		]
	}
]


func setup(sim_svc = null, db_svc = null, economy_svc = null) -> void:
	sim = sim_svc
	db = db_svc
	economy = economy_svc


func get_faction_data(player: String) -> Dictionary:
	var p := player.strip_edges()
	if not player_factions.has(p):
		player_factions[p] = {
			"faction": "neutral",
			"status": "civilian",
			"points": {
				"imperial": 200,
				"rebel": 150
			},
			"rank": "Citoyen Neutre",
			"kills": 0
		}
	return (player_factions[p] as Dictionary).duplicate(true)


func enlist(player: String, faction_name: String) -> Dictionary:
	var p := player.strip_edges()
	var f := faction_name.strip_edges().to_lower()
	if f != "imperial" and f != "rebel":
		return {"ok": false, "error": "invalid_faction", "allowed": ["imperial", "rebel"]}
	
	var data: Dictionary = get_faction_data(p)
	data["faction"] = f
	data["status"] = "on_leave"
	data["rank"] = "Soldat Recrue" if f == "imperial" else "Volontaire de l'Alliance"
	player_factions[p] = data
	return {"ok": true, "player": p, "faction": f, "status": "on_leave", "rank": data["rank"]}


func declare_special_forces(player: String) -> Dictionary:
	var p := player.strip_edges()
	var data: Dictionary = get_faction_data(p)
	if str(data.get("faction", "neutral")) == "neutral":
		return {"ok": false, "error": "neutral_cannot_go_sf"}
	data["status"] = "special_forces"
	player_factions[p] = data
	return {"ok": true, "player": p, "status": "special_forces", "pvp_overt": true}


func go_on_leave(player: String) -> Dictionary:
	var p := player.strip_edges()
	var data: Dictionary = get_faction_data(p)
	if str(data.get("faction", "neutral")) == "neutral":
		return {"ok": false, "error": "neutral_player"}
	data["status"] = "on_leave"
	player_factions[p] = data
	return {"ok": true, "player": p, "status": "on_leave", "pvp_overt": false}


func resign_to_civilian(player: String) -> Dictionary:
	var p := player.strip_edges()
	var data: Dictionary = get_faction_data(p)
	data["faction"] = "neutral"
	data["status"] = "civilian"
	data["rank"] = "Citoyen Neutre"
	player_factions[p] = data
	return {"ok": true, "player": p, "faction": "neutral", "status": "civilian"}


func add_faction_points(player: String, faction_name: String, amount: int) -> Dictionary:
	var p := player.strip_edges()
	var f := faction_name.strip_edges().to_lower()
	var data: Dictionary = get_faction_data(p)
	var pts: Dictionary = data.get("points", {})
	var current: int = int(pts.get(f, 0))
	var new_pts := maxi(0, current + amount)
	pts[f] = new_pts
	data["points"] = pts
	player_factions[p] = data
	return {"ok": true, "player": p, "faction": f, "points": new_pts}


func is_enemy(player_a: String, player_b: String) -> bool:
	var da: Dictionary = get_faction_data(player_a)
	var db_data: Dictionary = get_faction_data(player_b)

	var fa: String = str(da.get("faction", "neutral"))
	var fb: String = str(db_data.get("faction", "neutral"))

	if fa == "neutral" or fb == "neutral" or fa == fb:
		return false

	var sa: String = str(da.get("status", "civilian"))
	var sb: String = str(db_data.get("status", "civilian"))

	# En GCW SWG Pre-CU : deux belligérants opposés s'attaquent s'ils sont tous deux Special Forces
	if sa == "special_forces" and sb == "special_forces":
		return true

	return false


func list_recruiters() -> Array:
	return DEFAULT_RECRUITERS.duplicate(true)

