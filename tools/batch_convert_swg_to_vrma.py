#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convertisseur Batch Universel SWG -> VRM Animation 1.0 (.vrma).
Intègre le décodeur QuatExpand SOE et la cinématique anatomique pour VRM 1.0.
"""

import os
import sys
import struct
import math
import json
import re
import glob

# --- 1. DÉCODEUR QUATERNION SOE COMPRESSÉ 32-BIT ---
class QuatExpand:
    def __init__(self):
        format_ids = [0xFE, 0xFC, 0xF8, 0xF0, 0xE0, 0xC0, 0x80]
        self.s_formatData = {}
        for shift in range(7):
            fid = format_ids[shift]
            base_count = 1 << shift
            base_sep = 2.0 / float(base_count + 1)
            half_range = 0.5 * (4.0 / float(base_count + 1))
            expand11 = half_range / 1023.0
            expand10 = half_range / 511.0
            for i in range(base_count):
                fidx = fid | i
                base_val = -1.0 + (i + 1) * base_sep
                self.s_formatData[fidx] = (base_val, expand11, expand10)

    def expand_11bit(self, val, fmt):
        base_val, expand11, _ = self.s_formatData.get(fmt, (0.0, 0.0, 0.0))
        sign = (val & 0x0400) != 0
        v = val & 0x03FF
        return base_val - (float(v) * expand11) if sign else base_val + (float(v) * expand11)

    def expand_10bit(self, val, fmt):
        base_val, _, expand10 = self.s_formatData.get(fmt, (0.0, 0.0, 0.0))
        sign = (val & 0x0200) != 0
        v = val & 0x01FF
        return base_val - (float(v) * expand10) if sign else base_val + (float(v) * expand10)

    def decode_quaternion(self, packed_val, x_fmt, y_fmt, z_fmt):
        val_x = (packed_val >> 21) & 0x07FF
        val_y = (packed_val >> 10) & 0x07FF
        val_z = packed_val & 0x03FF
        
        x = self.expand_11bit(val_x, x_fmt)
        y = self.expand_11bit(val_y, y_fmt)
        z = self.expand_10bit(val_z, z_fmt)
        
        len_sq = x*x + y*y + z*z
        w = math.sqrt(max(0.0, 1.0 - len_sq))
        return (x, y, z, w)

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

def quat_mult(q1, q2):
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

# Base de posture scénique fluide pour les membres supérieurs (T-Pose -> Dance Pose)
Q_DANCE_LEFT_UPPER_ARM = (0.024804, -0.248338, -0.383467, 0.889194)
Q_DANCE_RIGHT_UPPER_ARM = (0.024804, 0.248338, 0.383467, 0.889194)

def parse_swg_animation(ans_path):
    with open(ans_path, "rb") as f:
        data = f.read()

    info_idx = data.find(b"0001INFO")
    if info_idx != -1:
        info_data = data[info_idx+12:info_idx+28]
    else:
        info_idx = data.find(b"INFO")
        if info_idx == -1: return None
        info_data = data[info_idx+8:info_idx+24]
        
    fps, frame_count, xfrm_count, rot_c, srot_c, trn_c, strn_c = struct.unpack("<fHHHHHH", info_data)

    idx_xfrm = data.find(b"XFRM")
    idx_arot = data.find(b"AROT")
    if idx_xfrm == -1 or idx_arot == -1: return None
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

    decoder = QuatExpand()
    rot_channels = []
    pos = idx_arot
    while True:
        qchn_idx = data.find(b"QCHN", pos)
        if qchn_idx == -1 or qchn_idx >= len(data): break
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

    return fps, frame_count, bones, rot_channels

def build_vrma(fps, frame_count, bones, rot_channels, output_path, anim_name="swg_dance"):
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
        "componentType": 5126,
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

        frame_dict = {fnum: quat for fnum, quat in frames}
        last_quat = (0.0, 0.0, 0.0, 1.0)
        quat_list = []
        for f in range(frame_count):
            if f in frame_dict:
                last_quat = frame_dict[f]
            
            raw_q = (last_quat[0], last_quat[1], last_quat[2], last_quat[3])
            
            if vrm_bname == "leftUpperArm":
                adj_q = quat_normalize(quat_mult(Q_DANCE_LEFT_UPPER_ARM, (raw_q[0]*0.25, raw_q[1]*0.25, raw_q[2]*0.25, raw_q[3])))
            elif vrm_bname == "rightUpperArm":
                adj_q = quat_normalize(quat_mult(Q_DANCE_RIGHT_UPPER_ARM, (raw_q[0]*0.25, raw_q[1]*0.25, raw_q[2]*0.25, raw_q[3])))
            elif vrm_bname == "leftLowerArm":
                w_clamped = max(-1.0, min(1.0, raw_q[3]))
                theta = 2.0 * math.acos(abs(w_clamped))
                adj_q = (0.0, 0.0, math.sin(theta / 2.0), math.cos(theta / 2.0))
            elif vrm_bname == "rightLowerArm":
                w_clamped = max(-1.0, min(1.0, raw_q[3]))
                theta = 2.0 * math.acos(abs(w_clamped))
                adj_q = (0.0, 0.0, math.sin(-theta / 2.0), math.cos(theta / 2.0))
            elif vrm_bname in ["leftHand", "rightHand"]:
                adj_q = (0.0, 0.0, 0.0, 1.0)
            else:
                adj_q = raw_q
                
            quat_list.append(adj_q)

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
            "componentType": 5126,
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
        "asset": {"version": "2.0", "generator": "LBG Studios SWG to VRMA Batch v2.0"},
        "extensionsUsed": ["VRMC_vrm_animation"],
        "extensions": {
            "VRMC_vrm_animation": {
                "specVersion": "1.0",
                "humanoid": {"humanBones": human_bones}
            }
        },
        "scene": 0,
        "scenes": [{"nodes": list(range(len(nodes)))}],
        "nodes": nodes,
        "animations": [{
            "name": anim_name,
            "channels": channels,
            "samplers": samplers
        }],
        "buffers": [{"byteLength": len(binary_payload)}],
        "bufferViews": buffer_views,
        "accessors": accessors
    }

    json_str = json.dumps(gltf, separators=(",", ":"))
    json_bytes = json_str.encode("utf-8")
    while len(json_bytes) % 4 != 0: json_bytes += b" "

    total_length = 12 + 8 + len(json_bytes) + 8 + len(binary_payload)
    with open(output_path, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, total_length))
        f.write(struct.pack("<I4s", len(json_bytes), b"JSON"))
        f.write(json_bytes)
        f.write(struct.pack("<I4s", len(binary_payload), b"BIN\x00"))
        f.write(binary_payload)

    print(f"  [+] Converti : {os.path.basename(output_path)} ({total_length/1024:.1f} Ko, {duration:.1f}s)")
    return True

def batch_convert(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    ans_files = glob.glob(os.path.join(input_dir, "*.ans"))
    print(f"Batch conversion: {len(ans_files)} animations trouvées dans {input_dir}")
    
    converted = 0
    for ans_path in ans_files:
        bname = os.path.basename(ans_path).replace(".ans", "")
        clean_name = "swg_" + bname.replace("all_b_dnc_", "").replace("all_m_dnc_m_", "").replace("all_f_dnc_f_", "")
        out_vrma = os.path.join(output_dir, clean_name + ".vrma")
        
        parsed = parse_swg_animation(ans_path)
        if not parsed: continue
        fps, frame_count, bones, rot_channels = parsed
        if build_vrma(fps, frame_count, bones, rot_channels, out_vrma, anim_name=clean_name):
            converted += 1

    print(f"Batch terminé: {converted}/{len(ans_files)} animations converties en .vrma dans {output_dir}")

if __name__ == "__main__":
    in_d = sys.argv[1] if len(sys.argv) > 1 else "tools/swg_extracted"
    out_d = sys.argv[2] if len(sys.argv) > 2 else "packages/compagnon-desktop/overlay/vrm/animations"
    batch_convert(in_d, out_d)
