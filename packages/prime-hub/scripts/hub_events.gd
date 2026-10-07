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


func setup(announce_cb: Callable = Callable()) -> void:
	_rng.randomize()
	_on_announce = announce_cb
	_catalog.clear()
	var path := _HubPaths.data_file("events/event_lh_scrap_fall_convoy.json")
	var raw: Variant = _HubPaths.read_json(path)
	if typeof(raw) == TYPE_DICTIONARY and str(raw.get("id", "")) != "":
		_catalog.append(raw)
	# Boot LAN : activer tout de suite pour board + rumeur.
	if not _catalog.is_empty():
		_activate(_catalog[0], Time.get_unix_time_from_system())


func tick(now: float) -> void:
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
		"source": "prime_hub",
	}


func _activate(ev: Dictionary, now: float) -> void:
	active = ev.duplicate(true)
	active_id = str(ev.get("id", ""))
	var dur = ev.get("duration_s", [1200, 2400])
	var d0 := 1200.0
	var d1 := 2400.0
	if typeof(dur) == TYPE_ARRAY and dur.size() >= 2:
		d0 = float(dur[0])
		d1 = float(dur[1])
	ends_at = now + _rng.randf_range(d0, d1)
	cooldown_until = 0.0
	print("[prime-hub] event ON %s until +%.0fs" % [active_id, ends_at - now])
	var ann = ev.get("announce", {})
	if typeof(ann) == TYPE_DICTIONARY and _on_announce.is_valid():
		_on_announce.call(
			str(ann.get("from", "Board")),
			int(ann.get("oid", 0)),
			str(ann.get("text", "")),
			"ia"
		)


func _deactivate(now: float) -> void:
	var cd = active.get("cooldown_s", [480, 900])
	var c0 := 480.0
	var c1 := 900.0
	if typeof(cd) == TYPE_ARRAY and cd.size() >= 2:
		c0 = float(cd[0])
		c1 = float(cd[1])
	print("[prime-hub] event OFF %s" % active_id)
	active_id = ""
	active = {}
	ends_at = 0.0
	cooldown_until = now + _rng.randf_range(c0, c1)
