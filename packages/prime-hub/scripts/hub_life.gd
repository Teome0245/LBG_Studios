extends RefCounted
class_name HubLife
## Triplons travail/loisir/repos + solos — objectifs court/moyen/long.

const _HubPaths = preload("res://scripts/hub_paths.gd")

var pois: Dictionary = {}
var triplons: Array = []
var solos: Array = []
var phase_seconds: Dictionary = {}
var _rng := RandomNumberGenerator.new()
## eid -> {triplon_id, member_idx, phase, phase_until, ...meta}
var _sched: Dictionary = {}


func setup(poi_map: Dictionary) -> void:
	pois = poi_map
	_rng.randomize()
	triplons.clear()
	solos.clear()
	_sched.clear()
	var raw: Variant = _HubPaths.read_json(_HubPaths.data_file("life/triplons.json"))
	if typeof(raw) != TYPE_DICTIONARY:
		push_warning("[prime-hub] life/triplons.json missing")
		return
	phase_seconds = raw.get("phase_seconds", {
		"work": [480, 840], "leisure": [300, 600], "rest": [360, 720],
	})
	var tarr = raw.get("triplons", [])
	if typeof(tarr) == TYPE_ARRAY:
		triplons = tarr
	var sarr = raw.get("solos", [])
	if typeof(sarr) == TYPE_ARRAY:
		solos = sarr
	_init_schedules()


func _init_schedules() -> void:
	for t in triplons:
		if typeof(t) != TYPE_DICTIONARY:
			continue
		var tid := str(t.get("id", ""))
		var members: Array = t.get("members", [])
		# Stagger : member i starts at phase i % 3
		var phases := ["work", "leisure", "rest"]
		for i in range(members.size()):
			var m = members[i]
			if typeof(m) != TYPE_DICTIONARY:
				continue
			var eid := str(m.get("eid", ""))
			var phase := str(phases[i % 3])
			_sched[eid] = {
				"kind": "triplon",
				"triplon_id": tid,
				"member_idx": i,
				"phase": phase,
				"phase_until": Time.get_unix_time_from_system() + _phase_dur(phase),
				"meta": m,
				"work_poi": str(t.get("work_poi", "plaza")),
				"leisure_poi": str(t.get("leisure_poi", "cantina")),
				"home_poi": str(t.get("home_poi", "inn")),
			}
	var solo_phases := ["work", "leisure", "rest"]
	var si := 0
	for s in solos:
		if typeof(s) != TYPE_DICTIONARY:
			continue
		var eid2 := str(s.get("eid", ""))
		var sp := str(solo_phases[si % 3])
		si += 1
		_sched[eid2] = {
			"kind": "solo",
			"phase": sp,
			"phase_until": Time.get_unix_time_from_system() + _phase_dur(sp),
			"meta": s,
			"work_poi": str(s.get("home", "plaza")),
			"leisure_poi": "cantina",
			"home_poi": "inn",
		}


func _phase_dur(phase: String) -> float:
	var arr = phase_seconds.get(phase, [300, 600])
	if typeof(arr) != TYPE_ARRAY or arr.size() < 2:
		return 400.0
	return _rng.randf_range(float(arr[0]), float(arr[1]))


func spawn_all(entities: Dictionary) -> void:
	## Remplit entities avec PNJ triplons + solos (rest = inactive).
	for eid in _sched.keys():
		var sch: Dictionary = _sched[eid]
		var meta: Dictionary = sch.get("meta", {})
		var phase := str(sch.get("phase", "work"))
		var active := phase != "rest"
		var pos := _pos_for_phase(sch, phase)
		var wander := 10.0
		if sch.get("kind") == "solo":
			wander = float(meta.get("wander_r", 10.0))
		elif phase == "work":
			wander = 8.0
		elif phase == "leisure":
			wander = 14.0
		entities[eid] = {
			"eid": eid,
			"oid": int(meta.get("oid", 910000)),
			"kind": "npc",
			"name": str(meta.get("name", eid)),
			"pos": pos,
			"target": Vector3.ZERO,
			"speed": 7.5,
			"is_bot": false,
			"goal": phase,
			"play_mode": "life",
			"quest_id": "",
			"linger_until": 0.0,
			"stuck_ticks": 0,
			"home_x": pos.x,
			"home_z": pos.z,
			"wander_r": wander,
			"ambient": str(meta.get("ambient", "")),
			"active": active,
			"life_phase": phase,
			"obj_short": str(meta.get("short", "")),
			"obj_medium": str(meta.get("medium", "")),
			"obj_long": str(meta.get("long", "")),
			"triplon_id": str(sch.get("triplon_id", "")),
		}


func tick_life(entities: Dictionary, now: float) -> void:
	for eid in _sched.keys():
		var sch: Dictionary = _sched[eid]
		if now < float(sch.get("phase_until", 0.0)):
			continue
		var next := _next_phase(str(sch.get("phase", "work")))
		# Pour triplon : éviter 0 personnes en work — si on quitte work, forcer un autre en work
		if sch.get("kind") == "triplon" and str(sch.get("phase")) == "work":
			_ensure_someone_works(str(sch.get("triplon_id", "")), eid, now, entities)
		sch["phase"] = next
		sch["phase_until"] = now + _phase_dur(next)
		_sched[eid] = sch
		_apply_phase(entities, eid, sch, next)


func _apply_phase(entities: Dictionary, eid: String, sch: Dictionary, phase: String) -> void:
	if not entities.has(eid):
		return
	var ent: Dictionary = entities[eid]
	var pos := _pos_for_phase(sch, phase)
	ent["life_phase"] = phase
	ent["active"] = phase != "rest"
	ent["goal"] = phase
	ent["home_x"] = pos.x
	ent["home_z"] = pos.z
	ent["wander_r"] = 14.0 if phase == "leisure" else 8.0
	if phase == "rest":
		ent["pos"] = pos
		ent["target"] = Vector3.ZERO
		ent["speed"] = 0.0
	else:
		ent["target"] = pos
		ent["speed"] = 7.5


func _ensure_someone_works(triplon_id: String, leaving_eid: String, now: float, entities: Dictionary) -> void:
	var workers := 0
	var candidate := ""
	for eid in _sched.keys():
		var sch: Dictionary = _sched[eid]
		if str(sch.get("triplon_id", "")) != triplon_id:
			continue
		if eid == leaving_eid:
			continue
		if str(sch.get("phase", "")) == "work":
			workers += 1
		elif candidate.is_empty() and str(sch.get("phase", "")) != "work":
			candidate = eid
	if workers > 0 or candidate.is_empty():
		return
	var sch2: Dictionary = _sched[candidate]
	sch2["phase"] = "work"
	sch2["phase_until"] = now + _phase_dur("work")
	_sched[candidate] = sch2
	_apply_phase(entities, candidate, sch2, "work")


func _next_phase(cur: String) -> String:
	match cur:
		"work":
			return "leisure"
		"leisure":
			return "rest"
		_:
			return "work"


func _pos_for_phase(sch: Dictionary, phase: String) -> Vector3:
	var meta: Dictionary = sch.get("meta", {})
	var key := str(sch.get("work_poi", "plaza"))
	if phase == "leisure":
		key = str(sch.get("leisure_poi", "cantina"))
		var leis := str(meta.get("leisure", ""))
		# aspiration loisir : biais dunes / cantina déjà dans leisure_poi
		if "dune" in leis.to_lower() or "hors" in leis.to_lower():
			return Vector3(5600.0, 0.15, -1000.0)
	elif phase == "rest":
		key = str(sch.get("home_poi", "inn"))
	var base: Vector3 = pois.get(key, Vector3(4749.0, 0.15, -737.0))
	var off = meta.get("work_offset", null)
	if phase == "work" and typeof(off) == TYPE_ARRAY and off.size() >= 2:
		base = Vector3(base.x + float(off[0]), 0.15, base.z + float(off[1]))
	# jitter léger anti-stack
	base.x += _rng.randf_range(-3.0, 3.0)
	base.z += _rng.randf_range(-3.0, 3.0)
	return base


func stats() -> Dictionary:
	var n_work := 0
	var n_lei := 0
	var n_rest := 0
	for eid in _sched.keys():
		var p := str((_sched[eid] as Dictionary).get("phase", ""))
		if p == "work":
			n_work += 1
		elif p == "leisure":
			n_lei += 1
		else:
			n_rest += 1
	var total := _sched.size()
	return {
		"npc_scheduled": total,
		"work": n_work,
		"leisure": n_lei,
		"rest": n_rest,
		"active_ratio": float(n_work + n_lei) / float(maxi(total, 1)),
		"triplons": triplons.size(),
	}
