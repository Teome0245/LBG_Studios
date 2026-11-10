#!/usr/bin/env python3
"""
tools/asset_pipeline/blender_prop_builder.py
Générateur de props 3D procéduraux pour Godot 4 via l'API headless de Blender (`bpy`).

Exemples d'utilisation :
    blender -b -P tools/asset_pipeline/blender_prop_builder.py -- --prop crate
    blender -b -P tools/asset_pipeline/blender_prop_builder.py -- --all
"""

import sys
import os
import argparse
import math

try:
    import bpy
    import bmesh
except ImportError:
    print("Ce script doit être exécuté par Blender en mode headless:")
    print("blender -b -P tools/asset_pipeline/blender_prop_builder.py -- [options]")
    sys.exit(1)


def clean_scene():
    """Supprime tous les objets de la scène par défaut."""
    bpy.ops.wm.read_factory_settings(use_empty=True)


def create_pbr_material(name: str, color=(0.8, 0.8, 0.8, 1.0), metallic=0.0, roughness=0.5, emission=(0.0, 0.0, 0.0, 1.0), emission_strength=0.0):
    """Crée un matériau Principled BSDF compatible glTF / Godot 4."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        if "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = color
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = metallic
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = roughness
        if emission_strength > 0:
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = emission
            elif "Emission" in bsdf.inputs:
                bsdf.inputs["Emission"].default_value = emission
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def build_sci_fi_crate():
    """Génère une caisse modulaire Sci-Fi avec panneaux, biseaux et collision."""
    clean_scene()
    
    # 1. Matériaux
    mat_body = create_pbr_material("Mat_CrateBody", color=(0.25, 0.28, 0.32, 1.0), metallic=0.8, roughness=0.35)
    mat_trim = create_pbr_material("Mat_CrateTrim", color=(0.85, 0.55, 0.1, 1.0), metallic=0.5, roughness=0.4)
    mat_glow = create_pbr_material("Mat_CrateGlow", color=(0.1, 0.9, 1.0, 1.0), emission=(0.1, 0.9, 1.0, 1.0), emission_strength=3.0)

    # 2. Corps principal
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.5))
    crate = bpy.context.active_object
    crate.name = "SciFiCrate"
    crate.data.materials.append(mat_body)
    crate.data.materials.append(mat_trim)
    crate.data.materials.append(mat_glow)

    # Bevel modifier pour le réalisme des arêtes
    bev = crate.modifiers.new(name="Bevel", type='BEVEL')
    bev.width = 0.04
    bev.segments = 2
    bpy.ops.object.modifier_apply(modifier="Bevel")

    # 3. Détails en relief (Bandes métalliques de renfort)
    bpy.ops.mesh.primitive_cube_add(size=1.02, location=(0, 0, 0.5))
    trim = bpy.context.active_object
    trim.name = "CrateTrim"
    trim.scale = (1.02, 1.02, 0.2)
    trim.data.materials.append(mat_trim)
    bpy.ops.object.transform_apply(scale=True)

    # 4. Indicateur lumineux LED
    bpy.ops.mesh.primitive_cylinder_add(radius=0.08, depth=0.04, location=(0, 0.52, 0.5))
    glow_led = bpy.context.active_object
    glow_led.name = "CrateLED"
    glow_led.rotation_euler = (math.radians(90), 0, 0)
    glow_led.data.materials.append(mat_glow)

    # Joindre les objets visibles
    bpy.ops.object.select_all(action='DESELECT')
    crate.select_set(True)
    trim.select_set(True)
    glow_led.select_set(True)
    bpy.context.view_layer.objects.active = crate
    bpy.ops.object.join()

    # 5. Forme de Collision Godot automatique : suffixe -col pour StaticBody3D avec ConvexShape3D
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.5))
    col = bpy.context.active_object
    col.name = "SciFiCrate-col"


def build_modular_pillar():
    """Génère un pilier architectural modulaire (base, fût hexagonal, chapiteau)."""
    clean_scene()
    
    mat_stone = create_pbr_material("Mat_PillarStone", color=(0.6, 0.62, 0.65, 1.0), metallic=0.1, roughness=0.7)
    mat_energy = create_pbr_material("Mat_PillarRune", color=(0.9, 0.2, 0.9, 1.0), emission=(0.9, 0.2, 0.9, 1.0), emission_strength=4.0)

    # Base carrée
    bpy.ops.mesh.primitive_cube_add(size=1.2, location=(0, 0, 0.2))
    base = bpy.context.active_object
    base.name = "ModularPillar"
    base.scale = (1.0, 1.0, 0.3)
    base.data.materials.append(mat_stone)

    # Fût hexagonal (6 côtés)
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.45, depth=2.8, location=(0, 0, 1.7))
    shaft = bpy.context.active_object
    shaft.data.materials.append(mat_stone)

    # Anneau runique lumineux
    bpy.ops.mesh.primitive_torus_add(major_radius=0.48, minor_radius=0.05, location=(0, 0, 1.7))
    rune = bpy.context.active_object
    rune.data.materials.append(mat_energy)

    # Chapiteau sommital
    bpy.ops.mesh.primitive_cube_add(size=1.1, location=(0, 0, 3.2))
    top = bpy.context.active_object
    top.scale = (1.0, 1.0, 0.25)
    top.data.materials.append(mat_stone)

    # Union des parties
    bpy.ops.object.select_all(action='DESELECT')
    base.select_set(True)
    shaft.select_set(True)
    rune.select_set(True)
    top.select_set(True)
    bpy.context.view_layer.objects.active = base
    bpy.ops.object.join()

    # Forme de collision (Cylindre englobant -col)
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.6, depth=3.4, location=(0, 0, 1.7))
    col = bpy.context.active_object
    col.name = "ModularPillar-col"


def build_terminal_console():
    """Génère un terminal / console d'interaction MMO."""
    clean_scene()
    
    mat_metal = create_pbr_material("Mat_ConsoleBase", color=(0.15, 0.17, 0.2, 1.0), metallic=0.9, roughness=0.25)
    mat_screen = create_pbr_material("Mat_ConsoleScreen", color=(0.0, 0.85, 0.7, 1.0), emission=(0.0, 0.85, 0.7, 1.0), emission_strength=2.5)

    # Socle
    bpy.ops.mesh.primitive_cube_add(size=0.6, location=(0, 0, 0.45))
    socle = bpy.context.active_object
    socle.name = "TerminalConsole"
    socle.scale = (1.0, 0.7, 1.5)
    socle.data.materials.append(mat_metal)

    # Écran incliné
    bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 0.05, 0.95))
    screen = bpy.context.active_object
    screen.scale = (0.9, 0.6, 0.08)
    screen.rotation_euler = (math.radians(-35), 0, 0)
    screen.data.materials.append(mat_screen)

    # Assemblage
    bpy.ops.object.select_all(action='DESELECT')
    socle.select_set(True)
    screen.select_set(True)
    bpy.context.view_layer.objects.active = socle
    bpy.ops.object.join()

    # Collision
    bpy.ops.mesh.primitive_cube_add(size=0.7, location=(0, 0, 0.55))
    col = bpy.context.active_object
    col.name = "TerminalConsole-col"
    col.scale = (1.0, 0.8, 1.6)


def export_gltf(filepath: str):
    """Exporte la scène en format glTF binaire (.glb) optimisé pour Godot 4."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=filepath,
        export_format='GLB',
        use_selection=False,
        export_apply=True,
        export_yup=True
    )
    print(f"[OK] Exporté avec succès : {filepath}")


def main():
    # Découper les arguments passés après '--'
    argv = sys.argv
    if "--" in argv:
        args_idx = argv.index("--") + 1
        args_list = argv[args_idx:]
    else:
        args_list = []

    parser = argparse.ArgumentParser(description="Blender Headless Prop Builder pour LBG Studios")
    parser.add_argument("--prop", choices=["crate", "pillar", "terminal"], default=None, help="Type de prop à générer")
    parser.add_argument("--all", action="store_true", help="Générer tous les props d'un coup")
    parser.add_argument("--out-dir", default="packages/prime-client/assets/models", help="Dossier de sortie")
    args = parser.parse_args(args_list)

    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)

    builders = {
        "crate": ("sci_fi_crate.glb", build_sci_fi_crate),
        "pillar": ("modular_pillar.glb", build_modular_pillar),
        "terminal": ("terminal_console.glb", build_terminal_console),
    }

    targets = list(builders.keys()) if args.all or not args.prop else [args.prop]

    for name in targets:
        filename, build_func = builders[name]
        filepath = os.path.join(out_dir, filename)
        print(f"[*] Construction de '{name}'...")
        build_func()
        export_gltf(filepath)


if __name__ == "__main__":
    main()

