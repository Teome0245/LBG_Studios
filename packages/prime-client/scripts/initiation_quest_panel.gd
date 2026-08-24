extends PanelContainer
## InitiationQuestPanel — dialogue Ryn Solh + actions quête Particule / Écho

signal panel_closed

@export var panel_visible: bool = false

var _controller: Node = null
var _speaker: Label
var _body: RichTextLabel
var _particule_box: PanelContainer
var _particule_label: Label
var _action_btn: Button
var _skip_btn: Button
var _noyau_id: String = ""
var _particule_seed: String = ""


func _ready() -> void:
	visible = panel_visible
	_apply_style()
	_ensure_ui()
	_apply_mouse_filter()


func bind_controller(ctrl: Node) -> void:
	_controller = ctrl
	if _controller == null:
		return
	if _controller.has_signal("step_changed"):
		if not _controller.step_changed.is_connected(_on_step_changed):
			_controller.step_changed.connect(_on_step_changed)


func set_particule_info(noyau_id: String, particule_seed: String) -> void:
	_noyau_id = noyau_id
	_particule_seed = particule_seed


func open_panel() -> void:
	panel_visible = true
	visible = true
	_apply_mouse_filter()


func refresh_step() -> void:
	_paint_step()


func close_panel() -> void:
	panel_visible = false
	visible = false
	_apply_mouse_filter()
	panel_closed.emit()


func _apply_style() -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.04, 0.05, 0.07, 0.97)
	sb.set_border_width_all(2)
	sb.border_color = Color(0.35, 0.85, 0.95, 0.85)
	sb.set_corner_radius_all(8)
	sb.content_margin_left = 16
	sb.content_margin_top = 14
	sb.content_margin_right = 16
	sb.content_margin_bottom = 14
	add_theme_stylebox_override("panel", sb)


func _apply_mouse_filter() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP if panel_visible else Control.MOUSE_FILTER_IGNORE


func _ensure_ui() -> void:
	var root := get_node_or_null("VBox") as VBoxContainer
	if root == null:
		root = VBoxContainer.new()
		root.name = "VBox"
		root.add_theme_constant_override("separation", 10)
		add_child(root)
	var title := Label.new()
	title.text = "Initiation — L'Éclat qui se divise"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	if root.get_child_count() == 0:
		root.add_child(title)
	_speaker = Label.new()
	_speaker.name = "Speaker"
	_speaker.add_theme_color_override("font_color", Color(0.55, 0.9, 1.0))
	root.add_child(_speaker)
	_body = RichTextLabel.new()
	_body.name = "Body"
	_body.bbcode_enabled = true
	_body.fit_content = true
	_body.custom_minimum_size = Vector2(360, 120)
	_body.scroll_active = false
	root.add_child(_body)
	_particule_box = PanelContainer.new()
	_particule_box.name = "ParticuleBox"
	_particule_box.visible = false
	var pv := VBoxContainer.new()
	_particule_label = Label.new()
	_particule_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_particule_label.add_theme_color_override("font_color", Color(0.9, 0.75, 0.35))
	pv.add_child(_particule_label)
	_particule_box.add_child(pv)
	root.add_child(_particule_box)
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 12)
	root.add_child(row)
	_action_btn = Button.new()
	_action_btn.text = "Continuer"
	_action_btn.pressed.connect(_on_action)
	row.add_child(_action_btn)
	_skip_btn = Button.new()
	_skip_btn.text = "Plus tard"
	_skip_btn.pressed.connect(close_panel)
	row.add_child(_skip_btn)


func _on_step_changed(_step_id: String, _idx: int) -> void:
	_paint_step()


func _paint_step() -> void:
	if _controller == null:
		return
	var step: Dictionary = _controller.get_current_step() if _controller.has_method("get_current_step") else {}
	if step.is_empty():
		close_panel()
		return
	open_panel()
	_speaker.text = str(step.get("speaker", "Ryn Solh"))
	_body.text = str(step.get("text", "")).replace("\n", "\n\n")
	var action := str(step.get("action", "continue"))
	_particule_box.visible = action == "show_particule"
	if _particule_box.visible:
		_particule_label.text = "Noyau : %s\nParticule : %s\n\n[pulse synchronisée entre tes éclats]" % [
			_noyau_id if _noyau_id else "—",
			_particule_seed if _particule_seed else "—",
		]
	var label := str(step.get("button_label", "Continuer"))
	if action == "continue" or action == "show_particule":
		label = "Continuer"
	_action_btn.text = label
	var min_roster := int(step.get("requires_roster_min", 0))
	if min_roster > 0 and _controller.get_parent():
		var main := get_tree().get_first_node_in_group("prime_main")
		var roster_size := 1
		if main and main.has_method("_get_roster_size"):
			roster_size = int(main.call("_get_roster_size"))
		_action_btn.disabled = roster_size < min_roster
	else:
		_action_btn.disabled = false


func _on_action() -> void:
	if _controller == null:
		close_panel()
		return
	var action: String = (
		_controller.get_action_for_step() if _controller.has_method("get_action_for_step") else "continue"
	)
	match action:
		"continue", "show_particule":
			_controller.advance_step()
		"create_second_character":
			if _controller.has_signal("request_create_character"):
				_controller.request_create_character.emit()
		"open_echo_panel":
			if _controller.has_signal("request_open_echo_panel"):
				_controller.request_open_echo_panel.emit()
		"complete":
			_controller.advance_step()
			close_panel()
		_:
			_controller.advance_step()
	_paint_step()
