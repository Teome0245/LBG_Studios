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


REPLENISH_IDEAS = [
    ("Pourquoi le multithreading de Godot 4 évite les freeze serveur", "Architecture & Perf"),
    ("Comment nous avons synchronisé les animations Three.js et VRM", "Frontend 3D & WebGL"),
    ("Le secret de la mémoire épisodique pour compagnons virtuels", "IA Locale & RAG"),
    ("Créer un système de combat dynamique sans lag réseau", "MMO & Game Design"),
    ("Gérer 100 000 objets sans draw-call avec MultiMeshInstance3D", "Graphisme & Shader"),
    ("Les pièges du cloud pour les studios de jeux vidéo indépendants", "Économie & Tech"),
    ("Pourquoi l'extraction d'échantillons géologiques est si addictive", "MMO & Gameplay"),
    ("Comment nous avons automatisé nos audits de code chaque nuit à 00h30", "DevOps & CI/CD"),
    ("Lia, notre avatar IA : architecture complète de son esprit 0€ cloud", "Compagnon IA"),
    ("Pourquoi nous préférons des micro-modèles 3B aux géants 70B", "IA Efficace"),
]


def replenish_backlog_if_needed(backlog: list[dict]) -> None:
    """Réapprovisionne automatiquement le backlog s'il reste moins de 5 sujets en attente."""
    pending = [item for item in backlog if item.get("status") == "pending"]
    if len(pending) >= 5:
        return

    logger.info("Backlog bas (%d sujets restants). Réapprovisionnement automatique...", len(pending))
    existing_topics = {item.get("topic", "").lower().strip() for item in backlog}
    cur_id = max((item.get("id", 0) for item in backlog), default=0)

    for topic_title, cat in REPLENISH_IDEAS:
        if topic_title.lower().strip() not in existing_topics:
            cur_id += 1
            backlog.append({
                "id": cur_id,
                "topic": topic_title,
                "category": cat,
                "status": "pending",
            })
            existing_topics.add(topic_title.lower().strip())
    save_backlog(backlog)


def run_daily_drop() -> None:
    backlog = load_backlog()
    replenish_backlog_if_needed(backlog)

    next_item = None
    for item in backlog:
        if item.get("status") == "pending":
            next_item = item
            break

    if not next_item:
        logger.error("Erreur critique : aucun sujet disponible même après réapprovisionnement.")
        sys.exit(1)

    topic = next_item["topic"]
    logger.info("=== Lancement du Drop Quotidien pour : '%s' ===", topic)

    cmd = [
        str(VENV_PYTHON),
        str(ENGINE_DIR / "content_bot.py"),
        "--topic",
        topic,
        "--youtube",
        "--tiktok",
        "--pilot",
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

