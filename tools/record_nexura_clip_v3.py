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
RAW_VIDEO = r"C:\Agent_IA\nexura_raw_v3.mp4"
FINAL_CLIP = r"C:\Agent_IA\clip_nexura_domina_v3_perfect.mp4"
FINAL_ONEDRIVE = r"O:\OneDrive\Pictures\IA\Contenue\clip_nexura_domina_v3_perfect.mp4"

URL = "http://192.168.0.143:8766/render_clip_nexura.html"
PROFILE = r"C:\Agent_IA\studio_render_profile"

print("[1/5] Fermeture prealable des overlays...")
subprocess.run(["taskkill", "/F", "/IM", "electron.exe", "/T"], capture_output=True)
time.sleep(1)

print("[2/5] Lancement du Studio WebGL Kiosk Plein Écran (Zéro Bureau)...")
chrome_cmd = [
    CHROME,
    f"--app={URL}",
    "--kiosk",
    "--autoplay-policy=no-user-gesture-required",
    f"--user-data-dir={PROFILE}",
    "--no-first-run",
    "--no-default-browser-check"
]
chrome_proc = subprocess.Popen(chrome_cmd)
print(f"Chrome Kiosk lance (PID={chrome_proc.pid}), attente chargement complet du VRM (4.0s)...")
time.sleep(4.0)

# Sur un écran 1920x1080, le cadre 540x960 centré est exactement à X=690, Y=60
print("[3/5] Demarrage de l'enregistrement FFmpeg gdigrab (Zone Centrale 540x960 @ 30 FPS)...")
ffmpeg_rec_cmd = [
    FFMPEG,
    "-f", "gdigrab",
    "-framerate", "30",
    "-offset_x", "690",
    "-offset_y", "60",
    "-video_size", "540x960",
    "-t", "158.0",
    "-i", "desktop",
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-pix_fmt", "yuv420p",
    "-y",
    RAW_VIDEO
]
# Lancement de l'enregistrement FFmpeg
rec_proc = subprocess.Popen(ffmpeg_rec_cmd)
time.sleep(0.5)

# Déclenchement du clap de synchronisation studio via Espace sur la fenêtre
try:
    ps_focus = r"$wshell = New-Object -ComObject Wscript.Shell; $wshell.AppActivate('Nexura Domina'); Start-Sleep -Milliseconds 80; $wshell.SendKeys(' ')"
    subprocess.run(["powershell", "-NoProfile", "-Command", ps_focus], capture_output=True)
    print("Clap de synchronisation envoyé (Touche Espace activee).")
except Exception as e:
    print(f"Note synchronisation: {e}")

rec_proc.wait()
print(f"Enregistrement termine (code {rec_proc.returncode}).")

print("[4/5] Fermeture de Chrome et relance Compagnon...")
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

print("[5/5] Muxing master audio + Lanczos Upscale HD 1080x1920 (qualite studio crf 17)...")
mux_cmd = [
    FFMPEG,
    "-i", RAW_VIDEO,
    "-i", AUDIO_PATH,
    "-filter_complex", "[0:v]scale=1080:1920:flags=lanczos[v]",
    "-map", "[v]",
    "-map", "1:a",
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-crf", "17",
    "-c:a", "aac",
    "-b:a", "320k",
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

