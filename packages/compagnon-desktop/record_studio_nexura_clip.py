# -*- coding: utf-8 -*-
import subprocess
import time
import os
import shutil

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME):
    CHROME = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

FFMPEG = r"C:\Users\sdesh\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0-full_build\bin\ffmpeg.EXE"
AUDIO_PATH = r"O:\OneDrive\Pictures\IA\Contenue\Nexura Domina_v1.mp3"
RAW_VIDEO = r"C:\Agent_IA\studio_nexura_raw_60s.mp4"
FINAL_CLIP = r"C:\Agent_IA\clip_nexura_domina_v1_studio_60s.mp4"
FINAL_ONEDRIVE = r"O:\OneDrive\Pictures\IA\Contenue\clip_nexura_domina_v1_studio_60s.mp4"

URL = "http://127.0.0.1:8766/studio_clip.html"
PROFILE = r"C:\Agent_IA\studio_profile"

print("[1/6] Fermeture des overlays bureau existants...")
subprocess.run(["taskkill", "/F", "/IM", "electron.exe", "/T"], capture_output=True)
subprocess.run(["taskkill", "/F", "/IM", "chrome.exe", "/T"], capture_output=True)
time.sleep(1)

# Relancer le serveur studio
print("[2/6] Demarrage du serveur local studio :8766...")
subprocess.Popen([r"C:\Python\Python314\python.exe", r"C:\Agent_IA\studio_server.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.5)

print("[3/6] Lancement du Studio WebGL Chrome (style @aeysamusic)...")
chrome_cmd = [
    CHROME,
    f"--app={URL}",
    "--window-size=556,1002",
    "--window-position=1340,30",
    "--autoplay-policy=no-user-gesture-required",
    f"--user-data-dir={PROFILE}",
    "--no-first-run",
    "--no-default-browser-check"
]
chrome_proc = subprocess.Popen(chrome_cmd)
print(f"Chrome lance (PID={chrome_proc.pid}), attente chargement VRM 3D (5s)...")
time.sleep(5.0)

print("[4/6] Demarrage de l'enregistrement FFmpeg gdigrab (60.5s @ 30 FPS)...")
# Zone utile plein ecran stage 540x960
ffmpeg_rec_cmd = [
    FFMPEG,
    "-f", "gdigrab",
    "-framerate", "30",
    "-offset_x", "1348",
    "-offset_y", "64",
    "-video_size", "540x960",
    "-t", "60.5",
    "-i", "desktop",
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-pix_fmt", "yuv420p",
    "-y",
    RAW_VIDEO
]
rec_proc = subprocess.run(ffmpeg_rec_cmd, capture_output=True, text=True)
print(f"Enregistrement termine (code {rec_proc.returncode}).")

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
    print(f"Copie reussie vers OneDrive : {FINAL_ONEDRIVE}")
else:
    print(f"Erreur muxing : {mux_proc.stderr}")

print("SUCCES_TOTAL_NEXURA")
