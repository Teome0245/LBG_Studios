#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convertisseur d'animation SWG (.ans) vers VRM Animation 1.0 (.vrma / glTF 2.0).
Décode les quaternions compressés 32 bits de Sony Online Entertainment et
génère un fichier .vrma universel prêt pour Three.js / VRM / Godot 4.
"""

import os
import sys
import struct
import math
import json
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.swg_quat_decoder import QuatExpand

SWG_TO_VRM_BONES = {
    "root": "hips",
    "pelvis": "hips",
    "spine1": "spine",
    "spine2": "chest",
    "spine3": "upperChest",
    "neck": "neck",
    "head": "head",
    "lclav": "leftShoulder",
    "larm": "leftUpperArm",
    "lforearm": "leftLowerArm",
    "lwrist": "leftHand",
    "rclav": "rightShoulder",
    "rarm": "rightUpperArm",
    "rforearm": "rightLowerArm",
    "rwrist": "rightHand",
    "lthigh": "leftUpperLeg",
    "lshin": "leftLowerLeg",
    "lankle": "leftFoot",
    "ltoe": "leftToes",
    "rthigh": "rightUpperLeg",
    "rshin": "rightLowerLeg",
    "rankle": "rightFoot",
    "rtoe": "rightToes",
}

def parse_swg_animation(ans_path):
    with open(ans_path, "rb") as f:
        data = f.read()

    # 1. INFO
    info_idx = data.find(b"0001INFO")
    if info_idx != -1:
        info_data = data[info_idx+12:info_idx+28]
    else:
        info_idx = data.find(b"INFO")
        info_data = data[info_idx+8:info_idx+24]
        
    fps, frame_count, xfrm_count, rot_c, srot_c, trn_c, strn_c = struct.unpack("<fHHHHHH", info_data)
    print(f"Animation INFO: FPS={fps}, Frames={frame_count}, Bones={xfrm_count}, RotChannels={rot_c}")

    # 2. XFRM - Bone declarations
    idx_xfrm = data.find(b"XFRM")
    idx_arot = data.find(b"AROT")
    xfrm_slice = data[idx_xfrm:idx_arot]

    bones = []
    matches = list(re.finditer(rb"([a-zA-Z0-9_]{3,20})\x00", xfrm_slice))
    for m in matches:
        bname = m.group(1).decode("latin1").lower()
        if bname in ["xfrmxfin", "xfin", "fin"]: continue
        post = xfrm_slice[m.end():m.end()+10]
        if len(post) < 10: continue
        has_rot = post[0] == 1
        rot_idx = struct.unpack("<H", post[1:3])[0]
        trn_mask = post[3]
        bones.append({
            "name": bname,
            "has_rot": has_rot,
            "rot_idx": rot_idx,
            "trn_mask": trn_mask
        })

    # 3. AROT - Rotation channels
    decoder = QuatExpand()
    rot_channels = []

    pos = idx_arot
    while True:
        qchn_idx = data.find(b"QCHN", pos)
        if qchn_idx == -1 or qchn_idx >= len(data): break
        # read size of chunk
        csz = struct.unpack(">I", data[qchn_idx+4:qchn_idx+8])[0]
        cdata = data[qchn_idx+8:qchn_idx+8+csz]
        if len(cdata) >= 5:
            key_count = struct.unpack("<H", cdata[:2])[0]
            xf, yf, zf = struct.unpack("<BBB", cdata[2:5])
            frames = []
            cp = 5
            for _ in range(key_count):
                if cp + 6 > len(cdata): break
                fnum, packed = struct.unpack("<HI", cdata[cp:cp+6])
                cp += 6
                quat = decoder.decode_quaternion(packed, xf, yf, zf)
                frames.append((fnum, quat))
            rot_channels.append(frames)
        pos = qchn_idx + 8 + csz
        if len(rot_channels) >= rot_c: break

    print(f"Extracted {len(bones)} bones, {len(rot_channels)} rotation channels.")
    return fps, frame_count, bones, rot_channels

def quat_mult(q1, q2):
    """Multiplie deux quaternions (x, y, z, w)."""
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    return (
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2,
        w1*w2 - x1*x2 - y1*y2 - z1*z2
    )

def quat_normalize(q):
    x, y, z, w = q
    l = math.sqrt(x*x + y*y + z*z + w*w)
    if l > 0.00001:
        return (x/l, y/l, z/l, w/l)
    return (0.0, 0.0, 0.0, 1.0)

# Quaternions de posture de danse naturelle pour les bras (T-Pose -> Dance Pose)
# Descente le long du buste (50°), orientation vers l'avant (25°), légère ouverture (15°)
Q_DANCE_LEFT_UPPER_ARM = (0.024804, -0.248338, -0.383467, 0.889194)
Q_DANCE_RIGHT_UPPER_ARM = (0.024804, 0.248338, 0.383467, 0.889194)

def build_vrma(fps, frame_count, bones, rot_channels, output_path):
    """Construit un conteneur glTF 2.0 / VRMA binaire valide."""
    duration = float(frame_count) / fps
    timestamps = [float(f) / fps for f in range(frame_count)]
    time_bytes = struct.pack(f"<{len(timestamps)}f", *timestamps)

    # Identifier les os mappés vers VRM
    animated_vrm_bones = []
    for b in bones:
        vrm_name = SWG_TO_VRM_BONES.get(b["name"])
        if vrm_name and b["has_rot"] and b["rot_idx"] < len(rot_channels):
            animated_vrm_bones.append((b["name"], vrm_name, rot_channels[b["rot_idx"]]))

    print(f"Total bones animés mappés sur le rig VRM Humanoid: {len(animated_vrm_bones)}")

    nodes = []
    channels = []
    samplers = []
    human_bones = {}
    accessors = []
    buffer_views = []
    binary_payload = bytearray()

    # Accessor 0: Timestamps (partagé par tous les samplers)
    time_offset = len(binary_payload)
    binary_payload.extend(time_bytes)
    while len(binary_payload) % 4 != 0: binary_payload.append(0)

    buffer_views.append({
        "buffer": 0,
        "byteOffset": time_offset,
        "byteLength": len(time_bytes)
    })
    accessors.append({
        "bufferView": 0,
        "byteOffset": 0,
        "componentType": 5126, # FLOAT
        "count": len(timestamps),
        "type": "SCALAR",
        "min": [timestamps[0]],
        "max": [timestamps[-1]]
    })
    time_accessor_idx = 0

    for i, (swg_bname, vrm_bname, frames) in enumerate(animated_vrm_bones):
        node_idx = len(nodes)
        nodes.append({"name": vrm_bname})
        human_bones[vrm_bname] = {"node": node_idx}

        # Échantillonnage des quaternions sur toutes les frames
        frame_dict = {fnum: quat for fnum, quat in frames}
        last_quat = (0.0, 0.0, 0.0, 1.0)
        quat_list = []
        for f in range(frame_count):
            if f in frame_dict:
                last_quat = frame_dict[f]
            
            # Repère SOE -> glTF VRM
            raw_q = (last_quat[0], last_quat[1], last_quat[2], last_quat[3])
            
            # Traitement anatomique rigoureux pour les membres supérieurs
            if vrm_bname == "leftUpperArm":
                # Pose de danse vers l'avant + oscillation rythmique SWG
                adj_q = quat_normalize(quat_mult(Q_DANCE_LEFT_UPPER_ARM, (raw_q[0]*0.3, raw_q[1]*0.3, raw_q[2]*0.3, raw_q[3])))
            elif vrm_bname == "rightUpperArm":
                adj_q = quat_normalize(quat_mult(Q_DANCE_RIGHT_UPPER_ARM, (raw_q[0]*0.3, raw_q[1]*0.3, raw_q[2]*0.3, raw_q[3])))
            elif vrm_bname == "leftLowerArm":
                # Flexion dynamique du coude extraite de la piste SWG, projetée sur l'axe Z anatomique VRM
                w_clamped = max(-1.0, min(1.0, raw_q[3]))
                theta = 2.0 * math.acos(abs(w_clamped))
                # Plier vers l'avant au rythme de l'animation
                sin_t = math.sin(theta / 2.0)
                cos_t = math.cos(theta / 2.0)
                adj_q = (0.0, 0.0, sin_t, cos_t)
            elif vrm_bname == "rightLowerArm":
                w_clamped = max(-1.0, min(1.0, raw_q[3]))
                theta = 2.0 * math.acos(abs(w_clamped))
                sin_t = math.sin(-theta / 2.0)
                cos_t = math.cos(theta / 2.0)
                adj_q = (0.0, 0.0, sin_t, cos_t)
            elif vrm_bname in ["leftHand", "rightHand"]:
                adj_q = (0.0, 0.0, 0.0, 1.0)
            else:
                # Tronc, tête et jambes : animation SWG 100% officielle intacte
                adj_q = raw_q
                
            quat_list.append(adj_q)

        # Quaternions (x, y, z, w)
        quat_bytes = bytearray()
        for qx, qy, qz, qw in quat_list:
            quat_bytes.extend(struct.pack("<4f", qx, qy, qz, qw))

        quat_offset = len(binary_payload)
        binary_payload.extend(quat_bytes)
        while len(binary_payload) % 4 != 0: binary_payload.append(0)

        bv_idx = len(buffer_views)
        buffer_views.append({
            "buffer": 0,
            "byteOffset": quat_offset,
            "byteLength": len(quat_bytes)
        })

        acc_idx = len(accessors)
        accessors.append({
            "bufferView": bv_idx,
            "byteOffset": 0,
            "componentType": 5126, # FLOAT
            "count": len(quat_list),
            "type": "VEC4"
        })

        sampler_idx = len(samplers)
        samplers.append({
            "input": time_accessor_idx,
            "output": acc_idx,
            "interpolation": "LINEAR"
        })

        channels.append({
            "sampler": sampler_idx,
            "target": {
                "node": node_idx,
                "path": "rotation"
            }
        })

    gltf = {
        "asset": {
            "version": "2.0",
            "generator": "LBG Studios SWG to VRMA Converter v1.0"
        },
        "extensionsUsed": ["VRMC_vrm_animation"],
        "extensions": {
            "VRMC_vrm_animation": {
                "specVersion": "1.0",
                "humanoid": {
                    "humanBones": human_bones
                }
            }
        },
        "scene": 0,
        "scenes": [{"nodes": list(range(len(nodes)))}],
        "nodes": nodes,
        "animations": [{
            "name": "swg_moonwalk",
            "channels": channels,
            "samplers": samplers
        }],
        "buffers": [{
            "byteLength": len(binary_payload)
        }],
        "bufferViews": buffer_views,
        "accessors": accessors
    }

    json_str = json.dumps(gltf, separators=(",", ":"))
    json_bytes = json_str.encode("utf-8")
    while len(json_bytes) % 4 != 0: json_bytes += b" "

    # glTF binary header: magic (4), version (4), length (4)
    # Chunk 0 (JSON): length (4), type (4) JSON (0x4E4F534A)
    # Chunk 1 (BIN): length (4), type (4) BIN (0x004E4942)
    total_length = 12 + 8 + len(json_bytes) + 8 + len(binary_payload)

    with open(output_path, "wb") as f:
        # Header
        f.write(struct.pack("<4sII", b"glTF", 2, total_length))
        # Chunk 0 JSON
        f.write(struct.pack("<I4s", len(json_bytes), b"JSON"))
        f.write(json_bytes)
        # Chunk 1 BIN
        f.write(struct.pack("<I4s", len(binary_payload), b"BIN\x00"))
        f.write(binary_payload)

    print(f"✦ [SUCCESS] VRMA généré avec succès : {output_path} ({total_length / 1024:.1f} Ko, {duration:.2f}s, {len(animated_vrm_bones)} os)")

if __name__ == "__main__":
    ans_file = "tools/swg_extracted/all_b_dnc_goofy_sp_moonwalk.ans"
    vrma_file = "packages/compagnon-desktop/overlay/vrm/animations/swg_moonwalk.vrma"
    fps, frame_count, bones, rot_channels = parse_swg_animation(ans_file)
    build_vrma(fps, frame_count, bones, rot_channels, vrma_file)
