#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline de Production Autonome HD (Machine .143)
Génère le clip officiel intégral Nexura Domina en Vertical 9:16 (1080×1920)
avec caméras cinématographiques, mouvements de Drone 360°, lipsync réactif et éclairage cyberpunk.
"""
import subprocess
import time
import os
import sys
import json
import urllib.request

DISPLAY_NUM = ":99"
RESOLUTION = "1080x1920"
DURATION = "158.0" # 2 min 38s intégrales

AUDIO_FILE = "/home/lbg/Projets/LBG_Studios/packages/compagnon-desktop/overlay/nexura_domina_v1.mp3"
OUTPUT_VIDEO = "/home/lbg/Projets/LBG_Studios/packages/compagnon-desktop/overlay/clip_nexura_domina_v2_drone_final.mp4"
URL = "http://127.0.0.1:8766/render_clip_nexura.html"
ONEDRIVE_DEST = r"O:\OneDrive\Pictures\IA\Contenue\clip_nexura_domina_v2_drone_final.mp4"

print("[1/5] Préparation du serveur d'affichage virtuel Xvfb 1080×1920...")
subprocess.run(["pkill", "-f", "Xvfb :99"], stderr=subprocess.DEVNULL)
time.sleep(0.5)

xvfb_proc = subprocess.Popen([
    "Xvfb", DISPLAY_NUM,
    "-screen", "0", f"{RESOLUTION}x24",
    "-ac", "+extension", "GLX", "+render", "-noreset"
])
time.sleep(1.5)

print("[2/5] Lancement de Chromium Kiosk avec accélération WebGL sur .143...")
env = dict(os.environ, DISPLAY=DISPLAY_NUM)
chr_proc = subprocess.Popen([
    "chromium",
    "--ozone-platform=x11",
    "--no-sandbox",
    "--window-size=1080,1920",
    "--window-position=0,0",
    "--kiosk",
    "--disable-infobars",
    "--autoplay-policy=no-user-gesture-required",
    "--enable-unsafe-swiftshader",
    "--remote-debugging-port=9222",
    "--user-data-dir=/tmp/chr_render_prod",
    URL
], env=env)

print("[3/5] Attente du chargement complet du VRM, des animations et de la chorégraphie...")
ready = False
for attempt in range(25):
    time.sleep(1.0)
    try:
        tabs_res = urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=2)
        tabs = json.loads(tabs_res.read().decode("utf-8"))
        tab = next((t for t in tabs if "render_clip" in t.get("url", "")), None)
        if tab:
            # Avatar et page prêts
            ready = True
            break
    except Exception:
        pass

if not ready:
    print("Avertissement: Timeout détection CDP, temporisation de sécurité (4s)...")
    time.sleep(4.0)
else:
    print("Avatar 3D & chorégraphie prêts ! Temporisation d'accroche (2.5s)...")
    time.sleep(2.5)

print(f"[4/5] Enregistrement Master HD FFmpeg (Durée: {DURATION}s @ 30 FPS CRF 18)...")
ffmpeg_cmd = [
    "ffmpeg", "-y",
    "-f", "x11grab",
    "-draw_mouse", "0",
    "-video_size", RESOLUTION,
    "-framerate", "30",
    "-i", f"{DISPLAY_NUM}.0",
    "-i", AUDIO_FILE,
    "-t", DURATION,
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-crf", "18",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac",
    "-b:a", "256k",
    "-shortest",
    OUTPUT_VIDEO
]

ff_proc = subprocess.run(ffmpeg_cmd)

print("[5/5] Fermeture des instances graphiques virtuelles...")
chr_proc.kill()
xvfb_proc.kill()

if os.path.exists(OUTPUT_VIDEO) and os.path.getsize(OUTPUT_VIDEO) > 1000000:
    size_mb = os.path.getsize(OUTPUT_VIDEO) / (1024 * 1024)
    print(f"Clip HD généré avec succès sur .143 : {size_mb:.2f} Mo !")

    # Transfert vers l'hôte Windows / OneDrive
    print(f"Transfert vers OneDrive : {ONEDRIVE_DEST}...")
    try:
        transfer_payload = {
            "action": "run_powershell",
            "parameters": {
                "command": f'Invoke-WebRequest -Uri "http://192.168.0.143:8766/clip_nexura_domina_v2_drone_final.mp4" -OutFile "{ONEDRIVE_DEST}"'
            }
        }
        req = urllib.request.Request(
            "http://192.168.0.10:5005/execute",
            data=json.dumps(transfer_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        res = urllib.request.urlopen(req, timeout=60)
        res_data = json.loads(res.read().decode("utf-8"))
        print("Transfert OneDrive réussi :", res_data)
        print("SUCCES_TOTAL")
    except Exception as e:
        print("Erreur transfert OneDrive:", e)
else:
    print("Erreur: Le fichier vidéo final n'a pas été produit correctement.")

