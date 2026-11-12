#!/usr/bin/env python3
"""
Convertit en parallèle tous les FBX de packages/compagnon-desktop/overlay/vrm/fbx_source
vers packages/compagnon-desktop/overlay/vrm/animations et compagnon_ui/public/vrm/animations.
"""
import os
import sys
import subprocess
import shutil
from concurrent.futures import ProcessPoolExecutor, as_completed

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FBX_DIR = os.path.join(REPO_ROOT, "packages/compagnon-desktop/overlay/vrm/fbx_source")
DEST_DESKTOP = os.path.join(REPO_ROOT, "packages/compagnon-desktop/overlay/vrm/animations")
DEST_WEB = os.path.join(REPO_ROOT, "packages/cortex/compagnon_ui/public/vrm/animations")
CONVERTER = os.path.join(REPO_ROOT, "tools/fbx2vrma/fbx2vrma-converter.js")
FBX2GLTF = os.path.join(REPO_ROOT, "tools/fbx2vrma/FBX2glTF-linux-x64")

def convert_one(fbx_file):
    base_name = os.path.splitext(fbx_file)[0]
    out_desktop = os.path.join(DEST_DESKTOP, f"{base_name}.vrma")
    out_web = os.path.join(DEST_WEB, f"{base_name}.vrma")
    
    if os.path.exists(out_desktop) and os.path.getsize(out_desktop) > 1000:
        if not os.path.exists(out_web) or os.path.getsize(out_web) != os.path.getsize(out_desktop):
            shutil.copy2(out_desktop, out_web)
        return {"file": fbx_file, "status": "skipped", "size": os.path.getsize(out_desktop)}

    fbx_path = os.path.join(FBX_DIR, fbx_file)
    cmd = [
        "node", CONVERTER,
        "-i", fbx_path,
        "-o", out_desktop,
        "--fbx2gltf", FBX2GLTF
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if proc.returncode == 0 and os.path.exists(out_desktop) and os.path.getsize(out_desktop) > 1000:
            shutil.copy2(out_desktop, out_web)
            return {"file": fbx_file, "status": "converted", "size": os.path.getsize(out_desktop)}
        else:
            return {"file": fbx_file, "status": "failed", "error": proc.stderr or proc.stdout}
    except Exception as e:
        return {"file": fbx_file, "status": "error", "error": str(e)}

def main():
    os.makedirs(DEST_DESKTOP, exist_ok=True)
    os.makedirs(DEST_WEB, exist_ok=True)
    
    fbx_files = [f for f in sorted(os.listdir(FBX_DIR)) if f.lower().endswith(".fbx")]
    total = len(fbx_files)
    print(f"Total FBX détectés : {total}")
    
    converted = 0
    skipped = 0
    failed = 0
    total_bytes = 0
    
    # 4 parallel workers to avoid thrashing disk while maximizing throughput
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(convert_one, f): f for f in fbx_files}
        for future in as_completed(futures):
            res = future.result()
            f = res["file"]
            st = res["status"]
            if st == "converted":
                converted += 1
                total_bytes += res["size"]
                sz_kb = round(res["size"] / 1024, 1)
                print(f"[✔] [{converted + skipped + failed}/{total}] CONVERTI : {f} ({sz_kb} KB)")
            elif st == "skipped":
                skipped += 1
                total_bytes += res["size"]
                print(f"[-] [{converted + skipped + failed}/{total}] DÉJÀ PRÊT : {f}")
            else:
                failed += 1
                print(f"[❌] [{converted + skipped + failed}/{total}] ÉCHEC : {f} -> {res.get('error', '')[:120]}")

    print("\n" + "="*50)
    print(f"Bilan conversion FBX -> VRMA :")
    print(f"  Convertis : {converted}")
    print(f"  Déjà existants : {skipped}")
    print(f"  Échecs : {failed}")
    print(f"  Taille totale VRMA : {round(total_bytes / (1024*1024), 2)} MB")
    print("="*50)

if __name__ == "__main__":
    main()

