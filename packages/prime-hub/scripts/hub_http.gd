extends Node
## Routeur HTTP peel natif (auth, inventaire, quêtes, craft, catalog, dialogue).
## Peut écouter seul (port dédié) ou être appelé par hub_gateway (port unifié).

const HubAuthScript = preload("res://scripts/hub_auth.gd")
const HubEconomyScript = preload("res://scripts/hub_economy.gd")
const HubCatalogScript = preload("res://scripts/hub_catalog.gd")
const HubDialogueScript = preload("res://scripts/hub_dialogue.gd")

@export var listen_host: String = "0.0.0.0"
@export var listen_port: int = 8789

var _tcp: TCPServer = TCPServer.new()
var _listening: bool = false
var sim: Node = null
var ws_port: int = 8787
var started_at: float = 0.0
var auth = null
var economy = null
var catalog = null
var dialogue = null
var events = null


func setup_services(auth_svc = null, economy_svc = null, catalog_svc = null, dialogue_svc = null) -> void:
	auth = auth_svc if auth_svc != null else HubAuthScript.new()
	economy = economy_svc if economy_svc != null else HubEconomyScript.new()
	catalog = catalog_svc if catalog_svc != null else HubCatalogScript.new()
	dialogue = dialogue_svc if dialogue_svc != null else HubDialogueScript.new()
	if auth_svc == null and auth.has_method("setup"):
		auth.setup()
	if economy_svc == null and economy.has_method("setup"):
		economy.setup()
	if dialogue_svc == null and dialogue.has_method("setup"):
		dialogue.setup()


func start(sim_node: Node, port: int = 8789, ws: int = 8787) -> Error:
	sim = sim_node
	listen_port = port
	ws_port = ws
	started_at = Time.get_unix_time_from_system()
	if auth == null:
		setup_services()
	if port <= 0:
		_listening = false
		print("[prime-hub] HTTP router only (unified gateway)")
		return OK
	var err := _tcp.listen(listen_port, listen_host)
	if err != OK:
		push_error("[prime-hub] HTTP listen failed port=%d err=%s" % [listen_port, err])
		return err
	_listening = true
	print("[prime-hub] HTTP native on http://%s:%d/healthz" % [listen_host, listen_port])
	set_process(true)
	return OK


func _process(_delta: float) -> void:
	if not _listening:
		return
	while _tcp.is_connection_available():
		var stream: StreamPeerTCP = _tcp.take_connection()
		if stream == null:
			break
		_serve_once(stream)


func handle_raw_request(method: String, path: String, query: String, body: String) -> Dictionary:
	## {code, body, content_type}
	return _dispatch(method, path, query, body)


func _collision_count() -> int:
	if sim == null or sim.collision == null:
		return 0
	return int(sim.collision.blocks.size())


func _serve_once(stream: StreamPeerTCP) -> void:
	var parsed := _read_http_request(stream)
	var result := _dispatch(
		str(parsed.get("method", "GET")),
		str(parsed.get("path", "/")),
		str(parsed.get("query", "")),
		str(parsed.get("body", ""))
	)
	_write_raw(
		stream,
		int(result.get("code", 500)),
		str(result.get("body", "")),
		str(result.get("content_type", "application/json; charset=utf-8"))
	)


func _query_param(query: String, key: String, default_value: String = "") -> String:
	for part in query.split("&"):
		var kv := str(part).split("=")
		if kv.size() >= 1 and str(kv[0]) == key:
			return str(kv[1] if kv.size() > 1 else "").uri_decode()
	return default_value


func _json_body(body: String) -> Dictionary:
	if body.strip_edges().is_empty():
		return {}
	var parsed: Variant = JSON.parse_string(body)
	if typeof(parsed) == TYPE_DICTIONARY:
		return parsed
	return {}


func _ok(payload: Dictionary, code: int = 200) -> Dictionary:
	return {
		"code": code,
		"body": JSON.stringify(payload),
		"content_type": "application/json; charset=utf-8",
	}


func _dispatch(method: String, path: String, query: String, req_body: String) -> Dictionary:
	method = method.to_upper()
	if method == "OPTIONS":
		return {"code": 204, "body": "", "content_type": "text/plain"}

	if path == "/healthz" or path == "/":
		var uptime := int(Time.get_unix_time_from_system() - started_at)
		var life := {}
		if sim and sim.has_method("life_stats"):
			life = sim.life_stats()
		var seats := {}
		if sim and sim.agent_api != null:
			var boot: Dictionary = sim.agent_api.bootstrap(sim)
			seats = boot.get("seats", {})
		var ev := {}
		if events != null and events.has_method("snapshot"):
			ev = events.snapshot()
		return _ok({
			"ok": true,
			"service": "prime_hub",
			"proto": "lbg-ws/2",
			"phase": "G5+",
			"ws_port": ws_port,
			"http_native": true,
			"python_peel": false,
			"tick": int(sim.tick) if sim else 0,
			"bot_count": int(sim.bot_count()) if sim else 0,
			"npc_count": int(sim.npc_count()) if sim else 0,
			"life": life,
			"ai_seats": seats,
			"active_event": ev,
			"collision_blocks": _collision_count(),
			"uptime_s": uptime,
			"note": "G5+ vie hub · joueurs IA évoluent · PNJ tiennent ; WS+HTTP :%d" % ws_port,
		})

	# --- Catalog C10 ---
	if method == "GET" and path in ["/catalog", "/v1/catalog", "/v1/catalog/skills"]:
		var t := "skills" if path.ends_with("/skills") else _query_param(query, "type", "skills")
		var payload: Dictionary = catalog.catalog(t)
		return _ok(payload, 200 if bool(payload.get("ok", false)) else 400)
	if method == "GET" and path in ["/guide", "/v1/guide"]:
		var payload: Dictionary = catalog.guide(_query_param(query, "playstyle", "prospecteur"))
		return _ok(payload, 200 if bool(payload.get("ok", true)) else 404)
	if method == "GET" and path in ["/tick-matrix", "/v1/tick-matrix"]:
		return _ok(catalog.tick_matrix())

	# --- Auth ---
	if method == "POST" and path == "/v1/auth/login":
		var b := _json_body(req_body)
		var out: Dictionary = auth.register_or_login(str(b.get("username", b.get("player", ""))), str(b.get("password", "")))
		return _ok(out, 200 if bool(out.get("ok")) else 401)
	if method == "POST" and path == "/v1/auth/guest":
		var b2 := _json_body(req_body)
		var out2: Dictionary = auth.guest(str(b2.get("player_name", b2.get("username", "Voyageur"))))
		return _ok(out2, 200 if bool(out2.get("ok")) else 400)
	if method == "POST" and path == "/v1/auth/select_character":
		var b3 := _json_body(req_body)
		var out3: Dictionary = auth.select_character(str(b3.get("session_token", "")), int(b3.get("character_id", 0)))
		return _ok(out3, 200 if bool(out3.get("ok")) else 401)
	if method == "POST" and path == "/v1/auth/enter_zone":
		var b4 := _json_body(req_body)
		var out4: Dictionary = auth.enter_zone(str(b4.get("session_token", "")), str(b4.get("zone", "scrapaltai")))
		return _ok(out4, 200 if bool(out4.get("ok")) else 401)
	if method == "POST" and path == "/v1/auth/resolve":
		var b5 := _json_body(req_body)
		var out5: Dictionary = auth.http_resolve(str(b5.get("session_token", "")))
		return _ok(out5, 200 if bool(out5.get("ok")) else 401)

	# --- Economy ---
	if method == "GET" and path == "/v1/inventory":
		return _ok(economy.inventory(_query_param(query, "player", "Voyageur")))
	if method == "GET" and path == "/v1/quests/board":
		return _ok(economy.board(_query_param(query, "giver", "npc:core3_daan_oth"), _query_param(query, "player", "Voyageur")))
	if method == "GET" and path in ["/v1/events/active", "/v1/events"]:
		if events != null and events.has_method("snapshot"):
			return _ok(events.snapshot())
		return _ok({"ok": true, "active": false, "event_id": "", "source": "prime_hub"})
	if method == "GET" and path == "/v1/quests/status":
		return _ok(economy.status(_query_param(query, "player", "Voyageur")))
	if method == "POST" and path == "/v1/quests/accept":
		var qb := _json_body(req_body)
		var qo: Dictionary = economy.accept(str(qb.get("player", "Voyageur")), str(qb.get("quest_id", "")), str(qb.get("giver_id", "")))
		return _ok(qo, 200 if bool(qo.get("ok")) else 400)
	if method == "POST" and path == "/v1/quests/progress":
		var qb2 := _json_body(req_body)
		var qo2: Dictionary = economy.progress(str(qb2.get("player", "Voyageur")), str(qb2.get("quest_id", "")), str(qb2.get("step_id", "")))
		return _ok(qo2, 200 if bool(qo2.get("ok")) else 400)
	if method == "POST" and path == "/v1/quests/complete":
		var qb3 := _json_body(req_body)
		var qo3: Dictionary = economy.complete(str(qb3.get("player", "Voyageur")), str(qb3.get("quest_id", "")))
		return _ok(qo3, 200 if bool(qo3.get("ok")) else 400)
	if method == "POST" and path == "/v1/quests/tip":
		var qb4 := _json_body(req_body)
		var qo4: Dictionary = economy.tip(str(qb4.get("player", "Voyageur")), str(qb4.get("quest_id", "")), int(qb4.get("amount", 2)))
		return _ok(qo4, 200 if bool(qo4.get("ok")) else 400)
	if method == "POST" and path == "/v1/craft/combine":
		var cb := _json_body(req_body)
		var rid := str(cb.get("schematic_id", cb.get("recipe_id", "")))
		var co: Dictionary = economy.craft_combine(str(cb.get("player", "Voyageur")), rid)
		return _ok(co, 200 if bool(co.get("ok")) else 400)
	if method == "POST" and path in ["/v1/salvage", "/v1/salvage/loot"]:
		var sb := _json_body(req_body)
		var sx := NAN
		var sz := NAN
		if sb.has("x"):
			sx = float(sb.get("x"))
		if sb.has("z"):
			sz = float(sb.get("z"))
		var so: Dictionary = economy.salvage_loot(
			str(sb.get("player", "Voyageur")),
			str(sb.get("poi_id", "poi:lh_scrap_pile")),
			sx,
			sz
		)
		return _ok(so, 200 if bool(so.get("ok")) else 400)

	# --- Dialogue ---
	if method == "POST" and path in ["/v1/dialogue/invoke", "/v1/pilot/agent-dialogue/invoke"]:
		var db := _json_body(req_body)
		var dout: Dictionary = dialogue.invoke(db)
		return _ok(dout, 200 if bool(dout.get("ok")) else 400)

	# --- Bots / say (thin) ---
	if method == "GET" and path == "/v1/bots":
		if sim and sim.has_method("bots_payload"):
			return _ok({"ok": true, "bots": sim.bots_payload(), "count": sim.bot_count()})
		return _ok({"ok": true, "bots": [], "count": 0})
	if method == "POST" and path == "/v1/bots/move_to":
		var mb := _json_body(req_body)
		var player := str(mb.get("player", "Nix"))
		if sim and sim.has_method("set_bot_target"):
			var ent = sim.set_bot_target(player, float(mb.get("x", 0)), float(mb.get("y", 0.15)), float(mb.get("z", 0)))
			if ent == null:
				return _ok({"ok": false, "error": "unknown_bot", "player": player}, 404)
			return _ok({"ok": true, "player": player, "source": "prime_hub"})
		return _ok({"ok": false, "error": "sim_missing"}, 501)
	if method == "POST" and path == "/v1/say":
		var sb := _json_body(req_body)
		var sp := str(sb.get("player", sb.get("from", "Nix"))).strip_edges()
		var text := str(sb.get("text", sb.get("message", ""))).strip_edges()
		if text.is_empty():
			return _ok({"ok": false, "error": "empty_text"}, 400)
		var source := str(sb.get("source", "")).strip_edges().to_lower()
		if source.is_empty():
			source = "ia" if sp.to_lower() in ["nix", "lia", "mira", "kael"] else "human"
		if sim and sim.has_method("enqueue_say"):
			sim.enqueue_say(sp, int(sb.get("oid", 0)), text, source)
		return _ok({"ok": true, "chat": {"from": sp, "text": text, "source": source}, "source": "prime_hub"})

	# --- Agent surface (LAN) : skill + bootstrap ---
	if method == "GET" and path in ["/v1/agent/skill", "/skill.md"]:
		if sim == null or sim.agent_api == null:
			return _ok({"ok": false, "error": "agent_api_unavailable"}, 501)
		var want_md := path == "/skill.md" or _query_param(query, "format", "") == "md"
		var sk: Dictionary = sim.agent_api.skill_payload(want_md)
		if want_md:
			return {
				"code": 200,
				"body": str(sk.get("skill", "")),
				"content_type": "text/markdown; charset=utf-8",
			}
		return _ok(sk)
	if method == "GET" and path == "/v1/agent/bootstrap":
		if sim == null or sim.agent_api == null:
			return _ok({"ok": false, "error": "agent_api_unavailable"}, 501)
		return _ok(sim.agent_api.bootstrap(sim))

	# --- Dev : suggestions monde (off → Studio, pas de mutation auto) ---
	if method == "GET" and path == "/v1/dev/world_suggestions":
		if sim == null or sim.suggest == null:
			return _ok({"ok": false, "error": "suggest_unavailable"}, 501)
		var lim := int(_query_param(query, "limit", "40"))
		return _ok(sim.suggest.list_recent(lim))
	if method == "POST" and path == "/v1/dev/world_suggestions":
		if sim == null or sim.suggest == null:
			return _ok({"ok": false, "error": "suggest_unavailable"}, 501)
		var wb := _json_body(req_body)
		var wout: Dictionary = sim.suggest.submit(
			str(wb.get("from", wb.get("player", "dev"))),
			str(wb.get("kind", "poi")),
			str(wb.get("text", "")),
			wb.get("context", {}) if typeof(wb.get("context", null)) == TYPE_DICTIONARY else {}
		)
		return _ok(wout, 200 if bool(wout.get("ok")) else 400)

	return _ok({"ok": false, "error": "not_found", "path": path}, 404)


func _read_http_request(stream: StreamPeerTCP) -> Dictionary:
	var deadline := Time.get_ticks_msec() + 4000
	var req := PackedByteArray()
	while Time.get_ticks_msec() < deadline:
		stream.poll()
		var n := stream.get_available_bytes()
		if n > 0:
			req.append_array(stream.get_data(n)[1])
			var text_so_far := req.get_string_from_utf8()
			var hdr_end := text_so_far.find("\r\n\r\n")
			if hdr_end >= 0:
				var headers_blob := text_so_far.substr(0, hdr_end)
				var content_len := _content_length(headers_blob)
				var body_start := hdr_end + 4
				var have := req.size() - body_start
				if content_len <= 0 or have >= content_len:
					break
		elif stream.get_status() != StreamPeerTCP.STATUS_CONNECTED:
			break
		else:
			OS.delay_usec(2000)
	return _parse_http_bytes(req)


func _parse_http_bytes(req: PackedByteArray) -> Dictionary:
	var text := req.get_string_from_utf8()
	var method := "GET"
	var full_path := "/"
	var query := ""
	var body := ""
	var line_end := text.find("\r\n")
	if line_end > 0:
		var first := text.substr(0, line_end)
		var parts := first.split(" ")
		if parts.size() >= 2:
			method = str(parts[0]).to_upper()
			full_path = str(parts[1])
	var qpos := full_path.find("?")
	var path := full_path
	if qpos >= 0:
		path = full_path.substr(0, qpos)
		query = full_path.substr(qpos + 1)
	var hdr_end2 := text.find("\r\n\r\n")
	if hdr_end2 >= 0:
		body = text.substr(hdr_end2 + 4)
	return {"method": method, "path": path, "query": query, "body": body, "raw": text}


func parse_http_bytes(req: PackedByteArray) -> Dictionary:
	return _parse_http_bytes(req)


func _content_length(headers_blob: String) -> int:
	for line in headers_blob.split("\r\n"):
		var lower := str(line).to_lower()
		if lower.begins_with("content-length:"):
			return int(str(line).substr(15).strip_edges())
	return 0


func write_response(stream: StreamPeerTCP, code: int, body: String, content_type: String) -> void:
	_write_raw(stream, code, body, content_type)


func _write_raw(stream: StreamPeerTCP, code: int, body: String, content_type: String) -> void:
	var reason := "OK"
	if code == 204:
		reason = "No Content"
	elif code == 400:
		reason = "Bad Request"
	elif code == 401:
		reason = "Unauthorized"
	elif code == 404:
		reason = "Not Found"
	elif code >= 400:
		reason = "Error"
	var bytes := body.to_utf8_buffer()
	var resp := "HTTP/1.1 %d %s\r\n" % [code, reason]
	resp += "Content-Type: %s\r\n" % content_type
	resp += "Content-Length: %d\r\n" % bytes.size()
	resp += "Connection: close\r\n"
	resp += "Access-Control-Allow-Origin: *\r\n"
	resp += "Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS\r\n"
	resp += "Access-Control-Allow-Headers: Content-Type, Authorization\r\n"
	resp += "\r\n"
	stream.put_data(resp.to_utf8_buffer())
	if code != 204 and bytes.size() > 0:
		stream.put_data(bytes)
	stream.disconnect_from_host()
