extends Node
## Routeur HTTP peel natif (auth, inventaire, quêtes, craft, catalog, dialogue).
## Peut écouter seul (port dédié) ou être appelé par hub_gateway (port unifié).

const HubAuthScript = preload("res://scripts/hub_auth.gd")
const HubEconomyScript = preload("res://scripts/hub_economy.gd")
const HubCatalogScript = preload("res://scripts/hub_catalog.gd")
const HubDialogueScript = preload("res://scripts/hub_dialogue.gd")
const HubHuntYardScript = preload("res://scripts/hub_hunt_yard.gd")
const HubFactionScript = preload("res://scripts/hub_faction.gd")

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
var world_stream = null
var faction = null

## C11 TickGate — cooldown mutations par joueur (aligné agent_catalog / sidecar).
const TICK_MUTATION_PATHS := {
	"/v1/quests/accept": "quests/accept",
	"/v1/quests/progress": "quests/progress",
	"/v1/quests/complete": "quests/complete",
	"/v1/quests/tip": "tip_stage",
	"/v1/show/train": "show/train",
	"/v1/craft/combine": "craft/complete",
	"/v1/salvage": "salvage/loot",
	"/v1/salvage/loot": "salvage/loot",
	"/v1/inventory/use": "inventory/use",
	"/v1/companion/escort": "companion/escort",
	"/v1/bots/move_to": "move_to",
	"/v1/hunt-yard/run": "hunt/engage",
	"/v1/hunt-yard/claim-quest": "hunt/engage",
	"/v1/world/beast/engage": "hunt/engage",
	"/v1/trade/offer": "trade/offer",
}
var _tick_last_ms: Dictionary = {}  # player_key -> msec
var hunt_yard = null


func setup_services(auth_svc = null, economy_svc = null, catalog_svc = null, dialogue_svc = null, hunt_svc = null) -> void:
	auth = auth_svc if auth_svc != null else HubAuthScript.new()
	economy = economy_svc if economy_svc != null else HubEconomyScript.new()
	catalog = catalog_svc if catalog_svc != null else HubCatalogScript.new()
	dialogue = dialogue_svc if dialogue_svc != null else HubDialogueScript.new()
	hunt_yard = hunt_svc if hunt_svc != null else HubHuntYardScript.new()
	if auth_svc == null and auth.has_method("setup"):
		auth.setup()
	if economy_svc == null and economy.has_method("setup"):
		economy.setup()
	if dialogue_svc == null and dialogue.has_method("setup"):
		dialogue.setup()
	if faction == null:
		faction = HubFactionScript.new()
		faction.setup(sim, null, economy)


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


func _tick_gate_enabled() -> bool:
	var raw := OS.get_environment("LBG_TICK_GATE").strip_edges().to_lower()
	if raw.is_empty():
		return true
	return raw not in ["0", "false", "no", "off"]


func _tick_cooldown_ms() -> int:
	var raw := OS.get_environment("LBG_TICK_COOLDOWN_S").strip_edges()
	var sec := 8.0
	if not raw.is_empty():
		sec = maxf(0.0, float(raw))
	return int(sec * 1000.0)


func _tick_player_key(body: Dictionary) -> String:
	for key in ["player", "player_name", "username", "firstname", "name"]:
		var v := str(body.get(key, "")).strip_edges()
		if not v.is_empty():
			return v.to_lower()
	return "local"


func _tick_busy(action: String, player: String, retry_after_s: float) -> Dictionary:
	return _ok({
		"ok": false,
		"error": "tick_busy",
		"reason": "cooldown",
		"player": player,
		"retry_after_s": snappedf(maxf(0.0, retry_after_s), 0.01),
		"queue_depth": 1,
		"tick_cost": "mutation",
		"requires_tick": true,
		"context": {
			"action": action,
			"tick_cost": "mutation",
			"requires_tick": true,
			"kind": "mutation",
		},
	}, 429)


func _tick_guard(method: String, path: String, body: Dictionary) -> Dictionary:
	## {} = OK ; sinon réponse 429 tick_busy.
	if method != "POST" or not _tick_gate_enabled():
		return {}
	if not TICK_MUTATION_PATHS.has(path):
		return {}
	var action := str(TICK_MUTATION_PATHS[path])
	var player := _tick_player_key(body)
	var now := Time.get_ticks_msec()
	var last := int(_tick_last_ms.get(player, 0))
	var cool := _tick_cooldown_ms()
	if cool > 0 and last > 0 and (now - last) < cool:
		var retry := float(cool - (now - last)) / 1000.0
		return _tick_busy(action, player, retry)
	_tick_last_ms[player] = now
	return {}


func _attach_tick_flags(payload: Dictionary, path: String) -> Dictionary:
	if not TICK_MUTATION_PATHS.has(path):
		return payload
	var action := str(TICK_MUTATION_PATHS[path])
	var out := payload.duplicate(true)
	out["tick_cost"] = "mutation"
	out["requires_tick"] = true
	var ctx = out.get("context", {})
	if typeof(ctx) != TYPE_DICTIONARY:
		ctx = {}
	else:
		ctx = (ctx as Dictionary).duplicate(true)
	ctx["action"] = action
	ctx["tick_cost"] = "mutation"
	ctx["requires_tick"] = true
	ctx["kind"] = "mutation"
	out["context"] = ctx
	return out


func _dispatch(method: String, path: String, query: String, req_body: String) -> Dictionary:
	method = method.to_upper()
	if method == "OPTIONS":
		return {"code": 204, "body": "", "content_type": "text/plain"}

	# C11 — gate mutations avant handlers économie / bots
	if method == "POST" and TICK_MUTATION_PATHS.has(path):
		var gate := _tick_guard(method, path, _json_body(req_body))
		if not gate.is_empty():
			return gate

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
		var wstream := {}
		var wsvc = world_stream
		if wsvc == null and sim != null:
			wsvc = sim.world_stream
		if wsvc != null and wsvc.has_method("snapshot"):
			wstream = wsvc.snapshot()
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
			"beast_count": int(sim.beast_count()) if sim and sim.has_method("beast_count") else 0,
			"life": life,
			"ai_seats": seats,
			"active_event": ev,
			"world_stream": wstream,
			"collision_blocks": _collision_count(),
			"navmesh": sim.navmesh_stats() if sim and sim.has_method("navmesh_stats") else {},
			"persistence": sim.persistence_stats() if sim and sim.has_method("persistence_stats") else {},
			"show": _show_snapshot(),
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
	if method == "GET" and path in ["/wiki", "/v1/wiki"]:
		var fmt := _query_param(query, "format", "json").to_lower()
		var wiki_payload: Dictionary = catalog.wiki()
		if fmt == "md" or fmt == "markdown":
			return {
				"code": 200,
				"body": str(wiki_payload.get("markdown", "")),
				"content_type": "text/markdown; charset=utf-8",
			}
		return _ok(wiki_payload, 200 if bool(wiki_payload.get("ok", true)) else 500)
	if method == "GET" and path in ["/tick-matrix", "/v1/tick-matrix"]:
		return _ok(catalog.tick_matrix())
	if method == "GET" and path in ["/v1/world/combat-density", "/combat-density"]:
		var dens: Dictionary = catalog.combat_density()
		return _ok(dens, 200 if bool(dens.get("ok", false)) else 404)
	if method == "GET" and path in ["/v1/world/beasts", "/world/beasts"]:
		if sim == null or not sim.has_method("beasts_snapshot"):
			return _ok({"ok": false, "error": "sim_missing"}, 501)
		return _ok(sim.beasts_snapshot())
	if method == "POST" and path in ["/v1/world/beast/telegraph", "/beast/telegraph"]:
		var bt := _json_body(req_body)
		if sim == null or not sim.has_method("force_beast_telegraph"):
			return _ok({"ok": false, "error": "sim_missing"}, 501)
		var tout: Dictionary = sim.force_beast_telegraph(
			float(bt.get("x", 0)),
			float(bt.get("z", 0)),
			float(bt.get("radius_m", 120)),
			bool(bt.get("bosses_only", true))
		)
		return _ok(tout, 200 if bool(tout.get("ok")) else 400)
	if method == "POST" and path in ["/v1/world/beast/engage", "/beast/engage"]:
		var bb := _json_body(req_body)
		if sim == null or not sim.has_method("engage_nearest_beast"):
			return _ok({"ok": false, "error": "sim_missing"}, 501)
		var bout: Dictionary = sim.engage_nearest_beast(
			str(bb.get("player", "Voyageur")),
			float(bb.get("x", 0)),
			float(bb.get("z", 0)),
			float(bb.get("radius_m", 42))
		)
		return _ok(_attach_tick_flags(bout, path), 200 if bool(bout.get("ok")) else 400)

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
	if method == "POST" and path in ["/v1/inventory/use", "/v1/items/use"]:
		var ub := _json_body(req_body)
		var uo: Dictionary = economy.use_item(str(ub.get("player", "Voyageur")), str(ub.get("item_id", ub.get("id", ""))))
		return _ok(_attach_tick_flags(uo, path), 200 if bool(uo.get("ok")) else 400)
	if method == "GET" and path == "/v1/quests/board":
		return _ok(economy.board(_query_param(query, "giver", "npc:core3_daan_oth"), _query_param(query, "player", "Voyageur")))
	if method == "GET" and path in ["/v1/events/active", "/v1/events"]:
		if events != null and events.has_method("snapshot"):
			return _ok(events.snapshot())
		return _ok({"ok": true, "active": false, "event_id": "", "source": "prime_hub"})
	# --- Plan 3.1 : Live World Stream (événements légers → Compagnon) ---
	if method == "GET" and path in ["/v1/world/stream", "/world/stream"]:
		var wsvc = world_stream
		if wsvc == null and sim != null:
			wsvc = sim.world_stream
		if wsvc == null or not wsvc.has_method("recent"):
			return _ok({"ok": false, "error": "stream_unavailable"}, 501)
		var since := int(_query_param(query, "since", "0"))
		var lim := int(_query_param(query, "limit", "20"))
		return _ok(wsvc.recent(since, lim))
	if method == "GET" and path in ["/v1/world/stream/status", "/world/stream/status"]:
		var wsvc2 = world_stream
		if wsvc2 == null and sim != null:
			wsvc2 = sim.world_stream
		if wsvc2 == null or not wsvc2.has_method("snapshot"):
			return _ok({"ok": false, "error": "stream_unavailable"}, 501)
		return _ok(wsvc2.snapshot())
	if method == "GET" and path == "/v1/quests/status":
		var st_player := _query_param(query, "player", "Voyageur")
		var st: Dictionary = economy.status(st_player)
		_escort_ensure_active(st_player, st)
		return _ok(st)
	if method == "POST" and path == "/v1/quests/accept":
		var qb := _json_body(req_body)
		var q_player := str(qb.get("player", "Voyageur"))
		var q_id := str(qb.get("quest_id", ""))
		var qo: Dictionary = economy.accept(q_player, q_id, str(qb.get("giver_id", "")))
		if bool(qo.get("ok")):
			_escort_on_accept(q_player, q_id, qo)
		return _ok(_attach_tick_flags(qo, path), 200 if bool(qo.get("ok")) else 400)
	if method == "POST" and path == "/v1/quests/progress":
		var qb2 := _json_body(req_body)
		var q2_player := str(qb2.get("player", "Voyageur"))
		var q2_id := str(qb2.get("quest_id", ""))
		var q2_step := str(qb2.get("step_id", ""))
		_escort_ensure_quest(q2_player, q2_id)
		var escort_gate := _escort_before_progress(q2_player, q2_id, q2_step)
		if not bool(escort_gate.get("ok", true)):
			return _ok(_attach_tick_flags(escort_gate, path), 400)
		var qo2: Dictionary = economy.progress(q2_player, q2_id, q2_step)
		if bool(qo2.get("ok")):
			_escort_after_progress(q2_player, q2_id, q2_step, qo2)
			if q2_id.strip_edges() == "lh_show_perle" and q2_step.strip_edges() == "arrive":
				var shp = _show_svc()
				if shp != null:
					shp.mark_attended(q2_player)
		return _ok(_attach_tick_flags(qo2, path), 200 if bool(qo2.get("ok")) else 400)
	if method == "POST" and path == "/v1/quests/complete":
		var qb3 := _json_body(req_body)
		var q3_player := str(qb3.get("player", "Voyageur"))
		var q3_id := str(qb3.get("quest_id", ""))
		var qo3: Dictionary = economy.complete(q3_player, q3_id)
		if bool(qo3.get("ok")):
			_escort_on_complete(q3_player, q3_id)
		return _ok(_attach_tick_flags(qo3, path), 200 if bool(qo3.get("ok")) else 400)
	if method == "GET" and path in ["/v1/quests/escort", "/v1/escort/status"]:
		return _ok(_escort_snapshot(_query_param(query, "player", "")))
	if method == "POST" and path == "/v1/quests/tip":
		var qb4 := _json_body(req_body)
		var tip_player := str(qb4.get("player", "Voyageur"))
		var tip_qid := str(qb4.get("quest_id", "lh_show_perle"))
		var tip_amt := int(qb4.get("amount", 2))
		var tip_gate := _show_validate_tip(tip_player, tip_amt)
		if not bool(tip_gate.get("ok", true)):
			return _ok(_attach_tick_flags(tip_gate, path), 400)
		var qo4: Dictionary = economy.tip(tip_player, tip_qid, tip_amt)
		if bool(qo4.get("ok")):
			_show_on_tip(tip_player, tip_amt, qo4)
			_show_mark_quest_progress(tip_player, tip_qid)
		return _ok(_attach_tick_flags(qo4, path), 200 if bool(qo4.get("ok")) else 400)
	if method == "GET" and path in ["/v1/show", "/v1/show/status"]:
		return _ok(_show_snapshot())
	if method == "POST" and path == "/v1/show/train":
		var tb := _json_body(req_body)
		var train_out := _show_train(str(tb.get("player", "Voyageur")))
		return _ok(_attach_tick_flags(train_out, path), 200 if bool(train_out.get("ok")) else 400)
	if method == "POST" and path == "/v1/craft/combine":
		var cb := _json_body(req_body)
		var rid := str(cb.get("schematic_id", cb.get("recipe_id", "")))
		var co: Dictionary = economy.craft_combine(str(cb.get("player", "Voyageur")), rid)
		return _ok(_attach_tick_flags(co, path), 200 if bool(co.get("ok")) else 400)
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
		return _ok(_attach_tick_flags(so, path), 200 if bool(so.get("ok")) else 400)
	if method == "GET" and path in ["/v1/chronicle", "/v1/chronicle/session"]:
		var cos := _query_param(query, "title", "1") != "0"
		return _ok(economy.chronicle(_query_param(query, "player", "Voyageur"), cos))
	if method == "POST" and path == "/v1/chronicle/export":
		var chb := _json_body(req_body)
		var cos2 := true
		if chb.has("cosmetic_title"):
			cos2 = bool(chb.get("cosmetic_title"))
		return _ok(economy.chronicle(str(chb.get("player", "Voyageur")), cos2))
	if method == "GET" and path in ["/v1/relation-memory", "/v1/relation_memory"]:
		return _ok(economy.relation_memory(
			_query_param(query, "player", "Voyageur"),
			_query_param(query, "npc_id", "")
		))
	if method == "POST" and path in ["/v1/relation-memory/append", "/v1/relation_memory/append"]:
		var rm := _json_body(req_body)
		var rmo: Dictionary = economy.remember_relation(
			str(rm.get("player", "Voyageur")),
			str(rm.get("npc_id", "")),
			str(rm.get("kind", "")),
			str(rm.get("note", "")),
			{
				"value": rm.get("value", null),
				"quest_id": str(rm.get("quest_id", "")),
				"item_id": str(rm.get("item_id", "")),
			}
		)
		return _ok(rmo, 200 if bool(rmo.get("ok")) else 400)
	if method == "GET" and path in ["/v1/trade/catalog", "/v1/trade"]:
		return _ok(economy.trade_catalog(_query_param(query, "vendor", "npc:core3_barman_jax")))
	if method == "POST" and path == "/v1/trade/offer":
		var tb := _json_body(req_body)
		var to: Dictionary = economy.trade_offer(
			str(tb.get("player", "Voyageur")),
			str(tb.get("vendor_id", "npc:core3_barman_jax")),
			str(tb.get("sku_id", "")),
			int(tb.get("offer_price", tb.get("price", 0)))
		)
		return _ok(_attach_tick_flags(to, path), 200 if bool(to.get("ok")) else 400)

	# --- Dialogue ---
	if method == "POST" and path in ["/v1/dialogue/invoke", "/v1/pilot/agent-dialogue/invoke"]:
		var db := _json_body(req_body)
		var dout: Dictionary = dialogue.invoke(db)
		return _ok(dout, 200 if bool(dout.get("ok")) else 400)

	# --- Cour de chasse P5a ---
	if method == "GET" and path in ["/v1/hunt-yard", "/hunt-yard"]:
		return _ok(hunt_yard.snapshot(), 200)
	if method == "POST" and path == "/v1/hunt-yard/reset":
		var hb := _json_body(req_body)
		return _ok(hunt_yard.reset(int(hb.get("seed", 1))))
	if method == "POST" and path == "/v1/hunt-yard/tick":
		var hb2 := _json_body(req_body)
		return _ok(hunt_yard.tick(int(hb2.get("ticks", 1))))
	if method == "POST" and path == "/v1/hunt-yard/run":
		var hb3 := _json_body(req_body)
		var hout: Dictionary = hunt_yard.run(int(hb3.get("max_ticks", 120)))
		return _ok(_attach_tick_flags(hout, path), 200 if bool(hout.get("ok", true)) else 400)
	if method == "POST" and path == "/v1/hunt-yard/claim-quest":
		var hb4 := _json_body(req_body)
		var cout: Dictionary = economy.claim_hunt_quest(
			str(hb4.get("player", "Voyageur")),
			str(hb4.get("quest_id", "lh_hunt_chacal")),
			hunt_yard
		)
		return _ok(_attach_tick_flags(cout, path), 200 if bool(cout.get("ok")) else 400)

	# --- Bots / say / presence dials (thin) ---
	if method == "GET" and path in ["/v1/presence-dials", "/v1/presence_dials"]:
		if sim and sim.has_method("presence_dials_payload"):
			return _ok(sim.presence_dials_payload())
		return _ok({"ok": false, "error": "sim_missing"}, 501)
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
			return _ok(_attach_tick_flags({"ok": true, "player": player, "source": "prime_hub"}, path))
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
	if method == "POST" and path == "/v1/companion/escort":
		var eb := _json_body(req_body)
		if sim == null or not sim.has_method("start_companion_escort_for"):
			return _ok({"ok": false, "error": "sim_missing"}, 501)
		var eo: Dictionary = sim.start_companion_escort_for(
			str(eb.get("player", "Voyageur")),
			float(eb.get("duration_s", 28.0))
		)
		return _ok(_attach_tick_flags(eo, path), 200 if bool(eo.get("ok")) else 400)

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

	# --- Ticket 2.3 : navmesh NavigationServer3D (stats + trace) ---
	if method == "GET" and path in ["/v1/navmesh", "/v1/navmesh/stats"]:
		if sim == null or not sim.has_method("navmesh_stats"):
			return _ok({"ok": false, "error": "sim_missing"}, 501)
		return _ok(sim.navmesh_stats())
	if method == "GET" and path in ["/v1/dev/navmesh/probe", "/v1/navmesh/path"]:
		if sim == null or not sim.has_method("nav_probe"):
			return _ok({"ok": false, "error": "sim_missing"}, 501)
		var fx := float(_query_param(query, "fx", _query_param(query, "sx", "4758")))
		var fz := float(_query_param(query, "fz", _query_param(query, "sz", "-545")))
		var tx := float(_query_param(query, "tx", _query_param(query, "dx", "4859.3")))
		var tz := float(_query_param(query, "tz", _query_param(query, "dz", "-1008.3")))
		return _ok(sim.nav_probe(fx, fz, tx, tz))

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

	# --- Phase 4 SWG Pre-CU : 4.1 Arbres de compétences 4x4 & Skill Points ---
	if method == "GET" and path == "/v1/skills/tree":
		if sim == null or sim.skills == null:
			return _ok({"ok": false, "error": "skills_unavailable"}, 501)
		var sp_player := _query_param(query, "player", "Voyageur")
		return _ok(sim.skills.player_tree_snapshot(sp_player))
	if method == "POST" and path == "/v1/skills/learn":
		if sim == null or sim.skills == null:
			return _ok({"ok": false, "error": "skills_unavailable"}, 501)
		var skb := _json_body(req_body)
		var sk_out: Dictionary = sim.skills.learn_box(
			str(skb.get("player", "Voyageur")),
			str(skb.get("box_id", "")),
			bool(skb.get("bypass_xp", false))
		)
		return _ok(sk_out, 200 if bool(sk_out.get("ok")) else 400)
	if method == "POST" and path == "/v1/skills/surrender":
		if sim == null or sim.skills == null:
			return _ok({"ok": false, "error": "skills_unavailable"}, 501)
		var srb := _json_body(req_body)
		var sr_out: Dictionary = sim.skills.surrender_box(
			str(srb.get("player", "Voyageur")),
			str(srb.get("box_id", ""))
		)
		return _ok(sr_out, 200 if bool(sr_out.get("ok")) else 400)

	# --- Phase 4 SWG Pre-CU : 4.2 Prospection dynamique (Survey) & Spawns 1..1000 ---
	if method == "GET" and path == "/v1/survey/spawns":
		if sim == null or sim.survey == null:
			return _ok({"ok": false, "error": "survey_unavailable"}, 501)
		var sp_list: Array = sim.survey.list_spawns()
		return _ok({"ok": true, "spawns": sp_list, "count": sp_list.size()})
	if method == "POST" and path == "/v1/survey/ping":
		if sim == null or sim.survey == null:
			return _ok({"ok": false, "error": "survey_unavailable"}, 501)
		var svb := _json_body(req_body)
		return _ok(sim.survey.survey_ping(
			str(svb.get("player", "Voyageur")),
			str(svb.get("filter", "")),
			float(svb.get("x", 4795.0)),
			float(svb.get("z", -565.0))
		))
	if method == "POST" and path == "/v1/survey/sample":
		if sim == null or sim.survey == null:
			return _ok({"ok": false, "error": "survey_unavailable"}, 501)
		var smb := _json_body(req_body)
		var sm_out: Dictionary = sim.survey.sample_resource(
			str(smb.get("player", "Voyageur")),
			str(smb.get("spawn_id", "res_lh_copper_kovess")),
			float(smb.get("x", 4795.0)),
			float(smb.get("z", -565.0))
		)
		return _ok(sm_out, 200 if bool(sm_out.get("ok")) else 400)

	# --- Phase 4 SWG Pre-CU : 4.3 Artisanat pondéré & Expérimentation ---
	if method == "POST" and path == "/v1/craft/assemble":
		if sim == null or sim.crafting == null:
			return _ok({"ok": false, "error": "crafting_unavailable"}, 501)
		var crb := _json_body(req_body)
		var cpos := Vector3(float(crb.get("x", 4755.5)), float(crb.get("y", 0.15)), float(crb.get("z", -518.0)))
		var cr_out: Dictionary = sim.crafting.assemble_at_bench(
			str(crb.get("player", "Voyageur")),
			str(crb.get("schematic_id", "")),
			cpos,
			float(crb.get("max_bench_dist", 8.0))
		)
		return _ok(cr_out, 200 if bool(cr_out.get("ok")) else 400)
	if method == "POST" and path == "/v1/craft/experiment":
		if sim == null or sim.crafting == null:
			return _ok({"ok": false, "error": "crafting_unavailable"}, 501)
		var exb := _json_body(req_body)
		var ex_out: Dictionary = sim.crafting.experiment(
			str(exb.get("player", "Voyageur")),
			str(exb.get("session_id", "")),
			str(exb.get("attribute", "quality_pct")),
			int(exb.get("points", 1)),
			float(exb.get("deterministic_roll", -1.0))
		)
		return _ok(ex_out, 200 if bool(ex_out.get("ok")) else 400)

	# --- Phase 4 SWG Pre-CU : 4.4 Boucle HAM / Wounds (Medcenter) / Battle Fatigue (Cantina) ---
	if method == "GET" and path == "/v1/medical/status":
		if sim == null or sim.ham_medical == null:
			return _ok({"ok": false, "error": "ham_medical_unavailable"}, 501)
		var m_player := _query_param(query, "player", "Voyageur")
		return _ok(sim.ham_medical.status(m_player))
	if method == "POST" and path == "/v1/medical/treat_wounds":
		if sim == null or sim.ham_medical == null:
			return _ok({"ok": false, "error": "ham_medical_unavailable"}, 501)
		var mdb := _json_body(req_body)
		var md_out: Dictionary = sim.ham_medical.treat_wounds(
			str(mdb.get("medic", "Voyageur")),
			str(mdb.get("patient", mdb.get("player", "Voyageur"))),
			str(mdb.get("pool", "health")),
			str(mdb.get("medpack_item_id", "")),
			bool(mdb.get("in_medcenter", true))
		)
		return _ok(md_out, 200 if bool(md_out.get("ok")) else 400)
	if method == "POST" and path == "/v1/show/watch":
		if sim == null or sim.ham_medical == null:
			return _ok({"ok": false, "error": "ham_medical_unavailable"}, 501)
		var wtb := _json_body(req_body)
		var wt_out: Dictionary = sim.ham_medical.watch_entertainer(
			str(wtb.get("listener", wtb.get("player", "Voyageur"))),
			str(wtb.get("performer", "Lia")),
			int(wtb.get("ticks", 3)),
			bool(wtb.get("in_cantina", true))
		)
		return _ok(wt_out, 200 if bool(wt_out.get("ok")) else 400)

	# --- Phase 4 SWG Pre-CU : 4.5 Extracteurs de terrain (Harvesters) ---
	if method == "GET" and path == "/v1/harvesters/list":
		if sim == null or sim.harvesters == null:
			return _ok({"ok": false, "error": "harvesters_unavailable"}, 501)
		var h_owner := _query_param(query, "owner", "")
		var h_list: Array = sim.harvesters.list_harvesters(h_owner)
		return _ok({"ok": true, "harvesters": h_list, "count": h_list.size()})
	if method == "POST" and path == "/v1/harvesters/deploy":
		if sim == null or sim.harvesters == null:
			return _ok({"ok": false, "error": "harvesters_unavailable"}, 501)
		var hdb := _json_body(req_body)
		var hd_out: Dictionary = sim.harvesters.deploy_harvester(
			str(hdb.get("player", "Voyageur")),
			str(hdb.get("spawn_id", "res_lh_copper_kovess")),
			float(hdb.get("x", 4795.0)),
			float(hdb.get("z", -565.0)),
			float(hdb.get("ber", 12.0))
		)
		return _ok(hd_out, 200 if bool(hd_out.get("ok")) else 400)
	if method == "POST" and path == "/v1/harvesters/collect":
		if sim == null or sim.harvesters == null:
			return _ok({"ok": false, "error": "harvesters_unavailable"}, 501)
		var hcb := _json_body(req_body)
		var hc_out: Dictionary = sim.harvesters.collect_hopper(
			str(hcb.get("player", "Voyageur")),
			str(hcb.get("harvester_id", ""))
		)
		return _ok(hc_out, 200 if bool(hc_out.get("ok")) else 400)

	# --- Ticket 4 : Faune, Scout & Creature Handler ---
	if method == "GET" and path == "/v1/creatures/bestiary":
		if sim == null or sim.creatures == null:
			return _ok({"ok": false, "error": "creatures_unavailable"}, 501)
		var c_list: Array = sim.creatures.list_creatures()
		return _ok({"ok": true, "creatures": c_list, "count": c_list.size()})

	if method == "GET" and path.begins_with("/v1/creatures/corpses"):
		if sim == null or sim.creatures == null:
			return _ok({"ok": false, "error": "creatures_unavailable"}, 501)
		var q_cx := 5100.0
		var q_cz := -800.0
		var q_rad := 40.0
		if "?" in path:
			var qs := path.split("?")[1]
			for pair in qs.split("&"):
				var kv = pair.split("=")
				if kv.size() == 2:
					if kv[0] == "x": q_cx = float(kv[1])
					elif kv[0] == "z": q_cz = float(kv[1])
					elif kv[0] == "radius": q_rad = float(kv[1])
		var corpses: Array = sim.creatures.list_corpses_near(q_cx, q_cz, q_rad)
		return _ok({"ok": true, "corpses": corpses, "count": corpses.size()})

	if method == "POST" and path == "/v1/creatures/harvest":
		if sim == null or sim.creatures == null:
			return _ok({"ok": false, "error": "creatures_unavailable"}, 501)
		var hb := _json_body(req_body)
		var h_res: Dictionary = sim.creatures.harvest_corpse(
			str(hb.get("player", "Voyageur")),
			str(hb.get("corpse_id", "")),
			str(hb.get("type", "meat"))
		)
		return _ok(h_res, 200 if bool(h_res.get("ok")) else 400)

	if method == "POST" and path == "/v1/scout/camp/deploy":
		if sim == null or sim.creatures == null:
			return _ok({"ok": false, "error": "creatures_unavailable"}, 501)
		var cb := _json_body(req_body)
		var c_res: Dictionary = sim.creatures.deploy_camp(
			str(cb.get("player", "Voyageur")),
			float(cb.get("x", 5500.0)),
			float(cb.get("z", -1200.0)),
			str(cb.get("type", "abri_toile"))
		)
		return _ok(c_res, 200 if bool(c_res.get("ok")) else 400)

	if method == "POST" and path == "/v1/scout/camp/abandon":
		if sim == null or sim.creatures == null:
			return _ok({"ok": false, "error": "creatures_unavailable"}, 501)
		var ab := _json_body(req_body)
		var a_res: Dictionary = sim.creatures.abandon_camp(
			str(ab.get("player", "Voyageur")),
			str(ab.get("camp_id", ""))
		)
		return _ok(a_res, 200 if bool(a_res.get("ok")) else 400)

	if method == "POST" and path == "/v1/scout/mask_scent":
		if sim == null or sim.creatures == null:
			return _ok({"ok": false, "error": "creatures_unavailable"}, 501)
		var mb := _json_body(req_body)
		var m_res: Dictionary = sim.creatures.mask_scent(str(mb.get("player", "Voyageur")))
		return _ok(m_res, 200 if bool(m_res.get("ok")) else 400)

	if method == "POST" and path == "/v1/creatures/tame":
		if sim == null or sim.creatures == null:
			return _ok({"ok": false, "error": "creatures_unavailable"}, 501)
		var tb := _json_body(req_body)
		var t_res: Dictionary = sim.creatures.tame_creature(
			str(tb.get("player", "Voyageur")),
			str(tb.get("beast_eid", ""))
		)
		return _ok(t_res, 200 if bool(t_res.get("ok")) else 400)

	if method == "GET" and path.begins_with("/v1/creatures/pets"):
		if sim == null or sim.creatures == null:
			return _ok({"ok": false, "error": "creatures_unavailable"}, 501)
		var q_player := "Voyageur"
		if "?" in path:
			var qs := path.split("?")[1]
			for pair in qs.split("&"):
				var kv = pair.split("=")
				if kv.size() == 2 and kv[0] == "player":
					q_player = kv[1]
		var pets: Array = sim.creatures.list_player_pets(q_player)
		return _ok({"ok": true, "player": q_player, "pets": pets, "count": pets.size()})

	if method == "POST" and path == "/v1/creatures/pets/call":
		if sim == null or sim.creatures == null:
			return _ok({"ok": false, "error": "creatures_unavailable"}, 501)
		var pb := _json_body(req_body)
		var p_res: Dictionary = sim.creatures.call_pet(
			str(pb.get("player", "Voyageur")),
			str(pb.get("pet_id", "")),
			float(pb.get("x", 5100.0)),
			float(pb.get("z", -800.0))
		)
		return _ok(p_res, 200 if bool(p_res.get("ok")) else 400)

	if method == "POST" and path == "/v1/creatures/pets/store":
		if sim == null or sim.creatures == null:
			return _ok({"ok": false, "error": "creatures_unavailable"}, 501)
		var sb := _json_body(req_body)
		var s_res: Dictionary = sim.creatures.store_pet(
			str(sb.get("player", "Voyageur")),
			str(sb.get("pet_id", ""))
		)
		return _ok(s_res, 200 if bool(s_res.get("ok")) else 400)

	if method == "POST" and path == "/v1/creatures/pets/command":
		if sim == null or sim.creatures == null:
			return _ok({"ok": false, "error": "creatures_unavailable"}, 501)
		var cb := _json_body(req_body)
		var c_res: Dictionary = sim.creatures.command_pet(
			str(cb.get("player", "Voyageur")),
			str(cb.get("pet_id", "")),
			str(cb.get("command", "follow")),
			str(cb.get("target_eid", ""))
		)
		return _ok(c_res, 200 if bool(c_res.get("ok")) else 400)

	if method == "POST" and path == "/v1/creatures/pets/feed":
		if sim == null or sim.creatures == null:
			return _ok({"ok": false, "error": "creatures_unavailable"}, 501)
		var fb := _json_body(req_body)
		var f_res: Dictionary = sim.creatures.feed_pet(
			str(fb.get("player", "Voyageur")),
			str(fb.get("pet_id", "")),
			str(fb.get("food_item_id", "viande"))
		)
		return _ok(f_res, 200 if bool(f_res.get("ok")) else 400)

	# --- Nids de Créatures (Lairs) & Destruction de Nid SWG Pre-CU ---
	if method == "GET" and path == "/v1/creatures/lairs":
		if sim == null or sim.creatures == null:
			return _ok({"ok": false, "error": "creatures_unavailable"}, 501)
		var lairs: Array = sim.creatures.list_lairs()
		return _ok({"ok": true, "lairs": lairs, "count": lairs.size()})

	if method == "POST" and path == "/v1/creatures/lair/attack":
		if sim == null or sim.creatures == null:
			return _ok({"ok": false, "error": "creatures_unavailable"}, 501)
		var lb := _json_body(req_body)
		var a_res: Dictionary = sim.creatures.attack_lair(
			str(lb.get("player", "Voyageur")),
			str(lb.get("lair_id", "")),
			int(lb.get("damage", 100))
		)
		return _ok(a_res, 200 if bool(a_res.get("ok")) else 400)

	if method == "POST" and path == "/v1/creatures/lair/harvest":
		if sim == null or sim.creatures == null:
			return _ok({"ok": false, "error": "creatures_unavailable"}, 501)
		var hb := _json_body(req_body)
		var h_res: Dictionary = sim.creatures.harvest_debris(
			str(hb.get("player", "Voyageur")),
			str(hb.get("lair_id", ""))
		)
		return _ok(h_res, 200 if bool(h_res.get("ok")) else 400)

	# --- Système de Factions & GCW SWG Pre-CU ---
	if method == "GET" and path.begins_with("/v1/factions/status"):
		if faction == null:
			return _ok({"ok": false, "error": "faction_unavailable"}, 501)
		var p_name := _query_param(query, "player", "Voyageur")
		return _ok({"ok": true, "faction_data": faction.get_faction_data(p_name)})

	if method == "GET" and path == "/v1/factions/recruiters":
		if faction == null:
			return _ok({"ok": false, "error": "faction_unavailable"}, 501)
		return _ok({"ok": true, "recruiters": faction.list_recruiters()})

	if method == "POST" and path == "/v1/factions/enlist":
		if faction == null:
			return _ok({"ok": false, "error": "faction_unavailable"}, 501)
		var fb := _json_body(req_body)
		var e_res: Dictionary = faction.enlist(str(fb.get("player", "Voyageur")), str(fb.get("faction", "neutral")))
		return _ok(e_res, 200 if bool(e_res.get("ok")) else 400)

	if method == "POST" and path == "/v1/factions/special_forces":
		if faction == null:
			return _ok({"ok": false, "error": "faction_unavailable"}, 501)
		var sfb := _json_body(req_body)
		var sf_res: Dictionary = faction.declare_special_forces(str(sfb.get("player", "Voyageur")))
		return _ok(sf_res, 200 if bool(sf_res.get("ok")) else 400)

	if method == "POST" and path == "/v1/factions/on_leave":
		if faction == null:
			return _ok({"ok": false, "error": "faction_unavailable"}, 501)
		var olb := _json_body(req_body)
		var ol_res: Dictionary = faction.go_on_leave(str(olb.get("player", "Voyageur")))
		return _ok(ol_res, 200 if bool(ol_res.get("ok")) else 400)

	if method == "POST" and path == "/v1/factions/resign":
		if faction == null:
			return _ok({"ok": false, "error": "faction_unavailable"}, 501)
		var rb := _json_body(req_body)
		var r_res: Dictionary = faction.resign_to_civilian(str(rb.get("player", "Voyageur")))
		return _ok(r_res, 200 if bool(r_res.get("ok")) else 400)

	# --- Espèces SWG (Image Designer) ---
	if method == "GET" and path == "/v1/species/catalog":
		var cats := [
			{"id": "human", "name": "Humain (Corellien)", "bonus": {"health": 100, "action": 100, "mind": 100}},
			{"id": "twilek", "name": "Twi'lek des Oasis", "bonus": {"health": 50, "action": 150, "mind": 200}},
			{"id": "cyborg", "name": "Androïde / Cyborg Compagnon", "bonus": {"health": 200, "action": 100, "mind": 50}},
			{"id": "zabrak", "name": "Zabrak d'Iridonia", "bonus": {"health": 150, "action": 150, "mind": 120}},
			{"id": "wookiee", "name": "Wookiee de Kashyyyk", "bonus": {"health": 350, "action": 50, "mind": 50}},
			{"id": "rodian", "name": "Rodien Chasseur", "bonus": {"health": 80, "action": 200, "mind": 80}}
		]
		return _ok({"ok": true, "species": cats})

	# --- Ticket 3 : Commerce, Player Vendors & Factories ---
	if method == "POST" and path == "/v1/vendors/deploy":
		if sim == null or sim.vendors_factories == null:
			return _ok({"ok": false, "error": "vendors_unavailable"}, 501)
		var vb := _json_body(req_body)
		var v_res: Dictionary = sim.vendors_factories.deploy_vendor(
			str(vb.get("player", "Voyageur")),
			str(vb.get("name", "")),
			float(vb.get("x", 5100.0)),
			float(vb.get("z", -800.0)),
			str(vb.get("appearance", "droide_protocole"))
		)
		return _ok(v_res, 200 if bool(v_res.get("ok")) else 400)

	if method == "GET" and path.begins_with("/v1/vendors/list"):
		if sim == null or sim.vendors_factories == null:
			return _ok({"ok": false, "error": "vendors_unavailable"}, 501)
		var q_owner := ""
		if "?" in path:
			var qs := path.split("?")[1]
			for pair in qs.split("&"):
				var kv = pair.split("=")
				if kv.size() == 2 and kv[0] == "owner": q_owner = kv[1]
		var v_list: Array = sim.vendors_factories.list_player_vendors(q_owner)
		return _ok({"ok": true, "vendors": v_list, "count": v_list.size()})

	if method == "POST" and path == "/v1/vendors/stock":
		if sim == null or sim.vendors_factories == null:
			return _ok({"ok": false, "error": "vendors_unavailable"}, 501)
		var sb := _json_body(req_body)
		var s_res: Dictionary = sim.vendors_factories.stock_item(
			str(sb.get("player", "Voyageur")),
			str(sb.get("vendor_id", "")),
			str(sb.get("item_id", "")),
			int(sb.get("qty", 1)),
			int(sb.get("price_credits", 10)),
			str(sb.get("item_name", "")),
			str(sb.get("description", "")),
			sb.get("stats", {}) if typeof(sb.get("stats")) == TYPE_DICTIONARY else {}
		)
		return _ok(s_res, 200 if bool(s_res.get("ok")) else 400)

	if method == "POST" and path == "/v1/vendors/buy":
		if sim == null or sim.vendors_factories == null:
			return _ok({"ok": false, "error": "vendors_unavailable"}, 501)
		var bb := _json_body(req_body)
		var b_res: Dictionary = sim.vendors_factories.buy_vendor_item(
			str(bb.get("buyer", "Voyageur")),
			str(bb.get("vendor_id", "")),
			str(bb.get("sku_id", "")),
			int(bb.get("qty", 1))
		)
		return _ok(b_res, 200 if bool(b_res.get("ok")) else 400)

	if method == "POST" and path == "/v1/vendors/withdraw":
		if sim == null or sim.vendors_factories == null:
			return _ok({"ok": false, "error": "vendors_unavailable"}, 501)
		var wb := _json_body(req_body)
		var w_res: Dictionary = sim.vendors_factories.withdraw_vendor_credits(
			str(wb.get("player", "Voyageur")),
			str(wb.get("vendor_id", "")),
			int(wb.get("amount", 0))
		)
		return _ok(w_res, 200 if bool(w_res.get("ok")) else 400)

	if method == "POST" and path == "/v1/factories/deploy":
		if sim == null or sim.vendors_factories == null:
			return _ok({"ok": false, "error": "factories_unavailable"}, 501)
		var fb := _json_body(req_body)
		var f_res: Dictionary = sim.vendors_factories.deploy_factory(
			str(fb.get("player", "Voyageur")),
			str(fb.get("type", "equipement")),
			float(fb.get("x", 5200.0)),
			float(fb.get("z", -750.0))
		)
		return _ok(f_res, 200 if bool(f_res.get("ok")) else 400)

	# --- Nids de Créatures (Lairs) & Destruction de Nid SWG Pre-CU ---
	if method == "GET" and path == "/v1/creatures/lairs":
		if sim == null or sim.creatures == null:
			return _ok({"ok": false, "error": "creatures_unavailable"}, 501)
		var lairs: Array = sim.creatures.list_lairs()
		return _ok({"ok": true, "lairs": lairs, "count": lairs.size()})

	if method == "POST" and path == "/v1/creatures/lair/attack":
		if sim == null or sim.creatures == null:
			return _ok({"ok": false, "error": "creatures_unavailable"}, 501)
		var lb := _json_body(req_body)
		var a_res: Dictionary = sim.creatures.attack_lair(
			str(lb.get("player", "Voyageur")),
			str(lb.get("lair_id", "")),
			int(lb.get("damage", 100))
		)
		return _ok(a_res, 200 if bool(a_res.get("ok")) else 400)

	if method == "POST" and path == "/v1/creatures/lair/harvest":
		if sim == null or sim.creatures == null:
			return _ok({"ok": false, "error": "creatures_unavailable"}, 501)
		var hb := _json_body(req_body)
		var h_res: Dictionary = sim.creatures.harvest_debris(
			str(hb.get("player", "Voyageur")),
			str(hb.get("lair_id", ""))
		)
		return _ok(h_res, 200 if bool(h_res.get("ok")) else 400)

	# --- Système de Factions & GCW SWG Pre-CU ---
	if method == "GET" and path.begins_with("/v1/factions/status"):
		if faction == null:
			return _ok({"ok": false, "error": "faction_unavailable"}, 501)
		var p_name := _query_param(query, "player", "Voyageur")
		return _ok({"ok": true, "faction_data": faction.get_faction_data(p_name)})

	if method == "GET" and path == "/v1/factions/recruiters":
		if faction == null:
			return _ok({"ok": false, "error": "faction_unavailable"}, 501)
		return _ok({"ok": true, "recruiters": faction.list_recruiters()})

	if method == "POST" and path == "/v1/factions/enlist":
		if faction == null:
			return _ok({"ok": false, "error": "faction_unavailable"}, 501)
		var fb := _json_body(req_body)
		var e_res: Dictionary = faction.enlist(str(fb.get("player", "Voyageur")), str(fb.get("faction", "neutral")))
		return _ok(e_res, 200 if bool(e_res.get("ok")) else 400)

	if method == "POST" and path == "/v1/factions/special_forces":
		if faction == null:
			return _ok({"ok": false, "error": "faction_unavailable"}, 501)
		var sfb := _json_body(req_body)
		var sf_res: Dictionary = faction.declare_special_forces(str(sfb.get("player", "Voyageur")))
		return _ok(sf_res, 200 if bool(sf_res.get("ok")) else 400)

	if method == "POST" and path == "/v1/factions/on_leave":
		if faction == null:
			return _ok({"ok": false, "error": "faction_unavailable"}, 501)
		var olb := _json_body(req_body)
		var ol_res: Dictionary = faction.go_on_leave(str(olb.get("player", "Voyageur")))
		return _ok(ol_res, 200 if bool(ol_res.get("ok")) else 400)

	if method == "POST" and path == "/v1/factions/resign":
		if faction == null:
			return _ok({"ok": false, "error": "faction_unavailable"}, 501)
		var rb := _json_body(req_body)
		var r_res: Dictionary = faction.resign_to_civilian(str(rb.get("player", "Voyageur")))
		return _ok(r_res, 200 if bool(r_res.get("ok")) else 400)

	# --- Espèces SWG (Image Designer) ---
	if method == "GET" and path == "/v1/species/catalog":
		var cats := [
			{"id": "human", "name": "Humain (Corellien)", "bonus": {"health": 100, "action": 100, "mind": 100}},
			{"id": "twilek", "name": "Twi'lek des Oasis", "bonus": {"health": 50, "action": 150, "mind": 200}},
			{"id": "cyborg", "name": "Androïde / Cyborg Compagnon", "bonus": {"health": 200, "action": 100, "mind": 50}},
			{"id": "zabrak", "name": "Zabrak d'Iridonia", "bonus": {"health": 150, "action": 150, "mind": 120}},
			{"id": "wookiee", "name": "Wookiee de Kashyyyk", "bonus": {"health": 350, "action": 50, "mind": 50}},
			{"id": "rodian", "name": "Rodien Chasseur", "bonus": {"health": 80, "action": 200, "mind": 80}}
		]
		return _ok({"ok": true, "species": cats})

	if method == "POST" and path == "/v1/factories/run":
		if sim == null or sim.vendors_factories == null:
			return _ok({"ok": false, "error": "factories_unavailable"}, 501)
		var rb := _json_body(req_body)
		var r_res: Dictionary = sim.vendors_factories.advance_factory_cycles(
			str(rb.get("factory_id", "")),
			int(rb.get("cycles", 1))
		)
		return _ok(r_res, 200 if bool(r_res.get("ok")) else 400)

	if method == "GET" and path == "/v1/bazaar/list":
		if sim == null or sim.vendors_factories == null:
			return _ok({"ok": false, "error": "bazaar_unavailable"}, 501)
		var b_items: Array = sim.vendors_factories.list_bazaar()
		return _ok({"ok": true, "listings": b_items, "count": b_items.size()})

	if method == "POST" and path == "/v1/bazaar/buy":
		if sim == null or sim.vendors_factories == null:
			return _ok({"ok": false, "error": "bazaar_unavailable"}, 501)
		var byb := _json_body(req_body)
		var by_res: Dictionary = sim.vendors_factories.buy_bazaar_listing(
			str(byb.get("buyer", "Voyageur")),
			str(byb.get("listing_id", ""))
		)
		return _ok(by_res, 200 if bool(by_res.get("ok")) else 400)

	# --- Ticket 2 : Housing Libre, Décoration & Villes de Joueurs ---
	if method == "POST" and path == "/v1/housing/deploy":
		if sim == null or sim.housing_cities == null:
			return _ok({"ok": false, "error": "housing_unavailable"}, 501)
		var hb := _json_body(req_body)
		var h_res: Dictionary = sim.housing_cities.deploy_structure(
			str(hb.get("player", "Voyageur")),
			str(hb.get("deed_id", "deed_maison_sable_p")),
			float(hb.get("x", 5400.0)),
			float(hb.get("z", -900.0)),
			float(hb.get("yaw", 0.0))
		)
		return _ok(h_res, 200 if bool(h_res.get("ok")) else 400)

	if method == "POST" and path == "/v1/housing/decorate/place":
		if sim == null or sim.housing_cities == null:
			return _ok({"ok": false, "error": "housing_unavailable"}, 501)
		var db := _json_body(req_body)
		var d_res: Dictionary = sim.housing_cities.place_decoration(
			str(db.get("player", "Voyageur")),
			str(db.get("struct_id", "")),
			str(db.get("item_id", "")),
			float(db.get("x", 0.0)),
			float(db.get("y", 0.0)),
			float(db.get("z", 0.0)),
			float(db.get("yaw", 0.0)),
			str(db.get("name", ""))
		)
		return _ok(d_res, 200 if bool(d_res.get("ok")) else 400)

	if method == "POST" and path == "/v1/housing/decorate/pickup":
		if sim == null or sim.housing_cities == null:
			return _ok({"ok": false, "error": "housing_unavailable"}, 501)
		var pb := _json_body(req_body)
		var p_res: Dictionary = sim.housing_cities.pickup_decoration(
			str(pb.get("player", "Voyageur")),
			str(pb.get("struct_id", "")),
			str(pb.get("deco_id", ""))
		)
		return _ok(p_res, 200 if bool(p_res.get("ok")) else 400)

	if method == "POST" and path == "/v1/cities/found":
		if sim == null or sim.housing_cities == null:
			return _ok({"ok": false, "error": "cities_unavailable"}, 501)
		var ctb := _json_body(req_body)
		var ct_res: Dictionary = sim.housing_cities.found_player_city(
			str(ctb.get("founder", "Voyageur")),
			str(ctb.get("name", "Nouvelle Oasis")),
			float(ctb.get("x", 5500.0)),
			float(ctb.get("z", -1000.0))
		)
		return _ok(ct_res, 200 if bool(ct_res.get("ok")) else 400)

	if method == "POST" and path == "/v1/cities/elect":
		if sim == null or sim.housing_cities == null:
			return _ok({"ok": false, "error": "cities_unavailable"}, 501)
		var elb := _json_body(req_body)
		var el_res: Dictionary = sim.housing_cities.hold_mayoral_election(
			str(elb.get("city_id", "")),
			elb.get("votes", {}) if typeof(elb.get("votes")) == TYPE_DICTIONARY else {}
		)
		return _ok(el_res, 200 if bool(el_res.get("ok")) else 400)

	# --- Ticket 1 : Combat Tactique SWG (HAM, Postures & Combos) ---
	if method == "POST" and path == "/v1/combat/posture":
		if sim == null or sim.swg_combat == null:
			return _ok({"ok": false, "error": "combat_unavailable"}, 501)
		var pb := _json_body(req_body)
		var p_res: Dictionary = sim.swg_combat.change_posture(
			str(pb.get("eid", "Voyageur")),
			str(pb.get("posture", "upright"))
		)
		return _ok(p_res, 200 if bool(p_res.get("ok")) else 400)

	if method == "POST" and path == "/v1/combat/strike":
		if sim == null or sim.swg_combat == null:
			return _ok({"ok": false, "error": "combat_unavailable"}, 501)
		var sb := _json_body(req_body)
		var s_res: Dictionary = sim.swg_combat.execute_tactical_strike(
			str(sb.get("attacker", "Voyageur")),
			str(sb.get("target", "")),
			str(sb.get("strike", "body_hit"))
		)
		return _ok(s_res, 200 if bool(s_res.get("ok")) else 400)

	if method == "POST" and path == "/v1/combat/armor/equip":
		if sim == null or sim.swg_combat == null:
			return _ok({"ok": false, "error": "combat_unavailable"}, 501)
		var ab := _json_body(req_body)
		var a_res: Dictionary = sim.swg_combat.equip_armor_piece(
			str(ab.get("player", "Voyageur")),
			str(ab.get("slot", "chest")),
			ab.get("armor", {}) if typeof(ab.get("armor")) == TYPE_DICTIONARY else {}
		)
		return _ok(a_res, 200 if bool(a_res.get("ok")) else 400)

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


func _show_svc():
	if sim != null and sim.show != null:
		return sim.show
	return null


func _show_snapshot() -> Dictionary:
	var sh = _show_svc()
	if sh == null:
		return {"ok": false, "error": "show_unavailable"}
	return sh.snapshot()


func _show_validate_tip(player: String, amount: int) -> Dictionary:
	var sh = _show_svc()
	if sh == null:
		return {"ok": true}
	return sh.validate_tip(sim, player, amount)


func _show_on_tip(player: String, amount: int, qo: Dictionary) -> void:
	var sh = _show_svc()
	if sh == null:
		return
	var meta: Dictionary = sh.on_tip_ok(player, amount)
	qo["show"] = meta.get("show", {})
	qo["message"] = str(meta.get("message", qo.get("message", "Scène")))


func _show_mark_quest_progress(player: String, quest_id: String) -> void:
	## Tip pendant le show compte comme présence scène (progress arrive si quête active).
	if quest_id.strip_edges() != "lh_show_perle":
		return
	var sh = _show_svc()
	if sh != null:
		sh.mark_attended(player)
	if economy == null:
		return
	var st: Dictionary = economy.status(player)
	for a in st.get("active", []):
		if typeof(a) == TYPE_DICTIONARY and str(a.get("id", "")) == "lh_show_perle":
			economy.progress(player, "lh_show_perle", "arrive")
			return


func _show_train(player: String) -> Dictionary:
	var sh = _show_svc()
	if sh == null:
		return {"ok": false, "error": "show_unavailable"}
	return sh.train(sim, economy, player)


func _escort_svc():
	if sim != null and sim.escort != null:
		return sim.escort
	return null


func _escort_on_accept(player: String, quest_id: String, qo: Dictionary) -> void:
	var esc = _escort_svc()
	if esc == null or not esc.is_escort_quest(quest_id):
		return
	# already : réhydrate si session absente (reboot hub / rejoin).
	if not esc.session_for(player).is_empty() and bool(qo.get("already", false)):
		qo["escort"] = esc.session_for(player)
		return
	var spawned: Dictionary = esc.on_accept(sim, player)
	if bool(spawned.get("ok")):
		qo["escort"] = spawned


func _escort_ensure_quest(player: String, quest_id: String) -> void:
	var esc = _escort_svc()
	if esc == null or not esc.is_escort_quest(quest_id):
		return
	if not esc.session_for(player).is_empty():
		return
	esc.on_accept(sim, player)


func _escort_ensure_active(player: String, status: Dictionary) -> void:
	var esc = _escort_svc()
	if esc == null:
		return
	var active = status.get("active", [])
	if typeof(active) != TYPE_ARRAY:
		return
	for a in active:
		if typeof(a) != TYPE_DICTIONARY:
			continue
		var qid := str(a.get("id", ""))
		if esc.is_escort_quest(qid):
			_escort_ensure_quest(player, qid)
			status["escort"] = esc.session_for(player)
			return


func _escort_before_progress(player: String, quest_id: String, step_id: String) -> Dictionary:
	var esc = _escort_svc()
	if esc == null or not esc.is_escort_quest(quest_id):
		return {"ok": true}
	# dropoff : civil doit être à la clinique avant d'enregistrer le progress economy.
	if step_id.strip_edges() == "dropoff":
		var gate: Dictionary = esc.on_progress(sim, player, step_id)
		if not bool(gate.get("ok", false)):
			return gate
	return {"ok": true}


func _escort_after_progress(player: String, quest_id: String, step_id: String, qo: Dictionary) -> void:
	var esc = _escort_svc()
	if esc == null or not esc.is_escort_quest(quest_id):
		return
	if step_id.strip_edges() == "dropoff":
		# déjà validé dans before ; annoter la réponse
		qo["escort"] = esc.session_for(player)
		return
	var after: Dictionary = esc.on_progress(sim, player, step_id)
	qo["escort"] = after


func _escort_on_complete(player: String, quest_id: String) -> void:
	var esc = _escort_svc()
	if esc == null or not esc.is_escort_quest(quest_id):
		return
	esc.on_complete(sim, player)


func _escort_snapshot(player: String) -> Dictionary:
	var esc = _escort_svc()
	if esc == null:
		return {"ok": false, "error": "escort_unavailable"}
	return esc.snapshot(player)


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
