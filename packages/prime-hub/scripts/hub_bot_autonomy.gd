extends RefCounted
class_name HubBotAutonomy
## Flotte IA : choix quête / explore (anneau LH) / hub + suggestions monde occasionnelles.

const _HubPaths = preload("res://scripts/hub_paths.gd")
const HubWikiScript = preload("res://scripts/hub_wiki.gd")

## Fallback si explore_ring_lh.json absent
const EXPLORE_FALLBACK: Dictionary = {
	"gate_east": {"label": "explorer porte est / dunes", "pos": Vector3(5813.6, 0.15, -982.5)},
	"gate_west": {"label": "surveiller porte ouest Zalem", "pos": Vector3(3688.9, 0.15, -675.9)},
	"hunt": {"label": "reconnaître hors murs", "pos": Vector3(5985.0, 0.15, -1120.0)},
	"spawn_apron": {"label": "repasser au shuttleport", "pos": Vector3(4749.0, 0.15, -537.0)},
}

const RING_CENTER_FALLBACK := Vector3(4749.0, 0.15, -737.0)
const RING_RADIUS_FALLBACK := 9500.0
const OUTPOST_ZALEM_CENTER := Vector3(-1200.0, 0.15, -550.0)
const OUTPOST_KSAR_CENTER := Vector3(4950.0, 0.15, -3800.0)

var personas: Dictionary = {}
var economy = null
var suggest = null
var pois: Dictionary = {}
var events = null
var world_clock = null
var explore: Dictionary = {}
var ring_center: Vector3 = RING_CENTER_FALLBACK
var ring_radius_m: float = RING_RADIUS_FALLBACK
var random_sample_chance: float = 0.28
var _rng := RandomNumberGenerator.new()
var _last_suggest: Dictionary = {}  # name -> unix
var _quest_cd: Dictionary = {}

var creatures = null
var vendors_factories = null
var housing_cities = null
var swg_combat = null
var ham_medical = null
var harvesters = null
var faction = null


func setup(economy_svc, suggest_svc, poi_map: Dictionary, events_svc = null) -> void:
	economy = economy_svc
	suggest = suggest_svc
	pois = poi_map
	events = events_svc
	_rng.randomize()
	_load_explore_ring()


func setup_swg_services(creatures_svc, vendors_factories_svc, housing_cities_svc, swg_combat_svc, ham_medical_svc = null, harvesters_svc = null, faction_svc = null) -> void:
	creatures = creatures_svc
	vendors_factories = vendors_factories_svc
	housing_cities = housing_cities_svc
	swg_combat = swg_combat_svc
	ham_medical = ham_medical_svc
	harvesters = harvesters_svc
	faction = faction_svc


func attach_world_clock(clock_svc) -> void:
	world_clock = clock_svc
	personas.clear()
	# Source primaire : ai_players.json (personas inline) ; fallback bot_personas.json
	var fleet: Variant = _HubPaths.read_json(_HubPaths.data_file("life/ai_players.json"))
	if typeof(fleet) == TYPE_DICTIONARY:
		var arr = fleet.get("players", [])
		if typeof(arr) == TYPE_ARRAY:
			for p in arr:
				if typeof(p) != TYPE_DICTIONARY:
					continue
				var nm := str(p.get("name", ""))
				if nm.is_empty():
					continue
				var og = p.get("out_game", {})
				if typeof(og) != TYPE_DICTIONARY:
					og = {}
				personas[nm] = {
					"short": str(p.get("short", "")),
					"medium": str(p.get("medium", "")),
					"long": str(p.get("long", "")),
					"quest_prefer": p.get("quest_prefer", []),
					"explore_prefer": p.get("explore_prefer", []),
					"suggest_kinds": p.get("suggest_kinds", ["poi"]),
					"playstyle": str(p.get("playstyle", "")),
					"admin_level": int(p.get("admin_level", 0)),
					"account_login": str(p.get("account_login", "")),
					"agent_id": str(og.get("agent_id", "")),
				}
	if personas.is_empty():
		var raw: Variant = _HubPaths.read_json(_HubPaths.data_file("life/bot_personas.json"))
		if typeof(raw) == TYPE_DICTIONARY:
			var bots = raw.get("bots", {})
			if typeof(bots) == TYPE_DICTIONARY:
				personas = bots


func _load_explore_ring() -> void:
	explore = EXPLORE_FALLBACK.duplicate(true)
	ring_center = RING_CENTER_FALLBACK
	ring_radius_m = RING_RADIUS_FALLBACK
	random_sample_chance = 0.28
	var raw: Variant = _HubPaths.read_json(_HubPaths.data_file("life/explore_ring_lh.json"))
	if typeof(raw) != TYPE_DICTIONARY:
		return
	var c = raw.get("center", {})
	if typeof(c) == TYPE_DICTIONARY:
		ring_center = Vector3(float(c.get("x", ring_center.x)), float(c.get("y", 0.15)), float(c.get("z", ring_center.z)))
	ring_radius_m = maxf(200.0, float(raw.get("max_radius_m", ring_radius_m)))
	random_sample_chance = clampf(float(raw.get("random_sample_chance", random_sample_chance)), 0.0, 1.0)
	var wps = raw.get("waypoints", {})
	if typeof(wps) != TYPE_DICTIONARY:
		return
	for id in wps.keys():
		var spot = wps[id]
		if typeof(spot) != TYPE_DICTIONARY:
			continue
		var p = spot.get("pos", {})
		if typeof(p) != TYPE_DICTIONARY:
			continue
		var pos := Vector3(float(p.get("x", 0.0)), float(p.get("y", 0.15)), float(p.get("z", 0.0)))
		pos = clamp_pos(pos)
		explore[str(id)] = {
			"label": str(spot.get("label", id)),
			"pos": pos,
		}


func clamp_xz(x: float, z: float) -> Vector2:
	var dx := x - ring_center.x
	var dz := z - ring_center.z
	var d := sqrt(dx * dx + dz * dz)
	if d <= ring_radius_m or d < 1e-6:
		return Vector2(x, z)
	var s := ring_radius_m / d
	return Vector2(ring_center.x + dx * s, ring_center.z + dz * s)


func clamp_pos(pos: Vector3) -> Vector3:
	var xz := clamp_xz(pos.x, pos.z)
	return Vector3(xz.x, pos.y, xz.y)


func in_ring(x: float, z: float) -> bool:
	var dx := x - ring_center.x
	var dz := z - ring_center.z
	return sqrt(dx * dx + dz * dz) <= ring_radius_m + 0.5


func assign_goal(bot: Dictionary, prefer: Array = []) -> Dictionary:
	## Retourne {target: Vector3, goal_id, goal_label, play_mode, quest_id, maybe_suggest?}
	var name := str(bot.get("name", ""))
	var persona: Dictionary = personas.get(name, {}) if personas.has(name) else {}

	# Priorité d'urgence météo : repli sous les bâtiments abrités si tempête active
	if events != null and events.has_method("is_weather_shelter_active") and events.is_weather_shelter_active():
		var shelter_g := _shelter_goal(bot)
		bot["obj_short"] = str(shelter_g.get("goal_label", "se mettre à l'abri"))
		bot["obj_medium"] = "se protéger de la tempête"
		bot["obj_long"] = "survie environnementale"
		return shelter_g

	var roll := _rng.randf()
	var out: Dictionary
	var is_night_time: bool = false
	if world_clock != null and world_clock.has_method("is_night_time"):
		is_night_time = bool(world_clock.is_night_time())

	if is_night_time:
		# De nuit : préférence marquée pour rester sous les lanternes et abris du Hub
		if roll < 0.20 and economy != null:
			out = _quest_goal(bot, name, persona)
		elif roll < 0.35:
			out = _explore_goal(bot, persona)
		else:
			out = _hub_goal(bot, prefer, persona)
	else:
		if roll < 0.45 and economy != null:
			out = _quest_goal(bot, name, persona)
		elif roll < 0.70:
			out = _explore_goal(bot, persona)
		else:
			out = _hub_goal(bot, prefer, persona)
	# Objectifs persona (méta, pas annoncé chat)
	bot["obj_short"] = str(persona.get("short", out.get("goal_label", "")))
	bot["obj_medium"] = str(persona.get("medium", ""))
	bot["obj_long"] = str(persona.get("long", ""))
	_maybe_world_suggest(bot, persona, out)
	return out


func _shelter_goal(bot: Dictionary) -> Dictionary:
	var bpos: Vector3 = bot.get("pos", Vector3(4749.0, 0.15, -737.0))
	var shelters := ["cantina", "inn", "hall", "craft", "clinic"]
	var best_key := "cantina"
	var best_dist := INF
	for k in shelters:
		if pois.has(k):
			var p: Vector3 = pois[k]
			var d := Vector2(bpos.x - p.x, bpos.z - p.z).length()
			if d < best_dist:
				best_dist = d
				best_key = k
	var target_pos: Vector3 = pois.get(best_key, Vector3(5028.3, 0.15, -784.1))
	return {
		"target": target_pos,
		"goal_id": "shelter_storm",
		"goal_label": "se mettre à l'abri à la %s" % best_key,
		"play_mode": "shelter",
		"quest_id": "",
	}


func _hub_goal(bot: Dictionary, prefer: Array, persona: Dictionary) -> Dictionary:
	var keys: Array = prefer.duplicate() if prefer.size() > 0 else pois.keys()
	if keys.is_empty():
		keys = ["plaza"]
	var avoid := str(bot.get("goal", ""))
	var pick := str(keys[_rng.randi() % keys.size()])
	if keys.size() > 1 and pick == avoid:
		pick = str(keys[_rng.randi() % keys.size()])
	var pos: Vector3 = pois.get(pick, Vector3(4749.0, 0.15, -737.0))
	return {
		"target": pos,
		"goal_id": pick,
		"goal_label": pick,
		"play_mode": "hub",
		"quest_id": "",
	}


func _explore_goal(bot: Dictionary, persona: Dictionary) -> Dictionary:
	# Point libre dans l'anneau (désert vide OK) — sinon waypoint catalogué
	if explore.size() > 0 and _rng.randf() < random_sample_chance:
		var rnd := _random_ring_pos(bot)
		return {
			"target": rnd,
			"goal_id": "ring_sample",
			"goal_label": "reconnaître l'anneau désert",
			"play_mode": "explore",
			"quest_id": "",
		}
	var prefer: Array = persona.get("explore_prefer", []) if typeof(persona.get("explore_prefer", null)) == TYPE_ARRAY else []
	var id := "gate_east"
	if prefer.size() > 0:
		id = str(prefer[_rng.randi() % prefer.size()])
	elif explore.size() > 0:
		var keys := explore.keys()
		id = str(keys[_rng.randi() % keys.size()])
	var spot: Dictionary = explore.get(id, explore.get("gate_east", EXPLORE_FALLBACK["gate_east"]))
	var raw_pos: Variant = spot.get("pos", RING_CENTER_FALLBACK)
	var pos: Vector3 = clamp_pos(raw_pos if typeof(raw_pos) == TYPE_VECTOR3 else RING_CENTER_FALLBACK)
	return {
		"target": pos,
		"goal_id": id,
		"goal_label": str(spot.get("label", id)),
		"play_mode": "explore",
		"quest_id": "",
	}


func _random_ring_pos(bot: Dictionary = {}) -> Vector3:
	var bpos: Vector3 = bot.get("pos", ring_center) if bot.has("pos") and typeof(bot["pos"]) == TYPE_VECTOR3 else ring_center
	var d_zalem := Vector2(bpos.x - OUTPOST_ZALEM_CENTER.x, bpos.z - OUTPOST_ZALEM_CENTER.z).length()
	var d_ksar := Vector2(bpos.x - OUTPOST_KSAR_CENTER.x, bpos.z - OUTPOST_KSAR_CENTER.z).length()
	
	# Échantillonnage local si le bot patrouille ou explore près d'un village
	if d_zalem < 1400.0:
		var ang_z := _rng.randf() * TAU
		var dist_z := _rng.randf_range(160.0, 750.0)
		return Vector3(OUTPOST_ZALEM_CENTER.x + cos(ang_z) * dist_z, 0.15, OUTPOST_ZALEM_CENTER.z + sin(ang_z) * dist_z)
	elif d_ksar < 1400.0:
		var ang_k := _rng.randf() * TAU
		var dist_k := _rng.randf_range(160.0, 750.0)
		return Vector3(OUTPOST_KSAR_CENTER.x + cos(ang_k) * dist_k, 0.15, OUTPOST_KSAR_CENTER.z + sin(ang_k) * dist_k)

	## Grand anneau désert global (30–95 % du rayon)
	var ang := _rng.randf() * TAU
	var dist := _rng.randf_range(ring_radius_m * 0.30, ring_radius_m * 0.95)
	return Vector3(
		ring_center.x + cos(ang) * dist,
		0.15,
		ring_center.z + sin(ang) * dist
	)


func _quest_goal(bot: Dictionary, name: String, persona: Dictionary) -> Dictionary:
	var now := Time.get_unix_time_from_system()
	if now - float(_quest_cd.get(name, 0.0)) < 6.0:
		return _explore_goal(bot, persona)
	_quest_cd[name] = now
	var active = null
	var st: Dictionary = economy.status(name)
	var act: Array = st.get("active", [])
	if typeof(act) == TYPE_ARRAY and act.size() > 0 and typeof(act[0]) == TYPE_DICTIONARY:
		active = act[0]
	if active == null:
		var qid := _pick_quest_id(name, persona)
		if qid.is_empty():
			return _explore_goal(bot, persona)
		economy.accept(name, qid, "npc:core3_daan_oth")
		return {
			"target": pois.get("board", Vector3(4939.0, 0.15, -932.0)),
			"goal_id": "quest_accept",
			"goal_label": "accepte %s" % qid,
			"play_mode": "quest",
			"quest_id": qid,
		}
	var qid2 := str(active.get("id", ""))
	var steps: Array = active.get("progress", [])
	var done: Array = active.get("steps_done", [])
	var pending = null
	for s in steps:
		if typeof(s) != TYPE_DICTIONARY:
			continue
		var sid := str(s.get("id", ""))
		if sid != "" and sid not in done:
			pending = s
			break
	if pending == null:
		economy.complete(name, qid2)
		return {
			"target": pois.get("board", Vector3(4939.0, 0.15, -932.0)),
			"goal_id": "quest_done",
			"goal_label": "termine %s" % qid2,
			"play_mode": "quest",
			"quest_id": qid2,
		}
	var poi := str(pending.get("poi", "poi:lost_heaven_gate"))
	var pos := _poi_to_pos(poi)
	# progress when close — handled in sim on arrival via autonomy.arrive
	bot["_pending_step"] = str(pending.get("id", ""))
	bot["_pending_quest"] = qid2
	return {
		"target": pos,
		"goal_id": "quest:%s:%s" % [qid2, str(pending.get("id", ""))],
		"goal_label": str(pending.get("label", pending.get("id", ""))),
		"play_mode": "quest",
		"quest_id": qid2,
	}


func on_arrival(bot: Dictionary) -> void:
	var qid := str(bot.get("_pending_quest", ""))
	var sid := str(bot.get("_pending_step", ""))
	if not qid.is_empty() and not sid.is_empty() and economy != null:
		economy.progress(str(bot.get("name", "")), qid, sid)
		bot.erase("_pending_quest")
		bot.erase("_pending_step")

	# Ticket 2.2 — Mémoire de voyage et propagation des rumeurs
	_update_travel_observations(bot)


func _update_travel_observations(bot: Dictionary) -> void:
	var bpos: Vector3 = bot.get("pos", Vector3.ZERO)
	var d_zalem := Vector2(bpos.x - OUTPOST_ZALEM_CENTER.x, bpos.z - OUTPOST_ZALEM_CENTER.z).length()
	var d_ksar := Vector2(bpos.x - OUTPOST_KSAR_CENTER.x, bpos.z - OUTPOST_KSAR_CENTER.z).length()
	var goal_id := str(bot.get("goal_id", bot.get("goal", "")))

	# Détection de visite d'un avant-poste ou zone distante
	if d_zalem < 1600.0 or goal_id in ["gate_west", "outpost_zalem", "zalem"]:
		record_travel_observation(bot, "outpost_zalem")
	elif d_ksar < 1600.0 or goal_id in ["outpost_ksar", "ksar"]:
		record_travel_observation(bot, "outpost_ksar")
	elif bpos.x > 5600.0 or goal_id in ["gate_east", "hunt"]:
		record_travel_observation(bot, "dunes_east")

	# Détection d'arrivée sur un lieu social du hub central
	var p_cantina: Vector3 = pois.get("cantina", Vector3(5075.0, 0.15, -835.0))
	var p_plaza: Vector3 = pois.get("plaza", Vector3(4939.0, 0.15, -932.0))
	var p_inn: Vector3 = pois.get("inn", Vector3(5120.0, 0.15, -780.0))
	var is_social_spot := (
		bpos.distance_to(p_cantina) < 70.0
		or bpos.distance_to(p_plaza) < 90.0
		or bpos.distance_to(p_inn) < 70.0
		or goal_id in ["cantina", "plaza", "inn", "social", "rest"]
	)
	if is_social_spot:
		share_rumor_at_hub(bot)


func record_travel_observation(bot: Dictionary, origin: String) -> Dictionary:
	if not bot.has("travel_memory") or typeof(bot["travel_memory"]) != TYPE_ARRAY:
		bot["travel_memory"] = []
	var mem: Array = bot["travel_memory"]
	# Ne pas empiler plus de 3 souvenirs
	if mem.size() >= 3:
		return {}
	# Éviter de dupliquer la même origine immédiatement
	for item in mem:
		if typeof(item) == TYPE_DICTIONARY and str(item.get("origin", "")) == origin:
			return {}

	var bot_name := str(bot.get("name", "Voyageur"))
	var obs := _generate_observation(origin, bot_name)
	mem.append(obs)
	return obs


func share_rumor_at_hub(bot: Dictionary) -> Dictionary:
	var mem: Array = bot.get("travel_memory", [])
	if mem.is_empty():
		return {}
	var rumor: Dictionary = mem.pop_front()
	HubWikiScript.add_rumor(rumor)
	bot["last_rumor_shared"] = Time.get_unix_time_from_system()
	return rumor


func _generate_observation(origin: String, bot_name: String) -> Dictionary:
	var label := "Zone sauvage"
	var text := "Rien de particulier à signaler."
	var topic := "exploration"
	match origin:
		"outpost_zalem":
			label = "Avant-poste Zalem"
			topic = "zalem"
			var zalem_facts := [
				"La milice du Capitaine Vael renforce la surveillance de la passe ouest.",
				"Soren Kray recherche activement des pièces de carbu à l'atelier de transit.",
				"Un convoi de minerai sécurisé s'apprête à traverser vers Lost Heaven.",
			]
			text = zalem_facts[_rng.randi() % zalem_facts.size()]
		"outpost_ksar":
			label = "Ksar Nomade"
			topic = "ksar"
			var ksar_facts := [
				"L'Ancien Nadir signale que l'oasis est paisible et les réserves d'eau stables.",
				"Miran Sael a préparé de nouveaux baumes contre les piqûres des bêtes des sables.",
				"Une caravane de marchands nomades fait étape sous les tentes du sud.",
			]
			text = ksar_facts[_rng.randi() % ksar_facts.size()]
		"dunes_east":
			label = "Dunes de l'Est"
			topic = "dunes"
			var dunes_facts := [
				"Une carcasse de transporteur offre encore de belles plaques de ferraille intactes.",
				"Des bêtes sauvages ont été aperçues rôdant à distance de la palissade est.",
				"Les vents d'est soulèvent de fines rafales de poussière abrasive sur l'anneau.",
			]
			text = dunes_facts[_rng.randi() % dunes_facts.size()]
	return {
		"id": "rumor_%s_%d" % [bot_name.to_lower(), int(Time.get_unix_time_from_system() * 1000.0)],
		"source_bot": bot_name,
		"origin": origin,
		"origin_label": label,
		"topic": topic,
		"text": text,
		"timestamp": Time.get_unix_time_from_system(),
	}


func _pick_quest_id(name: String, persona: Dictionary) -> String:
	var board: Dictionary = economy.board("npc:core3_daan_oth", name)
	var quests: Array = board.get("quests", [])
	if typeof(quests) != TYPE_ARRAY or quests.is_empty():
		return ""
	var by_id: Dictionary = {}
	for q in quests:
		if typeof(q) == TYPE_DICTIONARY and str(q.get("id", "")) != "":
			by_id[str(q["id"])] = q
	var prefer: Array = persona.get("quest_prefer", []) if typeof(persona.get("quest_prefer", null)) == TYPE_ARRAY else []
	for qid in prefer:
		if by_id.has(str(qid)):
			return str(qid)
	return str(quests[0].get("id", ""))


func _poi_to_pos(poi: String) -> Vector3:
	var p := poi
	if p.begins_with("poi:"):
		p = p.substr(4)
	# map common
	var map := {
		"lost_heaven": "plaza",
		"lost_heaven_market": "market",
		"lost_heaven_starport": "apron",
		"lost_heaven_cantina": "cantina",
		"lost_heaven_mission_post": "board",
		"lost_heaven_clinic": "clinic",
		"lost_heaven_training_hall": "train",
		"lost_heaven_inn": "inn",
		"lost_heaven_town_hall": "hall",
		"lost_heaven_artisan_hall": "craft",
		"lost_heaven_gate": "gate_east",
		"lost_heaven_gate_west": "gate_west",
		"lh_hunt_chacal": "hunt",
		"player_spawn": "spawn_apron",
	}
	var key := str(map.get(p, p))
	if pois.has(key):
		return pois[key]
	if explore.has(key):
		return explore[key]["pos"]
	return pois.get("plaza", Vector3(4749.0, 0.15, -737.0))


func _maybe_world_suggest(bot: Dictionary, persona: Dictionary, goal: Dictionary) -> void:
	if suggest == null:
		return
	var name := str(bot.get("name", ""))
	var now := Time.get_unix_time_from_system()
	if now - float(_last_suggest.get(name, 0.0)) < 420.0:
		return
	if _rng.randf() > 0.18:
		return
	_last_suggest[name] = now
	var kinds: Array = persona.get("suggest_kinds", ["poi"]) if typeof(persona.get("suggest_kinds", null)) == TYPE_ARRAY else ["poi"]
	var kind := str(kinds[_rng.randi() % kinds.size()]) if kinds.size() > 0 else "poi"
	var text := "Suggestion hub : %s pourrait enrichir %s (obj. %s)." % [
		str(goal.get("goal_label", "ce lieu")),
		kind,
		str(persona.get("long", "vie hub")),
	]
	suggest.submit(name, kind, text, {
		"goal_id": str(goal.get("goal_id", "")),
		"play_mode": str(goal.get("play_mode", "")),
		"obj_long": str(persona.get("long", "")),
		"agent_id": str(persona.get("agent_id", "")),
		"admin_level": int(persona.get("admin_level", 0)),
		"account_login": str(persona.get("account_login", "")),
	})


func evaluate_barter_needs(bot_name: String) -> Dictionary:
	## Ticket 3.2 — Évalue les surplus et les manques d'inventaire d'un Joueur IA pour le troc P2P.
	var nm := bot_name.strip_edges()
	if economy == null or nm.is_empty():
		return {"bot": nm, "surplus": [], "deficits": []}
	var inv_res: Dictionary = economy.inventory(nm)
	var items: Array = inv_res.get("inventory", []) if typeof(inv_res.get("inventory")) == TYPE_ARRAY else []
	var counts: Dictionary = {
		"scrap_metal": 0,
		"water_capsule": 0,
		"dried_grain": 0,
		"binding_tape": 0,
		"oasis_condensate_filter": 0,
	}
	for it in items:
		if typeof(it) == TYPE_DICTIONARY:
			var iid := str(it.get("id", ""))
			counts[iid] = int(it.get("qty", 0))

	# Seuils d'équilibre de survie
	var target_mins := {
		"scrap_metal": 3,
		"water_capsule": 2,
		"dried_grain": 2,
		"binding_tape": 2,
	}
	var surplus: Array = []
	var deficits: Array = []
	for k in target_mins.keys():
		var have := int(counts.get(k, 0))
		var target := int(target_mins[k])
		if have >= target + 2:
			surplus.append({"id": k, "qty": have - target, "have": have})
		elif have < target:
			deficits.append({"id": k, "qty": target - have, "have": have})

	return {
		"bot": nm,
		"counts": counts,
		"surplus": surplus,
		"deficits": deficits,
	}


func evaluate_swg_precu_priority(
	bot_name: String,
	ham_medical_svc = null,
	harvesters_svc = null,
	creatures_svc = null,
	vendors_svc = null,
	housing_svc = null,
	bot_pos: Vector3 = Vector3.ZERO
) -> Dictionary:
	## Arbitrage autonome SWG Pre-CU complet (4 piliers) pour un Joueur IA :
	## 1. Soins critiques : Cantina (Battle Fatigue >= 200) ou Medcenter (Wounds >= 120).
	## 2. Faune & Survie : Campement sauvage si blessé loin de la ville, ou dépeçage de bête si cadavre proche.
	## 3. Extracteurs & Usines : Récolte si hopper >= 40 ou caisse d'usine prête.
	## 4. Commerce & Vendeurs : Retrait bancaire vendeur si solde >= 300, ou approvisionnement si surplus.
	## 5. Housing & Citoyenneté : Dépôt de maintenance si réserve basse (< 200), ou vote municipal si élection.
	var nm := bot_name.strip_edges()
	var decision := "patrol_or_survey"
	var reason := "nominal"
	var target_meta: Dictionary = {}

	var h_svc = ham_medical_svc if ham_medical_svc != null else ham_medical
	var harv_svc = harvesters_svc if harvesters_svc != null else harvesters
	var creat_svc = creatures_svc if creatures_svc != null else creatures
	var vend_svc = vendors_svc if vendors_svc != null else vendors_factories
	var house_svc = housing_svc if housing_svc != null else housing_cities

	var bf: int = 0
	var wounds_h: int = 0
	var cur_health: int = 1000
	var eff_health: int = 1000
	var hopper_ready: int = 0

	if h_svc != null and h_svc.has_method("status"):
		var st: Dictionary = h_svc.status(nm)
		var ham: Dictionary = st.get("ham", {}) if typeof(st.get("ham")) == TYPE_DICTIONARY else {}
		bf = int(ham.get("battle_fatigue", 0))
		var h_bar: Dictionary = ham.get("health", {}) if typeof(ham.get("health")) == TYPE_DICTIONARY else {}
		wounds_h = int(h_bar.get("wounds", 0))
		cur_health = int(h_bar.get("current", 1000))
		eff_health = int(h_bar.get("effective_max", 1000))

	if harv_svc != null and harv_svc.has_method("list_harvesters"):
		var owned: Array = harv_svc.list_harvesters(nm)
		for h in owned:
			if typeof(h) == TYPE_DICTIONARY:
				hopper_ready += int(h.get("hopper_qty", 0))

	# 1. Soins d'urgence urbains
	if bf >= 200:
		decision = "visit_cantina_perle"
		reason = "high_battle_fatigue"
	elif wounds_h >= 120:
		decision = "visit_medcenter_odo"
		reason = "high_combat_wounds"
	# 2. Survie en terre sauvage (Pilier 4)
	elif (wounds_h >= 40 or cur_health < eff_health / 2) and bot_pos != Vector3.ZERO and bot_pos.distance_to(ring_center) > 250.0:
		decision = "deploy_wilderness_camp"
		reason = "survival_field_regen"
		target_meta = {"pos": [bot_pos.x, bot_pos.y, bot_pos.z], "camp_tier": 1}
	# 3. Dépeçage d'une bête abattue (Pilier 4)
	elif creat_svc != null and creat_svc.has_method("list_active_corpses") and not (creat_svc.list_active_corpses() as Array).is_empty():
		var corpses: Array = creat_svc.list_active_corpses()
		var best_corpse: Dictionary = corpses[0]
		decision = "harvest_beast_corpse"
		reason = "unharvested_corpse_available"
		target_meta = {
			"corpse_id": str(best_corpse.get("corpse_id", "")),
			"resource_type": "hide" if _rng.randf() < 0.5 else "meat",
		}
	# 4. Vidange d'extracteurs ressources
	elif hopper_ready >= 40:
		decision = "collect_harvester_hopper"
		reason = "hopper_threshold_reached"
	else:
		# 5. Banque de Vendeur Joueur (Pilier 3)
		var handled := false
		if vend_svc != null and vend_svc.has_method("list_player_vendors"):
			var v_list: Array = vend_svc.list_player_vendors(nm)
			for v in v_list:
				if typeof(v) == TYPE_DICTIONARY and int(v.get("bank_credits", 0)) >= 300:
					decision = "collect_vendor_revenue"
					reason = "vendor_bank_funds_ready"
					target_meta = {"vendor_id": str(v.get("vendor_id", v.get("id", "")))}
					handled = true
					break
		# 6. Entretien Foncier & Villes (Pilier 2)
		if not handled and house_svc != null and (house_svc.has_method("list_player_structures") or house_svc.has_method("list_structures_for_owner")):
			var structures: Array = house_svc.list_player_structures(nm) if house_svc.has_method("list_player_structures") else house_svc.list_structures_for_owner(nm)
			for s in structures:
				var m_pool := int(s.get("maintenance_pool", s.get("maintenance_credits", 1000)))
				if typeof(s) == TYPE_DICTIONARY and m_pool <= 200:
					decision = "deposit_structure_maintenance"
					reason = "structure_maintenance_low"
					target_meta = {"structure_id": str(s.get("struct_id", s.get("id", ""))), "deposit_credits": 300}
					handled = true
					break

		# 7. Chasse & Assaut de Nids de Créatures (Lairs) & Décombres
		if not handled and creat_svc != null and creat_svc.has_method("list_lairs"):
			var lairs: Array = creat_svc.list_lairs()
			for l in lairs:
				if typeof(l) == TYPE_DICTIONARY:
					var lid: String = str(l.get("id", ""))
					var is_dest: bool = bool(l.get("is_destroyed", false))
					var is_harv: bool = bool(l.get("is_harvested", false))
					if is_dest and not is_harv:
						decision = "harvest_lair_debris"
						reason = "unharvested_lair_debris_available"
						target_meta = {"lair_id": lid}
						handled = true
						break
					elif not is_dest and cur_health >= eff_health * 0.7 and bf < 100:
						decision = "attack_creature_lair"
						reason = "active_lair_assault"
						target_meta = {"lair_id": lid, "damage": 250}
						handled = true
						break

		# 8. Enrôlement GCW Factions
		var f_svc = faction
		if not handled and f_svc != null and f_svc.has_method("get_faction_data"):
			var fdata: Dictionary = f_svc.get_faction_data(nm)
			if str(fdata.get("faction", "neutral")) == "neutral":
				var target_f := "imperial" if (hash(nm) % 2 == 0) else "rebel"
				decision = "enlist_gcw_faction"
				reason = "bot_civil_war_enlistment"
				target_meta = {"faction": target_f}
				handled = true

		# 9. Construction d'Habitat / Housing
		if not handled and house_svc != null and economy != null and (house_svc.has_method("list_player_structures") or house_svc.has_method("list_structures_for_owner")):
			var structs: Array = house_svc.list_player_structures(nm) if house_svc.has_method("list_player_structures") else house_svc.list_structures_for_owner(nm)
			var bot_creds: int = int(economy.status(nm).get("credits", 0)) if economy.has_method("status") else (economy.get_credits(nm) if economy.has_method("get_credits") else 0)
			if structs.is_empty() and bot_creds >= 500:
				var h_pos := bot_pos if bot_pos != Vector3.ZERO else Vector3(5550.0, 0.15, -1150.0)
				decision = "build_player_house"
				reason = "bot_housing_settlement"
				target_meta = {
					"structure_type": "deed_maison_sable_p",
					"name": "Résidence de %s" % nm,
					"pos": [h_pos.x, h_pos.y, h_pos.z]
				}
				handled = true

		# 10. Approvisionnement de la boutique en cas de surplus
		if not handled and vend_svc != null and economy != null:
			var barter_eval := evaluate_barter_needs(nm)
			var surplus: Array = barter_eval.get("surplus", [])
			if not surplus.is_empty():
				decision = "stock_vendor_or_bazaar"
				reason = "surplus_goods_to_sell"
				target_meta = {"item": str(surplus[0]), "qty": 5}
				handled = true

	return {
		"bot": nm,
		"decision": decision,
		"reason": reason,
		"target_meta": target_meta,
		"battle_fatigue": bf,
		"health_wounds": wounds_h,
		"hopper_ready_qty": hopper_ready,
	}


func evaluate_tactical_combat_step(
	bot_name: String,
	target_id: String,
	combat_svc = null,
	ham_svc = null
) -> Dictionary:
	## Pilier 1 SWG — Arbitrage de combat tactique : postures & frappes ciblées HAM
	var nm := bot_name.strip_edges()
	var c_svc = combat_svc if combat_svc != null else swg_combat
	var h_svc = ham_svc if ham_svc != null else ham_medical

	var chosen_posture := "upright"
	var chosen_strike := "body_hit"
	var reason := "standard_skirmish"

	var bot_posture := "upright"
	var tgt_posture := "upright"
	var tgt_active_statuses: Dictionary = {}
	var bot_hp_pct := 1.0

	if c_svc != null and c_svc.has_method("get_combat_state"):
		var st_b: Dictionary = c_svc.get_combat_state(nm)
		bot_posture = str(st_b.get("posture", "upright"))
		var st_t: Dictionary = c_svc.get_combat_state(target_id)
		tgt_posture = str(st_t.get("posture", "upright"))
		tgt_active_statuses = st_t.get("active_statuses", {}) if typeof(st_t.get("active_statuses")) == TYPE_DICTIONARY else {}

	if h_svc != null and h_svc.has_method("status"):
		var h_st: Dictionary = h_svc.status(nm)
		var h_bar: Dictionary = h_st.get("ham", {}).get("health", {}) if typeof(h_st.get("ham", {})) == TYPE_DICTIONARY else {}
		var cur := float(h_bar.get("current", 1000))
		var eff := float(maxi(1, int(h_bar.get("effective_max", 1000))))
		bot_hp_pct = cur / eff

	# 1. Sélection de posture
	if bot_hp_pct < 0.25:
		chosen_posture = "prone" # Réduit dégâts reçus de 50%
		reason = "defensive_cover"
	elif tgt_posture == "prone" or tgt_active_statuses.has("knockdown"):
		chosen_posture = "kneeling" # Bonus +20% précision
		reason = "exploit_fallen_target"
	else:
		chosen_posture = "upright"

	# 2. Sélection du coup tactique SWG
	if tgt_active_statuses.has("knockdown") or tgt_active_statuses.has("dizzy"):
		# Cible au sol ou étourdie : viser le Mind (Head Shot) pour incapacitation rapide
		chosen_strike = "head_shot"
		reason = "execute_head_shot_combo"
	elif tgt_posture == "upright" and not tgt_active_statuses.has("knockdown"):
		# Cible debout : tenter le Knockdown (Leg Sweep)
		chosen_strike = "leg_sweep"
		reason = "attempt_knockdown_sweep"
	elif not tgt_active_statuses.has("intimidate"):
		# Réduire la puissance adverse
		chosen_strike = "intimidate"
		reason = "debuff_enemy_damage"
	else:
		chosen_strike = "body_hit"
		reason = "standard_body_attrition"

	return {
		"bot": nm,
		"target": target_id,
		"chosen_posture": chosen_posture,
		"chosen_strike": chosen_strike,
		"reason": reason,
	}


func execute_autonomous_action(bot: Dictionary, priority: Dictionary) -> Dictionary:
	## Exécute concrètement l'action arbitrée sur les sous-systèmes du hub
	var nm := str(bot.get("name", ""))
	var decision := str(priority.get("decision", ""))
	var meta: Dictionary = priority.get("target_meta", {}) if typeof(priority.get("target_meta")) == TYPE_DICTIONARY else {}
	var out := {"ok": false, "decision": decision}

	match decision:
		"harvest_beast_corpse":
			var cid := str(meta.get("corpse_id", ""))
			var res_type := str(meta.get("resource_type", "hide"))
			if creatures != null and creatures.has_method("harvest_corpse") and not cid.is_empty():
				out = creatures.harvest_corpse(nm, cid, res_type)
		"deploy_wilderness_camp":
			var pos_arr: Array = meta.get("pos", [4749.0, 0.15, -737.0])
			var cx: float = float(pos_arr[0])
			var cz: float = float(pos_arr[2]) if pos_arr.size() >= 3 else float(pos_arr[1])
			if creatures != null and creatures.has_method("deploy_camp"):
				out = creatures.deploy_camp(nm, cx, cz, "abri_toile")
		"collect_vendor_revenue":
			var vid := str(meta.get("vendor_id", ""))
			if vendors_factories != null and vendors_factories.has_method("withdraw_vendor_credits") and not vid.is_empty():
				out = vendors_factories.withdraw_vendor_credits(nm, vid, 300)
		"deposit_structure_maintenance":
			var sid := str(meta.get("structure_id", ""))
			var credits := int(meta.get("deposit_credits", 300))
			if housing_cities != null and housing_cities.has_method("deposit_maintenance") and not sid.is_empty():
				out = housing_cities.deposit_maintenance(nm, sid, credits)
		"stock_vendor_or_bazaar":
			var it := str(meta.get("item", "ferraille"))
			var qty := int(meta.get("qty", 5))
			if vendors_factories != null and vendors_factories.has_method("post_to_bazaar"):
				out = vendors_factories.post_to_bazaar(nm, it, qty, 25, 48)
		"attack_creature_lair":
			var lid := str(meta.get("lair_id", ""))
			var dmg := int(meta.get("damage", 250))
			if creatures != null and creatures.has_method("attack_lair") and not lid.is_empty():
				out = creatures.attack_lair(nm, lid, dmg)
		"harvest_lair_debris":
			var lid := str(meta.get("lair_id", ""))
			if creatures != null and creatures.has_method("harvest_debris") and not lid.is_empty():
				out = creatures.harvest_debris(nm, lid)
		"enlist_gcw_faction":
			var fac := str(meta.get("faction", "imperial"))
			var f_svc = faction
			if f_svc != null and f_svc.has_method("enlist"):
				out = f_svc.enlist(nm, fac)
		"build_player_house":
			var pos_arr: Array = meta.get("pos", [5550.0, 0.15, -1150.0])
			var h_x: float = float(pos_arr[0])
			var h_z: float = float(pos_arr[2]) if pos_arr.size() >= 3 else float(pos_arr[1])
			var stype := str(meta.get("structure_type", "deed_maison_sable_p"))
			if housing_cities != null and housing_cities.has_method("deploy_structure"):
				out = housing_cities.deploy_structure(nm, stype, h_x, h_z)
		_:
			out = {"ok": true, "note": "decision handled via navigation/movement"}

	return out

