# minimap_hud.gd — Minimap HUD coin écran (M9b, style SWG)
extends Control
class_name MinimapHud

const CONFIG_PATH := "res://config/minimap_config.json"
const POI_PATH := "res://assets/maps/tatooine_pois.json"
const MAP_CONFIG_PATH := "res://assets/maps/tatooine_map_config.json"

@export var camera_path: NodePath = NodePath("../../../Camera2D")
@export var entity_manager_path: NodePath = NodePath("../../../EntityManager")
@export var player_controller_path: NodePath = NodePath("../../../PlayerController")

var _size_px: float = 180.0
var _view_radius_m: float = 420.0
var _show_poi: bool = true
var _show_entities: bool = true
var _essential_poi_only: bool = true
var _click_pan: bool = true
var _visible_hud: bool = true
var _show_coords: bool = true
var _show_altitude: bool = true
var _coord_compact: bool = true
var _coord_strip_h: float = 22.0

var _half_size: float = 6500.0
var _coord_label: Label = null
var _planet_texture: Texture2D
var _pois: Array = []
var _camera: Camera2D
var _entity_manager: EntityManager
var _player_controller: PlayerController

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	_load_config()
	_load_map_meta()
	_load_pois()
	_load_planet_texture()
	_resolve_refs()
	_setup_coord_label()
	_apply_layout_size()
	queue_redraw()

func _setup_coord_label() -> void:
	if _coord_label != null:
		return
	_coord_label = Label.new()
	_coord_label.name = "CoordLabel"
	_coord_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_coord_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_coord_label.add_theme_font_size_override("font_size", 11)
	_coord_label.add_theme_color_override("font_color", Color(0.82, 0.88, 0.96, 0.98))
	add_child(_coord_label)

func _apply_layout_size() -> void:
	var total_h := _size_px + (_coord_strip_h if _show_coords else 0.0)
	custom_minimum_size = Vector2(_size_px, total_h)
	size = custom_minimum_size
	if _coord_label:
		_coord_label.visible = _show_coords
		_coord_label.position = Vector2(0.0, _size_px + 1.0)
		_coord_label.size = Vector2(_size_px, _coord_strip_h - 1.0)

func _resolve_refs() -> void:
	_camera = get_node_or_null(camera_path) as Camera2D
	_entity_manager = get_node_or_null(entity_manager_path) as EntityManager
	_player_controller = get_node_or_null(player_controller_path) as PlayerController

func _load_config() -> void:
	if not FileAccess.file_exists(CONFIG_PATH):
		return
	var f := FileAccess.open(CONFIG_PATH, FileAccess.READ)
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if not raw is Dictionary:
		return
	var cfg: Dictionary = raw
	_size_px = float(cfg.get("size_px", _size_px))
	_view_radius_m = float(cfg.get("view_radius_m", _view_radius_m))
	_show_poi = bool(cfg.get("show_poi", _show_poi))
	_show_entities = bool(cfg.get("show_entities", _show_entities))
	_essential_poi_only = bool(cfg.get("show_essential_poi_only", _essential_poi_only))
	_click_pan = bool(cfg.get("click_pan_camera", _click_pan))
	_show_coords = bool(cfg.get("show_coordinates", _show_coords))
	_coord_strip_h = float(cfg.get("coord_strip_px", _coord_strip_h))
	var coords_cfg: Variant = cfg.get("coordinates", null)
	if coords_cfg is Dictionary:
		var cc: Dictionary = coords_cfg
		_show_altitude = bool(cc.get("show_altitude", _show_altitude))
		_coord_compact = bool(cc.get("compact", _coord_compact))
	_apply_layout_size()

func _load_map_meta() -> void:
	if not FileAccess.file_exists(MAP_CONFIG_PATH):
		return
	var f := FileAccess.open(MAP_CONFIG_PATH, FileAccess.READ)
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if raw is Dictionary:
		_half_size = float((raw as Dictionary).get("half_size", _half_size))

func _load_pois() -> void:
	_pois.clear()
	if not FileAccess.file_exists(POI_PATH):
		return
	var f := FileAccess.open(POI_PATH, FileAccess.READ)
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if raw is Dictionary:
		var arr: Variant = (raw as Dictionary).get("pois", [])
		_pois = arr if arr is Array else []

func _load_planet_texture() -> void:
	for path in ["res://assets/maps/tatooine.png", "res://assets/maps/tatooine.svg"]:
		if ResourceLoader.exists(path):
			_planet_texture = load(path) as Texture2D
			if _planet_texture:
				return

func reload_data() -> void:
	_load_pois()
	_load_planet_texture()
	queue_redraw()

func set_minimap_visible(on: bool) -> void:
	_visible_hud = on
	visible = on
	queue_redraw()

func toggle_minimap() -> void:
	set_minimap_visible(not _visible_hud)

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_M and not event.ctrl_pressed:
			toggle_minimap()
			get_viewport().set_input_as_handled()

func _gui_input(event: InputEvent) -> void:
	if not _click_pan or _camera == null:
		return
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var local := get_local_mouse_position()
		if local.y > _size_px:
			return
		var core3 := _minimap_to_core3(local)
		_camera.position = Projection3D2D.to_screen(core3)
		accept_event()

func _process(_delta: float) -> void:
	if not _visible_hud:
		return
	var center := _center_core3()
	if _show_coords and _coord_label:
		_coord_label.text = _format_coords(center)
	queue_redraw()

func _format_coords(core3: Vector3) -> String:
	var pos := Projection3D2D.normalize_core3_pos(core3)
	if not _show_altitude:
		return Projection3D2D.format_hud_plan(pos, _coord_compact)
	return Projection3D2D.format_hud_coordinates(pos, _coord_compact)

func _center_core3() -> Vector3:
	if _player_controller and _player_controller.enabled and _player_controller.get_player_id() > 0:
		var oid := _player_controller.get_player_id()
		if _entity_manager:
			var e := _entity_manager.get_entity(oid)
			if e:
				return Projection3D2D.normalize_core3_pos(e.core3_pos)
	if _camera:
		return Projection3D2D.from_screen(_camera.position)
	return Vector3.ZERO

func _world_to_minimap(core3: Vector3, center: Vector3) -> Vector2:
	var rel := Vector2(core3.x - center.x, -(core3.z - center.z))
	var half := _size_px * 0.46
	var span_m := _view_radius_m * 2.0
	var scale := half / span_m
	return Vector2(_size_px * 0.5, _size_px * 0.5) + rel * scale

func _minimap_to_core3(local: Vector2) -> Vector3:
	var center := _center_core3()
	var half := _size_px * 0.46
	var span_m := _view_radius_m * 2.0
	var scale := half / span_m
	var rel := (local - Vector2(_size_px * 0.5, _size_px * 0.5)) / scale
	return Vector3(center.x + rel.x, 0.0, center.z - rel.y)

func _draw() -> void:
	if not _visible_hud:
		return
	var map_rect := Rect2(Vector2.ZERO, Vector2(_size_px, _size_px))
	draw_rect(map_rect, Color(0.04, 0.05, 0.09, 0.82))
	draw_rect(map_rect, Color(0.35, 0.55, 0.85, 0.55), false, 2.0)
	if _show_coords and _coord_strip_h > 0.0:
		var strip := Rect2(0.0, _size_px, _size_px, _coord_strip_h)
		draw_rect(strip, Color(0.03, 0.04, 0.07, 0.92))
		draw_line(Vector2(0.0, _size_px), Vector2(_size_px, _size_px), Color(0.35, 0.55, 0.85, 0.45), 1.0)

	var center := _center_core3()
	_draw_map_region(center)
	if _show_poi:
		_draw_pois(center)
	if _show_entities and _entity_manager:
		_draw_entities(center)
	_draw_player_marker(center)

	# Nord
	draw_string(
		ThemeDB.fallback_font,
		Vector2(_size_px * 0.5 - 4.0, 12.0),
		"N",
		HORIZONTAL_ALIGNMENT_LEFT,
		-1,
		11,
		Color(0.75, 0.85, 1.0, 0.9)
	)

func _draw_map_region(center: Vector3) -> void:
	if _planet_texture == null:
		return
	var tex_size := _planet_texture.get_size()
	if tex_size.x <= 0.0:
		return
	var world_span_px := 2.0 * _half_size * Projection3D2D.SCALE
	var uv_center_x := (center.x + _half_size) / (2.0 * _half_size)
	var uv_center_y := (-center.z + _half_size) / (2.0 * _half_size)
	var view_world_px := _view_radius_m * 2.0 * Projection3D2D.SCALE
	var uv_w := clampf(view_world_px / world_span_px, 0.01, 1.0)
	var uv_h := uv_w * (_size_px / _size_px)
	var src := Rect2(
		(uv_center_x - uv_w * 0.5) * tex_size.x,
		(uv_center_y - uv_h * 0.5) * tex_size.y,
		uv_w * tex_size.x,
		uv_h * tex_size.y
	)
	src = src.intersection(Rect2(Vector2.ZERO, tex_size))
	var dst := Rect2(Vector2(_size_px * 0.04, _size_px * 0.04), Vector2(_size_px * 0.92, _size_px * 0.92))
	draw_texture_rect_region(_planet_texture, dst, src, Color(1, 1, 1, 0.88))

func _draw_pois(center: Vector3) -> void:
	for item: Variant in _pois:
		if not item is Dictionary:
			continue
		var p: Dictionary = item
		if bool(p.get("deprecated", false)):
			continue
		if _essential_poi_only and not bool(p.get("essential", false)):
			continue
		var pos := Vector3(float(p.get("x", 0.0)), 0.0, float(p.get("z", 0.0)))
		if absf(pos.x - center.x) > _view_radius_m or absf(pos.z - center.z) > _view_radius_m:
			continue
		var mp := _world_to_minimap(pos, center)
		var kind := str(p.get("kind", ""))
		var col := _poi_color(kind)
		draw_circle(mp, 3.5, col)

func _draw_entities(center: Vector3) -> void:
	for entity in _entity_manager.get_all_entities():
		if entity == null:
			continue
		var pos: Vector3 = entity.core3_pos
		if not HubFocus.should_show_entity(pos, str(entity.kind), str(entity.label_text), str(entity.entity_key)):
			continue
		if absf(pos.x - center.x) > _view_radius_m or absf(pos.z - center.z) > _view_radius_m:
			continue
		var mp := _world_to_minimap(pos, center)
		draw_circle(mp, 2.5, Color(entity.color.r, entity.color.g, entity.color.b, 0.85))

func _draw_player_marker(center: Vector3) -> void:
	var mp := _world_to_minimap(center, center)
	var tri := PackedVector2Array([
		mp + Vector2(0, -7),
		mp + Vector2(-5, 5),
		mp + Vector2(5, 5),
	])
	draw_colored_polygon(tri, Color(0.95, 0.95, 0.3, 1.0))
	draw_polyline(tri + PackedVector2Array([tri[0]]), Color(0.1, 0.1, 0.1, 0.9), 1.0)

func _poi_color(kind: String) -> Color:
	match kind:
		"hub", "spawn":
			return Color(0.45, 0.95, 0.5, 1.0)
		"starport_shuttle":
			return Color(0.35, 0.75, 1.0, 1.0)
		"bank":
			return Color(0.95, 0.82, 0.25, 1.0)
		"shops", "market":
			return Color(1.0, 0.55, 0.2, 1.0)
		_:
			return Color(0.7, 0.7, 0.8, 0.9)
