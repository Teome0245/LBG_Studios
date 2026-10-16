extends RefCounted
class_name HubNav
## NavigationServer3D navmesh Lost Heaven (Scrapaltai) — ticket 2.3.
##
## Remplace l'A* grille AABB borné (PATH_BUDGET_PER_TICK=2) par un maillage de
## navigation *baked* une fois au démarrage :
##   1. recast voxelise le sol + grave les empreintes bâtiments (projected obstructions) ;
##   2. NavigationServer3D.map_get_path() calcule les trajectoires en C++ (BVH + funnel) ;
##   3. plus de budget par tick : N entités peuvent recalculer au même tick.
##
## Le maillage couvre le bourg + une marge. Hors bornes, `find_path` renvoie un
## tableau vide : l'appelant retombe sur l'A* grille AABB (dunes/anneau explore).

const GROUND_Y := 0.15
const BOUNDS_MARGIN := 300.0

const ZONES_DEF: Array = [
	{
		"id": "lost_heaven",
		"filter_min_x": 3000.0, "filter_max_x": 7000.0,
		"filter_min_z": -2000.0, "filter_max_z": 100.0,
		"default_bounds": [4000.0, -1400.0, 6300.0, -300.0],
		"margin": 300.0,
	},
	{
		"id": "zalem_outpost",
		"filter_min_x": -2500.0, "filter_max_x": 0.0,
		"filter_min_z": -1500.0, "filter_max_z": 200.0,
		"default_bounds": [-1450.0, -800.0, -950.0, -300.0],
		"margin": 150.0,
	},
	{
		"id": "ksar_nomade",
		"filter_min_x": 4000.0, "filter_max_x": 6000.0,
		"filter_min_z": -4600.0, "filter_max_z": -2800.0,
		"default_bounds": [4700.0, -4050.0, 5200.0, -3550.0],
		"margin": 150.0,
	},
]

var map: RID = RID()
var region: RID = RID()
var regions: Array[RID] = []
var nav_mesh: NavigationMesh = null
var ready_ok: bool = false

var min_x: float = 4000.0
var min_z: float = -1400.0
var max_x: float = 6300.0
var max_z: float = -300.0

var _zones_data: Array = []
var _poly_count: int = 0
var _bake_ms: int = 0
var path_queries: int = 0
var last_query_us: int = 0


func build(collision) -> bool:
	## collision : HubCollision déjà `reload()` (empreintes AABB + portes).
	free_nav()
	var t0 := Time.get_ticks_msec()
	_zones_data.clear()
	_poly_count = 0
	_bake_ms = 0

	map = NavigationServer3D.map_create()
	NavigationServer3D.map_set_use_async_iterations(map, false)
	NavigationServer3D.map_set_active(map, true)
	NavigationServer3D.map_set_up(map, Vector3.UP)

	var total_obst := 0
	for zdef in ZONES_DEF:
		var zid: String = str(zdef["id"])
		var fmin_x: float = float(zdef["filter_min_x"])
		var fmax_x: float = float(zdef["filter_max_x"])
		var fmin_z: float = float(zdef["filter_min_z"])
		var fmax_z: float = float(zdef["filter_max_z"])
		var def_b: Array = zdef["default_bounds"]
		var margin: float = float(zdef["margin"])

		var z_min_x := INF
		var z_min_z := INF
		var z_max_x := -INF
		var z_max_z := -INF
		var z_blocks: Array = []

		if collision != null:
			for b in collision.blocks:
				var bx: float = (float(b["min_x"]) + float(b["max_x"])) * 0.5
				var bz: float = (float(b["min_z"]) + float(b["max_z"])) * 0.5
				if bx < fmin_x or bx > fmax_x or bz < fmin_z or bz > fmax_z:
					continue
				z_min_x = minf(z_min_x, float(b["min_x"]))
				z_min_z = minf(z_min_z, float(b["min_z"]))
				z_max_x = maxf(z_max_x, float(b["max_x"]))
				z_max_z = maxf(z_max_z, float(b["max_z"]))
				z_blocks.append(b)

		if z_blocks.is_empty() or z_min_x >= z_max_x or z_min_z >= z_max_z:
			z_min_x = float(def_b[0])
			z_min_z = float(def_b[1])
			z_max_x = float(def_b[2])
			z_max_z = float(def_b[3])
		else:
			z_min_x = minf(z_min_x, float(def_b[0]))
			z_min_z = minf(z_min_z, float(def_b[1]))
			z_max_x = maxf(z_max_x, float(def_b[2]))
			z_max_z = maxf(z_max_z, float(def_b[3]))

		z_min_x -= margin
		z_min_z -= margin
		z_max_x += margin
		z_max_z += margin

		if zid == "lost_heaven":
			min_x = z_min_x
			min_z = z_min_z
			max_x = z_max_x
			max_z = z_max_z

		var src := NavigationMeshSourceGeometryData3D.new()
		src.add_faces(
			PackedVector3Array([
				Vector3(z_min_x, GROUND_Y, z_min_z), Vector3(z_max_x, GROUND_Y, z_min_z), Vector3(z_max_x, GROUND_Y, z_max_z),
				Vector3(z_min_x, GROUND_Y, z_min_z), Vector3(z_max_x, GROUND_Y, z_max_z), Vector3(z_min_x, GROUND_Y, z_max_z),
			]),
			Transform3D.IDENTITY
		)

		var n_obst := 0
		for b in z_blocks:
			src.add_projected_obstruction(
				PackedVector3Array([
					Vector3(float(b["min_x"]), GROUND_Y, float(b["min_z"])),
					Vector3(float(b["max_x"]), GROUND_Y, float(b["min_z"])),
					Vector3(float(b["max_x"]), GROUND_Y, float(b["max_z"])),
					Vector3(float(b["min_x"]), GROUND_Y, float(b["max_z"])),
				]),
				GROUND_Y - 1.0,
				30.0,
				true
			)
			n_obst += 1
		total_obst += n_obst

		var nm := NavigationMesh.new()
		nm.cell_size = 2.0
		nm.cell_height = 0.5
		nm.agent_height = 2.0
		nm.agent_radius = 2.0
		nm.agent_max_climb = 1.0
		nm.agent_max_slope = 45.0
		nm.region_min_size = 4.0
		nm.edge_max_error = 1.3

		var tb := Time.get_ticks_msec()
		NavigationServer3D.bake_from_source_geometry_data(nm, src)
		var b_ms := Time.get_ticks_msec() - tb
		_bake_ms += b_ms
		var p_count := nm.get_polygon_count()
		_poly_count += p_count

		if p_count > 0:
			var reg := NavigationServer3D.region_create()
			NavigationServer3D.region_set_use_async_iterations(reg, false)
			NavigationServer3D.region_set_map(reg, map)
			NavigationServer3D.region_set_enabled(reg, true)
			NavigationServer3D.region_set_navigation_mesh(reg, nm)
			regions.append(reg)
			if zid == "lost_heaven":
				region = reg
				nav_mesh = nm
			_zones_data.append({
				"id": zid,
				"bounds": [z_min_x, z_min_z, z_max_x, z_max_z],
				"region": reg,
				"polys": p_count,
			})

	NavigationServer3D.map_set_cell_size(map, 2.0)
	NavigationServer3D.map_set_cell_height(map, 0.5)
	NavigationServer3D.map_force_update(map)

	print("[prime-hub] navmesh multi-zones bake %d ms — zones=%d polys=%d obstacles=%d LH_bounds=[%.0f,%.0f,%.0f,%.0f]" % [
		_bake_ms, _zones_data.size(), _poly_count, total_obst, min_x, min_z, max_x, max_z,
	])

	if _poly_count <= 0 or _zones_data.is_empty():
		ready_ok = false
		push_warning("[prime-hub] navmesh vide — fallback A* grille AABB")
		return false

	ready_ok = NavigationServer3D.map_get_iteration_id(map) > 0
	if not ready_ok:
		push_warning("[prime-hub] navmesh map non synchronisée — fallback A* grille AABB")
	return ready_ok


func _zone_for_point(x: float, z: float) -> Variant:
	for zd in _zones_data:
		var b: Array = zd["bounds"]
		if x >= b[0] and x <= b[2] and z >= b[1] and z <= b[3]:
			return zd
	return null


func in_bounds(x: float, z: float) -> bool:
	return _zone_for_point(x, z) != null


func find_path(sx: float, sz: float, tx: float, tz: float) -> Array:
	## Array de Vector2 (x,z) : origine → … → destination. Vide si navmesh
	## indisponible ou hors bornes (l'appelant retombe sur l'A* grille).
	if not ready_ok:
		return []
	var zs = _zone_for_point(sx, sz)
	var zt = _zone_for_point(tx, tz)
	if zs == null or zt == null:
		return []
	if zs["id"] != zt["id"]:
		# Inter-zones (5 km de dunes sans obstacle) : laisser l'A*/ligne claire
		return []
	var origin := Vector3(sx, GROUND_Y, sz)
	var dest := Vector3(tx, GROUND_Y, tz)
	var t0 := Time.get_ticks_usec()
	var packed: PackedVector3Array = NavigationServer3D.map_get_path(map, origin, dest, true)
	last_query_us = Time.get_ticks_usec() - t0
	path_queries += 1
	var out: Array = []
	for p in packed:
		out.append(Vector2(p.x, p.z))
	return out


func stats() -> Dictionary:
	return {
		"ok": ready_ok,
		"engine": "NavigationServer3D",
		"regions": NavigationServer3D.map_get_regions(map).size() if map.is_valid() else 0,
		"polygons": _poly_count,
		"bake_ms": _bake_ms,
		"path_queries": path_queries,
		"last_query_us": last_query_us,
		"budget_per_tick": 0,
		"bounds": [min_x, min_z, max_x, max_z],
		"zones_count": _zones_data.size(),
	}


func free_nav() -> void:
	for reg in regions:
		if reg.is_valid():
			NavigationServer3D.free_rid(reg)
	regions.clear()
	region = RID()
	if map.is_valid():
		NavigationServer3D.free_rid(map)
		map = RID()
	ready_ok = false

