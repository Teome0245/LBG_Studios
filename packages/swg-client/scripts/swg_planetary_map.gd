extends Control
## Carte Planétaire Tactique SWG Pre-CU (Lost Heaven, Touche M)
## Affiche la topographie du secteur, les coordonnées GPS (X, Z), les POI et permet de poser des Waypoints.

signal waypoint_created(coord: Vector2, label_name: String)

var _panel: Panel = null
var _map_draw: Control = null
var _coord_lbl: Label = null

var player_pos_3d: Vector3 = Vector3.ZERO
var poi_list: Array = [
	{"name": "Cantina La Perle", "pos": Vector2(25, -22), "icon": "🍷", "col": Color(0.9, 0.4, 0.7)},
	{"name": "Spatioport (Shuttleport)", "pos": Vector2(-42, -28), "icon": "🚀", "col": Color(0.2, 0.9, 1.0)},
	{"name": "Hôtel de Ville (Town Hall)", "pos": Vector2(0, -45), "icon": "🏛️", "col": Color(0.96, 0.86, 0.35)},
	{"name": "Centre Médical & Bacta", "pos": Vector2(-28, 22), "icon": "🏥", "col": Color(0.2, 1.0, 0.5)},
	{"name": "Porte Ouest (Remparts)", "pos": Vector2(-65, 0), "icon": "🛡️", "col": Color(0.8, 0.6, 0.3)},
	{"name": "Porte Est (Remparts)", "pos": Vector2(65, 0), "icon": "🛡️", "col": Color(0.8, 0.6, 0.3)},
	{"name": "Campement de Scout Nomade", "pos": Vector2(-95, -45), "icon": "⛺", "col": Color(1.0, 0.8, 0.2)},
	{"name": "Extracteur Minier Lourd", "pos": Vector2(90, -55), "icon": "⛏️", "col": Color(1.0, 0.5, 0.2)}
]

var user_waypoints: Array = []


func _ready() -> void:
	visible = false
	custom_minimum_size = Vector2(760, 520)
	size = Vector2(760, 520)
	position = Vector2(260, 110)
	_build_ui()


func _build_ui() -> void:
	_panel = Panel.new()
	_panel.size = Vector2(760, 520)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.015, 0.08, 0.12, 0.97)
	sb.set_border_width_all(2)
	sb.border_color = Color(0.24, 0.86, 0.96, 0.95)
	sb.set_corner_radius_all(6)
	_panel.add_theme_stylebox_override("panel", sb)
	add_child(_panel)

	var title := Label.new()
	title.text = "◈ CARTE PLANÉTAIRE TACTIQUE • SECTEUR LOST HEAVEN ◈"
	title.position = Vector2(16, 12)
	title.add_theme_font_size_override("font_size", 13)
	title.add_theme_color_override("font_color", Color(0.3, 0.9, 1.0))
	_panel.add_child(title)

	var close_btn := Button.new()
	close_btn.text = "✕"
	close_btn.position = Vector2(720, 8)
	close_btn.size = Vector2(30, 24)
	close_btn.pressed.connect(close_panel)
	_panel.add_child(close_btn)

	# Zone de dessin de la carte
	_map_draw = Control.new()
	_map_draw.position = Vector2(20, 48)
	_map_draw.size = Vector2(720, 420)
	_map_draw.draw.connect(_on_map_draw)
	_map_draw.gui_input.connect(_on_map_gui_input)
	_panel.add_child(_map_draw)

	_coord_lbl = Label.new()
	_coord_lbl.text = "Coordonnées GPS Joueur : (X: 0m, Z: 0m) | Clic sur la carte = Créer Waypoint"
	_coord_lbl.position = Vector2(20, 480)
	_coord_lbl.add_theme_font_size_override("font_size", 11)
	_coord_lbl.add_theme_color_override("font_color", Color(0.96, 0.86, 0.35))
	_panel.add_child(_coord_lbl)


func _on_map_draw() -> void:
	var c := _map_draw.size * 0.5
	var scale_factor := 2.2 # 1 mètre = 2.2 pixels

	# Grille cartographique holographique
	for x in range(0, 720, 40):
		_map_draw.draw_line(Vector2(x, 0), Vector2(x, 420), Color(0.18, 0.64, 0.76, 0.15))
	for y in range(0, 420, 40):
		_map_draw.draw_line(Vector2(0, y), Vector2(720, y), Color(0.18, 0.64, 0.76, 0.15))

	# Périmètre urbain de Lost Heaven
	_map_draw.draw_rect(Rect2(c.x - 140, c.y - 120, 280, 240), Color(0.2, 0.8, 0.9, 0.08), true)
	_map_draw.draw_rect(Rect2(c.x - 140, c.y - 120, 280, 240), Color(0.24, 0.86, 0.96, 0.5), false, 1.5)

	var font := ThemeDB.fallback_font

	# Dessin des POI
	for p in poi_list:
		var p_screen: Vector2 = c + p["pos"] * scale_factor
		if Rect2(Vector2.ZERO, _map_draw.size).has_point(p_screen):
			_map_draw.draw_circle(p_screen, 5.0, p["col"])
			if font:
				_map_draw.draw_string(font, p_screen + Vector2(8, 4), p["name"], HORIZONTAL_ALIGNMENT_LEFT, 150, 10, Color(0.95, 0.95, 1.0))

	# Dessin des Waypoints utilisateur
	for wp in user_waypoints:
		var wp_screen: Vector2 = c + wp["pos"] * scale_factor
		_map_draw.draw_circle(wp_screen, 6.0, Color(0.2, 1.0, 0.5))
		if font:
			_map_draw.draw_string(font, wp_screen + Vector2(8, 4), "★ " + wp["name"], HORIZONTAL_ALIGNMENT_LEFT, 120, 10, Color(0.2, 1.0, 0.5))

	# Position actuelle du joueur (Triangle cyan brillant)
	var p_screen: Vector2 = c + Vector2(player_pos_3d.x, player_pos_3d.z) * scale_factor
	_map_draw.draw_circle(p_screen, 6.5, Color(1.0, 0.85, 0.2))
	_map_draw.draw_arc(p_screen, 12.0, 0.0, TAU, 18, Color(1.0, 0.85, 0.2, 0.6), 1.5)
	if font:
		_map_draw.draw_string(font, p_screen + Vector2(-20, -14), "VOUS ICI", HORIZONTAL_ALIGNMENT_CENTER, 40, 9, Color(1.0, 0.9, 0.3))


func _on_map_gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		var c: Vector2 = _map_draw.size * 0.5
		var scale_factor: float = 2.2
		var world_xz: Vector2 = (event.position - c) / scale_factor
		var wp_name: String = "Balise %d (%dm, %dm)" % [user_waypoints.size() + 1, int(world_xz.x), int(world_xz.y)]
		user_waypoints.append({"pos": world_xz, "name": wp_name})
		waypoint_created.emit(world_xz, wp_name)
		_coord_lbl.text = "✓ Waypoint [%s] créé à (X: %dm, Z: %dm) !" % [wp_name, int(world_xz.x), int(world_xz.y)]
		_map_draw.queue_redraw()


func update_player_position(pos: Vector3) -> void:
	player_pos_3d = pos
	if _coord_lbl:
		_coord_lbl.text = "Coordonnées GPS Joueur : (X: %dm, Z: %dm) | Clic sur la carte = Créer Waypoint" % [int(pos.x), int(pos.z)]
	if visible and _map_draw:
		_map_draw.queue_redraw()


func add_waypoint(world_xz: Vector2, wp_name: String) -> void:
	# Évite les doublons
	for wp in user_waypoints:
		if wp.get("name") == wp_name:
			return
	user_waypoints.append({"pos": world_xz, "name": wp_name})
	if _coord_lbl:
		_coord_lbl.text = "★ Objectif Actif : [%s] à (X: %dm, Z: %dm)" % [wp_name, int(world_xz.x), int(world_xz.y)]
	if _map_draw:
		_map_draw.queue_redraw()


func remove_waypoint(wp_name: String) -> void:
	var filtered: Array = []
	for wp in user_waypoints:
		if wp.get("name") != wp_name:
			filtered.append(wp)
	user_waypoints = filtered
	if _map_draw:
		_map_draw.queue_redraw()


func toggle() -> void:
	visible = not visible
	if visible and _map_draw:
		_map_draw.queue_redraw()


func open_panel() -> void:
	visible = true
	if _map_draw:
		_map_draw.queue_redraw()


func close_panel() -> void:
	visible = false
