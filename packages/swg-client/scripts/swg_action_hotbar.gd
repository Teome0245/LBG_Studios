extends Control
## Hotbar d'Actions Tactiques & Radar Boussole SWG Pre-CU (Holo-Teal)
## 1. Hotbar 8 slots [1..8] avec cooldowns et libellés holographiques.
## 2. Mini-Radar Circulaire en haut à droite indiquant le Nord et les entités proches.

signal hotbar_slot_triggered(slot_index: int, action_id: String)

var _hotbar_slots: Array = []
var _radar_panel: Control = null
var _radar_dots: Array = []

var tracked_player: Node3D = null
var tracked_entities: Array = []


func _ready() -> void:
	custom_minimum_size = Vector2(1280, 720)
	size = Vector2(1280, 720)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build_hotbar()
	_build_radar()


func _build_hotbar() -> void:
	var bar_container := HBoxContainer.new()
	bar_container.name = "HotbarContainer"
	bar_container.position = Vector2(340, 642)
	bar_container.size = Vector2(600, 36)
	bar_container.alignment = BoxContainer.ALIGNMENT_CENTER
	add_child(bar_container)

	var actions := [
		{"key": "1", "id": "blaster_shot", "label": "Tir Blaster", "col": Color(1.0, 0.3, 0.2)},
		{"key": "2", "id": "aim_shot", "label": "Tir Visé", "col": Color(0.2, 0.9, 1.0)},
		{"key": "3", "id": "dizzy_shot", "label": "Étourdir", "col": Color(0.9, 0.8, 0.2)},
		{"key": "4", "id": "bacta_stim", "label": "Stimpack", "col": Color(0.2, 1.0, 0.5)},
		{"key": "5", "id": "survey_tool", "label": "Sonde [U]", "col": Color(0.3, 0.8, 1.0)},
		{"key": "6", "id": "mask_scent", "label": "Camouflage", "col": Color(0.8, 0.6, 0.3)},
		{"key": "7", "id": "pet_command", "label": "Familier", "col": Color(0.9, 0.4, 0.7)},
		{"key": "8", "id": "speeder_mount", "label": "Speeder", "col": Color(0.95, 0.7, 0.15)}
	]

	for i in range(actions.size()):
		var act: Dictionary = actions[i]
		var btn := Button.new()
		btn.text = "[%s] %s" % [act["key"], act["label"]]
		btn.custom_minimum_size = Vector2(72, 34)
		btn.add_theme_font_size_override("font_size", 9)
		btn.add_theme_color_override("font_color", Color(0.95, 0.98, 1.0))

		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(0.02, 0.12, 0.16, 0.92)
		sb.set_border_width_all(1)
		sb.border_color = act["col"]
		sb.set_corner_radius_all(4)
		btn.add_theme_stylebox_override("normal", sb)

		var sb_h := sb.duplicate() as StyleBoxFlat
		sb_h.bg_color = Color(0.08, 0.35, 0.45, 0.98)
		sb_h.border_color = Color(1.0, 1.0, 1.0)
		btn.add_theme_stylebox_override("hover", sb_h)

		var slot_idx: int = i + 1
		var act_id: String = act["id"]
		btn.pressed.connect(func() -> void: hotbar_slot_triggered.emit(slot_idx, act_id))
		bar_container.add_child(btn)
		_hotbar_slots.append(btn)


func _build_radar() -> void:
	_radar_panel = Control.new()
	_radar_panel.name = "SwgRadar"
	_radar_panel.position = Vector2(1150, 20)
	_radar_panel.size = Vector2(110, 110)
	_radar_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_radar_panel)


func _draw() -> void:
	# Dessin du Radar Circulaire SWG (Holo-Teal)
	if _radar_panel == null:
		return
	var c: Vector2 = _radar_panel.position + Vector2(55, 55)
	var rad := 48.0

	# Fond et cercles concentriques du radar
	draw_circle(c, rad, Color(0.02, 0.10, 0.14, 0.85))
	draw_arc(c, rad, 0.0, TAU, 36, Color(0.24, 0.86, 0.96, 0.95), 1.5)
	draw_arc(c, rad * 0.6, 0.0, TAU, 24, Color(0.18, 0.64, 0.76, 0.45), 1.0)
	draw_arc(c, rad * 0.3, 0.0, TAU, 16, Color(0.18, 0.64, 0.76, 0.35), 1.0)

	# Lignes de mire du radar
	draw_line(c - Vector2(rad, 0), c + Vector2(rad, 0), Color(0.24, 0.86, 0.96, 0.35), 1.0)
	draw_line(c - Vector2(0, rad), c + Vector2(0, rad), Color(0.24, 0.86, 0.96, 0.35), 1.0)

	# Boussole : Nord
	var font := ThemeDB.fallback_font
	if font:
		draw_string(font, c + Vector2(-4, -rad - 2), "N", HORIZONTAL_ALIGNMENT_CENTER, 8, 10, Color(0.96, 0.86, 0.35))

	# Joueur au centre (triangle cyan)
	draw_circle(c, 3.5, Color(0.2, 1.0, 0.9, 1.0))

	# Points d'entités radar
	if tracked_player != null:
		var p_pos: Vector3 = tracked_player.global_position
		for ent in tracked_entities:
			if not is_instance_valid(ent):
				continue
			var ent_3d := ent as Node3D
			if ent_3d == null:
				continue
			var diff: Vector3 = ent_3d.global_position - p_pos
			# Conversion coordonnées monde (X, Z) vers écran radar (X, Y)
			var radar_offset := Vector2(diff.x, diff.z) * 0.45
			if radar_offset.length() < rad - 3.0:
				var dot_pos := c + radar_offset
				var dot_col := Color(0.95, 0.85, 0.2) # Jaune PNJ par défaut
				var e_name: String = ent_3d.name.to_lower()
				if "chacal" in e_name or "beetle" in e_name or "creature" in e_name:
					dot_col = Color(1.0, 0.25, 0.2) # Rouge bête hostile
				elif "terminal" in e_name or "shuttle" in e_name or "cantina" in e_name:
					dot_col = Color(0.2, 0.9, 1.0) # Bleu/cyan points d'intérêt
				draw_circle(dot_pos, 2.5, dot_col)


func _process(_delta: float) -> void:
	queue_redraw()


func trigger_slot(idx: int) -> void:
	if idx >= 1 and idx <= _hotbar_slots.size():
		var btn = _hotbar_slots[idx - 1] as Button
		btn.emit_signal("pressed")
