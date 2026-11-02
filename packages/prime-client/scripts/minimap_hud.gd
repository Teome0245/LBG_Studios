# minimap_hud.gd — Radar Circulaire SWG Pre-CU en Bas-Gauche + Coordonnées X Y Z
extends Control
class_name MinimapHud

const CONFIG_PATH := "res://config/minimap_config.json"
const POI_PATH := "res://assets/maps/scrapaltai_pois.json"
const MAP_CONFIG_PATH := "res://assets/maps/scrapaltai_map_config.json"

@export var camera_path: NodePath = NodePath("../../../Camera2D")
@export var entity_manager_path: NodePath = NodePath("../../../EntityManager")
@export var player_controller_path: NodePath = NodePath("../../../PlayerController")

var _size_px: float = 148.0
var _view_radius_m: float = 340.0
var _show_poi: bool = true
var _show_entities: bool = true
var _essential_poi_only: bool = true
var _click_pan: bool = true
var _visible_hud: bool = true
var _show_coords: bool = true
var _show_altitude: bool = true
var _coord_compact: bool = true
var _coord_strip_h: float = 20.0

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
	_size_px = 148.0
	_coord_strip_h = 20.0
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
	_coord_label.add_theme_font_size_override("font_size", 10)
	_coord_label.add_theme_color_override("font_color", Color(0.62, 0.96, 1.0, 0.98))
	add_child(_coord_label)

func _apply_layout_size() -> void:
	var total_h := _size_px + (_coord_strip_h if _show_coords else 0.0)
	custom_minimum_size = Vector2(_size_px, total_h)
	size = custom_minimum_size
	if _coord_label:
		_coord_label.visible = _show_coords
		_coord_label.position = Vector2(0.0, _size_px + 2.0)
		_coord_label.size = Vector2(_size_px, _coord_strip_h - 2.0)

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
	_view_radius_m = float(cfg.get("view_radius_m", _view_radius_m))
	_show_poi = bool(cfg.get("show_poi", _show_poi))
	_show_entities = bool(cfg.get("show_entities", _show_entities))
	_essential_poi_only = bool(cfg.get("show_essential_poi_only", _essential_poi_only))
	_click_pan = bool(cfg.get("click_pan_camera", _click_pan))
	_show_coords = bool(cfg.get("show_coordinates", _show_coords))

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
	for path in ["res://assets/maps/scrapaltai_shard_legacy.png", "res://assets/maps/scrapaltai.svg"]:
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
		var c := Vector2(_size_px * 0.5, _size_px * 0.5)
		if local.distance_to(c) > _size_px * 0.48:
			return
		var core3 := _minimap_to_core3(local)
		_camera.position = Projection3D2D.to_screen(core3)
		accept_event()

func _process(_delta: float) -> void:
	if not _visible_hud:
		return
	var center := _center_core3()
	if _show_coords and _coord_label:
		var pos := Projection3D2D.normalize_core3_pos(center)
		_coord_label.text = "%d    %d    %d" % [int(round(pos.x)), int(round(pos.y)), int(round(pos.z))]
	queue_redraw()

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
	var half := _size_px * 0.43
	var span_m := _view_radius_m * 2.0
	var scale := half / span_m
	return Vector2(_size_px * 0.5, _size_px * 0.5) + rel * scale

func _minimap_to_core3(local: Vector2) -> Vector3:
	var center := _center_core3()
	var half := _size_px * 0.43
	var span_m := _view_radius_m * 2.0
	var scale := half / span_m
	var rel := (local - Vector2(_size_px * 0.5, _size_px * 0.5)) / scale
	return Vector3(center.x + rel.x, 0.0, center.z - rel.y)

func _draw() -> void:
	if not _visible_hud:
		return
	var c := Vector2(_size_px * 0.5, _size_px * 0.5)
	var r := _size_px * 0.45

	# 1. Disque Radar Circulaire SWG (fond topographique sable/ocre + grille polaire)
	draw_circle(c, r + 4.0, Color(0.015, 0.09, 0.12, 0.92))
	draw_circle(c, r, Color(0.46, 0.38, 0.26, 0.88))
	draw_circle(c, r * 0.72, Color(0.52, 0.43, 0.30, 0.55))

	# Cône de vision caméra/joueur (style radar SWG)
	var cone_pts := PackedVector2Array([
		c,
		c + Vector2(-r * 0.52, -r * 0.84),
		c + Vector2(0.0, -r * 0.98),
		c + Vector2(r * 0.52, -r * 0.84),
	])
	draw_colored_polygon(cone_pts, Color(0.85, 0.96, 1.0, 0.14))

	# Cercles et axes de portée radar
	draw_arc(c, r * 0.66, 0.0, TAU, 36, Color(0.18, 0.56, 0.66, 0.42), 1.0)
	draw_arc(c, r * 0.33, 0.0, TAU, 24, Color(0.18, 0.56, 0.66, 0.32), 1.0)
	draw_line(Vector2(c.x - r, c.y), Vector2(c.x + r, c.y), Color(0.15, 0.48, 0.58, 0.35), 1.0)
	draw_line(Vector2(c.x, c.y - r), Vector2(c.x, c.y + r), Color(0.15, 0.48, 0.58, 0.35), 1.0)

	var center := _center_core3()
	if _show_poi:
		_draw_pois(center, c, r - 4.0)
	if _show_entities and _entity_manager:
		_draw_entities(center, c, r - 4.0)
	_draw_player_marker(c)

	# Couronne extérieure biseautée SWG (Cyan Holo-Teal + graduations d'azimut)
	draw_arc(c, r, 0.0, TAU, 64, Color(0.24, 0.84, 0.94, 0.96), 2.5)
	draw_arc(c, r + 3.5, 0.0, TAU, 64, Color(0.14, 0.52, 0.62, 0.80), 1.2)
	for deg in [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0]:
		var a: float = deg_to_rad(float(deg))
		var dir := Vector2(cos(a), sin(a))
		draw_line(c + dir * (r - 4.0), c + dir * (r + 3.0), Color(0.68, 0.96, 1.0, 0.90), 1.5)

	# Points cardinaux en français (N, S, E, O)
	var font := ThemeDB.fallback_font
	if font:
		draw_string(font, Vector2(c.x - 4.0, c.y - r + 10.0), "N", HORIZONTAL_ALIGNMENT_LEFT, -1, 9, Color(0.98, 0.88, 0.38, 1.0))
		draw_string(font, Vector2(c.x - 3.5, c.y + r - 3.0), "S", HORIZONTAL_ALIGNMENT_LEFT, -1, 8, Color(0.75, 0.94, 1.0, 0.9))
		draw_string(font, Vector2(c.x + r - 10.0, c.y + 3.0), "E", HORIZONTAL_ALIGNMENT_LEFT, -1, 8, Color(0.75, 0.94, 1.0, 0.9))
		draw_string(font, Vector2(c.x - r + 3.0, c.y + 3.0), "O", HORIZONTAL_ALIGNMENT_LEFT, -1, 8, Color(0.75, 0.94, 1.0, 0.9))

	# Bandeau coordonnées X Y Z sous le disque radar (comme en bas à gauche de SWG)
	if _show_coords and _coord_strip_h > 0.0:
		var strip := Rect2(4.0, _size_px, _size_px - 8.0, _coord_strip_h)
		draw_rect(strip, Color(0.015, 0.10, 0.13, 0.92), true)
		draw_rect(strip, Color(0.22, 0.78, 0.88, 0.88), false, 1.0)

func _draw_pois(center: Vector3, disc_c: Vector2, max_r: float) -> void:
	for item: Variant in _pois:
		if not item is Dictionary:
			continue
		var p: Dictionary = item
		if bool(p.get("deprecated", false)):
			continue
		if _essential_poi_only and not bool(p.get("essential", false)):
			continue
		var pos := Vector3(float(p.get("x", 0.0)), 0.0, float(p.get("z", 0.0)))
		var mp := _world_to_minimap(pos, center)
		if mp.distance_to(disc_c) > max_r:
			continue
		var kind := str(p.get("kind", ""))
		draw_circle(mp, 3.0, _poi_color(kind))

func _draw_entities(center: Vector3, disc_c: Vector2, max_r: float) -> void:
	for entity in _entity_manager.get_all_entities():
		if entity == null:
			continue
		var pos: Vector3 = entity.core3_pos
		if not HubFocus.should_show_entity(pos, str(entity.kind), str(entity.label_text), str(entity.entity_key)):
			continue
		var mp := _world_to_minimap(pos, center)
		if mp.distance_to(disc_c) > max_r:
			continue
		draw_circle(mp, 2.5, Color(entity.color.r, entity.color.g, entity.color.b, 0.92))

func _draw_player_marker(disc_c: Vector2) -> void:
	var tri := PackedVector2Array([
		disc_c + Vector2(0, -6),
		disc_c + Vector2(-4.5, 4.5),
		disc_c + Vector2(4.5, 4.5),
	])
	draw_colored_polygon(tri, Color(0.45, 0.98, 1.0, 1.0))
	draw_polyline(tri + PackedVector2Array([tri[0]]), Color(0.05, 0.15, 0.2, 0.95), 1.0)

func _poi_color(kind: String) -> Color:
	match kind:
		"hub", "spawn":
			return Color(0.35, 0.95, 0.65, 1.0)
		"starport_shuttle":
			return Color(0.35, 0.82, 1.0, 1.0)
		"bank":
			return Color(0.98, 0.84, 0.28, 1.0)
		"shops", "market":
			return Color(1.0, 0.58, 0.22, 1.0)
		_:
			return Color(0.75, 0.85, 0.92, 0.9)
