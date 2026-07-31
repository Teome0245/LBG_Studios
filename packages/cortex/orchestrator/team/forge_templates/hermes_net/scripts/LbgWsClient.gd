extends Node
class_name LbgWsClient
## LbgWsClient — WebSocket lbg-ws/2 (M12) après auth HTTP M11.
## Connecte avec session_token, consomme enter_world / zone_state, envoie move.

signal connected(your_character_id: int, zone: String)
signal disconnected(reason: String)
signal zone_state_received(payload: Dictionary)
signal login_result(success: bool, reason: String)
signal error_message(message: String)

@export var proto: String = "lbg-ws/2"
@export var auto_enter_world: bool = true

var _peer: WebSocketPeer = WebSocketPeer.new()
var _url: String = ""
var _session_token: String = ""
var _character_id: int = 0
var _zone: String = "tatooine"
var _ready_sent: bool = false
var _seq: int = 0
var _active: bool = false
var your_character_id: int = 0


func is_open() -> bool:
	return _active and _peer.get_ready_state() == WebSocketPeer.STATE_OPEN


func connect_session(ws_url: String, session_token: String, character_id: int, zone: String = "tatooine") -> int:
	disconnect_session()
	_url = ws_url.strip_edges()
	_session_token = session_token
	_character_id = character_id
	_zone = zone if not zone.is_empty() else "tatooine"
	_ready_sent = false
	your_character_id = character_id
	if _url.is_empty() or _session_token.is_empty():
		disconnected.emit("ws_url ou session_token vide")
		return ERR_INVALID_PARAMETER
	var err := _peer.connect_to_url(_url)
	if err != OK:
		disconnected.emit("connect_to_url err %s" % err)
		return err
	_active = true
	print("[LbgWs] connecting %s char=%d" % [_url, character_id])
	return OK


func disconnect_session() -> void:
	_active = false
	_ready_sent = false
	if _peer.get_ready_state() != WebSocketPeer.STATE_CLOSED:
		_peer.close()
	_peer = WebSocketPeer.new()


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


func _process(_delta: float) -> void:
	if not _active:
		return
	_peer.poll()
	var state := _peer.get_ready_state()
	if state == WebSocketPeer.STATE_OPEN:
		if not _ready_sent:
			_ready_sent = true
			_send({
				"type": "login",
				"proto": proto,
				"session_token": _session_token,
			})
		while _peer.get_available_packet_count() > 0:
			var raw := _peer.get_packet().get_string_from_utf8()
			_dispatch(raw)
	elif state == WebSocketPeer.STATE_CLOSING:
		pass
	elif state == WebSocketPeer.STATE_CLOSED:
		if _active:
			_active = false
			var code := _peer.get_close_code()
			disconnected.emit("closed code=%s" % code)


func _send(payload: Dictionary) -> void:
	var text := JSON.stringify(payload)
	_peer.send_text(text)


func _dispatch(text: String) -> void:
	var data: Variant = JSON.parse_string(text)
	if typeof(data) != TYPE_DICTIONARY:
		return
	var d: Dictionary = data
	var t := str(d.get("type", ""))
	match t:
		"login_result":
			var ok := bool(d.get("success", false))
			login_result.emit(ok, str(d.get("reason", "")))
			if ok and auto_enter_world:
				if _character_id > 0:
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
			if t == "enter_world":
				connected.emit(your_character_id, zone)
			zone_state_received.emit(d)
		"characters_list":
			pass
		"error":
			error_message.emit(str(d.get("message", "error")))
		"chat":
			pass
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
	return Crc32Util.entity_oid(s)
