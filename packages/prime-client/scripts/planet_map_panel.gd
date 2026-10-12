# planet_map_panel.gd — Carte planétaire Scrapaltai Ctrl+M (lore 12×4 + shard LH)
extends Control
class_name PlanetMapPanel

const POI_PATH := "res://assets/maps/scrapaltai_pois.json"
const LOC_PATH := "res://assets/maps/locations_tree.json"
const MAP_CONFIG := "res://assets/maps/scrapaltai_map_config.json"
const PLANET_LORE_PATH := "res://assets/maps/scrapaltai_planet_map.json"
const HUB := Vector3(4749.0, 0.0, -737.0)

@export var camera_path: NodePath = NodePath("../../../Camera2D")
@export var player_controller_path: NodePath = NodePath("../../../PlayerController")

var _open: bool = false
var _pan: Vector2 = Vector2.ZERO
var _zoom: float = 1.0
var _half_size: float = 6500.0
var _dragging: bool = false
var _drag_start: Vector2 = Vector2.ZERO
var _pan_start: Vector2 = Vector2.ZERO
var _last_click_ms: int = 0

var _texture: Texture2D
var _pois: Array = []
var _locations: Array = []
var _waypoints: Array = []
var _hover_label: String = ""

var _grid_cols: int = 12
var _grid_rows: int = 4
var _settlements: Array = []
var _planet_display: String = "Scrapaltai"
var _show_grid: bool = true
var _align_inset := Vector4(0.07, 0.11, 0.07, 0.20) # left, top, right, bottom (légende bas carte)

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
		_title.text = "Carte planétaire — %s" % _planet_display
	if _hint:
		_hint.text = "Ctrl+M fermer · molette zoom · double-clic Lost Heaven · Shift+clic waypoint · F centrer LH · G grille"
		_hint.add_theme_color_override("font_color", Color(0.72, 0.62, 0.48, 1))

func reload_data() -> void:
	_load_config()
	_load_data()
	queue_redraw()

func is_open() -> bool:
	return _open

func open_map() -> void:
	_open = true
	visible = true
	mouse_filter = Control.MOUSE_FILTER_STOP
	_sync_chrome()
	_waypoints = WaypointStore.load_all()
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
	_zoom = 1.7
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
			_zoom_at(mb.position, 1.12)
			accept_event()
		elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN and mb.pressed:
			_zoom_at(mb.position, 1.0 / 1.12)
			accept_event()
		elif mb.button_index == MOUSE_BUTTON_LEFT:
			if mb.pressed:
				if mb.shift_pressed:
					var core3 := _screen_to_core3(mb.position)
					var res := WaypointStore.add_waypoint("", core3.x, core3.z)
					if res.get("ok"):
						_waypoints = WaypointStore.load_all()
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
				WaypointStore.remove_waypoint(hit)
				_waypoints = WaypointStore.load_all()
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
	_zoom = clampf(_zoom * factor, 0.35, 4.0)
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
		_half_size = float(cfg.get("half_size", _half_size))
		var disp := str(cfg.get("display_name", "")).strip_edges()
		if disp != "":
			_planet_display = disp

func _load_texture() -> void:
	_texture = MapTextureLoader.load_texture("planet_map")
	if _texture:
		return
	for path in [
		"res://assets/maps/scrapaltai_planet.jpg",
		"res://assets/maps/scrapaltai_planet.png",
		"res://assets/maps/scrapaltai_shard_legacy.png",
	]:
		if ResourceLoader.exists(path) or FileAccess.file_exists(path):
			_texture = load(path) as Texture2D
			if _texture:
				return

func _load_data() -> void:
	_pois = _read_array(POI_PATH, "pois")
	_locations = _read_array(LOC_PATH, "locations")
	_waypoints = WaypointStore.load_all()
	_load_lore_map()

func _load_lore_map() -> void:
	_settlements.clear()
	var path := PLANET_LORE_PATH
	if FileAccess.file_exists(MAP_CONFIG):
		var fcfg := FileAccess.open(MAP_CONFIG, FileAccess.READ)
		var cfg_raw: Variant = JSON.parse_string(fcfg.get_as_text())
		fcfg.close()
		if cfg_raw is Dictionary:
			var explicit := str((cfg_raw as Dictionary).get("planet_lore_map", "")).strip_edges()
			if explicit != "":
				path = explicit
	if not FileAccess.file_exists(path):
		return
	var f := FileAccess.open(path, FileAccess.READ)
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if not raw is Dictionary:
		return
	var doc: Dictionary = raw
	_planet_display = str(doc.get("display_name", _planet_display))
	var grid: Variant = doc.get("grid", {})
	if grid is Dictionary:
		_grid_cols = int((grid as Dictionary).get("columns", 12))
		_grid_rows = int((grid as Dictionary).get("rows", 4))
		var align: Variant = (grid as Dictionary).get("map_align", null)
		if align is Dictionary:
			var a: Dictionary = align
			_align_inset = Vector4(
				float(a.get("inset_left", _align_inset.x)),
				float(a.get("inset_top", _align_inset.y)),
				float(a.get("inset_right", _align_inset.z)),
				float(a.get("inset_bottom", _align_inset.w))
			)
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
	var margin := 40.0
	var top := 68.0
	return Rect2(margin, top, vp.x - margin * 2.0, vp.y - top - margin - 28.0)

func _inner_rect(rect: Rect2) -> Rect2:
	var l := rect.size.x * _align_inset.x
	var t := rect.size.y * _align_inset.y
	var r := rect.size.x * _align_inset.z
	var b := rect.size.y * _align_inset.w
	return Rect2(l, t, rect.size.x - l - r, rect.size.y - t - b)

func _uv_to_local(u: float, v: float, rect: Rect2) -> Vector2:
	# u,v ∈ [0,1] — origine bas-gauche de la zone cartographique (hors bordure steampunk).
	var inner := _inner_rect(rect)
	return Vector2(
		inner.position.x + clampf(u, 0.0, 1.0) * inner.size.x,
		inner.position.y + (1.0 - clampf(v, 0.0, 1.0)) * inner.size.y
	)

func _grid_to_local(col: int, row: int, rect: Rect2) -> Vector2:
	var inner := _inner_rect(rect)
	var cols := maxi(_grid_cols, 1)
	var rows := maxi(_grid_rows, 1)
	var u := (float(col) - 0.5) / float(cols)
	var v := (float(row) - 0.5) / float(rows)
	return _uv_to_local(u, v, rect)

func _settlement_by_id(settlement_id: String) -> Dictionary:
	for item: Variant in _settlements:
		if item is Dictionary and str((item as Dictionary).get("id", "")) == settlement_id:
			return item as Dictionary
	return {}

func _settlement_local(item: Dictionary, rect: Rect2) -> Vector2:
	var uv: Variant = item.get("map_uv", null)
	if uv is Dictionary:
		var d: Dictionary = uv
		return _uv_to_local(float(d.get("u", 0.5)), float(d.get("v", 0.5)), rect)
	var g := _settlement_grid(item)
	return _grid_to_local(g.x, g.y, rect)

func _hub_local(rect: Rect2) -> Vector2:
	var lh := _settlement_by_id("city:lost_heaven")
	if not lh.is_empty():
		return _settlement_local(lh, rect)
	return _grid_to_local(8, 2, rect)

func _grid_to_screen(col: int, row: int) -> Vector2:
	var rect := _map_rect()
	var local := _grid_to_local(col, row, rect)
	return rect.position + _pan + local * _zoom

func _settlement_grid(item: Dictionary) -> Vector2i:
	var g: Variant = item.get("grid", {})
	if g is Dictionary:
		return Vector2i(int((g as Dictionary).get("col", 1)), int((g as Dictionary).get("row", 1)))
	return Vector2i(1, 1)

func _core3_to_local(core3: Vector3, rect: Rect2) -> Vector2:
	var local_lh := _hub_local(rect)
	var nx := core3.x / _half_size
	var nz := -core3.z / _half_size
	var inner := _inner_rect(rect)
	var cell := Vector2(inner.size.x / float(maxi(_grid_cols, 1)), inner.size.y / float(maxi(_grid_rows, 1)))
	return local_lh + Vector2(nx * cell.x * 0.22, nz * cell.y * 0.22)

func _screen_to_core3(screen_pos: Vector2) -> Vector3:
	var rect := _map_rect()
	var local := (screen_pos - rect.position - _pan) / _zoom
	var lh := _hub_local(rect)
	var inner := _inner_rect(rect)
	var cell := Vector2(inner.size.x / float(maxi(_grid_cols, 1)), inner.size.y / float(maxi(_grid_rows, 1)))
	var dx := (local.x - lh.x) / maxf(cell.x * 0.22, 1.0)
	var dy := (local.y - lh.y) / maxf(cell.y * 0.22, 1.0)
	return Vector3(clampf(dx, -1.0, 1.0) * _half_size, 0.0, -clampf(dy, -1.0, 1.0) * _half_size)

func _core3_to_screen(core3: Vector3) -> Vector2:
	var rect := _map_rect()
	var local := _core3_to_local(core3, rect)
	return rect.position + _pan + local * _zoom

func _pick_waypoint(screen_pos: Vector2) -> String:
	for item: Variant in _waypoints:
		if not item is Dictionary:
			continue
		var wp: Dictionary = item
		var p := _core3_to_screen(Vector3(float(wp.get("x", 0)), 0, float(wp.get("z", 0))))
		if p.distance_to(screen_pos) <= 10.0:
			return str(wp.get("id", ""))
	return ""

func _pick_label(screen_pos: Vector2) -> String:
	for item: Variant in _settlements:
		if not item is Dictionary:
			continue
		var s: Dictionary = item
		var g := _settlement_grid(s)
		var pos := _settlement_local(s, _map_rect())
		if pos.distance_to(screen_pos) <= 18.0:
			var role := str(s.get("role", ""))
			var extra := " — capitale" if role == "capital" else " — hub joueur"
			return str(s.get("label", s.get("id", ""))) + extra
	for item: Variant in _pois:
		if not item is Dictionary:
			continue
		var p: Dictionary = item
		if bool(p.get("deprecated", false)):
			continue
		if str(p.get("kind", "")) != "hub":
			continue
		var pos := _hub_local(_map_rect())
		pos = _map_rect().position + _pan + pos * _zoom
		if pos.distance_to(screen_pos) <= 16.0:
			return str(p.get("label", "Lost Heaven"))
	return ""

func _go_to_hub() -> void:
	var pc := get_node_or_null(player_controller_path) as PlayerController
	if pc and pc.enabled:
		pc.request_move_to(HUB.x, HUB.z)
	else:
		var cam := get_node_or_null(camera_path) as Camera2D
		if cam:
			cam.position = Projection3D2D.to_screen(HUB)

func _draw() -> void:
	if not _open:
		return
	draw_rect(get_viewport_rect(), Color(0.05, 0.04, 0.03, 0.94))
	var rect := _map_rect()
	draw_rect(rect, Color(0.10, 0.08, 0.06, 0.98))
	draw_rect(rect, Color(0.72, 0.52, 0.28, 0.75), false, 2.0)

	if _texture and _texture.get_size().x > 0.0:
		draw_set_transform(rect.position + _pan, 0.0, Vector2(_zoom, _zoom))
		draw_texture_rect(_texture, Rect2(Vector2.ZERO, rect.size), false, Color(1, 1, 1, 0.96))
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

	if _show_grid:
		_draw_grid(rect)

	for item: Variant in _settlements:
		if not item is Dictionary:
			continue
		_draw_settlement(item as Dictionary)

	for item: Variant in _waypoints:
		if not item is Dictionary:
			continue
		var wp: Dictionary = item
		var pos := _core3_to_screen(Vector3(float(wp.get("x", 0)), 0, float(wp.get("z", 0))))
		draw_circle(pos, 6.0, Color(1.0, 0.45, 0.85, 1.0))
		var lbl := str(wp.get("label", ""))
		if lbl != "":
			draw_string(ThemeDB.fallback_font, pos + Vector2(8, -8), lbl, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(1, 1, 1, 0.95))

	var footer := _hover_label if _hover_label != "" else "%s · Zalem (capitale) · Lost Heaven (petite ville, hub)" % _planet_display
	draw_string(
		ThemeDB.fallback_font,
		Vector2(rect.position.x + 8.0, get_viewport_rect().size.y - 18.0),
		footer,
		HORIZONTAL_ALIGNMENT_LEFT,
		-1,
		14,
		Color(0.92, 0.82, 0.62, 1)
	)

func _draw_grid(rect: Rect2) -> void:
	var inner := _inner_rect(rect)
	var cols := maxi(_grid_cols, 1)
	var rows := maxi(_grid_rows, 1)
	draw_set_transform(rect.position + _pan, 0.0, Vector2(_zoom, _zoom))
	var col_line := Color(0.95, 0.82, 0.45, 0.22)
	var row_line := Color(0.95, 0.82, 0.45, 0.18)
	for c in range(cols + 1):
		var x := inner.position.x + (float(c) / float(cols)) * inner.size.x
		draw_line(Vector2(x, inner.position.y), Vector2(x, inner.end.y), col_line, 1.0)
	for r in range(rows + 1):
		var y := inner.position.y + (float(r) / float(rows)) * inner.size.y
		draw_line(Vector2(inner.position.x, y), Vector2(inner.end.x, y), row_line, 1.0)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

func _draw_settlement(s: Dictionary) -> void:
	var rect := _map_rect()
	var pos := _map_rect().position + _pan + _settlement_local(s, rect) * _zoom
	var role := str(s.get("role", ""))
	var lbl := str(s.get("label", ""))
	if role == "capital":
		draw_circle(pos, 11.0, Color(0.95, 0.78, 0.22, 0.95))
		draw_arc(pos, 16.0, 0.0, TAU, 24, Color(1.0, 0.88, 0.4, 0.9), 2.0)
		if lbl != "":
			draw_string(
				ThemeDB.fallback_font,
				pos + Vector2(18, 4),
				"%s — capitale" % lbl,
				HORIZONTAL_ALIGNMENT_LEFT,
				-1,
				14,
				Color(1.0, 0.92, 0.55, 0.98)
			)
	elif role == "hub_joueur":
		draw_circle(pos, 7.0, Color(0.35, 0.85, 0.55, 0.95))
		draw_arc(pos, 12.0, 0.0, TAU, 20, Color(0.55, 0.95, 0.7, 0.9), 1.6)
		if lbl != "":
			draw_string(
				ThemeDB.fallback_font,
				pos + Vector2(14, 4),
				"%s — petite ville" % lbl,
				HORIZONTAL_ALIGNMENT_LEFT,
				-1,
				13,
				Color(0.85, 0.98, 0.88, 0.95)
			)
	else:
		draw_circle(pos, 5.0, Color(0.85, 0.65, 0.35, 0.9))
		if lbl != "":
			draw_string(ThemeDB.fallback_font, pos + Vector2(10, 4), lbl, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(0.96, 0.90, 0.78, 0.9))
