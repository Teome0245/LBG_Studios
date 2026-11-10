extends SceneTree
## Self-test headless du constructeur de terrain procédural (WorldTerrainBuilder).
##
## Usage:
##   packages/prime-hub/tools/Godot_v4.6.3-stable_linux.x86_64 --headless --path packages/prime-client \
##     -s res://tools/terrain_builder_selftest.gd

const WorldTerrainBuilderScript := preload("res://scripts/world_terrain_builder.gd")

func _init() -> void:
	print("[terrain_selftest] Démarrage du test de génération de terrain procédural...")

	var builder = WorldTerrainBuilderScript.new()
	assert(builder != null, "Échec instanciation WorldTerrainBuilder")

	# 1. Test du générateur de hauteur
	var h0 = builder.sample_height(0.0, 0.0)
	var h1 = builder.sample_height(25.0, 25.0)
	print("[terrain_selftest] Hauteur en (0,0) = %0.2f, en (25,25) = %0.2f" % [h0, h1])
	assert(h0 >= 0.0, "Hauteur négative inattendue")
	assert(h1 >= 0.0, "Hauteur négative inattendue")

	# 2. Construction d'un chunk de terrain
	var res: int = 16
	var chunk: MeshInstance3D = builder.build_terrain_chunk(60.0, 60.0, res, 12.0, 9999)
	assert(chunk != null, "Le chunk de terrain n'a pas été créé")
	assert(chunk.mesh != null, "Le mesh du terrain est nul")

	var arr_mesh: ArrayMesh = chunk.mesh as ArrayMesh
	assert(arr_mesh != null, "Le mesh n'est pas un ArrayMesh")
	var surface_count: int = arr_mesh.get_surface_count()
	assert(surface_count == 1, "Nombre de surfaces inattendu : %d" % surface_count)

	# Vérifier les sommets attendus : (res + 1) * (res + 1)
	var expected_verts: int = (res + 1) * (res + 1)
	var arrays = arr_mesh.surface_get_arrays(0)
	var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	print("[terrain_selftest] Sommets générés : %d (attendu : %d)" % [verts.size(), expected_verts])
	assert(verts.size() == expected_verts, "Nombre de sommets erroné")

	# Vérifier les indices triangles : res * res * 2 triangles * 3 indices
	var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
	var expected_indices: int = res * res * 6
	print("[terrain_selftest] Indices de triangles : %d (attendu : %d)" % [indices.size(), expected_indices])
	assert(indices.size() == expected_indices, "Nombre d'indices erroné")

	# 3. Vérification de la collision physique
	var static_body = chunk.get_node_or_null("TerrainCollision")
	assert(static_body != null, "StaticBody3D introuvable sur le terrain")
	var col_shape = static_body.get_node_or_null("TerrainShape")
	assert(col_shape != null, "CollisionShape3D introuvable sur le terrain")
	assert(col_shape.shape is ConcavePolygonShape3D, "Type de collision inattendu")
	print("[terrain_selftest] Collision ConcavePolygonShape3D générée avec succès.")

	# 4. Test du scatter de props
	var root := Node3D.new()
	root.add_child(chunk)

	# Création d'un mock PackedScene pour tester le scatter
	var prop_node := Node3D.new()
	prop_node.name = "MockProp"
	var pack := PackedScene.new()
	pack.pack(prop_node)

	var spawned = builder.scatter_props(root, [pack], 10, 50.0, 50.0, 0.6, 123)
	print("[terrain_selftest] Props dispersés avec succès sur le relief : %d" % spawned.size())
	assert(spawned.size() > 0, "Aucun prop n'a été dispersé sur le terrain")

	for p in spawned:
		assert(p.position.y >= 0.0, "Prop sous le niveau de base")

	# Nettoyage
	root.free()
	builder.free()

	print("[terrain_selftest] TOUS LES TESTS TERRAIN PROCÉDURAL ONT RÉUSSI AVEC SUCCÈS !")
	quit(0)
