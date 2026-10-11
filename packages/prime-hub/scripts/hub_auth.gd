extends RefCounted
class_name HubAuth
const _HubPaths = preload("res://scripts/hub_paths.gd")
const HubDbScript = preload("res://scripts/hub_db.gd")

## Auth / sessions HTTP natives — comptes + tokens (hors Python).
## Ticket 2.1 : comptes persistés en SQLite transactionnel (table accounts),
## export JSON conservé.

const HUMAN_OID := 100001
const SPIKE_TOKENS := ["spike-local", "spike", "dev-mock-token", "smoke-g0"]

var db: HubDbScript = null
var _accounts: Dictionary = {}  # lower -> row
var _sessions: Dictionary = {}  # token -> {username, character_id, created_at}
var _next_oid: int = HUMAN_OID
var _ws_public: String = "ws://192.168.0.246:8787/ws"
var _path: String = ""


func setup() -> void:
	_path = _HubPaths.data_file("accounts.json")
	var env_ws := OS.get_environment("LBG_HUB_WS_PUBLIC").strip_edges()
	if not env_ws.is_empty():
		_ws_public = env_ws
	db = HubDbScript.get_shared()
	_load()


func _load() -> void:
	_accounts.clear()
	if db != null and db.available:
		var rows := db.query_rows("SELECT login,data FROM accounts;")
		if rows.size() > 0:
			for r in rows:
				var blob: Variant = JSON.parse_string(str(r.get("data", "")))
				if typeof(blob) == TYPE_DICTIONARY:
					_accounts[str(r.get("login", "")).to_lower()] = blob
			_next_oid = int(db.meta_get("accounts.next_oid", str(HUMAN_OID)))
			return
		# Table vide → migration depuis le JSON legacy si présent.
		var migrated := _read_legacy_json()
		if migrated.size() > 0 or _next_oid != HUMAN_OID:
			_save_to_db()
		return
	_read_legacy_json()


func _read_legacy_json() -> Dictionary:
	_accounts.clear()
	var raw: Variant = _HubPaths.read_json(_path)
	if typeof(raw) != TYPE_DICTIONARY:
		return {}
	var acc = raw.get("accounts", {})
	if typeof(acc) == TYPE_DICTIONARY:
		for k in acc.keys():
			var row = acc[k]
			if typeof(row) == TYPE_DICTIONARY:
				_accounts[str(k).to_lower()] = row
	_next_oid = int(raw.get("next_oid", HUMAN_OID))
	return _accounts


func _save() -> void:
	if db != null and db.available:
		_save_to_db()
		return
	_write_json_legacy()


func _write_json_legacy() -> void:
	_HubPaths.write_json(_path, {
		"schema_version": 2,
		"backend": "sqlite" if (db != null and db.available) else "json",
		"accounts": _accounts,
		"next_oid": _next_oid,
		"saved_at": int(Time.get_unix_time_from_system()),
	})


func _save_to_db() -> void:
	# Snapshot sous verrou (une écriture asymétrique non bloquante pour le serveur).
	var stmts: Array = []
	var now := int(Time.get_unix_time_from_system())
	for key in _accounts.keys():
		var row: Dictionary = _accounts[key]
		stmts.append(
			"INSERT INTO accounts(login,data,updated_at) VALUES('%s','%s',%d) "
			% [
				HubDbScript.escape_sql(key),
				HubDbScript.json_literal(row),
				now,
			]
			+ "ON CONFLICT(login) DO UPDATE SET data=excluded.data,updated_at=excluded.updated_at;"
		)
	stmts.append(
		"INSERT INTO meta(k,v) VALUES('accounts.next_oid','%d') "
		% _next_oid
		+ "ON CONFLICT(k) DO UPDATE SET v=excluded.v;"
	)
	db.enqueue(stmts)
	_write_json_legacy()


func _hash_password(password: String, salt: String) -> String:
	return ("%s:%s" % [salt, password]).sha256_text()


func _alloc_oid() -> int:
	_next_oid = maxi(_next_oid + 1, HUMAN_OID + 1)
	return _next_oid


func _new_token() -> String:
	return "ph_%d_%08x%08x" % [Time.get_ticks_msec(), randi(), randi()]


func register_or_login(username: String, password: String) -> Dictionary:
	var name := username.strip_edges()
	if name.is_empty():
		return {"ok": false, "error": "auth_failed", "message": "username vide"}
	var key := name.to_lower()
	var acc = _accounts.get(key, null)
	if acc == null:
		var salt := "%08x" % randi()
		var oid := HUMAN_OID if key == "voyageur" else _alloc_oid()
		acc = {
			"username": name,
			"salt": salt,
			"password_hash": _hash_password(password, salt),
			"character_id": oid,
			"display_name": name,
			"created_at": int(Time.get_unix_time_from_system()),
		}
		_accounts[key] = acc
		_save()
	else:
		var salt := str(acc.get("salt", ""))
		var expect := str(acc.get("password_hash", ""))
		var got := _hash_password(password, salt)
		if expect != got:
			return {"ok": false, "error": "auth_failed", "message": "mot de passe invalide"}
	var token := _new_token()
	_sessions[token] = {
		"username": str(acc["username"]),
		"character_id": int(acc["character_id"]),
		"created_at": Time.get_unix_time_from_system(),
	}
	return {
		"ok": true,
		"session_token": token,
		"characters": [{
			"id": int(acc["character_id"]),
			"name": str(acc.get("display_name", name)),
			"race": "prime_hub",
		}],
		"source": "prime_hub",
	}


func guest(player_name: String = "Voyageur") -> Dictionary:
	var n := player_name.strip_edges()
	if n.is_empty():
		n = "Voyageur"
	return register_or_login(n, "")


func resolve_session(token: String) -> Variant:
	## Dictionary ou null
	var t := token.strip_edges()
	if t.is_empty():
		return null
	if t in SPIKE_TOKENS:
		return {"username": "Voyageur", "character_id": HUMAN_OID}
	return _sessions.get(t, null)


func resolve(token: String) -> Dictionary:
	## Compat WS login — {ok, username, character_id, source}
	var sess = resolve_session(token)
	if sess == null:
		return {"ok": false}
	return {
		"ok": true,
		"username": str(sess.get("username", "Voyageur")),
		"character_id": int(sess.get("character_id", HUMAN_OID)),
		"source": "prime_hub",
	}


func select_character(token: String, character_id: int) -> Dictionary:
	var sess = resolve_session(token)
	if sess == null:
		return {"ok": false, "error": "session_expired", "message": "login requis"}
	var cid := character_id if character_id > 0 else int(sess["character_id"])
	if cid != int(sess["character_id"]):
		return {"ok": false, "error": "auth_failed", "message": "character_id inconnu"}
	return {
		"ok": true,
		"character_id": cid,
		"ws_url": _ws_public,
		"source": "prime_hub",
	}


func enter_zone(token: String, zone: String = "scrapaltai") -> Dictionary:
	var sess = resolve_session(token)
	if sess == null:
		return {"ok": false, "error": "session_expired", "message": "login requis"}
	var z := zone.strip_edges()
	if z.is_empty():
		z = "scrapaltai"
	return {
		"ok": true,
		"ws_url": _ws_public,
		"your_character_id": int(sess["character_id"]),
		"zone": z,
		"source": "prime_hub",
	}


func http_resolve(token: String) -> Dictionary:
	var sess = resolve_session(token)
	if sess == null:
		return {"ok": false, "error": "session_expired", "message": "token inconnu"}
	return {
		"ok": true,
		"username": str(sess.get("username", "Voyageur")),
		"character_id": int(sess.get("character_id", HUMAN_OID)),
		"source": "prime_hub",
	}
