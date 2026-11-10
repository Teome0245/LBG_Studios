"""cron_daily_publisher.py — Planificateur de publication automatique quotidienne (2x par jour).

1. Parcourt `topics_backlog.json` pour trouver le prochain sujet en attente.
2. Lance `content_bot.py` avec upload YouTube automatique.
3. Copie le fichier vidéo vers `O:\\OneDrive\\Pictures\\IA\\Contenue\\`.
4. Crée un fichier texte d'accompagnement (.txt) avec la légende TikTok et les hashtags prêts pour le copier-coller.
5. Met à jour `topics_backlog.json` avec le lien YouTube et l'horodatage.
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("daily_publisher")

ENGINE_DIR = Path(__file__).resolve().parent
BACKLOG_FILE = ENGINE_DIR / "topics_backlog.json"
VENV_PYTHON = Path(__file__).resolve().parents[2] / "packages" / "cortex" / ".venv" / "bin" / "python"


def load_backlog() -> list[dict]:
    if not BACKLOG_FILE.exists():
        return []
    with open(BACKLOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_backlog(backlog: list[dict]) -> None:
    with open(BACKLOG_FILE, "w", encoding="utf-8") as f:
        json.dump(backlog, f, indent=2, ensure_ascii=False)


def run_daily_drop() -> None:
    backlog = load_backlog()
    next_item = None
    for item in backlog:
        if item.get("status") == "pending":
            next_item = item
            break

    if not next_item:
        logger.info("Tous les sujets du backlog ont été publiés ! Ajout d'un sujet automatique...")
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        next_item = {
            "id": len(backlog) + 1,
            "topic": f"Ingénierie locale et agents autonomes chez LBG Studios ({now_str})",
            "category": "Tech & Dev",
            "status": "pending",
        }
        backlog.append(next_item)

    topic = next_item["topic"]
    logger.info("=== Lancement du Drop Quotidien pour : '%s' ===", topic)

    cmd = [
        str(VENV_PYTHON),
        str(ENGINE_DIR / "content_bot.py"),
        "--topic",
        topic,
        "--youtube",
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        logger.error("Échec de content_bot.py :\n%s\n%s", res.stdout, res.stderr)
        sys.exit(res.returncode)

    # Récupérer les données de sortie JSON
    yt_url = None
    mp4_name = None
    title = topic
    for line in res.stdout.splitlines():
        if "https://www.youtube.com/shorts/" in line:
            parts = line.split("https://www.youtube.com/shorts/")
            if len(parts) > 1:
                vid_id = parts[1].strip().split()[0].replace('"', "").replace(",", "")
                yt_url = f"https://www.youtube.com/shorts/{vid_id}"

    # Recherche du dernier drop généré
    drops = sorted((ENGINE_DIR / "output").glob("drop_*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if drops:
        mp4_files = list(drops[0].glob("*_tiktok.mp4"))
        if mp4_files:
            mp4_name = mp4_files[0].name

    # Mise à jour du backlog
    next_item["status"] = "published"
    next_item["published_at"] = datetime.datetime.now().isoformat()
    next_item["youtube_url"] = yt_url
    save_backlog(backlog)

    # Création du fichier mémo TikTok sur Windows (OneDrive)
    if mp4_name:
        txt_content = (
            f"TITRE : {title}\n"
            f"FICHIER VIDÉO : {mp4_name}\n"
            f"LIEN YOUTUBE SHORTS : {yt_url}\n"
            f"DATE : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            "--- LÉGENDE TIKTOK (À COPIER-COLLER) ---\n"
            f"{title}\n\n"
            "Vidéo 100% générée par le Studio Content Engine de LBG Studios (0€ Cloud).\n"
            "#fyp #ia #tech #dev #godotengine #opensource #lbgstudios\n"
        )
        try:
            import httpx
            with httpx.Client(timeout=5.0) as client:
                txt_filename = mp4_name.replace(".mp4", "_tiktok_memo.txt")
                client.post(
                    "http://192.168.0.10:5005/execute",
                    json={
                        "action": "write_file",
                        "parameters": {
                            "path": f"O:\\OneDrive\\Pictures\\IA\\Contenue\\{txt_filename}",
                            "content": txt_content,
                        },
                    },
                )
                logger.info("Fiche mémo TikTok créée : O:\\OneDrive\\Pictures\\IA\\Contenue\\%s", txt_filename)
        except Exception as e:
            logger.warning("Échec écriture mémo Windows : %s", e)

    logger.info("=== Drop Quotidien Terminé avec Succès ===")
    logger.info("YouTube : %s", yt_url)


if __name__ == "__main__":
    run_daily_drop()

