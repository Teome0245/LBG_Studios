import struct
import zlib

tre_path = "J:/swgemu/clients/prime-lbg/data_animation_00.tre"

with open(tre_path, "rb") as f:
    f.seek(58729599)
    compressed_toc = f.read()
    
    decomp = zlib.decompressobj()
    toc_data = decomp.decompress(compressed_toc)
    unused = decomp.unused_data
    print(f"Decompressed TOC chunk 1 size: {len(toc_data)}")
    print(f"Remaining unused data size: {len(unused)}")
    
    if len(unused) > 0 and unused[:2] == b"\x78\x9c":
        print("Second chunk is also zlib!")
        toc_data_2 = zlib.decompress(unused)
        print(f"Decompressed TOC chunk 2 size: {len(toc_data_2)}")
        
        # Check if text/names are in chunk 2
        strings = toc_data_2.split(b"\x00")
        print(f"Chunk 2 has {len(strings)} strings.")
        dances = [s.decode('latin1', 'ignore') for s in strings if b"dance" in s.lower()]
        print(f"Found {len(dances)} dance occurrences in chunk 2:")
        for d in dances[:30]:
            print("  ", d)
    else:
        # Check chunk 1
        strings = toc_data.split(b"\x00")
        print(f"Chunk 1 has {len(strings)} strings.")
        dances = [s.decode('latin1', 'ignore') for s in strings if b"dance" in s.lower()]
        print(f"Found {len(dances)} dance occurrences in chunk 1:")
        for d in dances[:30]:
            print("  ", d)
