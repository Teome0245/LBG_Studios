class_name SwgVrmAnimator
extends Node
## Animateur procédural universel pour avatars VRM Humanoid dans SWG Godot 4.
## Élimine définitivement la T-Pose au repos (A-pose détendue naturelle)
## et génère le balancement locomoteur lors des déplacements.
## Compatible rigs : VRoid Biped, Mixamo, VRM standard, Unity Humanoid.

var skeleton: Skeleton3D = null

# Indices des os résolus dynamiquement
var _b_spine: int = -1
var _b_l_arm: int = -1
var _b_r_arm: int = -1
var _b_l_forearm: int = -1
var _b_r_forearm: int = -1
var _b_l_leg: int = -1
var _b_r_leg: int = -1
var _b_l_knee: int = -1
var _b_r_knee: int = -1

# État locomoteur & posture
var is_moving: bool = false
var is_entertainer: bool = false # Danse / Chant pour Lia et artistes
var is_arm_mirrored: bool = false # Détection automatique de l'orientation du squelette (VRoid vs Mixamo/VRM)
var move_speed: float = 0.0
var walk_cycle: float = 0.0
var idle_breath: float = 0.0

# Quaternions des bras
var _current_arm_l_rot: Quaternion = Quaternion.IDENTITY
var _current_arm_r_rot: Quaternion = Quaternion.IDENTITY


static func find_skeleton_in_tree(root_node: Node) -> Skeleton3D:
	if root_node is Skeleton3D:
		return root_node as Skeleton3D
	for c in root_node.get_children():
		var found := find_skeleton_in_tree(c)
		if found != null:
			return found
	return null


func setup(sk: Skeleton3D, entertainer: bool = false) -> void:
	skeleton = sk
	is_entertainer = entertainer
	if skeleton == null:
		return

	# Recherche multi-règles pour supporter Compagnon, LadyKoi, Aurora, Anna, etc.
	_b_spine = _find_any_bone(["J_Bip_C_Spine", "mixamorig_Spine", "Spine", "spine", "Spine1", "mixamorig_Spine1"])
	_b_l_arm = _find_any_bone(["J_Bip_L_UpperArm", "mixamorig_LeftArm", "LeftArm", "left_arm", "UpperArm.L", "arm.L"])
	_b_r_arm = _find_any_bone(["J_Bip_R_UpperArm", "mixamorig_RightArm", "RightArm", "right_arm", "UpperArm.R", "arm.R"])
	_b_l_forearm = _find_any_bone(["J_Bip_L_LowerArm", "mixamorig_LeftForeArm", "LeftForeArm", "left_forearm", "ForeArm.L", "forearm.L"])
	_b_r_forearm = _find_any_bone(["J_Bip_R_LowerArm", "mixamorig_RightForeArm", "RightForeArm", "right_forearm", "ForeArm.R", "forearm.R"])
	_b_l_leg = _find_any_bone(["J_Bip_L_UpperLeg", "mixamorig_LeftUpLeg", "LeftUpLeg", "left_upleg", "UpLeg.L", "thigh.L"])
	_b_r_leg = _find_any_bone(["J_Bip_R_UpperLeg", "mixamorig_RightUpLeg", "RightUpLeg", "right_upleg", "UpLeg.R", "thigh.R"])
	_b_l_knee = _find_any_bone(["J_Bip_L_LowerLeg", "mixamorig_LeftLeg", "LeftLeg", "left_leg", "Leg.L", "shin.L"])
	_b_r_knee = _find_any_bone(["J_Bip_R_LowerLeg", "mixamorig_RightLeg", "RightLeg", "right_leg", "Leg.R", "shin.R"])

	# Détection automatique du repère local des bras (LadyKoi / Mixamo vs Compagnon)
	if _b_l_arm != -1:
		var rest_l := skeleton.get_bone_rest(_b_l_arm)
		is_arm_mirrored = rest_l.origin.x < 0.0

	# Initialisation immédiate des bras au repos pour tuer net la T-Pose
	var z_sign: float = 1.0 if is_arm_mirrored else -1.0
	var arm_base_z_l := deg_to_rad(74.0 * z_sign)
	var arm_base_z_r := deg_to_rad(-74.0 * z_sign)
	_current_arm_l_rot = Quaternion(Vector3(0, 0, 1), arm_base_z_l)
	_current_arm_r_rot = Quaternion(Vector3(0, 0, 1), arm_base_z_r)

	if _b_l_arm != -1: skeleton.set_bone_pose_rotation(_b_l_arm, _current_arm_l_rot)
	if _b_r_arm != -1: skeleton.set_bone_pose_rotation(_b_r_arm, _current_arm_r_rot)
	if _b_l_forearm != -1: skeleton.set_bone_pose_rotation(_b_l_forearm, Quaternion(Vector3(1, 0, 0), deg_to_rad(14.0)))
	if _b_r_forearm != -1: skeleton.set_bone_pose_rotation(_b_r_forearm, Quaternion(Vector3(1, 0, 0), deg_to_rad(14.0)))

	_apply_pose(0.016)


func _find_any_bone(candidates: Array) -> int:
	if skeleton == null:
		return -1
	for c in candidates:
		var idx := skeleton.find_bone(str(c))
		if idx != -1:
			return idx
	return -1


func _process(delta: float) -> void:
	# Recherche du CharacterBody3D dans les ancêtres
	var cb := _find_parent_character_body()
	if cb != null:
		var planar_v := Vector2(cb.velocity.x, cb.velocity.z).length()
		update_animation(delta, planar_v > 0.15, planar_v)
	else:
		# PNJ statique : respiration et posture vivante
		update_animation(delta, false, 0.0)


func _find_parent_character_body() -> CharacterBody3D:
	var curr: Node = get_parent()
	while curr != null:
		if curr is CharacterBody3D:
			return curr as CharacterBody3D
		curr = curr.get_parent()
	return null


func update_animation(delta: float, moving: bool, speed: float) -> void:
	if skeleton == null:
		return

	is_moving = moving
	move_speed = speed
	idle_breath += delta * (2.8 if is_entertainer else 1.8)

	if is_moving:
		var freq: float = clampf(move_speed * 1.8, 4.0, 10.0)
		walk_cycle += delta * freq
	else:
		walk_cycle = lerpf(walk_cycle, roundf(walk_cycle / (PI * 2.0)) * PI * 2.0, delta * 5.0)

	_apply_pose(delta)


func _apply_pose(delta: float) -> void:
	if skeleton == null:
		return

	var breath_sin := sin(idle_breath) * 0.03
	var walk_sin := sin(walk_cycle)

	# 1. Torse & Respiration (ou chorégraphie de danse sensuelle si artiste)
	if _b_spine != -1:
		if is_entertainer and not is_moving:
			# Déhanchement en forme de 8 (courbe de Lissajous de cantina)
			var sway_y := sin(idle_breath * 0.9) * deg_to_rad(8.0)
			var sway_z := cos(idle_breath * 1.8) * deg_to_rad(6.0)
			var sway_x := sin(idle_breath * 3.6) * deg_to_rad(2.5) + breath_sin
			var spine_q := Quaternion.from_euler(Vector3(sway_x, sway_y, sway_z))
			skeleton.set_bone_pose_rotation(_b_spine, spine_q)
		else:
			var spine_rot := Quaternion(Vector3(1, 0, 0), breath_sin * 0.5)
			skeleton.set_bone_pose_rotation(_b_spine, spine_rot)

	# 2. Bras : Sortir de la T-Pose vers le bas (~ -74° / +74° selon orientation repère)
	var z_sign: float = 1.0 if is_arm_mirrored else -1.0
	var arm_base_z_l := deg_to_rad(74.0 * z_sign)
	var arm_base_z_r := deg_to_rad(-74.0 * z_sign)
	var arm_swing := 0.0

	if is_moving:
		arm_swing = walk_sin * deg_to_rad(24.0)
	elif is_entertainer:
		# Danse de Cantina : les bras restent bas et gracieux le long du corps
		# avec de légères ondulations harmoniques (fini les bras levés)
		var dance_wave := sin(idle_breath * 1.4) * deg_to_rad(8.0)
		arm_base_z_l = deg_to_rad((73.0 + sin(idle_breath * 1.8) * 3.0) * z_sign)
		arm_base_z_r = deg_to_rad((-73.0 - sin(idle_breath * 1.8) * 3.0) * z_sign)
		arm_swing = dance_wave

	# Bras Gauche
	if _b_l_arm != -1:
		var q_z := Quaternion(Vector3(0, 0, 1), arm_base_z_l)
		var q_x := Quaternion(Vector3(1, 0, 0), arm_swing + breath_sin)
		var target_q := q_x * q_z
		_current_arm_l_rot = _current_arm_l_rot.slerp(target_q, clampf(delta * 14.0, 0.1, 1.0))
		skeleton.set_bone_pose_rotation(_b_l_arm, _current_arm_l_rot)

	# Bras Droit (en opposition de phase)
	if _b_r_arm != -1:
		var q_z := Quaternion(Vector3(0, 0, 1), arm_base_z_r)
		var q_x := Quaternion(Vector3(1, 0, 0), -arm_swing + breath_sin)
		var target_q := q_x * q_z
		_current_arm_r_rot = _current_arm_r_rot.slerp(target_q, clampf(delta * 14.0, 0.1, 1.0))
		skeleton.set_bone_pose_rotation(_b_r_arm, _current_arm_r_rot)

	# Coudes / Avant-bras légèrement pliés (14° naturel, ondulation fluide pour artiste)
	var elbow_base := deg_to_rad(16.0)
	var ent_elbow := 0.0
	if is_entertainer and not is_moving:
		ent_elbow = sin(idle_breath * 2.2) * deg_to_rad(6.0)

	if _b_l_forearm != -1:
		var elbow_swing := 0.0
		if is_moving and arm_swing > 0.0:
			elbow_swing = arm_swing * 0.4
		var q_elbow := Quaternion(Vector3(1, 0, 0), elbow_base + elbow_swing + ent_elbow)
		skeleton.set_bone_pose_rotation(_b_l_forearm, q_elbow)

	if _b_r_forearm != -1:
		var elbow_swing := 0.0
		if is_moving and -arm_swing > 0.0:
			elbow_swing = -arm_swing * 0.4
		var q_elbow := Quaternion(Vector3(1, 0, 0), elbow_base + elbow_swing - ent_elbow)
		skeleton.set_bone_pose_rotation(_b_r_forearm, q_elbow)

	# 3. Jambes & Foulée (ou jeu de jambes de danse pour l'artiste)
	if is_moving:
		var leg_swing := walk_sin * deg_to_rad(28.0)
		if _b_l_leg != -1:
			var q_leg_l := Quaternion(Vector3(1, 0, 0), -leg_swing)
			skeleton.set_bone_pose_rotation(_b_l_leg, q_leg_l)
		if _b_l_knee != -1:
			var knee_flex := maxf(0.0, leg_swing) * 0.8
			skeleton.set_bone_pose_rotation(_b_l_knee, Quaternion(Vector3(1, 0, 0), knee_flex))

		if _b_r_leg != -1:
			var q_leg_r := Quaternion(Vector3(1, 0, 0), leg_swing)
			skeleton.set_bone_pose_rotation(_b_r_leg, q_leg_r)
		if _b_r_knee != -1:
			var knee_flex := maxf(0.0, -leg_swing) * 0.8
			skeleton.set_bone_pose_rotation(_b_r_knee, Quaternion(Vector3(1, 0, 0), knee_flex))
	elif is_entertainer:
		# Danseuse de Cantina : transfert de poids élégant d'un pied sur l'autre
		var dance_leg := sin(idle_breath * 1.8)
		if _b_l_knee != -1:
			var flex_l := maxf(0.0, dance_leg) * deg_to_rad(15.0)
			skeleton.set_bone_pose_rotation(_b_l_knee, Quaternion(Vector3(1, 0, 0), flex_l))
		if _b_r_knee != -1:
			var flex_r := maxf(0.0, -dance_leg) * deg_to_rad(15.0)
			skeleton.set_bone_pose_rotation(_b_r_knee, Quaternion(Vector3(1, 0, 0), flex_r))
		if _b_l_leg != -1:
			skeleton.set_bone_pose_rotation(_b_l_leg, Quaternion(Vector3(0, 0, 1), deg_to_rad(-2.0)))
		if _b_r_leg != -1:
			skeleton.set_bone_pose_rotation(_b_r_leg, Quaternion(Vector3(0, 0, 1), deg_to_rad(2.0)))
	else:
		if _b_l_leg != -1:
			skeleton.set_bone_pose_rotation(_b_l_leg, Quaternion.IDENTITY)
		if _b_r_leg != -1:
			skeleton.set_bone_pose_rotation(_b_r_leg, Quaternion.IDENTITY)
		if _b_l_knee != -1:
			skeleton.set_bone_pose_rotation(_b_l_knee, Quaternion.IDENTITY)
		if _b_r_knee != -1:
			skeleton.set_bone_pose_rotation(_b_r_knee, Quaternion.IDENTITY)
