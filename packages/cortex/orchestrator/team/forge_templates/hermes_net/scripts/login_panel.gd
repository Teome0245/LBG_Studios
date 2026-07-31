extends Control
## LoginPanel — écran connexion compte LBG (M11). Branche LbgAuthClient.

signal enter_world_requested(ws_url: String, character_id: int, session_token: String)

@onready var _user: LineEdit = %Username
@onready var _pass: LineEdit = %Password
@onready var _char_list: ItemList = %CharacterList
@onready var _status: Label = %StatusLabel
@onready var _btn_login: Button = %LoginButton
@onready var _btn_enter: Button = %EnterButton

var _auth: Node = null
var _chars: Array = []


func _ready() -> void:
	_btn_enter.disabled = true
	_btn_login.pressed.connect(_on_login_pressed)
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


func get_session_token() -> String:
	if _auth and "session_token" in _auth:
		return str(_auth.session_token)
	return ""


func _on_login_pressed() -> void:
	_status.text = "Connexion…"
	_btn_login.disabled = true
	_auth.login(_user.text, _pass.text)


func _on_login_ok(_session_token: String, characters: Array) -> void:
	_btn_login.disabled = false
	_chars = characters
	_char_list.clear()
	for c in characters:
		var label := str(c.get("name", c.get("id", "?")))
		_char_list.add_item(label)
	_status.text = "OK — choisis un perso"
	if _char_list.item_count > 0:
		_char_list.select(0)
		_btn_enter.disabled = false


func _on_login_failed(code: String, message: String) -> void:
	_btn_login.disabled = false
	_status.text = "%s: %s" % [code, message]


func _on_enter_pressed() -> void:
	var idx := _char_list.get_selected_items()
	if idx.is_empty():
		_status.text = "Sélectionne un personnage"
		return
	var c: Dictionary = _chars[idx[0]]
	var cid := int(c.get("id", 0))
	_status.text = "Select character…"
	_auth.select_character(cid)


func _on_select_ok(_character_id: int, _ws_url: String) -> void:
	_status.text = "Enter zone…"
	_auth.enter_zone("tatooine")


func _on_select_failed(code: String, message: String) -> void:
	_status.text = "%s: %s" % [code, message]


func _on_enter_zone_ok(ws_url: String, your_character_id: int) -> void:
	_status.text = "En zone — WS…"
	var token := get_session_token()
	enter_world_requested.emit(ws_url, your_character_id, token)


func _on_enter_zone_failed(code: String, message: String) -> void:
	_status.text = "%s: %s" % [code, message]
