#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LBG Studios - API HTTP Locale du Studio Musical & Vocale IA (Port 8099)
Fournit les endpoints pour composer de la musique depuis l'Atelier 3D (choreographer.html).
0 € Cloud - Traitement 100% local sur .143 et déploiement automatique sur .140.
"""

import os
import sys
import json
import time
import threading
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Import des styles depuis le générateur V3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from studio_music_generator_v3 import MUSIC_STYLES

PORT = 8099

# État global de génération
GENERATION_STATE = {
    "status": "idle",       # "idle", "generating", "done", "error"
    "progress": 0,          # 0 à 100
    "step": "",             # Description de l'étape courante
    "track_id": None,
    "title": None,
    "audio_url": None,
    "bpm": 128,
    "duration": 30,
    "style": "cyberpunk",
    "voice": "diva",
    "started_at": 0,
    "error_message": None
}

STATE_LOCK = threading.Lock()

def update_state(**kwargs):
    with STATE_LOCK:
        for k, v in kwargs.items():
            GENERATION_STATE[k] = v

def run_music_generation_task(style_key, title, duration, voice):
    try:
        update_state(
            status="generating",
            progress=5,
            step="Initialisation du studio...",
            style=style_key,
            voice=voice,
            duration=duration,
            started_at=time.time(),
            error_message=None
        )

        cfg = MUSIC_STYLES.get(style_key, MUSIC_STYLES["cyberpunk"])
        track_title = title if title and title.strip() else cfg["default_title"]
        track_id = f"lia_{style_key}_{duration}s"
        bpm = cfg["bpm"]

        update_state(progress=15, step="Écriture des paroles scénarisées...")
        # Lancer le script v3 en sous-processus unifié
        cmd = [
            os.path.abspath(".venv_audio/bin/python3"),
            "-u",
            os.path.abspath("tools/studio_music_generator_v3.py"),
            "--style", style_key,
            "--duration", str(duration),
            "--voice", voice
        ]
        if title:
            cmd.extend(["--title", track_title])

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        update_state(progress=30, step=f"Génération instrumentale MusicGen ({duration}s)...")

        # Lire la sortie pour ajuster la jauge
        for line in proc.stdout:
            line_str = line.strip()
            print(f"[API StudioGen] {line_str}")
            if "[1/4]" in line_str:
                update_state(progress=35, step="Composition des pistes MusicGen...")
            elif "Segment" in line_str:
                update_state(progress=50, step="Synthèse audio multicanale...")
            elif "[2/4]" in line_str:
                update_state(progress=70, step="Synthèse vocale des strophes de chant...")
            elif "[3/4]" in line_str:
                update_state(progress=85, step=f"Mixage & Mastering studio (Effet {voice.upper()})...")
            elif "[4/4]" in line_str:
                update_state(progress=95, step="Déploiement vers l'Atelier 3D...")

        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError(f"Le générateur s'est arrêté avec le code {proc.returncode}")

        filename = f"{track_id}_master.wav"
        audio_url = f"http://192.168.0.140/audio/{filename}"

        update_state(
            status="done",
            progress=100,
            step="Composition terminée et intégrée !",
            track_id=track_id,
            title=track_title,
            audio_url=audio_url,
            bpm=bpm,
            duration=duration
        )
        print(f"✦ [API StudioGen] Succès : {audio_url}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        update_state(
            status="error",
            progress=0,
            step="Erreur de génération",
            error_message=str(e)
        )

class StudioMusicHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/api/music/styles", "/styles"):
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            data = {
                "styles": MUSIC_STYLES,
                "voices": [
                    {"id": "diva", "label": "Diva Scénique (Clarté & Brillance Studio)"},
                    {"id": "vocoder", "label": "Cyber Vocoder (Robotique Daft Punk)"},
                    {"id": "autotune", "label": "Autotune Pop (Moderne & Présence)"},
                    {"id": "whisper", "label": "Intime Whisper (Feutré & ASMR)"}
                ],
                "durations": [15, 30, 60]
            }
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

        elif path in ("/api/music/status", "/status"):
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            with STATE_LOCK:
                data = dict(GENERATION_STATE)
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

        elif path in ("/api/music/tracks", "/tracks"):
            # Liste des morceaux disponibles
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            audio_dir = "packages/compagnon-desktop/overlay/audio"
            tracks = []
            if os.path.exists(audio_dir):
                for f in sorted(os.listdir(audio_dir)):
                    if f.endswith("_master.wav") or f.endswith("_master_60s.wav"):
                        tracks.append({
                            "filename": f,
                            "url": f"http://192.168.0.140/audio/{f}",
                            "size_bytes": os.path.getsize(os.path.join(audio_dir, f))
                        })
            self.wfile.write(json.dumps({"tracks": tracks}).encode("utf-8"))

        else:
            self.send_response(404)
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(b'{"error": "Endpoint inconnu"}')

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/api/music/generate", "/generate"):
            with STATE_LOCK:
                if GENERATION_STATE["status"] == "generating":
                    self.send_response(409)
                    self._send_cors_headers()
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "error": "Une génération musicale est déjà en cours dans le studio.",
                        "state": GENERATION_STATE
                    }).encode("utf-8"))
                    return

            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len).decode("utf-8")
            try:
                params = json.loads(post_body) if post_body else {}
            except Exception:
                params = {}

            style_key = params.get("style", "cyberpunk")
            title = params.get("title", None)
            duration = int(params.get("duration", 30))
            voice = params.get("voice", "diva")

            # Lancer le thread de génération
            th = threading.Thread(
                target=run_music_generation_task,
                args=(style_key, title, duration, voice),
                daemon=True
            )
            th.start()

            self.send_response(202)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({
                "message": "Génération musicale initiée avec succès",
                "params": {"style": style_key, "duration": duration, "voice": voice, "title": title}
            }).encode("utf-8"))
        else:
            self.send_response(404)
            self._send_cors_headers()
            self.end_headers()

def main():
    server_address = ("0.0.0.0", PORT)
    httpd = HTTPServer(server_address, StudioMusicHandler)
    print(f"✦ [STUDIO MUSIC API] En écoute sur http://0.0.0.0:{PORT}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt du serveur Studio Music API.")

if __name__ == "__main__":
    main()
