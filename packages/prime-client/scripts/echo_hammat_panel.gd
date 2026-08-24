extends PanelContainer
## EchoHammatPanel — UI prototype : invoquer / switch / renvoyer (max 2 persos simultanés)

signal panel_closed

@export var panel_visible: bool = false

var _controller: Node = null
var _status: Label
var _noyau: Label
var _invoke_list: ItemList
var _order_btn: OptionButton
var _btn_invoke: Button
var _btn_switch: Button
var _btn_dismiss: Button
var _btn_order: Button
var _btn_close: Button
var _msg: Label


func _ready() -> void:
	visible = panel_visible
	_apply_style()
	_ensure_ui()
	_apply_mouse_filter()


func bind_controller(ctrl: Node) -> void:
	_controller = ctrl
	if _controller == null:
		return
	if _controller.has_signal("state_changed"):
		if not _controller.state_changed.is_connected(_refresh):
			_controller.state_changed.connect(_refresh)
	if _controller.has_signal("action_message"):
		if not _controller.action_message.is_connected(_on_action_msg):
			_controller.action_message.connect(_on_action_msg)
	_refresh({})


func toggle() -> void:
	panel_visible = not panel_visible
	visible = panel_visible
	_apply_mouse_filter()
	if panel_visible:
		_refresh({})


func close_panel() -> void:
	panel_visible = false
	visible = false
	_apply_mouse_filter()
	panel_closed.emit()


func _apply_style() -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.04, 0.06, 0.08, 0.96)
	sb.set_border_width_all(2)
	sb.border_color = Color(0.35, 0.75, 0.9, 0.9)
	sb.set_corner_radius_all(6)
	sb.content_margin_left = 14
	sb.content_margin_top = 12
	sb.content_margin_right = 14
	sb.content_margin_bottom = 12
	add_theme_stylebox_override("panel", sb)


func _apply_mouse_filter() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP if panel_visible else Control.MOUSE_FILTER_IGNORE


func _ensure_ui() -> void:
	var root := get_node_or_null("VBox") as VBoxContainer
	if root == null:
		root = VBoxContainer.new()
		root.name = "VBox"
		root.add_theme_constant_override("separation", 8)
		add_child(root)
	var title := Label.new()
	title.text = "Écho Amas"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	if root.get_child_count() == 0:
		root.add_child(title)
	_status = _mk_label(root, "Status", "Actif : — · Écho : aucun")
	_noyau = _mk_label(root, "Noyau", "Particule : —")
	_invoke_list = ItemList.new()
	_invoke_list.name = "InvokeList"
	_invoke_list.custom_minimum_size = Vector2(300, 100)
	root.add_child(_invoke_list)
	var row1 := HBoxContainer.new()
	row1.add_theme_constant_override("separation", 6)
	root.add_child(row1)
	_btn_invoke = _mk_button(row1, "Invoke", "Invoquer écho")
	_btn_dismiss = _mk_button(row1, "Dismiss", "Renvoyer écho")
	var row2 := HBoxContainer.new()
	row2.add_theme_constant_override("separation", 6)
	root.add_child(row2)
	_btn_switch = _mk_button(row2, "Switch", "Switch actif ↔ écho")
	_order_btn = OptionButton.new()
	_order_btn.add_item("soin")
	_order_btn.add_item("forge")
	_order_btn.add_item("ping")
	_order_btn.add_item("buff")
	_order_btn.add_item("taunt")
	_order_btn.add_item("marque")
	row2.add_child(_order_btn)
	_btn_order = _mk_button(row2, "Order", "Ordre écho")
	_msg = _mk_label(root, "Msg", "")
	_btn_close = _mk_button(root, "Close", "Fermer")
	_btn_invoke.pressed.connect(_on_invoke)
	_btn_dismiss.pressed.connect(_on_dismiss)
	_btn_switch.pressed.connect(_on_switch)
	_btn_order.pressed.connect(_on_order)
	_btn_close.pressed.connect(close_panel)


func _mk_label(root: Node, name: String, text: String) -> Label:
	var n := root.get_node_or_null(name) as Label
	if n == null:
		n = Label.new()
		n.name = name
		n.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		root.add_child(n)
	n.text = text
	return n


func _mk_button(root: Node, name: String, text: String) -> Button:
	var b := root.get_node_or_null(name) as Button
	if b == null:
		b = Button.new()
		b.name = name
		b.text = text
		root.add_child(b)
	return b


func _refresh(_state: Dictionary) -> void:
	if _controller == null:
		return
	var act := str(_controller.get("active_character_name"))
	var echo := str(_controller.get("echo_character_name"))
	if echo.is_empty():
		echo = "aucun"
	var count := 1 + (1 if _controller.has_echo() else 0)
	_status.text = "Actif : %s · Écho : %s (%d/2 max)" % [act, echo, count]
	var nk := str(_controller.get("noyau_id"))
	var ps := str(_controller.get("particule_seed"))
	_noyau.text = "Noyau : %s · Particule : %s" % [nk if nk else "—", ps if ps else "—"]
	_invoke_list.clear()
	if _controller.has_method("invoke_candidates"):
		for entry in _controller.invoke_candidates():
			if entry is Dictionary:
				var label := str(entry.get("name", entry.get("character_id", "?")))
				var arch := str(entry.get("archetype", ""))
				if not arch.is_empty():
					label += " (%s)" % arch
				_invoke_list.add_item(label)
				var cid := str(entry.get("character_id", entry.get("id", "")))
				_invoke_list.set_item_metadata(_invoke_list.item_count - 1, cid)
	_btn_invoke.disabled = not (_controller.has_method("can_invoke") and _controller.can_invoke())
	_btn_switch.disabled = not (_controller.has_method("can_switch") and _controller.can_switch())
	_btn_dismiss.disabled = not (_controller.has_method("has_echo") and _controller.has_echo())
	_btn_order.disabled = _btn_dismiss.disabled


func _on_invoke() -> void:
	if _controller == null:
		return
	var sel := _invoke_list.get_selected_items()
	if sel.is_empty():
		_msg.text = "Sélectionne un perso à invoquer."
		return
	var cid := str(_invoke_list.get_item_metadata(int(sel[0])))
	_controller.invoke_echo(cid)


func _on_dismiss() -> void:
	if _controller:
		_controller.dismiss_echo()


func _on_switch() -> void:
	if _controller:
		_controller.switch_active()


func _on_order() -> void:
	if _controller == null:
		return
	var orders := ["soin", "forge", "ping", "buff", "taunt", "marque"]
	var idx := _order_btn.selected
	if idx >= 0 and idx < orders.size():
		_controller.echo_order(orders[idx])


func _on_action_msg(message: String) -> void:
	_msg.text = message
	_refresh({})
