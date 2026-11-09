extends RefCounted
class_name HubGcwBases
## Système SWG Pre-CU : Bases Factionnelles GCW, Tourelles Automatiques,
## Sabotage de Réacteur, Infiltration & Contrôle Territorial Planétaire.

const _HubPaths := preload("res://scripts/hub_paths.gd")

const BASE_TEMPLATES := {
	"base_imperial_outpost": {
		"id": "base_imperial_outpost",
		"faction": "imperial",
		"label": "Avant-Poste Fortifié Impérial",
		"turrets": 4,
		"turret_damage": 160,
		"reactor_hp": 25000,
		"influence_radius_m": 250.0
	},
	"base_rebel_hq": {
		"id": "base_rebel_hq",
		"faction": "rebel",
		"label": "Quartier Général Avancé Rebelle",
		"turrets": 4,
		"turret_damage": 160,
		"reactor_hp": 25000,
		"influence_radius_m": 250.0
	}
}

var sim = null
var faction_svc = null
var economy = null
var next_base_id: int = 1

var bases_by_id: Dictionary = {}


func setup(sim_svc = null, faction_service = null, economy_svc = null) -> void:
	sim = sim_svc
	faction_svc = faction_service
	economy = economy_svc
	_init_seed_bases()


func _init_seed_bases() -> void:
	bases_by_id.clear()
	# Une base impériale au Nord-Est et une base rebelle au Sud-Ouest
	deploy_base("Lt_Kren_Imperial", "base_imperial_outpost", Vector3(180.0, 0.15, -160.0))
	deploy_base("Cap_Vao_Rebel", "base_rebel_hq", Vector3(-190.0, 0.15, 175.0))


func deploy_base(creator: String, template_id: String, pos: Vector3) -> Dictionary:
	if not BASE_TEMPLATES.has(template_id):
		return {"ok": false, "error": "unknown_base_template"}

	var tmpl: Dictionary = BASE_TEMPLATES[template_id]
	var bid := "gcw_base_%d" % next_base_id
	next_base_id += 1

	var entry := {
		"id": bid,
		"template_id": template_id,
		"label": str(tmpl.get("label", "Base GCW")),
		"faction": str(tmpl.get("faction", "imperial")),
		"creator": creator,
		"pos": [pos.x, pos.y, pos.z],
		"turrets_count": int(tmpl.get("turrets", 4)),
		"turret_damage": int(tmpl.get("turret_damage", 160)),
		"turrets_active": true,
		"reactor_hp": int(tmpl.get("reactor_hp", 25000)),
		"reactor_max_hp": int(tmpl.get("reactor_hp", 25000)),
		"is_vulnerable": true,
		"is_overloading": false,
		"overload_timer_s": 0.0,
		"is_destroyed": false,
		"created_at": Time.get_unix_time_from_system()
	}
	bases_by_id[bid] = entry

	if sim != null and sim.has_method("_stream"):
		sim._stream("gcw.base_deployed", "« Une installation militaire (%s) a été érigée par %s à (%.0f, %.0f) ! »" % [entry["label"], creator, pos.x, pos.z], creator, "gcw", entry)

	return {"ok": true, "base": entry.duplicate(true)}


func list_bases() -> Array:
	return bases_by_id.values().duplicate(true)


func get_base(base_id: String) -> Dictionary:
	var bid := base_id.strip_edges()
	if bases_by_id.has(bid):
		return (bases_by_id[bid] as Dictionary).duplicate(true)
	return {}


## Sabotage Étape 1 : Piratage du Terminal de Sécurité (désactive les tourelles)
func hack_security_terminal(player: String, base_id: String) -> Dictionary:
	var b: Dictionary = get_base(base_id)
	if b.is_empty():
		return {"ok": false, "error": "unknown_base"}

	if bool(b.get("is_destroyed", false)):
		return {"ok": false, "error": "base_already_destroyed"}

	bases_by_id[base_id]["turrets_active"] = false

	if sim != null and sim.has_method("_stream"):
		sim._stream("gcw.terminal_hacked", "« ALARME GCW : Le terminal de sécurité de %s a été piraté par %s ! Les tourelles défensives sont hors-ligne. »" % [b["label"], player], player, "gcw", {"base_id": base_id})

	return {
		"ok": true,
		"player": player,
		"base_id": base_id,
		"turrets_active": false,
		"message": "Piratage réussi ! Les tourelles de défense ont été désactivées."
	}


## Sabotage Étape 2 : Déclenchement de la Surcharge du Réacteur
func overload_reactor(player: String, base_id: String) -> Dictionary:
	var b: Dictionary = get_base(base_id)
	if b.is_empty():
		return {"ok": false, "error": "unknown_base"}

	if bool(b.get("is_destroyed", false)):
		return {"ok": false, "error": "base_already_destroyed"}

	bases_by_id[base_id]["is_overloading"] = true
	bases_by_id[base_id]["overload_timer_s"] = 300.0 # 5 minutes

	if sim != null and sim.has_method("_stream"):
		sim._stream("gcw.reactor_overload", "« ALERTE CRITIQUE : Surcharge du cœur de réacteur en cours sur %s ! Détonation imminente dans 5 minutes ! »" % b["label"], player, "gcw", {"base_id": base_id})

	return {
		"ok": true,
		"player": player,
		"base_id": base_id,
		"overload_timer_s": 300.0,
		"message": "Surcharge critique enclenchée ! Défendez le réacteur pendant le compte à rebours."
	}


## Sabotage Étape 3 : Destruction finale de la base (ou détonation immédiate pour test/combat)
func detonate_base(player: String, base_id: String) -> Dictionary:
	var b: Dictionary = get_base(base_id)
	if b.is_empty():
		return {"ok": false, "error": "unknown_base"}

	bases_by_id[base_id]["is_overloading"] = false
	bases_by_id[base_id]["is_destroyed"] = true
	bases_by_id[base_id]["turrets_active"] = false
	bases_by_id[base_id]["reactor_hp"] = 0

	var gcw_points := 5000
	if faction_svc != null and faction_svc.has_method("award_faction_points"):
		faction_svc.award_faction_points(player, gcw_points)

	if sim != null and sim.has_method("_stream"):
		sim._stream("gcw.base_destroyed", "« VICTOIRE GCW : L'installation ennemie %s a été anéantie dans une gigantesque explosion par %s (+5000 pts de Faction) ! »" % [b["label"], player], player, "gcw", {"base_id": base_id})

	return {
		"ok": true,
		"player": player,
		"base_id": base_id,
		"is_destroyed": true,
		"gcw_points_awarded": gcw_points,
		"message": "La base militaire a été entièrement détruite !"
	}

