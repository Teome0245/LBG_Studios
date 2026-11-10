"""blender_render_keyframes.py — Pré-calcul des poses 3D du Compagnon pour le Studio Content Bot.

Génère en rendu Cycles CPU 3D (fond transparent) :
- neutral.png (visage repos, posture naturelle bras le long du corps — PAS de T-pose)
- talk_a.png (bouche ouverte voyelle A)
- talk_o.png (bouche ronde voyelle O)
- blink.png (clignement d'yeux)
- joy.png (sourire chaleureux)

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

print(f"==> Démarrage du rendu des keyframes 3D pour Compagnon ({AVATAR_PATH})...")
bpy.ops.wm.read_factory_settings(use_empty=True)

if not os.path.isfile(AVATAR_PATH):
    # Fallback vers prime-client ou swg-client
    for alt in [
        "packages/prime-client/assets/avatars/Compagnon.vrm",
        "packages/compagnon-desktop/overlay/vrm/Compagnon.vrm",
    ]:
        if os.path.isfile(alt):
            AVATAR_PATH = os.path.abspath(alt)
            break

print(f"Chargement avatar : {AVATAR_PATH}")
bpy.ops.import_scene.gltf(filepath=AVATAR_PATH)

# Posture naturelle de l'armature (PAS de T-pose : bras baissés le long du corps)
arm = bpy.data.objects.get("Armature")
if arm and arm.type == "ARMATURE":
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")

    p_l_arm = arm.pose.bones.get("J_Bip_L_UpperArm")
    p_r_arm = arm.pose.bones.get("J_Bip_R_UpperArm")
    p_l_forearm = arm.pose.bones.get("J_Bip_L_LowerArm")
    p_r_forearm = arm.pose.bones.get("J_Bip_R_LowerArm")

    if p_l_arm:
        p_l_arm.rotation_mode = "XYZ"
        p_l_arm.rotation_euler = (math.radians(10), math.radians(15), math.radians(-70))
    if p_r_arm:
        p_r_arm.rotation_mode = "XYZ"
        p_r_arm.rotation_euler = (math.radians(10), math.radians(-15), math.radians(70))

    if p_l_forearm:
        p_l_forearm.rotation_mode = "XYZ"
        p_l_forearm.rotation_euler = (math.radians(0), math.radians(20), math.radians(-15))
    if p_r_forearm:
        p_r_forearm.rotation_mode = "XYZ"
        p_r_forearm.rotation_euler = (math.radians(0), math.radians(-20), math.radians(15))

    bpy.ops.object.mode_set(mode="OBJECT")
    print("Posture naturelle des bras appliquée (bras baissés, fin de la T-pose).")

# Caméra cadrage portrait vertical face à l'avatar
cam_data = bpy.data.cameras.new("PortraitCamera")
cam_data.lens = 52.0  # 52mm portrait naturel
cam_obj = bpy.data.objects.new("PortraitCamera", cam_data)
bpy.context.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj
# Compagnon est orienté vers -Y -> Caméra à Y = -0.92m, hauteur 1.28m, regardant vers +Y
cam_obj.location = (0.0, -0.92, 1.28)
cam_obj.rotation_euler = (math.radians(90), 0.0, 0.0)

# Éclairage 3 points Cyber Studio
key_light = bpy.data.lights.new("StudioKey", type="SUN")
key_light.energy = 3.6
key_light.color = (1.0, 0.98, 0.95)
key_obj = bpy.data.objects.new("StudioKey", key_light)
key_obj.rotation_euler = (math.radians(35), math.radians(-20), 0.0)
bpy.context.collection.objects.link(key_obj)

rim_light = bpy.data.lights.new("CyberCyanRim", type="POINT")
rim_light.energy = 55.0
rim_light.color = (0.0, 0.95, 1.0)  # Cyan néon
rim_obj = bpy.data.objects.new("CyberCyanRim", rim_light)
rim_obj.location = (0.6, 0.5, 1.45)
bpy.context.collection.objects.link(rim_obj)

fill_light = bpy.data.lights.new("CyberMagentaFill", type="POINT")
fill_light.energy = 25.0
fill_light.color = (1.0, 0.15, 0.8)  # Magenta néon
fill_obj = bpy.data.objects.new("CyberMagentaFill", fill_light)
fill_obj.location = (-0.55, -0.6, 1.35)
bpy.context.collection.objects.link(fill_obj)

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

# Définition des poses cibles spécifiques à Compagnon.vrm
POSES = {
    "neutral": {},
    "talk_a": {"Fcl_MTH_A": 0.95},
    "talk_o": {"Fcl_MTH_O": 0.95},
    "blink": {"Fcl_EYE_Close": 1.0},
    "joy": {"Fcl_ALL_Joy": 0.85, "Fcl_MTH_Joy": 0.85},
}

for pose_name, weights in POSES.items():
    out_file = os.path.join(ASSETS_DIR, f"{pose_name}.png")

    # Réinitialiser toutes les shape_keys
    for sk in shape_keys:
        if sk.name != "Basis":
            sk.value = 0.0

    # Appliquer les poids de la pose
    for sk_name, w in weights.items():
        if sk_name in shape_keys:
            shape_keys[sk_name].value = w
        else:
            print(f"WARN: Shape key '{sk_name}' absente")

    scene.render.filepath = out_file
    t_start = time.time()
    print(f"Rendu de la pose Compagnon '{pose_name}'...")
    bpy.ops.render.render(write_still=True)
    print(f"-> {pose_name}.png généré en {time.time()-t_start:.2f}s ({os.path.getsize(out_file)} octets)")

print("==> Rendu des keyframes Compagnon terminé avec succès !")
