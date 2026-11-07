extends PanelContainer
## Interface SWG Pre-CU (2D Top-Down) — Outil de Prospection (Survey Tool),
## Radar polaire Holo-Teal (0..100%), Jauge Graphique des 5 Stats (OQ/CD/PE/MA/SR 1..1000) & Harvesters.

signal resource_sampled(result: Dictionary)
signal harvester_deployed(result: Dictionary)

const _HubRuntimeCfg = preload("res://scripts/hub_runtime_cfg.gd")

var sidecar_base_url: String = "http://192.168.0.246:8787"
var player_id: String = "Voyageur"
var player_pos_xz: Vector2 = Vector2(4795.0, -565.0)
var panel_visible: bool = false

var _spawns: Array = []
var _harvesters: Array = []
var _selected_idx: int = 0
var _last_density_pct: int = 88
var _last_dir: String = "HERE"

var _http_spawns: HTTPRequest = null
var _http_action: HTTPRequest = null

var _status_lbl: Label = null
var _spawns_list: ItemList = null
var _stats_lbl: Label = null
var _stats_draw: _SurveyStatsDraw = null
var _harv_lbl: Label = null
var _radar_draw: _SurveyRadarDraw = null


class _SurveyRadarDraw extends Control:
	var density_pct: int = 85
	var compass_dir: String = "NE"
	var spawn_name: String = "Cuivre Kovessien"

	func _init() -> void:
		custom_minimum_size = Vector2(210, 210)

	func update_radar(p_dens: int, p_dir: String, p_name: String) -> void:
		density_pct = clampi(p_dens, 0, 100)
		compass_dir = p_dir
		spawn_name = p_name
		queue_redraw()

	func _dir_to_vec(d: String) -> Vector2:
		match d.to_upper():
			"N": return Vector2(0, -1)
			"NE": return Vector2(0.707, -0.707)
			"E": return Vector2(1, 0)
			"SE": return Vector2(0.707, 0.707)
			"S": return Vector2(0, 1)
			"SW": return Vector2(-0.707, 0.707)
			"W": return Vector2(-1, 0)
			"NW": return Vector2(-0.707, -0.707)
			_: return Vector2.ZERO

	func _draw() -> void:
		var font := ThemeDB.fallback_font
		var c := Vector2(size.x * 0.5, size.y * 0.54)
		var r := minf(size.x, size.y) * 0.39
		draw_rect(Rect2(Vector2.ZERO, size), Color(0.01, 0.06, 0.08, 0.96), true)
		draw_rect(Rect2(Vector2.ZERO, size), Color(0.22, 0.72, 0.82, 0.85), false, 1.5)

		# Grilles polaires SWG Survey
		draw_arc(c, r, 0.0, TAU, 48, Color(0.25, 0.80, 0.90, 0.75), 1.5)
		draw_arc(c, r * 0.66, 0.0, TAU, 36, Color(0.20, 0.65, 0.75, 0.45), 1.0)
		draw_arc(c, r * 0.33, 0.0, TAU, 24, Color(0.20, 0.65, 0.75, 0.30), 1.0)
		draw_line(Vector2(c.x - r, c.y), Vector2(c.x + r, c.y), Color(0.18, 0.55, 0.65, 0.40), 1.0)
		draw_line(Vector2(c.x, c.y - r), Vector2(c.x, c.y + r), Color(0.18, 0.55, 0.65, 0.40), 1.0)

		# Nappe thermique de concentration
		var pulse_r := r * clampf(float(density_pct) / 100.0, 0.14, 0.94)
		var dvec := _dir_to_vec(compass_dir)
		var hotspot_pos := c + dvec * (r * 0.35)
		var col_outer := Color(0.12, 0.85, 0.55, 0.22) if density_pct >= 50 else Color(0.92, 0.65, 0.18, 0.22)
		var col_inner := Color(0.25, 0.98, 0.68, 0.42) if density_pct >= 50 else Color(0.98, 0.78, 0.25, 0.38)
		draw_circle(hotspot_pos, pulse_r * 0.75, col_outer)
		draw_circle(hotspot_pos, pulse_r * 0.40, col_inner)

		# Vecteur de balayage vers l'épicentre
		if dvec.length() > 0.01:
			draw_line(c, hotspot_pos, Color(0.98, 0.88, 0.32, 0.85), 1.5)
			draw_circle(hotspot_pos, 4.0, Color(0.98, 0.42, 0.22, 1.0))

		# Position joueur au centre
		draw_circle(c, 4.0, Color(0.45, 0.96, 1.0, 1.0))

		if font:
			draw_string(font, Vector2(6, 14), "%s" % spawn_name.to_upper(), HORIZONTAL_ALIGNMENT_LEFT, size.x - 12, 10, Color(0.65, 0.96, 1.0, 1.0))
			draw_string(font, Vector2(6, 26), "CONCENTRATION : %d%% (%s)" % [density_pct, compass_dir], HORIZONTAL_ALIGNMENT_LEFT, size.x - 12, 9, Color(0.98, 0.86, 0.35, 1.0))
			draw_string(font, Vector2(c.x - 4, c.y - r - 4), "N", HORIZONTAL_ALIGNMENT_LEFT, 16, 9, Color(0.55, 0.88, 0.95, 0.9))
			draw_string(font, Vector2(c.x - 4, c.y + r + 11), "S", HORIZONTAL_ALIGNMENT_LEFT, 16, 9, Color(0.55, 0.88, 0.95, 0.9))
			draw_string(font, Vector2(c.x + r + 4, c.y + 4), "E", HORIZONTAL_ALIGNMENT_LEFT, 16, 9, Color(0.55, 0.88, 0.95, 0.9))
			draw_string(font, Vector2(c.x - r - 12, c.y + 4), "W", HORIZONTAL_ALIGNMENT_LEFT, 16, 9, Color(0.55, 0.88, 0.95, 0.9))


class _SurveyStatsDraw extends Control:
	var stats: Dictionary = {"oq": 860, "cd": 920, "pe": 640, "ma": 780, "sr": 710}

	func _init() -> void:
		custom_minimum_size = Vector2(250, 130)

	func set_stats(p_stats: Dictionary) -> void:
		stats = p_stats.duplicate()
		queue_redraw()

	func _draw() -> void:
		var font := ThemeDB.fallback_font
		draw_rect(Rect2(Vector2.ZERO, size), Color(0.01, 0.06, 0.08, 0.94), true)
		draw_rect(Rect2(Vector2.ZERO, size), Color(0.20, 0.64, 0.74, 0.80), false, 1.0)
		var rows := [
			{"k": "oq", "lbl": "OQ · Qualité globale", "col": Color(0.22, 0.88, 0.68, 0.95)},
			{"k": "cd", "lbl": "CD · Conductivité", "col": Color(0.28, 0.78, 0.95, 0.95)},
			{"k": "pe", "lbl": "PE · Énergie potentielle", "col": Color(0.95, 0.78, 0.25, 0.95)},
			{"k": "ma", "lbl": "MA · Malléabilité", "col": Color(0.38, 0.86, 0.82, 0.95)},
			{"k": "sr", "lbl": "SR · Résistance chocs", "col": Color(0.88, 0.56, 0.28, 0.95)},
		]
		var y := 10.0
		for r in rows:
			var r_dict: Dictionary = r
			var val := clampi(int(stats.get(r_dict["k"], 500)), 0, 1000)
			var ratio := float(val) / 1000.0
			if font:
				draw_string(font, Vector2(8, y + 9), str(r_dict["lbl"]), HORIZONTAL_ALIGNMENT_LEFT, 118, 9, Color(0.78, 0.94, 0.98, 1.0))
			var bx := 126.0
			var bw := maxf(60.0, size.x - 182.0)
			var bh := 10.0
			var bar_col: Color = r_dict["col"]
			draw_rect(Rect2(bx, y, bw, bh), Color(0.02, 0.10, 0.13, 0.95), true)
			draw_rect(Rect2(bx, y, bw * ratio, bh), bar_col, true)
			draw_rect(Rect2(bx, y, bw * ratio, 3.0), Color(1, 1, 1, 0.22), true)
			draw_rect(Rect2(bx, y, bw, bh), Color(0.24, 0.68, 0.78, 0.75), false, 1.0)
			if font:
				draw_string(font, Vector2(bx + bw + 6, y + 9), "%d" % val, HORIZONTAL_ALIGNMENT_LEFT, 44, 9, Color(0.98, 0.88, 0.42, 1.0))
			y += 23.0


func _ready() -> void:
	visible = panel_visible
	_apply_runtime_cfg()
	_apply_style()
	_ensure_ui()
	_apply_local_fallback()
	_http_spawns = HTTPRequest.new()
	add_child(_http_spawns)
	_http_spawns.request_completed.connect(_on_spawns_http_done)
	_http_action = HTTPRequest.new()
	add_child(_http_action)
	_http_action.request_completed.connect(_on_action_http_done)


func _apply_runtime_cfg() -> void:
	if _HubRuntimeCfg.enabled():
		sidecar_base_url = _HubRuntimeCfg.http_url(sidecar_base_url)
		player_id = _HubRuntimeCfg.player_name("Voyageur")


func _apply_style() -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.02, 0.11, 0.14, 0.95)
	sb.set_border_width_all(2)
	sb.border_color = Color(0.28, 0.84, 0.78, 0.92)
	sb.set_corner_radius_all(6)
	sb.content_margin_left = 14
	sb.content_margin_top = 10
	sb.content_margin_right = 14
	sb.content_margin_bottom = 12
	add_theme_stylebox_override("panel", sb)


func _style_action_btn(btn: Button, accent: Color) -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.04, 0.22, 0.27, 0.95)
	sb.set_border_width_all(1)
	sb.border_color = accent
	sb.set_corner_radius_all(4)
	sb.content_margin_left = 10
	sb.content_margin_top = 5
	sb.content_margin_right = 10
	sb.content_margin_bottom = 5
	var sb_hov := sb.duplicate() as StyleBoxFlat
	sb_hov.bg_color = Color(0.08, 0.34, 0.40, 0.98)
	btn.add_theme_stylebox_override("normal", sb)
	btn.add_theme_stylebox_override("hover", sb_hov)
	btn.add_theme_stylebox_override("pressed", sb_hov)
	btn.add_theme_color_override("font_color", Color(0.88, 0.98, 1.0, 1.0))
	btn.add_theme_font_size_override("font_size", 10)


func toggle() -> void:
	panel_visible = not panel_visible
	visible = panel_visible
	mouse_filter = Control.MOUSE_FILTER_STOP if panel_visible else Control.MOUSE_FILTER_IGNORE
	if panel_visible:
		refresh_spawns()


func open_panel() -> void:
	panel_visible = true
	visible = true
	mouse_filter = Control.MOUSE_FILTER_STOP
	refresh_spawns()


func close_panel() -> void:
	panel_visible = false
	visible = false
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func update_survey_from_world(p_dens: int, p_dir: String, p_name: String) -> void:
	_last_density_pct = clampi(p_dens, 0, 100)
	_last_dir = p_dir
	if _radar_draw:
		_radar_draw.update_radar(p_dens, p_dir, p_name)
	if _status_lbl:
		_status_lbl.text = "Radar 3D actif : %s détecté à %d%% (%s)" % [p_name, p_dens, p_dir]


func _ensure_ui() -> void:
	if _spawns_list != null:
		return
	custom_minimum_size = Vector2(760, 430)
	position = Vector2(190, 95)
	size = Vector2(760, 430)

	var root := VBoxContainer.new()
	root.add_theme_constant_override("separation", 8)
	add_child(root)

	var hdr_panel := PanelContainer.new()
	var sb_hdr := StyleBoxFlat.new()
	sb_hdr.bg_color = Color(0.04, 0.24, 0.28, 0.96)
	sb_hdr.set_border_width_all(1)
	sb_hdr.border_color = Color(0.35, 0.92, 0.82, 0.90)
	sb_hdr.set_corner_radius_all(4)
	sb_hdr.content_margin_left = 10
	sb_hdr.content_margin_top = 4
	sb_hdr.content_margin_right = 8
	sb_hdr.content_margin_bottom = 4
	hdr_panel.add_theme_stylebox_override("panel", sb_hdr)
	root.add_child(hdr_panel)

	var top_bar := HBoxContainer.new()
	hdr_panel.add_child(top_bar)

	var title := Label.new()
	title.text = "◎  OUTIL DE PROSPECTION & EXTRACTEURS  —  SWG PRE-CU (STATS 1..1000)"
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title.add_theme_font_size_override("font_size", 12)
	title.add_theme_color_override("font_color", Color(0.62, 0.98, 0.88, 1.0))
	top_bar.add_child(title)

	var close_btn := Button.new()
	close_btn.text = "✕"
	close_btn.custom_minimum_size = Vector2(26, 22)
	close_btn.pressed.connect(toggle)
	top_bar.add_child(close_btn)

	_status_lbl = Label.new()
	_status_lbl.text = "Sélectionne un gisement planétaire pour lancer un balayage radar ou déployer un Harvester."
	_status_lbl.add_theme_font_size_override("font_size", 10)
	_status_lbl.add_theme_color_override("font_color", Color(0.75, 0.94, 0.88, 1.0))
	root.add_child(_status_lbl)

	var body := HBoxContainer.new()
	body.add_theme_constant_override("separation", 10)
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root.add_child(body)

	var sb_list := StyleBoxFlat.new()
	sb_list.bg_color = Color(0.01, 0.06, 0.08, 0.94)
	sb_list.set_border_width_all(1)
	sb_list.border_color = Color(0.20, 0.64, 0.74, 0.85)
	sb_list.set_corner_radius_all(4)
	sb_list.content_margin_left = 6
	sb_list.content_margin_top = 6
	sb_list.content_margin_right = 6
	sb_list.content_margin_bottom = 6

	_spawns_list = ItemList.new()
	_spawns_list.custom_minimum_size = Vector2(210, 240)
	_spawns_list.add_theme_stylebox_override("panel", sb_list)
	_spawns_list.add_theme_color_override("font_color", Color(0.76, 0.94, 0.96, 1.0))
	_spawns_list.add_theme_color_override("font_selected_color", Color(0.98, 0.88, 0.35, 1.0))
	_spawns_list.item_selected.connect(_on_spawn_selected)
	body.add_child(_spawns_list)

	_radar_draw = _SurveyRadarDraw.new()
	body.add_child(_radar_draw)

	var right_col := VBoxContainer.new()
	right_col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right_col.add_theme_constant_override("separation", 6)
	body.add_child(right_col)

	_stats_lbl = Label.new()
	_stats_lbl.add_theme_font_size_override("font_size", 10)
	_stats_lbl.add_theme_color_override("font_color", Color(0.96, 0.88, 0.55, 1.0))
	right_col.add_child(_stats_lbl)

	_stats_draw = _SurveyStatsDraw.new()
	_stats_draw.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right_col.add_child(_stats_draw)

	_harv_lbl = Label.new()
	_harv_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_harv_lbl.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_harv_lbl.add_theme_font_size_override("font_size", 10)
	_harv_lbl.add_theme_color_override("font_color", Color(0.72, 0.90, 0.95, 1.0))
	right_col.add_child(_harv_lbl)

	var btn_row := HBoxContainer.new()
	btn_row.add_theme_constant_override("separation", 8)
	root.add_child(btn_row)

	var ping_btn := Button.new()
	ping_btn.text = "◎  1. SONDER GISEMENT (RADAR)"
	ping_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_style_action_btn(ping_btn, Color(0.32, 0.88, 0.96, 0.95))
	ping_btn.pressed.connect(ping_selected_spawn)
	btn_row.add_child(ping_btn)

	var sample_btn := Button.new()
	sample_btn.text = "⛏  2. EXTRAIRE ÉCHANTILLON"
	sample_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_style_action_btn(sample_btn, Color(0.32, 0.92, 0.68, 0.95))
	sample_btn.pressed.connect(sample_selected_spawn)
	btn_row.add_child(sample_btn)

	var deploy_btn := Button.new()
	deploy_btn.text = "⚙  3. DÉPLOYER EXTRACTEUR"
	deploy_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_style_action_btn(deploy_btn, Color(0.95, 0.78, 0.28, 0.95))
	deploy_btn.pressed.connect(deploy_harvester_on_selected)
	btn_row.add_child(deploy_btn)


func _apply_local_fallback() -> void:
	_spawns = [
		{
			"spawn_id": "res_lh_copper_kovess",
			"spawn_name": "Cuivre Kovessien",
			"resource_class": "mineral_copper",
			"hotspot_x": 4795.0,
			"hotspot_z": -565.0,
			"peak_density": 94,
			"stats": {"oq": 860, "cd": 920, "pe": 640, "ma": 780, "sr": 710},
		},
		{
			"spawn_id": "res_lh_silica_oris",
			"spawn_name": "Silice d'Oris",
			"resource_class": "crystal_silica",
			"hotspot_x": 4842.0,
			"hotspot_z": -612.0,
			"peak_density": 89,
			"stats": {"oq": 910, "cd": 845, "pe": 880, "ma": 620, "sr": 890},
		},
	]
	_paint_all()


func apply_spawns_payload(payload: Dictionary) -> void:
	_ensure_ui()
	var arr: Variant = payload.get("spawns", [])
	if typeof(arr) == TYPE_ARRAY and not (arr as Array).is_empty():
		_spawns = (arr as Array).duplicate(true)
	_paint_all()


func refresh_spawns() -> void:
	_apply_runtime_cfg()
	if _http_spawns == null or not is_inside_tree():
		return
	var url := "%s/v1/survey/spawns" % sidecar_base_url.rstrip("/")
	if _http_spawns.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		_http_spawns.cancel_request()
	_http_spawns.request(url, [], HTTPClient.METHOD_GET)


func selected_spawn() -> Dictionary:
	if _spawns.is_empty():
		return {}
	var idx := clampi(_selected_idx, 0, _spawns.size() - 1)
	return _spawns[idx] if typeof(_spawns[idx]) == TYPE_DICTIONARY else {}


func ping_selected_spawn() -> void:
	var sp := selected_spawn()
	if sp.is_empty():
		return
	var sid := str(sp.get("spawn_id", ""))
	if _http_action != null and is_inside_tree():
		var url := "%s/v1/survey/ping" % sidecar_base_url.rstrip("/")
		var body := JSON.stringify({"player": player_id, "filter": sid, "x": player_pos_xz.x, "z": player_pos_xz.y})
		if _http_action.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
			_http_action.cancel_request()
		_http_action.request(url, PackedStringArray(["Content-Type: application/json"]), HTTPClient.METHOD_POST, body)


func sample_selected_spawn() -> void:
	var sp := selected_spawn()
	if sp.is_empty():
		return
	var sid := str(sp.get("spawn_id", ""))
	if _http_action != null and is_inside_tree():
		var url := "%s/v1/survey/sample" % sidecar_base_url.rstrip("/")
		var body := JSON.stringify({"player": player_id, "spawn_id": sid, "x": player_pos_xz.x, "z": player_pos_xz.y})
		if _http_action.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
			_http_action.cancel_request()
		_http_action.request(url, PackedStringArray(["Content-Type: application/json"]), HTTPClient.METHOD_POST, body)


func deploy_harvester_on_selected() -> void:
	var sp := selected_spawn()
	if sp.is_empty():
		return
	var sid := str(sp.get("spawn_id", ""))
	if _http_action != null and is_inside_tree():
		var url := "%s/v1/harvesters/deploy" % sidecar_base_url.rstrip("/")
		var body := JSON.stringify({"player": player_id, "spawn_id": sid, "x": player_pos_xz.x, "z": player_pos_xz.y})
		if _http_action.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
			_http_action.cancel_request()
		_http_action.request(url, PackedStringArray(["Content-Type: application/json"]), HTTPClient.METHOD_POST, body)


func _on_spawns_http_done(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS or code < 200 or code >= 300:
		return
	var parsed: Variant = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) == TYPE_DICTIONARY and bool((parsed as Dictionary).get("ok", false)):
		apply_spawns_payload(parsed as Dictionary)


func _on_action_http_done(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS or body.is_empty():
		return
	var parsed: Variant = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) != TYPE_DICTIONARY:
		return
	var d := parsed as Dictionary
	if bool(d.get("ok", false)):
		if d.has("readings"):
			var r_arr: Array = d.get("readings", [])
			if not r_arr.is_empty() and typeof(r_arr[0]) == TYPE_DICTIONARY:
				var r0: Dictionary = r_arr[0]
				_last_density_pct = int(r0.get("local_density_pct", 80))
				_last_dir = str(r0.get("direction", "HERE"))
				if _status_lbl:
					_status_lbl.text = "◎ Ping Radar : densité %d%% · relèvement %s" % [_last_density_pct, _last_dir]
		elif d.has("extracted_qty"):
			if _status_lbl:
				_status_lbl.text = "⛏ Échantillon extrait : +%dx %s (+%d XP)" % [
					int(d.get("extracted_qty", 1)),
					str(d.get("spawn_name", "")),
					int(d.get("xp_gained", 0))
				]
			resource_sampled.emit(d)
		elif d.has("harvester"):
			var h: Dictionary = d.get("harvester", {})
			_harvesters.append(h)
			if _status_lbl:
				_status_lbl.text = "⚙ Extracteur déployé : %s (BER %.1f)" % [str(h.get("harvester_id", "")), float(h.get("ber", 12.0))]
			harvester_deployed.emit(d)
		_paint_details()
	else:
		if _status_lbl:
			_status_lbl.text = "⚠ Action Survey refusée : %s" % str(d.get("error", code))


func _on_spawn_selected(idx: int) -> void:
	_selected_idx = idx
	_paint_details()


func _paint_all() -> void:
	if _spawns_list:
		_spawns_list.clear()
		for sp in _spawns:
			if typeof(sp) == TYPE_DICTIONARY:
				_spawns_list.add_item("◎ %s [%s]" % [str(sp.get("spawn_name", "?")), str(sp.get("resource_class", ""))])
		if _spawns_list.item_count > 0:
			_selected_idx = clampi(_selected_idx, 0, _spawns_list.item_count - 1)
			_spawns_list.select(_selected_idx)
	_paint_details()


func _paint_details() -> void:
	var sp := selected_spawn()
	if sp.is_empty():
		return
	var sname := str(sp.get("spawn_name", "?"))
	var rclass := str(sp.get("resource_class", "?"))
	var stats: Dictionary = sp.get("stats", {}) if typeof(sp.get("stats")) == TYPE_DICTIONARY else {}

	if _radar_draw:
		_radar_draw.update_radar(_last_density_pct, _last_dir, sname)

	if _stats_lbl:
		_stats_lbl.text = "ATTRIBUTS DE RESSOURCE — %s (%s)" % [sname.to_upper(), rclass]

	if _stats_draw:
		_stats_draw.set_stats(stats)

	if _harv_lbl:
		_harv_lbl.text = "◈ ÉPICENTRE : (%.0f, %.0f)  ·  PIC : %d%%\n◈ EXTRACTEURS ACTIFS DANS LE SECTEUR : %d" % [
			float(sp.get("hotspot_x", 0.0)),
			float(sp.get("hotspot_z", 0.0)),
			int(sp.get("peak_density", 90)),
			_harvesters.size()
		]
