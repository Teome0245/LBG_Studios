# dialogue_bridge.gd — Rang 2 : session_summary → persona MMO via Pilot (ADR 0004)
# Chemin court sans legacy /mmo/ : Godot → POST /v1/pilot/agent-dialogue/invoke
extends Node
class_name DialogueBridge

signal reply_ready(ok: bool, reply: String, meta: Dictionary)
signal busy_changed(busy: bool)

const CONFIG_PATH := "res://config/dialogue_bridge.json"
const MAP_CFG_PATH := "res://assets/maps/scrapaltai_map_config.json"
const SESSION_PATH := "user://session_summary.json"
const HISTORY_PATH := "user://dialogue_history.json"
const SESSION_KEYS: Array[String] = [
	"tracked_quest",
	"last_npc",
	"player_note",
	"session_mood",
	"quest_snapshot",
	"memory_hint",
]
const MAX_HISTORY := 12

var _http: HTTPRequest
var _busy: bool = false
var _cfg: Dictionary = {}
var _session: Dictionary = {}
var _req_id: int = 0
var _history: Array = []
var _history_npc_id: String = ""
var _pending_player_text: String = ""
var _pending_npc_name: String = ""

func _ready() -> void:
	_http = HTTPRequest.new()
	_http.timeout = 60.0
	add_child(_http)
	_http.request_completed.connect(_on_http_done)
	_load_config()
	_load_session()
	_load_history()


func is_enabled() -> bool:
	return bool(_cfg.get("enabled", true))


func is_busy() -> bool:
	return _busy


func get_session_summary() -> Dictionary:
	return _session.duplicate(true)


func get_history_for_npc(world_npc_id: String) -> Array:
	if world_npc_id != _history_npc_id:
		return []
	return _history.duplicate(true)


func clear_history() -> void:
	_history.clear()
	_history_npc_id = ""
	_save_history()


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
	update_session({"last_npc": npc_name})
	if not world_npc_id.is_empty():
		_session["_last_world_npc_id"] = world_npc_id
		_save_session()
		if world_npc_id != _history_npc_id:
			_history.clear()
			_history_npc_id = world_npc_id
			_save_history()


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
	# Texte vide = ouverture / relance (greeting) ; les tours suivants passent le texte joueur.
	# L'historique part dans context.history pour la cohérence multi-tours.
	if text.is_empty():
		text = str(_cfg.get("greeting_text", "Bonjour."))
	if world_npc_id != _history_npc_id:
		_history.clear()
		_history_npc_id = world_npc_id
	var ss := _sanitize_session_for_wire()
	if not npc_name.is_empty():
		ss["last_npc"] = npc_name
	var world := _world_context_for_wire()
	var context := {
		"world_npc_id": world_npc_id,
		"npc_name": npc_name,
		"lyra_engagement": "mmo_persona",
		"_skip_factual_status": true,
		"session_summary": ss,
		"planet_display": str(world.get("planet_display", "Scrapaltai")),
		"hub_city": str(world.get("hub_city", "Lost Heaven")),
		"scene": str(world.get("scene", "Lost Heaven")),
		"world_hint": str(world.get("world_hint", "")),
		"history": _history_for_wire(),
	}
	var body := {
		"actor_id": actor_id,
		"text": text,
		"context": context,
	}
	_pending_player_text = text
	_pending_npc_name = npc_name
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
		_pending_player_text = ""
		reply_ready.emit(false, "", {"error": "http_request_failed", "code": err, "req_id": my_id})
		return false
	return true


func _history_for_wire() -> Array:
	var out: Array = []
	for item in _history:
		if not item is Dictionary:
			continue
		var role := str((item as Dictionary).get("role", "")).strip_edges()
		var content := str((item as Dictionary).get("content", "")).strip_edges()
		if role.is_empty() or content.is_empty():
			continue
		if content.length() > 500:
			content = content.substr(0, 500)
		out.append({"role": role, "content": content})
	return out


func _append_turn(player_text: String, assistant_text: String) -> void:
	if not player_text.strip_edges().is_empty():
		_history.append({"role": "user", "content": player_text.strip_edges()})
	if not assistant_text.strip_edges().is_empty():
		_history.append({"role": "assistant", "content": assistant_text.strip_edges()})
	while _history.size() > MAX_HISTORY:
		_history.pop_front()
	_save_history()
	# session_summary : ce que le JOUEUR a dit (pas le blabla PNJ — sinon le rappel se perroquette).
	var patch := {"last_npc": _pending_npc_name}
	var said := player_text.strip_edges()
	var low := said.to_lower()
	var greet := low.is_empty() or low in ["bonjour", "bonjour.", "salut", "hello", "hey"] or low.begins_with("bonjour")
	if not said.is_empty() and not greet:
		if said.length() > 80:
			said = said.substr(0, 77) + "…"
		patch["player_note"] = said
	update_session(patch)


func _world_context_for_wire() -> Dictionary:
	var planet := str(_cfg.get("planet_display", "Scrapaltai")).strip_edges()
	var hub := str(_cfg.get("hub_city", "Lost Heaven")).strip_edges()
	if FileAccess.file_exists(MAP_CFG_PATH):
		var f := FileAccess.open(MAP_CFG_PATH, FileAccess.READ)
		var raw: Variant = JSON.parse_string(f.get_as_text())
		f.close()
		if raw is Dictionary:
			var d: Dictionary = raw
			var dn := str(d.get("display_name", "")).strip_edges()
			var hc := str(d.get("hub_city", "")).strip_edges()
			if not dn.is_empty():
				planet = dn
			if not hc.is_empty():
				hub = hc
	if planet.is_empty():
		planet = "Scrapaltai"
	if hub.is_empty():
		hub = "Lost Heaven"
	var hint := str(_cfg.get("world_hint", "")).strip_edges()
	if hint.is_empty():
		hint = (
			"Planète %s, ville hub %s — avant-poste désertique (bazar, shuttleport, quartiers). "
			+ "Ne jamais inventer d'autre nom de ville ou de planète."
		) % [planet, hub]
	return {
		"planet_display": planet,
		"hub_city": hub,
		"scene": "%s (%s)" % [hub, planet],
		"world_hint": hint,
	}


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
		"greeting_text": "Bonjour — parle-moi de Lost Heaven et de Scrapaltai.",
		"followup_placeholder": "Répondre au PNJ…",
	}
	if not FileAccess.file_exists(CONFIG_PATH):
		_apply_hub_runtime_override()
		var t0 := float(_cfg.get("timeout_sec", 60))
		_http.timeout = maxf(10.0, t0)
		return
	var f := FileAccess.open(CONFIG_PATH, FileAccess.READ)
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if raw is Dictionary:
		for k in (raw as Dictionary).keys():
			_cfg[k] = (raw as Dictionary)[k]
	_apply_hub_runtime_override()
	var t := float(_cfg.get("timeout_sec", 60))
	_http.timeout = maxf(10.0, t)


func _apply_hub_runtime_override() -> void:
	## Spike ADR 0026 : dialogue → hub_runtime sur .246 (pas Pilot 140 / 8020).
	const hub_path := "res://config/hub_runtime.json"
	if not FileAccess.file_exists(hub_path):
		return
	var hf := FileAccess.open(hub_path, FileAccess.READ)
	if hf == null:
		return
	var raw: Variant = JSON.parse_string(hf.get_as_text())
	hf.close()
	if not raw is Dictionary:
		return
	var hub: Dictionary = raw
	if not bool(hub.get("enabled", false)):
		return
	var http_url := str(hub.get("http_url", "")).strip_edges().rstrip("/")
	if http_url.is_empty():
		http_url = "http://192.168.0.246:8787"
	_cfg["pilot_base_url"] = http_url
	_cfg["invoke_path"] = "/v1/dialogue/invoke"
	_cfg["timeout_sec"] = minf(float(_cfg.get("timeout_sec", 60)), 20.0)
	_cfg["enabled"] = true
	print("[DialogueBridge] hub_runtime → %s%s" % [http_url, _cfg["invoke_path"]])


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
	if _session.has("_last_world_npc_id"):
		wire["_last_world_npc_id"] = _session["_last_world_npc_id"]
	var f := FileAccess.open(SESSION_PATH, FileAccess.WRITE)
	if f == null:
		return
	f.store_string(JSON.stringify(wire))
	f.close()


func _load_history() -> void:
	_history = []
	_history_npc_id = ""
	if not FileAccess.file_exists(HISTORY_PATH):
		return
	var f := FileAccess.open(HISTORY_PATH, FileAccess.READ)
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if not raw is Dictionary:
		return
	var d: Dictionary = raw
	_history_npc_id = str(d.get("npc_id", ""))
	var arr: Variant = d.get("turns", [])
	if arr is Array:
		_history = (arr as Array).duplicate(true)


func _save_history() -> void:
	var f := FileAccess.open(HISTORY_PATH, FileAccess.WRITE)
	if f == null:
		return
	f.store_string(JSON.stringify({"npc_id": _history_npc_id, "turns": _history_for_wire()}))
	f.close()


func _on_http_done(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	_busy = false
	busy_changed.emit(false)
	var meta := {"http_result": result, "status": response_code}
	if result != HTTPRequest.RESULT_SUCCESS:
		_pending_player_text = ""
		reply_ready.emit(false, "", meta)
		return
	var text := body.get_string_from_utf8()
	var raw: Variant = JSON.parse_string(text)
	if not raw is Dictionary:
		meta["error"] = "invalid_json"
		_pending_player_text = ""
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
	# C1 — suggested_moves (0–3) depuis l’agent ; absent = []
	var moves_raw: Variant = d.get("suggested_moves", [])
	var moves_out: Array = []
	var max_moves := int(_cfg.get("max_suggested_moves", 3))
	max_moves = clampi(max_moves, 0, 3)
	if moves_raw is Array:
		for item in moves_raw:
			if moves_out.size() >= max_moves:
				break
			if not item is Dictionary:
				continue
			var m: Dictionary = item
			var mid := str(m.get("id", "")).strip_edges()
			var label := str(m.get("label", "")).strip_edges()
			if mid.is_empty() or label.is_empty():
				continue
			if label.length() > 28:
				label = label.substr(0, 28)
			var utterance := str(m.get("utterance", label)).strip_edges()
			if utterance.is_empty():
				utterance = label
			if utterance.length() > 160:
				utterance = utterance.substr(0, 160)
			var move := {"id": mid, "label": label, "utterance": utterance}
			var kind := str(m.get("kind", "")).strip_edges()
			if not kind.is_empty():
				move["kind"] = kind
			if m.get("action") is Dictionary:
				move["action"] = (m.get("action") as Dictionary).duplicate(true)
			moves_out.append(move)
	meta["suggested_moves"] = moves_out
	if d.get("meta") is Dictionary:
		var src := str((d.get("meta") as Dictionary).get("suggested_moves_source", "")).strip_edges()
		if not src.is_empty():
			meta["suggested_moves_source"] = src
	if ok:
		_append_turn(_pending_player_text, reply)
		meta["history_turns"] = _history.size()
	_pending_player_text = ""
	reply_ready.emit(ok, reply, meta)
