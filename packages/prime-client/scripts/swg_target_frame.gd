class_name SwgTargetFrame
extends Control
## Cadre de Ciblage Tactique & Jauges HAM Cible SWG Pre-CU
## Affiche en temps réel le nom, la distance, l'hostilité et les jauges HAM (Santé, Action, Mental) de la cible verrouillée.

signal target_cleared()

var _panel: Panel = null
var _name_label: Label = null
var _distance_label: Label = null
var _status_badge: Label = null

var _health_bar: ProgressBar = null
var _action_bar: ProgressBar = null
var _mind_bar: ProgressBar = null

var _health_val_label: Label = null
var _action_val_label: Label = null
var _mind_val_label: Label = null

var _current_target: Node = null
var _player_ref: Node = null


func _ready() -> void:
	visible = false
	custom_minimum_size = Vector2(400, 78)
	size = Vector2(400, 78)
	position = Vector2(440, 12)
	_build_ui()


func _build_ui() -> void:
	_panel = Panel.new()
	_panel.size = Vector2(400, 78)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.01, 0.08, 0.12, 0.92)
	sb.set_border_width_all(2)
	sb.border_color = Color(0.24, 0.86, 0.96, 0.9)
	sb.set_corner_radius_all(5)
	_panel.add_theme_stylebox_override("panel", sb)
	add_child(_panel)

	# Ligne 1 : Nom de la cible et distance
	_name_label = Label.new()
	_name_label.text = "Cible Galactique"
	_name_label.position = Vector2(10, 4)
	_name_label.size = Vector2(250, 18)
	_name_label.add_theme_font_size_override("font_size", 11)
	_name_label.add_theme_color_override("font_color", Color(0.96, 0.86, 0.35))
	_panel.add_child(_name_label)

	_status_badge = Label.new()
	_status_badge.text = "[NEUTRE]"
	_status_badge.position = Vector2(240, 4)
	_status_badge.size = Vector2(75, 18)
	_status_badge.add_theme_font_size_override("font_size", 9)
	_status_badge.add_theme_color_override("font_color", Color(0.4, 0.85, 1.0))
	_panel.add_child(_status_badge)

	_distance_label = Label.new()
	_distance_label.text = "0.0m"
	_distance_label.position = Vector2(315, 4)
	_distance_label.size = Vector2(55, 18)
	_distance_label.add_theme_font_size_override("font_size", 10)
	_distance_label.add_theme_color_override("font_color", Color(0.8, 0.9, 1.0, 0.8))
	_panel.add_child(_distance_label)

	var close_btn := Button.new()
	close_btn.text = "✕"
	close_btn.position = Vector2(375, 3)
	close_btn.size = Vector2(20, 18)
	close_btn.add_theme_font_size_override("font_size", 9)
	close_btn.pressed.connect(clear_target)
	_panel.add_child(close_btn)

	# Ligne 2 : 3 Barres HAM compactes (Santé, Action, Mental)
	var bar_y := 26
	var bar_h := 13
	var bar_w := 315

	# Barre Santé (Rouge)
	_health_bar = _create_bar(Color(0.85, 0.15, 0.15))
	_health_bar.position = Vector2(10, bar_y)
	_health_bar.size = Vector2(bar_w, bar_h)
	_panel.add_child(_health_bar)

	_health_val_label = Label.new()
	_health_val_label.text = "S: 250/250"
	_health_val_label.position = Vector2(330, bar_y - 2)
	_health_val_label.size = Vector2(65, bar_h)
	_health_val_label.add_theme_font_size_override("font_size", 9)
	_health_val_label.add_theme_color_override("font_color", Color(1.0, 0.6, 0.6))
	_panel.add_child(_health_val_label)

	# Barre Action (Verte)
	_action_bar = _create_bar(Color(0.15, 0.85, 0.25))
	_action_bar.position = Vector2(10, bar_y + 16)
	_action_bar.size = Vector2(bar_w, bar_h)
	_panel.add_child(_action_bar)

	_action_val_label = Label.new()
	_action_val_label.text = "A: 200/200"
	_action_val_label.position = Vector2(330, bar_y + 14)
	_action_val_label.size = Vector2(65, bar_h)
	_action_val_label.add_theme_font_size_override("font_size", 9)
	_action_val_label.add_theme_color_override("font_color", Color(0.6, 1.0, 0.6))
	_panel.add_child(_action_val_label)

	# Barre Mental (Bleue)
	_mind_bar = _create_bar(Color(0.15, 0.55, 0.95))
	_mind_bar.position = Vector2(10, bar_y + 32)
	_mind_bar.size = Vector2(bar_w, bar_h)
	_panel.add_child(_mind_bar)

	_mind_val_label = Label.new()
	_mind_val_label.text = "M: 200/200"
	_mind_val_label.position = Vector2(330, bar_y + 30)
	_mind_val_label.size = Vector2(65, bar_h)
	_mind_val_label.add_theme_font_size_override("font_size", 9)
	_mind_val_label.add_theme_color_override("font_color", Color(0.6, 0.8, 1.0))
	_panel.add_child(_mind_val_label)


func _create_bar(fg_col: Color) -> ProgressBar:
	var pb := ProgressBar.new()
	pb.show_percentage = false
	pb.max_value = 100.0
	pb.value = 100.0

	var bg_sb := StyleBoxFlat.new()
	bg_sb.bg_color = Color(0.04, 0.12, 0.16, 0.9)
	bg_sb.set_corner_radius_all(2)
	pb.add_theme_stylebox_override("background", bg_sb)

	var fg_sb := StyleBoxFlat.new()
	fg_sb.bg_color = fg_col
	fg_sb.set_corner_radius_all(2)
	pb.add_theme_stylebox_override("fill", fg_sb)

	return pb


func set_target(ent: Node, player: Node) -> void:
	_current_target = ent
	_player_ref = player
	if ent == null or not is_instance_valid(ent):
		clear_target()
		return

	visible = true
	update_target_data()


func clear_target() -> void:
	_current_target = null
	visible = false
	target_cleared.emit()


func _process(_delta: float) -> void:
	if visible and _current_target != null:
		if not is_instance_valid(_current_target):
			clear_target()
			return
		update_target_data()


func update_target_data() -> void:
	if _current_target == null or not is_instance_valid(_current_target):
		return

	var display_name: String = str(_current_target.get_meta("display_name", _current_target.name))
	var kind: String = str(_current_target.get_meta("entity_kind", "unknown"))
	var is_dead: bool = bool(_current_target.get_meta("is_dead", false))

	_name_label.text = display_name

	# Calcul de distance (Support unifié 2D Topdown & 3D)
	if _player_ref != null and _current_target != null:
		if _player_ref is Node3D and _current_target is Node3D:
			var d: float = (_player_ref as Node3D).global_position.distance_to((_current_target as Node3D).global_position)
			_distance_label.text = "%.1fm" % d
		elif _player_ref is Node2D and _current_target is Node2D:
			var d_px: float = (_player_ref as Node2D).global_position.distance_to((_current_target as Node2D).global_position)
			var d_m: float = d_px / 32.0
			_distance_label.text = "%.1fm" % d_m
		else:
			_distance_label.text = "—"
	else:
		_distance_label.text = "—"

	# Statut d'hostilité et bordure
	var border_color := Color(0.24, 0.86, 0.96)
	if is_dead:
		_status_badge.text = "[CADAVRE]"
		_status_badge.add_theme_color_override("font_color", Color(0.7, 0.7, 0.7))
		border_color = Color(0.5, 0.5, 0.5)
	elif kind == "npc_tusken" or kind.begins_with("creature_"):
		_status_badge.text = "[HOSTILE]"
		_status_badge.add_theme_color_override("font_color", Color(1.0, 0.3, 0.2))
		border_color = Color(0.9, 0.2, 0.15)
	elif kind.begins_with("npc_"):
		_status_badge.text = "[CITOYEN]"
		_status_badge.add_theme_color_override("font_color", Color(0.3, 1.0, 0.5))
		border_color = Color(0.2, 0.9, 0.4)
	else:
		_status_badge.text = "[STRUCTURE]"
		_status_badge.add_theme_color_override("font_color", Color(0.9, 0.8, 0.3))
		border_color = Color(0.8, 0.7, 0.2)

	var sb: StyleBoxFlat = _panel.get_theme_stylebox("panel") as StyleBoxFlat
	if sb:
		sb.border_color = border_color

	# Jauges HAM
	var cur_hp: int = int(_current_target.get_meta("current_health", 250))
	var max_hp: int = int(_current_target.get_meta("max_health", 250))
	if max_hp <= 0: max_hp = 250

	var hp_ratio := clampf(float(cur_hp) / float(max_hp), 0.0, 1.0)
	_health_bar.value = hp_ratio * 100.0
	_health_val_label.text = "S: %d/%d" % [maxi(0, cur_hp), max_hp]

	# Action & Mental simulés proportionnels ou réels
	var cur_act: int = int(_current_target.get_meta("current_action", int(max_hp * 0.8)))
	var max_act: int = int(_current_target.get_meta("max_action", int(max_hp * 0.8)))
	if max_act <= 0: max_act = 200
	_action_bar.value = clampf(float(cur_act) / float(max_act), 0.0, 1.0) * 100.0
	_action_val_label.text = "A: %d/%d" % [cur_act, max_act]

	var cur_mind: int = int(_current_target.get_meta("current_mind", int(max_hp * 0.7)))
	var max_mind: int = int(_current_target.get_meta("max_mind", int(max_hp * 0.7)))
	if max_mind <= 0: max_mind = 180
	_mind_bar.value = clampf(float(cur_mind) / float(max_mind), 0.0, 1.0) * 100.0
	_mind_val_label.text = "M: %d/%d" % [cur_mind, max_mind]

