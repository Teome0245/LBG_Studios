import struct
import zlib
import os
import glob

swg_dir = "J:/swgemu/StarWarsGalaxies"
tre_files = glob.glob(os.path.join(swg_dir, "*.tre"))

all_dances = []

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
                    if ("dance" in nl or "entertainer" in nl or "rhythmic" in nl or "exotic" in nl or "poplock" in nl or "footloose" in nl or "tumble" in nl) and nl.endswith(".ans"):
                        dances.append((os.path.basename(tre_path), n))
    except Exception as e:
        pass
    return dances

print(f"Scanning {len(tre_files)} TRE files...")
for t in tre_files:
    found = parse_tre(t)
    if found:
        print(f"Found {len(found)} in {os.path.basename(t)}")
        all_dances.extend(found)

print(f"\nTOTAL DANCE/ENTERTAINER ANIMATIONS FOUND: {len(all_dances)}")
for tre, name in sorted(all_dances):
    print(f"[{tre}] {name}")

