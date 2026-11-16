# planet_map_panel.gd — Carte régionale Scrapaltai Ctrl+M (16 km × 16 km canon Core3/SWG)
extends Control
class_name PlanetMapPanel

const POI_PATH := "res://assets/maps/scrapaltai_pois.json"
const LOC_PATH := "res://assets/maps/locations_tree.json"
const MAP_CONFIG := "res://assets/maps/scrapaltai_map_config.json"
const PLANET_LORE_PATH := "res://assets/maps/scrapaltai_planet_map.json"
const HUB := Vector3(4749.0, 0.0, -737.0)
const _Projection3D2D = preload("res://scripts/projection.gd")
const _WaypointStore = preload("res://scripts/waypoint_store.gd")

const WORLD_MIN := -32000.0
const WORLD_MAX := 32000.0
const WORLD_SPAN := 64000.0

@export var camera_path: NodePath = NodePath("../../../Camera2D")
@export var player_controller_path: NodePath = NodePath("../../../PlayerController")

var _open: bool = false
var _pan: Vector2 = Vector2.ZERO
var _zoom: float = 1.0
var _dragging: bool = false
var _drag_start: Vector2 = Vector2.ZERO
var _pan_start: Vector2 = Vector2.ZERO
var _last_click_ms: int = 0

var _texture: Texture2D
var _pois: Array = []
var _locations: Array = []
var _waypoints: Array = []
var _hover_label: String = ""

var _settlements: Array = []
var _planet_display: String = "Scrapaltai"
var _show_grid: bool = false
var _game_hour: float = 12.0

@onready var _title: Label = $Panel/VBox/TitleLabel
@onready var _hint: Label = $Panel/VBox/HintLabel
@onready var _chrome: Control = $Panel

func _ready() -> void:
	_open = false
	visible = false
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_sync_chrome()
	_load_config()
	_load_texture()
	_load_data()
	if _title:
		_title.add_theme_color_override("font_color", Color(0.95, 0.88, 0.72, 1))
		_title.text = "Carte régionale — %s (64 km × 64 km)" % _planet_display
	if _hint:
		_hint.text = "Ctrl+M fermer · Molette zoom · Glisser déplacer · F centrer Lost Heaven · Shift+Clic waypoint · G grille"
		_hint.add_theme_color_override("font_color", Color(0.72, 0.62, 0.48, 1))


func _process(_delta: float) -> void:
	if _open:
		queue_redraw()

func reload_data() -> void:
	_load_config()
	_load_texture()
	_load_data()
	queue_redraw()

func is_open() -> bool:
	return _open

func open_map() -> void:
	_open = true
	visible = true
	mouse_filter = Control.MOUSE_FILTER_STOP
	_sync_chrome()
	_waypoints = _WaypointStore.load_all()
	_zoom = 1.0
	_pan = Vector2.ZERO
	queue_redraw()

func close_map() -> void:
	_open = false
	visible = false
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_sync_chrome()

func _sync_chrome() -> void:
	if _chrome:
		_chrome.visible = _open

func toggle_map() -> void:
	if _open:
		close_map()
	else:
		open_map()

func _focus_hub() -> void:
	var rect := _map_rect()
	_zoom = 1.6
	var local := _hub_local(rect)
	_pan = rect.size * 0.5 - local * _zoom
	queue_redraw()

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_M and event.ctrl_pressed:
			toggle_map()
			get_viewport().set_input_as_handled()
			return
	if not _open:
		return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_F:
			_focus_hub()
			get_viewport().set_input_as_handled()
		elif event.keycode == KEY_G:
			_show_grid = not _show_grid
			queue_redraw()
			get_viewport().set_input_as_handled()

func _gui_input(event: InputEvent) -> void:
	if not _open:
		return
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_WHEEL_UP and mb.pressed:
			_zoom_at(mb.position, 1.15)
			accept_event()
		elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN and mb.pressed:
			_zoom_at(mb.position, 1.0 / 1.15)
			accept_event()
		elif mb.button_index == MOUSE_BUTTON_LEFT:
			if mb.pressed:
				if mb.shift_pressed:
					var core3 := _screen_to_core3(mb.position)
					var res: Dictionary = _WaypointStore.add_waypoint("", core3.x, core3.z)
					if res.get("ok"):
						_waypoints = _WaypointStore.load_all()
						queue_redraw()
				else:
					var now := Time.get_ticks_msec()
					if now - _last_click_ms < 350:
						_go_to_hub()
					_last_click_ms = now
				_dragging = true
				_drag_start = mb.position
				_pan_start = _pan
			else:
				_dragging = false
			accept_event()
		elif mb.button_index == MOUSE_BUTTON_RIGHT and mb.pressed:
			var hit := _pick_waypoint(mb.position)
			if hit != "":
				_WaypointStore.remove_waypoint(hit)
				_waypoints = _WaypointStore.load_all()
				queue_redraw()
			accept_event()
	elif event is InputEventMouseMotion:
		var mm := event as InputEventMouseMotion
		if _dragging:
			_pan = _pan_start + (mm.position - _drag_start)
			queue_redraw()
		else:
			_hover_label = _pick_label(mm.position)
			queue_redraw()

func _zoom_at(screen_pos: Vector2, factor: float) -> void:
	var rect := _map_rect()
	var before := (screen_pos - rect.position - _pan) / _zoom
	_zoom = clampf(_zoom * factor, 0.6, 5.0)
	_pan = screen_pos - rect.position - before * _zoom
	queue_redraw()

func _load_config() -> void:
	if not FileAccess.file_exists(MAP_CONFIG):
		return
	var f := FileAccess.open(MAP_CONFIG, FileAccess.READ)
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if raw is Dictionary:
		var cfg: Dictionary = raw
		var disp := str(cfg.get("display_name", "")).strip_edges()
		if disp != "":
			_planet_display = disp

func _load_texture() -> void:
	for path in [
		"res://assets/maps/scrapaltai_planet.png",
		"res://assets/maps/scrapaltai_planet.jpg",
	]:
		if ResourceLoader.exists(path) or FileAccess.file_exists(path):
			_texture = load(path) as Texture2D
			if _texture:
				return

func _load_data() -> void:
	_pois = _read_array(POI_PATH, "pois")
	_locations = _read_array(LOC_PATH, "locations")
	_waypoints = _WaypointStore.load_all()
	_load_lore_map()

func _load_lore_map() -> void:
	_settlements.clear()
	var path := PLANET_LORE_PATH
	if not FileAccess.file_exists(path):
		return
	var f := FileAccess.open(path, FileAccess.READ)
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if not raw is Dictionary:
		return
	var doc: Dictionary = raw
	_planet_display = str(doc.get("display_name", _planet_display))
	var arr: Variant = doc.get("settlements", [])
	_settlements = arr if arr is Array else []

func _read_array(path: String, key: String) -> Array:
	if not FileAccess.file_exists(path):
		return []
	var f := FileAccess.open(path, FileAccess.READ)
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if raw is Dictionary:
		var arr: Variant = (raw as Dictionary).get(key, [])
		return arr if arr is Array else []
	return []

func _map_rect() -> Rect2:
	var vp := get_viewport_rect().size
	var margin := 24.0
	var top := 64.0
	var avail_w := vp.x - margin * 2.0
	var avail_h := vp.y - top - margin - 24.0
	var side := minf(avail_w, avail_h)
	var x := margin + (avail_w - side) * 0.5
	var y := top + (avail_h - side) * 0.5
	return Rect2(x, y, side, side)

func _core3_to_local(core3: Vector3, rect: Rect2) -> Vector2:
	var u := (core3.x - WORLD_MIN) / WORLD_SPAN
	var v := (core3.z - WORLD_MIN) / WORLD_SPAN
	return Vector2(
		clampf(u, 0.0, 1.0) * rect.size.x,
		(1.0 - clampf(v, 0.0, 1.0)) * rect.size.y
	)

func _core3_to_screen(core3: Vector3) -> Vector2:
	var rect := _map_rect()
	var local := _core3_to_local(core3, rect)
	return rect.position + _pan + local * _zoom

func _screen_to_core3(screen_pos: Vector2) -> Vector3:
	var rect := _map_rect()
	var local := (screen_pos - rect.position - _pan) / _zoom
	var u := clampf(local.x / maxf(rect.size.x, 1.0), 0.0, 1.0)
	var v := clampf(1.0 - (local.y / maxf(rect.size.y, 1.0)), 0.0, 1.0)
	return Vector3(
		WORLD_MIN + u * WORLD_SPAN,
		0.0,
		WORLD_MIN + v * WORLD_SPAN
	)

func _hub_local(rect: Rect2) -> Vector2:
	return _core3_to_local(HUB, rect)

func _settlement_by_id(settlement_id: String) -> Dictionary:
	for item: Variant in _settlements:
		if item is Dictionary and str((item as Dictionary).get("id", "")) == settlement_id:
			return item as Dictionary
	return {}

func _get_player_xz() -> Vector2:
	var main_node := get_node_or_null("../../..")
	if main_node and main_node.has_method("_player_world_xz"):
		var p: Vector2 = main_node._player_world_xz()
		if p != Vector2.INF and absf(p.x) <= 12000.0 and absf(p.y) <= 12000.0:
			return p
	var pc: Node = get_node_or_null(player_controller_path)
	if pc and pc.has_method("get_player_id"):
		var pid: int = int(pc.call("get_player_id"))
		var em: Node = pc.get("_em") if "_em" in pc else null
		if pid != 0 and em and em.has_method("get_entity"):
			var e: Node = em.call("get_entity", pid)
			if e and "core3_pos" in e:
				var c3: Vector3 = e.core3_pos
				if absf(c3.x) <= 12000.0 and absf(c3.z) <= 12000.0:
					return Vector2(c3.x, c3.z)
	var cam := get_node_or_null(camera_path) as Camera2D
	if cam:
		var c3_cam := _Projection3D2D.from_screen(cam.position)
		if absf(c3_cam.x) <= 12000.0 and absf(c3_cam.z) <= 12000.0:
			return Vector2(c3_cam.x, c3_cam.z)
	return Vector2(HUB.x, HUB.z)

func _get_player_display_name() -> String:
	var main_node := get_node_or_null("../../..")
	if main_node and "_local_character_name" in main_node:
		var n: String = str(main_node._local_character_name).strip_edges()
		if not n.is_empty():
			return n
	return "Teome"

func _pick_waypoint(screen_pos: Vector2) -> String:
	for item: Variant in _waypoints:
		if not item is Dictionary:
			continue
		var wp: Dictionary = item
		var p := _core3_to_screen(Vector3(float(wp.get("x", 0)), 0, float(wp.get("z", 0))))
		if p.distance_to(screen_pos) <= 12.0:
			return str(wp.get("id", ""))
	return ""

func _pick_label(screen_pos: Vector2) -> String:
	for item: Variant in _settlements:
		if not item is Dictionary:
			continue
		var s: Dictionary = item
		var sx := float(s.get("x", 0.0))
		var sz := float(s.get("z", 0.0))
		var pos := _core3_to_screen(Vector3(sx, 0.0, sz))
		if pos.distance_to(screen_pos) <= 22.0:
			var lbl := str(s.get("label", s.get("id", "")))
			var role := str(s.get("role", ""))
			var role_desc := " (Capitale)" if role == "capital" else (" (Hub Joueur)" if role == "hub_joueur" else "")
			return "%s%s [X: %.0f, Z: %.0f]" % [lbl, role_desc, sx, sz]
	for item: Variant in _waypoints:
		if not item is Dictionary:
			continue
		var wp: Dictionary = item
		var wx := float(wp.get("x", 0))
		var wz := float(wp.get("z", 0))
		var p := _core3_to_screen(Vector3(wx, 0.0, wz))
		if p.distance_to(screen_pos) <= 12.0:
			var w_lbl := str(wp.get("label", "Waypoint"))
			return "Waypoint: %s [X: %.0f, Z: %.0f]" % [w_lbl, wx, wz]
	return ""

func _go_to_hub() -> void:
	var pc: Node = get_node_or_null(player_controller_path)
	if pc and pc.enabled:
		pc.request_move_to(HUB.x, HUB.z)
	else:
		var cam := get_node_or_null(camera_path) as Camera2D
		if cam:
			cam.position = _Projection3D2D.to_screen(HUB)

func _draw() -> void:
	if not _open:
		return
	draw_rect(get_viewport_rect(), Color(0.04, 0.03, 0.02, 0.94))
	var rect := _map_rect()
	draw_rect(rect, Color(0.12, 0.09, 0.06, 1.0))

	# Texture de carte régionale (clippée dans le rectangle)
	if _texture and _texture.get_size().x > 0.0:
		draw_set_transform(rect.position + _pan, 0.0, Vector2(_zoom, _zoom))
		draw_texture_rect(_texture, Rect2(Vector2.ZERO, rect.size), false, Color(1, 1, 1, 0.98))
		_draw_solar_terminator(rect)
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


	# Cadre doré autour de la carte
	draw_rect(rect, Color(0.78, 0.60, 0.35, 0.9), false, 2.5)

	# Grille facultative (touche G)
	if _show_grid:
		_draw_grid_overlay(rect)

	# Waypoints personnalisés du joueur
	for item: Variant in _waypoints:
		if not item is Dictionary:
			continue
		var wp: Dictionary = item
		var pos := _core3_to_screen(Vector3(float(wp.get("x", 0)), 0, float(wp.get("z", 0))))
		if rect.has_point(pos):
			draw_circle(pos, 6.0, Color(1.0, 0.35, 0.85, 1.0))
			draw_arc(pos, 9.0, 0.0, TAU, 16, Color(1.0, 0.8, 0.95, 0.8), 1.5)
			var lbl := str(wp.get("label", ""))
			if lbl != "":
				draw_string(ThemeDB.fallback_font, pos + Vector2(10, -6), lbl, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(1, 1, 1, 0.95))

	# Radar joueur en direct (pulsant, vert émeraude)
	var p_xz := _get_player_xz()
	if p_xz != Vector2.INF:
		var p_pos := _core3_to_screen(Vector3(p_xz.x, 0.0, p_xz.y))
		if rect.has_point(p_pos):
			var pulse := (sin(float(Time.get_ticks_msec()) * 0.007) + 1.0) * 0.5
			var halo_r := 11.0 + pulse * 6.0
			draw_circle(p_pos, halo_r, Color(0.12, 0.95, 0.45, 0.25))
			draw_arc(p_pos, halo_r, 0.0, TAU, 28, Color(0.24, 1.0, 0.55, 0.85), 1.8)
			draw_line(p_pos + Vector2(-halo_r - 3, 0), p_pos + Vector2(halo_r + 3, 0), Color(0.24, 1.0, 0.55, 0.6), 1.0)
			draw_line(p_pos + Vector2(0, -halo_r - 3), p_pos + Vector2(0, halo_r + 3), Color(0.24, 1.0, 0.55, 0.6), 1.0)
			draw_circle(p_pos, 5.0, Color(0.15, 1.0, 0.45, 1.0))
			draw_circle(p_pos, 2.0, Color(1.0, 1.0, 1.0, 1.0))
			var p_name := _get_player_display_name()
			var p_lbl := "● %s (Vous) [%.0f, %.0f]" % [p_name, p_xz.x, p_xz.y]
			var font := ThemeDB.fallback_font
			if font:
				var fsize := 11
				var str_w := font.get_string_size(p_lbl, HORIZONTAL_ALIGNMENT_LEFT, -1, fsize).x
				var tag_bg := Rect2(p_pos.x + 12.0, p_pos.y - 14.0, str_w + 10.0, 18.0)
				draw_rect(tag_bg, Color(0.04, 0.16, 0.10, 0.92), true)
				draw_rect(tag_bg, Color(0.22, 0.95, 0.50, 0.90), false, 1.2)
				draw_string(font, p_pos + Vector2(17, -1), p_lbl, HORIZONTAL_ALIGNMENT_LEFT, -1, fsize, Color(0.85, 1.0, 0.88, 1.0))

	# Footer / barre d'information en bas
	var footer := _hover_label
	if footer == "":
		if p_xz != Vector2.INF:
			footer = "%s · Position actuelle : X %.0f, Z %.0f · 64 000 m × 64 000 m (4 096 km²) · Molette zoom · F Lost Heaven · Shift+Clic waypoint" % [_planet_display, p_xz.x, p_xz.y]
		else:
			footer = "%s · Mégalopole de Zalem, Lost Heaven & Grand Rift · 64 000 m × 64 000 m (4 096 km²)" % _planet_display
	draw_string(
		ThemeDB.fallback_font,
		Vector2(rect.position.x + 8.0, get_viewport_rect().size.y - 14.0),
		footer,
		HORIZONTAL_ALIGNMENT_LEFT,
		-1,
		13,
		Color(0.95, 0.85, 0.65, 1)
	)

func _draw_grid_overlay(rect: Rect2) -> void:
	draw_set_transform(rect.position + _pan, 0.0, Vector2(_zoom, _zoom))
	var col_line := Color(0.95, 0.82, 0.45, 0.25)
	for m in range(-28000, 29000, 8000):
		var u := (float(m) - WORLD_MIN) / WORLD_SPAN
		var px := u * rect.size.x
		var py := (1.0 - u) * rect.size.y
		draw_line(Vector2(px, 0.0), Vector2(px, rect.size.y), col_line, 1.0)
		draw_line(Vector2(0.0, py), Vector2(rect.size.x, py), col_line, 1.0)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

func set_world_clock(wc: Dictionary) -> void:
	_game_hour = float(wc.get("game_hour", _game_hour))
	if _open:
		queue_redraw()

func _current_game_hour() -> float:
	var wm: Node = get_node_or_null("../../WorldMap")
	if wm and "_atmosphere" in wm and wm._atmosphere != null:
		return float(wm._atmosphere._game_hour)
	return _game_hour

func _draw_solar_terminator(rect: Rect2) -> void:
	var gh := _current_game_hour()
	var u_midnight: float = fposmod(0.5 + (0.0 - gh) / 24.0, 1.0)
	var u_noon: float = fposmod(0.5 + (12.0 - gh) / 24.0, 1.0)

	var cols := 128
	var rows := 48
	var cell_w := rect.size.x / float(cols)
	var cell_h := rect.size.y / float(rows)

	# Voile d'ombre lissé haute résolution (Solar Terminator sans effet de damier)
	for r in range(rows):
		var v := (float(r) + 0.5) / float(rows)
		var py := float(r) * cell_h
		var curve_offset := sin((v - 0.5) * PI) * 0.075
		var u_center: float = fposmod(u_midnight + curve_offset, 1.0)

		for c in range(cols):
			var u := (float(c) + 0.5) / float(cols)
			var px := float(c) * cell_w
			var dist: float = absf(fposmod(u - u_center + 0.5, 1.0) - 0.5)

			if dist < 0.20:
				# Nuit noire profonde
				draw_rect(Rect2(px, py, cell_w + 0.5, cell_h + 0.5), Color(0.04, 0.06, 0.16, 0.52), true)
			elif dist < 0.28:
				# Dégradé crépusculaire / aube fluide
				var t := (dist - 0.20) / 0.08
				var dusk_alpha := (1.0 - t) * 0.52
				var col := Color(0.12, 0.10, 0.20, dusk_alpha)
				draw_rect(Rect2(px, py, cell_w + 0.5, cell_h + 0.5), col, true)

	# Icône du Soleil au zénith (Midi solaire)
	var sun_px := u_noon * rect.size.x
	var sun_py := rect.size.y * 0.5
	draw_circle(Vector2(sun_px, sun_py), 15.0, Color(1.0, 0.90, 0.35, 0.25))
	draw_circle(Vector2(sun_px, sun_py), 8.5, Color(1.0, 0.85, 0.20, 0.95))
	draw_circle(Vector2(sun_px, sun_py), 5.5, Color(1.0, 1.0, 0.85, 1.0))
	for ray in range(8):
		var a := (float(ray) / 8.0) * TAU
		var dir := Vector2(cos(a), sin(a))
		draw_line(Vector2(sun_px, sun_py) + dir * 11.0, Vector2(sun_px, sun_py) + dir * 17.0, Color(1.0, 0.85, 0.30, 0.85), 1.8)

	# Icône du Croissant de Lune au minuit solaire
	var moon_px := u_midnight * rect.size.x
	var moon_py := rect.size.y * 0.5
	draw_circle(Vector2(moon_px, moon_py), 7.5, Color(0.85, 0.92, 1.0, 0.95))
	draw_circle(Vector2(moon_px + 3.0, moon_py - 1.5), 6.5, Color(0.05, 0.07, 0.18, 0.98))
