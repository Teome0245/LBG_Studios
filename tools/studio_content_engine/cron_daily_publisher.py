"""cron_daily_publisher.py — Planificateur autonome TikTok & YouTube Shorts (Alternance Scène 3D Tech + Clips Musicaux 3D).

1. Parcourt `topics_backlog.json` pour trouver le prochain sujet `pending` (et réapprovisionne sans jamais tomber à sec).
2. Alterne automatiquement les Shorts Tech/MMO parlés en scène 3D (`--style stage3d`) et les Clips Musicaux / Chorégraphies 3D (`--style music3d`).
3. Lance `content_bot.py` avec publication YouTube Shorts et TikTok Studio.
4. Synchronise la vidéo et la fiche mémo vers `O:\\OneDrive\\Pictures\\IA\\Contenue\\` si `.10` est actif.
"""

from __future__ import annotations

import datetime
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("daily_publisher")

ENGINE_DIR = Path(__file__).resolve().parent
BACKLOG_FILE = ENGINE_DIR / "topics_backlog.json"
VENV_PYTHON = Path(__file__).resolve().parents[2] / "packages" / "cortex" / ".venv" / "bin" / "python"


def load_backlog() -> list[dict[str, Any]]:
    if not BACKLOG_FILE.exists():
        return []
    with open(BACKLOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_backlog(backlog: list[dict[str, Any]]) -> None:
    with open(BACKLOG_FILE, "w", encoding="utf-8") as f:
        json.dump(backlog, f, indent=2, ensure_ascii=False)


# Catalogue alterné : Shorts Tech/MMO parlés en scène 3D + Clips Musicaux / Chorégraphies 3D
REPLENISH_SCHEDULE: list[dict[str, str]] = [
    {
        "topic": "Comment notre forge d'intentions IA apprend sans jamais exposer le système",
        "category": "IA Locale & Sécurité",
        "format": "stage3d",
    },
    {
        "topic": "LIA — Nexura Domina (Drop Electro 3D) | Performance VRM",
        "category": "Clip 3D & Chorégraphie VRM",
        "format": "music3d",
        "music_preset": "nexura_drop_highlight",
    },
    {
        "topic": "Pourquoi fusionner Star Wars Galaxies Pre-CU et La 4ème Prophétie en 3D",
        "category": "MMO & Game Design",
        "format": "stage3d",
    },
    {
        "topic": "LIA — Cyberpunk Protocol (Live 3D 128 BPM) | LBG Studios",
        "category": "Performance Musicale IA",
        "format": "music3d",
        "music_preset": "cyberpunk_protocol_30s",
    },
    {
        "topic": "Comment passer de 30 à 60 FPS sur Godot 4 en coupant le brouillard volumétrique",
        "category": "Moteur Godot 4 & Perf",
        "format": "stage3d",
    },
    {
        "topic": "LIA — Cantina Lost Heaven (Danses SWG 3D) | Mocap VRM",
        "category": "Chorégraphie MMO & VRM",
        "format": "music3d",
        "music_preset": "swg_cantina_groove",
    },
    {
        "topic": "Isoler du code généré par IA dans une sandbox Bubblewrap sans réseau",
        "category": "DevSecOps & Agents IA",
        "format": "stage3d",
    },
    {
        "topic": "LIA — Synthwave Overdrive (Concert 3D) | 100% Local",
        "category": "Live Virtuel Three-VRM",
        "format": "music3d",
        "music_preset": "synthwave_energy_show",
    },
    {
        "topic": "Comment convertir les danses binaires de Star Wars Galaxies vers Three-VRM",
        "category": "Animation 3D & Reverse",
        "format": "stage3d",
    },
    {
        "topic": "LIA — Nexura Domina Climax (Solo Scénique 3D) | LBG Studios",
        "category": "Clip Officiel 3D",
        "format": "music3d",
        "music_preset": "nexura_climax_encore",
    },
    {
        "topic": "Découper le cerveau d'un agent IA en silos de connaissances JSON légers",
        "category": "Architecture RAG & LLM",
        "format": "stage3d",
    },
    {
        "topic": "Synchroniser vue 2D tactique et monde Full 3D en temps réel sous Godot 4",
        "category": "Architecture MMO 3D",
        "format": "stage3d",
    },
]


def replenish_backlog_if_needed(backlog: list[dict[str, Any]]) -> None:
    """Réapprovisionne le backlog avec alternance Tech 3D / Clip Musical 3D sans jamais tomber à sec."""
    pending = [item for item in backlog if item.get("status") == "pending"]
    if len(pending) >= 4:
        return

    logger.info("Backlog bas (%d sujets en attente). Réapprovisionnement alterné 3D...", len(pending))
    existing_topics = {item.get("topic", "").lower().strip() for item in backlog}
    cur_id = max((int(item.get("id", 0)) for item in backlog), default=0)

    added = 0
    for entry in REPLENISH_SCHEDULE:
        key = entry["topic"].lower().strip()
        if key not in existing_topics:
            cur_id += 1
            new_item: dict[str, Any] = {
                "id": cur_id,
                "topic": entry["topic"],
                "category": entry["category"],
                "format": entry["format"],
                "status": "pending",
            }
            if "music_preset" in entry:
                new_item["music_preset"] = entry["music_preset"]
            backlog.append(new_item)
            existing_topics.add(key)
            added += 1

    # Si tout le catalogue initial a déjà été publié, générer un nouveau cycle numéroté
    if added == 0:
        cycle_num = (len(backlog) // max(1, len(REPLENISH_SCHEDULE))) + 1
        for entry in REPLENISH_SCHEDULE[:6]:
            cur_id += 1
            suffixed_topic = f"{entry['topic']} #{cycle_num}"
            new_item = {
                "id": cur_id,
                "topic": suffixed_topic,
                "category": entry["category"],
                "format": entry["format"],
                "status": "pending",
            }
            if "music_preset" in entry:
                new_item["music_preset"] = entry["music_preset"]
            backlog.append(new_item)

    save_backlog(backlog)


def run_daily_drop() -> None:
    backlog = load_backlog()
    replenish_backlog_if_needed(backlog)

    next_item = next((item for item in backlog if item.get("status") == "pending"), None)
    if not next_item:
        logger.error("Erreur critique : aucun sujet disponible même après réapprovisionnement.")
        sys.exit(1)

    topic = next_item["topic"]
    style = next_item.get("format") or "stage3d"
    if style not in ("stage3d", "music3d", "jrpg", "standard"):
        style = "stage3d"

    logger.info("=== Lancement du Drop 3D [%s] pour : '%s' ===", style, topic)

    cmd = [
        str(VENV_PYTHON),
        str(ENGINE_DIR / "content_bot.py"),
        "--topic",
        topic,
        "--style",
        style,
        "--youtube",
        "--tiktok",
        "--pilot",
    ]
    if next_item.get("music_preset"):
        cmd += ["--music-preset", str(next_item["music_preset"])]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        logger.error("Échec de content_bot.py :\n%s\n%s", res.stdout, res.stderr)
        sys.exit(res.returncode)

    yt_url = None
    mp4_name = None
    title = topic
    for line in res.stdout.splitlines():
        if "https://www.youtube.com/shorts/" in line:
            parts = line.split("https://www.youtube.com/shorts/")
            if len(parts) > 1:
                vid_id = parts[1].strip().split()[0].replace('"', "").replace(",", "")
                yt_url = f"https://www.youtube.com/shorts/{vid_id}"

    drops = sorted((ENGINE_DIR / "output").glob("drop_*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if drops:
        mp4_files = list(drops[0].glob("*_tiktok.mp4"))
        if mp4_files:
            mp4_name = mp4_files[0].name

    next_item["status"] = "published"
    next_item["format"] = style
    next_item["published_at"] = datetime.datetime.now().isoformat()
    next_item["youtube_url"] = yt_url
    save_backlog(backlog)

    if mp4_name:
        hashtags = (
            "#fyp #vtuber #3d #cyberpunk #aiidol #godotengine #lbgstudios"
            if style == "music3d"
            else "#fyp #ia #tech #dev #godotengine #3d #opensource #lbgstudios"
        )
        txt_content = (
            f"TITRE : {title}\n"
            f"STYLE : {style}\n"
            f"FICHIER VIDÉO : {mp4_name}\n"
            f"LIEN YOUTUBE SHORTS : {yt_url}\n"
            f"DATE : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            "--- LÉGENDE TIKTOK (À COPIER-COLLER) ---\n"
            f"{title}\n\n"
            "Rendu 3D temps réel généré par le Studio Content Engine de LBG Studios (0€ Cloud).\n"
            f"{hashtags}\n"
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
            logger.warning("Écriture mémo Windows ignorée (.10 hors ligne) : %s", e)

    logger.info("=== Drop Quotidien Terminé avec Succès ===")
    logger.info("YouTube : %s", yt_url)


if __name__ == "__main__":
    run_daily_drop()
