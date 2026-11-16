extends Node
## Passerelle unifiée lbg-ws/2 + HTTP peel sur un seul TCPServer.
## WS = framing manuel après handshake 101 ; HTTP = hub_http router.

signal client_count_changed(n: int)

const HubAuthScript = preload("res://scripts/hub_auth.gd")
const PROTO := "lbg-ws/2"
const WS_GUID := "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

@export var listen_host: String = "0.0.0.0"
@export var listen_port: int = 8787

var _tcp: TCPServer = TCPServer.new()
var _clients: Array = []  # {stream, oid, name, buf: PackedByteArray, mode: "ws"}
var sim: Node = null
var http: Node = null
var auth = null
## 1 accept/frame : le handshake bloquant reste fiable (Godot headless), sans empiler les waits.
const MAX_ACCEPTS_PER_FRAME := 1


func start(sim_node: Node, port: int = 8787, http_router: Node = null, auth_svc = null) -> Error:
	sim = sim_node
	http = http_router
	auth = auth_svc if auth_svc != null else HubAuthScript.new()
	if auth_svc == null and auth.has_method("setup"):
		auth.setup()
	listen_port = port
	var err := _tcp.listen(listen_port, listen_host)
	if err != OK:
		push_error("[prime-hub] gateway listen failed port=%d err=%s" % [listen_port, err])
		return err
	print("[prime-hub] gateway HTTP+WS on :%d (ws://%s:%d/ws)" % [listen_port, listen_host, listen_port])
	set_process(true)
	return OK


func client_count() -> int:
	return _clients.size()


func _process(_delta: float) -> void:
	var accepted := 0
	while accepted < MAX_ACCEPTS_PER_FRAME and _tcp.is_connection_available():
		var stream: StreamPeerTCP = _tcp.take_connection()
		if stream == null:
			break
		stream.set_no_delay(true)
		_accept_connection(stream)
		accepted += 1
	_pump_clients()


func _read_request_blocking(stream: StreamPeerTCP, timeout_ms: int = 4000) -> PackedByteArray:
	## poll + delay — fiable headless. Pas de delay tant que des octets arrivent.
	var deadline := Time.get_ticks_msec() + timeout_ms
	var req := PackedByteArray()
	while Time.get_ticks_msec() < deadline:
		stream.poll()
		var n := stream.get_available_bytes()
		if n > 0:
			req.append_array(stream.get_data(n)[1])
			var text_so_far := req.get_string_from_utf8()
			var hdr_end := text_so_far.find("\r\n\r\n")
			if hdr_end < 0:
				hdr_end = text_so_far.find("\n\n")
			if hdr_end >= 0:
				var headers_blob := text_so_far.substr(0, hdr_end)
				var content_len := _header_int(headers_blob, "content-length")
				var sep := 4 if text_so_far.find("\r\n\r\n") >= 0 else 2
				var body_start := hdr_end + sep
				var have := req.size() - body_start
				if content_len <= 0 or have >= content_len:
					return req
			# Données partielles : re-poll immédiat sans dormir.
			continue
		elif stream.get_status() != StreamPeerTCP.STATUS_CONNECTED and stream.get_status() != StreamPeerTCP.STATUS_CONNECTING:
			break
		else:
			OS.delay_usec(500)
	return req


func _accept_connection(stream: StreamPeerTCP) -> void:
	var req := _read_request_blocking(stream)
	if req.is_empty():
		stream.disconnect_from_host()
		return
	var text := req.get_string_from_utf8()
	var hdr_end := text.find("\r\n\r\n")
	var sep := 4
	if hdr_end < 0:
		hdr_end = text.find("\n\n")
		sep = 2
	if hdr_end < 0:
		stream.disconnect_from_host()
		return
	var headers := text.substr(0, hdr_end)
	var lower := headers.to_lower()
	if "upgrade: websocket" in lower:
		if not _ws_handshake(stream, headers):
			stream.disconnect_from_host()
			return
		var leftover := req.slice(hdr_end + sep)
		_clients.append({
			"stream": stream,
			"oid": 100001,
			"name": "Voyageur",
			"buf": leftover,
			"mode": "ws",
		})
		client_count_changed.emit(_clients.size())
		print("[prime-hub] WS client +1 (n=%d)" % _clients.size())
		return
	if http == null:
		stream.disconnect_from_host()
		return
	var parsed: Dictionary = http.parse_http_bytes(req)
	var result: Dictionary = http.handle_raw_request(
		str(parsed.get("method", "GET")),
		str(parsed.get("path", "/")),
		str(parsed.get("query", "")),
		str(parsed.get("body", ""))
	)
	http.write_response(
		stream,
		int(result.get("code", 500)),
		str(result.get("body", "")),
		str(result.get("content_type", "application/json; charset=utf-8"))
	)


func _header_int(headers: String, name: String) -> int:
	var want := name.to_lower() + ":"
	for line in headers.split("\r\n"):
		var lower := str(line).to_lower()
		if lower.begins_with(want):
			return int(str(line).substr(name.length() + 1).strip_edges())
	return 0


func _header_value(headers: String, name: String) -> String:
	var want := name.to_lower() + ":"
	for line in headers.split("\r\n"):
		if str(line).to_lower().begins_with(want):
			return str(line).substr(name.length() + 1).strip_edges()
	return ""


func _ws_accept_key(client_key: String) -> String:
	var raw := (client_key + WS_GUID).to_utf8_buffer()
	var ctx := HashingContext.new()
	ctx.start(HashingContext.HASH_SHA1)
	ctx.update(raw)
	return Marshalls.raw_to_base64(ctx.finish())


func _ws_handshake(stream: StreamPeerTCP, headers: String) -> bool:
	var key := _header_value(headers, "Sec-WebSocket-Key")
	if key.is_empty():
		return false
	var accept := _ws_accept_key(key)
	var resp := "HTTP/1.1 101 Switching Protocols\r\n"
	resp += "Upgrade: websocket\r\n"
	resp += "Connection: Upgrade\r\n"
	resp += "Sec-WebSocket-Accept: %s\r\n\r\n" % accept
	stream.put_data(resp.to_utf8_buffer())
	return true


func _pump_clients() -> void:
	var dead: Array = []
	for i in range(_clients.size()):
		var c: Dictionary = _clients[i]
		var stream: StreamPeerTCP = c["stream"]
		stream.poll()
		if stream.get_status() != StreamPeerTCP.STATUS_CONNECTED:
			dead.append(i)
			continue
		var n := stream.get_available_bytes()
		if n > 0:
			(c["buf"] as PackedByteArray).append_array(stream.get_data(n)[1])
		var messages := _ws_take_messages(c)
		for raw in messages:
			_handle_message(c, str(raw))
	if not dead.is_empty():
		dead.reverse()
		for i in dead:
			var c2: Dictionary = _clients[i]
			var oid: int = int(c2.get("oid", 0))
			_clients.remove_at(i)
			if oid > 0 and not _oid_still_connected(oid):
				sim.remove_human(oid)
		client_count_changed.emit(_clients.size())


func _ws_take_messages(c: Dictionary) -> Array:
	var out: Array = []
	var buf: PackedByteArray = c["buf"]
	while buf.size() >= 2:
		var b0 := buf[0]
		var b1 := buf[1]
		var opcode := b0 & 0x0F
		var masked := (b1 & 0x80) != 0
		var length := b1 & 0x7F
		var offset := 2
		if length == 126:
			if buf.size() < 4:
				break
			length = (buf[2] << 8) | buf[3]
			offset = 4
		elif length == 127:
			# trop long pour hub — drop
			c["buf"] = PackedByteArray()
			return out
		var mask_offset := offset
		if masked:
			offset += 4
		if buf.size() < offset + length:
			break
		if masked:
			var mask := buf.slice(mask_offset, mask_offset + 4)
			var payload := PackedByteArray()
			payload.resize(length)
			for i in range(length):
				payload[i] = buf[offset + i] ^ mask[i % 4]
			buf = buf.slice(offset + length)
			c["buf"] = buf
			if opcode == 0x8:  # close
				return out
			if opcode == 0x9:  # ping → pong
				_ws_send_frame(c, payload, 0xA)
				continue
			if opcode == 0x1 or opcode == 0x2:
				out.append(payload.get_string_from_utf8())
		else:
			# serveur→client unmasked only; client must mask — ignore
			buf = buf.slice(offset + length)
			c["buf"] = buf
	return out


func _ws_send_frame(c: Dictionary, payload: PackedByteArray, opcode: int = 0x1, drop_on_backpressure: bool = false) -> bool:
	## drop_on_backpressure : zone_state — ne jamais bloquer la sim si Send-Q plein.
	var stream: StreamPeerTCP = c["stream"]
	var header := PackedByteArray()
	header.append(0x80 | (opcode & 0x0F))
	var n := payload.size()
	if n < 126:
		header.append(n)
	elif n <= 0xFFFF:
		header.append(126)
		header.append((n >> 8) & 0xFF)
		header.append(n & 0xFF)
	else:
		return false
	var packet := header
	if n > 0:
		packet.append_array(payload)
	if not drop_on_backpressure:
		stream.put_data(packet)
		return true
	var sent := 0
	while sent < packet.size():
		var r: Array = stream.put_partial_data(packet.slice(sent))
		if int(r[0]) != OK or int(r[1]) <= 0:
			return false
		sent += int(r[1])
	return true


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
			var oid2: int = int(c.get("oid", 100001))
			var player2: String = str(c.get("name", "Voyageur"))
			sim.ensure_human(oid2, player2)
			_send(c, sim.enter_world_payload(oid2))
			sim.fleet_greet_human(player2, oid2)
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


func _send(c: Dictionary, payload: Dictionary, drop_on_backpressure: bool = false) -> bool:
	return _ws_send_frame(c, JSON.stringify(payload).to_utf8_buffer(), 0x1, drop_on_backpressure)


func broadcast(payload: Dictionary) -> void:
	var raw := JSON.stringify(payload).to_utf8_buffer()
	for c in _clients:
		_ws_send_frame(c, raw, 0x1, false)


func _flush_chat() -> void:
	if sim == null:
		return
	for msg in sim.drain_chat():
		var range_m := float(msg.get("range_m", 0.0))
		var m_pos: Variant = msg.get("pos", null)
		if range_m > 0.0 and m_pos is Array and (m_pos as Array).size() >= 3:
			var arr: Array = m_pos
			var target_pos := Vector3(float(arr[0]), float(arr[1]), float(arr[2]))
			var r2 := range_m * range_m
			for c in _clients:
				var c_oid: int = int(c.get("oid", 0))
				var eid := "player:%d" % c_oid
				if sim.entities.has(eid):
					var p: Vector3 = sim.entities[eid]["pos"]
					var dx := p.x - target_pos.x
					var dz := p.z - target_pos.z
					if dx * dx + dz * dz <= r2:
						_send(c, msg, false)
				else:
					_send(c, msg, false)
		else:
			broadcast(msg)


func flush_chat() -> void:
	_flush_chat()


func broadcast_zone_state() -> void:
	if _clients.is_empty():
		return
	for c in _clients:
		var oid: int = int(c.get("oid", 100001))
		# Si le client ne consomme pas assez vite : drop (garde la sim fluide).
		_send(c, sim.zone_state_payload(oid), true)
