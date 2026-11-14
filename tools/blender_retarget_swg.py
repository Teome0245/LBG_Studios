#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Retargeting cinématique universel SWG -> VRM Lia via Blender 5.2 LTS headless.
Utilise l'espace World pour faire correspondre rigoureusement les orientations de membres
sans aucun conflit d'axes locaux.
"""

import sys
import os
import bpy
import mathutils

sys.path.insert(0, '/tmp/swg_addon')
sys.path.insert(0, '/home/lbg/Projets/LBG_Studios')

from io_scene_swg import import_skt
from tools.swg_to_vrma import parse_swg_animation

SWG_TO_LIA_BONES = {
    "root": "J_Bip_C_Hips",
    "spine1": "J_Bip_C_Spine",
    "spine2": "J_Bip_C_Chest",
    "spine3": "J_Bip_C_UpperChest",
    "neck": "J_Bip_C_Neck",
    "head": "J_Bip_C_Head",
    "lclav": "J_Bip_L_Shoulder",
    "larm": "J_Bip_L_UpperArm",
    "lforearm": "J_Bip_L_LowerArm",
    "lwrist": "J_Bip_L_Hand",
    "rclav": "J_Bip_R_Shoulder",
    "rarm": "J_Bip_R_UpperArm",
    "rforearm": "J_Bip_R_LowerArm",
    "rwrist": "J_Bip_R_Hand",
    "lthigh": "J_Bip_L_UpperLeg",
    "lshin": "J_Bip_L_LowerLeg",
    "lankle": "J_Bip_L_Foot",
    "ltoe": "J_Bip_L_ToeBase",
    "rthigh": "J_Bip_R_UpperLeg",
    "rshin": "J_Bip_R_LowerLeg",
    "rankle": "J_Bip_R_Foot",
    "rtoe": "J_Bip_R_ToeBase",
}

def retarget_swg_to_vrm(ans_path, skt_path, lia_vrm_path, output_glb):
    # Nettoyer la scène Blender
    bpy.ops.wm.read_factory_settings(use_empty=True)

    print("✦ 1. Importation du squelette SWG...")
    import_skt.import_skt(bpy.context, os.path.abspath(skt_path), lod_0_only=True)
    swg_arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    swg_arm.name = "Armature_SWG"

    print("✦ 2. Parsing et injection des keyframes d'animation SWG...")
    fps, frame_count, bones, rot_channels = parse_swg_animation(ans_path)
    bpy.context.scene.render.fps = int(round(fps))
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = frame_count - 1

    bpy.context.view_layer.objects.active = swg_arm
    bpy.ops.object.mode_set(mode='POSE')

    # Animer chaque bone de SWG
    for b in bones:
        bname = b["name"]
        if b["has_rot"] and b["rot_idx"] < len(rot_channels):
            pbone = swg_arm.pose.bones.get(bname)
            if not pbone: continue
            
            pbone.rotation_mode = 'QUATERNION'
            frames = rot_channels[b["rot_idx"]]
            frame_dict = {fnum: quat for fnum, quat in frames}
            last_quat = (0.0, 0.0, 0.0, 1.0)
            
            for f in range(frame_count):
                if f in frame_dict:
                    last_quat = frame_dict[f]
                # Format mathutils.Quaternion: (w, x, y, z)
                # SWG quat raw decoder renvoie (x, y, z, w)
                qx, qy, qz, qw = last_quat
                pbone.rotation_quaternion = mathutils.Quaternion((qw, qx, qy, qz))
                pbone.keyframe_insert(data_path="rotation_quaternion", frame=f)

    print(f"✦ Animation appliquée sur Armature_SWG ({frame_count} frames @ {fps} FPS)")

    print("✦ 3. Importation du modèle & armature de Lia...")
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(lia_vrm_path))
    lia_arm = [o for o in bpy.data.objects if o.type == 'ARMATURE' and o != swg_arm][0]
    lia_arm.name = "Armature_Lia"

    print("✦ 4. Configuration des contraintes de retargeting cinématique (World Space)...")
    bpy.context.view_layer.objects.active = lia_arm
    bpy.ops.object.mode_set(mode='POSE')

    for swg_name, lia_name in SWG_TO_LIA_BONES.items():
        lia_pbone = lia_arm.pose.bones.get(lia_name)
        swg_pbone = swg_arm.pose.bones.get(swg_name)
        if lia_pbone and swg_pbone:
            c = lia_pbone.constraints.new('COPY_ROTATION')
            c.target = swg_arm
            c.subtarget = swg_name
            c.target_space = 'WORLD'
            c.owner_space = 'WORLD'

    print("✦ 5. Cuisson (Bake) cinématique de l'animation sur l'armature de Lia...")
    bpy.ops.nla.bake(
        frame_start=0,
        frame_end=frame_count - 1,
        only_selected=False,
        visual_keying=True,
        clear_constraints=True,
        bake_types={'POSE'}
    )

    print("✦ 6. Export glTF/GLB animé...")
    bpy.ops.object.mode_set(mode='OBJECT')
    # Garder uniquement Lia
    bpy.data.objects.remove(swg_arm, do_unlink=True)
    
    # Exporter en glTF binaire
    bpy.ops.export_scene.gltf(
        filepath=os.path.abspath(output_glb),
        export_format='GLB',
        export_animations=True,
        export_current_frame=False
    )
    print(f"✦ [SUCCESS] Animation retargetée avec succès : {output_glb}")

if __name__ == "__main__":
    ans = "tools/swg_extracted/all_b_dnc_goofy_sp_moonwalk.ans"
    skt = "tools/swg_extracted/all_b.skt"
    lia = "/tmp/compagnon.glb"
    out = "packages/compagnon-desktop/overlay/vrm/animations/swg_moonwalk_baked.glb"
    retarget_swg_to_vrm(ans, skt, lia, out)
