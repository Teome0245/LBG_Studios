#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Séquenceur live autonome pour jouer la chorégraphie Nexura Domina
directement sur l'avatar de bureau Lia (LBG Compagnon Desktop).
Exécuté localement sur Windows (.10) via Python 3.14.
"""

import time
import json
import urllib.request
import sys

AVATAR_CMD_URL = "http://127.0.0.1:8765/avatar/command"
LOG_FILE = "C:/Agent_IA/choreo_live.log"

MOTIONS = [
    {"start": 0.00, "end": 3.52, "pose": "Female Dance Pose1.vrma", "name": "Intro Diva Mystique"},
    {"start": 3.40, "end": 9.40, "pose": "Idle.vrma", "name": "Suspension Mystique"},
    {"start": 9.34, "end": 12.38, "pose": "Samba Dancing1.vrma", "name": "Premiers Pas Samba"},
    {"start": 12.44, "end": 14.40, "pose": "Jazz Dancing3.vrma", "name": "Transition Jazz"},
    {"start": 14.44, "end": 25.28, "pose": "Bellydancing.vrma", "name": "Danse Orientale Couplet"},
    {"start": 25.33, "end": 70.29, "pose": "samba.vrma", "name": "Grande Samba Chorégraphiée"},
    {"start": 70.41, "end": 72.25, "pose": "jump.vrma", "name": "Saut Énergique"},
    {"start": 72.28, "end": 74.56, "pose": "Pro_Magic_Pack_Standing 2H Cast Spell 01.vrma", "name": "Incantation Magique 2 Mains"},
    {"start": 74.55, "end": 76.63, "pose": "Pro_Magic_Pack_Standing 2H Magic Area Attack 01.vrma", "name": "Attaque de Zone Magique"},
    {"start": 76.68, "end": 81.40, "pose": "Dwarf Idle.vrma", "name": "Posture Puissance"},
    {"start": 81.45, "end": 83.11, "pose": "Pro_Magic_Pack_standing 1H cast spell 01.vrma", "name": "Sort 1 Main Rapide"},
    {"start": 83.10, "end": 86.83, "pose": "Air Squat Bent Arms.vrma", "name": "Squat Fitness Aérien"},
    {"start": 86.83, "end": 92.51, "pose": "Crazy Gesture.vrma", "name": "Geste Folie Scénique"},
    {"start": 92.51, "end": 110.47, "pose": "Hip Hop Dancing3.vrma", "name": "Grand Solo Hip-Hop"},
    {"start": 110.53, "end": 129.85, "pose": "Bellydancing.vrma", "name": "Ondulation Danse du Ventre"},
    {"start": 129.83, "end": 130.35, "pose": "Female Dance Pose.vrma", "name": "Pose Finale 1"},
    {"start": 130.92, "end": 131.32, "pose": "Female Dance Pose1.vrma", "name": "Pose Finale 2"},
    {"start": 131.94, "end": 132.34, "pose": "Female Dance Pose.vrma", "name": "Pose Finale 3"},
    {"start": 133.05, "end": 144.09, "pose": "Hip Hop Dancing3.vrma", "name": "Drop Hip-Hop 3"},
    {"start": 144.13, "end": 148.21, "pose": "Taunt.vrma", "name": "Provocation Scénique Diva"},
    {"start": 148.12, "end": 150.73, "pose": "Pro_Magic_Pack_Standing 2H Magic Area Attack 02.vrma", "name": "Climax Magique Zone"},
    {"start": 150.70, "end": 157.61, "pose": "Dwarf Idle.vrma", "name": "Outro Finale Imposante"}
]

EXPRESSIONS = [
    {"start": 0.00, "end": 9.10, "mood": "serene"},
    {"start": 9.13, "end": 12.49, "mood": "serene"},
    {"start": 12.46, "end": 14.20, "mood": "happy"},
    {"start": 14.21, "end": 23.53, "mood": "serene"},
    {"start": 23.50, "end": 31.38, "mood": "happy"},
    {"start": 31.38, "end": 37.18, "mood": "happy"},
    {"start": 37.15, "end": 42.51, "mood": "serene"},
    {"start": 42.46, "end": 52.58, "mood": "happy"},
    {"start": 52.66, "end": 70.74, "mood": "serene"},
    {"start": 70.76, "end": 71.84, "mood": "happy"},
    {"start": 71.91, "end": 79.19, "mood": "serene"},
    {"start": 79.19, "end": 89.47, "mood": "happy"},
    {"start": 89.52, "end": 90.72, "mood": "serene"},
    {"start": 90.67, "end": 108.99, "mood": "happy"},
    {"start": 108.97, "end": 110.57, "mood": "serene"},
    {"start": 110.52, "end": 112.01, "mood": "happy"},
    {"start": 112.00, "end": 112.92, "mood": "serene"},
    {"start": 113.13, "end": 114.12, "mood": "happy"},
    {"start": 114.25, "end": 115.44, "mood": "serene"},
    {"start": 115.44, "end": 116.64, "mood": "happy"},
    {"start": 116.63, "end": 117.93, "mood": "serene"},
    {"start": 117.90, "end": 119.12, "mood": "happy"},
    {"start": 119.20, "end": 157.61, "mood": "serene"}
]

def log(msg):
    ts = time.strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{ts} {msg}\n"
    print(line, end="")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass

def send_cmd(cmd, detail=None):
    payload = {"cmd": cmd}
    if detail:
        payload["detail"] = detail
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        AVATAR_CMD_URL,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        log(f"Erreur envoi {cmd}: {e}")
        return None

def main():
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("=== DEMARRAGE DU SPECTACLE CHOREGRAPHIQUE NEXURA DOMINA ===\n")

    log("Initialisation : passage en plein corps et salutation...")
    send_cmd("set_mood", {"mood": "happy"})
    send_cmd("set_pose", {"pose": "wave", "holdMs": 2500})
    time.sleep(2.5)

    log("3... 2... 1... Lancement de la séquence chorégraphique !")
    t_start = time.perf_counter()

    motion_idx = 0
    expr_idx = 0
    total_motions = len(MOTIONS)
    total_exprs = len(EXPRESSIONS)

    while motion_idx < total_motions:
        now = time.perf_counter() - t_start

        # Gestion des expressions
        if expr_idx < total_exprs and now >= EXPRESSIONS[expr_idx]["start"]:
            e = EXPRESSIONS[expr_idx]
            send_cmd("set_mood", {"mood": e["mood"]})
            expr_idx += 1

        # Gestion des mouvements
        m = MOTIONS[motion_idx]
        if now >= m["start"]:
            duration_ms = int((m["end"] - m["start"]) * 1000)
            log(f"[{now:6.2f}s] ({motion_idx+1}/{total_motions}) Lancement : {m['name']} ({m['pose']}) pour {duration_ms}ms")
            send_cmd("set_pose", {"pose": m["pose"], "holdMs": duration_ms + 400})
            motion_idx += 1

        time.sleep(0.02)

    # Attendre la fin du dernier mouvement (jusqu'à 157.6s)
    while True:
        now = time.perf_counter() - t_start
        if now >= 157.61:
            break
        time.sleep(0.1)

    log(f"[{time.perf_counter() - t_start:6.2f}s] Fin du spectacle ! Lia salue et reprend son repos.")
    send_cmd("set_mood", {"mood": "happy"})
    send_cmd("set_pose", {"pose": "bow", "holdMs": 3500})
    time.sleep(3.6)
    send_cmd("set_pose", {"pose": "idle", "holdMs": 0})
    log("Spectacle terminé avec succès !")

if __name__ == "__main__":
    main()

