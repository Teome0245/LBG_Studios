import struct
import zlib
import os

tre_path = "J:/swgemu/StarWarsGalaxies/data_animation_00.tre"
out_dir = "C:/Agent_IA/swg_extracted"
os.makedirs(out_dir, exist_ok=True)

with open(tre_path, "rb") as f:
    hdr = f.read(16)
    magic, ver, count, toc_offset = struct.unpack("<4s4sII", hdr)
    
    f.seek(toc_offset)
    decomp = zlib.decompressobj()
    toc_data = decomp.decompress(f.read())
    unused = decomp.unused_data
    name_data = zlib.decompress(unused)
    
    names = [n.decode('latin1', 'ignore') for n in name_data.split(b"\x00") if n]
    print(f"Loaded {len(names)} names, {len(toc_data)//24} TOC entries.")
    
    # Each entry in toc_data is 24 bytes:
    # 0..4: checksum/hash?
    # 4..8: uncompressed size
    # 8..12: offset in file
    # 12..16: compression type (0: none, 2: zlib)
    # 16..20: compressed size
    # 20..24: name offset
    
    entries = []
    for i in range(count):
        off = i * 24
        csum, usize, data_off, comp, csize, name_off = struct.unpack("<6I", toc_data[off:off+24])
        name = names[i]
        entries.append({
            "name": name,
            "usize": usize,
            "data_off": data_off,
            "comp": comp,
            "csize": csize
        })
        
    targets = [
        "appearance/animation/all_b_dnc_goofy_sp_moonwalk.ans",
        "appearance/animation/all_b_dnc_tatooine_jazz_loop.ans",
        "appearance/animation/all_m_dnc_m_poplock_base_loop.ans"
    ]
    
    for e in entries:
        if e["name"] in targets or any(t.split("/")[-1] == e["name"].split("/")[-1] for t in targets):
            print(f"Extracting {e['name']} (comp={e['comp']}, csize={e['csize']}, usize={e['usize']})...")
            f.seek(e["data_off"])
            raw = f.read(e["csize"] if e["comp"] == 2 else e["usize"])
            if e["comp"] == 2:
                data = zlib.decompress(raw)
            else:
                data = raw
            fname = os.path.basename(e["name"])
            dst = os.path.join(out_dir, fname)
            with open(dst, "wb") as out_f:
                out_f.write(data)
            print(f"  -> Saved {dst} ({len(data)} bytes, IFF Header: {data[:16]})")

