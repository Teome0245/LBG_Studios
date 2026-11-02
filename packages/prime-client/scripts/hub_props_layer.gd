# hub_props_layer.gd — Chemins + props Lost Heaven (data-driven, _draw)
extends Node2D
class_name HubPropsLayer

const Projection3D2D = preload("res://scripts/projection.gd")
const PROPS_PATH := "res://assets/maps/lost_heaven_props.json"

@export var visible_props: bool = true
@export var show_prop_labels: bool = false

var _paths: Array = []
var _props: Array = []
var _defaults: Dictionary = {}
var _gate_exits: Array = []

func _ready() -> void:
	reload()

func reload() -> void:
	_paths.clear()
	_props.clear()
	_defaults.clear()
	if not FileAccess.file_exists(PROPS_PATH):
		push_warning("HubPropsLayer: %s absent" % PROPS_PATH)
		return
	var f := FileAccess.open(PROPS_PATH, FileAccess.READ)
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if raw is Dictionary:
		var d: Dictionary = raw
		_defaults = d.get("defaults", {}) if d.get("defaults") is Dictionary else {}
		var p: Variant = d.get("paths", [])
		_paths = p if p is Array else []
		var pr: Variant = d.get("props", [])
		_props = pr if pr is Array else []
		var ge: Variant = d.get("gate_exits", [])
		_gate_exits = ge if ge is Array else []
	_props.sort_custom(func(a: Variant, b: Variant) -> bool:
		return int((a as Dictionary).get("z_draw", 0)) < int((b as Dictionary).get("z_draw", 0))
	)
	queue_redraw()

func _draw() -> void:
	if not visible_props:
		return
	for item: Variant in _paths:
		if item is Dictionary:
			_draw_path(item as Dictionary)
	for item: Variant in _props:
		if item is Dictionary:
			_draw_prop(item as Dictionary)

func _draw_path(p: Dictionary) -> void:
	var kind := str(p.get("kind", "road"))
	var width_m := float(p.get("width_m", _defaults.get("path_width_m", 6.0)))
	var width_px := width_m * Projection3D2D.SCALE
	var alpha := float(_defaults.get("path_alpha", 0.45))
	var fill := _path_color(kind, alpha)
	var pts_raw: Variant = p.get("points", null)
	if not (pts_raw is Array and (pts_raw as Array).size() >= 2):
		return
	var screen := PackedVector2Array()
	for pt: Variant in pts_raw as Array:
		if not pt is Dictionary:
			continue
		var d: Dictionary = pt
		screen.append(Projection3D2D.to_screen(Vector3(float(d.get("x", 0.0)), 0.0, float(d.get("z", 0.0)))))
	if screen.size() < 2:
		return
	if kind == "fence":
		_draw_fence(screen, bool(p.get("closed", false)), fill, pts_raw as Array)
		return
	if kind == "cliff":
		_draw_dyson_cliff(screen, bool(p.get("closed", false)), p)
		return
	_stroke_polyline(screen, width_px, fill, bool(p.get("closed", false)))

func _draw_dyson_cliff(screen: PackedVector2Array, closed: bool, p: Dictionary) -> void:
	var n := screen.size()
	var segs := n if closed else n - 1
	var hatch_len_base := float(p.get("hatch_len", 14.0))
	var flip_side := bool(p.get("flip_hatch", false))
	var col_cliff := Color(0.18, 0.12, 0.08, 0.98)
	var col_shade := Color(0.34, 0.25, 0.16, 0.80)

	for i in range(segs):
		var a: Vector2 = screen[i]
		var b: Vector2 = screen[(i + 1) % n] if closed else screen[i + 1]
		var seg := b - a
		var d := seg.length()
		if d < 1.0:
			continue
		var dir := seg / d
		var norm := Vector2(-dir.y, dir.x)
		if flip_side:
			norm = -norm

		# 1. Crête rocheuse d'escarpement principale marquée
		draw_line(a, b, col_cliff, 3.2)

		# 2. Hachures géologiques régulières style Dyson Logos (relief naturel)
		var step := 7.0
		var dist := 0.0
		var h_idx := 0
		while dist <= d:
			var pt := a + dir * dist
			var hl := hatch_len_base * (1.0 if (h_idx % 2 == 0) else 0.55)
			var h_end := pt + norm * hl
			draw_line(pt, h_end, col_shade, 1.2)
			if h_idx % 3 == 0:
				draw_line(h_end, h_end + norm * 2.5 + dir * 2.0, col_cliff, 1.0)
			dist += step
			h_idx += 1

func _path_color(kind: String, alpha: float) -> Color:
	match kind:
		"plaza":
			return Color(0.72, 0.54, 0.34, alpha + 0.06)
		"alley":
			return Color(0.52, 0.42, 0.30, alpha * 0.85)
		"fence":
			return Color(0.48, 0.38, 0.28, alpha + 0.15)
		"road":
			return Color(0.78, 0.70, 0.55, 0.52) # Sable tassé et terre battue de piste désertique
	return Color(0.65, 0.55, 0.40, alpha * 0.9)

func _draw_fence(screen: PackedVector2Array, closed: bool, fill: Color, core3_pts: Array) -> void:
	var n := screen.size()
	var segs := n if closed else n - 1
	var wall_half_w := 4.5 # Mur épais de 9px (~2.5m de large)

	# 1. Ombre portée douce du mur projetée sur le sable
	for i in range(segs):
		var a: Vector2 = screen[i]
		var b: Vector2 = screen[(i + 1) % n] if closed else screen[i + 1]
		if _fence_segment_is_gate_gap(core3_pts, i, closed):
			continue
		var dir := b - a
		if dir.length_squared() < 0.01:
			continue
		var perp := Vector2(-dir.y, dir.x).normalized() * wall_half_w
		var shadow_offset := Vector2(3.5, 4.5)
		var shadow_quad := PackedVector2Array([
			a + perp + shadow_offset,
			b + perp + shadow_offset,
			b - perp + shadow_offset,
			a - perp + shadow_offset
		])
		draw_colored_polygon(shadow_quad, Color(0.14, 0.10, 0.06, 0.28))

	# 2. Corps du rempart en maçonnerie de grès fortifiée
	for i in range(segs):
		var a: Vector2 = screen[i]
		var b: Vector2 = screen[(i + 1) % n] if closed else screen[i + 1]
		if _fence_segment_is_gate_gap(core3_pts, i, closed):
			_draw_gate_opening(a, b, fill)
			continue
		var dir := b - a
		if dir.length_squared() < 0.01:
			continue
		var along := dir.normalized()
		var perp := Vector2(-along.y, along.x) * wall_half_w

		# Base de maçonnerie
		var wall_quad := PackedVector2Array([a + perp, b + perp, b - perp, a - perp])
		draw_colored_polygon(wall_quad, Color(0.42, 0.33, 0.22, 0.96))

		# Chemin de ronde supérieur plus clair
		var walk_quad := PackedVector2Array([a + perp * 0.55, b + perp * 0.55, b - perp * 0.55, a - perp * 0.55])
		draw_colored_polygon(walk_quad, Color(0.60, 0.49, 0.35, 0.98))

		# Lignes de contour encrées style Dyson Logos
		draw_line(a + perp, b + perp, Color(0.16, 0.11, 0.07, 0.95), 1.5)
		draw_line(a - perp, b - perp, Color(0.16, 0.11, 0.07, 0.95), 1.5)

		# Crénelage / merlons le long du rempart
		var post_step := 12.0
		var count := maxi(1, int(dir.length() / post_step))
		for j in range(count):
			var t := float(j + 0.5) / float(count)
			var p := a.lerp(b, t)
			# Meurtrière / saillie de merlon
			draw_line(p - perp * 0.9, p - perp * 0.2, Color(0.18, 0.12, 0.08, 0.95), 2.2)
			draw_line(p + perp * 0.2, p + perp * 0.9, Color(0.18, 0.12, 0.08, 0.95), 2.2)

	# 3. Bastions / tours d'angles circulaires aux sommets
	for i in range(n):
		var p: Vector2 = screen[i]
		# Ombre de la tour
		draw_circle(p + Vector2(3.0, 4.0), 7.5, Color(0.14, 0.10, 0.06, 0.30))
		# Base en pierre
		draw_circle(p, 6.5, Color(0.38, 0.29, 0.19, 0.98))
		# Sommet de tour crénelée
		draw_circle(p, 4.8, Color(0.62, 0.50, 0.36, 0.98))
		draw_arc(p, 6.5, 0.0, TAU, 18, Color(0.16, 0.11, 0.07, 0.95), 1.5)
		# Meurtrière centrale de guet
		draw_circle(p, 1.8, Color(0.12, 0.08, 0.05, 0.95))

	for item: Variant in _gate_exits:
		if item is Dictionary:
			_draw_gate_arch(item as Dictionary, fill)


func _fence_segment_is_gate_gap(core3_pts: Array, seg_index: int, closed: bool) -> bool:
	if _gate_exits.is_empty() or core3_pts.size() < 2:
		return false
	for ge: Variant in _gate_exits:
		if not ge is Dictionary:
			continue
		var g: Dictionary = ge
		var idxs: Variant = g.get("fence_open_segment_indices", [])
		if idxs is Array:
			for idx: Variant in idxs:
				if int(idx) == seg_index:
					return true
	var n := core3_pts.size()
	var i := seg_index
	var j := (i + 1) % n if closed else i + 1
	if j >= n:
		return false
	if not core3_pts[i] is Dictionary or not core3_pts[j] is Dictionary:
		return false
	var a: Dictionary = core3_pts[i]
	var b: Dictionary = core3_pts[j]
	var ax := float(a.get("x", 0.0))
	var az := float(a.get("z", 0.0))
	var bx := float(b.get("x", 0.0))
	var bz := float(b.get("z", 0.0))
	var mx := (ax + bx) * 0.5
	var mz := (az + bz) * 0.5
	for ge: Variant in _gate_exits:
		if not ge is Dictionary:
			continue
		var g: Dictionary = ge
		var c: Variant = g.get("center", {})
		if not c is Dictionary:
			continue
		var cd: Dictionary = c
		var gx := float(cd.get("x", 0.0))
		var gz := float(cd.get("z", 0.0))
		var hw := float(g.get("width_m", 16.0)) * 0.55
		if absf(mx - gx) <= hw and absf(mz - gz) <= 55.0:
			return true
	return false


func _draw_gate_opening(a: Vector2, b: Vector2, fill: Color) -> void:
	# Seuil pavé de passage de porte fortifiée
	var dir := (b - a).normalized()
	var perp := Vector2(-dir.y, dir.x) * 7.0
	var threshold := PackedVector2Array([a + perp, b + perp, b - perp, a - perp])
	draw_colored_polygon(threshold, Color(0.50, 0.40, 0.28, 0.70))
	draw_line(a - perp, a + perp, Color(0.18, 0.12, 0.08, 0.95), 2.5)
	draw_line(b - perp, b + perp, Color(0.18, 0.12, 0.08, 0.95), 2.5)

	# Poteaux d'enceinte et herses de porte
	draw_circle(a, 6.0, Color(0.32, 0.24, 0.16, 0.98))
	draw_circle(a, 4.0, Color(0.58, 0.48, 0.34, 0.98))
	draw_arc(a, 6.0, 0.0, TAU, 16, Color(0.14, 0.09, 0.06, 0.95), 1.5)

	draw_circle(b, 6.0, Color(0.32, 0.24, 0.16, 0.98))
	draw_circle(b, 4.0, Color(0.58, 0.48, 0.34, 0.98))
	draw_arc(b, 6.0, 0.0, TAU, 16, Color(0.14, 0.09, 0.06, 0.95), 1.5)

	# Lanterne de sentinelle de porte
	draw_circle(a, 18.0, Color(0.98, 0.76, 0.25, 0.18))
	draw_circle(b, 18.0, Color(0.98, 0.76, 0.25, 0.18))


func _draw_gate_arch(g: Dictionary, fill: Color) -> void:
	var c: Variant = g.get("center", {})
	if not c is Dictionary:
		return
	var cd: Dictionary = c
	var gx := float(cd.get("x", 0.0))
	var gz := float(cd.get("z", 0.0))
	var hw := float(g.get("width_m", 16.0)) * 0.5
	var scr := Projection3D2D.to_screen(Vector3(gx, 0.0, gz))
	var w_px := hw * Projection3D2D.SCALE * 2.0
	var axis := str(g.get("axis", "z")).to_lower()

	if axis == "x":
		# Arche fortifiée E-O
		var p1 := scr + Vector2(0, -w_px * 0.55)
		var p2 := scr + Vector2(0, w_px * 0.55)
		draw_line(p1, p2, Color(0.32, 0.24, 0.16, 0.85), 5.0)
		draw_line(p1, p2, Color(0.58, 0.48, 0.34, 0.95), 2.5)
	else:
		var p1 := scr + Vector2(-w_px * 0.55, 0)
		var p2 := scr + Vector2(w_px * 0.55, 0)
		draw_line(p1, p2, Color(0.32, 0.24, 0.16, 0.85), 5.0)
		draw_line(p1, p2, Color(0.58, 0.48, 0.34, 0.95), 2.5)

func _stroke_polyline(screen: PackedVector2Array, width_px: float, fill: Color, closed: bool) -> void:
	var n := screen.size()
	var segs := n if closed else n - 1
	for i in range(segs):
		var a: Vector2 = screen[i]
		var b: Vector2 = screen[(i + 1) % n] if closed else screen[i + 1]
		var dir := b - a
		if dir.length_squared() < 0.01:
			continue
		var perp := Vector2(-dir.y, dir.x).normalized() * (width_px * 0.5)
		var quad := PackedVector2Array([a + perp, b + perp, b - perp, a - perp])
		draw_colored_polygon(quad, fill)
		# Ornières de répulseurs / roues de convois (deux sillons plus foncés)
		var r1_a := a + perp * 0.45
		var r1_b := b + perp * 0.45
		var r2_a := a - perp * 0.45
		var r2_b := b - perp * 0.45
		draw_line(r1_a, r1_b, Color(0.38, 0.30, 0.20, 0.22), 1.0)
		draw_line(r2_a, r2_b, Color(0.38, 0.30, 0.20, 0.22), 1.0)
		# Bordures de piste au trait discret
		draw_line(a + perp, b + perp, Color(0.35, 0.28, 0.18, 0.35), 1.0)
		draw_line(a - perp, b - perp, Color(0.35, 0.28, 0.18, 0.35), 1.0)

func _draw_prop(p: Dictionary) -> void:
	var cx := float(p.get("x", 0.0))
	var cz := float(p.get("z", 0.0))
	var center := Projection3D2D.to_screen(Vector3(cx, 0.0, cz))
	var kind := str(p.get("kind", "crate"))
	var fill := _color_for_kind(kind)
	if p.has("color") and typeof(p.get("color")) == TYPE_STRING:
		fill = Color.html(str(p.get("color")))
	match kind:
		"crate_stack":
			_draw_crate_stack(center, fill)
		"stall":
			_draw_stall(center, p, fill)
		"lamp":
			_draw_lamp(center, p, fill)
		"bench":
			_draw_bench(center, p, fill)
		"table":
			_draw_table(center, p, fill)
		"barrier":
			_draw_barrier(center, p, fill)
		"monument":
			_draw_monument(center, fill)
		"oasis_pool":
			_draw_oasis_pool(center, p)
		"palm_tree":
			_draw_palm_tree(center, p)
		"stone_arch":
			_draw_stone_arch(center, p)
		_:
			var fp: Variant = p.get("footprint", null)
			if fp is Dictionary:
				_draw_footprint(center, fp as Dictionary, fill, kind)
			else:
				var size_m := float(p.get("size_m", 4.0))
				var half_px := size_m * 0.5 * Projection3D2D.SCALE
				var rect := Rect2(center - Vector2(half_px, half_px), Vector2(half_px * 2.0, half_px * 2.0))
				draw_rect(rect, Color(fill.r, fill.g, fill.b, 0.4))
				draw_rect(rect, fill, false, 1.2)
	if show_prop_labels:
		var label := str(p.get("label", ""))
		if label != "":
			draw_string(
				ThemeDB.fallback_font,
				center + Vector2(-label.length() * 3.0, -10.0),
				label,
				HORIZONTAL_ALIGNMENT_LEFT,
				-1,
				10,
				Color(0.95, 0.9, 0.8, 0.75)
			)

func _draw_crate_stack(center: Vector2, fill: Color) -> void:
	var s := 5.0 * Projection3D2D.SCALE
	var offsets := [Vector2.ZERO, Vector2(s * 0.35, -s * 0.2), Vector2(-s * 0.3, s * 0.25)]
	for off in offsets:
		var rect := Rect2(center + off - Vector2(s, s) * 0.5, Vector2(s, s))
		draw_rect(rect, Color(fill.r * 0.7, fill.g * 0.7, fill.b * 0.7, 0.85))
		draw_rect(rect, fill, false, 1.0)

func _draw_stall(center: Vector2, p: Dictionary, fill: Color) -> void:
	var fp: Dictionary = p.get("footprint", {"w_m": 6.0, "h_m": 4.0})
	var w := float(fp.get("w_m", 6.0)) * Projection3D2D.SCALE
	var h := float(fp.get("h_m", 4.0)) * Projection3D2D.SCALE
	var yaw := deg_to_rad(float(fp.get("yaw_deg", 0.0)))
	var xf := Transform2D(yaw, center)
	var base := PackedVector2Array([
		Vector2(-w * 0.5, -h * 0.5), Vector2(w * 0.5, -h * 0.5),
		Vector2(w * 0.5, h * 0.5), Vector2(-w * 0.5, h * 0.5),
	])
	for i in base.size():
		base[i] = xf * base[i]
	draw_colored_polygon(base, Color(fill.r, fill.g, fill.b, 0.55))
	draw_polyline(base, fill, 1.5, true)
	var awning := PackedVector2Array([
		xf * Vector2(-w * 0.55, -h * 0.5),
		xf * Vector2(w * 0.55, -h * 0.5),
		xf * Vector2(w * 0.35, -h * 0.5 - h * 0.45),
		xf * Vector2(-w * 0.35, -h * 0.5 - h * 0.45),
	])
	draw_colored_polygon(awning, Color(fill.r, fill.g * 0.85, fill.b * 0.7, 0.7))
	draw_polyline(awning, fill.lightened(0.15), 1.2, true)

func _draw_lamp(center: Vector2, p: Dictionary, fill: Color) -> void:
	var r := float((p.get("footprint", {}) as Dictionary).get("radius_m", 1.2)) * Projection3D2D.SCALE
	r = maxf(r, 3.0)
	draw_circle(center, r * 2.2, Color(fill.r, fill.g, fill.b, 0.12))
	draw_line(center + Vector2(0, r), center + Vector2(0, -r * 1.8), Color(0.35, 0.32, 0.28, 0.9), 1.5)
	draw_circle(center + Vector2(0, -r * 1.8), r * 0.55, fill)
	draw_arc(center + Vector2(0, -r * 1.8), r * 0.75, 0.0, TAU, 16, fill.lightened(0.2), 1.0)

func _draw_bench(center: Vector2, p: Dictionary, fill: Color) -> void:
	var fp: Dictionary = p.get("footprint", {"w_m": 4.0, "h_m": 1.2})
	var w := float(fp.get("w_m", 4.0)) * Projection3D2D.SCALE
	var h := float(fp.get("h_m", 1.2)) * Projection3D2D.SCALE
	var rect := Rect2(center - Vector2(w, h) * 0.5, Vector2(w, h))
	draw_rect(rect, Color(fill.r, fill.g, fill.b, 0.75))
	draw_rect(rect, fill.darkened(0.15), false, 1.0)
	draw_line(rect.position + Vector2(0, h * 0.35), rect.end - Vector2(0, h * 0.35), fill.darkened(0.25), 1.0)

func _draw_table(center: Vector2, p: Dictionary, fill: Color) -> void:
	var fp: Dictionary = p.get("footprint", {"w_m": 2.5, "h_m": 2.5})
	var w := float(fp.get("w_m", 2.5)) * Projection3D2D.SCALE
	draw_circle(center, w * 0.5, Color(fill.r, fill.g, fill.b, 0.65))
	draw_arc(center, w * 0.5, 0.0, TAU, 14, fill.darkened(0.1), 1.2)

func _draw_barrier(center: Vector2, p: Dictionary, fill: Color) -> void:
	var fp: Dictionary = p.get("footprint", {"w_m": 12.0, "h_m": 2.0})
	var w := float(fp.get("w_m", 12.0)) * Projection3D2D.SCALE
	var h := float(fp.get("h_m", 2.0)) * Projection3D2D.SCALE
	var rect := Rect2(center - Vector2(w, h) * 0.5, Vector2(w, h))
	draw_rect(rect, Color(fill.r, fill.g, fill.b, 0.65))
	var stripes := int(w / 8.0)
	for i in range(stripes):
		var x0 := rect.position.x + float(i) * (w / float(stripes))
		draw_line(Vector2(x0, rect.position.y), Vector2(x0 + 4.0, rect.end.y), Color(0.9, 0.75, 0.3, 0.55), 1.5)

func _draw_monument(center: Vector2, fill: Color) -> void:
	draw_circle(center, 8.0, Color(fill.r, fill.g, fill.b, 0.35))
	draw_circle(center, 5.0, fill)
	draw_line(center + Vector2(0, 5), center + Vector2(0, -14), Color(fill.r, fill.g, fill.b, 0.85), 2.0)
	draw_circle(center + Vector2(0, -14), 3.5, fill.lightened(0.1))

func _draw_footprint(center: Vector2, fp: Dictionary, fill: Color, kind: String) -> void:
	var shape := str(fp.get("shape", "rect"))
	var fa := float(_defaults.get("prop_fill_alpha", 0.35))
	var sa := float(_defaults.get("prop_stroke_alpha", 0.9))
	if shape == "circle":
		var r := float(fp.get("radius_m", 2.0)) * Projection3D2D.SCALE
		draw_circle(center, r, Color(fill.r, fill.g, fill.b, fa))
		draw_arc(center, r, 0.0, TAU, 20, Color(fill.r, fill.g, fill.b, sa), 1.2)
		return
	var w := float(fp.get("w_m", 4.0)) * Projection3D2D.SCALE
	var h := float(fp.get("h_m", 4.0)) * Projection3D2D.SCALE
	var yaw := deg_to_rad(float(fp.get("yaw_deg", 0.0)))
	var xf := Transform2D(yaw, center)
	var pts := PackedVector2Array([
		Vector2(-w * 0.5, -h * 0.5), Vector2(w * 0.5, -h * 0.5),
		Vector2(w * 0.5, h * 0.5), Vector2(-w * 0.5, h * 0.5),
	])
	for i in pts.size():
		pts[i] = xf * pts[i]
	draw_colored_polygon(pts, Color(fill.r, fill.g, fill.b, fa))
	if kind == "fence" or kind == "barrier":
		draw_polyline(pts, Color(fill.r, fill.g, fill.b, sa), 0.8, true)
	else:
		draw_polyline(pts, Color(fill.r, fill.g, fill.b, sa), 1.2, true)

func _draw_oasis_pool(center: Vector2, p: Dictionary) -> void:
	var r := float(p.get("radius_m", 28.0)) * Projection3D2D.SCALE
	# Bord de verdure / sol humide
	draw_circle(center, r + 7.0, Color(0.35, 0.48, 0.25, 0.45))
	draw_arc(center, r + 7.0, 0.0, TAU, 32, Color(0.28, 0.38, 0.18, 0.65), 1.5)
	# Rive de galets
	draw_circle(center, r + 2.0, Color(0.48, 0.42, 0.32, 0.70))
	# Eau turquoise profonde
	draw_circle(center, r, Color(0.12, 0.48, 0.62, 0.85))
	# Reflet miroitant eau claire
	draw_circle(center + Vector2(-r * 0.22, -r * 0.22), r * 0.65, Color(0.25, 0.70, 0.85, 0.65))
	draw_arc(center, r * 0.45, 0.0, TAU, 24, Color(0.65, 0.92, 0.98, 0.45), 1.2)

func _draw_palm_tree(center: Vector2, p: Dictionary) -> void:
	var s := float(p.get("scale", 1.0)) * 14.0
	# Ombre portée de la cime
	draw_circle(center + Vector2(6.0, 7.0), s * 0.75, Color(0.12, 0.08, 0.05, 0.28))
	# Tronc / souche
	draw_circle(center, 3.8, Color(0.36, 0.25, 0.16, 0.95))
	draw_arc(center, 3.8, 0.0, TAU, 10, Color(0.20, 0.14, 0.08, 0.95), 1.0)
	# 6 grandes palmes en éventail
	var palm_col := Color(0.22, 0.46, 0.18, 0.90)
	var palm_light := Color(0.36, 0.62, 0.24, 0.85)
	for i in range(6):
		var a := (float(i) / 6.0) * TAU + 0.35
		var dir := Vector2(cos(a), sin(a))
		var tip := center + dir * s
		var side1 := center + dir.rotated(0.3) * (s * 0.45)
		var side2 := center + dir.rotated(-0.3) * (s * 0.45)
		var poly := PackedVector2Array([center, side1, tip, side2])
		draw_colored_polygon(poly, palm_col)
		draw_line(center, tip, palm_light, 1.2)

func _draw_stone_arch(center: Vector2, p: Dictionary) -> void:
	var w := float(p.get("width_m", 16.0)) * Projection3D2D.SCALE
	var rot := deg_to_rad(float(p.get("rot_deg", 0.0)))
	var xf := Transform2D(rot, center)
	var p1 := xf * Vector2(-w * 0.5, 0)
	var p2 := xf * Vector2(w * 0.5, 0)
	# Piliers
	draw_circle(p1, 5.5, Color(0.32, 0.25, 0.18, 0.95))
	draw_circle(p2, 5.5, Color(0.32, 0.25, 0.18, 0.95))
	draw_arc(p1, 5.5, 0.0, TAU, 12, Color(0.16, 0.12, 0.08, 0.95), 1.2)
	draw_arc(p2, 5.5, 0.0, TAU, 12, Color(0.16, 0.12, 0.08, 0.95), 1.2)
	# Arche
	draw_line(p1, p2, Color(0.48, 0.38, 0.26, 0.95), 4.5)
	draw_line(p1, p2, Color(0.72, 0.62, 0.46, 0.85), 2.0)

func _color_for_kind(kind: String) -> Color:
	match kind:
		"crate", "crate_stack":
			return Color(0.55, 0.4, 0.22, 1.0)
		"lamp":
			return Color(0.95, 0.85, 0.45, 1.0)
		"fence", "barrier":
			return Color(0.45, 0.4, 0.35, 1.0)
		"bench", "table":
			return Color(0.5, 0.32, 0.18, 1.0)
		"stall":
			return Color(0.77, 0.52, 0.23, 1.0)
		"monument":
			return Color(0.7, 0.48, 0.28, 1.0)
		"tank":
			return Color(0.4, 0.63, 0.66, 1.0)
	return Color(0.6, 0.55, 0.45, 1.0)

func set_visible_props(on: bool) -> void:
	visible_props = on
	queue_redraw()
