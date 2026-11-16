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
		"krayt_skeleton":
			_draw_krayt_skeleton(center, p)
		"starship_wreck":
			_draw_starship_wreck(center, p)
		"boulder_cluster":
			_draw_boulder_cluster(center, p)
		"nomad_tent":
			_draw_nomad_tent(center, p)
		"mine_silo":
			_draw_mine_silo(center, p)
		"cargo_container":
			_draw_cargo_container(center, p)
		"moisture_vaporator":
			_draw_moisture_vaporator(center, p)
		"crystal_cluster":
			_draw_crystal_cluster(center, p)
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

func _draw_krayt_skeleton(center: Vector2, p: Dictionary) -> void:
	# Immense squelette de Léviathan / Dragon Krayt du désert (style SWG Tatooine Canon)
	var length_m := float(p.get("length_m", 45.0))
	var len_px := length_m * Projection3D2D.SCALE
	var yaw := deg_to_rad(float(p.get("yaw_deg", 0.0)))
	var xf := Transform2D(yaw, center)
	var col_bone := Color(0.90, 0.86, 0.76, 0.98) # Ivoire fossilisé
	var col_shadow := Color(0.18, 0.12, 0.08, 0.30)
	var col_dark := Color(0.38, 0.30, 0.22, 0.90)

	var rib_count := maxi(6, int(length_m / 4.0))
	var rib_max_span := float(p.get("width_m", 24.0)) * 0.5 * Projection3D2D.SCALE

	# 1. Ombre portée générale sous la cage thoracique
	var shadow_poly := PackedVector2Array()
	for i in range(rib_count + 1):
		var t := float(i) / float(rib_count)
		var lx := lerpf(-len_px * 0.5, len_px * 0.5, t)
		var span := sin(t * PI) * rib_max_span
		shadow_poly.append(xf * (Vector2(lx, span) + Vector2(4.0, 6.0)))
	for i in range(rib_count, -1, -1):
		var t := float(i) / float(rib_count)
		var lx := lerpf(-len_px * 0.5, len_px * 0.5, t)
		var span := sin(t * PI) * rib_max_span
		shadow_poly.append(xf * (Vector2(lx, -span) + Vector2(4.0, 6.0)))
	if shadow_poly.size() >= 3:
		draw_colored_polygon(shadow_poly, col_shadow)

	# 2. Paires de côtes émergeant du sable (arches osseuses recourbées)
	for i in range(rib_count):
		var t := float(i) / float(rib_count - 1)
		var lx := lerpf(-len_px * 0.45, len_px * 0.35, t)
		var span := sin(t * PI) * rib_max_span
		var spine_pt := xf * Vector2(lx, 0.0)

		# Côte gauche
		var tip_left := xf * Vector2(lx + span * 0.25, -span)
		var mid_left := xf * Vector2(lx - span * 0.1, -span * 0.6)
		draw_line(spine_pt, mid_left, col_dark, 2.5)
		draw_line(mid_left, tip_left, col_dark, 2.0)
		draw_line(spine_pt, mid_left, col_bone, 1.4)
		draw_line(mid_left, tip_left, col_bone, 1.0)
		draw_circle(tip_left, 1.8, col_bone)

		# Côte droite
		var tip_right := xf * Vector2(lx + span * 0.25, span)
		var mid_right := xf * Vector2(lx - span * 0.1, span * 0.6)
		draw_line(spine_pt, mid_right, col_dark, 2.5)
		draw_line(mid_right, tip_right, col_dark, 2.0)
		draw_line(spine_pt, mid_right, col_bone, 1.4)
		draw_line(mid_right, tip_right, col_bone, 1.0)
		draw_circle(tip_right, 1.8, col_bone)

	# 3. Colonne vertébrale (épine dorsale épaisse segmentée)
	for i in range(rib_count + 2):
		var t := float(i) / float(rib_count + 1)
		var lx := lerpf(-len_px * 0.5, len_px * 0.38, t)
		var p_vert := xf * Vector2(lx, 0.0)
		draw_circle(p_vert + Vector2(1.5, 2.0), 3.0, col_shadow)
		draw_circle(p_vert, 2.8, col_dark)
		draw_circle(p_vert, 2.0, col_bone)

	# 4. Crâne colossal fossilisé avec cornes de Léviathan
	var skull_pos := xf * Vector2(len_px * 0.48, 0.0)
	var skull_pts := PackedVector2Array([
		xf * Vector2(len_px * 0.38, -6.0),
		xf * Vector2(len_px * 0.55, -4.5),
		xf * Vector2(len_px * 0.60, 0.0),
		xf * Vector2(len_px * 0.55, 4.5),
		xf * Vector2(len_px * 0.38, 6.0)
	])
	draw_colored_polygon(skull_pts, col_bone)
	draw_polyline(skull_pts, col_dark, 1.5, true)
	# Orbites oculaires
	draw_circle(xf * Vector2(len_px * 0.48, -2.8), 1.8, col_dark)
	draw_circle(xf * Vector2(len_px * 0.48, 2.8), 1.8, col_dark)
	# Cornes recourbées
	var horn_l1 := xf * Vector2(len_px * 0.44, -5.0)
	var horn_l2 := xf * Vector2(len_px * 0.52, -12.0)
	var horn_r1 := xf * Vector2(len_px * 0.44, 5.0)
	var horn_r2 := xf * Vector2(len_px * 0.52, 12.0)
	draw_line(horn_l1, horn_l2, col_dark, 2.5)
	draw_line(horn_l1, horn_l2, col_bone, 1.5)
	draw_line(horn_r1, horn_r2, col_dark, 2.5)
	draw_line(horn_r1, horn_r2, col_bone, 1.5)

func _draw_starship_wreck(center: Vector2, p: Dictionary) -> void:
	# Épave de vaisseau spatial / carcasse industrielle (Scrapaltai)
	var length_m := float(p.get("length_m", 32.0))
	var len_px := length_m * Projection3D2D.SCALE
	var yaw := deg_to_rad(float(p.get("yaw_deg", 0.0)))
	var xf := Transform2D(yaw, center)
	var col_hull := Color(0.62, 0.42, 0.28, 0.98) # Métal rouillé délavé
	var col_trim := Color(0.25, 0.48, 0.58, 0.95) # Peinture de blindage bleu pétrole écaillée
	var col_dark := Color(0.18, 0.12, 0.08, 0.98)
	var col_shadow := Color(0.14, 0.10, 0.06, 0.35)

	# 1. Cratère d'impact / sable expulsé
	draw_circle(center + Vector2(4.0, 5.0), len_px * 0.55, Color(0.48, 0.38, 0.24, 0.35))

	# 2. Fuselage principal écrasé en biseau
	var body := PackedVector2Array([
		xf * Vector2(-len_px * 0.5, -len_px * 0.22),
		xf * Vector2(len_px * 0.45, -len_px * 0.12),
		xf * Vector2(len_px * 0.55, 0.0),
		xf * Vector2(len_px * 0.45, len_px * 0.12),
		xf * Vector2(-len_px * 0.5, len_px * 0.22)
	])
	draw_colored_polygon(body, col_hull)
	draw_polyline(body, col_dark, 1.8, true)

	# Bandeau de livrée écaillée
	var stripe := PackedVector2Array([
		xf * Vector2(-len_px * 0.1, -len_px * 0.18),
		xf * Vector2(len_px * 0.2, -len_px * 0.14),
		xf * Vector2(len_px * 0.2, len_px * 0.14),
		xf * Vector2(-len_px * 0.1, len_px * 0.18)
	])
	draw_colored_polygon(stripe, col_trim)
	draw_polyline(stripe, col_dark, 1.2, true)

	# 3. Tuyères de moteurs circulaires brisées à l'arrière
	var nozz1 := xf * Vector2(-len_px * 0.5, -len_px * 0.10)
	var nozz2 := xf * Vector2(-len_px * 0.5, len_px * 0.10)
	draw_circle(nozz1, 4.5, col_dark)
	draw_circle(nozz1, 3.0, Color(0.08, 0.06, 0.04, 0.98))
	draw_circle(nozz2, 4.5, col_dark)
	draw_circle(nozz2, 3.0, Color(0.08, 0.06, 0.04, 0.98))

	# 4. Aile brisée détachée dans le sable
	var wing := PackedVector2Array([
		xf * Vector2(-len_px * 0.1, len_px * 0.26),
		xf * Vector2(len_px * 0.15, len_px * 0.55),
		xf * Vector2(len_px * 0.05, len_px * 0.60),
		xf * Vector2(-len_px * 0.25, len_px * 0.32)
	])
	draw_colored_polygon(wing, col_hull.darkened(0.1))
	draw_polyline(wing, col_dark, 1.4, true)
	# Câblages / ferrailles tordues
	draw_line(xf * Vector2(0.0, len_px * 0.24), xf * Vector2(len_px * 0.08, len_px * 0.35), col_dark, 1.5)

func _draw_boulder_cluster(center: Vector2, p: Dictionary) -> void:
	# Amas de rochers massifs de grès style Dyson Logos
	var radius_m := float(p.get("radius_m", 12.0))
	var rad_px := radius_m * Projection3D2D.SCALE
	var col_rock := Color(0.52, 0.42, 0.30, 0.98)
	var col_edge := Color(0.18, 0.12, 0.08, 0.98)
	var col_light := Color(0.74, 0.64, 0.48, 0.98)
	var col_shadow := Color(0.14, 0.10, 0.06, 0.32)

	# 3 à 5 roches superposées
	var offsets := [
		Vector2.ZERO,
		Vector2(-rad_px * 0.5, -rad_px * 0.3),
		Vector2(rad_px * 0.45, -rad_px * 0.25),
		Vector2(-rad_px * 0.35, rad_px * 0.4),
		Vector2(rad_px * 0.4, rad_px * 0.35)
	]
	var scales := [1.0, 0.75, 0.8, 0.65, 0.7]

	for i in range(offsets.size()):
		var b_pos: Vector2 = center + (offsets[i] as Vector2)
		var b_rad: float = rad_px * 0.55 * float(scales[i])

		# Ombre portée
		draw_circle(b_pos + Vector2(3.5, 5.0), b_rad * 1.15, col_shadow)

		# Polygone rocheux taillé (6 sommets)
		var rock_pts := PackedVector2Array()
		var n_verts := 6
		for v in range(n_verts):
			var a := (float(v) / float(n_verts)) * TAU + float(i) * 0.8
			var r_sub: float = b_rad * (1.15 if (v % 2 == 0) else 0.85)
			rock_pts.append(b_pos + Vector2(cos(a) * r_sub, sin(a) * r_sub * 0.85))

		draw_colored_polygon(rock_pts, col_rock)
		draw_polyline(rock_pts, col_edge, 1.5, true)

		# Arête éclairée supérieure
		draw_circle(b_pos - Vector2(b_rad * 0.2, b_rad * 0.2), b_rad * 0.45, col_light)

func _draw_nomad_tent(center: Vector2, p: Dictionary) -> void:
	# Grande tente bédouine circulaire / octogonale du Ksar
	var size_m := float(p.get("size_m", 18.0))
	var rad_px := size_m * 0.5 * Projection3D2D.SCALE
	var col_cloth1 := Color(0.68, 0.26, 0.22, 0.98) # Tente rouge garance / bordeaux
	var col_cloth2 := Color(0.78, 0.68, 0.50, 0.98) # Toile écrue du désert
	var col_dark := Color(0.18, 0.10, 0.06, 0.98)
	var col_shadow := Color(0.14, 0.10, 0.06, 0.35)

	# 1. Ombre portée douce
	draw_circle(center + Vector2(4.0, 6.0), rad_px * 1.1, col_shadow)

	# 2. Piquets et cordelettes de tension rayonnantes
	var segs := 8
	for i in range(segs):
		var a := (float(i) / float(segs)) * TAU
		var p_rim := center + Vector2(cos(a), sin(a)) * rad_px
		var p_peg := center + Vector2(cos(a), sin(a)) * (rad_px * 1.35)
		draw_line(p_rim, p_peg, col_dark, 1.0)
		draw_circle(p_peg, 1.8, col_dark)

	# 3. Segments alternés de toile
	for i in range(segs):
		var a1 := (float(i) / float(segs)) * TAU
		var a2 := (float(i + 1) / float(segs)) * TAU
		var p1 := center + Vector2(cos(a1), sin(a1)) * rad_px
		var p2 := center + Vector2(cos(a2), sin(a2)) * rad_px
		var poly := PackedVector2Array([center, p1, p2])
		var col := col_cloth1 if (i % 2 == 0) else col_cloth2
		draw_colored_polygon(poly, col)
		draw_line(center, p1, col_dark, 1.2)
		draw_line(p1, p2, col_dark, 1.4)

	# 4. Mât central et chapeau de tente
	draw_circle(center, rad_px * 0.22, col_dark)
	draw_circle(center, rad_px * 0.15, Color(0.85, 0.75, 0.45, 0.98))
	draw_arc(center, rad_px * 0.22, 0.0, TAU, 12, col_dark, 1.2)

	# 5. Auvent d'entrée déployé au Sud
	var awning := PackedVector2Array([
		center + Vector2(-rad_px * 0.45, rad_px * 0.85),
		center + Vector2(rad_px * 0.45, rad_px * 0.85),
		center + Vector2(rad_px * 0.65, rad_px * 1.4),
		center + Vector2(-rad_px * 0.65, rad_px * 1.4)
	])
	draw_colored_polygon(awning, col_cloth2)
	draw_polyline(awning, col_dark, 1.4, true)
	# Intérieur ombragé du seuil
	draw_colored_polygon(PackedVector2Array([
		center + Vector2(-rad_px * 0.35, rad_px * 0.85),
		center + Vector2(rad_px * 0.35, rad_px * 0.85),
		center + Vector2(rad_px * 0.25, rad_px * 0.6),
		center + Vector2(-rad_px * 0.25, rad_px * 0.6)
	]), col_dark)

func _draw_mine_silo(center: Vector2, p: Dictionary) -> void:
	# Cuve industrielle / silo de minerai pour Zalem
	var radius_m := float(p.get("radius_m", 14.0))
	var rad_px := radius_m * Projection3D2D.SCALE
	var col_metal := Color(0.45, 0.48, 0.52, 0.98) # Acier industriel
	var col_dark := Color(0.16, 0.14, 0.12, 0.98)
	var col_shadow := Color(0.14, 0.10, 0.06, 0.35)

	# Ombre
	draw_circle(center + Vector2(4.0, 6.0), rad_px * 1.05, col_shadow)
	# Base circulaire
	draw_circle(center, rad_px, col_metal)
	draw_arc(center, rad_px, 0.0, TAU, 28, col_dark, 2.0)
	# Passerelle périphérique
	draw_arc(center, rad_px * 0.75, 0.0, TAU, 24, col_dark, 1.2)
	# Dôme supérieur avec rivets
	draw_circle(center, rad_px * 0.45, col_metal.lightened(0.15))
	draw_arc(center, rad_px * 0.45, 0.0, TAU, 16, col_dark, 1.4)
	# Valve centrale
	draw_circle(center, 3.0, Color(0.85, 0.45, 0.20, 0.98))

func _draw_cargo_container(center: Vector2, p: Dictionary) -> void:
	var w_m := float(p.get("w_m", 12.0))
	var h_m := float(p.get("h_m", 6.0))
	var w := w_m * Projection3D2D.SCALE
	var h := h_m * Projection3D2D.SCALE
	var yaw := deg_to_rad(float(p.get("yaw_deg", 0.0)))
	var xf := Transform2D(yaw, center)
	var rect_pts := PackedVector2Array([
		xf * Vector2(-w * 0.5, -h * 0.5),
		xf * Vector2(w * 0.5, -h * 0.5),
		xf * Vector2(w * 0.5, h * 0.5),
		xf * Vector2(-w * 0.5, h * 0.5)
	])
	var col_cont := Color(0.72, 0.45, 0.22, 0.98) if p.get("color") == null else Color.html(str(p.get("color")))
	var col_dark := Color(0.16, 0.12, 0.08, 0.98)
	# Ombre
	var shadow_pts := PackedVector2Array([
		rect_pts[0] + Vector2(3.0, 4.0), rect_pts[1] + Vector2(3.0, 4.0),
		rect_pts[2] + Vector2(3.0, 4.0), rect_pts[3] + Vector2(3.0, 4.0)
	])
	draw_colored_polygon(shadow_pts, Color(0.14, 0.10, 0.06, 0.30))
	draw_colored_polygon(rect_pts, col_cont)
	draw_polyline(rect_pts, col_dark, 1.5, true)
	# Nervures de container
	for i in range(1, 4):
		var t := float(i) / 4.0
		var lx := lerpf(-w * 0.5, w * 0.5, t)
		draw_line(xf * Vector2(lx, -h * 0.5), xf * Vector2(lx, h * 0.5), col_dark, 1.0)

func _draw_moisture_vaporator(center: Vector2, p: Dictionary) -> void:
	# Condenseur d'humidité atmosphérique tripode canon SWG
	var s := float(p.get("scale", 1.0)) * 12.0
	var col_steel := Color(0.72, 0.76, 0.82, 0.98)
	var col_dark := Color(0.18, 0.16, 0.14, 0.98)
	var col_shadow := Color(0.14, 0.10, 0.06, 0.30)
	# Ombre allongée du mât
	draw_line(center + Vector2(2.0, 3.0), center + Vector2(16.0, 20.0), col_shadow, 3.5)
	# Embase tripode (3 pieds à 120°)
	for i in range(3):
		var a := (float(i) / 3.0) * TAU - PI * 0.5
		var foot := center + Vector2(cos(a), sin(a)) * s
		draw_line(center, foot, col_dark, 2.4)
		draw_line(center, foot, col_steel, 1.2)
		draw_circle(foot, 2.2, col_dark)
	# Mât central cylindrique
	draw_circle(center, 4.5, col_dark)
	draw_circle(center, 3.2, col_steel)
	# Condenseur supérieur & capteur
	draw_circle(center, 1.8, Color(0.25, 0.65, 0.85, 0.98))

func _draw_crystal_cluster(center: Vector2, p: Dictionary) -> void:
	# Bouquet de cristaux géodiques d'améthyste violette
	var rad := float(p.get("radius_m", 6.0)) * Projection3D2D.SCALE
	var col_cryst := Color(0.68, 0.28, 0.82, 0.95)
	var col_light := Color(0.92, 0.70, 0.98, 0.98)
	var col_dark := Color(0.24, 0.08, 0.32, 0.98)
	var col_shadow := Color(0.14, 0.08, 0.16, 0.35)
	draw_circle(center + Vector2(3.0, 4.0), rad * 1.1, col_shadow)
	# 5 aiguilles de cristal
	for i in range(5):
		var a := (float(i) / 5.0) * TAU + 0.2
		var len_c := rad * (0.8 + 0.5 * sin(float(i) * 2.3))
		var tip := center + Vector2(cos(a), sin(a)) * len_c
		var s1 := center + Vector2(cos(a + 0.3), sin(a + 0.3)) * (rad * 0.4)
		var s2 := center + Vector2(cos(a - 0.3), sin(a - 0.3)) * (rad * 0.4)
		draw_colored_polygon(PackedVector2Array([center, s1, tip, s2]), col_cryst)
		draw_polyline(PackedVector2Array([s1, tip, s2]), col_dark, 1.2, false)
		draw_line(center, tip, col_light, 1.0)
	draw_circle(center, 3.0, col_dark)

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
