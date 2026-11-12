# -*- coding: utf-8 -*-
import subprocess
import time
import os
import shutil
import ctypes
import threading

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME):
    CHROME = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

FFMPEG = r"C:\Users\sdesh\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0-full_build\bin\ffmpeg.EXE"
AUDIO_PATH = r"O:\OneDrive\Pictures\IA\Contenue\Nexura Domina_v1.mp3"
RAW_VIDEO = r"C:\Agent_IA\studio_nexura_raw_full.mp4"
FINAL_CLIP = r"C:\Agent_IA\clip_nexura_domina_v1_studio_full.mp4"
FINAL_ONEDRIVE = r"O:\OneDrive\Pictures\IA\Contenue\clip_nexura_domina_v1_studio_full.mp4"

URL = "http://127.0.0.1:8766/studio_clip.html"
PROFILE = r"C:\Agent_IA\studio_profile"

def keep_topmost_worker(stop_event):
    user32 = ctypes.windll.user32
    try:
        user32.SetCursorPos(0, 0)
    except Exception:
        pass

    def enum_cb(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value
                if "Nexura" in title or "LBG Studios" in title or "Live Virtual Singer" in title:
                    user32.SetWindowPos(hwnd, -1, 1340, 30, 556, 1002, 0x0040)
                    user32.SetForegroundWindow(hwnd)
        return True

    CMPFUNC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    cb = CMPFUNC(enum_cb)

    while not stop_event.is_set():
        try:
            user32.EnumWindows(cb, 0)
        except Exception:
            pass
        time.sleep(1.0)

print("[1/6] Fermeture des overlays bureau existants et nettoyage cache...")
subprocess.run(["taskkill", "/F", "/IM", "electron.exe", "/T"], capture_output=True)
subprocess.run(["taskkill", "/F", "/IM", "chrome.exe", "/T"], capture_output=True)
time.sleep(1)

# Nettoyer le cache HTTP de Chrome pour charger le dernier bundle JS
cache_dir = os.path.join(PROFILE, "Default", "Cache")
if os.path.exists(cache_dir):
    try:
        shutil.rmtree(cache_dir, ignore_errors=True)
    except Exception:
        pass

# Relancer le serveur studio
print("[2/6] Demarrage du serveur local studio :8766...")
subprocess.Popen([r"C:\Python\Python314\python.exe", r"C:\Agent_IA\studio_server.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.5)

print("[3/6] Lancement du Studio WebGL Chrome (style @aeysamusic)...")
ts = int(time.time())
chrome_cmd = [
    CHROME,
    f"--app={URL}?v={ts}",
    "--window-size=556,1002",
    "--window-position=1340,30",
    "--autoplay-policy=no-user-gesture-required",
    "--disable-http-cache",
    f"--user-data-dir={PROFILE}",
    "--no-first-run",
    "--no-default-browser-check"
]
chrome_proc = subprocess.Popen(chrome_cmd)
print(f"Chrome lance (PID={chrome_proc.pid}), attente chargement VRM 3D (5s)...")
time.sleep(5.0)

# Lancement du gardien TopMost
stop_topmost = threading.Event()
topmost_thread = threading.Thread(target=keep_topmost_worker, args=(stop_topmost,), daemon=True)
topmost_thread.start()

print("[4/6] Demarrage de l'enregistrement FFmpeg gdigrab (chanson complete 158s @ 30 FPS)...")
# Zone utile plein ecran stage 540x960 sans curseur de souris (-draw_mouse 0)
ffmpeg_rec_cmd = [
    FFMPEG,
    "-f", "gdigrab",
    "-draw_mouse", "0",
    "-framerate", "30",
    "-offset_x", "1348",
    "-offset_y", "64",
    "-video_size", "540x960",
    "-t", "158.0",
    "-i", "desktop",
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-pix_fmt", "yuv420p",
    "-y",
    RAW_VIDEO
]
rec_proc = subprocess.run(ffmpeg_rec_cmd, capture_output=True, text=True)
print(f"Enregistrement termine (code {rec_proc.returncode}).")

# Arret du gardien TopMost
stop_topmost.set()

print("[5/6] Fermeture de Chrome et relance du compagnon bureau...")
try:
    chrome_proc.terminate()
    subprocess.run(["taskkill", "/F", "/IM", "chrome.exe", "/T"], capture_output=True)
except Exception:
    pass

# Relance de l'overlay de bureau habituel
try:
    subprocess.run(["schtasks", "/Run", "/TN", "LBG-Compagnon-Desktop"], capture_output=True)
except Exception:
    pass

raw_size = os.path.getsize(RAW_VIDEO) if os.path.exists(RAW_VIDEO) else 0
print(f"Flux video brut : {round(raw_size / (1024*1024), 2)} Mo")

print("[6/6] Muxing master audio Nexura Domina + Lanczos Upscale HD 1080x1920...")
mux_cmd = [
    FFMPEG,
    "-i", RAW_VIDEO,
    "-i", AUDIO_PATH,
    "-filter_complex", "[0:v]scale=1080:1920:flags=lanczos[v]",
    "-map", "[v]",
    "-map", "1:a",
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-crf", "18",
    "-c:a", "aac",
    "-b:a", "256k",
    "-shortest",
    "-y",
    FINAL_CLIP
]
mux_proc = subprocess.run(mux_cmd, capture_output=True, text=True)
if mux_proc.returncode == 0:
    final_size = os.path.getsize(FINAL_CLIP) if os.path.exists(FINAL_CLIP) else 0
    print(f"Clip Studio HD genere : {round(final_size / (1024*1024), 2)} Mo")
    shutil.copy2(FINAL_CLIP, FINAL_ONEDRIVE)
    # Copie de compatibilite
    shutil.copy2(FINAL_CLIP, r"O:\OneDrive\Pictures\IA\Contenue\clip_nexura_domina_v1_studio_60s.mp4")
    print(f"Copie reussie vers OneDrive : {FINAL_ONEDRIVE}")
else:
    print(f"Erreur muxing : {mux_proc.stderr}")

print("SUCCES_TOTAL_NEXURA")

