# hotbar.gd — Barre d'actions SWG Pre-CU en Haut-Centre (3 blocs de 4 cases F1..F12 / 1..0, style Holo-Teal)
extends PanelContainer
class_name Hotbar
const _UiIconRegistry = preload("res://scripts/ui_icon_registry.gd")

signal slot_activated(index: int)
signal item_assigned(slot_index: int, item_data: Dictionary)

@export var slot_count: int = 12
@export var slot_size: Vector2 = Vector2(36, 36)

var _slots: Array[Button] = []
var _tooltips: PackedStringArray = PackedStringArray([
	"Récupération / Combat",
	"Assemblage rapide",
	"Objet rapide",
	"Attitude / Emote",
	"Carte planétaire [M]",
	"Arbres de Compétences [K]",
	"Inventaire [I]",
	"Canal Spatial [Entrée]",
	"Escorte Compagnon",
	"Outil de Prospection [U]",
	"Atelier Expérimentation [X]",
	"Menu Système [Échap]"
])
var _active_index: int = -1

class HotbarSlotBtn extends Button:
	var slot_index: int = -1
	var hotbar: Hotbar = null

	func _can_drop_data(_at_position: Vector2, data: Variant) -> bool:
		if typeof(data) != TYPE_DICTIONARY:
			return false
		return data.get("type") == "inventory_slot"

	func _drop_data(_at_position: Vector2, data: Variant) -> void:
		if typeof(data) == TYPE_DICTIONARY and data.get("type") == "inventory_slot":
			var item: Dictionary = data.get("item", {})
			if hotbar != null:
				hotbar.assign_item_to_slot(slot_index, item)

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	_apply_swg_toolbar_frame()
	_build_slots()

func _apply_swg_toolbar_frame() -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.015, 0.09, 0.12, 0.86)
	sb.set_border_width_all(1)
	sb.border_color = Color(0.24, 0.82, 0.92, 0.88)
	sb.set_corner_radius_all(4)
	sb.content_margin_left = 8
	sb.content_margin_right = 8
	sb.content_margin_top = 4
	sb.content_margin_bottom = 14
	add_theme_stylebox_override("panel", sb)

func _make_slot_style(hover: bool = false, active: bool = false) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	if active:
		sb.bg_color = Color(0.10, 0.42, 0.48, 0.96)
		sb.border_color = Color(0.98, 0.86, 0.32, 1.0)
	elif hover:
		sb.bg_color = Color(0.06, 0.30, 0.36, 0.95)
		sb.border_color = Color(0.55, 0.96, 1.0, 0.98)
	else:
		sb.bg_color = Color(0.02, 0.16, 0.20, 0.92)
		sb.border_color = Color(0.22, 0.76, 0.86, 0.90)
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(3)
	return sb

func _build_slots() -> void:
	var row := get_node_or_null("Row") as HBoxContainer
	if row == null:
		row = HBoxContainer.new()
		row.name = "Row"
		add_child(row)
	row.add_theme_constant_override("separation", 3)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	for c in row.get_children():
		c.queue_free()
	_slots.clear()
	for i in range(slot_count):
		# Séparation SWG en 3 blocs de 4 slots (F1-F4  |  F5-F8  |  F9-F12)
		if i > 0 and i % 4 == 0:
			var sep := Control.new()
			sep.custom_minimum_size = Vector2(10, 1)
			row.add_child(sep)

		var btn := HotbarSlotBtn.new()
		btn.name = "Slot%d" % i
		btn.slot_index = i
		btn.hotbar = self
		btn.custom_minimum_size = slot_size
		btn.focus_mode = Control.FOCUS_NONE
		btn.text = ""
		btn.expand_icon = true
		btn.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
		btn.add_theme_stylebox_override("normal", _make_slot_style(false, false))
		btn.add_theme_stylebox_override("hover", _make_slot_style(true, false))
		btn.add_theme_stylebox_override("pressed", _make_slot_style(false, true))

		var icon_tex := _UiIconRegistry.tex(_UiIconRegistry.hotbar_icon(i % 10))
		if icon_tex:
			btn.icon = icon_tex
		var f_label := "F%d" % (i + 1)
		btn.tooltip_text = "%s (%d) — %s" % [f_label, (i + 1) % 10, _tooltips[i] if i < _tooltips.size() else ""]

		# Étiquette F1..F12 orange/or sous la case (exactement comme dans Star Wars Galaxies)
		var key_badge := Label.new()
		key_badge.name = "Key"
		key_badge.text = f_label
		key_badge.mouse_filter = Control.MOUSE_FILTER_IGNORE
		key_badge.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		key_badge.add_theme_font_size_override("font_size", 8)
		key_badge.add_theme_color_override("font_color", Color(0.98, 0.68, 0.22, 0.98))
		key_badge.position = Vector2(0.0, slot_size.y + 1.0)
		key_badge.size = Vector2(slot_size.x, 11.0)
		btn.add_child(key_badge)

		var idx := i
		btn.pressed.connect(func() -> void: _activate(idx))
		row.add_child(btn)
		_slots.append(btn)

func assign_item_to_slot(index: int, item: Dictionary) -> void:
	if index < 0 or index >= _slots.size():
		return
	var item_name := str(item.get("name", item.get("id", "Objet")))
	var icon_key := str(item.get("icon", _UiIconRegistry.item_icon(item_name)))
	var icon_tex := _UiIconRegistry.tex(icon_key)
	if icon_tex:
		_slots[index].icon = icon_tex
	_slots[index].tooltip_text = "F%d — %s (%s)" % [index + 1, _tooltips[index] if index < _tooltips.size() else "", item_name]
	item_assigned.emit(index, item)

func _unhandled_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed or event.echo:
		return
	var key := event as InputEventKey
	var idx := -1
	match key.keycode:
		KEY_1: idx = 0
		KEY_2: idx = 1
		KEY_3: idx = 2
		KEY_4: idx = 3
		KEY_5: idx = 4
		KEY_6: idx = 5
		KEY_7: idx = 6
		KEY_8: idx = 7
		KEY_9: idx = 8
		KEY_0: idx = 9
	if idx >= 0 and idx < slot_count:
		_activate(idx)
		get_viewport().set_input_as_handled()

func _activate(index: int) -> void:
	_active_index = index
	for i in range(_slots.size()):
		_slots[i].button_pressed = (i == index)
	slot_activated.emit(index)

func set_slot_label(index: int, text: String) -> void:
	if index < 0 or index >= _slots.size():
		return
	_slots[index].tooltip_text = text
