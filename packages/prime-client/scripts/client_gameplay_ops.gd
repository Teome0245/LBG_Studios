# client_gameplay_ops.gd — Opérations gameplay HTTP (Salvage, Chasse, Densité, Trade, Wiki)
extends RefCounted

const _HubRuntimeCfg = preload("res://scripts/hub_runtime_cfg.gd")
const _WikiHubPanelScript = preload("res://scripts/wiki_hub_panel.gd")
const _WaypointStore = preload("res://scripts/waypoint_store.gd")

const SALVAGE_POI_ID := "poi:lh_scrap_pile"
const SALVAGE_RADIUS_M := 90.0
const HUNT_POI_ID := "poi:lh_hunt_chacal"
const HUNT_RADIUS_M := 90.0

var main: Node = null
var wiki_panel: Node = null
var salvage_http: HTTPRequest = null
var salvage_poi_xz: Vector2 = Vector2(6042.0, -1065.0)
var hunt_http: HTTPRequest = null
var hunt_poi_xz: Vector2 = Vector2(5985.0, -1120.0)
var hunt_phase: String = ""  # reset | run | claim
var combat_density_zones: Array = []
var density_http: HTTPRequest = null
var beast_telegraph_seen: Dictionary = {}


func setup(p_main: Node) -> void:
	main = p_main
	load_salvage_poi()


func ensure_wiki_panel() -> void:
	if wiki_panel != null and is_instance_valid(wiki_panel):
		return
	if main == null:
		return
	var layer := main.get_node_or_null("UI/ModalLayer") as Control
	if layer == null:
		return
	wiki_panel = _WikiHubPanelScript.new()
	wiki_panel.name = "WikiHubPanel"
	layer.add_child(wiki_panel)


func toggle_wiki() -> void:
	ensure_wiki_panel()
	if wiki_panel and wiki_panel.has_method("toggle"):
		wiki_panel.toggle()
		if main and main.has_method("_hotbar_feedback"):
			main._hotbar_feedback("Wiki hub Lost Heaven")


func ensure_salvage_http() -> void:
	if salvage_http != null and is_instance_valid(salvage_http):
		return
	if main == null:
		return
	salvage_http = HTTPRequest.new()
	salvage_http.name = "SalvageHttp"
	main.add_child(salvage_http)
	salvage_http.request_completed.connect(on_salvage_http_done)


func load_salvage_poi() -> void:
	const path := "res://assets/maps/lost_heaven_buildings.json"
	if not FileAccess.file_exists(path):
		return
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if typeof(raw) != TYPE_DICTIONARY:
		return
	for item in (raw as Dictionary).get("buildings", []):
		if typeof(item) != TYPE_DICTIONARY:
			continue
		var iid := str(item.get("id", ""))
		if iid == SALVAGE_POI_ID:
			salvage_poi_xz = Vector2(float(item.get("x", 6042.0)), float(item.get("z", -1065.0)))
		elif iid == HUNT_POI_ID:
			hunt_poi_xz = Vector2(float(item.get("x", 5985.0)), float(item.get("z", -1120.0)))


func load_hunt_poi() -> void:
	load_salvage_poi()


func ensure_hunt_http() -> void:
	if hunt_http != null and is_instance_valid(hunt_http):
		return
	if main == null:
		return
	hunt_http = HTTPRequest.new()
	hunt_http.name = "HuntYardHttp"
	hunt_http.timeout = 120.0
	main.add_child(hunt_http)
	hunt_http.request_completed.connect(on_hunt_http_done)


func ensure_density_http() -> void:
	if density_http != null and is_instance_valid(density_http):
		return
	if main == null:
		return
	density_http = HTTPRequest.new()
	density_http.name = "CombatDensityHttp"
	main.add_child(density_http)
	density_http.request_completed.connect(on_density_http_done)


func fetch_combat_density() -> void:
	if not _HubRuntimeCfg.enabled():
		return
	ensure_density_http()
	var url: String = _HubRuntimeCfg.http_url().rstrip("/") + "/v1/world/combat-density"
	if density_http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		density_http.cancel_request()
	density_http.request(url)


func on_density_http_done(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS or code != 200:
		return
	var parsed = JSON.parse_string(body.get_string_from_utf8()) if body.size() > 0 else null
	if typeof(parsed) != TYPE_DICTIONARY or not bool(parsed.get("ok", false)):
		return
	var zones = parsed.get("zones", [])
	if typeof(zones) == TYPE_ARRAY:
		combat_density_zones = zones


func density_zone_at(pos: Vector2) -> Dictionary:
	var best: Dictionary = {}
	var best_d := INF
	for z in combat_density_zones:
		if typeof(z) != TYPE_DICTIONARY:
			continue
		var p = z.get("pos", {})
		if typeof(p) != TYPE_DICTIONARY:
			continue
		var zx := float(p.get("x", 0))
		var zz := float(p.get("z", 0))
		var r := float(z.get("radius_m", 80))
		var d := pos.distance_to(Vector2(zx, zz))
		if d <= r and d < best_d:
			best_d = d
			best = z
	return best


func try_beast_engage(pos: Vector2) -> void:
	if not _HubRuntimeCfg.enabled():
		if main:
			main._hotbar_feedback("Attaque — hub runtime off")
		return
	ensure_salvage_http()
	var player: String = _HubRuntimeCfg.player_name("Voyageur")
	var url: String = _HubRuntimeCfg.http_url().rstrip("/") + "/v1/world/beast/engage"
	var body := JSON.stringify({
		"player": player,
		"x": pos.x,
		"z": pos.y,
		"radius_m": 42.0,
	})
	var headers := PackedStringArray(["Content-Type: application/json"])
	if salvage_http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		salvage_http.cancel_request()
	if not salvage_http.request_completed.is_connected(on_beast_engage_done):
		if salvage_http.request_completed.is_connected(on_salvage_http_done):
			salvage_http.request_completed.disconnect(on_salvage_http_done)
		salvage_http.request_completed.connect(on_beast_engage_done)
	if main:
		main._hotbar_feedback("Attaque — meute locale…")
	var err := salvage_http.request(url, headers, HTTPClient.METHOD_POST, body)
	if err != OK:
		if main:
			main._hotbar_feedback("Attaque req_%d" % err)
		restore_salvage_http_handler()


func restore_salvage_http_handler() -> void:
	if salvage_http == null:
		return
	if salvage_http.request_completed.is_connected(on_beast_engage_done):
		salvage_http.request_completed.disconnect(on_beast_engage_done)
	if not salvage_http.request_completed.is_connected(on_salvage_http_done):
		salvage_http.request_completed.connect(on_salvage_http_done)


func on_beast_engage_done(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	restore_salvage_http_handler()
	var parsed = JSON.parse_string(body.get_string_from_utf8()) if body.size() > 0 else null
	if result != HTTPRequest.RESULT_SUCCESS:
		if main:
			main._hotbar_feedback("Attaque réseau KO")
		return
	if typeof(parsed) != TYPE_DICTIONARY:
		if main:
			main._hotbar_feedback("Attaque parse (%d)" % code)
		return
	if code == 429 or str(parsed.get("error", "")) == "tick_busy":
		if main:
			main._hotbar_feedback("Attaque tick_busy — %.0fs" % float(parsed.get("retry_after_s", 8)))
		return
	if not bool(parsed.get("ok", false)):
		var err := str(parsed.get("error", code))
		var hint := str(parsed.get("hint", ""))
		if err == "no_beast_in_range":
			var zone := density_zone_at(main._player_world_xz() if main else Vector2.ZERO)
			if not zone.is_empty():
				if main:
					main._hotbar_feedback("%s — densité %s · approche la meute" % [
						str(zone.get("label", zone.get("id", "zone"))),
						str(zone.get("density", "?")),
					])
			else:
				if main:
					main._hotbar_feedback(hint if hint != "" else "Attaque — aucune bête à portée")
		else:
			if main:
				main._hotbar_feedback("Attaque — %s" % (hint if hint != "" else err))
		return
	var loot = parsed.get("loot", [])
	var bits: PackedStringArray = PackedStringArray()
	if typeof(loot) == TYPE_ARRAY:
		for it in loot:
			if typeof(it) == TYPE_DICTIONARY:
				bits.append("%s×%d" % [str(it.get("name", it.get("id", "?"))), int(it.get("qty", 1))])
	if main:
		main._hotbar_feedback(
			"Attaque OK — %s · %s (+%d Cr)"
			% [
				str(parsed.get("beast_name", "bête")),
				", ".join(bits) if bits.size() > 0 else "loot",
				int(parsed.get("credits_gained", 0)),
			]
		)
		if main.inventory_panel and main.inventory_panel.has_method("refresh_inventory"):
			main.inventory_panel.refresh_inventory()


func try_hunt_yard() -> void:
	ensure_hunt_http()
	if main == null:
		return
	var pos: Vector2 = main._player_world_xz()
	if pos == Vector2.INF:
		main._hotbar_feedback("Chasse — position joueur inconnue")
		return
	var dist := pos.distance_to(hunt_poi_xz)
	if dist > HUNT_RADIUS_M:
		main._hotbar_feedback("Chasse — approche la meute hors palissade (%.0fm)" % dist)
		return
	if not _HubRuntimeCfg.enabled():
		main._hotbar_feedback("Chasse — hub runtime off")
		return
	if hunt_phase != "":
		main._hotbar_feedback("Chasse — déjà en cours…")
		return
	hunt_phase = "reset"
	var url: String = _HubRuntimeCfg.http_url().rstrip("/") + "/v1/hunt-yard/reset"
	var body := JSON.stringify({"seed": 1})
	var headers := PackedStringArray(["Content-Type: application/json"])
	if hunt_http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		hunt_http.cancel_request()
	main._hotbar_feedback("Chasse — engagement meute…")
	var err := hunt_http.request(url, headers, HTTPClient.METHOD_POST, body)
	if err != OK:
		hunt_phase = ""
		main._hotbar_feedback("Chasse req_%d" % err)


func hunt_post_run() -> void:
	hunt_phase = "run"
	var player: String = _HubRuntimeCfg.player_name("Voyageur")
	var url: String = _HubRuntimeCfg.http_url().rstrip("/") + "/v1/hunt-yard/run"
	var body := JSON.stringify({"max_ticks": 350, "player": player})
	var headers := PackedStringArray(["Content-Type: application/json"])
	var err := hunt_http.request(url, headers, HTTPClient.METHOD_POST, body)
	if err != OK:
		hunt_phase = ""
		if main:
			main._hotbar_feedback("Chasse run_%d" % err)


func hunt_post_claim() -> void:
	hunt_phase = "claim"
	var player: String = _HubRuntimeCfg.player_name("Voyageur")
	var url: String = _HubRuntimeCfg.http_url().rstrip("/") + "/v1/hunt-yard/claim-quest"
	var body := JSON.stringify({"player": player, "quest_id": "lh_hunt_chacal"})
	var headers := PackedStringArray(["Content-Type: application/json"])
	var err := hunt_http.request(url, headers, HTTPClient.METHOD_POST, body)
	if err != OK:
		hunt_phase = ""
		if main:
			main._hotbar_feedback("Chasse claim_%d" % err)


func on_hunt_http_done(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	var phase := hunt_phase
	var parsed = JSON.parse_string(body.get_string_from_utf8()) if body.size() > 0 else null
	if result != HTTPRequest.RESULT_SUCCESS:
		hunt_phase = ""
		if main:
			main._hotbar_feedback("Chasse réseau KO")
		return
	if typeof(parsed) != TYPE_DICTIONARY:
		hunt_phase = ""
		if main:
			main._hotbar_feedback("Chasse parse (%d)" % code)
		return
	if code == 429 or str(parsed.get("error", "")) == "tick_busy":
		var retry := float(parsed.get("retry_after_s", 8))
		if main:
			main._hotbar_feedback("Chasse tick_busy — retry %.0fs" % retry)
		if phase == "run" or phase == "claim":
			if main:
				main.get_tree().create_timer(maxf(1.0, retry + 0.3)).timeout.connect(
					func () -> void:
						if phase == "run":
							hunt_post_run()
						elif phase == "claim":
							hunt_post_claim()
				)
		else:
			hunt_phase = ""
		return
	if phase == "reset":
		if bool(parsed.get("ok", true)) == false and parsed.get("error"):
			hunt_phase = ""
			if main:
				main._hotbar_feedback("Chasse reset — %s" % str(parsed.get("error")))
			return
		hunt_post_run()
		return
	if phase == "run":
		var status := str(parsed.get("status", ""))
		if status != "victory":
			hunt_phase = ""
			if main:
				main._hotbar_feedback("Chasse — %s (kills=%s)" % [status if status != "" else "échec", str(parsed.get("kills", "?"))])
			return
		if main:
			main._hotbar_feedback(
				"Chasse OK — meute vaincue (tick=%s kills=%s) · claim…"
				% [str(parsed.get("tick", "?")), str(parsed.get("kills", "?"))]
			)
			main.get_tree().create_timer(8.5).timeout.connect(hunt_post_claim)
		return
	if phase == "claim":
		hunt_phase = ""
		if bool(parsed.get("ok", false)):
			if main:
				main._hotbar_feedback("Chasse — étape meute validée")
				if main._mission_board and main._mission_board.has_method("refresh_board"):
					main._mission_board.refresh_board()
				elif main._mission_board and main._mission_board.has_method("refresh"):
					main._mission_board.refresh()
		else:
			var err := str(parsed.get("error", code))
			var hint := str(parsed.get("hint", ""))
			if main:
				main._hotbar_feedback("Chasse claim — %s" % (hint if hint != "" else err))
		return
	hunt_phase = ""


func try_salvage_scrap() -> void:
	ensure_salvage_http()
	restore_salvage_http_handler()
	if main == null:
		return
	var pos: Vector2 = main._player_world_xz()
	if pos == Vector2.INF:
		main._hotbar_feedback("Salvage — position joueur inconnue")
		return
	var dist := pos.distance_to(salvage_poi_xz)
	if dist > SALVAGE_RADIUS_M:
		main._hotbar_feedback("Salvage — approche la pile ferraille (%.0fm)" % dist)
		return
	if not _HubRuntimeCfg.enabled():
		main._hotbar_feedback("Salvage — hub runtime off")
		return
	var player: String = _HubRuntimeCfg.player_name("Voyageur")
	var url: String = _HubRuntimeCfg.http_url().rstrip("/") + "/v1/salvage"
	var body := JSON.stringify({
		"player": player,
		"poi_id": SALVAGE_POI_ID,
		"x": pos.x,
		"z": pos.y,
	})
	var headers := PackedStringArray(["Content-Type: application/json"])
	if salvage_http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		salvage_http.cancel_request()
	main._hotbar_feedback("Salvage…")
	var err := salvage_http.request(url, headers, HTTPClient.METHOD_POST, body)
	if err != OK:
		main._hotbar_feedback("Salvage req_%d" % err)


func on_salvage_http_done(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	var parsed = JSON.parse_string(body.get_string_from_utf8()) if body.size() > 0 else null
	if result != HTTPRequest.RESULT_SUCCESS:
		if main:
			main._hotbar_feedback("Salvage réseau KO")
		return
	if typeof(parsed) != TYPE_DICTIONARY:
		if main:
			main._hotbar_feedback("Salvage parse (%d)" % code)
		return
	if not bool(parsed.get("ok", false)):
		var err := str(parsed.get("error", code))
		var hint := str(parsed.get("hint", ""))
		if err == "cooldown":
			if main:
				main._hotbar_feedback("Salvage cooldown %ss" % str(parsed.get("retry_in_s", "?")))
		elif hint != "":
			if main:
				main._hotbar_feedback("Salvage — %s" % hint)
		else:
			if main:
				main._hotbar_feedback("Salvage échec: %s" % err)
		return
	var loot = parsed.get("loot", [])
	var bits: PackedStringArray = PackedStringArray()
	if typeof(loot) == TYPE_ARRAY:
		for it in loot:
			if typeof(it) == TYPE_DICTIONARY:
				bits.append("%s×%d" % [str(it.get("name", it.get("id", "?"))), int(it.get("qty", 1))])
	var boost := " · event" if bool(parsed.get("event_boost", false)) else ""
	if main:
		main._hotbar_feedback("Salvage OK — %s%s" % [", ".join(bits) if bits.size() > 0 else "loot", boost])
		if main.inventory_panel and main.inventory_panel.has_method("refresh_inventory"):
			main.inventory_panel.refresh_inventory()


func try_trade_offer(sku_id: String, offer_price: int) -> void:
	if sku_id.strip_edges().is_empty():
		if main:
			main._hotbar_feedback("Trade — sku manquant")
		return
	if not _HubRuntimeCfg.enabled():
		if main:
			main._hotbar_feedback("Trade — hub runtime off")
		return
	ensure_salvage_http()
	var player: String = _HubRuntimeCfg.player_name("Voyageur")
	var url: String = _HubRuntimeCfg.http_url().rstrip("/") + "/v1/trade/offer"
	var body := JSON.stringify({
		"player": player,
		"vendor_id": "npc:core3_barman_jax",
		"sku_id": sku_id,
		"offer_price": offer_price,
	})
	var headers := PackedStringArray(["Content-Type: application/json"])
	if salvage_http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		salvage_http.cancel_request()
	if salvage_http.request_completed.is_connected(on_salvage_http_done):
		salvage_http.request_completed.disconnect(on_salvage_http_done)
	if not salvage_http.request_completed.is_connected(on_trade_http_done):
		salvage_http.request_completed.connect(on_trade_http_done)
	if main:
		main._hotbar_feedback("Négociation Jax…")
	var err := salvage_http.request(url, headers, HTTPClient.METHOD_POST, body)
	if err != OK:
		if main:
			main._hotbar_feedback("Trade req_%d" % err)
		restore_salvage_http_callback()


func restore_salvage_http_callback() -> void:
	if salvage_http == null:
		return
	if salvage_http.request_completed.is_connected(on_trade_http_done):
		salvage_http.request_completed.disconnect(on_trade_http_done)
	if not salvage_http.request_completed.is_connected(on_salvage_http_done):
		salvage_http.request_completed.connect(on_salvage_http_done)


func on_trade_http_done(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	restore_salvage_http_callback()
	var parsed = JSON.parse_string(body.get_string_from_utf8()) if body.size() > 0 else null
	if result != HTTPRequest.RESULT_SUCCESS:
		if main:
			main._hotbar_feedback("Trade réseau KO")
		return
	if typeof(parsed) != TYPE_DICTIONARY:
		if main:
			main._hotbar_feedback("Trade parse (%d)" % code)
		return
	if not bool(parsed.get("ok", false)):
		var hint := str(parsed.get("hint", parsed.get("error", code)))
		if main:
			main._hotbar_feedback("Jax refuse — %s" % hint)
			if main._dialogue_panel and main._dialogue_panel.has_method("set_body_text"):
				main._dialogue_panel.set_body_text(str(parsed.get("hint", "Offre hors bornes.")))
		return
	var msg := str(parsed.get("message", "Marché conclu."))
	if main:
		main._hotbar_feedback("%s (−%d Cr)" % [msg, int(parsed.get("price_paid", 0))])
		if main._dialogue_panel and main._dialogue_panel.has_method("set_body_text"):
			main._dialogue_panel.set_body_text(msg)
		if main.inventory_panel and main.inventory_panel.has_method("refresh_inventory"):
			main.inventory_panel.refresh_inventory()


func prime_wahou_hunt_beat() -> void:
	if main == null:
		return
	if main._mission_board and main._mission_board.has_method("seed_hub_hunt_beat"):
		var seeded: Variant = main._mission_board.call("seed_hub_hunt_beat")
		if typeof(seeded) == TYPE_DICTIONARY and bool((seeded as Dictionary).get("ok", false)):
			var title := str((seeded as Dictionary).get("title", "Meute aux portes"))
			main._hotbar_feedback("J — %s · porte est hors palissade" % title)
		else:
			main._hotbar_feedback("J — board chasse · porte est hors palissade")
	else:
		main._hotbar_feedback("J — board chasse · porte est hors palissade")
	ensure_east_gate_hunt_waypoint()


func ensure_east_gate_hunt_waypoint() -> void:
	const gate_x := 5813.6
	const gate_z := -982.5
	const label := "Porte est — chasse"
	var existing: Array = _WaypointStore.load_all()
	for item: Variant in existing:
		if item is Dictionary and str((item as Dictionary).get("label", "")).findn("porte est") >= 0:
			return
	_WaypointStore.add_waypoint(label, gate_x, gate_z)
