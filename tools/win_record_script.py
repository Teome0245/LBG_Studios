# -*- coding: utf-8 -*-
import subprocess
import time
import os
import shutil

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME):
    CHROME = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

FFMPEG = r"C:\Users\sdesh\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0-full_build\bin\ffmpeg.exe"
AUDIO_PATH = r"O:\OneDrive\Pictures\IA\Contenue\Nexura Domina_v1.mp3"
RAW_VIDEO = r"C:\Agent_IA\nexura_raw_full_v2.mp4"
FINAL_CLIP = r"C:\Agent_IA\clip_nexura_domina_v2_drone_final.mp4"
FINAL_ONEDRIVE = r"O:\OneDrive\Pictures\IA\Contenue\clip_nexura_domina_v2_drone_final.mp4"

URL = "http://192.168.0.143:8766/render_clip_nexura.html"
PROFILE = r"C:\Agent_IA\studio_render_profile"

print("[1/5] Nettoyage prealable des processus...")
subprocess.run(["taskkill", "/F", "/IM", "electron.exe", "/T"], capture_output=True)
time.sleep(1)

print("[2/5] Lancement de Chrome avec GPU NVIDIA...")
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
print(f"Chrome lance (PID={chrome_proc.pid}), attente chargement VRM & Choregraphie Drone (5s)...")
time.sleep(5.0)

print("[3/5] Demarrage de l'enregistrement FFmpeg gdigrab (158.5s @ 30 FPS - Full Track HD)...")
ffmpeg_rec_cmd = [
    FFMPEG,
    "-f", "gdigrab",
    "-framerate", "30",
    "-offset_x", "1348",
    "-offset_y", "64",
    "-video_size", "540x960",
    "-t", "158.5",
    "-i", "desktop",
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-pix_fmt", "yuv420p",
    "-y",
    RAW_VIDEO
]
rec_proc = subprocess.run(ffmpeg_rec_cmd, capture_output=True, text=True)
print(f"Enregistrement termine (code {rec_proc.returncode}).")

print("[4/5] Fermeture de Chrome...")
try:
    chrome_proc.terminate()
    subprocess.run(["taskkill", "/F", "/IM", "chrome.exe", "/T"], capture_output=True)
except Exception:
    pass

try:
    subprocess.run(["schtasks", "/Run", "/TN", "LBG-Compagnon-Desktop"], capture_output=True)
except Exception:
    pass

raw_size = os.path.getsize(RAW_VIDEO) if os.path.exists(RAW_VIDEO) else 0
print(f"Flux video brut capture : {round(raw_size / (1024*1024), 2)} Mo")

print("[5/5] Muxing master audio + Lanczos Upscale HD 1080x1920 (CRF 18)...")
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
    print(f"SUCCES_TOTAL: {FINAL_ONEDRIVE}")
else:
    print(f"Erreur muxing : {mux_proc.stderr}")

