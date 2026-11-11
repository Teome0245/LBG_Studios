# hub_buildings_layer.gd — Rendu Battlemap VTT / TTRPG Dyson Logos (Plans d'architecte, Mobilier soigné, Murs d'encre hachurés, Portes ouvertes franches)
extends Node2D
class_name HubBuildingsLayer

const Projection3D2D = preload("res://scripts/projection.gd")
const BUILDINGS_PATH := "res://assets/maps/lost_heaven_buildings.json"

@export var visible_buildings: bool = true
@export var show_labels: bool = true
@export var show_doors: bool = true
@export var size_multiplier: float = 1.0

var _buildings: Array = []
var _blueprint_cache: Dictionary = {}
var world_clock_data: Dictionary = {}
var night_lanterns_active: bool = false

func set_world_clock(wc: Dictionary) -> void:
	world_clock_data = wc
	var prev_lanterns := night_lanterns_active
	night_lanterns_active = bool(wc.get("night_lanterns_active", false))
	if prev_lanterns != night_lanterns_active:
		queue_redraw()

func _ready() -> void:
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
	var kind := str(b.get("kind", ""))
	# Ne pas dessiner les POI de chasse, de débris ou de portes en tant que maisons d'habitation
	if kind == "hunt_yard" or kind == "salvage_scrap" or kind == "city_gate" or kind == "spawn":
		return
	var cx := float(b.get("x", 0.0))
	var cz := float(b.get("z", 0.0))
	var size_m := float(b.get("size_m", 72.0))
	var half_px := size_m * 0.5 * Projection3D2D.SCALE * size_multiplier
	var center := Projection3D2D.to_screen(Vector3(cx, 0.0, cz))
	var rect := Rect2(center - Vector2(half_px, half_px), Vector2(half_px * 2.0, half_px * 2.0))

	# 1. Ombre portée douce solaire dynamique (Canvas of Kings)
	var shadow_off := Vector2(-6.0, 8.0)
	var shadow_alpha := 0.24
	var wm = get_parent()
	if wm and "_atmosphere" in wm and wm._atmosphere != null:
		shadow_off = wm._atmosphere.get_sun_shadow_offset()
		shadow_alpha = wm._atmosphere.get_sun_shadow_alpha()
	draw_rect(Rect2(rect.position + shadow_off, rect.size), Color(0.10, 0.08, 0.05, shadow_alpha), true)

	# 2. Sol intérieur dallé parchemin/pierre claire (style plan d'architecte Dyson Logos)
	_draw_interior_floor(rect, kind)

	# 3. Murs porteurs extérieurs d'encre sombre avec contour et hachures Dyson Logos
	var wall_th := 3.5
	draw_rect(rect, Color(0.14, 0.10, 0.07, 0.98), false, wall_th)
	_draw_dyson_wall_hatching(rect, wall_th)

	# 4. Aménagement intérieur & Mobilier VTT Dyson Logos (Comptoir, scène, lits, établis)
	_draw_generic_procedural_interior(rect, center, kind)

	# 5. Portes ouvertes & Seuils de passage francs découpés dans les murs
	if show_doors and kind != "city_gate":
		if b.get("doors") is Array:
			for d_item: Variant in b["doors"] as Array:
				if d_item is Dictionary:
					_draw_single_door_cutaway(d_item as Dictionary, rect, wall_th)
		elif b.get("door") is Dictionary:
			_draw_single_door_cutaway(b["door"] as Dictionary, rect, wall_th)

	# 6. Étiquette de bâtiment sobre et élégante (titre calligraphié d'architecte avec cartouche lisible)
	if show_labels:
		var vp := get_viewport()
		var cam := vp.get_camera_2d() if vp else null
		var z_val: float = cam.zoom.x if cam else 1.0
		# Ne pas polluer l'écran au grand dézoom stratégique (laisse respirer la vue d'ensemble)
		if z_val >= 0.7:
			var raw_label := str(b.get("label", ""))
			if raw_label != "":
				var short_lbl := _compact_french_building_label(raw_label)
				var font := ThemeDB.fallback_font
				if font:
					var fsize := 10
					var str_w := font.get_string_size(short_lbl, HORIZONTAL_ALIGNMENT_CENTER, -1, fsize).x
					var text_pos := Vector2(center.x - str_w * 0.5, rect.position.y - 8.0)
					var cartouche := Rect2(text_pos.x - 5.0, text_pos.y - fsize + 1.0, str_w + 10.0, fsize + 3.0)
					draw_rect(cartouche, Color(0.12, 0.08, 0.05, 0.85), true)
					draw_rect(cartouche, Color(0.68, 0.58, 0.44, 0.90), false, 1.0)
					draw_string(font, text_pos + Vector2(1, 1), short_lbl, HORIZONTAL_ALIGNMENT_LEFT, -1, fsize, Color(0.04, 0.02, 0.01, 0.95))
					draw_string(font, text_pos, short_lbl, HORIZONTAL_ALIGNMENT_LEFT, -1, fsize, Color(0.98, 0.94, 0.86, 0.98))


func _draw_interior_floor(rect: Rect2, kind: String) -> void:
	var inner := rect.grow(-2.5)
	# Fonds clairs et chauds façon papier millimétré / pierre taillée Dyson Logos
	var floor_col := Color(0.90, 0.87, 0.81, 0.98)
	match kind:
		"cantina", "inn":
			floor_col = Color(0.88, 0.83, 0.75, 0.98) # Teinte bois blond & grès de taverne
		"clinic":
			floor_col = Color(0.92, 0.94, 0.93, 0.98) # Dalles claires cliniques
		"trainer_artisan", "shops", "craft":
			floor_col = Color(0.87, 0.83, 0.77, 0.98) # Sol d'atelier mécatronique
		"bank", "town_hall":
			floor_col = Color(0.89, 0.86, 0.80, 0.98) # Dalles régulières de salle civique
		"trainers_combat", "training_hall":
			floor_col = Color(0.86, 0.81, 0.73, 0.98) # Sable battu & tatami de dojo
		_:
			floor_col = Color(0.89, 0.85, 0.79, 0.98)

	draw_rect(inner, floor_col, true)

	# Quadrillage discret régulier d'architecte (pas de 8px)
	var step := 8.0
	var col_grid := Color(0.28, 0.22, 0.16, 0.12)
	var gx := inner.position.x
	while gx <= inner.end.x:
		draw_line(Vector2(gx, inner.position.y), Vector2(gx, inner.end.y), col_grid, 1.0)
		gx += step
	var gy := inner.position.y
	while gy <= inner.end.y:
		draw_line(Vector2(inner.position.x, gy), Vector2(inner.end.x, gy), col_grid, 1.0)
		gy += step


func _draw_dyson_wall_hatching(rect: Rect2, wall_th: float) -> void:
	# Petites hachures d'architecte (cross-hatching) sur l'extérieur des murs
	var col_hatch := Color(0.20, 0.15, 0.10, 0.45)
	var h_len := 4.0
	var step := 7.0

	# Mur Nord (hachures vers le haut)
	var x := rect.position.x
	while x <= rect.end.x:
		draw_line(Vector2(x, rect.position.y), Vector2(x - h_len, rect.position.y - h_len), col_hatch, 1.0)
		x += step

	# Mur Sud (hachures vers le bas)
	x = rect.position.x
	while x <= rect.end.x:
		draw_line(Vector2(x, rect.end.y), Vector2(x + h_len, rect.end.y + h_len), col_hatch, 1.0)
		x += step

	# Mur Ouest (hachures vers la gauche)
	var y := rect.position.y
	while y <= rect.end.y:
		draw_line(Vector2(rect.position.x, y), Vector2(rect.position.x - h_len, y + h_len), col_hatch, 1.0)
		y += step

	# Mur Est (hachures vers la droite)
	y = rect.position.y
	while y <= rect.end.y:
		draw_line(Vector2(rect.end.x, y), Vector2(rect.end.x + h_len, y - h_len), col_hatch, 1.0)
		y += step


func _draw_generic_procedural_interior(rect: Rect2, center: Vector2, kind: String) -> void:
	var w := rect.size.x
	var h := rect.size.y
	var col_wood := Color(0.42, 0.28, 0.16, 0.95)
	var col_metal := Color(0.35, 0.38, 0.42, 0.95)
	var col_detail := Color(0.20, 0.14, 0.08, 0.95)

	match kind:
		"cantina":
			# Piste centrale de danse / salon ouverte (espace de circulation principal)
			var dance_r := minf(w, h) * 0.22
			draw_circle(center, dance_r, Color(0.48, 0.35, 0.22, 0.70))
			draw_arc(center, dance_r, 0.0, TAU, 32, Color(0.78, 0.62, 0.38, 0.85), 1.5)
			draw_arc(center, dance_r * 0.5, 0.0, TAU, 24, Color(0.78, 0.62, 0.38, 0.45), 1.0)

			# 1. Grand comptoir de bar en fer à cheval au Nord-Ouest (Jax Moro)
			var bar_x := rect.position.x + w * 0.12
			var bar_y := rect.position.y + h * 0.18
			var bar_w := w * 0.25
			var bar_h := h * 0.32
			# Étagères arrière du bar
			draw_rect(Rect2(bar_x, bar_y, 4.0, bar_h), Color(0.28, 0.18, 0.10, 0.95), true)
			# Comptoir avant en L
			var bar_front1 := Rect2(bar_x + 9.0, bar_y, 6.0, bar_h)
			var bar_front2 := Rect2(bar_x + 9.0, bar_y + bar_h - 6.0, bar_w - 9.0, 6.0)
			draw_rect(bar_front1, col_wood, true)
			draw_rect(bar_front1, col_detail, false, 1.0)
			draw_rect(bar_front2, col_wood, true)
			draw_rect(bar_front2, col_detail, false, 1.0)
			# Tabourets de bar alignés
			for sy in [0.24, 0.36, 0.48]:
				var stool_pos := Vector2(bar_x + 18.0, rect.position.y + h * sy)
				draw_circle(stool_pos, 2.8, Color(0.68, 0.45, 0.22, 0.95))
				draw_circle(stool_pos, 2.8, col_detail, false, 0.8)

			# 2. Scène live surélevée à l'Est pour les artistes et danseurs
			var stage_w := w * 0.28
			var stage_h := h * 0.45
			var stage_rect := Rect2(rect.end.x - stage_w - 6.0, center.y - stage_h * 0.5, stage_w, stage_h)
			draw_rect(stage_rect, Color(0.52, 0.34, 0.18, 0.98), true)
			draw_rect(stage_rect, Color(0.95, 0.82, 0.38, 0.95), false, 2.0)
			# Marches d'accès en bois clair
			draw_line(Vector2(stage_rect.position.x - 3.0, stage_rect.position.y + 4.0), Vector2(stage_rect.position.x - 3.0, stage_rect.end.y - 4.0), col_detail, 1.5)
			# Spots de scène et micro
			draw_circle(stage_rect.position + Vector2(6.0, 6.0), 3.0, Color(1.0, 0.92, 0.50, 0.95))
			draw_circle(Vector2(stage_rect.position.x + 6.0, stage_rect.end.y - 6.0), 3.0, Color(1.0, 0.92, 0.50, 0.95))
			draw_circle(stage_rect.get_center(), 2.0, Color(0.85, 0.88, 0.95, 0.95)) # Pied micro

			# 3. Salons / Alcôves avec banquettes en U (Booth Seating SWG) le long des murs
			var booths: Array[Vector2] = [
				Vector2(center.x - w * 0.08, rect.position.y + h * 0.18), # Nord-Centre
				Vector2(center.x + w * 0.16, rect.position.y + h * 0.18), # Nord-Est
				Vector2(center.x - w * 0.08, rect.end.y - h * 0.18),     # Sud-Centre
				Vector2(center.x + w * 0.16, rect.end.y - h * 0.18),     # Sud-Est
			]
			for bp: Vector2 in booths:
				var is_north: bool = bp.y < center.y
				# Banquette en arc de cercle le long du mur
				var arc_start: float = PI if is_north else 0.0
				var arc_end: float = TAU if is_north else PI
				draw_arc(bp, 11.0, arc_start, arc_end, 16, Color(0.55, 0.22, 0.18, 0.95), 4.0)
				# Table ronde centrale
				draw_circle(bp, 4.5, col_wood)
				draw_circle(bp, 4.5, col_detail, false, 1.0)
				# Lampe de table
				draw_circle(bp, 1.8, Color(1.0, 0.85, 0.35, 0.95))

		"clinic":
			# Lits d'examen médicaux ordonnés avec draps et oreillers
			var bed_w := w * 0.16
			var bed_h := h * 0.28
			var beds := [
				Rect2(rect.position.x + w * 0.12, rect.position.y + h * 0.16, bed_w, bed_h),
				Rect2(rect.position.x + w * 0.34, rect.position.y + h * 0.16, bed_w, bed_h),
				Rect2(rect.end.x - w * 0.28, rect.position.y + h * 0.16, bed_w, bed_h),
			]
			for b_rect in beds:
				draw_rect(b_rect, Color(0.96, 0.98, 1.0, 0.98), true)
				draw_rect(b_rect, Color(0.35, 0.65, 0.75, 0.85), false, 1.0)
				draw_rect(Rect2(b_rect.position.x, b_rect.position.y, b_rect.size.x, 3.5), Color(0.85, 0.92, 0.95, 1.0), true)
			# Bureau médical de consultation
			var desk := Rect2(center.x - w * 0.20, rect.end.y - h * 0.32, w * 0.40, h * 0.14)
			draw_rect(desk, col_wood, true)
			draw_rect(desk, col_detail, false, 1.0)
			# Cuve d'analyse / bacta circulaire avec aura turquoise
			var bacta_pos := Vector2(rect.end.x - w * 0.18, rect.end.y - h * 0.25)
			draw_circle(bacta_pos, 7.0, Color(0.20, 0.75, 0.85, 0.35))
			draw_circle(bacta_pos, 4.5, Color(0.35, 0.88, 0.95, 0.90))
			draw_circle(bacta_pos, 4.5, col_detail, false, 1.0)

		"trainer_artisan", "shops", "craft":
			# Grand établi central mécatronique avec étau et outils
			var bench := Rect2(center.x - w * 0.28, center.y - h * 0.10, w * 0.56, h * 0.20)
			draw_rect(bench, col_metal, true)
			draw_rect(bench, Color(0.95, 0.75, 0.35, 0.90), false, 1.2)
			# Étau / pièces sur l'établi
			draw_rect(Rect2(bench.position.x + 4.0, bench.position.y + 2.0, 5.0, 5.0), Color(0.20, 0.22, 0.25, 0.98), true)
			# Enclume de forge
			var anvil_pos := Vector2(rect.position.x + w * 0.20, rect.end.y - h * 0.25)
			draw_circle(anvil_pos, 4.0, Color(0.22, 0.22, 0.25, 0.98))
			draw_circle(anvil_pos, 4.0, col_detail, false, 1.0)
			# Caisses et racks de ferraille
			var crates := [
				Rect2(rect.position.x + 5.0, rect.position.y + 5.0, 8.0, 8.0),
				Rect2(rect.end.x - 13.0, rect.position.y + 5.0, 8.0, 8.0),
				Rect2(rect.end.x - 13.0, rect.end.y - 13.0, 8.0, 8.0),
			]
			for cr in crates:
				draw_rect(cr, Color(0.55, 0.40, 0.22, 0.95), true)
				draw_rect(cr, col_detail, false, 1.0)

		"bank", "town_hall":
			# Guichet transversal avec cloison d'accueil
			var counter := Rect2(rect.position.x + w * 0.15, center.y - 2.5, w * 0.70, 5.0)
			draw_rect(counter, col_wood, true)
			draw_rect(counter, Color(0.85, 0.72, 0.35, 0.9), false, 1.0)
			# Coffre-fort blindé au mur nord
			var safe := Rect2(center.x - w * 0.16, rect.position.y + 4.0, w * 0.32, 7.0)
			draw_rect(safe, Color(0.22, 0.25, 0.28, 0.98), true)
			draw_rect(safe, Color(0.95, 0.85, 0.35, 0.90), false, 1.2)
			# Roue crantée du coffre
			draw_circle(safe.get_center(), 2.2, Color(0.95, 0.85, 0.35, 0.95))

		"inn":
			# Tables communes d'auberge avec bancs
			var t1 := Rect2(center.x - w * 0.30, center.y - 4.0, w * 0.60, 8.0)
			draw_rect(t1, col_wood, true)
			draw_rect(t1, col_detail, false, 1.0)
			# Bancs de part et d'autre
			draw_rect(Rect2(t1.position.x, t1.position.y - 4.5, t1.size.x, 2.5), col_wood, true)
			draw_rect(Rect2(t1.position.x, t1.end.y + 2.0, t1.size.x, 2.5), col_wood, true)
			# Foyer de cheminée en pierre
			var fire_pos := Vector2(center.x, rect.position.y + 6.5)
			draw_circle(fire_pos, 5.5, Color(0.25, 0.20, 0.18, 0.98))
			draw_circle(fire_pos, 3.0, Color(0.98, 0.65, 0.22, 0.95))

		"trainers_combat", "training_hall":
			# Ring / Tatami central de combat
			var ring := Rect2(center.x - w * 0.26, center.y - h * 0.26, w * 0.52, h * 0.52)
			draw_rect(ring, Color(0.82, 0.76, 0.66, 0.98), true)
			draw_rect(ring, Color(0.70, 0.30, 0.20, 0.90), false, 1.5)
			# Mannequins de frappe dans les coins
			draw_circle(Vector2(rect.position.x + 8.0, rect.position.y + 8.0), 3.0, col_wood)
			draw_circle(Vector2(rect.end.x - 8.0, rect.position.y + 8.0), 3.0, col_wood)

		_:
			# Cloison intérieure partielle d'architecte
			draw_line(Vector2(rect.position.x + w * 0.45, rect.position.y + 4.0), Vector2(rect.position.x + w * 0.45, center.y), col_detail, 2.0)


func _draw_single_door_cutaway(door: Dictionary, rect: Rect2, wall_th: float) -> void:
	var face := str(door.get("face", "south")).to_lower()
	var door_len := maxf(18.0, rect.size.x * 0.26)
	var p_door := Vector2.ZERO
	var cut_th := wall_th + 6.0 # Épaisseur suffisante pour découper franchement le mur

	match face:
		"north":
			p_door = Vector2(rect.get_center().x, rect.position.y)
			draw_line(p_door - Vector2(door_len * 0.5, 0), p_door + Vector2(door_len * 0.5, 0), Color(0.90, 0.87, 0.81, 1.0), cut_th)
			# Seuil de pierre taillée
			draw_rect(Rect2(p_door.x - door_len * 0.5, p_door.y - 4.0, door_len, 5.0), Color(0.65, 0.58, 0.48, 0.95), true)
			draw_circle(p_door - Vector2(door_len * 0.5, 0), 2.2, Color(0.20, 0.15, 0.10, 1.0))
			draw_circle(p_door + Vector2(door_len * 0.5, 0), 2.2, Color(0.20, 0.15, 0.10, 1.0))
		"south":
			p_door = Vector2(rect.get_center().x, rect.end.y)
			draw_line(p_door - Vector2(door_len * 0.5, 0), p_door + Vector2(door_len * 0.5, 0), Color(0.90, 0.87, 0.81, 1.0), cut_th)
			draw_rect(Rect2(p_door.x - door_len * 0.5, p_door.y - 1.0, door_len, 5.0), Color(0.65, 0.58, 0.48, 0.95), true)
			draw_circle(p_door - Vector2(door_len * 0.5, 0), 2.2, Color(0.20, 0.15, 0.10, 1.0))
			draw_circle(p_door + Vector2(door_len * 0.5, 0), 2.2, Color(0.20, 0.15, 0.10, 1.0))
		"east":
			p_door = Vector2(rect.end.x, rect.get_center().y)
			draw_line(p_door - Vector2(0, door_len * 0.5), p_door + Vector2(0, door_len * 0.5), Color(0.90, 0.87, 0.81, 1.0), cut_th)
			draw_rect(Rect2(p_door.x - 1.0, p_door.y - door_len * 0.5, 5.0, door_len), Color(0.65, 0.58, 0.48, 0.95), true)
			draw_circle(p_door - Vector2(0, door_len * 0.5), 2.2, Color(0.20, 0.15, 0.10, 1.0))
			draw_circle(p_door + Vector2(0, door_len * 0.5), 2.2, Color(0.20, 0.15, 0.10, 1.0))
		_: # west
			p_door = Vector2(rect.position.x, rect.get_center().y)
			draw_line(p_door - Vector2(0, door_len * 0.5), p_door + Vector2(0, door_len * 0.5), Color(0.90, 0.87, 0.81, 1.0), cut_th)
			draw_rect(Rect2(p_door.x - 4.0, p_door.y - door_len * 0.5, 5.0, door_len), Color(0.65, 0.58, 0.48, 0.95), true)
			draw_circle(p_door - Vector2(0, door_len * 0.5), 2.2, Color(0.20, 0.15, 0.10, 1.0))
			draw_circle(p_door + Vector2(0, door_len * 0.5), 2.2, Color(0.20, 0.15, 0.10, 1.0))

	# Lanterne dorée d'entrée de bâtiment
	draw_circle(p_door, 3.0, Color(1.0, 0.92, 0.50, 0.98))
	draw_circle(p_door, 7.0, Color(1.0, 0.85, 0.30, 0.22))


func _compact_french_building_label(lbl: String) -> String:
	var low := lbl.to_lower()
	if "perle" in low or "cantina" in low:
		return "Cantina La Perle"
	if "médic" in low or "medic" in low or "clinique" in low:
		return "Centre Médical"
	if "commandement" in low:
		return "Poste Zalem"
	if "caserne" in low:
		return "Caserne"
	if "atelier" in low or "mécanique" in low or "artisan" in low:
		return "Atelier Méca"
	if "dépôt" in low or "ravitaillement" in low:
		return "Dépôt Nord"
	if "relais" in low or "convoi" in low:
		return "Relais Convois"
	if "barrière ouest" in low or "porte ouest" in low:
		return "Porte Ouest"
	if "barrière est" in low or "porte est" in low:
		return "Porte Est"
	if "banque" in low:
		return "Banque"
	if "mairie" in low:
		return "Mairie"
	if "auberge" in low:
		return "Auberge"
	if "marché" in low or "commerces" in low:
		return "Marché"
	if "shuttle" in low or "port" in low:
		return "Port Spatial"
	if "entraînement" in low or "training" in low:
		return "Entraînement"
	if "mission" in low or "bureau" in low:
		return "Missions"
	if "logement" in low:
		if "nord" in low or " n" in low:
			return "Logements N"
		if "sud" in low or " s" in low:
			return "Logements S"
		if "ouest" in low or " o" in low or " w" in low:
			return "Logements O"
		if "est" in low or " e" in low:
			return "Logements E"
		return "Logements"
	if "ancien" in low or "demeure" in low:
		return "Demeure Ancien"
	if "dispensaire" in low or "onguent" in low or "soins" in low:
		return "Dispensaire"
	if "bazar" in low:
		return "Grand Bazar"
	if "caravansérail" in low:
		return "Caravansérail"
	if "forge" in low:
		return "Forge Oasis"
	if "arches" in low:
		return "Arches Oasis"
	if "guet" in low or "vigie" in low:
		return "Poste Guet Est"
	if "al-khali" in low:
		return "Oasis Al-Khali"
	if "canyon" in low:
		return "Canyon Épaves"
	return lbl.split("—")[0].strip_edges()


func _get_or_load_blueprint(rel_path: String) -> Dictionary:
	if _blueprint_cache.has(rel_path):
		return _blueprint_cache[rel_path]
	var full_path := BUILDINGS_PATH.get_base_dir().path_join(rel_path)
	if not FileAccess.file_exists(full_path):
		return {}
	var f := FileAccess.open(full_path, FileAccess.READ)
	if not f:
		return {}
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if raw is Dictionary:
		_blueprint_cache[rel_path] = raw as Dictionary
		return raw as Dictionary
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
		var col_wall := Color(0.20, 0.15, 0.10, 0.95)

		if not (doors is Array) or doors.is_empty():
			var s1 := Projection3D2D.to_screen(Vector3(cx + p1.x, 0.0, cz + p1.y))
			var s2 := Projection3D2D.to_screen(Vector3(cx + p2.x, 0.0, cz + p2.y))
			draw_line(s1, s2, col_wall, 2.5)
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
					draw_line(sa, sb, col_wall, 2.5)
				cur_dist = d_off + d_w
			if cur_dist < length - 0.05:
				var pt_a := p1 + norm * cur_dist
				var sa := Projection3D2D.to_screen(Vector3(cx + pt_a.x, 0.0, cz + pt_a.y))
				var sb := Projection3D2D.to_screen(Vector3(cx + p2.x, 0.0, cz + p2.y))
				draw_line(sa, sb, col_wall, 2.5)


func set_visible_buildings(on: bool) -> void:
	visible_buildings = on
	queue_redraw()

func set_show_labels(on: bool) -> void:
	show_labels = on
	queue_redraw()

func set_show_doors(on: bool) -> void:
	show_doors = on
	queue_redraw()
