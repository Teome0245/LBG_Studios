extends RefCounted
class_name HubPlayerStore
## Persistance positions joueurs (reprise session) — ticket 2.1.
## Store transactionnel SQLite (table player_positions) + export JSON
## périodique conservé (audit + smokes existants).

const _HubPaths = preload("res://scripts/hub_paths.gd")
const HubDbScript = preload("res://scripts/hub_db.gd")

var path: String = ""  # export JSON
var db: HubDbScript = null
var _pos: Dictionary = {}  # "oid" -> {x,y,z,ts,name}
var _export_every := 6  # ~30 s @ save ~5 s
var _saves_since_export: int = 0


func setup(data_dir: String = "") -> void:
	if data_dir.is_empty():
		var env := OS.get_environment("LBG_PRIME_HUB_STATE_DIR").strip_edges()
		if env.is_empty():
			var root := ProjectSettings.globalize_path("res://").rstrip("/")
			env = root.path_join("data")
		data_dir = env
	DirAccess.make_dir_recursive_absolute(data_dir)
	path = data_dir.path_join("player_positions.json")
	db = HubDbScript.get_shared()
	_load()


func _load() -> void:
	_pos.clear()
	if db != null and db.available:
		var rows := db.query_rows("SELECT oid,x,y,z,name,ts FROM player_positions;")
		if rows.size() > 0:
			for r in rows:
				var key := str(r.get("oid", 0))
				if key == "0":
					continue
				_pos[key] = {
					"x": float(r.get("x", 0.0)),
					"y": float(r.get("y", 0.15)),
					"z": float(r.get("z", 0.0)),
					"name": str(r.get("name", "")),
					"ts": int(r.get("ts", 0)),
				}
		# Migration legacy JSON → SQLite (une seule fois, si table vide).
		if _pos.is_empty() and FileAccess.file_exists(path):
			var legacy = _read_legacy_json()
			if legacy.size() > 0:
				_pos = legacy
				save_all()
				db.wait_idle(8000)
		return
	# Fallback JSON si SQLite indisponible.
	_pos = _read_legacy_json()


func _read_legacy_json() -> Dictionary:
	var out: Dictionary = {}
	if path.is_empty() or not FileAccess.file_exists(path):
		return out
	var raw: Variant = JSON.parse_string(FileAccess.open(path, FileAccess.READ).get_as_text())
	if typeof(raw) != TYPE_DICTIONARY:
		return out
	var players = raw.get("players", raw)
	if typeof(players) != TYPE_DICTIONARY:
		return out
	for k in players.keys():
		var row = players[k]
		if typeof(row) == TYPE_DICTIONARY:
			out[str(k)] = row
	return out


func save_all() -> void:
	if _pos.is_empty():
		return
	if db != null and db.available:
		var stmts: Array = []
		var now := int(Time.get_unix_time_from_system())
		for key in _pos.keys():
			var row: Dictionary = _pos[key]
			stmts.append(
				"INSERT INTO player_positions(oid,x,y,z,name,ts) VALUES(%d,%.3f,%.3f,%.3f,'%s',%d) "
				% [
					int(key),
					float(row.get("x", 0.0)),
					float(row.get("y", 0.15)),
					float(row.get("z", 0.0)),
					HubDbScript.escape_sql(str(row.get("name", ""))),
					int(row.get("ts", now)),
				]
				+ "ON CONFLICT(oid) DO UPDATE SET x=excluded.x,y=excluded.y,z=excluded.z,"
				+ "name=excluded.name,ts=excluded.ts;"
			)
		db.enqueue(stmts)
	else:
		_export_json()
		return
	_saves_since_export += 1
	if _saves_since_export >= _export_every:
		_saves_since_export = 0
		_export_json()
		if db != null:
			db.checkpoint()


func _export_json() -> void:
	_HubPaths.write_json(path, {
		"schema_version": 2,
		"backend": "sqlite" if (db != null and db.available) else "json",
		"saved_at": int(Time.get_unix_time_from_system()),
		"players": _pos,
	})


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


func stats() -> Dictionary:
	var base := {"ok": true, "cached_players": _pos.size()}
	if db != null:
		base.merge(db.stats())
	else:
		base["ok"] = false
	return base


func flush() -> void:
	if db != null:
		db.wait_idle(8000)


func shutdown() -> void:
	_export_json()
	if db != null:
		db.shutdown()