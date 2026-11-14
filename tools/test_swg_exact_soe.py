#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de conversion SWG -> VRMA avec la formule exacte du moteur SOE :
Q = Q_post * Q_anim * Q_pre
"""

import os
import sys
import struct
import math
import json
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.swg_quat_decoder import QuatExpand
from tools.swg_to_vrma import SWG_TO_VRM_BONES

def quat_mult(q1, q2):
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    return (
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2,
        w1*w2 - x1*x2 - y1*y2 - z1*z2
    )

def quat_norm(q):
    x, y, z, w = q
    l = math.sqrt(x*x + y*y + z*z + w*w)
    if l > 0.00001:
        res = (x/l, y/l, z/l, w/l)
        return (-res[0], -res[1], -res[2], -res[3]) if res[3] < 0 else res
    return (0.0, 0.0, 0.0, 1.0)

def load_skt_rotations(skt_path):
    with open(skt_path, "rb") as f:
        data = f.read()
    idx_name = data.find(b"NAME")
    idx_prnt = data.find(b"PRNT")
    idx_rpre = data.find(b"RPRE")
    idx_rpst = data.find(b"RPST")
    names = [n.decode("latin1").lower() for n in data[idx_name+8:idx_prnt].split(b"\x00") if n]
    ct = len(names)
    skt_bones = {}
    for i in range(ct):
        # Format IFF SWG : w, x, y, z
        pw, px, py, pz = struct.unpack("<4f", data[idx_rpre+8+i*16:idx_rpre+8+(i+1)*16])
        qw, qx, qy, qz = struct.unpack("<4f", data[idx_rpst+8+i*16:idx_rpst+8+(i+1)*16])
        skt_bones[names[i]] = {
            "pre": (px, py, pz, pw),
            "post": (qx, qy, qz, qw)
        }
    return skt_bones

def convert_soe_to_vrma(ans_path, skt_path, output_vrma):
    from tools.swg_to_vrma import parse_swg_animation
    fps, frame_count, bones, rot_channels = parse_swg_animation(ans_path)
    skt_bones = load_skt_rotations(skt_path)
    
    duration = float(frame_count) / fps
    timestamps = [float(f) / fps for f in range(frame_count)]
    time_bytes = struct.pack(f"<{len(timestamps)}f", *timestamps)

    animated_vrm_bones = []
    for b in bones:
        vrm_name = SWG_TO_VRM_BONES.get(b["name"])
        if vrm_name and b["has_rot"] and b["rot_idx"] < len(rot_channels):
            animated_vrm_bones.append((b["name"], vrm_name, rot_channels[b["rot_idx"]]))

    nodes = []
    channels = []
    samplers = []
    human_bones = {}
    accessors = []
    buffer_views = []
    binary_payload = bytearray()

    # Time accessor
    time_offset = len(binary_payload)
    binary_payload.extend(time_bytes)
    while len(binary_payload) % 4 != 0: binary_payload.append(0)
    buffer_views.append({"buffer": 0, "byteOffset": time_offset, "byteLength": len(time_bytes)})
    accessors.append({"bufferView": 0, "byteOffset": 0, "componentType": 5126, "count": len(timestamps), "type": "SCALAR", "min": [timestamps[0]], "max": [timestamps[-1]]})
    time_acc_idx = 0

    for i, (swg_bname, vrm_bname, frames) in enumerate(animated_vrm_bones):
        node_idx = len(nodes)
        nodes.append({"name": vrm_bname})
        human_bones[vrm_bname] = {"node": node_idx}

        pre_q = skt_bones.get(swg_bname, {}).get("pre", (0.0, 0.0, 0.0, 1.0))
        post_q = skt_bones.get(swg_bname, {}).get("post", (0.0, 0.0, 0.0, 1.0))

        frame_dict = {fnum: quat for fnum, quat in frames}
        last_quat = (0.0, 0.0, 0.0, 1.0)
        quat_list = []
        for f in range(frame_count):
            if f in frame_dict:
                last_quat = frame_dict[f]
            # Formule exacte du moteur SOE : Q = Q_post * Q_anim * Q_pre
            q_comb = quat_norm(quat_mult(post_q, quat_mult(last_quat, pre_q)))
            quat_list.append(q_comb)

        quat_bytes = bytearray()
        for qx, qy, qz, qw in quat_list:
            quat_bytes.extend(struct.pack("<4f", qx, qy, qz, qw))

        q_offset = len(binary_payload)
        binary_payload.extend(quat_bytes)
        while len(binary_payload) % 4 != 0: binary_payload.append(0)

        bv_idx = len(buffer_views)
        buffer_views.append({"buffer": 0, "byteOffset": q_offset, "byteLength": len(quat_bytes)})
        acc_idx = len(accessors)
        accessors.append({"bufferView": bv_idx, "byteOffset": 0, "componentType": 5126, "count": len(quat_list), "type": "VEC4"})
        s_idx = len(samplers)
        samplers.append({"input": time_acc_idx, "output": acc_idx, "interpolation": "LINEAR"})
        channels.append({"sampler": s_idx, "target": {"node": node_idx, "path": "rotation"}})

    gltf = {
        "asset": {"version": "2.0", "generator": "LBG Studios SWG to VRMA SOE Engine v2.0"},
        "extensionsUsed": ["VRMC_vrm_animation"],
        "extensions": {"VRMC_vrm_animation": {"specVersion": "1.0", "humanoid": {"humanBones": human_bones}}},
        "scene": 0,
        "scenes": [{"nodes": list(range(len(nodes)))}],
        "nodes": nodes,
        "animations": [{"name": "swg_moonwalk_soe", "channels": channels, "samplers": samplers}],
        "buffers": [{"byteLength": len(binary_payload)}],
        "bufferViews": buffer_views,
        "accessors": accessors
    }

    json_bytes = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    while len(json_bytes) % 4 != 0: json_bytes += b" "
    total_len = 12 + 8 + len(json_bytes) + 8 + len(binary_payload)

    with open(output_vrma, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, total_len))
        f.write(struct.pack("<I4s", len(json_bytes), b"JSON"))
        f.write(json_bytes)
        f.write(struct.pack("<I4s", len(binary_payload), b"BIN\x00"))
        f.write(binary_payload)

    print(f"✦ [SOE ENGINE VRMA] Fichier généré : {output_vrma} ({total_len/1024:.1f} Ko, {duration:.2f}s)")

if __name__ == "__main__":
    ans = "tools/swg_extracted/all_b_dnc_goofy_sp_moonwalk.ans"
    skt = "tools/swg_extracted/all_b.skt"
    out = "packages/compagnon-desktop/overlay/vrm/animations/swg_moonwalk.vrma"
    convert_soe_to_vrma(ans, skt, out)

