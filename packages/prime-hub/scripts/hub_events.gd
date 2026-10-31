extends RefCounted
class_name HubEvents
## C4 — events hub dynamiques (board + annonce chat). LAN : durées compressées.

const _HubPaths = preload("res://scripts/hub_paths.gd")

var _catalog: Array = []
var _rng := RandomNumberGenerator.new()
var active_id: String = ""
var active: Dictionary = {}
var ends_at: float = 0.0
var cooldown_until: float = 0.0
var _on_announce: Callable = Callable()
var world_stream = null
var world_clock = null

var weather_phase: String = "calm"  # "calm", "warning", "storm", "clearing"
var weather_intensity: float = 0.0  # 0.0 à 1.0
var weather_kind: String = "clear"  # "clear", "sandstorm"
var weather_shelter_required: bool = false
var weather_phase_ends_at: float = 0.0
var _weather_cfg: Dictionary = {}


func attach_world_stream(stream_svc) -> void:
	world_stream = stream_svc


func attach_world_clock(clock_svc) -> void:
	world_clock = clock_svc


func _stream(kind: String, text: String, actor: String = "", zone: String = "", detail: Dictionary = {}) -> void:
	if world_stream != null and world_stream.has_method("emit"):
		world_stream.emit(kind, text, actor, zone, detail)


func setup(announce_cb: Callable = Callable()) -> void:
	_rng.randomize()
	_on_announce = announce_cb
	_catalog.clear()
	var paths := [
		"events/event_lh_scrap_fall_convoy.json",
		"events/event_lh_sandstorm.json",
	]
	for p in paths:
		var path := _HubPaths.data_file(p)
		var raw: Variant = _HubPaths.read_json(path)
		if typeof(raw) == TYPE_DICTIONARY and str(raw.get("id", "")) != "":
			_catalog.append(raw)
	# Boot LAN : activer tout de suite pour board + rumeur.
	if not _catalog.is_empty():
		_activate(_catalog[0], Time.get_unix_time_from_system())


func tick(now: float) -> void:
	_tick_weather(now)
	if not active_id.is_empty() and now >= ends_at:
		_deactivate(now)
		return
	if active_id.is_empty() and now >= cooldown_until and not _catalog.is_empty():
		var pick = _catalog[_rng.randi() % _catalog.size()]
		_activate(pick, now)


func is_active(event_id: String = "") -> bool:
	if active_id.is_empty():
		return false
	if event_id.is_empty():
		return true
	return active_id == event_id


func is_weather_shelter_active() -> bool:
	return weather_shelter_required


func get_weather_state() -> Dictionary:
	return {
		"kind": weather_kind,
		"phase": weather_phase,
		"intensity": weather_intensity,
		"shelter_required": weather_shelter_required,
		"label": _weather_phase_label(),
	}


func _weather_phase_label() -> String:
	match weather_phase:
		"warning":
			return "Avis de tempête"
		"storm":
			return "Tempête de ferraille active"
		"clearing":
			return "Accalmie / Retombées"
		_:
			return "Ciel dégagé"


func trigger_sandstorm(warning_s: float = 45.0, storm_s: float = 240.0, clearing_s: float = 45.0, at_time: float = -1.0) -> void:
	var now := at_time if at_time > 0.0 else Time.get_unix_time_from_system()
	_weather_cfg = {
		"warning_s": warning_s,
		"storm_s": storm_s,
		"clearing_s": clearing_s,
	}
	weather_kind = "sandstorm"
	weather_phase = "warning"
	weather_intensity = 0.35
	weather_shelter_required = true
	weather_phase_ends_at = now + warning_s
	_stream("weather.phase", "Avis de tempête de sable : vents violents détectés à l'est.", "Météo", "scrapaltai", get_weather_state())
	if _on_announce.is_valid():
		_on_announce.call("Guet de Scrapaltai", 910002, "Alerte Météo : Avis de tempête de sable sur le plateau. Mettez-vous à l'abri !", "ia")


func _start_sandstorm(ev: Dictionary, _now: float) -> void:
	var w: Dictionary = ev.get("weather", {}) if ev.get("weather") is Dictionary else {}
	var warn_s := float(w.get("warning_s", 45.0))
	var st_s := float(w.get("storm_s", 240.0))
	var cl_s := float(w.get("clearing_s", 45.0))
	trigger_sandstorm(warn_s, st_s, cl_s)


func _stop_sandstorm(_now: float) -> void:
	weather_kind = "clear"
	weather_phase = "calm"
	weather_intensity = 0.0
	weather_shelter_required = false
	weather_phase_ends_at = 0.0
	_stream("weather.phase", "Retour au calme météo sur Lost Heaven.", "Météo", "scrapaltai", get_weather_state())


func _tick_weather(now: float) -> void:
	if weather_phase == "calm":
		return
	if weather_phase_ends_at > 0.0 and now >= weather_phase_ends_at:
		match weather_phase:
			"warning":
				weather_phase = "storm"
				weather_intensity = 1.0
				weather_shelter_required = true
				var storm_dur := float(_weather_cfg.get("storm_s", 240.0))
				weather_phase_ends_at = now + storm_dur
				_stream("weather.phase", "La tempête de sable frappe le plateau de plein fouet !", "Météo", "scrapaltai", get_weather_state())
			"storm":
				weather_phase = "clearing"
				weather_intensity = 0.4
				weather_shelter_required = false
				var cl_dur := float(_weather_cfg.get("clearing_s", 45.0))
				weather_phase_ends_at = now + cl_dur
				_stream("weather.phase", "Les vents faiblissent : accalmie en cours.", "Météo", "scrapaltai", get_weather_state())
			"clearing":
				_stop_sandstorm(now)


func board_quest_ids() -> Array:
	if active_id.is_empty():
		return []
	var qid := str(active.get("board_quest_id", "")).strip_edges()
	if qid.is_empty():
		return []
	return [qid]


func rumor_hint() -> String:
	if active_id.is_empty():
		return ""
	return str(active.get("rumor_hint", "")).strip_edges()


func snapshot() -> Dictionary:
	return {
		"ok": true,
		"active": not active_id.is_empty(),
		"event_id": active_id,
		"title": str(active.get("title", "")),
		"ends_at": ends_at,
		"cooldown_until": cooldown_until,
		"board_quest_id": str(active.get("board_quest_id", "")),
		"rumor_hint": rumor_hint(),
		"weather": get_weather_state(),
		"world_clock": world_clock.get_time_state() if (world_clock != null and world_clock.has_method("get_time_state")) else {},
		"source": "prime_hub",
	}


func _activate(ev: Dictionary, now: float) -> void:
	active = ev.duplicate(true)
	active_id = str(ev.get("id", ""))
	if str(ev.get("event_kind", "")) == "weather_sandstorm":
		_start_sandstorm(ev, now)
	var dur = ev.get("duration_s", [1200, 2400])
	var d0 := 1200.0
	var d1 := 2400.0
	if typeof(dur) == TYPE_ARRAY and dur.size() >= 2:
		d0 = float(dur[0])
		d1 = float(dur[1])
	ends_at = now + _rng.randf_range(d0, d1)
	cooldown_until = 0.0
	print("[prime-hub] event ON %s until +%.0fs" % [active_id, ends_at - now])
	var title := str(ev.get("title", active_id))
	var hint := str(ev.get("rumor_hint", "")).strip_edges()
	var line := title
	if not hint.is_empty():
		line = "%s — %s" % [title, hint]
	_stream("event.activate", line, "Monde", "scrapaltai", {"event_id": active_id, "board_quest_id": str(ev.get("board_quest_id", ""))})
	var ann = ev.get("announce", {})
	if typeof(ann) == TYPE_DICTIONARY and _on_announce.is_valid():
		_on_announce.call(
			str(ann.get("from", "Board")),
			int(ann.get("oid", 0)),
			str(ann.get("text", "")),
			"ia"
		)


func _deactivate(now: float) -> void:
	if str(active.get("event_kind", "")) == "weather_sandstorm":
		_stop_sandstorm(now)
	var cd = active.get("cooldown_s", [480, 900])
	var c0 := 480.0
	var c1 := 900.0
	if typeof(cd) == TYPE_ARRAY and cd.size() >= 2:
		c0 = float(cd[0])
		c1 = float(cd[1])
	print("[prime-hub] event OFF %s" % active_id)
	var off_id := active_id
	var off_title := str(active.get("title", off_id))
	_stream("event.end", "Fin de l'événement : %s." % off_title, "Monde", "scrapaltai", {"event_id": off_id})
	active_id = ""
	active = {}
	ends_at = 0.0
	cooldown_until = now + _rng.randf_range(c0, c1)
