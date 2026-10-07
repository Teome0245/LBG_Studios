extends Node
## HTTP G2 — /healthz local ; le reste proxy → hub_runtime Python (anti double-build).

@export var listen_host: String = "0.0.0.0"
@export var listen_port: int = 8789

var _tcp: TCPServer = TCPServer.new()
var sim: Node = null
var ws_port: int = 8788
var started_at: float = 0.0
var upstream: String = "http://127.0.0.1:8787"


func start(sim_node: Node, port: int = 8789, ws: int = 8788) -> Error:
	sim = sim_node
	listen_port = port
	ws_port = ws
	started_at = Time.get_unix_time_from_system()
	var env_up := OS.get_environment("LBG_HUB_HTTP_UPSTREAM").strip_edges()
	if env_up.is_empty():
		env_up = OS.get_environment("LBG_HUB_AUTH_UPSTREAM").strip_edges()
	if not env_up.is_empty():
		upstream = env_up.rstrip("/")
	var err := _tcp.listen(listen_port, listen_host)
	if err != OK:
		push_error("[prime-hub] HTTP listen failed port=%d err=%s" % [listen_port, err])
		return err
	print("[prime-hub] HTTP on http://%s:%d/healthz (proxy → %s)" % [listen_host, listen_port, upstream])
	set_process(true)
	return OK


func _process(_delta: float) -> void:
	while _tcp.is_connection_available():
		var stream: StreamPeerTCP = _tcp.take_connection()
		if stream == null:
			break
		_serve_once(stream)


func _collision_count() -> int:
	if sim == null or sim.collision == null:
		return 0
	return int(sim.collision.blocks.size())


func _serve_once(stream: StreamPeerTCP) -> void:
	var parsed := _read_http_request(stream)
	var method: String = str(parsed.get("method", "GET"))
	var path: String = str(parsed.get("path", "/"))
	var query: String = str(parsed.get("query", ""))
	var req_body: String = str(parsed.get("body", ""))

	if method == "OPTIONS":
		_write_raw(stream, 204, "", "text/plain")
		return

	if path == "/healthz" or path == "/":
		var uptime := int(Time.get_unix_time_from_system() - started_at)
		var body := JSON.stringify({
			"ok": true,
			"service": "prime_hub",
			"proto": "lbg-ws/2",
			"phase": "G4b",
			"ws_port": ws_port,
			"http_proxy": upstream,
			"tick": int(sim.tick) if sim else 0,
			"bot_count": int(sim.bot_count()) if sim else 0,
			"npc_count": int(sim.npc_count()) if sim else 0,
			"collision_blocks": _collision_count(),
			"uptime_s": uptime,
			"note": "G4b resume ; WS:8787 HTTP:8789 ; peel Python :8797",
		})
		_write_raw(stream, 200, body, "application/json; charset=utf-8")
		return

	var proxied := _proxy(method, path, query, req_body)
	_write_raw(
		stream,
		int(proxied.get("code", 502)),
		str(proxied.get("body", "{\"ok\":false,\"error\":\"proxy_failed\"}")),
		str(proxied.get("content_type", "application/json; charset=utf-8"))
	)


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
	return {"method": method, "path": path, "query": query, "body": body}


func _content_length(headers_blob: String) -> int:
	for line in headers_blob.split("\r\n"):
		var lower := str(line).to_lower()
		if lower.begins_with("content-length:"):
			return int(str(line).substr(15).strip_edges())
	return 0


func _proxy(method: String, path: String, query: String, body: String) -> Dictionary:
	var url_path := path
	if not query.is_empty():
		url_path = path + "?" + query
	var http := HTTPClient.new()
	var host := _host_of(upstream)
	var port := _port_of(upstream)
	var err := http.connect_to_host(host, port)
	if err != OK:
		return {"code": 502, "body": JSON.stringify({"ok": false, "error": "upstream_connect", "detail": err})}
	var deadline := Time.get_ticks_msec() + 8000
	while http.get_status() == HTTPClient.STATUS_CONNECTING or http.get_status() == HTTPClient.STATUS_RESOLVING:
		http.poll()
		if Time.get_ticks_msec() > deadline:
			return {"code": 504, "body": JSON.stringify({"ok": false, "error": "upstream_timeout_connect"})}
		OS.delay_usec(2000)
	if http.get_status() != HTTPClient.STATUS_CONNECTED:
		return {"code": 502, "body": JSON.stringify({"ok": false, "error": "upstream_not_connected", "status": http.get_status()})}

	var headers := PackedStringArray([
		"Content-Type: application/json",
		"Accept: application/json",
		"Connection: close",
	])
	var http_method := HTTPClient.METHOD_GET
	match method:
		"POST":
			http_method = HTTPClient.METHOD_POST
		"PUT":
			http_method = HTTPClient.METHOD_PUT
		"DELETE":
			http_method = HTTPClient.METHOD_DELETE
		"PATCH":
			http_method = HTTPClient.METHOD_PATCH
		_:
			http_method = HTTPClient.METHOD_GET

	err = http.request(http_method, url_path, headers, body)
	if err != OK:
		return {"code": 502, "body": JSON.stringify({"ok": false, "error": "upstream_request", "detail": err})}

	while http.get_status() == HTTPClient.STATUS_REQUESTING:
		http.poll()
		if Time.get_ticks_msec() > deadline:
			return {"code": 504, "body": JSON.stringify({"ok": false, "error": "upstream_timeout_request"})}
		OS.delay_usec(2000)

	if not http.has_response():
		return {"code": 502, "body": JSON.stringify({"ok": false, "error": "upstream_no_response"})}

	var code := http.get_response_code()
	var rb := PackedByteArray()
	while http.get_status() == HTTPClient.STATUS_BODY:
		http.poll()
		var chunk := http.read_response_body_chunk()
		if chunk.size() == 0:
			OS.delay_usec(2000)
		else:
			rb.append_array(chunk)
		if Time.get_ticks_msec() > deadline:
			break

	var content_type := "application/json; charset=utf-8"
	var resp_headers := http.get_response_headers_as_dictionary()
	if resp_headers.has("Content-Type"):
		content_type = str(resp_headers["Content-Type"])
	elif resp_headers.has("content-type"):
		content_type = str(resp_headers["content-type"])
	return {"code": code, "body": rb.get_string_from_utf8(), "content_type": content_type}


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
	elif code == 502:
		reason = "Bad Gateway"
	elif code == 504:
		reason = "Gateway Timeout"
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


func _host_of(url: String) -> String:
	var u := url.replace("http://", "").replace("https://", "")
	return u.split("/")[0].split(":")[0]


func _port_of(url: String) -> int:
	var u := url.replace("http://", "").replace("https://", "")
	var hostport := u.split("/")[0]
	if ":" in hostport:
		return int(hostport.split(":")[1])
	return 80
