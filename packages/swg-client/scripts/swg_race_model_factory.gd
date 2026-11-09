class_name SwgRaceModelFactory
extends RefCounted
## Fabrique de Morphologie et d'Appendices 3D pour les Races de Prime & SWG.
## Instancie les éléments anatomiques 3D (oreilles félines, cornes, lunettes,
## générateur dorsal, masques, harnais) et les ancre directement aux os du
## squelette humanoïde (BoneAttachment3D) ou au maillage procedural.

const BONE_HEAD_CANDIDATES := ["J_Bip_C_Head", "mixamorig_Head", "Head", "head", "Head_0"]
const BONE_SPINE_CANDIDATES := ["J_Bip_C_Spine", "mixamorig_Spine", "Spine", "spine", "Spine1", "mixamorig_Spine1"]
const BONE_HIPS_CANDIDATES := ["J_Bip_C_Hips", "mixamorig_Hips", "Hips", "hips"]

const PREFIX_FEATURE := "RaceFeature_"


static func attach_race_features(root_node: Node3D, sp: Dictionary) -> void:
	if root_node == null:
		return

	# 1. Nettoyage des appendices raciaux précédents
	clear_race_features(root_node)

	# 2. Identification de la race
	var s_id: String = str(sp.get("id", "human")).to_lower()
	var prime_id: String = str(sp.get("prime_id", s_id)).to_lower()
	var tint: Color = sp.get("skin_tint", Color.WHITE)

	# 3. Résolution du Skeleton3D
	var skeleton: Skeleton3D = _find_skeleton(root_node)

	# 4. Construction des appendices selon la race
	match s_id:
		"fel_rani", "twilek":
			_build_fel_rani_features(root_node, skeleton, tint)
		"tinkling":
			_build_tinkling_features(root_node, skeleton)
		"mechari", "cyborg":
			_build_mechari_features(root_node, skeleton)
		"varkoon", "wookiee":
			_build_varkoon_features(root_node, skeleton)
		"mogrul":
			_build_mogrul_features(root_node, skeleton)
		"kmiri", "zabrak":
			_build_kmiri_features(root_node, skeleton)
		"pykrel", "rodian":
			_build_pykrel_features(root_node, skeleton)
		"human":
			_build_human_features(root_node, skeleton)
		_:
			# Fallback par prime_id si différent
			if prime_id != s_id:
				attach_race_features(root_node, {"id": prime_id, "skin_tint": tint})


static func clear_race_features(root_node: Node3D) -> void:
	if root_node == null:
		return
	var to_remove: Array[Node] = []
	_collect_features(root_node, to_remove)
	for node in to_remove:
		node.queue_free()


static func _collect_features(curr: Node, out_arr: Array[Node]) -> void:
	for child in curr.get_children():
		if child.name.begins_with(PREFIX_FEATURE):
			out_arr.append(child)
		else:
			_collect_features(child, out_arr)


static func _find_skeleton(root_node: Node) -> Skeleton3D:
	if root_node is Skeleton3D:
		return root_node as Skeleton3D
	for c in root_node.get_children():
		var found := _find_skeleton(c)
		if found != null:
			return found
	return null


static func _attach_to_bone_or_root(
	root_node: Node3D,
	skeleton: Skeleton3D,
	bone_candidates: Array,
	feature_name: String,
	mesh_instance: Node3D,
	fallback_offset: Vector3
) -> void:
	mesh_instance.name = PREFIX_FEATURE + feature_name

	if skeleton != null:
		var bone_name: String = ""
		for candidate in bone_candidates:
			var idx := skeleton.find_bone(str(candidate))
			if idx != -1:
				bone_name = skeleton.get_bone_name(idx)
				break

		if not bone_name.is_empty():
			var att := BoneAttachment3D.new()
			att.name = PREFIX_FEATURE + feature_name + "_BoneAtt"
			att.bone_name = bone_name
			skeleton.add_child(att)
			att.add_child(mesh_instance)
			return

	# Fallback si pas de skeleton (avatar procédural ou headless)
	mesh_instance.position = fallback_offset
	root_node.add_child(mesh_instance)


# -------------------------------------------------------------------------
# APPENDICES PAR RACE
# -------------------------------------------------------------------------

## Fel'Rani (Arvandor) : Oreilles félines pointues & Queue féline souple
static func _build_fel_rani_features(root_node: Node3D, sk: Skeleton3D, tint: Color) -> void:
	# 1. Oreilles félines sur la tête
	var ears_holder := Node3D.new()
	var mat_fur := StandardMaterial3D.new()
	mat_fur.albedo_color = tint * 0.95
	mat_fur.roughness = 0.8

	var mat_inner := StandardMaterial3D.new()
	mat_inner.albedo_color = Color(0.95, 0.65, 0.65) # Intérieur rosé doux
	mat_inner.roughness = 0.9

	for side in [-1.0, 1.0]:
		var ear := MeshInstance3D.new()
		var prism := PrismMesh.new()
		prism.size = Vector3(0.08, 0.16, 0.05)
		ear.mesh = prism
		ear.set_surface_override_material(0, mat_fur)
		ear.position = Vector3(side * 0.13, 0.22, 0.02)
		ear.rotation_degrees = Vector3(-10.0, 0.0, side * -24.0)
		ears_holder.add_child(ear)

		# Pavillon intérieur
		var inner := MeshInstance3D.new()
		var in_prism := PrismMesh.new()
		in_prism.size = Vector3(0.05, 0.11, 0.03)
		inner.mesh = in_prism
		inner.set_surface_override_material(0, mat_inner)
		inner.position = Vector3(side * 0.125, 0.21, -0.015)
		inner.rotation_degrees = Vector3(-10.0, 0.0, side * -24.0)
		ears_holder.add_child(inner)

	_attach_to_bone_or_root(root_node, sk, BONE_HEAD_CANDIDATES, "FelRani_Ears", ears_holder, Vector3(0, 1.7, 0))

	# 2. Queue féline sur les Hanches
	var tail_holder := Node3D.new()
	var cur_pos := Vector3(0, -0.05, 0.12)
	for i in range(4):
		var seg := MeshInstance3D.new()
		var cyl := CylinderMesh.new()
		cyl.top_radius = 0.03 - (i * 0.005)
		cyl.bottom_radius = 0.035 - (i * 0.005)
		cyl.height = 0.14
		seg.mesh = cyl
		seg.set_surface_override_material(0, mat_fur)
		seg.position = cur_pos
		seg.rotation_degrees = Vector3(25.0 + (i * 12.0), 0.0, 0.0)
		tail_holder.add_child(seg)
		cur_pos += Vector3(0, -0.06 + (i * 0.03), 0.10)

	_attach_to_bone_or_root(root_node, sk, BONE_HIPS_CANDIDATES, "FelRani_Tail", tail_holder, Vector3(0, 0.9, 0))


## Tinkling (Mecha-Prime) : Grandes lunettes steampunk & Sacoche d'artisan
static func _build_tinkling_features(root_node: Node3D, sk: Skeleton3D) -> void:
	# 1. Lunettes de mécanicien sur le front/visage
	var goggles := Node3D.new()
	var mat_brass := StandardMaterial3D.new()
	mat_brass.albedo_color = Color(0.85, 0.65, 0.25)
	mat_brass.metallic = 0.85
	mat_brass.roughness = 0.3

	var mat_lens := StandardMaterial3D.new()
	mat_lens.albedo_color = Color(1.0, 0.8, 0.2)
	mat_lens.emission_enabled = true
	mat_lens.emission = Color(1.0, 0.75, 0.15)
	mat_lens.emission_energy_multiplier = 1.6

	for side in [-1.0, 1.0]:
		var rim := MeshInstance3D.new()
		var cyl := CylinderMesh.new()
		cyl.top_radius = 0.065
		cyl.bottom_radius = 0.065
		cyl.height = 0.04
		rim.mesh = cyl
		rim.set_surface_override_material(0, mat_brass)
		rim.position = Vector3(side * 0.08, 0.06, -0.16)
		rim.rotation_degrees = Vector3(90.0, 0.0, 0.0)
		goggles.add_child(rim)

		var lens := MeshInstance3D.new()
		var l_cyl := CylinderMesh.new()
		l_cyl.top_radius = 0.05
		l_cyl.bottom_radius = 0.05
		l_cyl.height = 0.02
		lens.mesh = l_cyl
		lens.set_surface_override_material(0, mat_lens)
		lens.position = Vector3(side * 0.08, 0.06, -0.18)
		lens.rotation_degrees = Vector3(90.0, 0.0, 0.0)
		goggles.add_child(lens)

	_attach_to_bone_or_root(root_node, sk, BONE_HEAD_CANDIDATES, "Tinkling_Goggles", goggles, Vector3(0, 1.55, 0))

	# 2. Sacoche d'artisan sur la hanche
	var pouch := Node3D.new()
	var mat_leather := StandardMaterial3D.new()
	mat_leather.albedo_color = Color(0.40, 0.25, 0.15)
	mat_leather.roughness = 0.7

	var bag := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = Vector3(0.12, 0.16, 0.18)
	bag.mesh = box
	bag.set_surface_override_material(0, mat_leather)
	bag.position = Vector3(0.24, -0.05, 0.02)
	pouch.add_child(bag)

	_attach_to_bone_or_root(root_node, sk, BONE_HIPS_CANDIDATES, "Tinkling_Pouch", pouch, Vector3(0, 0.85, 0))


## Mechari (Mecha-Prime) : Capteur optique cybernétique, antenne & réacteur dorsal
static func _build_mechari_features(root_node: Node3D, sk: Skeleton3D) -> void:
	# 1. Capteur optique & Antenne comlink
	var head_unit := Node3D.new()
	var mat_steel := StandardMaterial3D.new()
	mat_steel.albedo_color = Color(0.75, 0.80, 0.85)
	mat_steel.metallic = 0.95
	mat_steel.roughness = 0.2

	var mat_cyan_eye := StandardMaterial3D.new()
	mat_cyan_eye.albedo_color = Color(0.1, 0.9, 1.0)
	mat_cyan_eye.emission_enabled = true
	mat_cyan_eye.emission = Color(0.1, 0.9, 1.0)
	mat_cyan_eye.emission_energy_multiplier = 2.0

	var optic := MeshInstance3D.new()
	var opt_mesh := CylinderMesh.new()
	opt_mesh.top_radius = 0.035
	opt_mesh.bottom_radius = 0.04
	opt_mesh.height = 0.05
	optic.mesh = opt_mesh
	optic.set_surface_override_material(0, mat_cyan_eye)
	optic.position = Vector3(0.07, 0.05, -0.16)
	optic.rotation_degrees = Vector3(90.0, 0.0, 0.0)
	head_unit.add_child(optic)

	var antenna := MeshInstance3D.new()
	var ant_mesh := CylinderMesh.new()
	ant_mesh.top_radius = 0.006
	ant_mesh.bottom_radius = 0.012
	ant_mesh.height = 0.26
	antenna.mesh = ant_mesh
	antenna.set_surface_override_material(0, mat_steel)
	antenna.position = Vector3(-0.14, 0.22, -0.04)
	antenna.rotation_degrees = Vector3(-25.0, 0.0, 15.0)
	head_unit.add_child(antenna)

	_attach_to_bone_or_root(root_node, sk, BONE_HEAD_CANDIDATES, "Mechari_Optic", head_unit, Vector3(0, 1.6, 0))

	# 2. Générateur dorsal et dissipateurs sur le dos (Spine)
	var pack := Node3D.new()
	var pack_mesh := MeshInstance3D.new()
	var p_box := BoxMesh.new()
	p_box.size = Vector3(0.24, 0.32, 0.12)
	pack_mesh.mesh = p_box
	pack_mesh.set_surface_override_material(0, mat_steel)
	pack_mesh.position = Vector3(0, 0.08, 0.18)
	pack.add_child(pack_mesh)

	var conduit := MeshInstance3D.new()
	var c_box := BoxMesh.new()
	c_box.size = Vector3(0.16, 0.04, 0.14)
	conduit.mesh = c_box
	conduit.set_surface_override_material(0, mat_cyan_eye)
	conduit.position = Vector3(0, 0.14, 0.19)
	pack.add_child(conduit)

	_attach_to_bone_or_root(root_node, sk, BONE_SPINE_CANDIDATES, "Mechari_Pack", pack, Vector3(0, 1.25, 0))


## Varkoon (Arvandor) : Harnais lourd, cartouchière croisée et épaulière de guerre
static func _build_varkoon_features(root_node: Node3D, sk: Skeleton3D) -> void:
	var harness := Node3D.new()
	var mat_leather := StandardMaterial3D.new()
	mat_leather.albedo_color = Color(0.28, 0.18, 0.12)
	mat_leather.roughness = 0.9

	var mat_metal := StandardMaterial3D.new()
	mat_metal.albedo_color = Color(0.85, 0.85, 0.85)
	mat_metal.metallic = 0.9
	mat_metal.roughness = 0.25

	# Bandoulière croisée
	var strap := MeshInstance3D.new()
	var s_box := BoxMesh.new()
	s_box.size = Vector3(0.12, 0.48, 0.28)
	strap.mesh = s_box
	strap.set_surface_override_material(0, mat_leather)
	strap.position = Vector3(0, 0.05, 0)
	strap.rotation_degrees = Vector3(0, 0, 32.0)
	harness.add_child(strap)

	# Cartouches de munitions
	for i in range(3):
		var cart := MeshInstance3D.new()
		var c_cyl := CylinderMesh.new()
		c_cyl.top_radius = 0.022
		c_cyl.bottom_radius = 0.022
		c_cyl.height = 0.08
		cart.mesh = c_cyl
		cart.set_surface_override_material(0, mat_metal)
		cart.position = Vector3(-0.08 + (i * 0.08), 0.12 - (i * 0.07), -0.16)
		cart.rotation_degrees = Vector3(0, 0, 45.0)
		harness.add_child(cart)

	# Épaulière lourde gauche
	var pauldron := MeshInstance3D.new()
	var p_box := BoxMesh.new()
	p_box.size = Vector3(0.22, 0.08, 0.22)
	pauldron.mesh = p_box
	pauldron.set_surface_override_material(0, mat_metal)
	pauldron.position = Vector3(-0.28, 0.26, 0)
	pauldron.rotation_degrees = Vector3(0, 0, -18.0)
	harness.add_child(pauldron)

	_attach_to_bone_or_root(root_node, sk, BONE_SPINE_CANDIDATES, "Varkoon_Harness", harness, Vector3(0, 1.35, 0))


## Mogrul (Aetherion) : Respirateur à double cartouche & Fioles d'herboriste
static func _build_mogrul_features(root_node: Node3D, sk: Skeleton3D) -> void:
	var breather := Node3D.new()
	var mat_bronze := StandardMaterial3D.new()
	mat_bronze.albedo_color = Color(0.65, 0.50, 0.30)
	mat_bronze.metallic = 0.8
	mat_bronze.roughness = 0.4

	# Masque facial
	var mask := MeshInstance3D.new()
	var m_box := BoxMesh.new()
	m_box.size = Vector3(0.18, 0.10, 0.12)
	mask.mesh = m_box
	mask.set_surface_override_material(0, mat_bronze)
	mask.position = Vector3(0, -0.06, -0.14)
	breather.add_child(mask)

	# Cartouches de filtre droite et gauche
	for side in [-1.0, 1.0]:
		var cart := MeshInstance3D.new()
		var c_cyl := CylinderMesh.new()
		c_cyl.top_radius = 0.04
		c_cyl.bottom_radius = 0.04
		c_cyl.height = 0.09
		cart.mesh = c_cyl
		cart.set_surface_override_material(0, mat_bronze)
		cart.position = Vector3(side * 0.11, -0.06, -0.12)
		cart.rotation_degrees = Vector3(0, 0, side * 15.0)
		breather.add_child(cart)

	_attach_to_bone_or_root(root_node, sk, BONE_HEAD_CANDIDATES, "Mogrul_Breather", breather, Vector3(0, 1.45, 0))


## K'Miri / Zabrak (Khar'Zuun) : Couronne de 6 cornes crâniennes
static func _build_kmiri_features(root_node: Node3D, sk: Skeleton3D) -> void:
	var crown := Node3D.new()
	var mat_horn := StandardMaterial3D.new()
	mat_horn.albedo_color = Color(0.92, 0.88, 0.78)
	mat_horn.roughness = 0.6

	var horn_angles := [-60.0, -35.0, -12.0, 12.0, 35.0, 60.0]
	for ang in horn_angles:
		var rad := deg_to_rad(ang)
		var horn := MeshInstance3D.new()
		var cone := CylinderMesh.new()
		cone.top_radius = 0.002
		cone.bottom_radius = 0.022
		cone.height = 0.08
		horn.mesh = cone
		horn.set_surface_override_material(0, mat_horn)
		horn.position = Vector3(sin(rad) * 0.14, 0.18, cos(rad) * 0.10 - 0.04)
		horn.rotation_degrees = Vector3(15.0, 0.0, -ang * 0.45)
		crown.add_child(horn)

	_attach_to_bone_or_root(root_node, sk, BONE_HEAD_CANDIDATES, "Kmiri_Horns", crown, Vector3(0, 1.7, 0))


## Pykrel / Rodien (Arvandor) : Museau tubulaire et yeux noirs globuleux
static func _build_pykrel_features(root_node: Node3D, sk: Skeleton3D) -> void:
	var head_feats := Node3D.new()
	var mat_skin := StandardMaterial3D.new()
	mat_skin.albedo_color = Color(0.32, 0.68, 0.40)
	mat_skin.roughness = 0.7

	var mat_eye := StandardMaterial3D.new()
	mat_eye.albedo_color = Color(0.05, 0.05, 0.05)
	mat_eye.metallic = 0.95
	mat_eye.roughness = 0.1

	# Museau tubulaire
	var snout := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = 0.035
	cyl.bottom_radius = 0.05
	cyl.height = 0.12
	snout.mesh = cyl
	snout.set_surface_override_material(0, mat_skin)
	snout.position = Vector3(0, -0.04, -0.19)
	snout.rotation_degrees = Vector3(90.0, 0.0, 0.0)
	head_feats.add_child(snout)

	# Grands yeux noirs à facettes
	for side in [-1.0, 1.0]:
		var eye := MeshInstance3D.new()
		var sp := SphereMesh.new()
		sp.radius = 0.055
		sp.height = 0.11
		eye.mesh = sp
		eye.set_surface_override_material(0, mat_eye)
		eye.position = Vector3(side * 0.10, 0.04, -0.13)
		head_feats.add_child(eye)

	_attach_to_bone_or_root(root_node, sk, BONE_HEAD_CANDIDATES, "Pykrel_Face", head_feats, Vector3(0, 1.6, 0))


## Humain (Terre1 / Lost Heaven) : Écharpe de voyageur du désert
static func _build_human_features(root_node: Node3D, sk: Skeleton3D) -> void:
	var scarf := Node3D.new()
	var mat_cloth := StandardMaterial3D.new()
	mat_cloth.albedo_color = Color(0.80, 0.72, 0.58)
	mat_cloth.roughness = 0.85

	var wrap := MeshInstance3D.new()
	var torus := TorusMesh.new()
	torus.inner_radius = 0.10
	torus.outer_radius = 0.17
	wrap.mesh = torus
	wrap.set_surface_override_material(0, mat_cloth)
	wrap.position = Vector3(0, 0.18, 0)
	scarf.add_child(wrap)

	_attach_to_bone_or_root(root_node, sk, BONE_SPINE_CANDIDATES, "Human_Scarf", scarf, Vector3(0, 1.4, 0))

