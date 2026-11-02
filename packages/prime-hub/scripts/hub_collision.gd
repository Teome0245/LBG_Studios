extends RefCounted
class_name HubCollision
## AABB bâtiments + clamp_move (port mince de hub_collision.py — même JSON client).

const HubBlueprintBuilderScript := preload("res://scripts/hub_blueprint_builder.gd")

var blocks: Array = []  # {id, min_x, max_x, min_z, max_z, door?}
var furniture_anchors: Array = []  # [{id, kind, label, pos: Vector3, interaction_type, capacity, ...}]
var size_mul: float = 1.0
var enforce_fence: bool = true
var fence_ring: Array = []
var gate_exits: Array = []
var open_fence_segments: Dictionary = {}


func reload(buildings_path: String = "") -> void:
	blocks.clear()
	furniture_anchors.clear()
	var path := buildings_path
	if path.is_empty():
		path = _default_buildings_path()
	if path.is_empty() or not FileAccess.file_exists(path):
		push_warning("[prime-hub] buildings JSON introuvable: %s" % path)
		return
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return
	var data: Variant = JSON.parse_string(f.get_as_text())
	if typeof(data) != TYPE_DICTIONARY:
		return
	var buildings: Variant = data.get("buildings", [])
	if typeof(buildings) != TYPE_ARRAY:
		push_warning("[prime-hub] buildings non-array dans %s" % path)
		return
	for item in buildings:
		if typeof(item) != TYPE_DICTIONARY:
			continue
		if str(item.get("kind", "")) == "city_gate":
			continue
		var cx := float(item.get("x", 0.0))
		var cz := float(item.get("z", 0.0))
		var bp_rel: String = str(item.get("cad_blueprint_ref", "")).strip_edges()
		if not bp_rel.is_empty():
			var bp_path := path.get_base_dir().path_join(bp_rel)
			if FileAccess.file_exists(bp_path):
				var bp: Dictionary = HubBlueprintBuilderScript.load_blueprint(bp_path)
				var bp_blocks: Array = HubBlueprintBuilderScript.blueprint_to_collision_blocks(bp, cx, cz)
				var bp_anchors: Array = HubBlueprintBuilderScript.blueprint_to_furniture_anchors(bp, cx, cz)
				if not bp_anchors.is_empty():
					furniture_anchors.append_array(bp_anchors)

		var size_m := float(item.get("size_m", 32.0))
		var half := size_m * 0.5 * size_mul
		var doors_list: Array = []
		if item.get("doors") is Array:
			for d_raw in item.get("doors"):
				if typeof(d_raw) == TYPE_DICTIONARY:
					doors_list.append(_door_corridor(d_raw, cx, cz, half))
		elif typeof(item.get("door")) == TYPE_DICTIONARY:
			doors_list.append(_door_corridor(item["door"], cx, cz, half))
		blocks.append({
			"id": str(item.get("id", item.get("kind", "building"))),
			"min_x": cx - half,
			"max_x": cx + half,
			"min_z": cz - half,
			"max_z": cz + half,
			"doors": doors_list,
		})
	_load_fence_and_gates()
	print("[prime-hub] collision blocks=%d fence_pts=%d path=%s" % [blocks.size(), fence_ring.size(), path])


func _default_buildings_path() -> String:
	var env := OS.get_environment("LBG_HUB_BUILDINGS_JSON").strip_edges()
	if not env.is_empty() and FileAccess.file_exists(env):
		return env
	var root := ProjectSettings.globalize_path("res://").rstrip("/")
	var candidates := [
		root.path_join("../prime-client/assets/maps/lost_heaven_buildings.json"),
		"/opt/lbg-hub-runtime/data/lost_heaven_buildings.json",
		root.path_join("data/lost_heaven_buildings.json"),
	]
	for p in candidates:
		if FileAccess.file_exists(p):
			return p
	return candidates[0]


func _default_props_path() -> String:
	var env := OS.get_environment("LBG_HUB_PROPS_JSON").strip_edges()
	if not env.is_empty() and FileAccess.file_exists(env):
		return env
	var root := ProjectSettings.globalize_path("res://").rstrip("/")
	var candidates := [
		root.path_join("../prime-client/assets/maps/lost_heaven_props.json"),
		"/opt/lbg-hub-runtime/data/lost_heaven_props.json",
		root.path_join("data/lost_heaven_props.json"),
	]
	for p in candidates:
		if FileAccess.file_exists(p):
			return p
	return candidates[0]


func _load_fence_and_gates(props_path: String = "") -> void:
	fence_ring.clear()
	gate_exits.clear()
	open_fence_segments.clear()
	var path := props_path
	if path.is_empty():
		path = _default_props_path()
	if path.is_empty() or not FileAccess.file_exists(path):
		return
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return
	var data: Variant = JSON.parse_string(f.get_as_text())
	if typeof(data) != TYPE_DICTIONARY:
		return
	var d: Dictionary = data
	var gates: Variant = d.get("gate_exits", [])
	if typeof(gates) == TYPE_ARRAY:
		gate_exits = gates
		for g in gates:
			if typeof(g) == TYPE_DICTIONARY:
				for idx in g.get("fence_open_segment_indices", []):
					open_fence_segments[int(idx)] = true
	for item in d.get("paths", []):
		if typeof(item) != TYPE_DICTIONARY:
			continue
		if str(item.get("id", "")) != "path:lh_perimeter_fence":
			continue
		for pt in item.get("points", []):
			if typeof(pt) == TYPE_DICTIONARY:
				fence_ring.append(Vector2(float(pt.get("x", 0.0)), float(pt.get("z", 0.0))))
		break


func _door_corridor(door: Dictionary, cx: float, cz: float, half: float) -> Dictionary:
	var face := str(door.get("face", "south")).to_lower()
	var hw := float(door.get("width_m", 12.0)) * 0.5
	var depth := float(door.get("depth_m", 14.0))
	var apron := float(door.get("apron_m", 8.0))
	match face:
		"north":
			return {"min_x": cx - hw, "max_x": cx + hw, "min_z": cz + half - depth, "max_z": cz + half + apron}
		"south":
			return {"min_x": cx - hw, "max_x": cx + hw, "min_z": cz - half - apron, "max_z": cz - half + depth}
		"east":
			return {"min_x": cx + half - depth, "max_x": cx + half + apron, "min_z": cz - hw, "max_z": cz + hw}
		_:
			return {"min_x": cx - half - apron, "max_x": cx - half + depth, "min_z": cz - hw, "max_z": cz + hw}


func _in_door(doors, x: float, z: float) -> bool:
	if doors == null:
		return false
	if typeof(doors) == TYPE_ARRAY:
		for d in doors:
			if typeof(d) == TYPE_DICTIONARY:
				if float(d["min_x"]) <= x and x <= float(d["max_x"]) and float(d["min_z"]) <= z and z <= float(d["max_z"]):
					return true
		return false
	elif typeof(doors) == TYPE_DICTIONARY:
		return float(doors["min_x"]) <= x and x <= float(doors["max_x"]) and float(doors["min_z"]) <= z and z <= float(doors["max_z"])
	return false


func allows(x: float, z: float) -> bool:
	for b in blocks:
		var min_x: float = float(b["min_x"])
		var max_x: float = float(b["max_x"])
		var min_z: float = float(b["min_z"])
		var max_z: float = float(b["max_z"])
		if min_x <= x and x <= max_x and min_z <= z and z <= max_z:
			var wall_th := 2.2
			# Pièce creuse visitable : l'intérieur du bâtiment est praticable pour les joueurs et les PNJ
			if x > min_x + wall_th and x < max_x - wall_th and z > min_z + wall_th and z < max_z - wall_th:
				continue
			# Ouverture des portes : franchissable
			if _in_door(b.get("doors", b.get("door")), x, z):
				continue
			# Mur extérieur périphérique : bloqué
			return false
	return true


func nearest_walkable(x: float, z: float, radius: float = 120.0) -> Vector2:
	if allows(x, z):
		return Vector2(x, z)
	var best_d := INF
	var best := Vector2(x, z)
	var r := 5.0
	while r <= radius:
		for i in range(24):
			var ang := TAU * float(i) / 24.0
			var cx := x + cos(ang) * r
			var cz := z + sin(ang) * r
			if allows(cx, cz):
				var d := Vector2(cx - x, cz - z).length()
				if d < best_d:
					best_d = d
					best = Vector2(cx, cz)
		if best_d < INF:
			return best
		r += 5.0
	return Vector2(x, z)


func _in_gate_corridor(x: float, z: float) -> bool:
	for ge in gate_exits:
		if typeof(ge) != TYPE_DICTIONARY:
			continue
		var g: Dictionary = ge
		var c = g.get("center")
		if typeof(c) != TYPE_DICTIONARY:
			continue
		var gx := float(c.get("x", 0.0))
		var gz := float(c.get("z", 0.0))
		var hw := float(g.get("width_m", 16.0)) * 0.55
		var axis := str(g.get("axis", "z")).to_lower()
		if axis == "x":
			var east := float(g.get("depth_east_m", g.get("depth_m", 32.0)))
			var west := float(g.get("depth_west_m", g.get("depth_m", 32.0)))
			if absf(z - gz) <= hw and gx - west <= x and x <= gx + east:
				return true
		else:
			var north := float(g.get("depth_north_m", g.get("depth_m", 32.0)))
			var south := float(g.get("depth_south_m", g.get("depth_m", 32.0)))
			if absf(x - gx) <= hw and gz - south <= z and z <= gz + north:
				return true
	return false


func _fence_segment_open(seg_index: int) -> bool:
	if open_fence_segments.has(seg_index):
		return true
	var n := fence_ring.size()
	if n < 2:
		return false
	var i := seg_index % n
	var j := (i + 1) % n
	var mx: float = (fence_ring[i].x + fence_ring[j].x) * 0.5
	var mz: float = (fence_ring[i].y + fence_ring[j].y) * 0.5
	for ge in gate_exits:
		if typeof(ge) != TYPE_DICTIONARY:
			continue
		var g: Dictionary = ge
		var c = g.get("center")
		if typeof(c) != TYPE_DICTIONARY:
			continue
		var gx := float(c.get("x", 0.0))
		var gz := float(c.get("z", 0.0))
		var hw := float(g.get("width_m", 16.0)) * 0.55
		if absf(mx - gx) <= hw and absf(mz - gz) <= 55.0:
			return true
	return false


func _orient(a: Vector2, b: Vector2, c: Vector2) -> float:
	return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)


func _segments_intersect(a: Vector2, b: Vector2, c: Vector2, d: Vector2) -> bool:
	return _orient(a, b, c) * _orient(a, b, d) < 0.0 and _orient(c, d, a) * _orient(c, d, b) < 0.0


func _crosses_blocked_fence(from_x: float, from_z: float, to_x: float, to_z: float) -> bool:
	if not enforce_fence or fence_ring.size() < 3:
		return false
	var a := Vector2(from_x, from_z)
	var b := Vector2(to_x, to_z)
	var n := fence_ring.size()
	for i in range(n):
		if _fence_segment_open(i):
			continue
		var p1: Vector2 = fence_ring[i]
		var p2: Vector2 = fence_ring[(i + 1) % n]
		if _segments_intersect(a, b, p1, p2):
			if _in_gate_corridor(to_x, to_z):
				continue
			return true
	return false


func clamp_move(from_x: float, from_z: float, to_x: float, to_z: float) -> Vector2:
	if _crosses_blocked_fence(from_x, from_z, to_x, to_z):
		# Essai glissement X
		if not _crosses_blocked_fence(from_x, from_z, to_x, from_z) and allows(to_x, from_z):
			return Vector2(to_x, from_z)
		# Essai glissement Z
		if not _crosses_blocked_fence(from_x, from_z, from_x, to_z) and allows(from_x, to_z):
			return Vector2(from_x, to_z)
		return Vector2(from_x, from_z)
	if allows(to_x, to_z):
		return Vector2(to_x, to_z)
	if allows(to_x, from_z):
		return Vector2(to_x, from_z)
	if allows(from_x, to_z):
		return Vector2(from_x, to_z)
	return Vector2(from_x, from_z)


func find_path(sx: float, sz: float, tx: float, tz: float, cell: float = 16.0, max_expand: int = 800) -> Array:
	## A* grille AABB — Array de Vector2 (x,z). Budget CPU borné (headless).
	var start_w := nearest_walkable(sx, sz)
	var goal_w := nearest_walkable(tx, tz)
	sx = start_w.x
	sz = start_w.y
	tx = goal_w.x
	tz = goal_w.y
	if Vector2(tx - sx, tz - sz).length() < cell * 0.5:
		return [Vector2(tx, tz)]
	# Ligne droite libre → un seul waypoint
	if allows(tx, tz) and _line_clear(sx, sz, tx, tz):
		return [Vector2(tx, tz)]

	var si := int(round(sx / cell))
	var sj := int(round(sz / cell))
	var gi := int(round(tx / cell))
	var gj := int(round(tz / cell))
	if si == gi and sj == gj:
		return [Vector2(tx, tz)]

	var open_i: PackedInt32Array = PackedInt32Array([si])
	var open_j: PackedInt32Array = PackedInt32Array([sj])
	var open_f: PackedFloat32Array = PackedFloat32Array([0.0])
	var came: Dictionary = {}
	var gscore: Dictionary = {"%d,%d" % [si, sj]: 0.0}
	came["%d,%d" % [si, sj]] = ""
	var expanded := 0
	var found_key := ""
	var neigh := [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [1, -1], [-1, 1], [-1, -1]]

	while open_i.size() > 0 and expanded < max_expand:
		var best := 0
		var best_f: float = open_f[0]
		for k in range(1, open_i.size()):
			if open_f[k] < best_f:
				best_f = open_f[k]
				best = k
		var ci: int = open_i[best]
		var cj: int = open_j[best]
		open_i.remove_at(best)
		open_j.remove_at(best)
		open_f.remove_at(best)
		var ckey := "%d,%d" % [ci, cj]
		expanded += 1
		if ci == gi and cj == gj:
			found_key = ckey
			break
		for d in neigh:
			var ni: int = ci + int(d[0])
			var nj: int = cj + int(d[1])
			var nkey := "%d,%d" % [ni, nj]
			var nx := float(ni) * cell
			var nz := float(nj) * cell
			if not allows(nx, nz):
				continue
			var step := cell * (1.414 if int(d[0]) != 0 and int(d[1]) != 0 else 1.0)
			var ng: float = float(gscore[ckey]) + step
			if gscore.has(nkey) and ng >= float(gscore[nkey]):
				continue
			came[nkey] = ckey
			gscore[nkey] = ng
			var h := absf(float(gi - ni)) + absf(float(gj - nj))
			open_i.append(ni)
			open_j.append(nj)
			open_f.append(ng + h * cell)

	if found_key.is_empty():
		var detour = detour_waypoint(sx, sz, tx, tz)
		if detour != null:
			return [detour as Vector2, Vector2(tx, tz)]
		var fb := nearest_walkable(tx, tz)
		if absf(fb.x - sx) + absf(fb.y - sz) > 1.0:
			return [fb]
		return []

	var rev: Array = []
	var cur_key := found_key
	while cur_key != "":
		rev.append(cur_key)
		cur_key = str(came.get(cur_key, ""))
	rev.reverse()
	var out: Array = []
	for i in range(rev.size()):
		if i == 0:
			continue
		if i == rev.size() - 1 or i % 2 == 0:
			var bits: PackedStringArray = str(rev[i]).split(",")
			out.append(Vector2(float(bits[0]) * cell, float(bits[1]) * cell))
	if out.is_empty():
		out.append(Vector2(tx, tz))
	else:
		var last: Vector2 = out[out.size() - 1]
		if Vector2(last.x - tx, last.y - tz).length() > 1.0:
			out.append(Vector2(tx, tz))
	return out


func _line_clear(ax: float, az: float, bx: float, bz: float, samples: int = 12) -> bool:
	for i in range(1, samples):
		var t := float(i) / float(samples)
		var x := ax + (bx - ax) * t
		var z := az + (bz - az) * t
		if not allows(x, z):
			return false
	return true


func detour_waypoint(x: float, z: float, tx: float, tz: float) -> Variant:
	## Vector2 ou null
	var steps := 16
	for i in range(1, steps + 1):
		var t := float(i) / float(steps)
		var px := x + (tx - x) * t
		var pz := z + (tz - z) * t
		for b in blocks:
			if float(b["min_x"]) <= px and px <= float(b["max_x"]) and float(b["min_z"]) <= pz and pz <= float(b["max_z"]):
				if _in_door(b.get("door"), px, pz):
					continue
				var pad := 6.0
				var candidates := [
					Vector2(float(b["min_x"]) - pad, float(b["min_z"]) - pad),
					Vector2(float(b["min_x"]) - pad, float(b["max_z"]) + pad),
					Vector2(float(b["max_x"]) + pad, float(b["min_z"]) - pad),
					Vector2(float(b["max_x"]) + pad, float(b["max_z"]) + pad),
					Vector2(float(b["min_x"]) - pad, (float(b["min_z"]) + float(b["max_z"])) * 0.5),
					Vector2(float(b["max_x"]) + pad, (float(b["min_z"]) + float(b["max_z"])) * 0.5),
					Vector2((float(b["min_x"]) + float(b["max_x"])) * 0.5, float(b["min_z"]) - pad),
					Vector2((float(b["min_x"]) + float(b["max_x"])) * 0.5, float(b["max_z"]) + pad),
				]
				var best = null
				var best_score := INF
				for c in candidates:
					if not allows(c.x, c.y):
						continue
					var score := Vector2(c.x - x, c.y - z).length() + Vector2(tx - c.x, tz - c.y).length()
					if score < best_score:
						best_score = score
						best = c
				return best
	var w := nearest_walkable(tx, tz)
	if absf(w.x - x) + absf(w.y - z) > 1.0:
		return w
	return null


func get_furniture_anchors(filter_interaction: String = "") -> Array:
	## Retourne les points d'ancrage de mobilier avec filtre optionnel par type d'interaction.
	if filter_interaction.is_empty():
		return furniture_anchors
	var filtered: Array = []
	for a: Variant in furniture_anchors:
		if a is Dictionary and str(a.get("interaction_type", "")) == filter_interaction:
			filtered.append(a)
	return filtered


func find_anchor_near(pos: Vector3, max_dist: float = 35.0, filter_interaction: String = "") -> Dictionary:
	## Trouve le point d'ancrage de mobilier le plus proche d'une position donnée.
	var candidates: Array = get_furniture_anchors(filter_interaction)
	var best: Dictionary = {}
	var best_d: float = max_dist
	for a: Variant in candidates:
		if not (a is Dictionary):
			continue
		var a_pos: Vector3 = a.get("pos", Vector3.ZERO)
		var d := pos.distance_to(a_pos)
		if d < best_d:
			best_d = d
			best = a
	return best


func is_near_craft_bench(pos: Vector3, max_dist: float = 8.0) -> Dictionary:
	## Ticket 2.2 — Vérifie si une entité est à portée d'interaction d'un établi CAO (`craft`).
	var anchor := find_anchor_near(pos, max_dist, "craft")
	if anchor.is_empty():
		return {
			"near": false,
			"anchor": {},
			"distance": INF,
		}
	var a_pos: Vector3 = anchor.get("pos", Vector3.ZERO)
	return {
		"near": true,
		"anchor": anchor,
		"distance": pos.distance_to(a_pos),
	}
