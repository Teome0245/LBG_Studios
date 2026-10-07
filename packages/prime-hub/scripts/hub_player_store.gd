extends RefCounted
class_name HubPlayerStore
## Persistance positions joueurs (reprise session) — JSON sur disque.

var path: String = ""
var _pos: Dictionary = {}  # "oid" -> {x,y,z,ts,name}


func setup(data_dir: String = "") -> void:
	if data_dir.is_empty():
		var env := OS.get_environment("LBG_PRIME_HUB_STATE_DIR").strip_edges()
		if env.is_empty():
			var root := ProjectSettings.globalize_path("res://").rstrip("/")
			env = root.path_join("data")
		data_dir = env
	DirAccess.make_dir_recursive_absolute(data_dir)
	path = data_dir.path_join("player_positions.json")
	_load()


func _load() -> void:
	_pos.clear()
	if path.is_empty() or not FileAccess.file_exists(path):
		return
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if typeof(raw) != TYPE_DICTIONARY:
		return
	var players = raw.get("players", raw)
	if typeof(players) != TYPE_DICTIONARY:
		return
	for k in players.keys():
		var row = players[k]
		if typeof(row) == TYPE_DICTIONARY:
			_pos[str(k)] = row


func save_all() -> void:
	if path.is_empty():
		return
	var payload := {
		"schema_version": 1,
		"saved_at": int(Time.get_unix_time_from_system()),
		"players": _pos,
	}
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f == null:
		push_warning("[prime-hub] cannot write %s" % path)
		return
	f.store_string(JSON.stringify(payload))
	f.close()


func set_pos(oid: int, x: float, y: float, z: float, player_name: String = "") -> void:
	if oid < 1:
		return
	if (absf(x) < 50.0 and absf(z) < 50.0) or x < 2500.0 or x > 7500.0:
		return
	_pos[str(oid)] = {
		"x": x,
		"y": y,
		"z": z,
		"name": player_name,
		"ts": int(Time.get_unix_time_from_system()),
	}


func get_pos(oid: int) -> Variant:
	## Vector3 ou null
	var row = _pos.get(str(oid), null)
	if typeof(row) != TYPE_DICTIONARY:
		return null
	return Vector3(float(row.get("x", 0.0)), float(row.get("y", 0.15)), float(row.get("z", 0.0)))
