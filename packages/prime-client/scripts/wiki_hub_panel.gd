extends PanelContainer
class_name WikiHubPanel
## C6 — wiki hub Lost Heaven (GET /v1/wiki).

const HubRuntimeCfg = preload("res://scripts/hub_runtime_cfg.gd")
const SIDECAR_DEFAULT := "http://192.168.0.246:8787"

@export var sidecar_base_url: String = SIDECAR_DEFAULT
@export var panel_visible: bool = false

var _title: Label
var _status: Label
var _body: RichTextLabel
var _refresh_btn: Button
var _close_btn: Button
var _http: HTTPRequest


func _ready() -> void:
	visible = panel_visible
	mouse_filter = Control.MOUSE_FILTER_IGNORE if not panel_visible else Control.MOUSE_FILTER_STOP
	_apply_hub_runtime()
	_apply_style()
	_ensure_ui()
	_http = HTTPRequest.new()
	add_child(_http)
	_http.request_completed.connect(_on_http_done)
	set_anchors_preset(Control.PRESET_CENTER)
	custom_minimum_size = Vector2(520, 420)
	offset_left = -260
	offset_top = -220
	offset_right = 260
	offset_bottom = 220


func _apply_hub_runtime() -> void:
	if HubRuntimeCfg.enabled():
		sidecar_base_url = HubRuntimeCfg.http_url(sidecar_base_url)


func toggle() -> void:
	panel_visible = not panel_visible
	visible = panel_visible
	mouse_filter = Control.MOUSE_FILTER_STOP if panel_visible else Control.MOUSE_FILTER_IGNORE
	if panel_visible:
		_apply_hub_runtime()
		refresh()


func refresh() -> void:
	_status.text = "fetch…"
	_apply_hub_runtime()
	var url := sidecar_base_url.rstrip("/") + "/v1/wiki"
	if _http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		_http.cancel_request()
	var err := _http.request(url, [], HTTPClient.METHOD_GET)
	if err != OK:
		_status.text = "req_%d" % err
		_body.text = "(hors ligne — wiki local indisponible)"


func _apply_style() -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.06, 0.055, 0.05, 0.96)
	sb.set_border_width_all(2)
	sb.border_color = Color(0.45, 0.72, 0.62, 0.95)
	sb.set_corner_radius_all(5)
	sb.content_margin_left = 12
	sb.content_margin_top = 10
	sb.content_margin_right = 12
	sb.content_margin_bottom = 12
	sb.shadow_color = Color(0, 0, 0, 0.45)
	sb.shadow_size = 8
	add_theme_stylebox_override("panel", sb)


func _ensure_ui() -> void:
	var root := get_node_or_null("VBox") as VBoxContainer
	if root == null:
		root = VBoxContainer.new()
		root.name = "VBox"
		root.add_theme_constant_override("separation", 6)
		add_child(root)
	var head := root.get_node_or_null("Header") as HBoxContainer
	if head == null:
		head = HBoxContainer.new()
		head.name = "Header"
		root.add_child(head)
	_title = head.get_node_or_null("Title") as Label
	if _title == null:
		_title = Label.new()
		_title.name = "Title"
		_title.text = "Wiki hub — Lost Heaven"
		_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		head.add_child(_title)
	_refresh_btn = head.get_node_or_null("Refresh") as Button
	if _refresh_btn == null:
		_refresh_btn = Button.new()
		_refresh_btn.name = "Refresh"
		_refresh_btn.text = "Rafraîchir"
		head.add_child(_refresh_btn)
	_close_btn = head.get_node_or_null("Close") as Button
	if _close_btn == null:
		_close_btn = Button.new()
		_close_btn.name = "Close"
		_close_btn.text = "Fermer"
		head.add_child(_close_btn)
	if not _refresh_btn.pressed.is_connected(refresh):
		_refresh_btn.pressed.connect(refresh)
	if not _close_btn.pressed.is_connected(toggle):
		_close_btn.pressed.connect(toggle)
	_status = root.get_node_or_null("Status") as Label
	if _status == null:
		_status = Label.new()
		_status.name = "Status"
		_status.add_theme_font_size_override("font_size", 11)
		root.add_child(_status)
	_body = root.get_node_or_null("Body") as RichTextLabel
	if _body == null:
		_body = RichTextLabel.new()
		_body.name = "Body"
		_body.bbcode_enabled = true
		_body.fit_content = false
		_body.scroll_active = true
		_body.size_flags_vertical = Control.SIZE_EXPAND_FILL
		_body.custom_minimum_size = Vector2(0, 320)
		root.add_child(_body)


func _on_http_done(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS or code < 200 or code >= 300:
		_status.text = "hors ligne (%s)" % str(code)
		_body.text = "Impossible de charger /v1/wiki"
		return
	var parsed = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) != TYPE_DICTIONARY:
		_status.text = "parse error"
		return
	var drift = parsed.get("drift", {})
	var drift_ok := bool(drift.get("ok", false)) if typeof(drift) == TYPE_DICTIONARY else false
	_status.text = "live — PNJ %s · POI %s · M10 %s%s" % [
		str(drift.get("npc_count", "?")),
		str(drift.get("poi_count", "?")),
		str(drift.get("profession_count", "?")),
		" · drift OK" if drift_ok else " · DRIFT",
	]
	_title.text = str(parsed.get("title", "Wiki hub — Lost Heaven"))
	var md := str(parsed.get("markdown", ""))
	_body.clear()
	_body.append_text(_md_to_bbcode(md))


func _md_to_bbcode(md: String) -> String:
	var out: PackedStringArray = PackedStringArray()
	for line in md.split("\n"):
		var s := str(line)
		if s.begins_with("# "):
			out.append("[b][font_size=18]%s[/font_size][/b]" % s.substr(2))
		elif s.begins_with("## "):
			out.append("[b][color=#8fd4b8]%s[/color][/b]" % s.substr(3))
		elif s.begins_with("> "):
			out.append("[i][color=#b8b0a0]%s[/color][/i]" % s.substr(2))
		elif s.begins_with("|"):
			out.append("[color=#c8c0b0]%s[/color]" % s)
		elif s.begins_with("- "):
			out.append("• %s" % s.substr(2).replace("**", ""))
		else:
			out.append(s.replace("**", "").replace("`", ""))
	return "\n".join(out)
