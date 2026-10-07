extends RefCounted
class_name HubAuth
## Résolution session — spike tokens locaux + optionnel upstream Python hub_runtime.

const SPIKE_TOKENS := ["spike-local", "spike", "dev-mock-token", "smoke-g0"]
const HUMAN_OID := 100001


func resolve(token: String) -> Dictionary:
	## Retourne {ok, username, character_id} ou {ok:false}
	var t := token.strip_edges()
	if t.is_empty():
		return {"ok": false}
	if t in SPIKE_TOKENS:
		return {"ok": true, "username": "Voyageur", "character_id": HUMAN_OID, "source": "spike"}
	var upstream := OS.get_environment("LBG_HUB_AUTH_UPSTREAM").strip_edges()
	if upstream.is_empty():
		upstream = "http://127.0.0.1:8787"
	var url := upstream.rstrip("/") + "/v1/auth/resolve"
	var body := JSON.stringify({"session_token": t})
	var http := HTTPClient.new()
	var err := http.connect_to_host(_host_of(url), _port_of(url))
	if err != OK:
		# Fallback G1 : token opaque → Voyageur (lab local sans Python)
		return {"ok": true, "username": "Voyageur", "character_id": HUMAN_OID, "source": "fallback"}
	var deadline := Time.get_ticks_msec() + 2500
	while http.get_status() == HTTPClient.STATUS_CONNECTING or http.get_status() == HTTPClient.STATUS_RESOLVING:
		http.poll()
		if Time.get_ticks_msec() > deadline:
			return {"ok": true, "username": "Voyageur", "character_id": HUMAN_OID, "source": "fallback_timeout"}
		OS.delay_usec(2000)
	if http.get_status() != HTTPClient.STATUS_CONNECTED:
		return {"ok": true, "username": "Voyageur", "character_id": HUMAN_OID, "source": "fallback_conn"}
	var path := _path_of(url)
	err = http.request(HTTPClient.METHOD_POST, path, PackedStringArray(["Content-Type: application/json"]), body)
	if err != OK:
		return {"ok": true, "username": "Voyageur", "character_id": HUMAN_OID, "source": "fallback_req"}
	while http.get_status() == HTTPClient.STATUS_REQUESTING:
		http.poll()
		if Time.get_ticks_msec() > deadline:
			break
		OS.delay_usec(2000)
	if http.has_response():
		var rb := PackedByteArray()
		while http.get_status() == HTTPClient.STATUS_BODY:
			http.poll()
			var chunk := http.read_response_body_chunk()
			if chunk.size() == 0:
				OS.delay_usec(2000)
			else:
				rb.append_array(chunk)
		var parsed: Variant = JSON.parse_string(rb.get_string_from_utf8())
		if typeof(parsed) == TYPE_DICTIONARY and bool(parsed.get("ok", false)):
			return {
				"ok": true,
				"username": str(parsed.get("username", "Voyageur")),
				"character_id": int(parsed.get("character_id", HUMAN_OID)),
				"source": "upstream",
			}
		if typeof(parsed) == TYPE_DICTIONARY and parsed.get("error") == "session_expired":
			return {"ok": false}
	return {"ok": true, "username": "Voyageur", "character_id": HUMAN_OID, "source": "fallback_parse"}


func _host_of(url: String) -> String:
	var u := url.replace("http://", "").replace("https://", "")
	return u.split("/")[0].split(":")[0]


func _port_of(url: String) -> int:
	var u := url.replace("http://", "").replace("https://", "")
	var hostport := u.split("/")[0]
	if ":" in hostport:
		return int(hostport.split(":")[1])
	return 80


func _path_of(url: String) -> String:
	var u := url.replace("http://", "").replace("https://", "")
	var slash := u.find("/")
	if slash < 0:
		return "/"
	return u.substr(slash)
