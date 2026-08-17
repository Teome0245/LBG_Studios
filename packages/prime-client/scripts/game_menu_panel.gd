# game_menu_panel.gd — Menu pause / options (hotbar 0)
extends PanelContainer
class_name GameMenuPanel

signal resume_pressed
signal logout_pressed

@export var panel_visible: bool = false

var _title: Label
var _resume_btn: Button
var _missions_btn: Button
var _talents_btn: Button
var _inventory_btn: Button
var _quit_btn: Button

func _ready() -> void:
	visible = panel_visible
	_apply_style()
	_ensure_ui()
	_apply_mouse_filter()

func _apply_style() -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.05, 0.05, 0.06, 0.96)
	sb.set_border_width_all(2)
	sb.border_color = Color(0.75, 0.55, 0.3, 0.95)
	sb.set_corner_radius_all(6)
	sb.content_margin_left = 16
	sb.content_margin_top = 14
	sb.content_margin_right = 16
	sb.content_margin_bottom = 14
	sb.shadow_color = Color(0, 0, 0, 0.5)
	sb.shadow_size = 10
	add_theme_stylebox_override("panel", sb)

func _apply_mouse_filter() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP if panel_visible else Control.MOUSE_FILTER_IGNORE

func toggle() -> void:
	panel_visible = not panel_visible
	visible = panel_visible
	_apply_mouse_filter()

func close_menu() -> void:
	panel_visible = false
	visible = false
	_apply_mouse_filter()

func _ensure_ui() -> void:
	var root := get_node_or_null("VBox") as VBoxContainer
	if root == null:
		root = VBoxContainer.new()
		root.name = "VBox"
		root.add_theme_constant_override("separation", 8)
		add_child(root)
	_title = root.get_node_or_null("Title") as Label
	if _title == null:
		_title = Label.new()
		_title.name = "Title"
		_title.text = "Menu"
		_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		root.add_child(_title)
	_resume_btn = _mk_btn(root, "Resume", "Reprendre")
	_missions_btn = _mk_btn(root, "Missions", "Bureau des missions (J)")
	_talents_btn = _mk_btn(root, "Talents", "Talents / craft (T)")
	_inventory_btn = _mk_btn(root, "Inventory", "Inventaire (I)")
	_quit_btn = _mk_btn(root, "Quit", "Quitter le client")
	if not _resume_btn.pressed.is_connected(_on_resume):
		_resume_btn.pressed.connect(_on_resume)
	if not _missions_btn.pressed.is_connected(_on_missions):
		_missions_btn.pressed.connect(_on_missions)
	if not _talents_btn.pressed.is_connected(_on_talents):
		_talents_btn.pressed.connect(_on_talents)
	if not _inventory_btn.pressed.is_connected(_on_inventory):
		_inventory_btn.pressed.connect(_on_inventory)
	if not _quit_btn.pressed.is_connected(_on_quit):
		_quit_btn.pressed.connect(_on_quit)

func _mk_btn(root: VBoxContainer, name: String, text: String) -> Button:
	var b := root.get_node_or_null(name) as Button
	if b == null:
		b = Button.new()
		b.name = name
		b.text = text
		b.custom_minimum_size = Vector2(0, 34)
		root.add_child(b)
	return b

func _on_resume() -> void:
	close_menu()
	resume_pressed.emit()

func _on_missions() -> void:
	close_menu()
	var main := get_tree().get_first_node_in_group("prime_main")
	if main and main.has_method("_toggle_missions"):
		main.call("_toggle_missions")

func _on_talents() -> void:
	close_menu()
	var main := get_tree().get_first_node_in_group("prime_main")
	if main and main.has_method("_toggle_talents"):
		main.call("_toggle_talents")

func _on_inventory() -> void:
	close_menu()
	var main := get_tree().get_first_node_in_group("prime_main")
	if main and main.has_method("_toggle_inventory"):
		main.call("_toggle_inventory")

func _on_quit() -> void:
	logout_pressed.emit()
	get_tree().quit()
