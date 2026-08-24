extends Node
class_name LbgWsClient
## LbgWsClient — WebSocket lbg-ws/2 (M12) après auth HTTP M11.
## Connecte avec session_token, consomme enter_world / zone_state, envoie move.

# preload (pas class_name) : reste compilable même si le cache global .godot est incomplet.
const _Crc32Util = preload("res://scripts/crc32_util.gd")

signal connected(your_character_id: int, zone: String)
signal disconnected(reason: String)
signal zone_state_received(payload: Dictionary)
signal login_result(success: bool, reason: String)
signal error_message(message: String)
signal connecting(ws_url: String)
signal handoff_progress(phase: String, detail: String)
signal reconnecting(attempt: int, delay_s: float)
signal echo_state_changed(payload: Dictionary)

@export var proto: String = "lbg-ws/2"
@export var echo_ws_stub: bool = true
@export var auto_enter_world: bool = true
## Après login_result : `enter_world` si HTTP M11 a déjà fait select+enter_zone (défaut).
@export var post_login_ws_action: String = "enter_world"
@export var connect_timeout_s: float = 12.0
@export var response_timeout_s: float = 25.0
@export var auto_reconnect: bool = true
@export var reconnect_base_delay_s: float = 1.0
@export var reconnect_max_delay_s: float = 30.0
## 0 = tentatives illimitées tant que la session était en jeu.
@export var reconnect_max_attempts: int = 0

var _peer: WebSocketPeer = WebSocketPeer.new()
var _url: String = ""
var _session_token: String = ""
var _character_id: int = 0
var _zone: String = "tatooine"
var _ready_sent: bool = false
var _entered: bool = false
var _seq: int = 0
var _active: bool = false
var _connect_elapsed: float = 0.0
var _last_state: int = -1
var _open_elapsed: float = 0.0
var your_character_id: int = 0

var _user_disconnect: bool = false
var _was_in_world: bool = false
var _reconnect_attempts: int = 0
var _reconnect_countdown: float = -1.0
var _reconnect_scheduled: bool = false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	add_to_group("lbg_ws_client")


func is_open() -> bool:
	return _active and _peer.get_ready_state() == WebSocketPeer.STATE_OPEN


func is_reconnecting() -> bool:
	return _reconnect_scheduled or _reconnect_countdown >= 0.0


func connect_session(ws_url: String, session_token: String, character_id: int, zone: String = "tatooine") -> int:
	_cancel_reconnect()
	_user_disconnect = false
	_was_in_world = false
	_reconnect_attempts = 0
	_active = false
	if _peer.get_ready_state() != WebSocketPeer.STATE_CLOSED:
		_peer.close()
	return _start_connect(ws_url, session_token, character_id, zone, false)


func disconnect_session() -> void:
	_user_disconnect = true
	_was_in_world = false
	_cancel_reconnect()
	_active = false
	_ready_sent = false
	_entered = false
	_connect_elapsed = 0.0
	_open_elapsed = 0.0
	_last_state = -1
	if _peer.get_ready_state() != WebSocketPeer.STATE_CLOSED:
		_peer.close()
	_peer = WebSocketPeer.new()
	set_process(false)


func send_move(pos: Vector3, heading: float = 0.0, cell: int = 0) -> void:
	if not is_open():
		return
	_seq += 1
	_send({
		"type": "move",
		"proto": proto,
		"pos": [pos.x, pos.y, pos.z],
		"heading": heading,
		"cell": cell,
		"seq": _seq,
	})


func send_raw(payload: Dictionary) -> void:
	if not is_open():
		return
	_send(payload)


func send_echo_message(payload: Dictionary) -> void:
	var msg_type := str(payload.get("type", ""))
	if echo_ws_stub or not is_open():
		print("[LbgWs] echo stub >> %s" % msg_type)
		_emit_echo_stub(msg_type, payload)
		return
	print("[LbgWs] >> echo %s" % msg_type)
	_send(payload)


func _emit_echo_stub(msg_type: String, payload: Dictionary) -> void:
	var out := {"type": "echo_state", "message": "stub: %s" % msg_type}
	match msg_type:
		"invoke_echo":
			out["echo_character_id"] = str(payload.get("character_id", ""))
		"dismiss_echo":
			out["echo_character_id"] = ""
			out["echo_character_name"] = ""
		"switch_active":
			out["switched"] = true
	echo_state_changed.emit(out)


func _cancel_reconnect() -> void:
	_reconnect_countdown = -1.0
	_reconnect_scheduled = false


func _start_connect(ws_url: String, session_token: String, character_id: int, zone: String, is_retry: bool) -> int:
	_url = ws_url.strip_edges()
	_session_token = session_token
	_character_id = character_id
	_zone = zone if not zone.is_empty() else "tatooine"
	_ready_sent = false
	_entered = false
	_connect_elapsed = 0.0
	_open_elapsed = 0.0
	_last_state = -1
	your_character_id = character_id
	if _url.is_empty() or _session_token.is_empty():
		var why := "ws_url vide" if _url.is_empty() else "session_token vide"
		handoff_progress.emit("error", why)
		disconnected.emit(why)
		return ERR_INVALID_PARAMETER
	_peer = WebSocketPeer.new()
	var err := _peer.connect_to_url(_url)
	if err != OK:
		if is_retry and _was_in_world and auto_reconnect:
			_schedule_reconnect("connect_to_url err %s" % err)
		else:
			disconnected.emit("connect_to_url err %s" % err)
		return err
	_active = true
	set_process(true)
	if is_retry:
		print("[LbgWs] reconnect attempt %d %s char=%d" % [_reconnect_attempts, _url, character_id])
	else:
		print("[LbgWs] connecting %s char=%d" % [_url, character_id])
	connecting.emit(_url)
	return OK


func _schedule_reconnect(reason: String) -> void:
	if _user_disconnect or not auto_reconnect or not _was_in_world:
		set_process(false)
		disconnected.emit(reason)
		return
	if reconnect_max_attempts > 0 and _reconnect_attempts >= reconnect_max_attempts:
		set_process(false)
		disconnected.emit("%s (reconnect max %d)" % [reason, reconnect_max_attempts])
		return
	_reconnect_attempts += 1
	var exp := pow(2.0, float(_reconnect_attempts - 1))
	var delay := minf(reconnect_base_delay_s * exp, reconnect_max_delay_s)
	_active = false
	_ready_sent = false
	_entered = false
	_connect_elapsed = 0.0
	_open_elapsed = 0.0
	_last_state = -1
	if _peer.get_ready_state() != WebSocketPeer.STATE_CLOSED:
		_peer.close()
	_peer = WebSocketPeer.new()
	_reconnect_countdown = delay
	_reconnect_scheduled = true
	set_process(true)
	reconnecting.emit(_reconnect_attempts, delay)
	handoff_progress.emit("reconnect", "dans %.0fs (#%d)" % [delay, _reconnect_attempts])
	print("[LbgWs] reconnect in %.1fs attempt=%d — %s" % [delay, _reconnect_attempts, reason])


func _ws_state_name(state: int) -> String:
	match state:
		WebSocketPeer.STATE_CONNECTING:
			return "CONNECTING"
		WebSocketPeer.STATE_OPEN:
			return "OPEN"
		WebSocketPeer.STATE_CLOSING:
			return "CLOSING"
		WebSocketPeer.STATE_CLOSED:
			return "CLOSED"
		_:
			return str(state)


func _send_login_if_needed() -> void:
	## Envoyer le login AVANT tout signal UI — un handler qui plante ne doit pas bloquer l’auth.
	if _ready_sent or not _active:
		return
	if _peer.get_ready_state() != WebSocketPeer.STATE_OPEN:
		return
	_ready_sent = true
	var login_payload := {
		"type": "login",
		"proto": proto,
		"session_token": _session_token,
	}
	_send(login_payload)
	print("[LbgWs] >> login token_len=%d" % _session_token.length())
	handoff_progress.emit("auth", "login WS…")


func _process(delta: float) -> void:
	if _reconnect_countdown >= 0.0:
		_reconnect_countdown -= delta
		if _reconnect_countdown <= 0.0:
			_reconnect_countdown = -1.0
			_reconnect_scheduled = false
			_start_connect(_url, _session_token, _character_id, _zone, true)
		return
	if not _active:
		return
	_peer.poll()
	var state := _peer.get_ready_state()
	if state != _last_state:
		_last_state = state
		print("[LbgWs] state=%s url=%s" % [_ws_state_name(state), _url])
		if state == WebSocketPeer.STATE_OPEN:
			_send_login_if_needed()
		handoff_progress.emit("state", _ws_state_name(state))
	if state == WebSocketPeer.STATE_CONNECTING:
		_connect_elapsed += delta
		if connect_timeout_s > 0.0 and _connect_elapsed >= connect_timeout_s:
			_active = false
			_peer.close()
			var hint := " (pare-feu Windows ? test: Test-NetConnection 192.168.0.246 -Port 50000)"
			var msg := "timeout TCP %ss %s%s" % [int(connect_timeout_s), _url, hint]
			if _was_in_world and auto_reconnect:
				_schedule_reconnect(msg)
			else:
				disconnected.emit(msg)
			return
	elif state == WebSocketPeer.STATE_OPEN and not _entered:
		_open_elapsed += delta
		if response_timeout_s > 0.0 and _open_elapsed >= response_timeout_s:
			_active = false
			_peer.close()
			var msg := "timeout réponse gateway %ss après OPEN" % int(response_timeout_s)
			if _was_in_world and auto_reconnect:
				_schedule_reconnect(msg)
			else:
				disconnected.emit(msg)
			return
	if state == WebSocketPeer.STATE_OPEN:
		_send_login_if_needed()
		while _peer.get_available_packet_count() > 0:
			var raw := _peer.get_packet().get_string_from_utf8()
			if raw.is_empty():
				error_message.emit("paquet WS vide (binaire ?)")
				continue
			print("[LbgWs] << %s" % raw.substr(0, mini(120, raw.length())))
			_dispatch(raw)
	elif state == WebSocketPeer.STATE_CLOSING:
		pass
	elif state == WebSocketPeer.STATE_CLOSED:
		if not _active:
			return
		_active = false
		var code := _peer.get_close_code()
		var reason := _peer.get_close_reason()
		var msg := "closed code=%s" % code
		if not reason.is_empty():
			msg = "closed code=%s %s" % [code, reason]
		if _was_in_world and auto_reconnect:
			_schedule_reconnect(msg)
		else:
			disconnected.emit(msg)


func _send(payload: Dictionary) -> void:
	var text := JSON.stringify(payload)
	_peer.send_text(text)


func _dispatch(text: String) -> void:
	var data: Variant = JSON.parse_string(text)
	if typeof(data) != TYPE_DICTIONARY:
		push_warning("[LbgWs] JSON invalide: %s" % text.substr(0, min(120, text.length())))
		error_message.emit("réponse gateway illisible")
		return
	var d: Dictionary = data
	var t := str(d.get("type", ""))
	match t:
		"login_result":
			var ok := bool(d.get("success", false))
			var reason := str(d.get("reason", ""))
			login_result.emit(ok, reason)
			if not ok:
				_was_in_world = false
				_cancel_reconnect()
				error_message.emit("login_result: %s" % (reason if reason else "auth_failed"))
				disconnected.emit("login_result: %s" % (reason if reason else "auth_failed"))
				return
			handoff_progress.emit("auth", "OK — enter_world…")
			_open_elapsed = 0.0
			if auto_enter_world:
				if post_login_ws_action == "select_character" and _character_id > 0:
					_send({
						"type": "select_character",
						"proto": proto,
						"character_id": _character_id,
					})
				else:
					_send({"type": "enter_world", "proto": proto, "zone": _zone})
		"enter_world", "zone_state":
			if d.has("your_character_id"):
				your_character_id = int(d.get("your_character_id"))
			var zone := str(d.get("zone", d.get("map", _zone)))
			if not _entered:
				_entered = true
				_was_in_world = true
				_reconnect_attempts = 0
				_cancel_reconnect()
				connected.emit(your_character_id, zone)
			zone_state_received.emit(d)
		"characters_list":
			pass
		"error":
			error_message.emit(str(d.get("message", "error")))
		"chat":
			pass
		"echo_state":
			echo_state_changed.emit(d)
		_:
			pass


## Convertit un id gateway (string|int) en oid EntityManager.
static func resolve_oid(raw: Variant) -> int:
	if typeof(raw) == TYPE_INT:
		return int(raw)
	var s := str(raw)
	if s.is_valid_int():
		return int(s)
	if s.is_empty():
		return 0
	return _Crc32Util.entity_oid(s)
