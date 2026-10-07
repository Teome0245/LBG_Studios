extends RefCounted
class_name HubCollision
## AABB bâtiments + clamp_move (port mince de hub_collision.py — même JSON client).

var blocks: Array = []  # {id, min_x, max_x, min_z, max_z, door?}
var size_mul: float = 1.0


func reload(buildings_path: String = "") -> void:
	blocks.clear()
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
		var size_m := float(item.get("size_m", 32.0))
		var half := size_m * 0.5 * size_mul
		var door_raw = item.get("door")
		var door = null
		if typeof(door_raw) == TYPE_DICTIONARY:
			door = _door_corridor(door_raw, cx, cz, half)
		blocks.append({
			"id": str(item.get("id", item.get("kind", "building"))),
			"min_x": cx - half,
			"max_x": cx + half,
			"min_z": cz - half,
			"max_z": cz + half,
			"door": door,
		})
	print("[prime-hub] collision blocks=%d path=%s" % [blocks.size(), path])


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


func _in_door(door, x: float, z: float) -> bool:
	if door == null or typeof(door) != TYPE_DICTIONARY:
		return false
	return float(door["min_x"]) <= x and x <= float(door["max_x"]) and float(door["min_z"]) <= z and z <= float(door["max_z"])


func allows(x: float, z: float) -> bool:
	for b in blocks:
		if float(b["min_x"]) <= x and x <= float(b["max_x"]) and float(b["min_z"]) <= z and z <= float(b["max_z"]):
			if not _in_door(b.get("door"), x, z):
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


func clamp_move(from_x: float, from_z: float, to_x: float, to_z: float) -> Vector2:
	if allows(to_x, to_z):
		return Vector2(to_x, to_z)
	if allows(to_x, from_z):
		return Vector2(to_x, from_z)
	if allows(from_x, to_z):
		return Vector2(from_x, to_z)
	return Vector2(from_x, from_z)


func find_path(sx: float, sz: float, tx: float, tz: float, cell: float = 16.0, max_expand: int = 400) -> Array:
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
