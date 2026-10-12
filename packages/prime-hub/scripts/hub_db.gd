extends RefCounted
class_name HubDb
## Couche SQLite transactionnelle pour prime-hub — ticket 2.1.
##
## SQLite via le binaire `sqlite3` (WAL + transactions) sur un thread dédié :
##   - les écritures sont enqueueées et appliquées en lot via un seul
##     `BEGIN IMMEDIATE … COMMIT` : le tick serveur n'attend jamais le disque ;
##   - journal_mode=WAL + synchronous=NORMAL : coupure forcée (kill -9) ne
##     corrompt rien (commit atomique / rollback auto) ;
##   - si le binaire est absent, `available == false` → les stores retombent
##     sur leur export JSON historique (aucune régression).
##
## Persistance: single shared instance via get_shared().

const _HubPaths = preload("res://scripts/hub_paths.gd")

const _SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS meta(
	k TEXT PRIMARY KEY,
	v TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS player_positions(
	oid INTEGER PRIMARY KEY,
	x REAL NOT NULL,
	y REAL NOT NULL,
	z REAL NOT NULL,
	name TEXT NOT NULL DEFAULT '',
	ts INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS accounts(
	login TEXT PRIMARY KEY,
	data TEXT NOT NULL,
	updated_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS player_state(
	player TEXT PRIMARY KEY,
	data TEXT NOT NULL,
	updated_at INTEGER NOT NULL
);
"""

static var _shared = null

var db_path: String = ""
var available: bool = false
var last_error: String = ""
var binary: String = "sqlite3"

var _mutex := Mutex.new()
var _job_sem := Semaphore.new()
var _queue: Array = []
var _pending: int = 0
var _writes: int = 0
var _flushes: int = 0
var _errors: int = 0
var _stop: bool = false
var _thread: Thread = null


static func get_shared():
	if _shared == null:
		_shared = load("res://scripts/hub_db.gd").new()
		_shared.setup()
	return _shared


static func escape_sql(s: String) -> String:
	return s.replace("'", "''")


static func json_literal(blob: Dictionary) -> String:
	return escape_sql(JSON.stringify(blob))


func setup() -> bool:
	return setup_at(_HubPaths.data_file("prime_hub.sqlite3"))


func setup_at(path: String) -> bool:
	db_path = path.strip_edges()
	if db_path.is_empty():
		push_warning("[prime-hub][db] empty db path")
		return false
	var env_bin := OS.get_environment("LBG_SQLITE_BIN").strip_edges()
	if not env_bin.is_empty():
		binary = env_bin
	var bout: Array = []
	if OS.execute(binary, ["-version"], bout, true) != 0:
		available = false
		push_warning("[prime-hub][db] binaire sqlite introuvable (%s) — fallback JSON" % binary)
		return false
	DirAccess.make_dir_recursive_absolute(db_path.get_base_dir())
	if not exec_sync(_SCHEMA):
		available = false
		push_warning("[prime-hub][db] schema init failed: %s" % last_error)
		return false
	available = true
	_stop = false
	_thread = Thread.new()
	_thread.start(_worker)
	_flushes = 0
	_writes = 0
	_errors = 0
	return true


func shutdown() -> void:
	wait_idle(8000)
	if _thread != null:
		_stop = true
		_job_sem.post()
		_thread.wait_to_finish()
		_thread = null
	if available and db_path != "":
		exec_sync("PRAGMA wal_checkpoint(TRUNCATE);")


func _worker() -> void:
	while true:
		if not _job_sem.try_wait():
			if _stop:
				break
			if OS != null:
				OS.delay_msec(5)
			else:
				break
			continue
		_mutex.lock()
		if _queue.is_empty():
			var stop := _stop
			_mutex.unlock()
			if stop:
				break
			continue
		var batch: Array = _queue
		_queue = []
		_mutex.unlock()
		_run_batch(batch)
		_mutex.lock()
		_pending -= batch.size()
		if _pending < 0:
			_pending = 0
		_mutex.unlock()


func _run_batch(batch: Array) -> void:
	if batch.is_empty():
		return
	var sql: String = "PRAGMA busy_timeout=5000;\nBEGIN IMMEDIATE;\n"
	for s in batch:
		sql += str(s) + "\n"
	sql += "COMMIT;\n"
	var out: Array = []
	var safe_sql := sql.replace('"', '\\"')
	var rc := OS.execute(binary, [db_path, safe_sql], out, true)
	if rc != 0:
		_errors += 1
		last_error = String(out.back()) if out.size() > 0 else "sqlite rc=%d" % rc
		push_warning("[prime-hub][db] write failed rc=%d %s" % [rc, last_error])
	else:
		_flushes += 1
		_writes += batch.size()
		last_error = ""


func enqueue(sql: Array) -> void:
	if not available or _thread == null:
		return
	if sql.is_empty():
		return
	_mutex.lock()
	for s in sql:
		_queue.append(String(s))
	_pending += sql.size()
	_mutex.unlock()
	_job_sem.post()


func exec_sync(sql: String) -> bool:
	if not available and db_path == "":
		return false
	var out: Array = []
	var safe_sql := ("PRAGMA busy_timeout=5000; " + sql).replace('"', '\\"')
	var rc := OS.execute(binary, [db_path, safe_sql], out, true)
	if rc != 0:
		last_error = String(out.back()) if out.size() > 0 else "sqlite rc=%d" % rc
		return false
	last_error = ""
	return true


func query_rows(sql: String) -> Array:
	## Retourne un Array de Dictionaries (lignes) ou [].
	if not available:
		return []
	var out: Array = []
	var safe_sql := sql.replace('"', '\\"')
	var rc := OS.execute(binary, ["-json", db_path, safe_sql], out, true)
	if rc != 0:
		last_error = String(out.back()) if out.size() > 0 else "sqlite rc=%d" % rc
		push_warning("[prime-hub][db] query failed rc=%d %s" % [rc, last_error])
		return []
	last_error = ""
	if out.is_empty():
		return []
	var text := ""
	for line in out:
		text += str(line)
	if text.strip_edges().is_empty():
		return []
	var parsed: Variant = JSON.parse_string(text)
	if typeof(parsed) != TYPE_ARRAY:
		return []
	return parsed


func dump(table_name: String) -> Array:
	return query_rows("SELECT * FROM %s;" % table_name)


func meta_set(k: String, v: String) -> bool:
	return exec_sync("INSERT INTO meta(k,v) VALUES('%s','%s') ON CONFLICT(k) DO UPDATE SET v=excluded.v;" % [escape_sql(k), escape_sql(v)])


func meta_get(k: String, default_v: String = "") -> String:
	var rows := query_rows("SELECT v FROM meta WHERE k='%s';" % escape_sql(k))
	if rows.size() > 0 and typeof(rows[0]) == TYPE_DICTIONARY:
		return str(rows[0].get("v", default_v))
	return default_v


func count_rows(table_name: String) -> int:
	var rows := query_rows("SELECT count(*) AS n FROM %s;" % table_name)
	if rows.size() > 0 and typeof(rows[0]) == TYPE_DICTIONARY:
		return int(rows[0].get("n", 0))
	return 0


func integrity_ok() -> bool:
	var rows := query_rows("PRAGMA integrity_check;")
	if rows.size() >= 1 and typeof(rows[0]) == TYPE_DICTIONARY:
		return str(rows[0].get("integrity_check", "??")).to_lower() == "ok"
	return false


func checkpoint() -> void:
	if available:
		exec_sync("PRAGMA wal_checkpoint(TRUNCATE);")


func wait_idle(max_ms: int = 8000) -> bool:
	if not available or _thread == null:
		return _pending == 0
	var t0 := Time.get_ticks_msec()
	while true:
		_mutex.lock()
		var n := _pending
		_mutex.unlock()
		if n <= 0:
			return true
		if Time.get_ticks_msec() - t0 > max_ms:
			return false
		OS.delay_msec(5)
	return false


func stats() -> Dictionary:
	return {
		"ok": available,
		"backend": "sqlite3_wal",
		"path": db_path,
		"binary": binary,
		"rows_player_positions": count_rows("player_positions") if available else -1,
		"rows_accounts": count_rows("accounts") if available else -1,
		"rows_player_state": count_rows("player_state") if available else -1,
		"writes": _writes,
		"flushes": _flushes,
		"errors": _errors,
		"pending": _pending,
		"integrity": integrity_ok() if available else false,
		"last_error": last_error,
	}