import struct

with open("tools/swg_extracted/all_b_dnc_goofy_sp_moonwalk.ans", "rb") as f:
    data = f.read()

# Locate FORM:CKAT -> FORM:0001 -> FORM:XFRM
pos = 0
xfrm_data = b""
while pos < len(data):
    tag = data[pos:pos+4]
    if pos + 8 > len(data): break
    sz = struct.unpack(">I", data[pos+4:pos+8])[0]
    if tag == b"FORM" and data[pos+8:pos+12] == b"CKAT":
        sub = data[pos+12:pos+8+sz]
        p2 = 0
        while p2 < len(sub):
            t2 = sub[p2:p2+4]
            sz2 = struct.unpack(">I", sub[p2+4:p2+8])[0]
            if t2 == b"FORM" and sub[p2+8:p2+12] == b"0001":
                sub3 = sub[p2+12:p2+8+sz2]
                p3 = 0
                while p3 < len(sub3):
                    t3 = sub3[p3:p3+4]
                    sz3 = struct.unpack(">I", sub3[p3+4:p3+8])[0]
                    if t3 == b"FORM" and sub3[p3+8:p3+12] == b"XFRM":
                        xfrm_data = sub3[p3+12:p3+8+sz3]
                        break
                    p3 += 8 + sz3
                    if p3 % 2 != 0: p3 += 1
                break
            p2 += 8 + sz2
            if p2 % 2 != 0: p2 += 1
        break
    pos += 8 + sz
    if pos % 2 != 0: pos += 1

print(f"XFRM chunk length: {len(xfrm_data)}")

p = 0
bones = []
while p < len(xfrm_data):
    c_tag = xfrm_data[p:p+4].decode("latin1", "ignore")
    c_sz = struct.unpack(">I", xfrm_data[p+4:p+8])[0]
    c_data = xfrm_data[p+8:p+8+c_sz]
    str_end = c_data.find(b"\x00")
    bname = c_data[:str_end].decode("latin1")
    rest = c_data[str_end+1:]
    has_rot, rot_idx, trn_mask, x_trn, y_trn, z_trn = struct.unpack("<BHBHHH", rest[:10])
    bones.append({
        "name": bname,
        "has_rot": has_rot,
        "rot_idx": rot_idx,
        "trn_mask": trn_mask,
        "trn_idx": (x_trn, y_trn, z_trn)
    })
    p += 8 + c_sz
    if p % 2 != 0: p += 1

print(f"Total bones: {len(bones)}")
for i, b in enumerate(bones):
    print(f"  [{i:02d}] {b['name']:<12} rot={b['has_rot']} (rot_idx={b['rot_idx']}) trn_mask={b['trn_mask']}")

