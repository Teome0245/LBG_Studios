# hub_buildings_layer.gd — Bâtiments Lost Heaven (tuiles SVG + labels + portes)
extends Node2D
class_name HubBuildingsLayer

const BUILDINGS_PATH := "res://assets/maps/lost_heaven_buildings.json"

@export var visible_buildings: bool = true
@export var show_labels: bool = true
@export var show_doors: bool = true
## size_m JSON = mètres Core3 (collision = rendu) ; mul doit rester 1.0.
@export var size_multiplier: float = 1.0

var _buildings: Array = []
var _blueprint_cache: Dictionary = {}

func _ready() -> void:
	var mul := float(MapTextureLoader.world_render_cfg().get("building_size_multiplier", size_multiplier))
	if mul > 0.0:
		size_multiplier = mul
	reload()

func reload() -> void:
	_buildings.clear()
	_blueprint_cache.clear()
	if not FileAccess.file_exists(BUILDINGS_PATH):
		push_warning("HubBuildingsLayer: %s absent" % BUILDINGS_PATH)
		return
	var f := FileAccess.open(BUILDINGS_PATH, FileAccess.READ)
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if raw is Dictionary:
		var arr: Variant = (raw as Dictionary).get("buildings", [])
		_buildings = arr if arr is Array else []
	queue_redraw()

func _draw() -> void:
	if not visible_buildings:
		return
	for item: Variant in _buildings:
		if item is Dictionary:
			_draw_building(item as Dictionary)

func _draw_building(b: Dictionary) -> void:
	var cx := float(b.get("x", 0.0))
	var cz := float(b.get("z", 0.0))
	var size_m := float(b.get("size_m", 32.0))
	var half_px := size_m * 0.5 * Projection3D2D.SCALE * size_multiplier
	var center := Projection3D2D.to_screen(Vector3(cx, 0.0, cz))
	var rect := Rect2(center - Vector2(half_px, half_px), Vector2(half_px * 2.0, half_px * 2.0))
	var kind := str(b.get("kind", ""))
	var fill := _color_for_kind(kind)
	draw_rect(rect.grow(3.0), Color(0, 0, 0, 0.28))
	var tex := BuildingTileRegistry.texture_for_kind(kind)
	if tex:
		draw_texture_rect(tex, rect, false, Color(1, 1, 1, 0.96))
		draw_rect(rect, Color(fill.r, fill.g, fill.b, 0.55), false, 1.5)
	else:
		draw_rect(rect, Color(fill.r * 0.55, fill.g * 0.55, fill.b * 0.55, 0.75))
		draw_rect(rect, Color(fill.r, fill.g, fill.b, 0.95), false, 2.5)

	# Si un blueprint CAO est associé, dessiner les cloisons intérieures et pièces
	var bp_rel: String = str(b.get("cad_blueprint_ref", "")).strip_edges()
	if not bp_rel.is_empty():
		var bp := _get_or_load_blueprint(bp_rel)
		if not bp.is_empty():
			_draw_blueprint_interior(bp, cx, cz)

	if show_doors and kind != "city_gate" and b.get("door") is Dictionary:
		_draw_door(b, cx, cz, size_m, fill)
	if show_labels:
		var label := str(b.get("label", ""))
		if label != "":
			var font_size := clampi(int(half_px * 0.55), 9, 12)
			draw_string(
				ThemeDB.fallback_font,
				center + Vector2(-label.length() * (font_size * 0.28), -half_px - 6.0),
				label,
				HORIZONTAL_ALIGNMENT_LEFT,
				-1,
				font_size,
				Color(1.0, 0.98, 0.92, 0.95)
			)

## Porte + seuil + tablier (apron) hors emprise — face Core3 N/S/E/O.
func _draw_door(b: Dictionary, cx: float, cz: float, size_m: float, fill: Color) -> void:
	var door: Dictionary = b["door"]
	var face := str(door.get("face", "south")).to_lower()
	var width_m := float(door.get("width_m", 12.0))
	var depth_m := float(door.get("depth_m", 14.0))
	var apron_m := float(door.get("apron_m", 8.0))
	var half := size_m * 0.5
	var hw := width_m * 0.5
	# Vestibule (dans le bâtiment) + tablier (dehors), en mètres Core3.
	var min_x: float
	var max_x: float
	var min_z: float
	var max_z: float
	var apron_min_x: float
	var apron_max_x: float
	var apron_min_z: float
	var apron_max_z: float
	match face:
		"north":
			min_x = cx - hw
			max_x = cx + hw
			min_z = cz + half - depth_m
			max_z = cz + half
			apron_min_x = cx - hw
			apron_max_x = cx + hw
			apron_min_z = cz + half
			apron_max_z = cz + half + apron_m
		"south":
			min_x = cx - hw
			max_x = cx + hw
			min_z = cz - half
			max_z = cz - half + depth_m
			apron_min_x = cx - hw
			apron_max_x = cx + hw
			apron_min_z = cz - half - apron_m
			apron_max_z = cz - half
		"east":
			min_x = cx + half - depth_m
			max_x = cx + half
			min_z = cz - hw
			max_z = cz + hw
			apron_min_x = cx + half
			apron_max_x = cx + half + apron_m
			apron_min_z = cz - hw
			apron_max_z = cz + hw
		_: # west
			min_x = cx - half
			max_x = cx - half + depth_m
			min_z = cz - hw
			max_z = cz + hw
			apron_min_x = cx - half - apron_m
			apron_max_x = cx - half
			apron_min_z = cz - hw
			apron_max_z = cz + hw
	var s := Projection3D2D.SCALE * size_multiplier
	var vestibule := _core3_rect_to_screen(min_x, min_z, max_x, max_z, s)
	var apron := _core3_rect_to_screen(apron_min_x, apron_min_z, apron_max_x, apron_max_z, s)
	# Tablier (chemin d'accès)
	draw_rect(apron, Color(0.72, 0.58, 0.38, 0.45))
	draw_rect(apron, Color(0.9, 0.78, 0.5, 0.7), false, 1.0)
	# Vestibule / seuil
	draw_rect(vestibule, Color(0.12, 0.1, 0.08, 0.55))
	draw_rect(vestibule, Color(fill.r, fill.g, fill.b, 0.85), false, 1.6)
	# Seuil lumineux au milieu du tablier
	var mid := Projection3D2D.to_screen(Vector3(
		(apron_min_x + apron_max_x) * 0.5,
		0.0,
		(apron_min_z + apron_max_z) * 0.5
	))
	draw_circle(mid, 2.4, Color(1.0, 0.9, 0.55, 0.9))
	# Coupe visuelle du mur sur la face porte (trait sombre = ouverture)
	match face:
		"north":
			var p0 := Projection3D2D.to_screen(Vector3(min_x, 0.0, cz + half))
			var p1 := Projection3D2D.to_screen(Vector3(max_x, 0.0, cz + half))
			draw_line(p0, p1, Color(0.08, 0.06, 0.04, 0.95), 3.0)
		"south":
			var p2 := Projection3D2D.to_screen(Vector3(min_x, 0.0, cz - half))
			var p3 := Projection3D2D.to_screen(Vector3(max_x, 0.0, cz - half))
			draw_line(p2, p3, Color(0.08, 0.06, 0.04, 0.95), 3.0)
		"east":
			var p4 := Projection3D2D.to_screen(Vector3(cx + half, 0.0, min_z))
			var p5 := Projection3D2D.to_screen(Vector3(cx + half, 0.0, max_z))
			draw_line(p4, p5, Color(0.08, 0.06, 0.04, 0.95), 3.0)
		_:
			var p6 := Projection3D2D.to_screen(Vector3(cx - half, 0.0, min_z))
			var p7 := Projection3D2D.to_screen(Vector3(cx - half, 0.0, max_z))
			draw_line(p6, p7, Color(0.08, 0.06, 0.04, 0.95), 3.0)

func _core3_rect_to_screen(min_x: float, min_z: float, max_x: float, max_z: float, _s: float) -> Rect2:
	var tl := Projection3D2D.to_screen(Vector3(min_x, 0.0, max_z))
	var br := Projection3D2D.to_screen(Vector3(max_x, 0.0, min_z))
	return Rect2(tl, br - tl).abs()

func _color_for_kind(kind: String) -> Color:
	match kind:
		"bank":
			return Color(0.95, 0.82, 0.25, 1.0)
		"shops", "market":
			return Color(1.0, 0.55, 0.2, 1.0)
		"cantina", "inn":
			return Color(0.85, 0.45, 0.35, 1.0)
		"npc_housing_block":
			return Color(0.55, 0.48, 0.42, 1.0)
		"terminal", "blue_frog", "mission_terminal":
			return Color(0.35, 0.75, 1.0, 1.0)
		"starport_shuttle":
			return Color(0.45, 0.95, 0.5, 1.0)
		"clinic":
			return Color(0.5, 0.85, 0.75, 1.0)
		"town_hall":
			return Color(0.75, 0.7, 0.95, 1.0)
		"city_gate":
			return Color(0.55, 0.5, 0.45, 1.0)
		"trainers_combat", "trainer_artisan":
			return Color(0.7, 0.55, 0.4, 1.0)
	return Color(0.65, 0.65, 0.75, 1.0)

func set_visible_buildings(on: bool) -> void:
	visible_buildings = on
	queue_redraw()

func _get_or_load_blueprint(rel_path: String) -> Dictionary:
	if _blueprint_cache.has(rel_path):
		return _blueprint_cache[rel_path]
	var full_path := "res://assets/maps/".path_join(rel_path)
	if not FileAccess.file_exists(full_path):
		_blueprint_cache[rel_path] = {}
		return {}
	var f := FileAccess.open(full_path, FileAccess.READ)
	if f == null:
		_blueprint_cache[rel_path] = {}
		return {}
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if raw is Dictionary:
		_blueprint_cache[rel_path] = raw
		return raw
	_blueprint_cache[rel_path] = {}
	return {}

func _draw_blueprint_interior(bp: Dictionary, cx: float, cz: float) -> void:
	var floors: Variant = bp.get("floors", [])
	if not (floors is Array) or floors.is_empty():
		return
	var floor_zero: Dictionary = floors[0]
	var walls: Variant = floor_zero.get("walls", [])
	if not (walls is Array):
		return

	for w_item: Variant in walls:
		if not (w_item is Dictionary):
			continue
		var w: Dictionary = w_item
		if bool(w.get("is_exterior", false)):
			continue

		var start: Array = w.get("start", [0.0, 0.0])
		var end: Array = w.get("end", [0.0, 0.0])
		var p1 := Vector2(float(start[0]), float(start[1]))
		var p2 := Vector2(float(end[0]), float(end[1]))
		var dir := p2 - p1
		var length := dir.length()
		if length <= 0.01:
			continue
		var norm := dir.normalized()
		var doors: Variant = w.get("doors", [])
		var col_wall := Color(0.92, 0.92, 0.88, 0.85)

		if not (doors is Array) or doors.is_empty():
			var s1 := Projection3D2D.to_screen(Vector3(cx + p1.x, 0.0, cz + p1.y))
			var s2 := Projection3D2D.to_screen(Vector3(cx + p2.x, 0.0, cz + p2.y))
			draw_line(s1, s2, col_wall, 2.0)
		else:
			var cur_dist := 0.0
			for d_item: Variant in doors:
				if not (d_item is Dictionary):
					continue
				var d: Dictionary = d_item
				var d_off := clampf(float(d.get("offset_m", 0.0)), 0.0, length)
				var d_w := clampf(float(d.get("width_m", 1.2)), 0.0, length - d_off)
				if d_off > cur_dist + 0.05:
					var pt_a := p1 + norm * cur_dist
					var pt_b := p1 + norm * d_off
					var sa := Projection3D2D.to_screen(Vector3(cx + pt_a.x, 0.0, cz + pt_a.y))
					var sb := Projection3D2D.to_screen(Vector3(cx + pt_b.x, 0.0, cz + pt_b.y))
					draw_line(sa, sb, col_wall, 2.0)
				cur_dist = d_off + d_w
			if cur_dist < length - 0.05:
				var pt_a := p1 + norm * cur_dist
				var sa := Projection3D2D.to_screen(Vector3(cx + pt_a.x, 0.0, cz + pt_a.y))
				var sb := Projection3D2D.to_screen(Vector3(cx + p2.x, 0.0, cz + p2.y))
				draw_line(sa, sb, col_wall, 2.0)
