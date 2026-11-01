extends RefCounted
class_name HubCrafting
## Ticket 2.2 (O2 Phase 3) — Métier de Récupérateur : Établis d'Assemblage Mécatronique & Recettes de Terrain.
## Autorité serveur stricte : validation de proximité d'ancrage CAO `craft`, vérification des ingrédients
## et snap en posture Triplon `craft` sur l'établi. Zéro mutation libre LLM.

const _HubPaths := preload("res://scripts/hub_paths.gd")

var economy = null
var collision = null
var schematics_by_id: Dictionary = {}
var active_craft_states: Dictionary = {}  # player -> {schematic_id, anchor_id, snap_pos, posture, duration_sec, started_at}


func setup(economy_svc, collision_svc = null) -> void:
	economy = economy_svc
	collision = collision_svc
	reload_schematics()


func reload_schematics(custom_path: String = "") -> void:
	schematics_by_id.clear()
	var path := custom_path
	if path.is_empty():
		path = _HubPaths.data_file("craft/schematics_scrap.json")
	var raw: Variant = _HubPaths.read_json(path)
	if typeof(raw) != TYPE_DICTIONARY:
		return
	var arr: Variant = raw.get("schematics", [])
	if typeof(arr) != TYPE_ARRAY:
		return
	for sc in arr:
		if typeof(sc) == TYPE_DICTIONARY and not str(sc.get("id", "")).is_empty():
			schematics_by_id[str(sc["id"])] = (sc as Dictionary).duplicate(true)


func list_schematics() -> Array:
	var out: Array = []
	for k in schematics_by_id.keys():
		out.append((schematics_by_id[k] as Dictionary).duplicate(true))
	return out


func get_schematic(schematic_id: String) -> Dictionary:
	var sid := schematic_id.strip_edges()
	if schematics_by_id.has(sid):
		return (schematics_by_id[sid] as Dictionary).duplicate(true)
	return {}


func assemble_at_bench(
	player: String,
	schematic_id: String,
	entity_pos: Vector3 = Vector3.ZERO,
	max_bench_dist: float = 8.0
) -> Dictionary:
	var p_name := player.strip_edges()
	if p_name.is_empty():
		p_name = "Voyageur"
	var sid := schematic_id.strip_edges()
	if not schematics_by_id.has(sid):
		return {
			"ok": false,
			"error": "unknown_schematic",
			"schematic_id": sid,
		}
	if economy == null:
		return {
			"ok": false,
			"error": "economy_unavailable",
		}

	var sc: Dictionary = schematics_by_id[sid]
	var requires_bench := bool(sc.get("requires_bench", true))
	var bench_info := {"near": false, "anchor": {}, "distance": INF}

	if requires_bench:
		if collision == null or not collision.has_method("is_near_craft_bench"):
			return {
				"ok": false,
				"error": "collision_unavailable",
			}
		bench_info = collision.is_near_craft_bench(entity_pos, max_bench_dist)
		if not bool(bench_info.get("near", false)):
			return {
				"ok": false,
				"error": "not_near_craft_bench",
				"hint": "Approche-toi d'un établi d'assemblage mécatronique (ex. Hangar Dépôt Nord).",
				"schematic_id": sid,
				"distance": bench_info.get("distance", INF),
			}

	# Délègue la vérification déterministe de compétence + consommation d'ingrédients à HubEconomy
	var craft_res: Dictionary = economy.craft_combine(p_name, sid)
	if not bool(craft_res.get("ok", false)):
		return craft_res

	var anchor: Dictionary = bench_info.get("anchor", {}) if typeof(bench_info.get("anchor")) == TYPE_DICTIONARY else {}
	var snap_pos: Vector3 = anchor.get("pos", entity_pos) if not anchor.is_empty() else entity_pos
	var craft_time_sec := float(sc.get("craft_time_sec", 3.5))
	var state := {
		"player": p_name,
		"schematic_id": sid,
		"anchor_id": str(anchor.get("id", "field_craft")),
		"anchor_label": str(anchor.get("label", "Assemblage terrain")),
		"snap_pos": [snap_pos.x, snap_pos.y, snap_pos.z],
		"posture": "craft",
		"craft_time_sec": craft_time_sec,
		"started_at": Time.get_unix_time_from_system(),
	}
	active_craft_states[p_name] = state

	var out := craft_res.duplicate(true)
	out["schematic_id"] = sid
	out["craft_time_sec"] = craft_time_sec
	out["triplon_state"] = state
	out["bench_anchor_id"] = state["anchor_id"]
	out["posture"] = "craft"
	out["snap_pos"] = state["snap_pos"]
	return out

