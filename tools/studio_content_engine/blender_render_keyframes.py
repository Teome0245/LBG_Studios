"""blender_render_keyframes.py — Pré-calcul des poses 3D en plein pied de Lia Androïde pour le Studio Content Bot.

Génère en rendu Cycles CPU 3D (fond transparent, texture Cyber-Androïde exacte, cinématique naturelle) :
- neutral.png (posture naturelle détendue, micro-contrapposto, regard vivant)
- talk_a.png (bouche ouverte voyelle A avec sourcils attentifs)
- talk_o.png (bouche ronde voyelle O expressive)
- blink.png (clignement d'yeux naturel)
- joy.png (sourire chaleureux et bienveillant)
- explain.png (gestuelle mains ouvertes vers le spectateur)
- explain_talk.png (gestuelle explication + parole synchronisée)
- point.png (bras droit désignant l'infographie avec regard connecté)
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
VRM_TEXTURES_DIR = os.path.abspath("packages/cortex/compagnon_ui/public/vrm")

os.makedirs(ASSETS_DIR, exist_ok=True)

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

# ==============================================================================
# 1. APPLICATION DU SKIN OFFICIEL LIA ANDROÏDE CYBER (CYAN & MÉTAUX)
# ==============================================================================
print("==> Application des textures et matériaux Lia Androïde Cyber...")

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
            print(f"  [+] Texture appliquée : {mat_name} -> {img_name}")

# Optiques cybernétiques : Yeux iris cyan émissifs néon (#00f5d4)
iris_mat = bpy.data.materials.get("N00_000_00_EyeIris_00_EYE (Instance)")
if iris_mat and iris_mat.node_tree:
    for n in iris_mat.node_tree.nodes:
        if n.type == "EMISSION":
            n.inputs["Color"].default_value = (0.0, 0.96, 0.83, 1.0)
            n.inputs["Strength"].default_value = 3.2
            print("  [+] Iris cyber cyan émissifs activés (0x00f5d4)")


# ==============================================================================
# 2. CINÉMATIQUE CORPORELLE NATURELLE (BASSIN, BUSTE, ÉPAULES, COUDES, POIGNETS)
# ==============================================================================
def apply_full_pose(bone_dict: dict[str, tuple[float, float, float]]) -> None:
    """Applique une pose anatomique naturelle complète sur l'armature humanoïde."""
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    bones = arm.pose.bones

    # Réinitialisation préalable des os majeurs
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


# Dictionnaires articulaires naturels (angles mesurés en degrés XYZ)
# 1. Pose de repos vivante : léger contrapposto, buste souple, coudes légèrement fléchis, mains détendues
POSE_NATURAL_IDLE = {
    "J_Bip_C_Hips": (0.0, 1.5, 0.5),          # Léger déhanché féminin subtil
    "J_Bip_C_Spine": (2.5, 0.0, -0.5),        # Légère écoute vers l'avant
    "J_Bip_C_Neck": (-1.0, 0.0, 0.0),
    "J_Bip_C_Head": (1.0, -1.0, 0.5),         # Regard doux droit caméra
    "J_Bip_L_Shoulder": (0.0, 0.0, -3.0),     # Épaule gauche tombante détendue
    "J_Bip_R_Shoulder": (0.0, 0.0, 3.0),      # Épaule droite tombante détendue
    "J_Bip_L_UpperArm": (8.0, 12.0, -68.0),
    "J_Bip_R_UpperArm": (8.0, -12.0, 68.0),
    "J_Bip_L_LowerArm": (0.0, 25.0, -12.0),   # Coude souple fléchi à 25°
    "J_Bip_R_LowerArm": (0.0, -25.0, 12.0),
    "J_Bip_L_Hand": (0.0, 8.0, -5.0),         # Poignet décontracté
    "J_Bip_R_Hand": (0.0, -8.0, 5.0),
}

# 2. Pose d'explication expressive : mains ouvertes, coudes souples, buste engagé
POSE_EXPLAIN = {
    "J_Bip_C_Hips": (0.0, 0.5, 0.0),
    "J_Bip_C_Spine": (4.0, 0.0, 0.0),         # Présence orientée spectateur
    "J_Bip_C_Head": (1.5, 0.0, 0.0),
    "J_Bip_L_Shoulder": (0.0, 3.0, -2.0),
    "J_Bip_R_Shoulder": (0.0, -3.0, 2.0),
    "J_Bip_L_UpperArm": (32.0, 18.0, -38.0),
    "J_Bip_R_UpperArm": (32.0, -18.0, 38.0),
    "J_Bip_L_LowerArm": (-22.0, 38.0, -25.0),
    "J_Bip_R_LowerArm": (-22.0, -38.0, 25.0),
    "J_Bip_L_Hand": (10.0, 15.0, -10.0),      # Paumes orientées vers le haut
    "J_Bip_R_Hand": (10.0, -15.0, 10.0),
}

# 3. Pose de désignation (Point) : bras droit désignant l'infographie sur le côté
POSE_POINT = {
    "J_Bip_C_Hips": (0.0, -1.5, -0.5),
    "J_Bip_C_Spine": (2.0, -1.0, 1.5),
    "J_Bip_C_Head": (-1.0, 5.0, -3.0),        # Tête orientée vers l'élément montré
    "J_Bip_L_Shoulder": (0.0, 0.0, -3.0),
    "J_Bip_R_Shoulder": (0.0, -5.0, 5.0),
    "J_Bip_L_UpperArm": (10.0, 12.0, -68.0),
    "J_Bip_R_UpperArm": (28.0, -28.0, 24.0),
    "J_Bip_L_LowerArm": (0.0, 22.0, -12.0),
    "J_Bip_R_LowerArm": (0.0, -48.0, 42.0),
    "J_Bip_R_Hand": (5.0, -20.0, 15.0),       # Main ouverte invitant du regard
}

# 4. Pose de réflexion (Think) : main gauche près du menton, légère inclinaison de tête
POSE_THINK = {
    "J_Bip_C_Hips": (0.0, 2.0, 0.0),
    "J_Bip_C_Spine": (2.0, 0.0, -1.0),
    "J_Bip_C_Head": (4.0, -7.0, 6.0),         # Inclinaison pensive
    "J_Bip_L_Shoulder": (0.0, 4.0, -2.0),
    "J_Bip_R_Shoulder": (0.0, 0.0, 3.0),
    "J_Bip_L_UpperArm": (48.0, 22.0, -18.0),
    "J_Bip_R_UpperArm": (10.0, -12.0, 68.0),
    "J_Bip_L_LowerArm": (-28.0, 78.0, -46.0),
    "J_Bip_R_LowerArm": (0.0, -20.0, 12.0),
    "J_Bip_L_Hand": (15.0, 25.0, -15.0),      # Doigts vers la mâchoire
}


# ==============================================================================
# 3. CAMÉRA ET ÉCLAIRAGE STUDIO PLEIN PIED 1080x1920
# ==============================================================================
cam_data = bpy.data.cameras.new("FullBodyCamera")
cam_data.lens = 46.0
cam_obj = bpy.data.objects.new("FullBodyCamera", cam_data)
bpy.context.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj
# Cadrage parfait du personnage (1.62m) centré de la tête aux pieds
cam_obj.location = (0.0, -2.52, 0.84)
cam_obj.rotation_euler = (math.radians(90), 0.0, 0.0)

# Éclairage 4 points Cyber Androïde (Lia Signature)
key_light = bpy.data.lights.new("StudioKey", type="SUN")
key_light.energy = 4.0
key_light.color = (1.0, 0.98, 0.96)
key_obj = bpy.data.objects.new("StudioKey", key_light)
key_obj.rotation_euler = (math.radians(38), math.radians(-22), 0.0)
bpy.context.collection.objects.link(key_obj)

rim_light = bpy.data.lights.new("CyberCyanRim", type="POINT")
rim_light.energy = 75.0
rim_light.color = (0.0, 0.96, 0.83)  # Cyan néon vif
rim_obj = bpy.data.objects.new("CyberCyanRim", rim_light)
rim_obj.location = (0.80, 0.55, 1.10)
bpy.context.collection.objects.link(rim_obj)

fill_light = bpy.data.lights.new("CyberMagentaFill", type="POINT")
fill_light.energy = 42.0
fill_light.color = (1.0, 0.12, 0.78)  # Magenta cyber
fill_obj = bpy.data.objects.new("CyberMagentaFill", fill_light)
fill_obj.location = (-0.80, -0.60, 0.98)
bpy.context.collection.objects.link(fill_obj)

floor_light = bpy.data.lights.new("CyberFloorRim", type="POINT")
floor_light.energy = 28.0
floor_light.color = (0.0, 0.88, 1.0)
floor_obj = bpy.data.objects.new("CyberFloorRim", floor_light)
floor_obj.location = (0.0, -0.45, 0.16)
bpy.context.collection.objects.link(floor_obj)

# Cycles CPU optimisé
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 6
scene.cycles.use_denoising = True
scene.render.film_transparent = True
scene.render.resolution_x = 720
scene.render.resolution_y = 1280
scene.render.resolution_percentage = 100

face_obj = bpy.data.objects.get("Face")
if not face_obj or not face_obj.data.shape_keys:
    print("ERR: Face mesh ou shape_keys introuvables")
    sys.exit(1)

shape_keys = face_obj.data.shape_keys.key_blocks

# ==============================================================================
# 4. DICTIONNAIRE DES 9 POSES CLÉS AVEC EXPRESSIONS VIVANTES
# ==============================================================================
POSES: dict[str, dict] = {
    "neutral": {
        "armature": POSE_NATURAL_IDLE,
        "face": {"Fcl_ALL_Joy": 0.15, "Fcl_MTH_Joy": 0.12},  # Micro-sourire naturel
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
    "point": {
        "armature": POSE_POINT,
        "face": {"Fcl_MTH_Joy": 0.40, "Fcl_BRW_Joy": 0.40},
    },
    "think": {
        "armature": POSE_THINK,
        "face": {"Fcl_MTH_O": 0.30, "Fcl_BRW_Fun": 0.35},
    },
}

# ==============================================================================
# 5. RENDU CYCLES DES 9 POSES LIA ANDROÏDE
# ==============================================================================
print(f"==> Lancement du rendu des 9 poses Lia Androïde dans {ASSETS_DIR}...")

for pose_name, conf in POSES.items():
    out_file = os.path.join(ASSETS_DIR, f"{pose_name}.png")

    # 1. Pose squelettique naturelle
    apply_full_pose(conf["armature"])

    # 2. Reset des morphs faciaux
    for sk in shape_keys:
        if sk.name != "Basis":
            sk.value = 0.0

    # 3. Application des morphs expressifs
    for sk_name, w in conf["face"].items():
        if sk_name in shape_keys:
            shape_keys[sk_name].value = w

    # 4. Rendu de l'image
    scene.render.filepath = out_file
    t_start = time.time()
    print(f"Rendu pose '{pose_name}'...")
    bpy.ops.render.render(write_still=True)
    dur = time.time() - t_start
    size_kb = os.path.getsize(out_file) / 1024
    print(f"  -> {pose_name}.png généré en {dur:.1f}s ({size_kb:.1f} Ko)")

print("\n==> TOUTES LES POSES LIA ANDROÏDE ONT ÉTÉ GÉNÉRÉES AVEC SUCCÈS !")
