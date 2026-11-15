import struct
import zlib
import os
import glob

tre_paths = sorted(glob.glob("J:/swgemu/StarWarsGalaxies/*.tre"))
out_dir = "C:/Agent_IA/swg_extracted"
os.makedirs(out_dir, exist_ok=True)

target_keywords = [
    "tatooine",
    "jazz",
    "tumble",
    "exotic",
    "lyrical",
    "breakdance",
    "rhythm",
    "elaine",
    "poplock",
    "moonwalk",
    "starwars",
    "freestyle",
    "basic"
]

extracted = set()

for tre_path in tre_paths:
    try:
        with open(tre_path, "rb") as f:
            hdr = f.read(16)
            if len(hdr) < 16:
                continue
            magic, ver, count, toc_offset = struct.unpack("<4s4sII", hdr)
            if magic != b"EERT":
                continue
            f.seek(toc_offset)
            decomp = zlib.decompressobj()
            toc_data = decomp.decompress(f.read())
            unused = decomp.unused_data
            if not unused:
                continue
            name_data = zlib.decompress(unused)
            names = [n.decode('latin1', 'ignore') for n in name_data.split(b"\x00") if n]
            
            for i in range(min(count, len(names))):
                name = names[i]
                if not name.endswith(".ans") or "dnc" not in name:
                    continue
                
                basename = os.path.basename(name).lower()
                if any(k in basename for k in target_keywords):
                    if basename not in extracted:
                        off = i * 24
                        if off + 24 > len(toc_data):
                            continue
                        csum, usize, data_off, comp, csize, name_off = struct.unpack("<6I", toc_data[off:off+24])
                        f.seek(data_off)
                        raw = f.read(csize if comp == 2 else usize)
                        data = zlib.decompress(raw) if comp == 2 else raw
                        dst = os.path.join(out_dir, basename)
                        with open(dst, "wb") as out_f:
                            out_f.write(data)
                        extracted.add(basename)
                        print(f"  [+] {os.path.basename(tre_path)} -> {basename} ({len(data)} bytes)")
    except Exception as e:
        pass

print(f"Scan complete. Total extracted: {len(extracted)} animations into {out_dir}")
