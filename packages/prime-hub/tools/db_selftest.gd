extends SceneTree
## Selftest headless ticket 2.1 — SQLite hub_player_store / accounts / player_state.
## Usage: godot --headless --path packages/prime-hub --script res://tools/db_selftest.gd
## Exit 0 = OK ; exit 1 = échec. Aucun réseau requis (sqlite3 local).

const HubDbScript = preload("res://scripts/hub_db.gd")
const HubPlayerStoreScript = preload("res://scripts/hub_player_store.gd")
const HubAuthScript = preload("res://scripts/hub_auth.gd")
const HubEconomyScript = preload("res://scripts/hub_economy.gd")

var _fails := 0
var _checks := 0


func _check(name: String, ok: bool, detail: String = "") -> void:
	_checks += 1
	if not ok:
		_fails += 1
	print("[%s] %s%s" % ["PASS" if ok else "FAIL", name, (" — " + detail) if detail != "" else ""])


func _init() -> void:
	var state_dir := OS.get_environment("LBG_PRIME_HUB_STATE_DIR").strip_edges()
	if state_dir.is_empty():
		state_dir = "/tmp/opencode/db_selftest/state"
		OS.set_environment("LBG_PRIME_HUB_STATE_DIR", state_dir)
	DirAccess.make_dir_recursive_absolute(state_dir)
	DirAccess.remove_absolute(state_dir.path_join("prime_hub.sqlite3"))
	DirAccess.remove_absolute(state_dir.path_join("prime_hub.sqlite3-wal"))
	DirAccess.remove_absolute(state_dir.path_join("prime_hub.sqlite3-shm"))
	DirAccess.remove_absolute(state_dir.path_join("player_positions.json"))
	OS.set_environment("LBG_PRIME_HUB_STATE_DIR", state_dir)

	var db = HubDbScript.get_shared()
	_check("db available", db.available, db.db_path)
	_check("db wal schema", db.db_path.ends_with("prime_hub.sqlite3"), db.db_path)

	# --- Positions (async) : enqueue non bloquant, flush~5s, reload depuis SQLite.
	var p1 := HubPlayerStoreScript.new()
	p1.setup(state_dir)
	for i in range(3):
		p1.set_pos(100001 + i, 5100.0 + i, 0.15, -800.0 + i, "Voyageur%d" % i)
	var t0 := Time.get_ticks_usec()
	p1.save_all()
	var enq_us := Time.get_ticks_usec() - t0
	_check("enqueue non-bloquant (<5ms)", enq_us < 5000, "enqueue %dus" % enq_us)
	var flushed = db.wait_idle(8000)
	_check("wait_idle flushed", flushed)
	_check("positions persisted", db.count_rows("player_positions") == 3, "rows=%d" % db.count_rows("player_positions"))

	var p2 := HubPlayerStoreScript.new()
	p2.setup(state_dir)
	var pos: Variant = p2.get_pos(100001)
	_check("reload SQLite → pos", typeof(pos) == TYPE_VECTOR3 and pos.x == 5100.0, str(pos))

	# --- Comptes (auth) transactionnels.
	var auth := HubAuthScript.new()
	auth.setup()
	var r1: Dictionary = auth.register_or_login("Teome", "s3cret")
	_check("register ok", bool(r1.get("ok", false)))
	var r2: Dictionary = auth.register_or_login("Teome", "BAD")
	_check("mauvais mdp refusé", not bool(r2.get("ok", false)))
	var acc_rows = db.count_rows("accounts")
	_check("accounts persisted", acc_rows >= 1, "rows=%d" % acc_rows)
	_check("next_oid meta", int(db.meta_get("accounts.next_oid", "0")) >= 100002, db.meta_get("accounts.next_oid"))

	# --- État joueur (inventaire / quêtes / chronique).
	var eco := HubEconomyScript.new()
	eco.setup()
	var inv: Dictionary = eco.inventory("Teome")
	_check("inventory seed", bool(inv.get("ok", false)))
	eco.log_session_event("Teome", "fight", "Bataille gagnée hors des murs")
	var st_rows = db.count_rows("player_state")
	_check("player_state persisted", st_rows >= 1, "rows=%d" % st_rows)

	# Reload économique depuis SQLite.
	var eco2 := HubEconomyScript.new()
	eco2.setup()
	var st: Dictionary = eco2.status("Teome")
	_check("economy reload SQLite", bool(st.get("ok", false)) and int(st.get("credits", 0)) == 50, "credits=%s" % st.get("credits"))

	# Intégrité + checkpoint.
	_check("integrity_check ok", db.integrity_ok())
	db.checkpoint()
	_check("post-checkpoint intègre", db.integrity_ok() and db.count_rows("player_positions") == 3)

	# Export JSON conservé.
	_check("export JSON positions", FileAccess.file_exists(state_dir.path_join("player_positions.json")))
	_check("export JSON accounts", FileAccess.file_exists(state_dir.path_join("accounts.json")))
	_check("export JSON players_state", FileAccess.file_exists(state_dir.path_join("players_state.json")))

	p1.shutdown()
	print("selftest: %d/%d checks OK%s" % [_checks - _fails, _checks, "" if _fails == 0 else " — %d FAIL" % _fails])
	quit(0 if _fails == 0 else 1)