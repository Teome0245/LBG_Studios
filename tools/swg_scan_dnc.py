import struct
import zlib
import os
import glob

swg_dir = "J:/swgemu/StarWarsGalaxies"
tre_files = glob.glob(os.path.join(swg_dir, "*.tre"))

all_dnc = []

def parse_tre(tre_path):
    dances = []
    try:
        with open(tre_path, "rb") as f:
            hdr = f.read(16)
            magic, ver, count, toc_offset = struct.unpack("<4s4sII", hdr)
            if magic != b"EERT":
                return []
            f.seek(toc_offset)
            compressed_toc = f.read()
            decomp = zlib.decompressobj()
            toc_entries = decomp.decompress(compressed_toc)
            unused = decomp.unused_data
            if len(unused) > 0:
                name_data = zlib.decompress(unused)
                names = [n.decode('latin1', 'ignore') for n in name_data.split(b"\x00") if n]
                for n in names:
                    nl = n.lower()
                    if "_dnc_" in nl and nl.endswith(".ans"):
                        dances.append((os.path.basename(tre_path), n))
    except Exception as e:
        pass
    return dances

for t in tre_files:
    found = parse_tre(t)
    if found:
        all_dnc.extend(found)

print(f"TOTAL _DNC_ ANIMATIONS FOUND: {len(all_dnc)}")
for tre, name in sorted(all_dnc):
    print(f"[{tre}] {name}")

