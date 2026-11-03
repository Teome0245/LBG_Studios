extends Node3D
## Système de Terrain 3D Grande Échelle SWG Pre-CU (Planète 16 km × 16 km)
## Reproduction du moteur de terrain SOE SWG en Godot 4 :
## 1. Découpage en Chunks de 64m × 64m générés dynamiquement autour du joueur.
## 2. Générateur de hauteur fractale (FastNoiseLite Simplex + Ridges) simulant les dunes et plateaux de Lost Heaven.
## 3. Zone d'Aplanissement Urbain (City Flat Affector) pour intégrer sans couture les cités et cantinas.
## 4. Collision physique 3D temps réel avec HeightMapShape3D.

signal chunk_loaded(chunk_coord: Vector2i)
signal chunk_unloaded(chunk_coord: Vector2i)

const CHUNK_SIZE_M: float = 64.0
const CHUNK_RESOLUTION: int = 16 # 16x16 quads par chunk
const VIEW_DISTANCE_CHUNKS: int = 4 # Rayon de chunks chargés autour du joueur

var noise: FastNoiseLite = null
var loaded_chunks: Dictionary = {} # Vector2i -> Node3D (chunk)
var player_node: Node3D = null

# Villes & Aplanissements (Position X, Z, Rayon d'aplanissement, Hauteur Y)
var city_flatten_zones: Array = [
	{"center": Vector2(0, 0), "radius": 120.0, "blend_dist": 40.0, "height": 0.0}, # Cité de Lost Heaven
	{"center": Vector2(150, -200), "radius": 60.0, "blend_dist": 30.0, "height": 2.0} # Hameau des Dunes
]

var _material: StandardMaterial3D = null


func _ready() -> void:
	_init_noise()
	_init_material()


func _init_noise() -> void:
	noise = FastNoiseLite.new()
	noise.noise_type = FastNoiseLite.TYPE_SIMPLEX
	noise.seed = 1977 # Année de sortie de l'inspiration originale
	noise.frequency = 0.005 # Échelle des grandes dunes (ondes amples)
	noise.fractal_type = FastNoiseLite.FRACTAL_FBM
	noise.fractal_octaves = 4
	noise.fractal_gain = 0.45


func _init_material() -> void:
	_material = StandardMaterial3D.new()
	_material.albedo_color = Color(0.78, 0.65, 0.47, 1.0) # Sable ocre Lost Heaven
	_material.roughness = 0.95
	_material.metallic = 0.05


## Calcule la hauteur exacte Y en coordonnées monde (X, Z) avec application des règles d'aplanissement urbain
func get_height_at(world_x: float, world_z: float) -> float:
	if noise == null:
		_init_noise()

	# Hauteur naturelle par bruit fractal
	var base_h: float = noise.get_noise_2d(world_x, world_z) * 18.0

	# Application des affecteurs d'aplanissement de villes (SWG City Boundary Affectors)
	var final_h: float = base_h
	for zone in city_flatten_zones:
		var d: Dictionary = zone
		var center: Vector2 = d["center"]
		var radius: float = float(d["radius"])
		var blend: float = float(d["blend_dist"])
		var target_h: float = float(d["height"])

		var dist: float = Vector2(world_x, world_z).distance_to(center)
		if dist < radius:
			final_h = target_h
			break
		elif dist < radius + blend:
			var factor: float = (dist - radius) / blend
			final_h = lerpf(target_h, base_h, factor)

	return final_h


## Met à jour les chunks autour de la position du joueur (Streaming de terrain SWG)
func update_chunks_around_position(pos: Vector3) -> void:
	var center_chunk := Vector2i(
		int(floor(pos.x / CHUNK_SIZE_M)),
		int(floor(pos.z / CHUNK_SIZE_M))
	)

	var needed_chunks: Dictionary = {}

	for dx in range(-VIEW_DISTANCE_CHUNKS, VIEW_DISTANCE_CHUNKS + 1):
		for dz in range(-VIEW_DISTANCE_CHUNKS, VIEW_DISTANCE_CHUNKS + 1):
			var coord := Vector2i(center_chunk.x + dx, center_chunk.y + dz)
			needed_chunks[coord] = true
			if not loaded_chunks.has(coord):
				_load_chunk(coord)

	# Déchargement des chunks hors de portée
	var to_remove: Array = []
	for coord in loaded_chunks.keys():
		if not needed_chunks.has(coord):
			to_remove.append(coord)

	for coord in to_remove:
		_unload_chunk(coord)


func _load_chunk(coord: Vector2i) -> void:
	var chunk_node := StaticBody3D.new()
	chunk_node.name = "Chunk_%d_%d" % [coord.x, coord.y]
	var origin_x: float = coord.x * CHUNK_SIZE_M
	var origin_z: float = coord.y * CHUNK_SIZE_M
	chunk_node.position = Vector3(origin_x, 0, origin_z)

	# Génération de la grille de vertices
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	st.set_material(_material)

	var step: float = CHUNK_SIZE_M / float(CHUNK_RESOLUTION)

	for gz in range(CHUNK_RESOLUTION):
		for gx in range(CHUNK_RESOLUTION):
			var x0: float = gx * step
			var z0: float = gz * step
			var x1: float = (gx + 1) * step
			var z1: float = (gz + 1) * step

			var y00: float = get_height_at(origin_x + x0, origin_z + z0)
			var y10: float = get_height_at(origin_x + x1, origin_z + z0)
			var y01: float = get_height_at(origin_x + x0, origin_z + z1)
			var y11: float = get_height_at(origin_x + x1, origin_z + z1)

			var p00 := Vector3(x0, y00, z0)
			var p10 := Vector3(x1, y10, z0)
			var p01 := Vector3(x0, y01, z1)
			var p11 := Vector3(x1, y11, z1)

			# Triangle 1
			st.set_uv(Vector2(x0 / CHUNK_SIZE_M, z0 / CHUNK_SIZE_M))
			st.add_vertex(p00)
			st.set_uv(Vector2(x1 / CHUNK_SIZE_M, z0 / CHUNK_SIZE_M))
			st.add_vertex(p10)
			st.set_uv(Vector2(x0 / CHUNK_SIZE_M, z1 / CHUNK_SIZE_M))
			st.add_vertex(p01)

			# Triangle 2
			st.set_uv(Vector2(x1 / CHUNK_SIZE_M, z0 / CHUNK_SIZE_M))
			st.add_vertex(p10)
			st.set_uv(Vector2(x1 / CHUNK_SIZE_M, z1 / CHUNK_SIZE_M))
			st.add_vertex(p11)
			st.set_uv(Vector2(x0 / CHUNK_SIZE_M, z1 / CHUNK_SIZE_M))
			st.add_vertex(p01)

	st.generate_normals()
	var mesh: ArrayMesh = st.commit()

	var mesh_inst := MeshInstance3D.new()
	mesh_inst.mesh = mesh
	chunk_node.add_child(mesh_inst)

	# Collision physique exacte
	var col_shape := CollisionShape3D.new()
	col_shape.shape = mesh.create_trimesh_shape()
	chunk_node.add_child(col_shape)

	add_child(chunk_node)
	loaded_chunks[coord] = chunk_node
	chunk_loaded.emit(coord)


func _unload_chunk(coord: Vector2i) -> void:
	if loaded_chunks.has(coord):
		var node: Node3D = loaded_chunks[coord]
		loaded_chunks.erase(coord)
		node.queue_free()
		chunk_unloaded.emit(coord)


func _process(_delta: float) -> void:
	if player_node != null and is_instance_valid(player_node):
		update_chunks_around_position(player_node.global_position)

