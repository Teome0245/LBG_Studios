extends RefCounted
class_name HubShow
## Show live La Perle + formation courte Talen (O-JEUX-SHOW / suite P2c).

const QUEST_ID := "lh_show_perle"
const ARTISTE_EID := "npc:core3_artiste_scene"
const ARTISTE_OID := 910016
const ARTISTE_NAME := "Artiste de scène"
const TALEN_EID := "npc:core3_talen_ress"
const CANTINA := Vector3(4939.0, 0.15, -802.0)
const STAGE := Vector3(4955.0, 0.15, -790.0)
const INN := Vector3(4809.0, 0.15, -672.0)
const NEAR_CANTINA_M := 55.0
const NEAR_INN_M := 50.0
const IDLE_S := 40.0
const LIVE_S := 70.0
const ENCORE_S := 12.0

const LINES_LIVE := [
	"Un rythme de récup' — ferraille qui chante sous les doigts.",
	"À La Perle, on ne joue pas neuf : on joue vrai.",
	"Merci d'être là — le désert attend dehors, ici on respire.",
	"Danse courte, morale haute. Jax, un verre pour ceux qui tiennent.",
]
const LINES_ENCORE := [
	"Bis — un dernier couplet avant la pause.",
	"Encore une mesure… puis on laisse la scène au silence.",
]

var phase: String = "idle"  # idle | live | encore
var phase_until: float = 0.0
var show_id: int = 0
var tips_this_show: int = 0
var _last_line_at: float = 0.0
var _trained: Dictionary = {}  # player -> unix last train
var _attended: Dictionary = {}  # player -> true (arrived / tipped this session)


func clear() -> void:
	phase = "idle"
	phase_until = 0.0
	show_id = 0
	tips_this_show = 0
	_last_line_at = 0.0
	_trained.clear()
	_attended.clear()


func bootstrap(sim) -> void:
	## Démarre en idle ; premier live après IDLE_S.
	var now := Time.get_unix_time_from_system()
	phase = "idle"
	phase_until = now + IDLE_S
	_ensure_artiste(sim, false)


func tick(sim, dt: float) -> void:
	if sim == null:
		return
	dt = clampf(dt, 0.001, 0.25)
	var now := Time.get_unix_time_from_system()
	if phase_until <= 0.0:
		bootstrap(sim)
		return
	if now >= phase_until:
		_advance_phase(sim, now)
	if phase == "live" or phase == "encore":
		_ensure_artiste(sim, true)
		_maybe_line(sim, now)
	else:
		_park_artiste(sim)


func mark_attended(player: String) -> void:
	_attended[_key(player)] = true


func is_live() -> bool:
	return phase == "live" or phase == "encore"


func snapshot() -> Dictionary:
	var now := Time.get_unix_time_from_system()
	return {
		"ok": true,
		"venue": "La Perle de Scrapaltai",
		"poi": "poi:lost_heaven_cantina",
		"phase": phase,
		"live": is_live(),
		"show_id": show_id,
		"tips_this_show": tips_this_show,
		"seconds_left": maxf(0.0, phase_until - now),
		"quest_id": QUEST_ID,
		"artiste": ARTISTE_NAME,
		"formation": {
			"npc": "Talen Ress",
			"poi": "poi:lost_heaven_inn",
			"hint": "Après le show (ou un tip), passe à l'auberge pour une courte formation.",
		},
	}


func validate_tip(sim, player: String, amount: int) -> Dictionary:
	if not is_live():
		return {
			"ok": false,
			"error": "show_not_live",
			"hint": "Pas de spectacle en cours — reviens pendant le show à La Perle.",
			"show": snapshot(),
		}
	if not _player_near(sim, player, CANTINA, NEAR_CANTINA_M):
		return {
			"ok": false,
			"error": "too_far_from_stage",
			"hint": "Approche-toi de La Perle (scène) pour tipper.",
			"show": snapshot(),
		}
	if amount < 1:
		return {"ok": false, "error": "tip_too_small", "hint": "Tip min 1 Cr"}
	return {"ok": true, "show": snapshot()}


func on_tip_ok(player: String, amount: int) -> Dictionary:
	tips_this_show += 1
	mark_attended(player)
	return {
		"ok": true,
		"tipped": amount,
		"tips_this_show": tips_this_show,
		"show_id": show_id,
		"message": "L'artiste salue ton pourboire depuis la scène.",
		"show": snapshot(),
	}


func train(sim, economy, player: String) -> Dictionary:
	## Formation courte chez Talen — une fois / 10 min, après show/tip.
	var key := _key(player)
	if not bool(_attended.get(key, false)):
		# Accepte aussi si quête show active/completed côté economy.
		var ok_hist := false
		if economy != null and economy.has_method("status"):
			var st: Dictionary = economy.status(player)
			for a in st.get("active", []):
				if typeof(a) == TYPE_DICTIONARY and str(a.get("id", "")) == QUEST_ID:
					ok_hist = true
			for c in st.get("completed", []):
				if str(c) == QUEST_ID:
					ok_hist = true
		if not ok_hist:
			return {
				"ok": false,
				"error": "need_show_first",
				"hint": "Assiste au show (ou tippe) à La Perle avant la formation Talen.",
				"show": snapshot(),
			}
	if not _player_near(sim, player, INN, NEAR_INN_M):
		return {
			"ok": false,
			"error": "too_far_from_inn",
			"hint": "Talen Ress forme à l'auberge — rapproche-toi.",
			"show": snapshot(),
		}
	var now := Time.get_unix_time_from_system()
	var last := float(_trained.get(key, 0.0))
	if now - last < 600.0:
		return {
			"ok": false,
			"error": "train_cooldown",
			"hint": "Formation déjà donnée — reviens plus tard.",
			"cooldown_s": int(600.0 - (now - last)),
		}
	_trained[key] = now
	if economy != null and economy.has_method("remember_relation"):
		economy.remember_relation(
			player,
			TALEN_EID,
			"train",
			"Talen t'a donné une courte formation scène.",
			{"value": "scene_basics", "quest_id": QUEST_ID}
		)
	if economy != null and economy.has_method("log_session_event"):
		economy.log_session_event(
			player,
			"show_train",
			"Formation courte Talen Ress (scène / moral).",
			{"quest_id": QUEST_ID}
		)
	_stream(sim, "show.train", "Talen Ress forme %s à l'auberge." % key, "Talen Ress")
	return {
		"ok": true,
		"trainer": "Talen Ress",
		"lesson": "Respiration, rythme, regard public — moral du hub avant la technique.",
		"xp_scene": 8,
		"show": snapshot(),
		"source": "prime_hub",
	}


func _advance_phase(sim, now: float) -> void:
	if phase == "idle":
		phase = "live"
		show_id += 1
		tips_this_show = 0
		phase_until = now + LIVE_S
		_ensure_artiste(sim, true)
		_stream(sim, "show.start", "Le spectacle démarre à La Perle.", ARTISTE_NAME)
		if sim != null and sim.ambient != null:
			sim.ambient.enqueue_say(ARTISTE_NAME, ARTISTE_OID, "Bonsoir La Perle — on ouvre la scène.", "show")
	elif phase == "live":
		phase = "encore"
		phase_until = now + ENCORE_S
		_stream(sim, "show.encore", "Bis à La Perle.", ARTISTE_NAME)
	else:
		phase = "idle"
		phase_until = now + IDLE_S
		_park_artiste(sim)
		_stream(sim, "show.end", "Fin du set à La Perle — pause.", ARTISTE_NAME)


func _maybe_line(sim, now: float) -> void:
	if now - _last_line_at < 18.0:
		return
	_last_line_at = now
	var pool: Array = LINES_LIVE if phase == "live" else LINES_ENCORE
	if pool.is_empty() or sim == null or sim.ambient == null:
		return
	var line := str(pool[randi() % pool.size()])
	sim.ambient.enqueue_say(ARTISTE_NAME, ARTISTE_OID, line, "show")


func _ensure_artiste(sim, on_stage: bool) -> void:
	if sim == null:
		return
	var pos := STAGE if on_stage else CANTINA
	var wz: Vector2 = _walkable(sim, pos.x, pos.z)
	if sim.entities.has(ARTISTE_EID):
		var e: Dictionary = sim.entities[ARTISTE_EID]
		e["pos"] = Vector3(wz.x, pos.y, wz.y)
		e["target"] = Vector3.ZERO
		e["wander_r"] = 0.0 if on_stage else 4.0
		e["goal"] = "show_stage" if on_stage else "show_idle"
		e["speed"] = 0.0 if on_stage else 3.5
		e["active"] = true
		e["ambient"] = "Spectacle à La Perle — tip si le cœur t'en dit." if on_stage else "Pause. Le prochain set arrive."
		return
	sim.entities[ARTISTE_EID] = {
		"eid": ARTISTE_EID,
		"oid": ARTISTE_OID,
		"kind": "npc",
		"name": ARTISTE_NAME,
		"pos": Vector3(wz.x, pos.y, wz.y),
		"target": Vector3.ZERO,
		"speed": 0.0 if on_stage else 3.5,
		"is_bot": false,
		"goal": "show_stage" if on_stage else "show_idle",
		"play_mode": "show",
		"quest_id": QUEST_ID,
		"linger_until": 0.0,
		"stuck_ticks": 0,
		"home_x": wz.x,
		"home_z": wz.y,
		"wander_r": 0.0 if on_stage else 4.0,
		"ambient": "Spectacle à La Perle." if on_stage else "Pause scène.",
		"active": true,
	}


func _park_artiste(sim) -> void:
	_ensure_artiste(sim, false)


func _player_near(sim, player: String, anchor: Vector3, radius_m: float) -> bool:
	if sim == null:
		# Selftest / tip sans sim : toléré uniquement si on force via tests.
		return true
	var want := _key(player).to_lower()
	for eid in sim.entities.keys():
		var e: Dictionary = sim.entities[eid]
		if str(e.get("kind", "")) != "player" or bool(e.get("is_bot", false)):
			continue
		if str(e.get("name", "")).strip_edges().to_lower() != want:
			continue
		var p: Vector3 = e["pos"]
		return Vector2(p.x - anchor.x, p.z - anchor.z).length() <= radius_m
	# Joueur pas encore spawn en sim (HTTP seul) : ne pas bloquer tip live.
	return true


func _walkable(sim, x: float, z: float) -> Vector2:
	if sim != null and sim.has_method("_walkable_xz"):
		return sim._walkable_xz(x, z) as Vector2
	return Vector2(x, z)


func _key(player: String) -> String:
	return player.strip_edges()


func _stream(sim, kind: String, text: String, actor: String) -> void:
	if sim != null and sim.has_method("_stream"):
		sim._stream(kind, text, actor, "show:perle", {"quest_id": QUEST_ID, "show_id": show_id})
