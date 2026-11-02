extends RefCounted
class_name HubHarvesters
## Ticket 4.5 (O2/O3 Phase 4 SWG Pre-CU) — Extracteurs de Terrain (Harvesters),
## Trémies d'Extraction Asynchrones (Hopper) & Maintenance Civique.

const MIN_DEPLOY_DENSITY := 25
const DEFAULT_HOPPER_CAP := 500
const DEFAULT_MAINTENANCE := 100
const MAINT_COST_PER_CYCLE := 5

var economy = null
var survey = null
var skills = null
var collision = null
var harvesters_by_id: Dictionary = {}
var _seq: int = 1


func setup(economy_svc = null, survey_svc = null, skills_svc = null, collision_svc = null) -> void:
	economy = economy_svc
	survey = survey_svc
	skills = skills_svc
	collision = collision_svc


func list_harvesters(owner_filter: String = "") -> Array:
	var f := owner_filter.strip_edges()
	var out: Array = []
	for hid in harvesters_by_id.keys():
		var h: Dictionary = harvesters_by_id[hid]
		if f.is_empty() or str(h.get("owner", "")) == f:
			out.append(h.duplicate(true))
	return out


func deploy_harvester(
	player: String,
	spawn_id: String,
	x: float,
	z: float,
	custom_ber: float = 12.0
) -> Dictionary:
	var p_name := player.strip_edges()
	if p_name.is_empty():
		p_name = "Voyageur"
	var sid := spawn_id.strip_edges()
	if survey == null:
		return {"ok": false, "error": "survey_unavailable"}
	var sp: Dictionary = survey.get_spawn(sid)
	if sp.is_empty():
		return {"ok": false, "error": "unknown_spawn", "spawn_id": sid}

	if collision != null and collision.has_method("is_inside_building"):
		if bool(collision.is_inside_building(Vector3(x, 0.15, z))):
			return {
				"ok": false,
				"error": "no_build_inside_structure",
				"hint": "Impossible de déployer un extracteur à l'intérieur d'un bâtiment CAO.",
			}

	var local_dens: int = survey.density_at(sid, x, z)
	if local_dens < MIN_DEPLOY_DENSITY:
		return {
			"ok": false,
			"error": "density_too_low_for_harvester",
			"local_density_pct": local_dens,
			"min_required_pct": MIN_DEPLOY_DENSITY,
		}

	var max_slots := 1
	if skills != null and skills.has_method("compute_skill_mods"):
		var mods: Dictionary = skills.compute_skill_mods(p_name)
		max_slots = maxi(1, int(mods.get("harvester_slots", 1)))

	var active_owned := list_harvesters(p_name).size()
	if active_owned >= max_slots:
		return {
			"ok": false,
			"error": "max_harvester_slots_reached",
			"active_harvesters": active_owned,
			"max_slots": max_slots,
		}

	var hid := "harv_%s_%d" % [p_name.to_lower(), _seq]
	_seq += 1

	var h_record := {
		"harvester_id": hid,
		"owner": p_name,
		"spawn_id": sid,
		"spawn_name": str(sp.get("spawn_name", sid)),
		"base_item_id": str(sp.get("base_item_id", "scrap_metal")),
		"label": str(sp.get("label", sid)),
		"icon": str(sp.get("icon", "copper")),
		"resource_stats": (sp.get("stats", {}) as Dictionary).duplicate(true),
		"x": x,
		"z": z,
		"local_density_pct": local_dens,
		"ber": maxf(2.0, custom_ber),
		"hopper_qty": 0,
		"hopper_capacity": DEFAULT_HOPPER_CAP,
		"maintenance_pool": DEFAULT_MAINTENANCE,
		"cycles_run": 0,
		"active": true,
	}
	harvesters_by_id[hid] = h_record

	if economy != null:
		economy.log_session_event(
			p_name,
			"harvester_deploy",
			"Extracteur %s posé sur %s (densité %d%%)" % [hid, str(sp.get("spawn_name", sid)), local_dens],
			{"harvester_id": hid, "spawn_id": sid, "density": local_dens}
		)

	return {
		"ok": true,
		"harvester": h_record.duplicate(true),
	}


func advance_cycles(cycles: int = 1) -> Dictionary:
	var n := maxi(1, cycles)
	var updated := 0
	for hid in harvesters_by_id.keys():
		var h: Dictionary = harvesters_by_id[hid]
		if not bool(h.get("active", true)):
			continue
		for _i in range(n):
			var maint := int(h.get("maintenance_pool", 0))
			if maint < MAINT_COST_PER_CYCLE:
				h["active"] = false
				break
			var cap := int(h.get("hopper_capacity", DEFAULT_HOPPER_CAP))
			var cur := int(h.get("hopper_qty", 0))
			if cur >= cap:
				break
			h["maintenance_pool"] = maint - MAINT_COST_PER_CYCLE
			var ber := float(h.get("ber", 12.0))
			var dens := float(h.get("local_density_pct", 50))
			var extracted := maxi(1, int(round(ber * (dens / 100.0))))
			h["hopper_qty"] = mini(cap, cur + extracted)
			h["cycles_run"] = int(h.get("cycles_run", 0)) + 1
			updated += 1
	return {
		"ok": true,
		"cycles_requested": n,
		"extractions_processed": updated,
	}


func add_maintenance(player: String, harvester_id: String, amount: int = 50) -> Dictionary:
	var hid := harvester_id.strip_edges()
	if not harvesters_by_id.has(hid):
		return {"ok": false, "error": "unknown_harvester", "harvester_id": hid}
	var h: Dictionary = harvesters_by_id[hid]
	if str(h.get("owner", "")) != player.strip_edges():
		return {"ok": false, "error": "not_harvester_owner"}
	h["maintenance_pool"] = int(h.get("maintenance_pool", 0)) + maxi(1, amount)
	h["active"] = true
	return {
		"ok": true,
		"harvester_id": hid,
		"maintenance_pool": int(h["maintenance_pool"]),
		"active": true,
	}


func collect_hopper(player: String, harvester_id: String) -> Dictionary:
	var p_name := player.strip_edges()
	if p_name.is_empty():
		p_name = "Voyageur"
	var hid := harvester_id.strip_edges()
	if not harvesters_by_id.has(hid):
		return {"ok": false, "error": "unknown_harvester", "harvester_id": hid}
	var h: Dictionary = harvesters_by_id[hid]
	if str(h.get("owner", "")) != p_name:
		return {"ok": false, "error": "not_harvester_owner", "owner": str(h.get("owner", ""))}
	var qty := int(h.get("hopper_qty", 0))
	if qty <= 0:
		return {"ok": false, "error": "hopper_empty", "harvester_id": hid}
	if economy == null:
		return {"ok": false, "error": "economy_unavailable"}

	var p: Dictionary = economy._player(p_name)
	var inv: Array = p.get("inventory", [])
	var base_id := str(h.get("base_item_id", "scrap_metal"))
	var sid := str(h.get("spawn_id", ""))
	var sname := str(h.get("spawn_name", sid))
	var stats: Dictionary = (h.get("resource_stats", {}) as Dictionary).duplicate(true)

	var found := false
	for item in inv:
		if typeof(item) == TYPE_DICTIONARY and str(item.get("id", "")) == base_id:
			item["qty"] = int(item.get("qty", 0)) + qty
			item["spawn_id"] = sid
			item["spawn_name"] = sname
			item["resource_stats"] = stats.duplicate(true)
			found = true
			break
	if not found:
		inv.append({
			"id": base_id,
			"name": str(h.get("label", sname)),
			"qty": qty,
			"icon": str(h.get("icon", "copper")),
			"spawn_id": sid,
			"spawn_name": sname,
			"resource_stats": stats.duplicate(true),
		})
	p["inventory"] = inv
	h["hopper_qty"] = 0

	if skills != null and skills.has_method("grant_xp"):
		skills.grant_xp(p_name, "xp_prospection", qty * 4)
		skills.grant_xp(p_name, "xp_civique", qty * 2)

	economy.log_session_event(
		p_name,
		"harvester_collect",
		"Vidange extracteur %s : +%d %s (OQ %d)" % [hid, qty, sname, int(stats.get("oq", 500))],
		{"harvester_id": hid, "qty": qty, "spawn_id": sid}
	)
	economy._save_players()

	return {
		"ok": true,
		"harvester_id": hid,
		"player": p_name,
		"collected_qty": qty,
		"base_item_id": base_id,
		"spawn_id": sid,
		"resource_stats": stats,
		"remaining_maintenance": int(h.get("maintenance_pool", 0)),
	}

