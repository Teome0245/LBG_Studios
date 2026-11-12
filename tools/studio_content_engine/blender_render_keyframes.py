"""blender_render_keyframes.py — Pré-calcul des poses 3D en plein pied pour le Studio Content Bot.

Génère en rendu Cycles CPU 3D (fond transparent, cadrage en pied) :
- neutral.png (posture naturelle debout bras le long du corps, regard repos)
- talk_a.png (bouche ouverte voyelle A)
- talk_o.png (bouche ronde voyelle O)
- blink.png (clignement d'yeux)
- joy.png (sourire chaleureux)
- explain.png (gestuelle mains ouvertes vers le spectateur)
- explain_talk.png (gestuelle explication + parole bouche A)
- point.png (bras droit désignant le côté / l'encart d'information)
- think.png (posture de réflexion, main au menton, tête inclinée)

Utilisation :
    blender -b --python tools/studio_content_engine/blender_render_keyframes.py
"""

from __future__ import annotations

import math
import os
import sys
import time
import bpy

ASSETS_DIR = os.path.abspath("tools/studio_content_engine/assets/compagnon")
AVATAR_PATH = os.path.abspath("packages/cortex/compagnon_ui/public/vrm/Compagnon.vrm")

os.makedirs(ASSETS_DIR, exist_ok=True)

print(f"==> Démarrage du rendu des keyframes 3D plein pied pour Compagnon ({AVATAR_PATH})...")
bpy.ops.wm.read_factory_settings(use_empty=True)

if not os.path.isfile(AVATAR_PATH):
    for alt in [
        "packages/prime-client/assets/avatars/Compagnon.vrm",
        "packages/compagnon-desktop/overlay/vrm/Compagnon.vrm",
    ]:
        if os.path.isfile(alt):
            AVATAR_PATH = os.path.abspath(alt)
            break

print(f"Chargement avatar : {AVATAR_PATH}")
bpy.ops.import_scene.gltf(filepath=AVATAR_PATH)

arm = bpy.data.objects.get("Armature")
if not arm or arm.type != "ARMATURE":
    print("ERR: Armature introuvable pour Compagnon")
    sys.exit(1)


def apply_armature_pose(
    l_arm: tuple[float, float, float],
    r_arm: tuple[float, float, float],
    l_forearm: tuple[float, float, float],
    r_forearm: tuple[float, float, float],
    head: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> None:
    """Applique une pose spécifique sur les membres supérieurs et la tête de l'avatar."""
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    bones = arm.pose.bones

    bone_configs = [
        ("J_Bip_L_UpperArm", l_arm),
        ("J_Bip_R_UpperArm", r_arm),
        ("J_Bip_L_LowerArm", l_forearm),
        ("J_Bip_R_LowerArm", r_forearm),
        ("J_Bip_C_Head", head),
    ]
    for b_name, euler_deg in bone_configs:
        pb = bones.get(b_name)
        if pb:
            pb.rotation_mode = "XYZ"
            pb.rotation_euler = (
                math.radians(euler_deg[0]),
                math.radians(euler_deg[1]),
                math.radians(euler_deg[2]),
            )
    bpy.ops.object.mode_set(mode="OBJECT")


# Configurations articulaires clés
POSE_NATURAL_ARMS = {
    "l_arm": (10.0, 15.0, -70.0),
    "r_arm": (10.0, -15.0, 70.0),
    "l_forearm": (0.0, 20.0, -15.0),
    "r_forearm": (0.0, -20.0, 15.0),
    "head": (0.0, 0.0, 0.0),
}

POSE_EXPLAIN_ARMS = {
    "l_arm": (35.0, 20.0, -35.0),
    "r_arm": (35.0, -20.0, 35.0),
    "l_forearm": (-25.0, 40.0, -30.0),
    "r_forearm": (-25.0, -40.0, 30.0),
    "head": (2.0, 0.0, 0.0),
}

POSE_POINT_ARMS = {
    "l_arm": (10.0, 15.0, -70.0),
    "r_arm": (30.0, -30.0, 25.0),
    "l_forearm": (0.0, 20.0, -15.0),
    "r_forearm": (0.0, -50.0, 45.0),
    "head": (0.0, 6.0, -4.0),
}

POSE_THINK_ARMS = {
    "l_arm": (50.0, 25.0, -15.0),
    "r_arm": (10.0, -15.0, 70.0),
    "l_forearm": (-30.0, 80.0, -50.0),
    "r_forearm": (0.0, -20.0, 15.0),
    "head": (5.0, -8.0, 8.0),
}

# Caméra cadrage vertical PLEIN PIED (tête à pieds visible)
cam_data = bpy.data.cameras.new("FullBodyCamera")
cam_data.lens = 45.0  # 45mm perspective équilibrée
cam_obj = bpy.data.objects.new("FullBodyCamera", cam_data)
bpy.context.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj
# Compagnon 1.62m -> Caméra reculée à Y = -2.55m, hauteur Z = 0.82m
cam_obj.location = (0.0, -2.55, 0.82)
cam_obj.rotation_euler = (math.radians(90), 0.0, 0.0)

# Éclairage 4 points Cyber Studio Full Body
key_light = bpy.data.lights.new("StudioKey", type="SUN")
key_light.energy = 3.8
key_light.color = (1.0, 0.98, 0.95)
key_obj = bpy.data.objects.new("StudioKey", key_light)
key_obj.rotation_euler = (math.radians(35), math.radians(-20), 0.0)
bpy.context.collection.objects.link(key_obj)

rim_light = bpy.data.lights.new("CyberCyanRim", type="POINT")
rim_light.energy = 65.0
rim_light.color = (0.0, 0.95, 1.0)  # Cyan néon
rim_obj = bpy.data.objects.new("CyberCyanRim", rim_light)
rim_obj.location = (0.75, 0.5, 1.05)
bpy.context.collection.objects.link(rim_obj)

fill_light = bpy.data.lights.new("CyberMagentaFill", type="POINT")
fill_light.energy = 40.0
fill_light.color = (1.0, 0.15, 0.8)  # Magenta néon
fill_obj = bpy.data.objects.new("CyberMagentaFill", fill_light)
fill_obj.location = (-0.75, -0.6, 0.95)
bpy.context.collection.objects.link(fill_obj)

floor_light = bpy.data.lights.new("CyberFloorRim", type="POINT")
floor_light.energy = 25.0
floor_light.color = (0.0, 0.85, 1.0)  # Rim discret chaussures / sol
floor_obj = bpy.data.objects.new("CyberFloorRim", floor_light)
floor_obj.location = (0.0, -0.4, 0.15)
bpy.context.collection.objects.link(floor_obj)

# Configuration Cycles CPU
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 4
scene.cycles.use_denoising = True
scene.render.film_transparent = True
scene.render.resolution_x = 720
scene.render.resolution_y = 1280
scene.render.resolution_percentage = 100

face_obj = bpy.data.objects.get("Face")
if not face_obj or not face_obj.data.shape_keys:
    print("ERR: Face mesh ou shape_keys introuvables pour Compagnon")
    sys.exit(1)

shape_keys = face_obj.data.shape_keys.key_blocks

# Définition complète des poses : articulation du corps + morph facial
POSES: dict[str, dict] = {
    "neutral": {
        "armature": POSE_NATURAL_ARMS,
        "face": {},
    },
    "talk_a": {
        "armature": POSE_NATURAL_ARMS,
        "face": {"Fcl_MTH_A": 0.95},
    },
    "talk_o": {
        "armature": POSE_NATURAL_ARMS,
        "face": {"Fcl_MTH_O": 0.95},
    },
    "blink": {
        "armature": POSE_NATURAL_ARMS,
        "face": {"Fcl_EYE_Close": 1.0},
    },
    "joy": {
        "armature": POSE_NATURAL_ARMS,
        "face": {"Fcl_ALL_Joy": 0.85, "Fcl_MTH_Joy": 0.85},
    },
    "explain": {
        "armature": POSE_EXPLAIN_ARMS,
        "face": {"Fcl_MTH_A": 0.20},
    },
    "explain_talk": {
        "armature": POSE_EXPLAIN_ARMS,
        "face": {"Fcl_MTH_A": 0.90},
    },
    "point": {
        "armature": POSE_POINT_ARMS,
        "face": {"Fcl_MTH_A": 0.60, "Fcl_ALL_Joy": 0.40},
    },
    "think": {
        "armature": POSE_THINK_ARMS,
        "face": {"Fcl_MTH_O": 0.35},
    },
}

for pose_name, conf in POSES.items():
    out_file = os.path.join(ASSETS_DIR, f"{pose_name}.png")

    # 1. Appliquer la pose squelettique
    arm_conf = conf["armature"]
    apply_armature_pose(
        l_arm=arm_conf["l_arm"],
        r_arm=arm_conf["r_arm"],
        l_forearm=arm_conf["l_forearm"],
        r_forearm=arm_conf["r_forearm"],
        head=arm_conf["head"],
    )

    # 2. Réinitialiser toutes les shape_keys du visage
    for sk in shape_keys:
        if sk.name != "Basis":
            sk.value = 0.0

    # 3. Appliquer les poids de morph du visage
    for sk_name, w in conf["face"].items():
        if sk_name in shape_keys:
            shape_keys[sk_name].value = w
        else:
            print(f"WARN: Shape key '{sk_name}' absente")

    # 4. Rendu de l'image
    scene.render.filepath = out_file
    t_start = time.time()
    print(f"Rendu de la pose plein pied '{pose_name}'...")
    bpy.ops.render.render(write_still=True)
    print(f"-> {pose_name}.png généré en {time.time()-t_start:.2f}s ({os.path.getsize(out_file)} octets)")

print("==> Rendu des keyframes Compagnon plein pied terminé avec succès !")
