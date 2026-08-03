# dialogue_bridge.gd — Rang 2 : session_summary → persona MMO via Pilot (ADR 0004)
# Chemin court sans legacy /mmo/ : Godot → POST /v1/pilot/agent-dialogue/invoke
extends Node
class_name DialogueBridge

signal reply_ready(ok: bool, reply: String, meta: Dictionary)
signal busy_changed(busy: bool)

const CONFIG_PATH := "res://config/dialogue_bridge.json"
const SESSION_PATH := "user://session_summary.json"
const SESSION_KEYS: Array[String] = [
	"tracked_quest",
	"last_npc",
	"player_note",
	"session_mood",
	"quest_snapshot",
	"memory_hint",
]

var _http: HTTPRequest
var _busy: bool = false
var _cfg: Dictionary = {}
var _session: Dictionary = {}
var _req_id: int = 0

func _ready() -> void:
	_http = HTTPRequest.new()
	_http.timeout = 60.0
	add_child(_http)
	_http.request_completed.connect(_on_http_done)
	_load_config()
	_load_session()


func is_enabled() -> bool:
	return bool(_cfg.get("enabled", true))


func is_busy() -> bool:
	return _busy


func get_session_summary() -> Dictionary:
	return _session.duplicate(true)


func update_session(patch: Dictionary) -> void:
	for k in SESSION_KEYS:
		if not patch.has(k):
			continue
		var v: Variant = patch[k]
		if v == null:
			_session.erase(k)
			continue
		var s := str(v).strip_edges()
		if s.is_empty():
			_session.erase(k)
			continue
		if s.length() > 160:
			s = s.substr(0, 160)
		_session[k] = s
	_save_session()


func touch_npc(npc_name: String, world_npc_id: String = "") -> void:
	var patch := {"last_npc": npc_name}
	if not world_npc_id.is_empty() and not _session.has("tracked_quest"):
		pass
	update_session(patch)
	if not world_npc_id.is_empty():
		# world_npc_id n'est pas dans session_summary ; stocké uniquement pour debug local
		_session["_last_world_npc_id"] = world_npc_id
		_save_session()


func fallback_stub_on_error() -> bool:
	return bool(_cfg.get("fallback_stub_on_error", true))


func request_npc_reply(
	player_text: String,
	world_npc_id: String,
	npc_name: String,
	actor_id: String = "prime:client"
) -> bool:
	if _busy:
		return false
	if not is_enabled():
		reply_ready.emit(false, "", {"error": "dialogue_bridge_disabled"})
		return false
	var base := str(_cfg.get("pilot_base_url", "http://192.168.0.140:8000")).rstrip("/")
	var path := str(_cfg.get("invoke_path", "/v1/pilot/agent-dialogue/invoke"))
	var url := "%s%s" % [base, path]
	var text := player_text.strip_edges()
	if text.is_empty():
		text = str(_cfg.get("greeting_text", "Bonjour."))
	var ss := _sanitize_session_for_wire()
	if not npc_name.is_empty():
		ss["last_npc"] = npc_name if str(ss.get("last_npc", "")).is_empty() else str(ss.get("last_npc"))
	var context := {
		"world_npc_id": world_npc_id,
		"npc_name": npc_name,
		"lyra_engagement": "mmo_persona",
		"_skip_factual_status": true,
		"session_summary": ss,
	}
	var body := {
		"actor_id": actor_id,
		"text": text,
		"context": context,
	}
	var payload := JSON.stringify(body)
	var headers := PackedStringArray(["Content-Type: application/json", "Accept: application/json"])
	_busy = true
	busy_changed.emit(true)
	_req_id += 1
	var my_id := _req_id
	var err := _http.request(url, headers, HTTPClient.METHOD_POST, payload)
	if err != OK:
		_busy = false
		busy_changed.emit(false)
		reply_ready.emit(false, "", {"error": "http_request_failed", "code": err, "req_id": my_id})
		return false
	return true


func _sanitize_session_for_wire() -> Dictionary:
	var out := {}
	for k in SESSION_KEYS:
		if not _session.has(k):
			continue
		var s := str(_session[k]).strip_edges()
		if s.is_empty():
			continue
		if s.length() > 160:
			s = s.substr(0, 160)
		out[k] = s
	return out


func _load_config() -> void:
	_cfg = {
		"enabled": true,
		"pilot_base_url": "http://192.168.0.140:8000",
		"invoke_path": "/v1/pilot/agent-dialogue/invoke",
		"timeout_sec": 60,
		"fallback_stub_on_error": true,
		"greeting_text": "Bonjour, parle-moi de cet endroit.",
	}
	if not FileAccess.file_exists(CONFIG_PATH):
		return
	var f := FileAccess.open(CONFIG_PATH, FileAccess.READ)
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if raw is Dictionary:
		for k in (raw as Dictionary).keys():
			_cfg[k] = (raw as Dictionary)[k]
	var t := float(_cfg.get("timeout_sec", 60))
	_http.timeout = maxf(10.0, t)


func _load_session() -> void:
	_session = {}
	if not FileAccess.file_exists(SESSION_PATH):
		return
	var f := FileAccess.open(SESSION_PATH, FileAccess.READ)
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if raw is Dictionary:
		update_session(raw as Dictionary)


func _save_session() -> void:
	var wire := _sanitize_session_for_wire()
	# conserver debug keys locales
	if _session.has("_last_world_npc_id"):
		wire["_last_world_npc_id"] = _session["_last_world_npc_id"]
	var f := FileAccess.open(SESSION_PATH, FileAccess.WRITE)
	if f == null:
		return
	f.store_string(JSON.stringify(wire))
	f.close()


func _on_http_done(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	_busy = false
	busy_changed.emit(false)
	var meta := {"http_result": result, "status": response_code}
	if result != HTTPRequest.RESULT_SUCCESS:
		reply_ready.emit(false, "", meta)
		return
	var text := body.get_string_from_utf8()
	var raw: Variant = JSON.parse_string(text)
	if not raw is Dictionary:
		meta["error"] = "invalid_json"
		reply_ready.emit(false, "", meta)
		return
	var d: Dictionary = raw
	meta["lyra_engagement_resolved"] = str(
		((d.get("meta") as Dictionary).get("lyra_engagement_resolved", ""))
		if d.get("meta") is Dictionary else ""
	)
	meta["dialogue_profile_resolved"] = str(
		((d.get("meta") as Dictionary).get("dialogue_profile_resolved", ""))
		if d.get("meta") is Dictionary else ""
	)
	var reply := str(d.get("reply", "")).strip_edges()
	var ok := bool(d.get("ok", response_code >= 200 and response_code < 300)) and not reply.is_empty()
	if not ok and d.has("detail"):
		meta["detail"] = d.get("detail")
	reply_ready.emit(ok, reply, meta)
