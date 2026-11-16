extends RefCounted
class_name HubLife
## Triplons travail/loisir/repos + solos — objectifs court/moyen/long.
## Repos : marche vers un logement PNJ, puis inactive (hors zone_state).

const _HubPaths = preload("res://scripts/hub_paths.gd")

var pois: Dictionary = {}
var triplons: Array = []
var solos: Array = []
var phase_seconds: Dictionary = {}
var _rng := RandomNumberGenerator.new()
## eid -> {triplon_id, member_idx, phase, phase_until, ...meta}
var _sched: Dictionary = {}
## Rotation des logements si home_poi absent.
const _LODGE_KEYS: Array = ["lodge_w", "lodge_n", "lodge_e", "lodge_s", "inn"]

var collision = null
## allow_leisure_citizens : les PNJ en quartier libre (leisure) animent le monde
## (tavernes, marché, récolte/cueillette dunes, danse/spectacle, déambulation)
## tandis que le 3e membre (rest) se repose dans ses quartiers privés.
var allow_leisure_citizens: bool = true


func setup(poi_map: Dictionary, collision_svc = null) -> void:
	pois = poi_map
	collision = collision_svc
	_rng.randomize()
	triplons.clear()
	solos.clear()
	_sched.clear()
	var raw: Variant = _HubPaths.read_json(_HubPaths.data_file("life/triplons.json"))
	if typeof(raw) != TYPE_DICTIONARY:
		push_warning("[prime-hub] life/triplons.json missing")
		return
	allow_leisure_citizens = bool(raw.get("allow_leisure_citizens", true))
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
	var lodge_i := 0
	for t in triplons:
		if typeof(t) != TYPE_DICTIONARY:
			continue
		var tid := str(t.get("id", ""))
		var members: Array = t.get("members", [])
		# Stagger : member i starts at phase i % 3
		var phases := ["work", "leisure", "rest"]
		var default_home := str(t.get("home_poi", ""))
		if default_home.is_empty():
			default_home = str(_LODGE_KEYS[lodge_i % _LODGE_KEYS.size()])
			lodge_i += 1
		for i in range(members.size()):
			var m = members[i]
			if typeof(m) != TYPE_DICTIONARY:
				continue
			var eid := str(m.get("eid", ""))
			var phase := str(phases[i % 3])
			var home := str(m.get("home_poi", default_home))
			_sched[eid] = {
				"kind": "triplon",
				"triplon_id": tid,
				"member_idx": i,
				"phase": phase,
				"phase_until": Time.get_unix_time_from_system() + _phase_dur(phase),
				"meta": m,
				"work_poi": str(t.get("work_poi", "plaza")),
				"leisure_poi": str(t.get("leisure_poi", "cantina")),
				"home_poi": home,
			}
	var solo_phases := ["work", "leisure", "rest"]
	var si := 0
	for s in solos:
		if typeof(s) != TYPE_DICTIONARY:
			continue
		var eid2 := str(s.get("eid", ""))
		var sp := str(solo_phases[si % 3])
		var solo_home := str(s.get("home_poi", ""))
		if solo_home.is_empty():
			solo_home = str(_LODGE_KEYS[si % _LODGE_KEYS.size()])
		si += 1
		_sched[eid2] = {
			"kind": "solo",
			"phase": sp,
			"phase_until": Time.get_unix_time_from_system() + _phase_dur(sp),
			"meta": s,
			"work_poi": str(s.get("home", "plaza")),
			"leisure_poi": "cantina",
			"home_poi": solo_home,
			"member_idx": si,
		}


func _phase_dur(phase: String) -> float:
	var arr = phase_seconds.get(phase, [300, 600])
	if typeof(arr) != TYPE_ARRAY or arr.size() < 2:
		return 400.0
	return _rng.randf_range(float(arr[0]), float(arr[1]))


func _leisure_meta(sch: Dictionary) -> Dictionary:
	var meta: Dictionary = sch.get("meta", {})
	var raw_leis: String = str(meta.get("leisure", "")).to_lower()
	var tid: String = str(sch.get("triplon_id", "")).to_lower()

	# 1. Récolte de ressources / Cueillette / Récupération dans les dunes
	if raw_leis.contains("cueillir") or raw_leis.contains("dune") or raw_leis.contains("ferraille") or raw_leis.contains("hors"):
		var p_gather := Vector3(5350.0, 0.15, -737.0) # Dunes porte est
		if hash(raw_leis) % 2 == 0:
			p_gather = Vector3(4749.0, 0.15, -1430.0) # Dunes porte sud
		return {
			"goal": "gather",
			"activity": "Cueillette / Récup'",
			"poi": p_gather,
			"wander_r": 18.0,
			"ambient": "Un bon filon de pièces et d'herbes sous le sable.",
		}

	# 2. Taverne / Cantina / Boisson
	if raw_leis.contains("verre") or raw_leis.contains("cantina") or raw_leis.contains("perle") or raw_leis.contains("thé") or raw_leis.contains("bar"):
		var p_tavern := Vector3(5080.0, 0.15, -737.0) # Cantina La Perle
		if raw_leis.contains("auberge") or raw_leis.contains("thé"):
			p_tavern = Vector3(4749.0, 0.15, -520.0) # Auberge
		return {
			"goal": "drink",
			"activity": "Prend un verre",
			"poi": p_tavern,
			"wander_r": 6.0,
			"ambient": "Un verre bien mérité après le service.",
		}

	# 3. Animation / Danse / Spectacle
	if raw_leis.contains("danse") or raw_leis.contains("musique") or raw_leis.contains("scène") or tid == "entertainer":
		return {
			"goal": "dance",
			"activity": "Danse & Spectacle",
			"poi": Vector3(5115.0, 0.15, -737.0), # Scène La Perle
			"wander_r": 5.0,
			"ambient": "Le rythme fait du bien à l'esprit dans ce désert.",
		}

	# 4. Commerce / Marché / Bazar
	if raw_leis.contains("marché") or raw_leis.contains("bazar") or raw_leis.contains("chine") or tid == "artisan":
		return {
			"goal": "trade",
			"activity": "Flâne au marché",
			"poi": Vector3(4749.0, 0.15, -980.0), # Place du marché
			"wander_r": 14.0,
			"ambient": "Les étals regorgent de pièces intéressantes aujourd'hui.",
		}

	# 5. Déambulation urbaine / Spatioport / Promenade
	var p_stroll := Vector3(4400.0, 0.15, -737.0) # Spatioport
	if hash(raw_leis) % 2 == 0:
		p_stroll = Vector3(4749.0, 0.15, -737.0) # Place centrale
	return {
		"goal": "stroll",
		"activity": "Déambule en ville",
		"poi": p_stroll,
		"wander_r": 15.0,
		"ambient": "Une brise légère traverse le hub aujourd'hui.",
	}


func spawn_all(entities: Dictionary) -> void:
	## Remplit entities :
	## - 1 seul travailleur en service par poste officiel (phase == "work")
	## - 1 citoyen en loisir actif qui meuble le monde (cantina, marché, récolte, danse...)
	## - 1 membre au repos dans ses quartiers privés (phase == "rest", invisible)
	for eid in _sched.keys():
		var sch: Dictionary = _sched[eid]
		var meta: Dictionary = sch.get("meta", {})
		var phase := str(sch.get("phase", "work"))
		var is_triplon := str(sch.get("kind", "")) == "triplon"
		var active := false
		var pos := Vector3.ZERO
		var wander := 8.0
		var activity := "En service"
		var goal := phase
		var amb := str(meta.get("ambient", ""))

		if is_triplon:
			if phase == "work":
				active = true
				pos = _pos_for_phase(sch, "work")
				activity = "En service"
				wander = 8.0
			elif phase == "leisure" and allow_leisure_citizens:
				active = true
				var l_info := _leisure_meta(sch)
				pos = l_info["poi"]
				activity = str(l_info["activity"])
				goal = str(l_info["goal"])
				wander = float(l_info["wander_r"])
				amb = str(l_info["ambient"])
			else:
				# rest (ou leisure si désactivé)
				active = false
				pos = _pos_for_phase(sch, "rest")
				wander = 0.0
		else:
			# Solos (Jax, Scribe, Sergent...)
			active = (phase != "rest")
			pos = _pos_for_phase(sch, phase)
			wander = float(meta.get("wander_r", 10.0))
			activity = "Citoyen"

		entities[eid] = {
			"eid": eid,
			"oid": int(meta.get("oid", 910000)),
			"kind": "npc",
			"name": str(meta.get("name", eid)),
			"pos": pos,
			"target": Vector3.ZERO,
			"speed": 0.0 if not active else 7.5,
			"is_bot": false,
			"goal": goal,
			"activity": activity,
			"play_mode": "life",
			"quest_id": "",
			"linger_until": 0.0,
			"stuck_ticks": 0,
			"home_x": pos.x,
			"home_z": pos.z,
			"wander_r": wander,
			"ambient": amb,
			"active": active,
			"life_phase": phase,
			"obj_short": str(meta.get("short", "")),
			"obj_medium": str(meta.get("medium", "")),
			"obj_long": str(meta.get("long", "")),
			"triplon_id": str(sch.get("triplon_id", "")),
			"_rest_commute": false,
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
	ent["goal"] = phase
	ent["home_x"] = pos.x
	ent["home_z"] = pos.z
	var is_triplon := str(sch.get("kind", "")) == "triplon"

	if is_triplon:
		if phase == "work":
			ent["active"] = true
			ent["_rest_commute"] = false
			ent["goal"] = "work"
			ent["activity"] = "En service"
			ent["pos"] = pos
			ent["target"] = pos
			ent["speed"] = 7.5
			ent["wander_r"] = 8.0
		elif phase == "leisure":
			var l_info := _leisure_meta(sch)
			ent["active"] = allow_leisure_citizens
			ent["_rest_commute"] = false
			ent["goal"] = str(l_info["goal"])
			ent["activity"] = str(l_info["activity"])
			ent["pos"] = l_info["poi"]
			ent["target"] = l_info["poi"]
			ent["speed"] = 7.5 if allow_leisure_citizens else 0.0
			ent["wander_r"] = float(l_info["wander_r"])
			ent["ambient"] = str(l_info["ambient"])
		else: # rest
			ent["active"] = false
			ent["_rest_commute"] = false
			ent["pos"] = pos
			ent["target"] = Vector3.ZERO
			ent["speed"] = 0.0
			ent["wander_r"] = 0.0
			ent["activity"] = "Repos"
		return

	if phase == "rest":
		# Marche vers le logement, reste visible, puis inactive à l'arrivée (hub_sim).
		ent["active"] = true
		ent["goal"] = "rest_home"
		ent["_rest_commute"] = true
		ent["target"] = pos
		ent["speed"] = 7.5
		ent["wander_r"] = 0.0
	else:
		ent["active"] = true
		ent["_rest_commute"] = false
		ent["target"] = pos
		ent["speed"] = 7.5
		ent["wander_r"] = 14.0 if phase == "leisure" else 8.0


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
		key = str(sch.get("home_poi", "lodge_w"))
	var base: Vector3 = pois.get(key, Vector3(4749.0, 0.15, -737.0))

	# Si un meuble interactif correspondant est disponible près du POI (Ticket 3.1)
	if collision != null and collision.has_method("find_anchor_near"):
		var req_interaction := ""
		if phase == "leisure":
			req_interaction = "drink" if _rng.randf() < 0.6 else "sit"
		elif phase == "rest":
			req_interaction = "rest"
		elif phase == "work" and ("artisan" in key or "craft" in key or "warehouse" in key):
			req_interaction = "craft"

		if not req_interaction.is_empty():
			var anchor: Dictionary = collision.find_anchor_near(base, 35.0, req_interaction)
			if not anchor.is_empty() and anchor.get("pos") is Vector3:
				var a_pos: Vector3 = anchor["pos"]
				var slot_m := int(sch.get("member_idx", 0))
				return Vector3(
					a_pos.x + float(slot_m % 2) * 0.8 - 0.4,
					0.15,
					a_pos.z + float((slot_m / 2) % 2) * 0.8 - 0.4
				)

	var off = meta.get("work_offset", null)
	if phase == "work" and typeof(off) == TYPE_ARRAY and off.size() >= 2:
		base = Vector3(base.x + float(off[0]), 0.15, base.z + float(off[1]))
	if phase == "rest":
		# Slot par membre — plusieurs lits dans le même bloc.
		var slot := int(sch.get("member_idx", 0))
		var ang := float(slot) * (TAU / 4.0) + float(hash(str(meta.get("eid", ""))) % 7) * 0.15
		var rad := 5.0 + float(slot % 3) * 2.0
		base.x += cos(ang) * rad
		base.z += sin(ang) * rad
	else:
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
		"active_ratio": float(n_work + (n_lei if allow_leisure_citizens else 0)) / float(maxi(total, 1)),
		"allow_leisure_citizens": allow_leisure_citizens,
		"triplons": triplons.size(),
	}
