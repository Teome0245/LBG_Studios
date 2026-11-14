import struct
import math
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.swg_quat_decoder import QuatExpand

def parse_swg_ans(filepath):
    with open(filepath, "rb") as f:
        data = f.read()

    pos = 0
    total_len = len(data)

    info = {}
    bones = []
    qchn_list = [] # list of lists of uint32
    chnl_list = [] # list of lists of float
    srot_list = [] # static rotations: list of (formats, uint32)
    strn_list = [] # static translations: list of float

    decoder = QuatExpand()

    def read_chunk(offset):
        if offset + 8 > total_len: return None
        tag = data[offset:offset+4].decode("latin1", "ignore")
        size = struct.unpack(">I", data[offset+4:offset+8])[0]
        cdata = data[offset+8:offset+8+size]
        next_off = offset + 8 + size
        if next_off % 2 != 0: next_off += 1
        return tag, size, cdata, next_off

    # Walk IFF recursively or by linear token search
    def parse_iff(buffer, base_offset=0):
        p = 0
        buf_len = len(buffer)
        while p + 8 <= buf_len:
            tag = buffer[p:p+4].decode("latin1", "ignore")
            sz = struct.unpack(">I", buffer[p+4:p+8])[0]
            cdata = buffer[p+8:p+8+sz]
            next_p = p + 8 + sz
            if next_p % 2 != 0: next_p += 1

            if tag in ["FORM", "LIST"]:
                subtype = cdata[:4].decode("latin1", "ignore")
                parse_iff(cdata[4:], base_offset + p + 12)
            else:
                handle_leaf(tag, cdata)
            p = next_p

    def handle_leaf(tag, cdata):
        nonlocal info, bones, qchn_list, chnl_list, srot_list, strn_list
        if tag == "INFO":
            fps, frames, xfrm_c, rot_c, srot_c, trn_c, strn_c = struct.unpack("<fHHHHHH", cdata[:16])
            info = {
                "fps": fps,
                "frames": frames,
                "transform_count": xfrm_c,
                "rot_channels": rot_c,
                "srot_count": srot_c,
                "trn_channels": trn_c,
                "strn_count": strn_c
            }
        elif tag in ["XFIN", "FIN\x00", "FIN "]:
            # Multiple bone entries can be inside XFRM
            bp = 0
            while bp < len(cdata):
                null_pos = cdata.find(b"\x00", bp)
                if null_pos == -1 or null_pos + 11 > len(cdata): break
                bname = cdata[bp:null_pos].decode("latin1", "ignore")
                rest = cdata[null_pos+1:null_pos+11]
                has_rot, rot_idx, trn_mask, x_trn, y_trn, z_trn = struct.unpack("<BHBHHH", rest)
                bones.append({
                    "name": bname.lower(),
                    "has_rot": has_rot == 1,
                    "rot_idx": rot_idx,
                    "trn_mask": trn_mask,
                    "has_x_trn": bool(trn_mask & 0x08),
                    "has_y_trn": bool(trn_mask & 0x10),
                    "has_z_trn": bool(trn_mask & 0x20),
                    "x_trn_idx": x_trn,
                    "y_trn_idx": y_trn,
                    "z_trn_idx": z_trn
                })
                bp = null_pos + 11
        elif tag in ["QCHN", "CHN\x00", "CHN "]:
            # Rotations compressed channel
            # First 2 bytes = key_count (uint16)
            # Next 3 bytes = x_format, y_format, z_format (uint8)
            # Then loop key_count: frame_num (uint16), packed_val (uint32)
            cp = 0
            while cp + 5 <= len(cdata):
                key_count = struct.unpack("<H", cdata[cp:cp+2])[0]
                xf, yf, zf = struct.unpack("<BBB", cdata[cp+2:cp+5])
                cp += 5
                frames_data = {}
                for _ in range(key_count):
                    if cp + 6 > len(cdata): break
                    fnum, packed = struct.unpack("<HI", cdata[cp:cp+6])
                    cp += 6
                    frames_data[fnum] = decoder.decode_quaternion(packed, xf, yf, zf)
                qchn_list.append(frames_data)
        elif tag == "SROT":
            # Static rotations: format (3 bytes) + uint32 (4 bytes) = 7 bytes per entry
            sp = 0
            while sp + 7 <= len(cdata):
                xf, yf, zf, packed = struct.unpack("<BBBI", cdata[sp:sp+7])
                sp += 7
                quat = decoder.decode_quaternion(packed, xf, yf, zf)
                srot_list.append(quat)
        elif tag in ["CHNL", "LOCT"]:
            # Translations: key_count (uint16), then (frame_num uint16, val float)
            tp = 0
            while tp + 2 <= len(cdata):
                kcount = struct.unpack("<H", cdata[tp:tp+2])[0]
                tp += 2
                trn_frames = {}
                for _ in range(kcount):
                    if tp + 6 > len(cdata): break
                    fnum, val = struct.unpack("<Hf", cdata[tp:tp+6])
                    tp += 6
                    trn_frames[fnum] = val
                chnl_list.append(trn_frames)

    parse_iff(data)
    print(f"Parsed {filepath}:")
    print(f"  Info: {info}")
    print(f"  Bones declared: {len(bones)}")
    print(f"  Rotation channels: {len(qchn_list)}")
    print(f"  Static rotations: {len(srot_list)}")
    print(f"  Translation channels: {len(chnl_list)}")
    return info, bones, qchn_list, srot_list, chnl_list

if __name__ == "__main__":
    parse_swg_ans("tools/swg_extracted/all_b_dnc_goofy_sp_moonwalk.ans")
