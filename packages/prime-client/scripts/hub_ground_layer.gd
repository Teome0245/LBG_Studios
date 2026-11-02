# hub_ground_layer.gd — Sol avant-poste Lost Heaven style Battlemap VTT (Dalles, Allées ouvertes, Halos de lanternes & Feux)
extends Node2D
class_name HubGroundLayer

const Projection3D2D = preload("res://scripts/projection.gd")
const BUILDINGS_PATH := "res://assets/maps/lost_heaven_buildings.json"
const PROPS_PATH := "res://assets/maps/lost_heaven_props.json"

@export var visible_ground: bool = true
@export var draw_emprise_fill: bool = true
@export var padding_m: float = 80.0

var _anchor := Vector2(4749.0, -737.0)
var _plaza_points: PackedVector2Array = PackedVector2Array()

func _ready() -> void:
	reload()

func reload() -> void:
	_plaza_points = PackedVector2Array()
	_load_plaza_ring()
	queue_redraw()

func _load_plaza_ring() -> void:
	if not FileAccess.file_exists(PROPS_PATH):
		return
	var f := FileAccess.open(PROPS_PATH, FileAccess.READ)
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if not raw is Dictionary:
		return
	for item: Variant in (raw as Dictionary).get("paths", []):
		if not item is Dictionary:
			continue
		var p: Dictionary = item
		if str(p.get("id", "")) != "path:lh_plaza_ring":
			continue
		var pts: Variant = p.get("points", [])
		if not pts is Array:
			return
		for pt: Variant in pts as Array:
			if pt is Dictionary:
				var d: Dictionary = pt
				var scr := Projection3D2D.to_screen(Vector3(float(d.get("x", 0.0)), 0.0, float(d.get("z", 0.0))))
				_plaza_points.append(scr)
		return

func _building_bounds() -> Dictionary:
	var min_x := 1.0e12
	var max_x := -1.0e12
	var min_z := 1.0e12
	var max_z := -1.0e12
	if not FileAccess.file_exists(BUILDINGS_PATH):
		return {"ok": false}
	var f := FileAccess.open(BUILDINGS_PATH, FileAccess.READ)
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if not raw is Dictionary:
		return {"ok": false}
	var doc: Dictionary = raw
	if doc.get("anchor") is Dictionary:
		var a: Dictionary = doc["anchor"]
		_anchor = Vector2(float(a.get("x", _anchor.x)), float(a.get("z", _anchor.y)))
	var arr: Variant = doc.get("buildings", [])
	if not arr is Array:
		return {"ok": false}
	for item: Variant in arr:
		if not item is Dictionary:
			continue
		var b: Dictionary = item
		var cx := float(b.get("x", 0.0))
		var cz := float(b.get("z", 0.0))
		var mul := float(MapTextureLoader.world_render_cfg().get("building_size_multiplier", 1.0))
		if mul <= 0.0:
			mul = 1.0
		var half := float(b.get("size_m", 64.0)) * 0.5 * mul + padding_m * 0.25
		min_x = minf(min_x, cx - half)
		max_x = maxf(max_x, cx + half)
		min_z = minf(min_z, cz - half)
		max_z = maxf(max_z, cz + half)
	if min_x > max_x:
		return {"ok": false}
	return {
		"ok": true,
		"min_x": min_x - padding_m,
		"max_x": max_x + padding_m,
		"min_z": min_z - padding_m,
		"max_z": max_z + padding_m,
	}

func _draw() -> void:
	if not visible_ground:
		return
	var b := _building_bounds()
	if not b.get("ok", false):
		return
	var tl := Projection3D2D.to_screen(Vector3(float(b["min_x"]), 0.0, float(b["min_z"])))
	var br := Projection3D2D.to_screen(Vector3(float(b["max_x"]), 0.0, float(b["max_z"])))
	var rect := Rect2(tl, br - tl).abs()
	var center := Projection3D2D.to_screen(Vector3(_anchor.x, 0.0, _anchor.y))

	# 1. Zone de terre battue / dalles qui s'estompe organiquement (pas de gros rectangle coupé)
	draw_circle(center, 280.0, Color(0.64, 0.54, 0.40, 0.22))
	draw_circle(center, 210.0, Color(0.66, 0.56, 0.42, 0.35))
	draw_circle(center, 140.0, Color(0.72, 0.62, 0.48, 0.55))

	# 2. Allées pavées / dalles de pierre entre les bâtiments principaux
	_draw_cobblestone_paths(rect, center)

	# 3. Plaza centrale circulaire pavée avec rosace
	draw_circle(center, 34.0, Color(0.62, 0.52, 0.38, 0.85))
	draw_arc(center, 34.0, 0.0, TAU, 48, Color(0.40, 0.32, 0.22, 0.75), 2.0)
	draw_arc(center, 20.0, 0.0, TAU, 36, Color(0.40, 0.32, 0.22, 0.50), 1.2)
	draw_circle(center, 5.0, Color(0.28, 0.22, 0.16, 0.90))

	# 4. Halos d'éclairage chaud de lanternes & feux de camp (comme l'image 2 de référence)
	_draw_warm_lighting_halos(center)


func _draw_cobblestone_paths(_rect: Rect2, center: Vector2) -> void:
	# Allées pavées reliant la rosace de la Plaza aux parvis de chaque bâtiment
	var endpoints := [
		center + Vector2(125.0, 0.0),    # Cantina La Perle (Entrée Ouest)
		center + Vector2(263.0, 0.0),    # Atelier Mécatronique
		center + Vector2(-117.0, 0.0),   # Banque de Scrapaltai (Entrée Est)
		center + Vector2(-215.0, 0.0),   # Terminal Starport
		center + Vector2(0.0, -81.0),    # Auberge de Lost Heaven (Entrée Sud)
		center + Vector2(0.0, 84.0),     # Grand Marché (Entrée Nord)
		center + Vector2(-134.5, -77.0), # Clinique / Centre Médical (Entrée Sud)
		center + Vector2(135.5, -76.0),  # Hall d'entraînement (Entrée Sud)
		center + Vector2(-134.5, 79.0),  # Mairie & Administration (Entrée Nord)
		center + Vector2(135.5, 83.0),   # Bureau des missions (Entrée Nord)
		center + Vector2(-280.0, 0.0),   # Allée vers Porte Ouest
		center + Vector2(300.0, 0.0),    # Allée vers Porte Est
	]
	for ep in endpoints:
		var target: Vector2 = ep
		draw_line(center, target, Color(0.55, 0.46, 0.34, 0.45), 12.0)
		draw_line(center, target, Color(0.46, 0.38, 0.28, 0.65), 7.0)


func _draw_warm_lighting_halos(center: Vector2) -> void:
	# Lanternes dorées ancrées devant les entrées de chaque bâtiment
	var lights := [
		center,                          # Rosace Plaza centrale
		center + Vector2(125.0, 0.0),    # Parvis Cantina La Perle
		center + Vector2(263.0, 0.0),    # Parvis Atelier Mécatronique
		center + Vector2(-117.0, 0.0),   # Parvis Banque
		center + Vector2(-215.0, 0.0),   # Parvis Terminal Starport
		center + Vector2(0.0, -81.0),    # Parvis Auberge
		center + Vector2(0.0, 84.0),     # Parvis Grand Marché
		center + Vector2(-134.5, -77.0), # Parvis Clinique
		center + Vector2(135.5, -76.0),  # Parvis Hall d'entraînement
		center + Vector2(-134.5, 79.0),  # Parvis Mairie
		center + Vector2(135.5, 83.0),   # Parvis Bureau des missions
	]
	for l_pos in lights:
		var lp: Vector2 = l_pos
		# Halo étendu et doux (comme la référence VTT nocturne)
		draw_circle(lp, 54.0, Color(0.98, 0.68, 0.18, 0.08))
		draw_circle(lp, 34.0, Color(0.98, 0.74, 0.24, 0.16))
		draw_circle(lp, 18.0, Color(0.98, 0.84, 0.32, 0.28))
		draw_circle(lp, 6.0, Color(1.0, 0.92, 0.60, 0.65))
		# Cercle de pierres de foyer
		draw_arc(lp, 4.5, 0.0, TAU, 10, Color(0.24, 0.18, 0.12, 0.9), 1.2)
		draw_circle(lp, 2.2, Color(1.0, 0.98, 0.88, 0.95))


func set_visible_ground(on: bool) -> void:
	visible_ground = on
	queue_redraw()
