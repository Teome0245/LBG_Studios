class_name WorldTerrainBuilder
extends Node3D

## WorldTerrainBuilder — Générateur procédural de terrain 3D et d'environnements pour Godot 4.
## Construit des chunks de terrain maillés en ArrayMesh, calcule les normales/UVs,
## applique les collisions physiques et disperse des props (arbres, rochers, conteneurs, terminaux).

const DEFAULT_WIDTH: float = 120.0
const DEFAULT_DEPTH: float = 120.0
const DEFAULT_RESOLUTION: int = 32
const DEFAULT_MAX_HEIGHT: float = 14.0

var noise: FastNoiseLite


func _init() -> void:
	noise = FastNoiseLite.new()
	noise.noise_type = FastNoiseLite.TYPE_PERLIN
	noise.fractal_type = FastNoiseLite.FRACTAL_FBM
	noise.fractal_octaves = 4
	noise.frequency = 0.02


func sample_height(x: float, z: float, max_height: float = DEFAULT_MAX_HEIGHT) -> float:
	if noise == null:
		return 0.0
	var n_val: float = noise.get_noise_2d(x, z) # Valeur entre -1.0 et 1.0
	# Forme du relief avec crêtes et vallées
	var elevation: float = (n_val + 1.0) * 0.5
	return pow(elevation, 1.4) * max_height


func build_terrain_chunk(
	width: float = DEFAULT_WIDTH,
	depth: float = DEFAULT_DEPTH,
	resolution: int = DEFAULT_RESOLUTION,
	max_height: float = DEFAULT_MAX_HEIGHT,
	noise_seed: int = 1337
) -> MeshInstance3D:
	noise.seed = noise_seed

	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)

	var step_x: float = width / float(resolution)
	var step_z: float = depth / float(resolution)
	var half_w: float = width * 0.5
	var half_d: float = depth * 0.5

	# Grille de sommets
	for z_idx in range(resolution + 1):
		for x_idx in range(resolution + 1):
			var world_x: float = float(x_idx) * step_x - half_w
			var world_z: float = float(z_idx) * step_z - half_d
			var world_y: float = sample_height(world_x, world_z, max_height)

			var uv := Vector2(float(x_idx) / float(resolution), float(z_idx) / float(resolution))
			
			# Couleur de sommet basée sur l'altitude (plaine = vert, roche = gris, sommet = sable/blanc)
			var h_ratio: float = clampf(world_y / max_height, 0.0, 1.0)
			var v_color: Color
			if h_ratio < 0.25:
				v_color = Color(0.2, 0.45, 0.2, 1.0) # Plaine
			elif h_ratio < 0.7:
				v_color = Color(0.5, 0.42, 0.32, 1.0) # Roche / terre
			else:
				v_color = Color(0.75, 0.72, 0.65, 1.0) # Crête

			st.set_uv(uv)
			st.set_color(v_color)
			st.add_vertex(Vector3(world_x, world_y, world_z))

	# Génération des triangles (indexation de la grille)
	for z_idx in range(resolution):
		for x_idx in range(resolution):
			var row_stride: int = resolution + 1
			var top_left: int = z_idx * row_stride + x_idx
			var top_right: int = top_left + 1
			var bottom_left: int = (z_idx + 1) * row_stride + x_idx
			var bottom_right: int = bottom_left + 1

			# Triangle 1
			st.add_index(top_left)
			st.add_index(bottom_left)
			st.add_index(top_right)

			# Triangle 2
			st.add_index(top_right)
			st.add_index(bottom_left)
			st.add_index(bottom_right)

	st.generate_normals()
	st.generate_tangents()

	var array_mesh: ArrayMesh = st.commit()

	var mesh_inst := MeshInstance3D.new()
	mesh_inst.name = "TerrainChunk"
	mesh_inst.mesh = array_mesh

	# Matériau standard avec vertex colors
	var mat := StandardMaterial3D.new()
	mat.vertex_color_use_as_albedo = true
	mat.roughness = 0.85
	mesh_inst.material_override = mat

	# Génération de la collision physique ConcavePolygonShape3D
	var static_body := StaticBody3D.new()
	static_body.name = "TerrainCollision"
	var col_shape := CollisionShape3D.new()
	col_shape.name = "TerrainShape"
	col_shape.shape = array_mesh.create_trimesh_shape()
	static_body.add_child(col_shape)
	mesh_inst.add_child(static_body)

	return mesh_inst


func scatter_props(
	parent_node: Node3D,
	prop_scenes: Array[PackedScene],
	count: int,
	area_width: float = DEFAULT_WIDTH,
	area_depth: float = DEFAULT_DEPTH,
	max_slope_rad: float = 0.5,
	seed_val: int = 42
) -> Array[Node3D]:
	var spawned: Array[Node3D] = []
	if prop_scenes.is_empty():
		return spawned

	var rng := RandomNumberGenerator.new()
	rng.seed = seed_val

	var half_w: float = area_width * 0.45
	var half_d: float = area_depth * 0.45

	for i in range(count):
		var px: float = rng.randf_range(-half_w, half_w)
		var pz: float = rng.randf_range(-half_d, half_d)
		var py: float = sample_height(px, pz)

		# Évaluer la pente locale (approximation par gradient)
		var delta: float = 0.5
		var h_px: float = sample_height(px + delta, pz)
		var h_mx: float = sample_height(px - delta, pz)
		var h_pz: float = sample_height(px, pz + delta)
		var h_mz: float = sample_height(px, pz - delta)

		var slope_x: float = (h_px - h_mx) / (2.0 * delta)
		var slope_z: float = (h_pz - h_mz) / (2.0 * delta)
		var slope_angle: float = atan(sqrt(slope_x * slope_x + slope_z * slope_z))

		if slope_angle > max_slope_rad:
			continue # Terrain trop raide pour ce prop

		var scene_idx: int = rng.randi_range(0, prop_scenes.size() - 1)
		var scene: PackedScene = prop_scenes[scene_idx]
		var inst: Node3D = scene.instantiate() as Node3D
		if inst:
			inst.position = Vector3(px, py, pz)
			inst.rotation.y = rng.randf_range(0.0, TAU)
			var s: float = rng.randf_range(0.85, 1.2)
			inst.scale = Vector3(s, s, s)
			parent_node.add_child(inst)
			spawned.append(inst)

	return spawned

