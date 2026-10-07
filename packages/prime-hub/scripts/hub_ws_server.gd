extends Node
## Serveur WebSocket lbg-ws/2 (port dédié — pair HTTP séparé).

signal client_count_changed(n: int)

const HubAuthScript = preload("res://scripts/hub_auth.gd")
const PROTO := "lbg-ws/2"

@export var listen_host: String = "0.0.0.0"
@export var listen_port: int = 8787

var _tcp: TCPServer = TCPServer.new()
var _clients: Array = []
var sim: Node = null
var auth = HubAuthScript.new()


func start(sim_node: Node, port: int = 8787) -> Error:
	sim = sim_node
	listen_port = port
	var err := _tcp.listen(listen_port, listen_host)
	if err != OK:
		push_error("[prime-hub] WS listen failed port=%d err=%s" % [listen_port, err])
		return err
	print("[prime-hub] WS lbg-ws/2 on ws://%s:%d/ws" % [listen_host, listen_port])
	set_process(true)
	return OK


func client_count() -> int:
	return _clients.size()


func _process(_delta: float) -> void:
	while _tcp.is_connection_available():
		var stream: StreamPeerTCP = _tcp.take_connection()
		if stream == null:
			break
		var peer := WebSocketPeer.new()
		var err := peer.accept_stream(stream)
		if err != OK:
			push_warning("[prime-hub] accept_stream failed: %s" % err)
			continue
		_clients.append({"peer": peer, "oid": 100001, "name": "Voyageur"})
		client_count_changed.emit(_clients.size())
		print("[prime-hub] WS client +1 (n=%d)" % _clients.size())

	var dead: Array = []
	for i in range(_clients.size()):
		var c: Dictionary = _clients[i]
		var peer: WebSocketPeer = c["peer"]
		peer.poll()
		var st := peer.get_ready_state()
		if st == WebSocketPeer.STATE_OPEN:
			while peer.get_available_packet_count() > 0:
				_handle_message(c, peer.get_packet().get_string_from_utf8())
		elif st == WebSocketPeer.STATE_CLOSED:
			dead.append(i)

	if not dead.is_empty():
		dead.reverse()
		for i in dead:
			var c: Dictionary = _clients[i]
			var oid: int = int(c.get("oid", 0))
			_clients.remove_at(i)
			if oid > 0 and not _oid_still_connected(oid):
				sim.remove_human(oid)
		client_count_changed.emit(_clients.size())


func _oid_still_connected(oid: int) -> bool:
	for c in _clients:
		if int(c.get("oid", 0)) == oid:
			return true
	return false


func _handle_message(c: Dictionary, raw: String) -> void:
	var data: Variant = JSON.parse_string(raw)
	if typeof(data) != TYPE_DICTIONARY:
		_send(c, {"type": "error", "message": "bad_json"})
		return
	var msg: Dictionary = data
	var mtype := str(msg.get("type", ""))
	match mtype:
		"login":
			var token := str(msg.get("session_token", "")).strip_edges()
			var sess: Dictionary = auth.resolve(token)
			var ok := bool(sess.get("ok", false))
			var oid := int(sess.get("character_id", 100001))
			var player := str(sess.get("username", "Voyageur"))
			if ok:
				c["oid"] = oid
				c["name"] = player
				sim.ensure_human(oid, player)
			_send(c, {
				"type": "login_result",
				"proto": PROTO,
				"success": ok,
				"reason": str(sess.get("source", "prime_hub")) if ok else "bad_token",
				"character_id": oid if ok else 0,
				"player": player if ok else "",
			})
		"enter_world", "select_character":
			var oid: int = int(c.get("oid", 100001))
			var player: String = str(c.get("name", "Voyageur"))
			sim.ensure_human(oid, player)
			_send(c, sim.enter_world_payload(oid))
			sim.fleet_greet_human(player, oid)
			_flush_chat()
		"move":
			var pos = msg.get("pos")
			if typeof(pos) == TYPE_ARRAY and pos.size() >= 3:
				sim.set_human_pos(int(c["oid"]), float(pos[0]), float(pos[1]), float(pos[2]))
			elif typeof(pos) == TYPE_ARRAY and pos.size() >= 2:
				sim.set_human_pos(int(c["oid"]), float(pos[0]), 0.15, float(pos[1]))
		"chat", "say":
			var text := str(msg.get("text", msg.get("message", ""))).strip_edges()
			if text.is_empty():
				return
			if text.length() > 200:
				text = text.substr(0, 200)
			broadcast({
				"type": "chat",
				"proto": PROTO,
				"from": str(c.get("name", "?")),
				"from_oid": int(c.get("oid", 0)),
				"oid": int(c.get("oid", 0)),
				"text": text,
				"source": "human",
			})
		_:
			pass


func _send(c: Dictionary, payload: Dictionary) -> void:
	var peer: WebSocketPeer = c["peer"]
	if peer.get_ready_state() != WebSocketPeer.STATE_OPEN:
		return
	peer.send_text(JSON.stringify(payload))


func broadcast(payload: Dictionary) -> void:
	var raw := JSON.stringify(payload)
	for c in _clients:
		var peer: WebSocketPeer = c["peer"]
		if peer.get_ready_state() == WebSocketPeer.STATE_OPEN:
			peer.send_text(raw)


func _flush_chat() -> void:
	if sim == null:
		return
	for msg in sim.drain_chat():
		broadcast(msg)


func flush_chat() -> void:
	_flush_chat()


func broadcast_zone_state() -> void:
	if _clients.is_empty():
		return
	var base: Dictionary = sim.zone_state_payload(100001)
	var raw_base := JSON.stringify(base)
	for c in _clients:
		var peer: WebSocketPeer = c["peer"]
		if peer.get_ready_state() != WebSocketPeer.STATE_OPEN:
			continue
		var oid: int = int(c.get("oid", 100001))
		var err: Error
		if oid == 100001:
			err = peer.send_text(raw_base)
		else:
			base["your_character_id"] = oid
			var eid := "player:%d" % oid
			if sim.entities.has(eid):
				var p: Vector3 = sim.entities[eid]["pos"]
				base["position"] = [p.x, p.y, p.z]
			err = peer.send_text(JSON.stringify(base))
		if err != OK:
			pass
