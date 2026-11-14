#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extrait l'animation cuite par Blender sur l'armature de Lia et la transforme
en un fichier VRMA 1.0 standard (VRMC_vrm_animation).
"""

import struct
import json
import os

LIA_TO_VRM_BONES = {
    "J_Bip_C_Hips": "hips",
    "J_Bip_C_Spine": "spine",
    "J_Bip_C_Chest": "chest",
    "J_Bip_C_UpperChest": "upperChest",
    "J_Bip_C_Neck": "neck",
    "J_Bip_C_Head": "head",
    "J_Bip_L_Shoulder": "leftShoulder",
    "J_Bip_L_UpperArm": "leftUpperArm",
    "J_Bip_L_LowerArm": "leftLowerArm",
    "J_Bip_L_Hand": "leftHand",
    "J_Bip_R_Shoulder": "rightShoulder",
    "J_Bip_R_UpperArm": "rightUpperArm",
    "J_Bip_R_LowerArm": "rightLowerArm",
    "J_Bip_R_Hand": "rightHand",
    "J_Bip_L_UpperLeg": "leftUpperLeg",
    "J_Bip_L_LowerLeg": "leftLowerLeg",
    "J_Bip_L_Foot": "leftFoot",
    "J_Bip_L_ToeBase": "leftToes",
    "J_Bip_R_UpperLeg": "rightUpperLeg",
    "J_Bip_R_LowerLeg": "rightLowerLeg",
    "J_Bip_R_Foot": "rightFoot",
    "J_Bip_R_ToeBase": "rightToes",
}

def extract_vrma(glb_path, output_vrma_path):
    with open(glb_path, "rb") as f:
        data = f.read()

    json_len = struct.unpack("<I", data[12:16])[0]
    gltf = json.loads(data[20:20+json_len].decode("utf-8"))
    bin_chunk_start = 20 + json_len + 8
    bin_chunk = data[bin_chunk_start:]

    # Sélectionner la première animation valide avec le plus de canaux
    best_anim = max(gltf["animations"], key=lambda a: len(a["channels"]))
    print(f"Extracted animation: {best_anim.get('name')} with {len(best_anim['channels'])} channels")

    nodes = gltf["nodes"]
    
    # Identifier les canaux qui ciblent nos os humanoïdes
    vrma_nodes = []
    vrma_human_bones = {}
    vrma_channels = []
    vrma_samplers = []
    vrma_accessors = []
    vrma_bufferviews = []
    new_bin_payload = bytearray()

    node_map = {} # lia_bone_name -> new_node_idx

    for ch in best_anim["channels"]:
        target = ch["target"]
        node_id = target["node"]
        bone_name = nodes[node_id].get("name", "")
        vrm_bone = LIA_TO_VRM_BONES.get(bone_name)
        
        if vrm_bone and target["path"] == "rotation":
            if vrm_bone not in node_map:
                new_idx = len(vrma_nodes)
                vrma_nodes.append({"name": vrm_bone})
                vrma_human_bones[vrm_bone] = {"node": new_idx}
                node_map[vrm_bone] = new_idx
            
            curr_node_idx = node_map[vrm_bone]
            sampler = best_anim["samplers"][ch["sampler"]]
            
            # Copier l'accessor d'input (timestamps)
            in_acc = gltf["accessors"][sampler["input"]]
            in_bv = gltf["bufferViews"][in_acc["bufferView"]]
            in_bytes = bin_chunk[in_bv["byteOffset"] : in_bv["byteOffset"] + in_bv["byteLength"]]
            
            in_offset = len(new_bin_payload)
            new_bin_payload.extend(in_bytes)
            while len(new_bin_payload) % 4 != 0: new_bin_payload.append(0)
            
            new_in_bv = len(vrma_bufferviews)
            vrma_bufferviews.append({"buffer": 0, "byteOffset": in_offset, "byteLength": len(in_bytes)})
            new_in_acc = len(vrma_accessors)
            vrma_accessors.append({
                "bufferView": new_in_bv,
                "byteOffset": 0,
                "componentType": in_acc["componentType"],
                "count": in_acc["count"],
                "type": in_acc["type"],
                "min": in_acc.get("min"),
                "max": in_acc.get("max")
            })

            # Copier l'accessor d'output (quaternions)
            out_acc = gltf["accessors"][sampler["output"]]
            out_bv = gltf["bufferViews"][out_acc["bufferView"]]
            out_bytes = bin_chunk[out_bv["byteOffset"] : out_bv["byteOffset"] + out_bv["byteLength"]]
            
            out_offset = len(new_bin_payload)
            new_bin_payload.extend(out_bytes)
            while len(new_bin_payload) % 4 != 0: new_bin_payload.append(0)
            
            new_out_bv = len(vrma_bufferviews)
            vrma_bufferviews.append({"buffer": 0, "byteOffset": out_offset, "byteLength": len(out_bytes)})
            new_out_acc = len(vrma_accessors)
            vrma_accessors.append({
                "bufferView": new_out_bv,
                "byteOffset": 0,
                "componentType": out_acc["componentType"],
                "count": out_acc["count"],
                "type": out_acc["type"]
            })

            new_samp_idx = len(vrma_samplers)
            vrma_samplers.append({
                "input": new_in_acc,
                "output": new_out_acc,
                "interpolation": sampler.get("interpolation", "LINEAR")
            })

            vrma_channels.append({
                "sampler": new_samp_idx,
                "target": {
                    "node": curr_node_idx,
                    "path": "rotation"
                }
            })

    out_gltf = {
        "asset": {"version": "2.0", "generator": "LBG Studios Blender Retargeted VRMA v1.0"},
        "extensionsUsed": ["VRMC_vrm_animation"],
        "extensions": {"VRMC_vrm_animation": {"specVersion": "1.0", "humanoid": {"humanBones": vrma_human_bones}}},
        "scene": 0,
        "scenes": [{"nodes": list(range(len(vrma_nodes)))}],
        "nodes": vrma_nodes,
        "animations": [{
            "name": "swg_moonwalk_blender",
            "channels": vrma_channels,
            "samplers": vrma_samplers
        }],
        "buffers": [{"byteLength": len(new_bin_payload)}],
        "bufferViews": vrma_bufferviews,
        "accessors": vrma_accessors
    }

    json_str = json.dumps(out_gltf, separators=(",", ":"))
    json_bytes = json_str.encode("utf-8")
    while len(json_bytes) % 4 != 0: json_bytes += b" "

    total_len = 12 + 8 + len(json_bytes) + 8 + len(new_bin_payload)

    with open(output_vrma_path, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, total_len))
        f.write(struct.pack("<I4s", len(json_bytes), b"JSON"))
        f.write(json_bytes)
        f.write(struct.pack("<I4s", len(new_bin_payload), b"BIN\x00"))
        f.write(new_bin_payload)

    print(f"✦ [SUCCESS] VRMA retargeté généré : {output_vrma_path} ({total_len/1024:.1f} Ko, {len(vrma_human_bones)} os)")

if __name__ == "__main__":
    extract_vrma(
        "packages/compagnon-desktop/overlay/vrm/animations/swg_moonwalk_baked.glb",
        "packages/compagnon-desktop/overlay/vrm/animations/swg_moonwalk.vrma"
    )
