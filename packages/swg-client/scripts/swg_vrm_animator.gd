class_name SwgVrmAnimator
extends Node
## Animateur procédural pour avatars VRM Humanoid dans SWG Godot 4.
## Élimine la T-Pose au repos (A-pose détendue naturelle) et génère
## le balancement locomoteur lors des déplacements.

var skeleton: Skeleton3D = null

# Indices des os Humanoid VRoid / VRM
var _b_spine: int = -1
var _b_l_arm: int = -1
var _b_r_arm: int = -1
var _b_l_forearm: int = -1
var _b_r_forearm: int = -1
var _b_l_leg: int = -1
var _b_r_leg: int = -1
var _b_l_knee: int = -1
var _b_r_knee: int = -1

# État locomoteur
var is_moving: bool = false
var move_speed: float = 0.0
var walk_cycle: float = 0.0
var idle_breath: float = 0.0

# Facteur de transition douce (lerp)
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


func setup(sk: Skeleton3D) -> void:
	skeleton = sk
	if skeleton == null:
		return

	_b_spine = skeleton.find_bone("J_Bip_C_Spine")
	_b_l_arm = skeleton.find_bone("J_Bip_L_UpperArm")
	_b_r_arm = skeleton.find_bone("J_Bip_R_UpperArm")
	_b_l_forearm = skeleton.find_bone("J_Bip_L_LowerArm")
	_b_r_forearm = skeleton.find_bone("J_Bip_R_LowerArm")
	_b_l_leg = skeleton.find_bone("J_Bip_L_UpperLeg")
	_b_r_leg = skeleton.find_bone("J_Bip_R_UpperLeg")
	_b_l_knee = skeleton.find_bone("J_Bip_L_LowerLeg")
	_b_r_knee = skeleton.find_bone("J_Bip_R_LowerLeg")

	# Initialisation immédiate au repos sans T-Pose dès la frame 0
	_apply_pose(0.016)


func _process(delta: float) -> void:
	var parent_node := get_parent()
	if parent_node is CharacterBody3D:
		var cb := parent_node as CharacterBody3D
		var planar_v := Vector2(cb.velocity.x, cb.velocity.z).length()
		update_animation(delta, planar_v > 0.15, planar_v)
	else:
		# PNJ ou décor animé : Idle naturelle
		update_animation(delta, false, 0.0)


func update_animation(delta: float, moving: bool, speed: float) -> void:
	if skeleton == null:
		return

	is_moving = moving
	move_speed = speed
	idle_breath += delta * 2.0

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

	# 1. Torse & Respiration
	if _b_spine != -1:
		var spine_rot := Quaternion(Vector3(1, 0, 0), breath_sin * 0.5)
		skeleton.set_bone_pose_rotation(_b_spine, spine_rot)

	# 2. Bras : Sortir de la T-Pose vers les côtés (Z: ~ -72° gauche, +72° droite)
	var arm_base_z_l := deg_to_rad(-72.0)
	var arm_base_z_r := deg_to_rad(72.0)
	var arm_swing := 0.0

	if is_moving:
		arm_swing = walk_sin * deg_to_rad(24.0)

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

	# Coudes / Avant-bras légèrement pliés (14° naturel)
	if _b_l_forearm != -1:
		var elbow_swing := 0.0
		if is_moving and arm_swing > 0.0:
			elbow_swing = arm_swing * 0.4
		var q_elbow := Quaternion(Vector3(1, 0, 0), deg_to_rad(14.0) + elbow_swing)
		skeleton.set_bone_pose_rotation(_b_l_forearm, q_elbow)

	if _b_r_forearm != -1:
		var elbow_swing := 0.0
		if is_moving and -arm_swing > 0.0:
			elbow_swing = -arm_swing * 0.4
		var q_elbow := Quaternion(Vector3(1, 0, 0), deg_to_rad(14.0) + elbow_swing)
		skeleton.set_bone_pose_rotation(_b_r_forearm, q_elbow)

	# 3. Jambes & Foulée
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
	else:
		if _b_l_leg != -1:
			skeleton.set_bone_pose_rotation(_b_l_leg, Quaternion.IDENTITY)
		if _b_r_leg != -1:
			skeleton.set_bone_pose_rotation(_b_r_leg, Quaternion.IDENTITY)
		if _b_l_knee != -1:
			skeleton.set_bone_pose_rotation(_b_l_knee, Quaternion.IDENTITY)
		if _b_r_knee != -1:
			skeleton.set_bone_pose_rotation(_b_r_knee, Quaternion.IDENTITY)
