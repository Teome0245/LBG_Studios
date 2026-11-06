import json
import urllib.request
from pathlib import Path

BASE_LOCAL = Path("/home/lbg/Projets/LBG_Studios/packages/swg-client")
BASE_REMOTE = "J:/swgemu/clients/swg-client"
ENDPOINT = "http://192.168.0.10:5005/execute"

FILES = [
    "scripts/swg_inventory_paperdoll.gd",
    "scripts/swg_audio_synthesizer.gd",
    "scripts/swg_asset_pipeline.gd",
    "scripts/swg_radial_menu.gd",
    "scripts/swg_world_3d.gd",
]

for rel_path in FILES:
    local_p = BASE_LOCAL / rel_path
    remote_p = f"{BASE_REMOTE}/{rel_path}"
    content = local_p.read_text(encoding="utf-8")
    
    payload = {
        "action": "write_file",
        "parameters": {
            "path": remote_p,
            "content": content
        }
    }
    
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            print(f"[OK] {rel_path} -> {remote_p}: {res_data.get('status', 'written')}")
    except Exception as e:
        print(f"[ERR] {rel_path}: {e}")

