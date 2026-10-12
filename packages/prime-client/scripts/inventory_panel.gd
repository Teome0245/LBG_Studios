# inventory_panel.gd — Inventaire grille (hub :8787 peel natif)
extends PanelContainer
class_name InventoryPanel
const _UiIconRegistry = preload("res://scripts/ui_icon_registry.gd")

const SIDECAR_DEFAULT := "http://192.168.0.246:8787"
const PLAYER_DEFAULT := "local"

@export var sidecar_base_url: String = SIDECAR_DEFAULT
@export var player_id: String = PLAYER_DEFAULT
@export var panel_visible: bool = false
@export var columns: int = 5
@export var rows: int = 4
@export var slot_px: float = 52.0

var _grid: GridContainer
var _title: Label
var _hint: Label
var _weight: Label
var _http: HTTPRequest
var _items: Array = []

const STUB_ITEMS: Array[Dictionary] = [
	{"id": "scrap_metal", "name": "Ferraille", "icon": "copper", "qty": 4},
	{"id": "binding_tape", "name": "Ruban de liaison", "icon": "screw", "qty": 2},
	{"id": "dried_grain", "name": "Grain séché", "icon": "ration", "qty": 4},
	{"id": "water_capsule", "name": "Capsule d'eau", "icon": "kit", "qty": 2},
]

func _ready() -> void:
	visible = panel_visible
	mouse_filter = Control.MOUSE_FILTER_IGNORE if not panel_visible else Control.MOUSE_FILTER_STOP
	_apply_hub_runtime_sidecar()
	_apply_modal_style()
	_ensure_ui()
	_http = HTTPRequest.new()
	add_child(_http)
	_http.request_completed.connect(_on_http_done)
	_fill_from_items(STUB_ITEMS)
	call_deferred("refresh_inventory")


func _apply_hub_runtime_sidecar() -> void:
	if not HubRuntimeCfg.enabled():
		return
	sidecar_base_url = HubRuntimeCfg.http_url(sidecar_base_url)
	player_id = HubRuntimeCfg.player_name("Voyageur")


func toggle() -> void:
	panel_visible = not panel_visible
	visible = panel_visible
	mouse_filter = Control.MOUSE_FILTER_STOP if panel_visible else Control.MOUSE_FILTER_IGNORE
	if panel_visible:
		_apply_hub_runtime_sidecar()
		refresh_inventory()

func _apply_modal_style() -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.06, 0.055, 0.05, 0.94)
	sb.set_border_width_all(2)
	sb.border_color = Color(0.78, 0.52, 0.28, 0.95)
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
		add_child(root)
	root.add_theme_constant_override("separation", 8)

	var head := root.get_node_or_null("Header") as HBoxContainer
	if head == null:
		head = HBoxContainer.new()
		head.name = "Header"
		root.add_child(head)
		root.move_child(head, 0)

	var old_title := root.get_node_or_null("Title") as Label
	if old_title and old_title.get_parent() == root:
		old_title.reparent(head)

	_title = head.get_node_or_null("Title") as Label
	if _title == null:
		_title = Label.new()
		_title.name = "Title"
		_title.text = "Inventaire"
		head.add_child(_title)
	_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_title.add_theme_font_size_override("font_size", 15)

	_weight = head.get_node_or_null("Weight") as Label
	if _weight == null:
		_weight = Label.new()
		_weight.name = "Weight"
		_weight.text = "— / 40"
		_weight.add_theme_font_size_override("font_size", 11)
		_weight.add_theme_color_override("font_color", Color(0.7, 0.75, 0.7, 0.9))
		head.add_child(_weight)

	_hint = root.get_node_or_null("Hint") as Label
	if _hint == null:
		_hint = Label.new()
		_hint.name = "Hint"
		root.add_child(_hint)
	_hint.text = "I fermer · sync M10 inventaire"
	_hint.add_theme_font_size_override("font_size", 10)
	_hint.add_theme_color_override("font_color", Color(0.65, 0.6, 0.52, 0.85))

	_grid = root.get_node_or_null("Grid") as GridContainer
	if _grid == null:
		_grid = GridContainer.new()
		_grid.name = "Grid"
		root.add_child(_grid)
	_grid.columns = columns
	_grid.add_theme_constant_override("h_separation", 5)
	_grid.add_theme_constant_override("v_separation", 5)
	_grid.size_flags_horizontal = Control.SIZE_SHRINK_CENTER

func set_items(items: Array) -> void:
	_fill_from_items(items)

func apply_craft_result(result: Dictionary) -> void:
	if typeof(result.get("inventory")) == TYPE_ARRAY:
		_fill_from_items(result.get("inventory"))
		var crafted = result.get("crafted", {})
		if typeof(crafted) == TYPE_DICTIONARY and _hint:
			_hint.text = "Craft OK — %s ×%d" % [
				str(crafted.get("name", crafted.get("id", "?"))),
				int(crafted.get("qty", 1)),
			]
	else:
		refresh_inventory()

func refresh_inventory() -> void:
	var url := "%s/v1/inventory?player=%s" % [sidecar_base_url.rstrip("/"), player_id.uri_encode()]
	if _http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		_http.cancel_request()
	var err := _http.request(url, [], HTTPClient.METHOD_GET)
	if err != OK and _hint:
		_hint.text = "inventaire hors ligne (stub local)"

func _on_http_done(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS or code < 200 or code >= 300:
		if _hint:
			_hint.text = "inventaire hors ligne (%s) · stub" % str(code)
		return
	var parsed = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) != TYPE_DICTIONARY:
		return
	var inv = parsed.get("inventory", [])
	if typeof(inv) == TYPE_ARRAY:
		_fill_from_items(inv)
		if _hint:
			var src := str(parsed.get("source", "m10"))
			if bool(parsed.get("core3_live", false)):
				_hint.text = "I fermer · Core3 live (%d stacks)" % inv.size()
			else:
				_hint.text = "I fermer · sync %s (%d stacks)" % [src, inv.size()]

func _fill_from_items(items: Array) -> void:
	_items = items.duplicate()
	if _grid == null:
		return
	for c in _grid.get_children():
		c.queue_free()
	var total := columns * rows
	var used := 0
	for i in range(total):
		var item: Dictionary = {}
		if i < _items.size() and typeof(_items[i]) == TYPE_DICTIONARY:
			item = _items[i]
		var slot := Button.new()
		slot.custom_minimum_size = Vector2(slot_px, slot_px)
		slot.focus_mode = Control.FOCUS_NONE
		slot.theme_type_variation = &"HotbarSlot"
		slot.text = ""
		slot.expand_icon = true
		slot.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
		if item.is_empty() or int(item.get("qty", 0)) <= 0:
			slot.icon = _UiIconRegistry.tex("empty")
			slot.disabled = true
			slot.tooltip_text = "Vide"
		else:
			used += 1
			var icon_key := str(item.get("icon", _UiIconRegistry.item_icon(str(item.get("name", "")))))
			slot.icon = _UiIconRegistry.tex(icon_key)
			var qty := int(item.get("qty", 1))
			var item_name := str(item.get("name", item.get("id", "")))
			slot.tooltip_text = "%s ×%d" % [item_name, qty]
			slot.disabled = false
			var slot_idx := i
			slot.pressed.connect(func() -> void: _on_item_slot(slot_idx, item_name, qty))
			if qty > 1:
				var qty_lbl := Label.new()
				qty_lbl.text = "×%d" % qty
				qty_lbl.mouse_filter = Control.MOUSE_FILTER_IGNORE
				qty_lbl.add_theme_font_size_override("font_size", 10)
				qty_lbl.add_theme_color_override("font_color", Color(0.95, 0.88, 0.7, 1))
				qty_lbl.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
				qty_lbl.offset_left = -28.0
				qty_lbl.offset_top = -16.0
				qty_lbl.offset_right = -3.0
				qty_lbl.offset_bottom = -2.0
				slot.add_child(qty_lbl)
		_grid.add_child(slot)
	if _weight:
		_weight.text = "%d / %d" % [used, total]

func _on_item_slot(_index: int, item_name: String, qty: int) -> void:
	if _hint:
		_hint.text = "%s ×%d" % [item_name, qty]
