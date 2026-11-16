# client_net_world.gd — Réseau WebSocket, Ingestion ZoneState & Entités du monde
extends RefCounted

const _Projection3D2D = preload("res://scripts/projection.gd")
const _HubFocus = preload("res://scripts/hub_focus.gd")
const _LbgWsClientScript = preload("res://scripts/LbgWsClient.gd")
const _LastPos = preload("res://scripts/last_position_store.gd")
const _HubRuntimeCfg = preload("res://scripts/hub_runtime_cfg.gd")
const _EntityScript = preload("res://scripts/entity.gd")

const COLOR_PLAYER_OFFICIAL := Color(0.2, 0.4, 1.0, 1.0)
## Alias historique — même teinte que joueur officiel (C1).
const COLOR_PLAYER_BOT := Color(0.2, 0.4, 1.0, 1.0)
const COLOR_NPC := Color(1.0, 0.5, 0.1, 1.0)

const LOST_HEAVEN_HUB := Vector3(4749.0, 0.0, -737.0)
const LOST_HEAVEN_ZOOM: Vector2 = Vector2(3.0, 3.0)
const HUB_FIT_MARGIN: float = 0.72

var main: Node = null


func setup(p_main: Node) -> void:
	main = p_main


func ensure_ws_client() -> void:
	if main == null:
		return
	if main._ws != null and is_instance_valid(main._ws):
		if not main._ws.is_in_group("lbg_ws_client"):
			main._ws.add_to_group("lbg_ws_client")
		return
	main._ws = main.get_node_or_null("LbgWsClient")
	if main._ws == null:
		main._ws = _LbgWsClientScript.new()
		main._ws.name = "LbgWsClient"
		main.add_child(main._ws)
		print("[Main] LbgWsClient créé dynamiquement")
	if not main._ws.is_in_group("lbg_ws_client"):
		main._ws.add_to_group("lbg_ws_client")


func on_ws_handoff_started(ws_url: String, character_id: int, session_token: String, ws: Node) -> void:
	if main == null:
		return
	main._last_ws_url = ws_url
	main._ws_handoff_busy = true
	if main._login_panel and main._login_panel.has_method("get_selected_character_name"):
		main._local_character_name = str(main._login_panel.call("get_selected_character_name")).strip_edges()
	if not main._local_character_name.is_empty():
		_HubRuntimeCfg.set_player_name(main._local_character_name)
	print("[Main] handoff attaché (LoginPanel pilote) ws=%s char=%d name=%s" % [
		ws_url, character_id, main._local_character_name
	])
	if ws != null and is_instance_valid(ws):
		main._ws = ws
		if not main._ws.is_in_group("lbg_ws_client"):
			main._ws.add_to_group("lbg_ws_client")
	else:
		ensure_ws_client()
	wire_ws_signals_only()
	var pc: Node = main.get_node_or_null("PlayerController")
	if pc and pc.has_method("set_ws_client") and main._ws:
		pc.set_ws_client(main._ws)
	if main.state_label:
		main.state_label.text = "WS…"
	if session_token.strip_edges().is_empty():
		push_warning("[Main] session_token vide à l’attach handoff")


func wire_ws_signals_only() -> void:
	if main == null or main._ws == null:
		return
	var ws = main._ws
	if ws.has_signal("connecting") and not ws.connecting.is_connected(on_ws_connecting):
		ws.connecting.connect(on_ws_connecting)
	if ws.has_signal("connected") and not ws.connected.is_connected(on_ws_connected):
		ws.connected.connect(on_ws_connected)
	if ws.has_signal("zone_state_received") and not ws.zone_state_received.is_connected(on_ws_zone_state):
		ws.zone_state_received.connect(on_ws_zone_state)
	if ws.has_signal("disconnected") and not ws.disconnected.is_connected(on_ws_disconnected):
		ws.disconnected.connect(on_ws_disconnected)
	if ws.has_signal("error_message") and not ws.error_message.is_connected(on_ws_error):
		ws.error_message.connect(on_ws_error)
	if ws.has_signal("login_result") and not ws.login_result.is_connected(on_ws_login_result):
		ws.login_result.connect(on_ws_login_result)
	if ws.has_signal("handoff_progress") and not ws.handoff_progress.is_connected(on_ws_handoff_progress):
		ws.handoff_progress.connect(on_ws_handoff_progress)
	if ws.has_signal("reconnecting") and not ws.reconnecting.is_connected(on_ws_reconnecting):
		ws.reconnecting.connect(on_ws_reconnecting)
	if ws.has_signal("chat_received") and not ws.chat_received.is_connected(main._on_hub_chat_received):
		ws.chat_received.connect(main._on_hub_chat_received)


func wire_login_ws() -> void:
	if main == null:
		return
	if main._login_panel:
		main._login_panel.visible = main.show_login_on_start
		if main.show_login_on_start:
			dismiss_modals_for_login()
		if main._login_panel.has_signal("enter_world_requested"):
			main._login_panel.enter_world_requested.connect(on_enter_world_requested)
	wire_ws_signals_only()
	var pc: Node = main.get_node_or_null("PlayerController")
	if pc and pc.has_method("set_ws_client") and main._ws:
		pc.set_ws_client(main._ws)


func dismiss_modals_for_login() -> void:
	if main == null:
		return
	var pmap: Node = main.get_node_or_null("UI/ModalLayer/PlanetMapPanel")
	if pmap and pmap.has_method("close_map"):
		pmap.close_map()
	if main.inventory_panel and main.inventory_panel.get("visible") and main.inventory_panel.has_method("toggle"):
		main.inventory_panel.toggle()
	if main._talents_panel and main._talents_panel.get("visible") and main._talents_panel.has_method("toggle"):
		main._talents_panel.toggle()
	if main._mission_board and main._mission_board.get("visible") and main._mission_board.has_method("toggle"):
		main._mission_board.toggle()
	if main._game_menu and main._game_menu.get("visible") and main._game_menu.has_method("close_menu"):
		main._game_menu.close_menu()
	if main._dialogue_panel and main._dialogue_panel.get("visible") and main._dialogue_panel.has_method("hide_portrait"):
		main._dialogue_panel.hide_portrait()
	var retail: Node = main.get_node_or_null("WorldMap/RetailLayoutLayer")
	if retail and retail.has_method("set_visible_layout") and bool(retail.get("visible_layout")):
		retail.set_visible_layout(false)


func set_login_status(message: String) -> void:
	if main == null or main._login_panel == null:
		return
	if main._login_panel.has_method("set_ws_status"):
		main._login_panel.set_ws_status(message)
	elif main._login_panel.has_node("%StatusLabel"):
		(main._login_panel.get_node("%StatusLabel") as Label).text = message


func on_enter_world_requested(ws_url: String, character_id: int, session_token: String) -> void:
	if main == null:
		return
	if main._ws_handoff_busy and main._ws != null and main._ws.has_method("is_open") and bool(main._ws.is_open()):
		return
	if session_token.strip_edges().is_empty():
		on_ws_error("session_token vide (login HTTP)")
		return
	main._ws_handoff_busy = true
	if main._login_panel and main._login_panel.has_method("get_selected_character_name"):
		main._local_character_name = str(main._login_panel.call("get_selected_character_name")).strip_edges()
	if not main._local_character_name.is_empty():
		_HubRuntimeCfg.set_player_name(main._local_character_name)
	print("[Main] M11→M12 handoff (legacy) ws=%s char=%d name=%s" % [ws_url, character_id, main._local_character_name])
	main._last_ws_url = ws_url
	if main._login_panel:
		main._login_panel.visible = true
	dismiss_modals_for_login()
	ensure_ws_client()
	wire_ws_signals_only()
	set_login_status("WS %s…" % ws_url)
	if main.state_label:
		main.state_label.text = "WS…"
	if main._ws and main._ws.has_method("connect_session"):
		var err: int = main._ws.connect_session(ws_url, session_token, character_id, "tatooine")
		if err != OK:
			main._ws_handoff_busy = false
			on_ws_error("connect_session err %s" % err)
	else:
		main._ws_handoff_busy = false
		on_ws_error("LbgWsClient absent après ensure_ws_client")


func on_ws_connecting(ws_url: String) -> void:
	set_login_status("WS connexion %s…" % ws_url)
	if main and main.state_label:
		main.state_label.text = "WS…"


func on_ws_handoff_progress(phase: String, detail: String) -> void:
	if main == null:
		return
	if phase == "state":
		var host: String = main._last_ws_url
		if host.length() > 48:
			host = host.substr(0, 45) + "…"
		set_login_status("WS %s — %s" % [detail, host])
	elif phase == "auth":
		set_login_status("WS %s" % detail)
	elif phase == "reconnect":
		set_login_status("WS %s" % detail)
	elif phase == "error":
		on_ws_error(detail)


func on_ws_reconnecting(attempt: int, delay_s: float) -> void:
	if main == null:
		return
	main._ws_live = false
	var msg := "Reconnexion WS dans %.0fs (#%d)…" % [delay_s, attempt]
	set_login_status(msg)
	if main.state_label:
		main.state_label.text = "WS RECON…"
	print("[Main] %s" % msg)


func on_ws_connected(your_character_id: int, zone: String) -> void:
	if main == null:
		return
	main._ws_live = true
	main._is_connected = true
	if main.ui_dialogue:
		main.ui_dialogue.refresh_hub_chat_visibility()
	on_world_entered(your_character_id, zone)


func hub_runtime_enabled() -> bool:
	return _HubRuntimeCfg.enabled()


func hub_runtime_ws_url() -> String:
	const path := "res://config/hub_runtime.json"
	if not FileAccess.file_exists(path):
		return ""
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return ""
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if raw is Dictionary:
		return str((raw as Dictionary).get("ws_url", "")).strip_edges()
	return ""


func hub_runtime_clear_cache_entities(your_id: int) -> void:
	if main == null or your_id <= 0:
		return
	for entity_v in main.entity_manager.get_all_entities():
		var entity: Node = entity_v as Node
		if entity == null:
			continue
		if int(entity.object_id) == your_id:
			continue
		main.entity_manager.despawn(int(entity.object_id))
	print("[Main] hub_runtime — entités cache effacées (reste char=%d)" % your_id)


func on_world_entered(your_character_id: int, zone: String) -> void:
	if main == null or main._world_entry_done:
		return
	main._world_entry_done = true
	main._ws_handoff_busy = false
	main._ws_live = true
	main._is_connected = true
	main._play_mode = true
	main.camera_free_pan = false
	main._planet_name = zone
	if hub_runtime_enabled():
		main.call_deferred("_hub_runtime_clear_cache_entities", your_character_id)
	print("[Main] entrée monde char=%d zone=%s hub=%s" % [
		your_character_id, zone, hub_runtime_enabled()
	])
	if main._login_panel and main._login_panel.has_method("on_ws_connected"):
		main._login_panel.on_ws_connected(your_character_id, zone)
	else:
		set_login_status("Connecté — %s" % zone)
	dismiss_modals_for_login()
	if main._login_panel:
		main._login_panel.visible = false
	if main.quest_ops:
		main.quest_ops.ensure_echo_hammat()
		main.quest_ops.sync_echo_roster()
	if your_character_id > 0:
		main.call_deferred("_possess_local_player", your_character_id, zone, false)
	if main.quest_ops:
		main.get_tree().create_timer(1.2).timeout.connect(main.quest_ops.maybe_start_initiation_quest)
	if main.gameplay_ops:
		main.get_tree().create_timer(1.8).timeout.connect(main.gameplay_ops.prime_wahou_hunt_beat)
	if main.state_label:
		main.state_label.text = "WS OK"


func on_ws_disconnected(reason: String) -> void:
	if main == null:
		return
	if main._ws != null and main._ws.has_method("is_reconnecting") and bool(main._ws.is_reconnecting()):
		main._ws_handoff_busy = false
		main._ws_live = false
		if main.state_label:
			main.state_label.text = "WS RECON…"
		print("[Main] WS drop — reconnexion auto: %s" % reason)
		return
	main._ws_handoff_busy = false
	main._ws_live = false
	main._world_entry_done = false
	main._possessed_id = 0
	if main.ui_dialogue:
		main.ui_dialogue.refresh_hub_chat_visibility()
	print("[Main] WS disconnected: %s" % reason)
	if main.state_label:
		main.state_label.text = "WS OFF"
	if not main._is_connected:
		if main._login_panel:
			main._login_panel.visible = true
			dismiss_modals_for_login()
			if main._login_panel.has_method("on_ws_failed"):
				main._login_panel.on_ws_failed(reason)
			else:
				set_login_status("WS échoué: %s" % reason)


func on_ws_login_result(success: bool, reason: String) -> void:
	if success:
		set_login_status("WS auth OK — entrée zone…")
		return
	if main:
		main._ws_handoff_busy = false
	on_ws_error("login_result: %s" % (reason if reason != "" else "auth_failed"))


func on_ws_error(message: String) -> void:
	if main == null:
		return
	main._ws_handoff_busy = false
	push_warning("[Main] WS error: %s" % message)
	if main._login_panel and not main._is_connected:
		main._login_panel.visible = true
		dismiss_modals_for_login()
		if main._login_panel.has_method("on_ws_failed"):
			main._login_panel.on_ws_failed(message)
		else:
			set_login_status(message)
	if main.state_label:
		main.state_label.text = "WS ERR"


func on_ws_zone_state(payload: Dictionary) -> void:
	if main == null:
		return
	main._ws_live = true
	main._snapshot_live = true
	if payload.has("online_players") and payload.get("online_players") is Array:
		main._online_players = payload.get("online_players")
		main._refresh_connection_hud()
	if payload.has("world_clock") and payload.get("world_clock") is Dictionary:
		var wc: Dictionary = payload.get("world_clock")
		var wm_clock: Node = main.get_node_or_null("WorldMap")
		if wm_clock:
			if wm_clock.has_method("set_world_clock"):
				wm_clock.set_world_clock(wc)
			var bl_clock: Node = wm_clock.get_node_or_null("HubBuildingsLayer")
			if bl_clock and bl_clock.has_method("set_world_clock"):
				bl_clock.set_world_clock(wc)
		var pmap_clock: Node = main.get_node_or_null("UI/ModalLayer/PlanetMapPanel")
		if pmap_clock and pmap_clock.has_method("set_world_clock"):
			pmap_clock.set_world_clock(wc)
	var zone := str(payload.get("zone", payload.get("map", main._planet_name)))
	if zone != "":
		var z_norm := zone.to_lower()
		var changed: bool = z_norm != main._planet_name.to_lower()
		main._planet_name = zone
		if changed:
			var wm: Node = main.get_node_or_null("WorldMap")
			if wm:
				wm.set_planet(z_norm)

	var your_id: int = int(payload.get("your_character_id", 0))
	if your_id == 0 and main._ws and "your_character_id" in main._ws:
		your_id = int(main._ws.your_character_id)
	if your_id > 0 and not main._world_entry_done:
		on_world_entered(your_id, zone if zone != "" else "tatooine")
	elif your_id > 0 and main._login_panel and main._login_panel.visible:
		main._ws_handoff_busy = false
		if main._login_panel.has_method("on_ws_connected"):
			main._login_panel.on_ws_connected(your_id, zone if zone != "" else "tatooine")

	var pos := Vector3(LOST_HEAVEN_HUB.x, LOST_HEAVEN_HUB.y, LOST_HEAVEN_HUB.z)
	var has_pos := false
	if payload.get("position") is Array:
		var p: Array = payload["position"]
		if p.size() >= 3:
			pos = Vector3(float(p[0]), float(p[1]), float(p[2]))
			has_pos = true

	var entities: Array = payload.get("entities", [])
	if typeof(entities) == TYPE_ARRAY:
		for ent in entities:
			if not ent is Dictionary:
				continue
			apply_ws_entity(ent as Dictionary, your_id)
		var retail: Node = main.get_node_or_null("WorldMap/RetailLayoutLayer")
		if retail:
			retail.merge_zone_entities(entities, your_id)
		cull_stray_entities(your_id)
		if str(payload.get("session_policy", "")) == "spike":
			purge_stale_ia_not_in_ws(entities, your_id)

	if your_id > 0:
		if not has_pos and typeof(entities) == TYPE_ARRAY:
			for ent in entities:
				if not ent is Dictionary:
					continue
				var ed: Dictionary = ent
				if resolve_ws_oid(ed.get("id", "")) == your_id:
					var pr = ed.get("pos")
					if pr is Array and (pr as Array).size() >= 3:
						var a: Array = pr
						pos = Vector3(float(a[0]), float(a[1]), float(a[2]))
						has_pos = true
					break
		var existing: Node = main.entity_manager.get_entity(your_id)
		var first_spawn := existing == null
		if first_spawn:
			var label: String = main._local_character_name if main._local_character_name != "" else "You"
			var cfg: Dictionary = main._load_human_cfg()
			if label == "You" and str(cfg.get("display_name", "")) != "":
				label = str(cfg["display_name"])
			if hub_runtime_enabled():
				var hub_spawn := Vector3(4758.0, 0.15, -545.0)
				if not has_pos or (absf(pos.x) < 50.0 and absf(pos.z) < 50.0):
					var saved_hub: Vector3 = _LastPos.load_pos(your_id)
					if saved_hub != Vector3.INF and not (absf(saved_hub.x) < 50.0 and absf(saved_hub.z) < 50.0):
						pos = saved_hub
					else:
						pos = Vector3(LOST_HEAVEN_HUB.x, 0.15, LOST_HEAVEN_HUB.z)
					has_pos = true
				else:
					var near_spawn := (pos - hub_spawn).length_squared() < 100.0
					var saved2: Vector3 = _LastPos.load_pos(your_id)
					if near_spawn and saved2 != Vector3.INF and (saved2 - pos).length_squared() > 400.0:
						pos = saved2
			else:
				var saved: Vector3 = _LastPos.load_pos(your_id)
				if saved != Vector3.INF:
					var near_default := (pos - LOST_HEAVEN_HUB).length_squared() < 4.0
					if near_default or not has_pos:
						pos = saved
						has_pos = true
			main.entity_manager.spawn(your_id, pos, COLOR_PLAYER_OFFICIAL, label, "player", "player:human")
			if hub_runtime_enabled() and main.camera:
				var e_spawn: Node = main.entity_manager.get_entity(your_id)
				if e_spawn:
					main.camera.position = e_spawn.position
					main.camera.zoom = LOST_HEAVEN_ZOOM
					main._cam_target = e_spawn.position
		elif has_pos and existing != null:
			var spike := str(payload.get("session_policy", "")) == "spike"
			var pc_chk: Node = main.get_node_or_null("PlayerController")
			var moving := pc_chk != null and pc_chk.has_method("is_moving") and bool(pc_chk.is_moving())
			if not moving:
				var dx: float = existing.core3_pos.x - pos.x
				var dz: float = existing.core3_pos.z - pos.z
				var d2: float = dx * dx + dz * dz
				if spike:
					if d2 > 2500.0:
						main.entity_manager.move(your_id, pos)
				elif d2 > 1600.0:
					main.entity_manager.move(your_id, pos)
		var pc: Node = main.get_node_or_null("PlayerController")
		if pc:
			pc.set_player_id(your_id)
			if first_spawn and pc.has_method("send_initial_position"):
				pc.send_initial_position(pos.x, pos.y, pos.z)
		main._possess_local_player(your_id, zone if zone != "" else "tatooine", first_spawn)

	for rid in payload.get("removed_entity_ids", []):
		var oid := resolve_ws_oid(rid)
		if oid != 0 and oid != your_id:
			main.entity_manager.despawn(oid)


func resolve_ws_oid(raw: Variant) -> int:
	return _LbgWsClientScript.resolve_oid(raw)


func apply_ws_entity(ent: Dictionary, your_id: int = 0) -> void:
	if main == null:
		return
	var oid := resolve_ws_oid(ent.get("id", ent.get("name", "")))
	if oid == 0:
		return
	if your_id > 0 and oid == your_id:
		return
	if main._echo_controller and oid == int(main._echo_controller.echo_object_id()):
		return
	var name := str(ent.get("name", ""))
	var kind := str(ent.get("kind", "npc"))
	var name_l := name.strip_edges().to_lower()
	if kind == "player":
		if name_l.begins_with("vous") or name_l == "you":
			return
		if main._local_character_name != "" and name_l == main._local_character_name.strip_edges().to_lower():
			if your_id == 0 or oid == your_id:
				return
	var pos_raw = ent.get("pos")
	var pos := Vector3.ZERO
	if pos_raw is Array and (pos_raw as Array).size() >= 3:
		var a: Array = pos_raw
		pos = Vector3(float(a[0]), float(a[1]), float(a[2]))
	else:
		pos = Vector3(float(ent.get("x", 0)), float(ent.get("y", 0)), float(ent.get("z", 0)))
	if kind == "npc" and not _HubFocus.should_show_entity(pos, kind, name, str(ent.get("id", ""))):
		if main.entity_manager.get_entity(oid) != null:
			main.entity_manager.despawn(oid)
		return
	if _HubFocus.is_clutter(kind, name, str(ent.get("id", ""))):
		if main.entity_manager.get_entity(oid) != null:
			main.entity_manager.despawn(oid)
		return
	if name == "":
		name = str(ent.get("id", ""))
	var color := COLOR_NPC
	if kind == "player":
		# C1 — joueur = joueur (pas de teinte « bot »)
		color = COLOR_PLAYER_OFFICIAL
	elif kind == "beast":
		color = Color(0.85, 0.55, 0.22, 1.0)
		if bool(ent.get("is_boss", false)):
			color = Color(0.72, 0.35, 0.55, 1.0)
	if main.entity_manager.get_entity(oid) == null:
		var ekey := str(ent.get("entity_key", ent.get("id", "")))
		main.entity_manager.spawn(oid, pos, color, name, kind, ekey)
	else:
		main.entity_manager.move(oid, pos)
	if hub_runtime_enabled():
		var e2: Node = main.entity_manager.get_entity(oid)
		if e2 and e2.has_method("set_force_nameplate"):
			if kind in ["player", "npc", "beast", "terminal", "droid", "ship", "dungeon"]:
				if not bool(e2.get("force_nameplate")):
					e2.call("set_force_nameplate", true)
		# C1/C2 — activité courte (status idle|busy|quest) · pas de tag IA
		if (kind == "player" or kind == "npc") and e2 and e2.has_method("set_label"):
			var activity := str(ent.get("activity", "")).strip_edges()
			if activity.is_empty():
				activity = str(ent.get("goal", "")).strip_edges()
			var status := str(ent.get("status", "")).strip_edges().to_lower()
			var shown := name
			var skip := activity.is_empty() or activity.to_lower() in ["idle", "none", "null"]
			if status == "idle":
				skip = true
			if not skip:
				var short_g := activity if activity.length() <= 18 else activity.substr(0, 16) + "…"
				shown = "%s · %s" % [name, short_g]
			e2.call("set_label", shown)
		if kind == "beast" and e2 and e2.has_method("set_beast_combat"):
			var bg := str(ent.get("goal", "")).strip_edges().to_lower()
			var boss := bool(ent.get("is_boss", false))
			e2.call("set_beast_combat", bg, boss)
			if bg == "telegraph" and not main._beast_telegraph_seen.has(oid):
				main._beast_telegraph_seen[oid] = true
				main._hotbar_feedback("⚠ %s — telegraph !" % name)
			elif bg != "telegraph":
				main._beast_telegraph_seen.erase(oid)


func purge_stale_ia_not_in_ws(entities: Array, your_id: int) -> void:
	if main == null:
		return
	var allowed: Dictionary = {}
	for ent: Variant in entities:
		if not ent is Dictionary:
			continue
		var oid := resolve_ws_oid((ent as Dictionary).get("id", ""))
		if oid > 0 and oid != your_id:
			allowed[oid] = true
	const ia_labels: Array[String] = ["lia", "nix", "mira", "kael", "kaele", "gally", "bot_ia"]
	for entity_v in main.entity_manager.get_all_entities():
		var entity: Node = entity_v as Node
		if entity == null:
			continue
		var oid := int(entity.object_id)
		if oid == your_id or allowed.has(oid):
			continue
		var label := str(entity.label_text).strip_edges().to_lower()
		if label in ia_labels or label.begins_with("mord kael"):
			main.entity_manager.despawn(oid)
	if main.entity_manager.get_entity(900001) != null:
		for oid_key: Variant in allowed.keys():
			var live: Node = main.entity_manager.get_entity(int(oid_key))
			if live and str(live.label_text).strip_edges().to_lower() == "nix":
				main.entity_manager.despawn(900001)
				break


func cull_stray_entities(your_id: int = 0) -> void:
	if main == null:
		return
	for entity_v in main.entity_manager.get_all_entities():
		var entity: Node = entity_v as Node
		if entity == null:
			continue
		if your_id > 0 and int(entity.object_id) == your_id:
			continue
		if main._echo_controller and int(entity.object_id) == int(main._echo_controller.echo_object_id()):
			continue
		if not _HubFocus.should_show_entity(entity.core3_pos, str(entity.kind), str(entity.label_text), str(entity.entity_key)):
			main.entity_manager.despawn(int(entity.object_id))


func focus_lost_heaven_hub() -> void:
	if main == null or main.camera == null:
		return
	var center := _Projection3D2D.to_screen(LOST_HEAVEN_HUB)
	var fit_z := hub_fit_zoom()
	main.camera.position = center
	main.camera.zoom = Vector2(fit_z, fit_z)
	main._cam_target = center
	print("[Main] focus Lost Heaven hub (4749, -737) zoom=%.2f" % fit_z)


func hub_fit_zoom() -> float:
	if main == null:
		return LOST_HEAVEN_ZOOM.x
	var vp: Vector2 = main.get_viewport().get_visible_rect().size
	if vp.x < 64.0 or vp.y < 64.0:
		return LOST_HEAVEN_ZOOM.x
	var bounds := hub_world_bounds()
	if bounds.is_empty():
		return LOST_HEAVEN_ZOOM.x
	var span_x: float = (float(bounds["max_x"]) - float(bounds["min_x"])) * _Projection3D2D.SCALE
	var span_z: float = (float(bounds["max_z"]) - float(bounds["min_z"])) * _Projection3D2D.SCALE
	if span_x < 1.0 or span_z < 1.0:
		return LOST_HEAVEN_ZOOM.x
	var zx: float = (vp.x * HUB_FIT_MARGIN) / span_x
	var zy: float = (vp.y * HUB_FIT_MARGIN) / span_z
	return clampf(minf(zx, zy), main.CAM_ZOOM_MIN.x, main.CAM_ZOOM_MAX.x)


func hub_world_bounds() -> Dictionary:
	const path := "res://assets/maps/lost_heaven_buildings.json"
	const pad := 80.0
	if not FileAccess.file_exists(path):
		return {}
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return {}
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if not raw is Dictionary:
		return {}
	var min_x := 1.0e12
	var max_x := -1.0e12
	var min_z := 1.0e12
	var max_z := -1.0e12
	for item: Variant in (raw as Dictionary).get("buildings", []):
		if not item is Dictionary:
			continue
		var b: Dictionary = item
		var cx := float(b.get("x", 0.0))
		var cz := float(b.get("z", 0.0))
		var mul := 1.0
		var MapTexLoader = load("res://scripts/map_texture_loader.gd")
		if MapTexLoader != null and MapTexLoader.has_method("world_render_cfg"):
			mul = float(MapTexLoader.world_render_cfg().get("building_size_multiplier", 1.0))
		if mul <= 0.0:
			mul = 1.0
		var half := float(b.get("size_m", 32.0)) * 0.5 * mul + pad * 0.35
		min_x = minf(min_x, cx - half)
		max_x = maxf(max_x, cx + half)
		min_z = minf(min_z, cz - half)
		max_z = maxf(max_z, cz + half)
	if min_x > max_x:
		return {}
	return {"min_x": min_x - pad, "max_x": max_x + pad, "min_z": min_z - pad, "max_z": max_z + pad}


func maybe_demo_spawn() -> void:
	if main == null or not main.allow_demo_fallback:
		return
	if main._snapshot_live or main._udp_live or main.entity_manager.count() > 0:
		return
	demo_spawn()


func demo_spawn() -> void:
	if main == null:
		return
	main.entity_manager.spawn(
		0x0000_0001_0000_0001,
		Vector3(4749.0, 0.0, -737.0),
		COLOR_PLAYER_OFFICIAL,
		"SWG_Client",
		"player"
	)
	main.entity_manager.spawn(
		0x0000_0001_0000_0002,
		Vector3(4755.0, 0.0, -732.0),
		COLOR_PLAYER_OFFICIAL,
		"Nix",
		"player"
	)
	main.entity_manager.spawn(
		0x0000_0002_0000_0001,
		Vector3(4738.0, 8.0, -745.0),
		COLOR_NPC,
		"NPC_Guard",
		"npc"
	)
	# Spawns SWG de Lost Heaven
	main.entity_manager.spawn(800101, Vector3(5025.0, 0.0, -945.0), Color(0.9, 0.2, 0.2), "Terminal Primes SWG", "terminal", "terminal:bounty")
	main.entity_manager.spawn(800102, Vector3(4485.0, 0.0, -525.0), Color(0.2, 0.8, 1.0), "Assurance Clonage", "terminal", "terminal:insurance")
	main.entity_manager.spawn(800103, Vector3(4475.0, 0.0, -945.0), Color(1.0, 0.85, 0.3), "Mairie de Lost Heaven", "terminal", "terminal:cityhall")
	main.entity_manager.spawn(800104, Vector3(5325.0, 0.0, -735.0), Color(0.3, 0.9, 0.4), "Incubateur Génétique", "terminal", "terminal:bio_incubator")
	main.entity_manager.spawn(800105, Vector3(4755.0, 0.0, -730.0), Color(0.9, 0.9, 1.0), "R2-D2", "droid", "droid:r2d2")
	main.entity_manager.spawn(800106, Vector3(4250.0, 0.0, -745.0), Color(0.7, 0.6, 1.0), "Console Galactique", "terminal", "terminal:planets")
	main.entity_manager.spawn(800107, Vector3(4230.0, 0.0, -750.0), Color(1.0, 0.7, 0.2), "Chasseur X-Wing T-65B", "ship", "ship:xwing")
	main.entity_manager.spawn(800108, Vector3(4220.0, 0.0, -735.0), Color(0.8, 0.3, 0.8), "Corvette Corellienne (Sas)", "dungeon", "dungeon:corvette")
	main.entity_manager.spawn(0, Vector3(0.0, 0.0, 0.0), Color(1.0, 1.0, 0.0, 0.6), "(0,0)")
	var center := _Projection3D2D.to_screen(Vector3(4749.0, 0.0, -737.0))
	if main.camera:
		main.camera.position = center
	main._cam_target = center
