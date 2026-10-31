import os
import subprocess
import logging
import string
import shutil
import winreg
import re
import textwrap
import importlib
import inspect

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("executor")

# ---------------------------------------------------------
#  CACHE LOCAL DES PROGRAMMES RÉSOLUS
# ---------------------------------------------------------
PROGRAM_CACHE = {}

# ---------------------------------------------------------
#  RESOLVEUR AVANCÉ WINDOWS (multi-lecteurs, registre, PATH)
# ---------------------------------------------------------
def list_drives():
    return [f"{letter}:\\" for letter in string.ascii_uppercase if os.path.exists(f"{letter}:\\")]

def find_in_path(program_name):
    result = shutil.which(program_name)
    if result:
        print(f"[RESOLVER] ✔ Trouvé via PATH : {result}")
    return result

def find_in_registry(program_name):
    registry_paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths",
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
    ]

    for reg_path in registry_paths:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    if program_name.lower() in subkey_name.lower():
                        subkey = winreg.OpenKey(key, subkey_name)
                        path, _ = winreg.QueryValueEx(subkey, None)
                        print(f"[RESOLVER] ✔ Trouvé via registre : {path}")
                        return path
                    i += 1
                except OSError:
                    break
        except Exception:
            continue

    return None

def search_executable(program_name, drives):
    exe_name = program_name.lower() + ".exe"

    search_dirs = [
        "Program Files",
        "Program Files (x86)",
        "Users\\%USERNAME%\\AppData\\Local",
        "Users\\%USERNAME%\\AppData\\Roaming",
        "Applications",
        "PortableApps",
        "Games",
        "SteamLibrary"
    ]

    for drive in drives:
        for folder in search_dirs:
            base = os.path.expandvars(os.path.join(drive, folder))
            if not os.path.exists(base):
                continue

            print(f"[RESOLVER] 🔍 Scan : {base}")

            for root, dirs, files in os.walk(base):
                if exe_name in (f.lower() for f in files):
                    full_path = os.path.join(root, exe_name)
                    print(f"[RESOLVER] ✔ Trouvé via scan : {full_path}")
                    return full_path

    return None

def find_uwp_app(program_name):
    try:
        cmd = [
            "powershell",
            "-Command",
            f"Get-AppxPackage *{program_name}* | Select-Object -ExpandProperty InstallLocation"
        ]
        result = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True).strip()

        if result and os.path.exists(result):
            print(f"[RESOLVER] ✔ Trouvé via UWP : {result}")
            return result

    except Exception:
        pass

    return None

def resolve_program(program_name):
    print(f"[RESOLVER] 🔎 Recherche du programme : {program_name}")

    # 0) Cache local
    if program_name in PROGRAM_CACHE:
        print(f"[RESOLVER] ✔ Trouvé dans le cache : {PROGRAM_CACHE[program_name]}")
        return PROGRAM_CACHE[program_name]

    # 1) PATH
    path = find_in_path(program_name)
    if path:
        PROGRAM_CACHE[program_name] = path
        return path

    # 2) Registre
    path = find_in_registry(program_name)
    if path:
        PROGRAM_CACHE[program_name] = path
        return path

    # 3) UWP
    path = find_uwp_app(program_name)
    if path:
        PROGRAM_CACHE[program_name] = path
        return path

    # 4) Scan intelligent multi-lecteurs
    drives = list_drives()
    path = search_executable(program_name, drives)
    if path:
        PROGRAM_CACHE[program_name] = path
        return path

    print(f"[RESOLVER] ❌ Programme introuvable : {program_name}")
    return None

# ---------------------------------------------------------
#  FONCTION GÉNÉRIQUE : ouvrir un programme automatiquement
# ---------------------------------------------------------
def ouvrir_programme(program_name: str):
    path = resolve_program(program_name)

    if not path:
        return {
            "status": "error",
            "message": f"Programme '{program_name}' introuvable"
        }

    try:
        subprocess.Popen([path])
        return {
            "status": "ok",
            "message": f"Programme '{program_name}' lancé"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

# ---------------------------------------------------------
#  CAPABILITY AUTO-CORRECTIVE : ouvrir_notepad
# ---------------------------------------------------------
def ouvrir_notepad(**kwargs):
    """
    Capability auto-corrective :
    - essaie notepad.exe
    - fallback vers le resolver avancé
    """
    print("[AUTO] Correction automatique de 'ouvrir_notepad'")

    # 1) Tentative directe
    try:
        subprocess.Popen(["notepad.exe"])
        return {"status": "ok", "message": "Notepad ouvert."}
    except Exception:
        pass

    # 2) Fallback via resolver
    result = ouvrir_programme("notepad")
    return result

# ---------------------------------------------------------
#  AUTRES CAPABILITÉS EXISTANTES
# ---------------------------------------------------------
def open_notepad():
    try:
        subprocess.Popen(['notepad.exe'])
        return {"status": "ok", "message": "Notepad ouvert."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def list_directory(path="."):
    try:
        files = os.listdir(path)
        return {"status": "ok", "path": os.path.abspath(path), "files": files}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return {"status": "ok", "content": f.read()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def write_file(path, content):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return {"status": "ok", "message": f"Fichier écrit : {path}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def delete_file(path):
    try:
        if os.path.exists(path):
            os.remove(path)
            return {"status": "ok", "message": f"Fichier supprimé : {path}"}
        else:
            return {"status": "error", "message": "Le fichier n'existe pas."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def ouvre_fichier(path):
    try:
        if path.lower() in ["calc", "calc.exe", "calculatrice"]:
            subprocess.Popen(["calc.exe"])
            return {"status": "ok", "message": "Calculatrice lancée."}

        os.startfile(path)
        return {"status": "ok", "message": f"Ouverture de : {path}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------------------------------------------------------
#  CAPABILITY AUTO-GÉNÉRÉE : ouvrir_vlc (OK)
# ---------------------------------------------------------
def ouvrir_vlc(**kwargs):
    try:
        subprocess.Popen([r"C:\Program Files\VideoLAN\VLC\vlc.exe"])
        return {
            "status": "ok",
            "message": "ouvrir_vlc exécuté."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }




# --- Capability auto-installée ---
# Description : Auto-installed capability ouvrir_istripper

def ouvrir_istripper(**kwargs):
    return {
        "status": "error",
        "message": "Capability 'ouvrir_istripper' auto-générée mais programme inconnu ou non configuré"
    }




# --- Capability auto-installée ---
# Description : Auto-installed capability reload_capabilities

def reload_capabilities(**kwargs):
    return {
        "status": "error",
        "message": "Capability 'reload_capabilities' auto-générée mais programme inconnu ou non configuré"
    }




# --- Capability auto-installée ---
# Description : Auto-installed capability liste_capabilities

def liste_capabilities(**kwargs):
    return {
        "status": "error",
        "message": "Capability 'liste_capabilities' auto-générée mais programme inconnu ou non configuré"
    }




# --- Capability auto-installée ---
# Description : Auto-installed capability ouvrir_firefox

def ouvrir_firefox(**kwargs):
    return {
        "status": "error",
        "message": "Capability 'ouvrir_firefox' auto-générée mais programme inconnu ou non configuré"
    }




# --- Capability auto-installée ---
# Description : Auto-installed capability list_agent_capabilities

def list_agent_capabilities(**kwargs):
    return {
        "status": "error",
        "message": "Capability 'list_agent_capabilities' auto-générée mais programme inconnu ou non configuré"
    }




# --- Capability auto-installée ---
# Description : Auto-installed capability ouvrir_paint

def ouvrir_paint(**kwargs):
    return {
        "status": "error",
        "message": "Capability 'ouvrir_paint' auto-générée mais programme inconnu ou non configuré"
    }



# --- Capability auto-installée ---
# Description : Copie le modele Compagnon.vrm et les textures vers N:/Upload/IA
def copier_vrm_upload_ia(**kwargs):
    import shutil
    import os
    src_dir = "A:/LBG_Studios/packages/compagnon-desktop/overlay/vrm"
    dst_dir = "N:/Upload/IA"
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir, exist_ok=True)
    files_to_copy = [
        "Compagnon.vrm",
        "body_skin_android.png", "body_skin_android_5b.png",
        "face_skin_android.png",
        "hair_android.png"
    ]
    copied = []
    errors = []
    for f in files_to_copy:
        src = os.path.join(src_dir, f)
        dst = os.path.join(dst_dir, f)
        try:
            if os.path.exists(src):
                shutil.copy2(src, dst)
                copied.append(f)
            else:
                errors.append(f"Source introuvable: {src}")
        except Exception as e:
            errors.append(f"Erreur copie {f}: {str(e)}")
    return {"status": "ok" if not errors else "partial", "copied": copied, "errors": errors, "destination": dst_dir}



# --- Capability auto-installée ---
# Description : Synchronise les textures et bundles VRM vers C:/Agent_IA/compagnon-desktop/overlay/vrm
def sync_vrm_desktop(**kwargs):
    import shutil
    import os
    import urllib.request
    dst_dir = "C:/Agent_IA/compagnon-desktop/overlay/vrm"
    os.makedirs(dst_dir, exist_ok=True)
    files = ["body_skin_android.png", "body_skin_android_5b.png", "face_skin_android.png", "hair_android.png", "metallic_matcap.png", "rim_multiply_mask.png", "vrm_pet.bundle.js", "vrm_pet.js"]
    res = []
    src_dir = "A:/LBG_Studios/packages/compagnon-desktop/overlay/vrm"
    if os.path.exists(src_dir):
        for f in files:
            s = os.path.join(src_dir, f)
            d = os.path.join(dst_dir, f)
            if os.path.exists(s):
                shutil.copy2(s, d)
                res.append(f)
    if not res:
        base_url = "http://192.168.0.100:5174/vrm/"
        errs = []
        for f in files:
            url = base_url + f
            d = os.path.join(dst_dir, f)
            try:
                urllib.request.urlretrieve(url, d)
                res.append(f)
            except Exception as e:
                errs.append(f"{f}: {e}")
        if errs:
            return {"status": "partial", "synced": res, "errors": errs}
    return {"status": "ok", "synced": res}



# --- Capability auto-installée ---
# Description : Redemarre l'overlay Electron compagnon-desktop
def restart_desktop_overlay(**kwargs):
    import subprocess
    import time
    # 1. Kill any electron instances
    try:
        subprocess.run(["taskkill", "/F", "/IM", "electron.exe", "/T"], capture_output=True)
    except Exception:
        pass
    time.sleep(1)
    # 2. Run scheduled task in user interactive session (sdesh)
    try:
        out = subprocess.check_output(["schtasks", "/Run", "/TN", "LBG-Compagnon-Desktop"], text=True)
    except Exception as e:
        out = str(e)
    time.sleep(2)
    # 3. Check running electron processes
    try:
        chk = subprocess.check_output(["powershell", "-NoProfile", "-Command", "Get-Process electron -ErrorAction SilentlyContinue | Select-Object Id, SessionId, ProcessName | ConvertTo-Json"], text=True)
        return {"status": "ok", "schtasks": out.strip(), "electron": chk.strip()}
    except Exception as e:
        return {"status": "ok", "schtasks": out.strip(), "electron": str(e)}



# --- Capability auto-installée ---
# Description : Copie N:/Upload/IA/face_skin_android.png vers A: et C:
def importer_face_skin_upload_ia(**kwargs):
    import shutil
    import os
    src = "N:/Upload/IA/face_skin_android.png"
    dst_repo = "A:/LBG_Studios/packages/compagnon-desktop/overlay/vrm/face_skin_android.png"
    dst_local = "C:/Agent_IA/compagnon-desktop/overlay/vrm/face_skin_android.png"
    
    if not os.path.exists(src):
        return {"status": "error", "message": f"Fichier source introuvable sur N: {src}"}
    
    src_size = os.path.getsize(src)
    src_mtime = os.path.getmtime(src)
    
    # Copie vers le dépôt sur A:
    shutil.copy2(src, dst_repo)
    
    # Copie vers le local desktop C:
    if os.path.exists("C:/Agent_IA/compagnon-desktop/overlay/vrm"):
        shutil.copy2(src, dst_local)
        
    return {
        "status": "ok",
        "src": src,
        "src_size": src_size,
        "src_mtime": src_mtime,
        "dst_repo": dst_repo,
        "repo_size": os.path.getsize(dst_repo),
        "dst_local": dst_local
    }



# --- Capability auto-installée ---
def stat_upload_ia(**kwargs):
    import os
    import time
    d = "N:/Upload/IA"
    res = {}
    for f in os.listdir(d):
        if "skin" in f.lower() or "body" in f.lower() or "face" in f.lower():
            p = os.path.join(d, f)
            st = os.stat(p)
            res[f] = {
                "size": st.st_size,
                "mtime": time.ctime(st.st_mtime)
            }
    return res



# --- Capability auto-installée ---
def copier_nouveaux_skins(**kwargs):
    import shutil
    import os
    d_src = "N:/Upload/IA"
    d_dst = "A:/LBG_Studios/scratch"
    res = []
    for f in ["body_skin_android_2.png", "body_skin_android_3.png", "face_skin_android_old.png", "body_skin_android.png", "body_skin_android_5b.png"]:
        sp = os.path.join(d_src, f)
        dp = os.path.join(d_dst, f)
        if os.path.exists(sp):
            shutil.copy2(sp, dp)
            res.append({"file": f, "size": os.path.getsize(sp), "copied": True})
        else:
            res.append({"file": f, "copied": False})
    return res



# --- Capability auto-installée ---
def exporter_body_skin_upload_ia(**kwargs):
    import shutil
    import os
    src = "A:/LBG_Studios/packages/compagnon-desktop/overlay/vrm/body_skin_android.png"
    dst = "N:/Upload/IA/body_skin_android.png"
    if os.path.exists(src):
        shutil.copy2(src, dst)
        return {"status": "ok", "copied": dst, "size": os.path.getsize(dst)}
    return {"status": "error", "message": f"Source introuvable: {src}"}




# --- Capability synchronisation complète VRM Upload IA ---
def synchroniser_tout_vrm_upload_ia(**kwargs):
    import shutil
    import os
    src_dir = "A:/LBG_Studios/packages/compagnon-desktop/overlay/vrm"
    dst_dir = "N:/Upload/IA"
    files = ["body_skin_android.png", "body_skin_android_5b.png", "metallic_matcap.png", "rim_multiply_mask.png", "face_skin_android.png", "hair_android.png", "vrm_pet.bundle.js", "vrm_pet.js"]
    res = []
    for f in files:
        s = os.path.join(src_dir, f)
        d = os.path.join(dst_dir, f)
        if os.path.exists(s):
            shutil.copy2(s, d)
            res.append(f)
    return {"status": "ok", "exported_to_upload_ia": res}


def chercher_vroid(**kwargs):
    import os
    found = []
    paths_to_check = [
        os.path.expandvars("%USERPROFILE%/Documents/vroid"),
        os.path.expandvars("%USERPROFILE%/AppData/LocalLow/pixiv"),
        "C:/Users",
        "N:/",
        "A:/"
    ]
    for base in paths_to_check:
        if not os.path.exists(base):
            continue
        try:
            for root, dirs, files in os.walk(base):
                for f in files:
                    if f.lower().endswith(".vroid"):
                        found.append(os.path.join(root, f).replace("\\", "/"))
                dirs[:] = [d for d in dirs if d not in [".git", "node_modules", ".venv", "AppData", "Windows"]]
        except Exception:
            pass
    return {"status": "ok", "found": found}


# --- Capability copie vers E:/IA ---
def copier_tout_vers_e_ia(**kwargs):
    import shutil
    import os
    src_dir = "A:/LBG_Studios/packages/compagnon-desktop/overlay/vrm"
    dst_dir = "E:/IA"
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir, exist_ok=True)
    
    files_to_copy = [
        "Compagnon.vrm",
        "body_skin_android.png",
        "body_skin_android_5b.png",
        "face_skin_android.png",
        "hair_android.png",
        "metallic_matcap.png",
        "rim_multiply_mask.png",
        "vrm_pet.bundle.js",
        "vrm_pet.js",
        "Anna.vrm",
        "Aurora.vrm",
        "LadyKoi.vrm",
        "default.vrm"
    ]
    copied = []
    errors = []
    for f in files_to_copy:
        s = os.path.join(src_dir, f)
        d = os.path.join(dst_dir, f)
        try:
            if os.path.exists(s):
                shutil.copy2(s, d)
                copied.append(f)
            else:
                errors.append(f"Source introuvable: {s}")
        except Exception as e:
            errors.append(f"Erreur copie {f}: {str(e)}")

    # Search and copy any .vroid files found in user Documents or C:/Agent_IA
    vroid_copied = []
    user_bases = ["C:/Users/sdesharches/Documents", "C:/Users/sdesharches.LABOITEAGEEKS/Documents", "C:/Users/sdesh/Documents", "C:/Agent_IA"]
    for ub in user_bases:
        if os.path.exists(ub):
            for root, dirs, files in os.walk(ub):
                for f in files:
                    if f.lower().endswith(".vroid") or f.lower().endswith(".xroid"):
                        sf = os.path.join(root, f)
                        df = os.path.join(dst_dir, f)
                        try:
                            shutil.copy2(sf, df)
                            vroid_copied.append(f)
                        except Exception:
                            pass
                dirs[:] = [d for d in dirs if d not in [".git", "node_modules", "AppData"]]

    dst_files = os.listdir(dst_dir)
    return {
        "status": "ok",
        "copied": copied,
        "vroid_copied": vroid_copied,
        "errors": errors,
        "destination": dst_dir,
        "all_dst_files": dst_files
    }

def stat_e_ia(**kwargs):
    import os
    res = {}
    for f in os.listdir('E:/IA'):
        p = os.path.join('E:/IA', f)
        res[f] = os.path.getsize(p)
    return {'status': 'ok', 'files': res}

def hash_files(**kwargs):
    import hashlib
    res = {}
    for p in ['C:/Agent_IA/compagnon-desktop/overlay/vrm/vrm_pet.bundle.js', 'C:/Agent_IA/compagnon-desktop/overlay/vrm/Compagnon.vrm']:
        try:
            with open(p, 'rb') as f:
                res[p] = hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            res[p] = str(e)
    return {'status': 'ok', 'hashes': res}

def check_a_hash(**kwargs):
    import hashlib
    p = 'A:/LBG_Studios/packages/compagnon-desktop/overlay/vrm/Compagnon.vrm'
    with open(p, 'rb') as f:
        return {'status': 'ok', 'hash': hashlib.md5(f.read()).hexdigest()}

def update_desktop_compagnon_vrm(**kwargs):
    import shutil
    src = 'A:/LBG_Studios/packages/compagnon-desktop/overlay/vrm/Compagnon.vrm'
    dst = 'C:/Agent_IA/compagnon-desktop/overlay/vrm/Compagnon.vrm'
    shutil.copy2(src, dst)
    return {'status': 'ok', 'copied': True}

def deploy_smooth_framing_desktop(**kwargs):
    import shutil
    import subprocess
    import os
    src_dir = 'A:/LBG_Studios/packages/compagnon-desktop/overlay/vrm'
    dst_dir_c = 'C:/Agent_IA/compagnon-desktop/overlay/vrm'
    dst_dir_e = 'E:/IA'
    
    files = ['vrm_pet.bundle.js', 'vrm_pet.js', 'Compagnon.vrm']
    copied = []
    for f in files:
        s = os.path.join(src_dir, f)
        d_c = os.path.join(dst_dir_c, f)
        d_e = os.path.join(dst_dir_e, f)
        if os.path.exists(s):
            shutil.copy2(s, d_c)
            shutil.copy2(s, d_e)
            copied.append(f)
    
    # Restart Electron overlay
    subprocess.run(['taskkill', '/F', '/IM', 'electron.exe'], capture_output=True)
    # Start overlay via powershell in background
    app_dir = 'C:/Agent_IA/compagnon-desktop'
    p = subprocess.Popen(['npx.cmd', 'electron', '.'], cwd=app_dir, shell=True)
    
    return {'status': 'ok', 'copied': copied, 'new_pid': p.pid}

def check_bridge_local(**kwargs):
    import urllib.request
    try:
        with urllib.request.urlopen('http://127.0.0.1:8765/avatar/state', timeout=2) as r:
            return {'status': 'ok', 'bridge': r.read().decode()}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_compagnon_status(**kwargs):
    import subprocess
    ps_cmd = "Get-CimInstance Win32_Process | Where-Object { $_.Name -match \"electron\" -or $_.CommandLine -match \"compagnon\" } | Select-Object ProcessId, Name, CommandLine | ConvertTo-Json"
    try:
        out = subprocess.check_output(["powershell", "-NoProfile", "-Command", ps_cmd], text=True)
        return {"status": "ok", "processes": out.strip()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_windows_list(**kwargs):
    import subprocess
    ps_cmd = "Get-Process | Where-Object { $_.MainWindowTitle } | Select-Object ProcessId, ProcessName, MainWindowTitle | ConvertTo-Json"
    try:
        out = subprocess.check_output(["powershell", "-NoProfile", "-Command", ps_cmd], text=True)
        return {"status": "ok", "windows": out.strip()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_electron_session(**kwargs):
    import subprocess
    ps_cmd = "Get-Process electron -ErrorAction SilentlyContinue | Select-Object Id, SessionId, ProcessName, WorkingSet | ConvertTo-Json"
    try:
        out = subprocess.check_output(["powershell", "-NoProfile", "-Command", ps_cmd], text=True)
        return {"status": "ok", "sessions": out.strip()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_scheduled_tasks(**kwargs):
    import subprocess
    ps_cmd = "Get-ScheduledTask | Where-Object { $_.TaskName -match \"LBG|Compagnon|Agent\" } | Select-Object TaskName, State | ConvertTo-Json"
    try:
        out = subprocess.check_output(["powershell", "-NoProfile", "-Command", ps_cmd], text=True)
        return {"status": "ok", "tasks": out.strip()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def kill_all_electron(**kwargs):
    import subprocess
    try:
        out = subprocess.check_output(["taskkill", "/F", "/IM", "electron.exe", "/T"], text=True)
        return {"status": "ok", "message": out.strip()}
    except subprocess.CalledProcessError as e:
        return {"status": "ok", "message": "No electron running or: " + str(e.output)}

def get_task_xml(**kwargs):
    import subprocess
    try:
        out = subprocess.check_output(["schtasks", "/Query", "/TN", "LBG-AgentIA-logon", "/XML"], text=True)
        return {"status": "ok", "xml": out[:1200]}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def run_setup_task(**kwargs):
    import subprocess
    try:
        out = subprocess.check_output(["python", "C:\\Agent_IA\\setup_task.py"], text=True)
        return {"status": "ok", "output": out.strip()}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_active_window_context(**kwargs):
    """Focus Awareness (Ticket 1.2) : Récupère le nom du processus et la catégorie de la fenêtre active au premier plan sans scan intrusif."""
    import json
    import subprocess

    ps_script = """
    Add-Type @"
    using System;
    using System.Text;
    using System.Runtime.InteropServices;
    public class User32Active {
      [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
      [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
      [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
    }
    "@
    $hwnd = [User32Active]::GetForegroundWindow()
    if ($hwnd -ne [IntPtr]::Zero) {
      $sb = New-Object System.Text.StringBuilder 512
      [void][User32Active]::GetWindowText($hwnd, $sb, 512)
      $pidVal = 0
      [void][User32Active]::GetWindowThreadProcessId($hwnd, [ref]$pidVal)
      $proc = Get-Process -Id $pidVal -ErrorAction SilentlyContinue
      [PSCustomObject]@{
        title = $sb.ToString()
        process = if ($proc) { $proc.ProcessName } else { "" }
        pid = $pidVal
      } | ConvertTo-Json -Compress
    }
    """
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=5,
        )
        out = res.stdout.strip()
        if not out:
            return {"status": "ok", "category": "idle", "app": "unknown", "attitude": "relax"}
        parsed = json.loads(out)
        proc = str(parsed.get("process", "")).lower()
        title = str(parsed.get("title", "")).lower()

        if any(k in proc or k in title for k in ["cursor", "code", "devenv", "pycharm"]):
            cat, att = "coding", "think"
        elif any(k in proc or k in title for k in ["godot", "blender", "unreal", "unity"]):
            cat, att = "gamedev", "curious"
        elif any(k in proc or k in title for k in ["terminal", "powershell", "cmd", "wt", "bash"]):
            cat, att = "terminal", "alert"
        elif any(k in proc or k in title for k in ["prime", "swg", "lost heaven"]):
            cat, att = "gaming", "cheer"
        elif any(k in proc or k in title for k in ["chrome", "msedge", "firefox", "brave"]):
            cat, att = "browsing", "serene"
        else:
            cat, att = "general", "serene"

        return {
            "status": "ok",
            "category": cat,
            "attitude": att,
            "process": parsed.get("process", ""),
            "title_summary": (parsed.get("title", "")[:80]),
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc), "category": "unknown", "attitude": "serene"}

