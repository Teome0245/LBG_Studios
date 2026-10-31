extends RefCounted
class_name HubBlueprintBuilder
## Décompose les blueprints CAO en segments de collision AABB pour prime-hub.
## Permet aux joueurs et PNJ d'entrer et naviguer à l'intérieur des bâtiments.

static func load_blueprint(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return {}
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if raw is Dictionary:
		return raw
	return {}


static func blueprint_to_collision_blocks(bp: Dictionary, world_x: float, world_z: float) -> Array:
	## Transforme les murs d'un blueprint en blocs de collision AABB monde.
	## Les murs avec portes sont subdivisés pour laisser le passage ouvert.
	var blocks: Array = []
	var floors: Variant = bp.get("floors", [])
	if not (floors is Array) or floors.is_empty():
		return blocks

	var floor_zero: Dictionary = floors[0]
	var walls: Variant = floor_zero.get("walls", [])
	if not (walls is Array):
		return blocks

	var b_id: String = str(bp.get("id", "building"))

	for w_idx in range(walls.size()):
		var w_item: Variant = walls[w_idx]
		if not (w_item is Dictionary):
			continue
		var w: Dictionary = w_item
		var start: Array = w.get("start", [0.0, 0.0])
		var end: Array = w.get("end", [0.0, 0.0])
		var thickness: float = float(w.get("thickness_m", 0.3))
		var doors: Variant = w.get("doors", [])

		var p1 := Vector2(float(start[0]), float(start[1]))
		var p2 := Vector2(float(end[0]), float(end[1]))
		var dir := p2 - p1
		var length := dir.length()
		if length <= 0.001:
			continue

		var norm := dir.normalized()
		var wall_id := "%s:w%d" % [b_id, w_idx]

		# Cas 1 : Pas de porte sur ce mur -> 1 seul bloc AABB englobant
		if not (doors is Array) or doors.is_empty():
			blocks.append(_segment_to_aabb(wall_id, p1, p2, thickness, world_x, world_z))
			continue

		# Cas 2 : Découpe du mur autour des portes (supporte 1 ou plusieurs portes)
		# Triage des portes par offset croissant
		var sorted_doors: Array = doors.duplicate()
		sorted_doors.sort_custom(func(a, b): return float(a.get("offset_m", 0.0)) < float(b.get("offset_m", 0.0)))

		var cur_dist := 0.0
		var sub_idx := 0
		for d_item: Variant in sorted_doors:
			if not (d_item is Dictionary):
				continue
			var d: Dictionary = d_item
			var d_off := clampf(float(d.get("offset_m", 0.0)), 0.0, length)
			var d_w := clampf(float(d.get("width_m", 1.2)), 0.0, length - d_off)

			# Segment de mur plein avant la porte
			if d_off > cur_dist + 0.05:
				var seg_start := p1 + norm * cur_dist
				var seg_end := p1 + norm * d_off
				blocks.append(_segment_to_aabb("%s_p%d" % [wall_id, sub_idx], seg_start, seg_end, thickness, world_x, world_z))
				sub_idx += 1

			# Le trou de la porte n'ajoute pas de bloc (passage libre !)
			cur_dist = d_off + d_w

		# Segment de mur restant après la dernière porte
		if cur_dist < length - 0.05:
			var seg_start := p1 + norm * cur_dist
			var seg_end := p2
			blocks.append(_segment_to_aabb("%s_p%d" % [wall_id, sub_idx], seg_start, seg_end, thickness, world_x, world_z))

	return blocks


static func blueprint_to_furniture_anchors(bp: Dictionary, world_x: float, world_z: float) -> Array:
	## Extrait les points d'ancrage et meubles d'un blueprint et calcule leurs coordonnées monde (Ticket 3.1).
	var anchors: Array = []
	var floors: Variant = bp.get("floors", [])
	if not (floors is Array) or floors.is_empty():
		return anchors

	var floor_zero: Dictionary = floors[0]
	var furniture: Variant = floor_zero.get("furniture", [])
	if not (furniture is Array):
		return anchors

	var b_id: String = str(bp.get("id", "building"))

	for f_item: Variant in furniture:
		if not (f_item is Dictionary):
			continue
		var f: Dictionary = f_item
		var fid: String = str(f.get("id", "furn"))
		var kind: String = str(f.get("kind", "generic"))
		var label: String = str(f.get("label", kind))
		var pos_rel: Array = f.get("pos", [0.0, 0.0])
		var lx: float = float(pos_rel[0]) if pos_rel.size() > 0 else 0.0
		var lz: float = float(pos_rel[1]) if pos_rel.size() > 1 else 0.0

		var wx := world_x + lx
		var wz := world_z + lz
		var pos_v3 := Vector3(wx, 0.15, wz)

		anchors.append({
			"id": "%s:%s" % [b_id, fid],
			"furn_id": fid,
			"building_id": b_id,
			"kind": kind,
			"label": label,
			"pos": pos_v3,
			"pos_arr": [wx, 0.15, wz],
			"room_id": str(f.get("room_id", "")),
			"interaction_type": str(f.get("interaction_type", "inspect")),
			"capacity": int(f.get("capacity", 1)),
			"width_m": float(f.get("width_m", 1.0)),
			"depth_m": float(f.get("depth_m", 1.0)),
			"rotation_deg": float(f.get("rotation_deg", 0.0)),
		})

	return anchors


static func _segment_to_aabb(id: String, p1: Vector2, p2: Vector2, thickness: float, wx: float, wz: float) -> Dictionary:
	var half_t := thickness * 0.5
	var min_lx := minf(p1.x, p2.x) - half_t
	var max_lx := maxf(p1.x, p2.x) + half_t
	var min_lz := minf(p1.y, p2.y) - half_t
	var max_lz := maxf(p1.y, p2.y) + half_t

	return {
		"id": id,
		"min_x": wx + min_lx,
		"max_x": wx + max_lx,
		"min_z": wz + min_lz,
		"max_z": wz + max_lz,
		"door": null,  # Les portes sont déjà découpées en ouvertures physiques
	}
