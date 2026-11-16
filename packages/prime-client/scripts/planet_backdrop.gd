# planet_backdrop.gd — Fond Désertique Infini Battlemap VTT / TTRPG (style Czepeku / Dyson Logos)
extends Node2D
class_name PlanetBackdrop

const CORE3_TO_PX: float = 0.5

@export var half_size: float = 6500.0
@export var draw_enabled: bool = true

const _SEED := 0x7A4F00

func _ready() -> void:
	# Couleur de fond par défaut unifiée avec le sable chaud de Scrapaltai (jamais de vide noir/marron sombre)
	RenderingServer.set_default_clear_color(Color(0.70, 0.60, 0.46, 1.0))
	set_process(true)

func _process(_delta: float) -> void:
	# Suivre la caméra pour un fond désertique véritablement infini sans coupure
	var vp := get_viewport()
	var cam := vp.get_camera_2d() if vp else null
	if cam:
		var cam_p := cam.global_position
		# Décalage par crans discrets de 500m pour éviter de redessiner à chaque frame
		var snapped_p := Vector2(snappedf(cam_p.x, 250.0), snappedf(cam_p.y, 250.0))
		if position != snapped_p:
			position = snapped_p
			queue_redraw()

func _draw() -> void:
	if not draw_enabled:
		return
	# Couverture infinie centrée sur le point d'ancrage local (50 km × 50 km)
	var rect := Rect2(-25000.0, -25000.0, 50000.0, 50000.0)

	# 1. Base chaude style grès / parchemin désertique
	draw_rect(rect, Color(0.70, 0.60, 0.46, 1.0))

	# 2. Quadrillage tactique discret battlemap 5 pieds / 1.5m (style Roll20/Foundry VTT)
	_draw_tactical_grid(rect)

	# 3. Grandes ondulations de dunes et formations rocheuses de désert
	_draw_dune_crescents(rect)
	_draw_rock_outcrops(rect)
	_draw_canyons_and_cliffs(rect)

	# 4. Végétation aride et grain de sable du désert
	_draw_desert_shrubs(rect)
	_draw_grain_texture(rect)


func _draw_tactical_grid(rect: Rect2) -> void:
	var step := 32.0
	var col_grid := Color(0.48, 0.38, 0.28, 0.12)
	var x := rect.position.x
	while x <= rect.end.x:
		draw_line(Vector2(x, rect.position.y), Vector2(x, rect.end.y), col_grid, 1.0)
		x += step
	var y := rect.position.y
	while y <= rect.end.y:
		draw_line(Vector2(rect.position.x, y), Vector2(rect.end.x, y), col_grid, 1.0)
		y += step


func _draw_dune_crescents(rect: Rect2) -> void:
	# Dunes naturelles en croissants (Barkhanes) isolées plutôt que des lignes infinies
	var rng := RandomNumberGenerator.new()
	rng.seed = _SEED ^ 0xD00E
	var count := 120
	for _i in range(count):
		var cx := rng.randf_range(rect.position.x * 0.7, rect.end.x * 0.7)
		var cy := rng.randf_range(rect.position.y * 0.7, rect.end.y * 0.7)
		var radius := rng.randf_range(60.0, 180.0)
		var rot := rng.randf_range(-0.4, 0.4)
		var pts_ridge := PackedVector2Array()
		var pts_shade := PackedVector2Array()
		var arc_steps := 12
		for s in range(arc_steps + 1):
			var a := lerpf(-PI * 0.6, PI * 0.6, float(s) / float(arc_steps))
			var p := Vector2(cos(a) * radius * 0.4, sin(a) * radius).rotated(rot) + Vector2(cx, cy)
			pts_ridge.append(p)
			pts_shade.append(p + Vector2(8.0, 10.0))
		# Ombre douce sous le vent de la dune
		draw_polyline(pts_shade, Color(0.44, 0.34, 0.22, 0.22), 8.0, false)
		# Crête de sable éclairée
		draw_polyline(pts_ridge, Color(0.86, 0.78, 0.62, 0.50), 3.0, false)


func _draw_rock_outcrops(rect: Rect2) -> void:
	# Affleurements de rochers de grès style VTT / Dyson Logos
	var rng := RandomNumberGenerator.new()
	rng.seed = 0x5A17 ^ _SEED
	var count := 80
	for _i in range(count):
		var rx := rng.randf_range(rect.position.x * 0.65, rect.end.x * 0.65)
		var ry := rng.randf_range(rect.position.y * 0.65, rect.end.y * 0.65)
		var r_size := rng.randf_range(12.0, 32.0)
		var rock_pts := PackedVector2Array()
		var shadow_pts := PackedVector2Array()
		var n_verts := rng.randi_range(5, 8)
		var shadow_off := Vector2(4.0, 6.0)
		for v in range(n_verts):
			var a := (float(v) / float(n_verts)) * TAU
			var rad := r_size * rng.randf_range(0.75, 1.25)
			var pt := Vector2(cos(a) * rad, sin(a) * rad * 0.7) + Vector2(rx, ry)
			rock_pts.append(pt)
			shadow_pts.append(pt + shadow_off)
		# Ombre portée douce
		draw_colored_polygon(shadow_pts, Color(0.20, 0.14, 0.08, 0.25))
		# Corps du rocher en pierre
		draw_colored_polygon(rock_pts, Color(0.48, 0.38, 0.26, 0.90))
		# Arête supérieure de roche éclairée
		draw_polyline(rock_pts, Color(0.18, 0.12, 0.07, 0.85), 1.4, true)
		# Face supérieure éclairée
		draw_circle(Vector2(rx, ry) - Vector2(2, 2), r_size * 0.35, Color(0.68, 0.58, 0.44, 0.85))


func _draw_desert_shrubs(rect: Rect2) -> void:
	# Buissons et végétation du désert disséminés
	var rng := RandomNumberGenerator.new()
	rng.seed = 0x8842 ^ _SEED
	var count := 160
	for _i in range(count):
		var px := rng.randf_range(rect.position.x * 0.6, rect.end.x * 0.6)
		var py := rng.randf_range(rect.position.y * 0.6, rect.end.y * 0.6)
		var s := rng.randf_range(3.0, 7.0)
		# Ombre
		draw_circle(Vector2(px + 2.0, py + 2.5), s, Color(0.14, 0.10, 0.06, 0.22))
		# Végétation aride (vert olive / sauge / paille)
		var shrub_col := Color(0.38, 0.42, 0.28, 0.75) if rng.randf() > 0.4 else Color(0.55, 0.48, 0.30, 0.75)
		draw_circle(Vector2(px, py), s, shrub_col)
		draw_circle(Vector2(px, py), s * 0.55, shrub_col.lightened(0.2))


func _draw_canyons_and_cliffs(rect: Rect2) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = _SEED
	var count := 56
	for i in range(count):
		rng.seed = _SEED + i * 7919
		var sx := rng.randf_range(rect.position.x, rect.end.x)
		var sy := rng.randf_range(rect.position.y, rect.end.y)
		var angle := rng.randf_range(-0.5, 0.5)
		var length := rng.randf_range(300.0, 900.0)
		var dir := Vector2(cos(angle), sin(angle))
		var w := rng.randf_range(3.0, 8.0)
		var pts := PackedVector2Array()
		var p := Vector2(sx, sy)
		pts.append(p)
		for _s in range(5):
			dir = dir.rotated(rng.randf_range(-0.35, 0.35))
			p += dir * (length / 5.0)
			pts.append(p)
		draw_polyline(pts, Color(0.30, 0.22, 0.15, 0.45), w, false)
		draw_polyline(pts, Color(0.85, 0.76, 0.60, 0.38), maxf(1.0, w * 0.3), false)


func _draw_grain_texture(rect: Rect2) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 99173
	var n := 450
	for _i in range(n):
		var p := Vector2(
			rng.randf_range(rect.position.x * 0.5, rect.end.x * 0.5),
			rng.randf_range(rect.position.y * 0.5, rect.end.y * 0.5)
		)
		var g := rng.randf_range(0.35, 0.55)
		draw_circle(p, rng.randf_range(0.8, 2.2), Color(g, g * 0.88, g * 0.70, 0.30))


func set_half_size(v: float) -> void:
	half_size = v
	queue_redraw()
