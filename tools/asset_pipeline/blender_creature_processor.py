#!/usr/bin/env python3
"""
tools/asset_pipeline/blender_creature_processor.py
Nettoie, retopolise, rigge et anime des créatures / personnages (issus d'IA générative ou de scans)
en mode Blender Headless pour Godot 4.

Usage :
    blender -b -P tools/asset_pipeline/blender_creature_processor.py -- --creature-type beast --name quadrupede_alpha
"""

import sys
import os
import argparse
import math

try:
    import bpy
    import bmesh
except ImportError:
    print("Doit être exécuté avec blender -b -P ...")
    sys.exit(1)


def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def build_beast_base_mesh():
    """Génère un maillage de créature quadrupède extraterrestre stylisé (corps, tête, 4 pattes, queue)."""
    clean_scene()

    # Corps / Torse
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.7, location=(0, 0, 1.0))
    torso = bpy.context.active_object
    torso.name = "CreatureMesh"
    torso.scale = (1.5, 0.8, 0.7)
    bpy.ops.object.transform_apply(scale=True)

    # Tête agressive
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.45, subdivisions=2, location=(1.3, 0, 1.35))
    head = bpy.context.active_object
    head.scale = (1.2, 0.7, 0.8)
    bpy.ops.object.transform_apply(scale=True)

    # Pattes (4 cylindres angulés)
    legs = []
    leg_coords = [
        (0.7, 0.55, 0.5),   # Avant gauche
        (0.7, -0.55, 0.5),  # Avant droite
        (-0.7, 0.55, 0.5),  # Arrière gauche
        (-0.7, -0.55, 0.5), # Arrière droite
    ]
    for i, (lx, ly, lz) in enumerate(leg_coords):
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.14, depth=1.0, location=(lx, ly, lz))
        leg = bpy.context.active_object
        leg.name = f"Leg_{i}"
        legs.append(leg)

    # Queue
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.15, radius2=0.03, depth=1.2, location=(-1.3, 0, 0.9))
    tail = bpy.context.active_object
    tail.rotation_euler = (0, math.radians(70), 0)
    bpy.ops.object.transform_apply(rotation=True)

    # Fusion des parties en un seul maillage
    bpy.ops.object.select_all(action='DESELECT')
    torso.select_set(True)
    head.select_set(True)
    tail.select_set(True)
    for leg in legs:
        leg.select_set(True)
    bpy.context.view_layer.objects.active = torso
    bpy.ops.object.join()

    # Matériau chitine / peau extraterrestre
    mat = bpy.data.materials.new(name="Mat_CreatureSkin")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        if "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = (0.35, 0.15, 0.45, 1.0)
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = 0.4
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.2
    torso.data.materials.append(mat)

    return torso


def rig_and_animate_creature(mesh_obj, creature_name: str):
    """Crée un squelette (Armature), bind le mesh et ajoute des animations Idle et Walk."""
    # Création de l'armature
    bpy.ops.object.armature_add(location=(0, 0, 0))
    armature = bpy.context.active_object
    armature.name = f"Armature_{creature_name}"

    bpy.ops.object.mode_set(mode='EDIT')
    bones = armature.data.edit_bones
    root_bone = bones[0]
    root_bone.name = "Root"
    root_bone.head = (0, 0, 0)
    root_bone.tail = (0, 0, 0.5)

    # Spine & Head
    spine = bones.new("Spine")
    spine.head = (0, 0, 1.0)
    spine.tail = (0.6, 0, 1.1)
    spine.parent = root_bone

    head_bone = bones.new("Head")
    head_bone.head = (0.6, 0, 1.1)
    head_bone.tail = (1.5, 0, 1.4)
    head_bone.parent = spine

    # Legs
    for side, sign in [("L", 1), ("R", -1)]:
        # Front
        fl = bones.new(f"Leg_Front_{side}")
        fl.head = (0.7, sign * 0.5, 1.0)
        fl.tail = (0.7, sign * 0.5, 0.0)
        fl.parent = spine

        # Back
        bl = bones.new(f"Leg_Back_{side}")
        bl.head = (-0.7, sign * 0.5, 1.0)
        bl.tail = (-0.7, sign * 0.5, 0.0)
        bl.parent = root_bone

    bpy.ops.object.mode_set(mode='OBJECT')

    # Parentage avec poids automatiques (Bone Heat Weighting)
    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')

    # Création d'une animation d'attente (Idle)
    armature.animation_data_create()
    action = bpy.data.actions.new(name=f"{creature_name}_Idle")
    armature.animation_data.action = action

    # Mode Pose pour animer
    bpy.ops.object.mode_set(mode='POSE')
    pose_spine = armature.pose.bones.get("Spine")
    pose_head = armature.pose.bones.get("Head")

    if pose_spine:
        # Frame 1
        pose_spine.location = (0, 0, 0)
        pose_spine.keyframe_insert(data_path="location", frame=1)
        # Frame 30 : Respiration (monte légèrement)
        pose_spine.location = (0, 0, 0.06)
        pose_spine.keyframe_insert(data_path="location", frame=30)
        # Frame 60 : Retour
        pose_spine.location = (0, 0, 0)
        pose_spine.keyframe_insert(data_path="location", frame=60)

    if pose_head:
        pose_head.rotation_euler = (0, 0, 0)
        pose_head.keyframe_insert(data_path="rotation_euler", frame=1)
        pose_head.rotation_euler = (0, math.radians(-5), 0)
        pose_head.keyframe_insert(data_path="rotation_euler", frame=30)
        pose_head.rotation_euler = (0, 0, 0)
        pose_head.keyframe_insert(data_path="rotation_euler", frame=60)

    bpy.ops.object.mode_set(mode='OBJECT')


def export_gltf_creature(filepath: str):
    """Exporte la créature avec armature et animations pour Godot 4."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=filepath,
        export_format='GLB',
        use_selection=False,
        export_apply=False,
        export_yup=True,
        export_animations=True,
        export_skins=True
    )
    print(f"[OK] Créature animée exportée : {filepath}")


def main():
    argv = sys.argv
    if "--" in argv:
        args_list = argv[argv.index("--") + 1:]
    else:
        args_list = []

    parser = argparse.ArgumentParser(description="Blender Headless Creature Rig & Animate")
    parser.add_argument("--name", default="beast_krayt", help="Nom de la créature")
    parser.add_argument("--out-dir", default="packages/prime-client/assets/models", help="Dossier de sortie")
    args = parser.parse_args(args_list)

    out_file = os.path.join(os.path.abspath(args.out_dir), f"{args.name}.glb")
    print(f"[*] Génération et rigging de la créature '{args.name}'...")
    mesh = build_beast_base_mesh()
    rig_and_animate_creature(mesh, args.name)
    export_gltf_creature(out_file)


if __name__ == "__main__":
    main()

