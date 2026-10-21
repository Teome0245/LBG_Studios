import urllib.request
import json
import subprocess

agent_url = "http://192.168.0.10:5005/execute"

def send_action(action, parameters=None):
    payload = {"action": action, "parameters": parameters or {}}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(agent_url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as res:
        return json.loads(res.read().decode())

print("1. Lecture de C:\\Agent_IA\\executor.py...")
res = send_action("read_file", {"path": "C:\\Agent_IA\\executor.py"})
content = res.get("result", {}).get("content", "")

# Ajouter "rim_multiply_mask.png" si pas encore présent
if '"rim_multiply_mask.png"' not in content:
    print("Mise à jour des listes de fichiers dans executor.py...")
    old_files_1 = 'files = ["body_skin_android.png", "face_skin_android.png", "hair_android.png", "metallic_matcap.png", "vrm_pet.bundle.js", "vrm_pet.js"]'
    new_files_1 = 'files = ["body_skin_android.png", "face_skin_android.png", "hair_android.png", "metallic_matcap.png", "rim_multiply_mask.png", "vrm_pet.bundle.js", "vrm_pet.js"]'
    
    old_files_2 = 'files = ["body_skin_android.png", "metallic_matcap.png", "face_skin_android.png", "hair_android.png", "vrm_pet.bundle.js", "vrm_pet.js"]'
    new_files_2 = 'files = ["body_skin_android.png", "metallic_matcap.png", "rim_multiply_mask.png", "face_skin_android.png", "hair_android.png", "vrm_pet.bundle.js", "vrm_pet.js"]'
    
    content = content.replace(old_files_1, new_files_1).replace(old_files_2, new_files_2)
    write_res = send_action("write_file", {"path": "C:\\Agent_IA\\executor.py", "content": content})
    print("Ecriture executor.py:", write_res.get("result", {}).get("message"))
else:
    print("executor.py contient déjà rim_multiply_mask.png.")

print("\n2. Synchronisation vers N:\\Upload\\IA...")
upload_res = send_action("synchroniser_tout_vrm_upload_ia")
print("Upload IA result:", upload_res.get("result"))

print("\n3. Synchronisation locale vers C:\\Agent_IA\\compagnon-desktop...")
sync_res = send_action("sync_vrm_desktop")
print("Sync Desktop result:", sync_res.get("result"))

print("\n4. Redémarrage de l'overlay Electron sur Windows...")
restart_res = send_action("restart_desktop_overlay")
print("Restart Electron result:", restart_res.get("result"))
