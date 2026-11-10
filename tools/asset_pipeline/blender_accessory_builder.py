#!/usr/bin/env python3
"""
tools/asset_pipeline/blender_accessory_builder.py
Générateur d'accessoires 3D modulaires pour l'avatar VRM du Compagnon Desktop.
Génère des modèles .glb calibrés pour les os humanoïdes (head, leftHand, rightHand).

Usage :
    blender -b -P tools/asset_pipeline/blender_accessory_builder.py -- --all
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


def create_pbr_material(name: str, color=(0.1, 0.1, 0.1, 1.0), metallic=0.9, roughness=0.2, emission=(0, 0, 0, 1), emission_strength=0.0, alpha=1.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        if "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = color
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = metallic
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = roughness
        if alpha < 1.0 and "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = alpha
            mat.blend_method = 'BLEND'
        if emission_strength > 0:
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = emission
            elif "Emission" in bsdf.inputs:
                bsdf.inputs["Emission"].default_value = emission
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def build_cyber_visor():
    """Génère une visière HUD holographique cyberpunk à monter sur la tête (os 'head')."""
    clean_scene()

    mat_frame = create_pbr_material("Mat_VisorFrame", color=(0.05, 0.06, 0.08, 1.0), metallic=0.95, roughness=0.15)
    mat_hud = create_pbr_material("Mat_VisorGlass", color=(0.0, 0.9, 1.0, 0.75), emission=(0.0, 0.95, 1.0, 1.0), emission_strength=3.5, alpha=0.75)
    mat_accent = create_pbr_material("Mat_VisorGold", color=(0.95, 0.75, 0.15, 1.0), metallic=0.85, roughness=0.3)

    # 1. Écran de visière holographique incurvé devant les yeux
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.11, depth=0.035, location=(0, 0.05, 0.03))
    visor_glass = bpy.context.active_object
    visor_glass.name = "VisorGlass"
    visor_glass.scale = (1.0, 0.6, 0.7)
    visor_glass.rotation_euler = (math.radians(90), 0, 0)
    visor_glass.data.materials.append(mat_hud)

    # 2. Monture frontale fine au-dessus du verre
    bpy.ops.mesh.primitive_cube_add(size=0.015, location=(0, 0.09, 0.055))
    frame = bpy.context.active_object
    frame.name = "VisorFrame"
    frame.scale = (13.0, 1.2, 0.8)
    frame.data.materials.append(mat_frame)

    # 3. Branches latérales cybernétiques
    branches = []
    for side, sign in [("L", 1), ("R", -1)]:
        bpy.ops.mesh.primitive_cube_add(size=0.012, location=(sign * 0.10, -0.01, 0.045))
        b = bpy.context.active_object
        b.name = f"Branch_{side}"
        b.scale = (0.7, 9.0, 1.2)
        b.data.materials.append(mat_accent)
        branches.append(b)

    # Fusion des parties
    bpy.ops.object.select_all(action='DESELECT')
    visor_glass.select_set(True)
    frame.select_set(True)
    for b in branches:
        b.select_set(True)
    bpy.context.view_layer.objects.active = frame
    bpy.ops.object.join()
    frame.name = "CyberVisor"


def build_holo_datapad():
    """Génère un terminal datapad holographique pour la main (os 'leftHand' ou 'rightHand')."""
    clean_scene()

    mat_casing = create_pbr_material("Mat_PadCase", color=(0.12, 0.14, 0.18, 1.0), metallic=0.85, roughness=0.3)
    mat_screen = create_pbr_material("Mat_PadHolo", color=(0.1, 0.85, 0.65, 0.9), emission=(0.1, 0.85, 0.65, 1.0), emission_strength=4.0, alpha=0.9)
    mat_led = create_pbr_material("Mat_PadLed", color=(1.0, 0.2, 0.4, 1.0), emission=(1.0, 0.2, 0.4, 1.0), emission_strength=5.0)

    # 1. Châssis ergonomique ultra-plat
    bpy.ops.mesh.primitive_cube_add(size=0.18, location=(0, 0, 0))
    case = bpy.context.active_object
    case.name = "HoloDatapad"
    case.scale = (0.8, 1.3, 0.07)
    case.data.materials.append(mat_casing)

    # 2. Écran holographique flottant au-dessus du châssis
    bpy.ops.mesh.primitive_cube_add(size=0.16, location=(0, 0.01, 0.012))
    screen = bpy.context.active_object
    screen.name = "PadScreen"
    screen.scale = (0.72, 1.15, 0.02)
    screen.data.materials.append(mat_screen)

    # 3. Voyant LED de transmission
    bpy.ops.mesh.primitive_cylinder_add(radius=0.008, depth=0.01, location=(0.05, 0.10, 0.01))
    led = bpy.context.active_object
    led.name = "PadLED"
    led.data.materials.append(mat_led)

    # Fusion
    bpy.ops.object.select_all(action='DESELECT')
    case.select_set(True)
    screen.select_set(True)
    led.select_set(True)
    bpy.context.view_layer.objects.active = case
    bpy.ops.object.join()


def build_neural_headset():
    """Génère un casque neural de communication avec micro-antenne (os 'head')."""
    clean_scene()

    mat_chassis = create_pbr_material("Mat_HeadsetMetal", color=(0.2, 0.22, 0.25, 1.0), metallic=0.9, roughness=0.25)
    mat_ring = create_pbr_material("Mat_HeadsetGlow", color=(0.95, 0.1, 0.6, 1.0), emission=(0.95, 0.1, 0.6, 1.0), emission_strength=4.5)

    # Oreillette droite
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.035, depth=0.025, location=(0.09, -0.01, 0.02))
    ear = bpy.context.active_object
    ear.name = "NeuralHeadset"
    ear.rotation_euler = (0, math.radians(90), 0)
    ear.data.materials.append(mat_chassis)

    # Anneau néon sur l'écouteur
    bpy.ops.mesh.primitive_torus_add(major_radius=0.025, minor_radius=0.005, location=(0.105, -0.01, 0.02))
    ring = bpy.context.active_object
    ring.rotation_euler = (0, math.radians(90), 0)
    ring.data.materials.append(mat_ring)

    # Micro orienté vers la bouche
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.004, depth=0.09, location=(0.08, 0.05, -0.01))
    mic = bpy.context.active_object
    mic.rotation_euler = (math.radians(35), math.radians(20), 0)
    mic.data.materials.append(mat_chassis)

    # Fusion
    bpy.ops.object.select_all(action='DESELECT')
    ear.select_set(True)
    ring.select_set(True)
    mic.select_set(True)
    bpy.context.view_layer.objects.active = ear
    bpy.ops.object.join()


def export_gltf(filepath: str):
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=filepath,
        export_format='GLB',
        use_selection=False,
        export_apply=True,
        export_yup=True
    )
    print(f"[OK] Accessoire exporté : {filepath}")


def main():
    argv = sys.argv
    if "--" in argv:
        args_list = argv[argv.index("--") + 1:]
    else:
        args_list = []

    parser = argparse.ArgumentParser(description="Générateur d'accessoires VRM pour Compagnon Desktop")
    parser.add_argument("--item", choices=["visor", "datapad", "headset"], default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--out-dir", default="packages/compagnon-desktop/overlay/vrm/accessories")
    args = parser.parse_args(args_list)

    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)

    items = {
        "visor": ("cyber_visor.glb", build_cyber_visor),
        "datapad": ("holo_datapad.glb", build_holo_datapad),
        "headset": ("neural_headset.glb", build_neural_headset),
    }

    targets = list(items.keys()) if args.all or not args.item else [args.item]

    for key in targets:
        filename, build_fn = items[key]
        filepath = os.path.join(out_dir, filename)
        print(f"[*] Construction de l'accessoire '{key}'...")
        build_fn()
        export_gltf(filepath)


if __name__ == "__main__":
    main()

