extends Node
## LbgCharacterClient — création de personnage via Cortex POST /v1/characters

signal create_ok(result: Dictionary)
signal create_failed(code: String, message: String)

const CONFIG_PATH := "res://config/character_creation.json"

@export var cortex_http_base: String = "http://192.168.0.140:8000"
@export var use_mock_fallback: bool = true
@export var account_id: String = "default"

var _http: HTTPRequest
var _mock_seq: int = 9000
var _pending_payload: Dictionary = {}


func _ready() -> void:
	_load_config()
	_http = HTTPRequest.new()
	_http.name = "CharacterHTTP"
	add_child(_http)
	_http.request_completed.connect(_on_http_completed)


func _load_config() -> void:
	if not FileAccess.file_exists(CONFIG_PATH):
		return
	var raw: Variant = JSON.parse_string(FileAccess.get_file_as_string(CONFIG_PATH))
	if raw is Dictionary:
		var base := str((raw as Dictionary).get("cortex_http_base", "")).strip_edges()
		if not base.is_empty():
			cortex_http_base = base
		if "use_mock_fallback" in raw:
			use_mock_fallback = bool(raw.get("use_mock_fallback"))


func create_character(payload: Dictionary) -> void:
	_pending_payload = payload.duplicate(true)
	# V1 : cristallisation locale immédiate. Cortex (.140) est best-effort, jamais bloquant.
	if use_mock_fallback:
		_mock_create(_pending_payload)
		_try_http_best_effort()
		return
	_try_http_best_effort()


func _try_http_best_effort() -> void:
	if _http == null:
		return
	var body := JSON.stringify(_pending_payload)
	var headers := [
		"Content-Type: application/json",
		"X-Account-Id: %s" % account_id,
	]
	var err := _http.request(
		cortex_http_base.rstrip("/") + "/v1/characters",
		headers,
		HTTPClient.METHOD_POST,
		body
	)
	if err != OK and not use_mock_fallback:
		create_failed.emit("zone_unavailable", "HTTPRequest error %s" % err)


func _mock_create(payload: Dictionary) -> void:
	_mock_seq += 1
	var mode := str(payload.get("mode", "chaos"))
	var customization: Dictionary = payload.get("customization", {})
	var name := str(customization.get("name", "Amas"))
	var archetype := str(payload.get("archetype", "traqueur"))
	var race := "race:human"
	var race_display := "Humain"
	if mode == "empreinte":
		race = "race:fel_rani"
		race_display = "Fel'Rani"
		archetype = "soigneur"
	var cid := "chr_mock_%04d" % _mock_seq
	create_ok.emit({
		"character_id": cid,
		"name": name,
		"race": race,
		"race_display": race_display,
		"archetype_starter": archetype,
		"stats": {
			"force": 55, "agilite": 60, "intelligence": 50,
			"hp": 100, "endurance": 55, "esprit": 45,
		},
		"origin": {"mode": mode, "amas_location": "champ_des_amas_est"},
		"is_ai": bool(payload.get("is_ai", false)),
		"lore_brief": "L'Amas pulse en mode démo — Cortex indisponible.",
		"noyau_id": "noyau_mock_%04d" % (_mock_seq / 10),
		"particule_seed": "%08x" % (_mock_seq * 9973),
		"_mock_numeric_id": _mock_seq,
	})


func _finish_unavailable(reason: String) -> void:
	if use_mock_fallback:
		# Déjà cristallisé en local — ne pas spammer l'UI.
		print("[LbgCharacterClient] Cortex KO (%s) — ignoré (mock déjà OK)" % reason)
		return
	create_failed.emit("zone_unavailable", reason)


func _on_http_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if use_mock_fallback:
		# L'UI a déjà le perso local ; une réponse Cortex 4xx ne doit pas l'annuler.
		if result != HTTPRequest.RESULT_SUCCESS:
			print("[LbgCharacterClient] Cortex réseau (%s) — mock déjà OK" % result)
		return
	var text := body.get_string_from_utf8()
	var data: Variant = JSON.parse_string(text)
	if typeof(data) != TYPE_DICTIONARY:
		data = {}
	var d: Dictionary = data

	if result != HTTPRequest.RESULT_SUCCESS:
		_finish_unavailable("réseau (%s)" % result)
		return

	if response_code >= 400:
		var detail := str(d.get("detail", "erreur création"))
		var code := "create_failed"
		if response_code == 409:
			code = "name_taken"
		elif response_code == 403:
			code = "max_characters"
		elif response_code == 404:
			code = "pnj_unknown"
		create_failed.emit(code, detail)
		return

	create_ok.emit(d)
