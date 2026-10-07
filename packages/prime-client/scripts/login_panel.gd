extends Control
## LoginPanel — écran connexion compte LBG (M11). Branche LbgAuthClient + handoff WS M12.
## Le LoginPanel PILOTE le connect WS (ne délègue plus à Main) pour éviter l’UI figée « WS … ».

signal enter_world_requested(ws_url: String, character_id: int, session_token: String)

@onready var _user: LineEdit = %Username
@onready var _pass: LineEdit = %Password
@onready var _char_list: ItemList = %CharacterList
@onready var _status: Label = %StatusLabel
@onready var _btn_login: Button = %LoginButton
@onready var _btn_create: Button = %CreateButton
@onready var _btn_enter: Button = %EnterButton
@onready var _subtitle: Label = $Center/Panel/VBox/Subtitle

var _auth: Node = null
var _chars: Array = []
var _local_char_id_seq: int = 9000
var _local_ws: Node = null
var _handoff_watchdog: SceneTreeTimer = null
var _handoff_active: bool = false
var _creation_panel: Control = null
var _hub_runtime: Dictionary = {}


func _ready() -> void:
	_btn_enter.disabled = true
	_btn_create.disabled = true
	_apply_planet_subtitle()
	_btn_login.pressed.connect(_on_login_pressed)
	_btn_create.pressed.connect(_on_create_pressed)
	_btn_enter.pressed.connect(_on_enter_pressed)
	_auth = get_node_or_null("LbgAuthClient")
	if _auth == null:
		_auth = preload("res://scripts/LbgAuthClient.gd").new()
		_auth.name = "LbgAuthClient"
		add_child(_auth)
	_auth.login_ok.connect(_on_login_ok)
	_auth.login_failed.connect(_on_login_failed)
	_auth.select_ok.connect(_on_select_ok)
	_auth.select_failed.connect(_on_select_failed)
	_auth.enter_zone_ok.connect(_on_enter_zone_ok)
	_auth.enter_zone_failed.connect(_on_enter_zone_failed)
	call_deferred("_wire_creation_panel")
	call_deferred("_maybe_enable_hub_runtime_spike")


func _get_creation_panel() -> Control:
	if _creation_panel != null and is_instance_valid(_creation_panel):
		return _creation_panel
	var main := _find_main()
	if main:
		_creation_panel = main.get_node_or_null("UI/ModalLayer/CharacterCreationPanel") as Control
	return _creation_panel


func _wire_creation_panel() -> void:
	var panel := _get_creation_panel()
	if panel == null:
		push_warning("[LoginPanel] CharacterCreationPanel introuvable (UI/ModalLayer)")
		return
	if panel.has_signal("creation_completed"):
		if not panel.creation_completed.is_connected(_on_character_created):
			panel.creation_completed.connect(_on_character_created)
	if panel.has_signal("creation_cancelled"):
		if not panel.creation_cancelled.is_connected(_on_character_creation_cancelled):
			panel.creation_cancelled.connect(_on_character_creation_cancelled)
	if panel.has_signal("creation_completed_in_game"):
		if not panel.creation_completed_in_game.is_connected(_on_character_created_in_game):
			panel.creation_completed_in_game.connect(_on_character_created_in_game)


func _apply_planet_subtitle() -> void:
	var planet_label := "Scrapaltai"
	const cfg_path := "res://assets/maps/scrapaltai_map_config.json"
	if FileAccess.file_exists(cfg_path):
		var f := FileAccess.open(cfg_path, FileAccess.READ)
		var raw: Variant = JSON.parse_string(f.get_as_text())
		f.close()
		if raw is Dictionary:
			var dn := str((raw as Dictionary).get("display_name", "")).strip_edges()
			if not dn.is_empty():
				planet_label = dn
	if _subtitle:
		_subtitle.text = "Prime · %s" % planet_label


func get_session_token() -> String:
	if _auth and "session_token" in _auth:
		return str(_auth.session_token)
	return ""


func get_selected_character_name() -> String:
	if _char_list == null or _chars.is_empty():
		return ""
	var idx: PackedInt32Array = _char_list.get_selected_items()
	if idx.is_empty():
		return ""
	var i: int = int(idx[0])
	if i < 0 or i >= _chars.size():
		return ""
	var c: Dictionary = _chars[i]
	return str(c.get("name", ""))


func get_account_roster() -> Array:
	return _chars.duplicate()


func get_selected_character_meta() -> Dictionary:
	if _char_list == null or _chars.is_empty():
		return {}
	var idx: PackedInt32Array = _char_list.get_selected_items()
	if idx.is_empty():
		return {}
	var i: int = int(idx[0])
	if i < 0 or i >= _chars.size():
		return {}
	return _chars[i]


func _on_login_pressed() -> void:
	_status.text = "Connexion…"
	_btn_login.disabled = true
	_auth.login(_user.text, _pass.text)


func _on_login_ok(_session_token: String, characters: Array) -> void:
	_btn_login.disabled = false
	_btn_create.disabled = false
	_chars = characters
	_char_list.clear()
	for c in characters:
		var label := str(c.get("name", c.get("id", "?")))
		_char_list.add_item(label)
	_status.text = "OK — choisis un perso"
	if _char_list.item_count > 0:
		_char_list.select(0)
		_btn_enter.disabled = false
		if _hub_runtime_enabled() and characters.size() > 0 and typeof(characters[0]) == TYPE_DICTIONARY:
			_hub_runtime["session_token"] = _session_token
			_hub_runtime["character_id"] = int((characters[0] as Dictionary).get("id", 100001))
			_hub_runtime["player_name"] = str((characters[0] as Dictionary).get("name", "Voyageur"))
			if _auth:
				_auth.your_character_id = int(_hub_runtime["character_id"])
			_status.text = "OK hub — Enter"
	else:
		_status.text = "Aucun Amas — crée ton premier éclat"
		call_deferred("_on_create_pressed")


func _on_login_failed(code: String, message: String) -> void:
	_btn_login.disabled = false
	_status.text = "%s: %s" % [code, message]
	if _hub_runtime_enabled():
		_btn_enter.disabled = false


func _on_create_pressed() -> void:
	var panel := _get_creation_panel()
	if panel == null:
		_status.text = "Création indisponible"
		return
	if panel.has_method("open_panel"):
		panel.call("open_panel")
	else:
		panel.visible = true


func _on_character_created(result: Dictionary) -> void:
	var numeric_id := int(result.get("_mock_numeric_id", 0))
	if numeric_id < 1:
		numeric_id = _local_char_id_seq
		_local_char_id_seq += 1
	var entry := {
		"id": numeric_id,
		"name": str(result.get("name", "Amas")),
		"character_id": str(result.get("character_id", "")),
		"race": str(result.get("race_display", result.get("race", ""))),
		"archetype": str(result.get("archetype_starter", "")),
		"lore_brief": str(result.get("lore_brief", "")),
		"noyau_id": str(result.get("noyau_id", "")),
		"particule_seed": str(result.get("particule_seed", "")),
	}
	_chars.append(entry)
	_char_list.add_item("%s — %s" % [entry["name"], entry["race"]])
	_char_list.select(_char_list.item_count - 1)
	_btn_enter.disabled = false
	_status.text = "Amas éveillé — %s" % entry["name"]


func _on_character_created_in_game(result: Dictionary) -> void:
	var numeric_id := int(result.get("_mock_numeric_id", 0))
	if numeric_id < 1:
		numeric_id = _local_char_id_seq
		_local_char_id_seq += 1
	var entry := {
		"id": numeric_id,
		"name": str(result.get("name", "Amas")),
		"character_id": str(result.get("character_id", "")),
		"race": str(result.get("race_display", result.get("race", ""))),
		"archetype": str(result.get("archetype_starter", "")),
		"noyau_id": str(result.get("noyau_id", "")),
		"particule_seed": str(result.get("particule_seed", "")),
	}
	add_character_to_roster(entry)
	if str(entry.get("noyau_id", "")) != "":
		for i in range(_chars.size()):
			_chars[i]["noyau_id"] = entry["noyau_id"]
			_chars[i]["particule_seed"] = entry.get("particule_seed", "")
	var main := get_tree().get_first_node_in_group("prime_main")
	if main and main.has_method("_on_second_character_created_in_game"):
		main.call("_on_second_character_created_in_game", entry)


func _on_character_creation_cancelled() -> void:
	_status.text = "Création annulée"


func open_character_creation_in_game() -> void:
	var panel := _get_creation_panel()
	if panel == null:
		push_warning("[LoginPanel] création in-game indisponible")
		return
	if panel.has_method("open_panel"):
		panel.call("open_panel", true)
	else:
		panel.visible = true


func add_character_to_roster(entry: Dictionary) -> void:
	_chars.append(entry)
	if _char_list:
		_char_list.add_item("%s — %s" % [entry.get("name", "?"), entry.get("race", "")])


func _load_hub_runtime_cfg() -> Dictionary:
	const path := "res://config/hub_runtime.json"
	if not FileAccess.file_exists(path):
		return {}
	var f := FileAccess.open(path, FileAccess.READ)
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	return raw if raw is Dictionary else {}


func _hub_runtime_enabled() -> bool:
	return bool(_hub_runtime.get("enabled", false))


func _maybe_enable_hub_runtime_spike() -> void:
	_hub_runtime = _load_hub_runtime_cfg()
	if not _hub_runtime_enabled():
		return
	# Auth HTTP → hub_runtime (même contrat LbgAuthClient M11)
	if _auth:
		_auth.gateway_http_base = str(_hub_runtime.get("http_url", "http://192.168.0.246:8787"))
		_auth.gateway_ws_base = str(_hub_runtime.get("ws_url", "ws://192.168.0.246:8787/ws"))
	_chars = [{
		"id": int(_hub_runtime.get("character_id", 100001)),
		"name": str(_hub_runtime.get("player_name", "Voyageur")),
		"race": "hub_runtime",
	}]
	if _char_list:
		_char_list.clear()
		_char_list.add_item("%s — hub_runtime" % str(_chars[0].get("name", "Voyageur")))
		_char_list.select(0)
	_btn_enter.disabled = false
	_btn_login.disabled = false
	_btn_create.disabled = true
	var label := str(_hub_runtime.get("label", "Spike hub_runtime"))
	_status.text = "%s — Login ou Enter (guest)" % label
	print("[LoginPanel] hub_runtime spike ON → %s" % str(_hub_runtime.get("ws_url", "")))


func _on_enter_pressed() -> void:
	if _hub_runtime_enabled():
		# Guest si pas encore de session
		if _auth and str(_auth.session_token).is_empty():
			_status.text = "Guest hub…"
			_btn_enter.disabled = true
			_hub_guest_then_enter()
			return
		if _auth and not str(_auth.session_token).is_empty():
			_auth.enter_zone(str(_hub_runtime.get("zone", "scrapaltai")))
			return
		_start_hub_runtime_spike()
		return
	var idx := _char_list.get_selected_items()
	if idx.is_empty():
		_status.text = "Sélectionne un personnage"
		return
	var c: Dictionary = _chars[idx[0]]
	var cid := int(c.get("id", 0))
	_status.text = "Select character…"
	_btn_enter.disabled = true
	_auth.select_character(cid)


func _hub_guest_then_enter() -> void:
	## POST /v1/auth/guest puis WS avec le token.
	var http := HTTPRequest.new()
	add_child(http)
	var player := str(_hub_runtime.get("player_name", "Voyageur"))
	var url := str(_hub_runtime.get("http_url", "http://192.168.0.246:8787")).rstrip("/") + "/v1/auth/guest"
	var body := JSON.stringify({"player_name": player})
	http.request_completed.connect(func(result: int, code: int, _h: PackedStringArray, raw: PackedByteArray) -> void:
		http.queue_free()
		if result != HTTPRequest.RESULT_SUCCESS or code < 200 or code >= 300:
			_status.text = "Guest échoué (%s) — fallback spike-local" % code
			_start_hub_runtime_spike()
			return
		var parsed: Variant = JSON.parse_string(raw.get_string_from_utf8())
		if typeof(parsed) != TYPE_DICTIONARY or not bool((parsed as Dictionary).get("ok", false)):
			_start_hub_runtime_spike()
			return
		var d: Dictionary = parsed
		var token := str(d.get("session_token", ""))
		var chars: Array = d.get("characters", [])
		if _auth:
			_auth.session_token = token
			_auth.characters = chars
			if chars.size() > 0 and typeof(chars[0]) == TYPE_DICTIONARY:
				_auth.your_character_id = int((chars[0] as Dictionary).get("id", 100001))
		_chars = chars if chars.size() > 0 else _chars
		_hub_runtime["session_token"] = token
		if chars.size() > 0 and typeof(chars[0]) == TYPE_DICTIONARY:
			_hub_runtime["character_id"] = int((chars[0] as Dictionary).get("id", 100001))
			_hub_runtime["player_name"] = str((chars[0] as Dictionary).get("name", player))
		HubRuntimeCfg.set_player_name(str(_hub_runtime.get("player_name", player)))
		_start_hub_runtime_spike()
	)
	var err := http.request(url, ["Content-Type: application/json"], HTTPClient.METHOD_POST, body)
	if err != OK:
		http.queue_free()
		_start_hub_runtime_spike()


func _start_hub_runtime_spike() -> void:
	var ws_url := str(_hub_runtime.get("ws_url", "ws://127.0.0.1:8787/ws"))
	var token := str(_hub_runtime.get("session_token", "spike-local"))
	var cid := int(_hub_runtime.get("character_id", 100001))
	_status.text = "Spike hub_runtime — WS…"
	_btn_enter.disabled = true
	_handoff_active = true
	_arm_handoff_watchdog()
	call_deferred("_start_ws_handoff", ws_url, cid, token, str(_hub_runtime.get("zone", "scrapaltai")))


func _on_select_ok(_character_id: int, _ws_url: String) -> void:
	_status.text = "Enter zone…"
	var zone := "scrapaltai" if _hub_runtime_enabled() else "tatooine"
	if _hub_runtime_enabled():
		zone = str(_hub_runtime.get("zone", "scrapaltai"))
	_auth.enter_zone(zone)


func _on_select_failed(code: String, message: String) -> void:
	_btn_enter.disabled = false
	_status.text = "%s: %s" % [code, message]


func _on_enter_zone_ok(ws_url: String, your_character_id: int) -> void:
	_status.text = "En zone — ouverture WS…"
	_btn_enter.disabled = true
	_handoff_active = true
	_arm_handoff_watchdog()
	var token := get_session_token()
	if token.strip_edges().is_empty():
		on_ws_failed("session_token vide — reconnecte (login HTTP)")
		return
	# Toujours piloter le WS ici (Main ne fait que s’attacher pour le spawn entités).
	call_deferred("_start_ws_handoff", ws_url, your_character_id, token)


func _arm_handoff_watchdog() -> void:
	var tree := get_tree()
	if tree == null:
		return
	# >= LbgWsClient.connect_timeout_s + response_timeout_s (12+25), process_always.
	_handoff_watchdog = tree.create_timer(40.0, true, false, false)
	_handoff_watchdog.timeout.connect(_on_handoff_watchdog_timeout)


func _on_handoff_watchdog_timeout() -> void:
	if not visible or not _handoff_active:
		return
	_btn_enter.disabled = false
	_handoff_active = false
	_status.text = "WS timeout — ferme Godot puis relance Launchpad (Prime)"
	push_warning("[LoginPanel] handoff WS timeout 40s")
	if _local_ws != null and is_instance_valid(_local_ws) and _local_ws.has_method("disconnect_session"):
		_local_ws.call("disconnect_session")


func _wire_ws_signals(ws: Node) -> void:
	if ws == null:
		return
	if ws.has_signal("connected") and not ws.connected.is_connected(_on_local_ws_connected):
		ws.connected.connect(_on_local_ws_connected)
	if ws.has_signal("disconnected") and not ws.disconnected.is_connected(_on_local_ws_disconnected):
		ws.disconnected.connect(_on_local_ws_disconnected)
	if ws.has_signal("error_message") and not ws.error_message.is_connected(_on_local_ws_error):
		ws.error_message.connect(_on_local_ws_error)
	if ws.has_signal("zone_state_received") and not ws.zone_state_received.is_connected(_on_local_zone_state):
		ws.zone_state_received.connect(_on_local_zone_state)
	if ws.has_signal("login_result") and not ws.login_result.is_connected(_on_local_login_result):
		ws.login_result.connect(_on_local_login_result)
	if ws.has_signal("handoff_progress") and not ws.handoff_progress.is_connected(_on_local_handoff_progress):
		ws.handoff_progress.connect(_on_local_handoff_progress)
	if ws.has_signal("connecting") and not ws.connecting.is_connected(_on_local_connecting):
		ws.connecting.connect(_on_local_connecting)
	if ws.has_signal("reconnecting") and not ws.reconnecting.is_connected(_on_local_reconnecting):
		ws.reconnecting.connect(_on_local_reconnecting)


func _on_local_connecting(ws_url: String) -> void:
	_status.text = "WS connexion %s…" % ws_url


func _on_local_reconnecting(attempt: int, delay_s: float) -> void:
	_status.text = "Reconnexion WS dans %.0fs (#%d)…" % [delay_s, attempt]


func _on_local_handoff_progress(phase: String, detail: String) -> void:
	if phase == "state":
		_status.text = "WS %s…" % detail
	elif phase == "auth":
		_status.text = "WS %s" % detail
	elif phase == "error":
		on_ws_failed(detail)


func _ensure_local_ws() -> Node:
	if _local_ws != null and is_instance_valid(_local_ws) and _local_ws.has_method("connect_session"):
		_local_ws.process_mode = Node.PROCESS_MODE_ALWAYS
		_wire_ws_signals(_local_ws)
		return _local_ws
	var script_res: Resource = load("res://scripts/LbgWsClient.gd")
	if script_res == null or not (script_res is GDScript):
		push_error("[LoginPanel] load LbgWsClient.gd a échoué (script null)")
		return null
	var gd: GDScript = script_res
	if gd.can_instantiate() == false:
		push_error("[LoginPanel] LbgWsClient.gd non instantiable (parse error — voir console)")
		return null
	_local_ws = gd.new() as Node
	if _local_ws == null or not _local_ws.has_method("connect_session"):
		push_error("[LoginPanel] LbgWsClient.new() sans connect_session")
		_local_ws = null
		return null
	_local_ws.name = "LbgWsClientLocal"
	_local_ws.process_mode = Node.PROCESS_MODE_ALWAYS
	add_child(_local_ws)
	_wire_ws_signals(_local_ws)
	print("[LoginPanel] LbgWsClient local créé")
	return _local_ws


func _find_ws_client() -> Node:
	var tree := get_tree()
	if tree == null:
		return null
	var ws: Node = null
	var scene := tree.current_scene
	if scene:
		ws = scene.get_node_or_null("%LbgWsClient")
		if ws and ws.has_method("connect_session"):
			return ws
		ws = scene.get_node_or_null("LbgWsClient")
		if ws and ws.has_method("connect_session"):
			return ws
	ws = tree.get_first_node_in_group("lbg_ws_client")
	if ws and ws.has_method("connect_session") and str(ws.name) != "LbgWsClientLocal":
		return ws
	var n: Node = self
	while n:
		ws = n.get_node_or_null("LbgWsClient")
		if ws and ws.has_method("connect_session"):
			return ws
		n = n.get_parent()
	return null


func _find_main() -> Node:
	var n: Node = get_parent()
	while n:
		if n.has_method("_on_ws_handoff_started") or n.has_method("_on_enter_world_requested"):
			return n
		n = n.get_parent()
	var tree := get_tree()
	if tree and tree.current_scene:
		return tree.current_scene
	return null


func _start_ws_handoff(ws_url: String, character_id: int, session_token: String, zone: String = "tatooine") -> void:
	# Toujours un WS local dédié sous LoginPanel (PROCESS_MODE_ALWAYS).
	# Évite l'état busy/stuck du LbgWsClient de Main et les doubles connect.
	process_mode = Node.PROCESS_MODE_ALWAYS
	var ws := _ensure_local_ws()
	if ws == null or not ws.has_method("connect_session"):
		_status.text = "WS: impossible de créer LbgWsClient"
		_btn_enter.disabled = false
		_handoff_active = false
		push_error("[LoginPanel] échec création WS")
		return

	# Attacher Main pour spawn / caméra — sans lui laisser le connect.
	var main := _find_main()
	if main and main.has_method("_on_ws_handoff_started"):
		main.call("_on_ws_handoff_started", ws_url, character_id, session_token, ws)
	elif main and main.has_method("_on_enter_world_requested"):
		# Très ancien Main : délègue tout le connect (signaux UI déjà câblés).
		main.call("_on_enter_world_requested", ws_url, character_id, session_token)
		_status.text = "WS %s…" % ws_url
		return

	var z := zone if not zone.is_empty() else "tatooine"
	_status.text = "WS %s…" % ws_url
	print("[LoginPanel] connect_session %s char=%d zone=%s" % [ws_url, character_id, z])
	var err: int = ws.connect_session(ws_url, session_token, character_id, z)
	if err != OK:
		_status.text = "WS connect err %s" % err
		_btn_enter.disabled = false
		_handoff_active = false


func _on_local_ws_connected(character_id: int, zone: String) -> void:
	on_ws_connected(character_id, zone)
	var main := _find_main()
	if main and main.has_method("_on_ws_connected"):
		main.call("_on_ws_connected", character_id, zone)


func _on_local_ws_disconnected(reason: String) -> void:
	if _local_ws != null and _local_ws.has_method("is_reconnecting") and bool(_local_ws.is_reconnecting()):
		_status.text = "Reconnexion WS…"
		return
	if _handoff_active or visible:
		on_ws_failed(reason)


func _on_local_ws_error(message: String) -> void:
	if _handoff_active or visible:
		on_ws_failed(message)


func _on_local_login_result(success: bool, reason: String) -> void:
	if success:
		_status.text = "WS auth OK — entrée zone…"
	else:
		on_ws_failed("login_result: %s" % (reason if reason else "auth_failed"))


func _on_local_zone_state(payload: Dictionary) -> void:
	var main := _find_main()
	if main and main.has_method("_on_ws_zone_state"):
		main.call("_on_ws_zone_state", payload)
	# Filet UI : premier zone_state / enter_world = entrée monde même si signal connected a raté.
	if visible and _handoff_active:
		var your_id := int(payload.get("your_character_id", 0))
		if your_id <= 0 and _local_ws != null and is_instance_valid(_local_ws) and "your_character_id" in _local_ws:
			your_id = int(_local_ws.your_character_id)
		var zone := str(payload.get("zone", payload.get("map", "tatooine")))
		# Même sans id : si on reçoit zone_state pendant handoff, considérer succès.
		var cid := your_id if your_id > 0 else 1
		var z := zone if zone != "" else "tatooine"
		on_ws_connected(cid, z)
		if main and main.has_method("_on_world_entered"):
			main.call("_on_world_entered", cid, z)


func _on_enter_zone_failed(code: String, message: String) -> void:
	_btn_enter.disabled = false
	_handoff_active = false
	_status.text = "%s: %s" % [code, message]


func set_ws_status(message: String) -> void:
	_status.text = message


func on_ws_connected(_character_id: int, zone: String) -> void:
	_handoff_active = false
	_status.text = "Connecté — %s" % zone
	_btn_enter.disabled = false
	visible = false


func on_ws_failed(reason: String) -> void:
	_handoff_active = false
	_btn_enter.disabled = false
	visible = true
	var short := reason if reason.length() < 120 else reason.substr(0, 117) + "…"
	_status.text = "WS échoué: %s" % short
