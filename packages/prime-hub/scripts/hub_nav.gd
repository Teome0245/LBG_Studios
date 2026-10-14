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
const DEFAULT_BOUNDS := [4000.0, -1400.0, 6300.0, -300.0]  # min_x, min_z, max_x, max_z
const BOUNDS_MARGIN := 300.0

var map: RID = RID()
var region: RID = RID()
var nav_mesh: NavigationMesh = null
var ready_ok: bool = false

var min_x: float = DEFAULT_BOUNDS[0]
var min_z: float = DEFAULT_BOUNDS[1]
var max_x: float = DEFAULT_BOUNDS[2]
var max_z: float = DEFAULT_BOUNDS[3]

var _poly_count: int = 0
var _bake_ms: int = 0
var path_queries: int = 0
var last_query_us: int = 0


func build(collision) -> bool:
	## collision : HubCollision déjà `reload()` (empreintes AABB + portes).
	var t0 := Time.get_ticks_msec()
	_compute_bounds(collision)

	var src := NavigationMeshSourceGeometryData3D.new()
	# Sol : quad unique couvrant le bourg.
	src.add_faces(
		PackedVector3Array([
			Vector3(min_x, GROUND_Y, min_z), Vector3(max_x, GROUND_Y, min_z), Vector3(max_x, GROUND_Y, max_z),
			Vector3(min_x, GROUND_Y, min_z), Vector3(max_x, GROUND_Y, max_z), Vector3(min_x, GROUND_Y, max_z),
		]),
		Transform3D.IDENTITY
	)
	# Bâtiments : gravés (carve) dans le maillage.
	var n_obst := 0
	if collision != null:
		for b in collision.blocks:
			var bx: float = (float(b["min_x"]) + float(b["max_x"])) * 0.5
			var bz: float = (float(b["min_z"]) + float(b["max_z"])) * 0.5
			if bx < min_x or bx > max_x or bz < min_z or bz > max_z:
				continue
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

	nav_mesh = NavigationMesh.new()
	# cell_height = sous-multiple exact de agent_height / max_climb (évite warnings Recast).
	nav_mesh.cell_size = 2.0
	nav_mesh.cell_height = 0.5
	nav_mesh.agent_height = 2.0
	nav_mesh.agent_radius = 2.0
	nav_mesh.agent_max_climb = 1.0
	nav_mesh.agent_max_slope = 45.0
	nav_mesh.region_min_size = 4.0
	nav_mesh.edge_max_error = 1.3

	var tb := Time.get_ticks_msec()
	NavigationServer3D.bake_from_source_geometry_data(nav_mesh, src)
	_bake_ms = Time.get_ticks_msec() - tb
	_poly_count = nav_mesh.get_polygon_count()
	print("[prime-hub] navmesh bake %d ms — polys=%d obstacles=%d bounds=[%.0f,%.0f,%.0f,%.0f]" % [
		_bake_ms, _poly_count, n_obst, min_x, min_z, max_x, max_z,
	])
	if _poly_count <= 0:
		ready_ok = false
		push_warning("[prime-hub] navmesh vide — fallback A* grille AABB")
		return false

	map = NavigationServer3D.map_create()
	# Async iterations cassent map_force_update (Godot 4.4+) : offline pour un
	# build synchrone déterministe au boot. Le maillage est figé ensuite.
	NavigationServer3D.map_set_use_async_iterations(map, false)
	NavigationServer3D.map_set_active(map, true)
	NavigationServer3D.map_set_up(map, Vector3.UP)
	NavigationServer3D.map_set_cell_size(map, nav_mesh.cell_size)
	NavigationServer3D.map_set_cell_height(map, nav_mesh.cell_height)

	region = NavigationServer3D.region_create()
	NavigationServer3D.region_set_use_async_iterations(region, false)
	NavigationServer3D.region_set_map(region, map)
	NavigationServer3D.region_set_enabled(region, true)
	NavigationServer3D.region_set_navigation_mesh(region, nav_mesh)
	NavigationServer3D.map_force_update(map)

	ready_ok = NavigationServer3D.map_get_iteration_id(map) > 0
	if not ready_ok:
		push_warning("[prime-hub] navmesh map non synchronisée — fallback A* grille AABB")
	return ready_ok


func _compute_bounds(collision) -> void:
	min_x = INF
	min_z = INF
	max_x = -INF
	max_z = -INF
	var n := 0
	if collision != null:
		for b in collision.blocks:
			var bx: float = (float(b["min_x"]) + float(b["max_x"])) * 0.5
			var bz: float = (float(b["min_z"]) + float(b["max_z"])) * 0.5
			if bx < 3000.0 or bx > 7000.0 or bz < -2000.0 or bz > 100.0:
				continue
			min_x = minf(min_x, float(b["min_x"]))
			min_z = minf(min_z, float(b["min_z"]))
			max_x = maxf(max_x, float(b["max_x"]))
			max_z = maxf(max_z, float(b["max_z"]))
			n += 1
	if n == 0 or min_x >= max_x or min_z >= max_z:
		min_x = DEFAULT_BOUNDS[0]
		min_z = DEFAULT_BOUNDS[1]
		max_x = DEFAULT_BOUNDS[2]
		max_z = DEFAULT_BOUNDS[3]
	# Le bourg ne doit jamais être plus petit que la zone par défaut.
	min_x = minf(min_x, DEFAULT_BOUNDS[0])
	min_z = minf(min_z, DEFAULT_BOUNDS[1])
	max_x = maxf(max_x, DEFAULT_BOUNDS[2])
	max_z = maxf(max_z, DEFAULT_BOUNDS[3])
	min_x -= BOUNDS_MARGIN
	min_z -= BOUNDS_MARGIN
	max_x += BOUNDS_MARGIN
	max_z += BOUNDS_MARGIN


func in_bounds(x: float, z: float) -> bool:
	return x >= min_x and x <= max_x and z >= min_z and z <= max_z


func find_path(sx: float, sz: float, tx: float, tz: float) -> Array:
	## Array de Vector2 (x,z) : origine → … → destination. Vide si navmesh
	## indisponible ou hors bornes (l'appelant retombe sur l'A* grille).
	if not ready_ok:
		return []
	if not in_bounds(sx, sz) or not in_bounds(tx, tz):
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
	}


func free_nav() -> void:
	if map.is_valid():
		NavigationServer3D.free_rid(map)
		map = RID()
	if region.is_valid():
		NavigationServer3D.free_rid(region)
		region = RID()
	ready_ok = false
