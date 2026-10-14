# inventory_panel.gd — Inventaire grille (hub :8787 peel natif)
extends PanelContainer
class_name InventoryPanel
const _UiIconRegistry = preload("res://scripts/ui_icon_registry.gd")
const HubRuntimeCfg = preload("res://scripts/hub_runtime_cfg.gd")

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
			var line := "Craft OK — %s ×%d" % [
				str(crafted.get("name", crafted.get("id", "?"))),
				int(crafted.get("qty", 1)),
			]
			var cost = result.get("cost", {})
			if typeof(cost) == TYPE_DICTIONARY:
				var summary := str(cost.get("summary", "")).strip_edges()
				if summary != "":
					line = "%s · coût %s" % [line, summary]
			_hint.text = line
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

class InventorySlotBtn extends Button:
	var slot_index: int = -1
	var item_data: Dictionary = {}
	var panel: InventoryPanel = null

	func _get_drag_data(_at_position: Vector2) -> Variant:
		if item_data.is_empty() or int(item_data.get("qty", 0)) <= 0:
			return null
		var preview_box := Control.new()
		var preview := TextureRect.new()
		preview.texture = icon
		preview.custom_minimum_size = Vector2(40, 40)
		preview.size = Vector2(40, 40)
		preview.position = -Vector2(20, 20)
		preview.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		preview.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		preview.modulate = Color(1.0, 1.0, 1.0, 0.85)
		preview_box.add_child(preview)
		if is_inside_tree():
			set_drag_preview(preview_box)
		return {
			"type": "inventory_slot",
			"from_index": slot_index,
			"item": item_data
		}

	func _can_drop_data(_at_position: Vector2, data: Variant) -> bool:
		if typeof(data) != TYPE_DICTIONARY:
			return false
		if data.get("type") != "inventory_slot":
			return false
		return int(data.get("from_index", -1)) != slot_index

	func _drop_data(_at_position: Vector2, data: Variant) -> void:
		if typeof(data) == TYPE_DICTIONARY and data.get("type") == "inventory_slot":
			var from_idx: int = int(data.get("from_index", -1))
			if from_idx >= 0 and from_idx != slot_index and panel != null:
				panel.swap_or_move_slots(from_idx, slot_index)

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
		var slot := InventorySlotBtn.new()
		slot.slot_index = i
		slot.item_data = item
		slot.panel = self
		slot.custom_minimum_size = Vector2(slot_px, slot_px)
		slot.focus_mode = Control.FOCUS_NONE
		slot.theme_type_variation = &"HotbarSlot"
		slot.text = ""
		slot.expand_icon = true
		slot.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
		if item.is_empty() or int(item.get("qty", 0)) <= 0:
			slot.icon = _UiIconRegistry.tex("empty")
			slot.disabled = false
			slot.tooltip_text = "Vide (glisser un objet ici)"
		else:
			used += 1
			var icon_key := str(item.get("icon", _UiIconRegistry.item_icon(str(item.get("name", "")))))
			slot.icon = _UiIconRegistry.tex(icon_key)
			var qty := int(item.get("qty", 1))
			var item_name := str(item.get("name", item.get("id", "")))
			slot.tooltip_text = "%s ×%d (glisser pour déplacer · clic pour utiliser)" % [item_name, qty]
			slot.disabled = false
			var slot_idx := i
			var item_id := str(item.get("id", ""))
			slot.pressed.connect(func() -> void: _on_item_slot(slot_idx, item_name, qty, item_id))
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

func swap_or_move_slots(from_idx: int, to_idx: int) -> void:
	var total := columns * rows
	while _items.size() < total:
		_items.append({})
	if from_idx < 0 or from_idx >= _items.size() or to_idx < 0 or to_idx >= _items.size():
		return
	if from_idx == to_idx:
		return
	var item_from: Dictionary = _items[from_idx]
	if item_from.is_empty():
		return
	var item_to: Dictionary = _items[to_idx]
	var from_name := str(item_from.get("name", item_from.get("id", "Objet")))

	if not item_to.is_empty() and str(item_to.get("id", "")) == str(item_from.get("id", "")) and item_from.get("id") != "":
		var new_qty := int(item_to.get("qty", 0)) + int(item_from.get("qty", 0))
		item_to["qty"] = new_qty
		_items[to_idx] = item_to
		_items[from_idx] = {}
		if _hint:
			_hint.text = "Empilé : %s (total ×%d)" % [from_name, new_qty]
	else:
		_items[to_idx] = item_from
		_items[from_idx] = item_to
		if _hint:
			if item_to.is_empty():
				_hint.text = "Déplacé : %s (slot %d → %d)" % [from_name, from_idx + 1, to_idx + 1]
			else:
				var to_name := str(item_to.get("name", item_to.get("id", "Objet")))
				_hint.text = "Permuté : %s ↔ %s" % [from_name, to_name]

	_fill_from_items(_items)

func _on_item_slot(_index: int, item_name: String, qty: int, item_id: String = "") -> void:
	if _hint:
		_hint.text = "%s ×%d — clic = utiliser si consommable" % [item_name, qty]
	var ops = null
	var n: Node = self
	while n != null:
		if n.get("gameplay_ops") != null:
			ops = n.get("gameplay_ops")
			break
		n = n.get_parent()
	if ops != null and ops.has_method("try_use_item"):
		ops.try_use_item(item_id)
