"""blender_render_multicam.py — Rendu des poses Lia en Plan Moyen et Gros Plan pour le mode JRPG.

Génère avec Cycles CPU 3D (fond transparent, texture Cyber-Androïde exacte, cinématique naturelle) :
- compagnon_medium/ : neutral, talk_a, talk_o, blink, think, explain, explain_talk, joy
- compagnon_closeup/ : neutral, talk_a, talk_o, blink, think, explain, explain_talk, joy

Utilisation :
    blender -b --python tools/studio_content_engine/blender_render_multicam.py
"""

from __future__ import annotations

import math
import os
import sys
import time
import bpy

ASSETS_DIR = os.path.abspath("tools/studio_content_engine/assets")
MEDIUM_DIR = os.path.join(ASSETS_DIR, "compagnon_medium")
CLOSEUP_DIR = os.path.join(ASSETS_DIR, "compagnon_closeup")
AVATAR_PATH = os.path.abspath("packages/cortex/compagnon_ui/public/vrm/Compagnon.vrm")
VRM_TEXTURES_DIR = os.path.abspath("packages/cortex/compagnon_ui/public/vrm")

os.makedirs(MEDIUM_DIR, exist_ok=True)
os.makedirs(CLOSEUP_DIR, exist_ok=True)

print(f"==> Chargement de l'avatar 3D de Lia ({AVATAR_PATH})...")
bpy.ops.wm.read_factory_settings(use_empty=True)

if not os.path.isfile(AVATAR_PATH):
    for alt in [
        "packages/prime-client/assets/avatars/Compagnon.vrm",
        "packages/compagnon-desktop/overlay/vrm/Compagnon.vrm",
    ]:
        if os.path.isfile(alt):
            AVATAR_PATH = os.path.abspath(alt)
            break

bpy.ops.import_scene.gltf(filepath=AVATAR_PATH)

arm = bpy.data.objects.get("Armature")
if not arm or arm.type != "ARMATURE":
    print("ERR: Armature introuvable pour Compagnon")
    sys.exit(1)

# 1. TEXTURES LIA ANDROÏDE CYBER
texture_mappings = {
    "N00_000_00_Body_00_SKIN (Instance)": "body_skin_android.png",
    "N00_000_00_Face_00_SKIN (Instance)": "face_skin_android.png",
    "N00_000_00_HairBack_00_HAIR (Instance)": "hair_android.png",
    "N00_000_Hair_00_HAIR (Instance)": "hair_android.png",
}

for mat_name, img_name in texture_mappings.items():
    mat = bpy.data.materials.get(mat_name)
    if mat and mat.node_tree:
        img_path = os.path.join(VRM_TEXTURES_DIR, img_name)
        if os.path.isfile(img_path):
            img = bpy.data.images.load(img_path)
            for n in mat.node_tree.nodes:
                if n.type == "TEX_IMAGE":
                    n.image = img

# Yeux iris cyan émissifs
iris_mat = bpy.data.materials.get("N00_000_00_EyeIris_00_EYE (Instance)")
if iris_mat and iris_mat.node_tree:
    for n in iris_mat.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            n.inputs["Emission Color"].default_value = (0.0, 0.96, 0.83, 1.0)
            n.inputs["Emission Strength"].default_value = 2.8
        elif n.type == "EMISSION":
            n.inputs["Color"].default_value = (0.0, 0.96, 0.83, 1.0)
            n.inputs["Strength"].default_value = 2.8

# 2. CINÉMATIQUE CORPORELLE
def apply_full_pose(bone_dict: dict[str, tuple[float, float, float]]) -> None:
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    bones = arm.pose.bones

    reset_bones = [
        "J_Bip_C_Hips", "J_Bip_C_Spine", "J_Bip_C_Neck", "J_Bip_C_Head",
        "J_Bip_L_Shoulder", "J_Bip_R_Shoulder",
        "J_Bip_L_UpperArm", "J_Bip_R_UpperArm",
        "J_Bip_L_LowerArm", "J_Bip_R_LowerArm",
        "J_Bip_L_Hand", "J_Bip_R_Hand",
    ]
    for b_name in reset_bones:
        pb = bones.get(b_name)
        if pb:
            pb.rotation_mode = "XYZ"
            pb.rotation_euler = (0.0, 0.0, 0.0)

    for b_name, euler_deg in bone_dict.items():
        pb = bones.get(b_name)
        if pb:
            pb.rotation_mode = "XYZ"
            pb.rotation_euler = (
                math.radians(euler_deg[0]),
                math.radians(euler_deg[1]),
                math.radians(euler_deg[2]),
            )
    bpy.ops.object.mode_set(mode="OBJECT")

POSE_NATURAL_IDLE = {
    "J_Bip_C_Hips": (0.0, 1.5, 0.5),
    "J_Bip_C_Spine": (2.5, 0.0, -0.5),
    "J_Bip_C_Neck": (-1.0, 0.0, 0.0),
    "J_Bip_C_Head": (1.0, -1.0, 0.5),
    "J_Bip_L_Shoulder": (0.0, 0.0, -3.0),
    "J_Bip_R_Shoulder": (0.0, 0.0, 3.0),
    "J_Bip_L_UpperArm": (8.0, 12.0, -68.0),
    "J_Bip_R_UpperArm": (8.0, -12.0, 68.0),
    "J_Bip_L_LowerArm": (0.0, 25.0, -12.0),
    "J_Bip_R_LowerArm": (0.0, -25.0, 12.0),
    "J_Bip_L_Hand": (0.0, 8.0, -5.0),
    "J_Bip_R_Hand": (0.0, -8.0, 5.0),
}

POSE_EXPLAIN = {
    "J_Bip_C_Hips": (0.0, 0.5, 0.0),
    "J_Bip_C_Spine": (4.0, 0.0, 0.0),
    "J_Bip_C_Head": (1.5, 0.0, 0.0),
    "J_Bip_L_Shoulder": (0.0, 3.0, -2.0),
    "J_Bip_R_Shoulder": (0.0, -3.0, 2.0),
    "J_Bip_L_UpperArm": (32.0, 18.0, -38.0),
    "J_Bip_R_UpperArm": (32.0, -18.0, 38.0),
    "J_Bip_L_LowerArm": (-22.0, 38.0, -25.0),
    "J_Bip_R_LowerArm": (-22.0, -38.0, 25.0),
    "J_Bip_L_Hand": (10.0, 15.0, -10.0),
    "J_Bip_R_Hand": (10.0, -15.0, 10.0),
}

POSE_THINK = {
    "J_Bip_C_Hips": (0.0, 2.0, 0.0),
    "J_Bip_C_Spine": (2.0, 0.0, -1.0),
    "J_Bip_C_Head": (4.0, -7.0, 6.0),
    "J_Bip_L_Shoulder": (0.0, 4.0, -2.0),
    "J_Bip_R_Shoulder": (0.0, 0.0, 3.0),
    "J_Bip_L_UpperArm": (48.0, 22.0, -18.0),
    "J_Bip_R_UpperArm": (10.0, -12.0, 68.0),
    "J_Bip_L_LowerArm": (-28.0, 78.0, -46.0),
    "J_Bip_R_LowerArm": (0.0, -20.0, 12.0),
    "J_Bip_L_Hand": (15.0, 25.0, -15.0),
}

# 3. CAMÉRAS ET ÉCLAIRAGE
# Key light
key_light = bpy.data.lights.new("KeyLight", type="SUN")
key_light.energy = 4.0
key_light.color = (1.0, 0.98, 0.96)
key_obj = bpy.data.objects.new("KeyLight", key_light)
key_obj.rotation_euler = (math.radians(38), math.radians(-22), 0.0)
bpy.context.collection.objects.link(key_obj)

# Cyan rim light
rim_light = bpy.data.lights.new("CyanRim", type="POINT")
rim_light.energy = 70.0
rim_light.color = (0.0, 0.96, 0.83)
rim_obj = bpy.data.objects.new("CyanRim", rim_light)
rim_obj.location = (0.75, 0.50, 1.25)
bpy.context.collection.objects.link(rim_obj)

# Magenta fill light
fill_light = bpy.data.lights.new("MagentaFill", type="POINT")
fill_light.energy = 38.0
fill_light.color = (1.0, 0.12, 0.78)
fill_obj = bpy.data.objects.new("MagentaFill", fill_light)
fill_obj.location = (-0.75, -0.55, 1.15)
bpy.context.collection.objects.link(fill_obj)

# Caméra Plan Moyen (Medium Cam) : cadrage taille/buste/tête
cam_m_data = bpy.data.cameras.new("MediumCam")
cam_m_data.lens = 48.0
cam_m = bpy.data.objects.new("MediumCam", cam_m_data)
cam_m.location = (0.0, -1.35, 1.22)
cam_m.rotation_euler = (math.radians(90), 0.0, 0.0)
bpy.context.collection.objects.link(cam_m)

# Caméra Gros Plan (CloseUp Cam) : visage et regard expressif
cam_c_data = bpy.data.cameras.new("CloseUpCam")
cam_c_data.lens = 54.0
cam_c = bpy.data.objects.new("CloseUpCam", cam_c_data)
cam_c.location = (0.0, -0.72, 1.38)
cam_c.rotation_euler = (math.radians(90), 0.0, 0.0)
bpy.context.collection.objects.link(cam_c)

# Paramètres de rendu Cycles CPU rapide
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 6
scene.cycles.use_denoising = True
scene.render.film_transparent = True
scene.render.resolution_x = 720
scene.render.resolution_y = 1280
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"

face_obj = bpy.data.objects.get("Face")
if not face_obj or not face_obj.data.shape_keys:
    print("ERR: Face mesh ou shape_keys introuvables")
    sys.exit(1)

shape_keys = face_obj.data.shape_keys.key_blocks

# Dictionnaire des poses avec morphs faciaux
POSES = {
    "neutral": {
        "armature": POSE_NATURAL_IDLE,
        "face": {"Fcl_ALL_Joy": 0.15, "Fcl_MTH_Joy": 0.12},
    },
    "talk_a": {
        "armature": POSE_NATURAL_IDLE,
        "face": {"Fcl_MTH_A": 0.90, "Fcl_BRW_Joy": 0.25, "Fcl_ALL_Joy": 0.18},
    },
    "talk_o": {
        "armature": POSE_NATURAL_IDLE,
        "face": {"Fcl_MTH_O": 0.88, "Fcl_BRW_Fun": 0.30},
    },
    "blink": {
        "armature": POSE_NATURAL_IDLE,
        "face": {"Fcl_EYE_Close": 1.0, "Fcl_MTH_Joy": 0.10},
    },
    "joy": {
        "armature": POSE_NATURAL_IDLE,
        "face": {"Fcl_ALL_Joy": 0.85, "Fcl_MTH_Joy": 0.85, "Fcl_BRW_Joy": 0.50},
    },
    "explain": {
        "armature": POSE_EXPLAIN,
        "face": {"Fcl_MTH_Joy": 0.30, "Fcl_BRW_Joy": 0.25},
    },
    "explain_talk": {
        "armature": POSE_EXPLAIN,
        "face": {"Fcl_MTH_A": 0.85, "Fcl_BRW_Joy": 0.35, "Fcl_ALL_Joy": 0.20},
    },
    "think": {
        "armature": POSE_THINK,
        "face": {"Fcl_MTH_O": 0.30, "Fcl_BRW_Fun": 0.35},
    },
}

# 4. RENDU DES POSES POUR LES DEUX PLANS
targets = [
    ("medium", cam_m, MEDIUM_DIR),
    ("closeup", cam_c, CLOSEUP_DIR),
]

for mode_name, camera_obj, out_dir in targets:
    print(f"\n==> Rendu des poses mode {mode_name.upper()} dans {out_dir}...")
    scene.camera = camera_obj
    for pose_name, conf in POSES.items():
        out_file = os.path.join(out_dir, f"{pose_name}.png")

        # 1. Pose squelettique naturelle
        apply_full_pose(conf["armature"])

        # 2. Reset des shape keys
        for sk in shape_keys:
            if sk.name != "Basis":
                sk.value = 0.0

        # 3. Application des shape keys de la pose
        for sk_name, w in conf["face"].items():
            if sk_name in shape_keys:
                shape_keys[sk_name].value = w

        # 4. Rendu de l'image
        scene.render.filepath = out_file
        t_start = time.time()
        bpy.ops.render.render(write_still=True)
        dur = time.time() - t_start
        size_kb = os.path.getsize(out_file) / 1024
        print(f"  [{mode_name}] {pose_name}.png rendu en {dur:.1f}s ({size_kb:.1f} Ko)")

print("\n==> RENDU MULTI-CAM CYCLES TERMINÉ AVEC SUCCÈS !")
