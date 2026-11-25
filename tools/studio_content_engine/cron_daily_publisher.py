"""cron_daily_publisher.py — Planificateur autonome 5 Shorts/jour (YouTube Shorts + TikTok Studio en parallèle).

1. Parcourt `topics_backlog.json` (couvrant O1 Compagnon/Gladys, O2 MMO Prime, O3 Bots IA, Hardware & Clips 3D).
2. Alterne automatiquement les Shorts Tech/MMO parlés (`stage3d`) et les Clips Musicaux 3D (`music3d`).
3. Publie systématiquement sur YouTube Shorts (`@lbg-p8k`) ET sur TikTok Studio en parallèle (avec retry de sécurité).
4. Enregistre `youtube_url` ET `tiktok_status` dans `topics_backlog.json`.
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


# Couverture complète de tous les piliers LBG Studios (O1, O2, O3, Hardware & Clips 3D)
REPLENISH_SCHEDULE: list[dict[str, str]] = [
    {
        "topic": "Pourquoi un serveur Dell R720 à 150 € d'occasion bat les abonnements Cloud pour l'IA",
        "category": "Homelab & Hardware",
        "format": "stage3d",
    },
    {
        "topic": "LIA — Nexura Domina (Drop Electro 3D) | Performance VRM",
        "category": "Clip 3D & Chorégraphie VRM",
        "format": "music3d",
        "music_preset": "nexura_drop_highlight",
    },
    {
        "topic": "Comment nos 10 joueurs IA vivent et commercent dans notre MMO 3D sans tricher",
        "category": "Pilier O3 Joueurs IA",
        "format": "stage3d",
    },
    {
        "topic": "Piloter Windows et Linux par IA sans jamais voler la souris grâce à l'accessibilité native",
        "category": "Pilier O1 Compagnon & Bureau",
        "format": "stage3d",
    },
    {
        "topic": "LIA — Cantina Lost Heaven (Danses SWG 3D) | Mocap VRM",
        "category": "Chorégraphie MMO & VRM",
        "format": "music3d",
        "music_preset": "swg_cantina_groove",
    },
    {
        "topic": "Artisanat Star Wars Galaxies : pourquoi des minerais notés de 1 à 1000 changent tout",
        "category": "Pilier O2 MMO Prime",
        "format": "stage3d",
    },
    {
        "topic": "Faire tourner un modèle MoE 30B sur processeur Xeon sans aucune carte graphique",
        "category": "IA Locale & Benchmarks",
        "format": "stage3d",
    },
    {
        "topic": "LIA — Synthwave Overdrive (Concert 3D) | Studio LBG",
        "category": "Live Virtuel Three-VRM",
        "format": "music3d",
        "music_preset": "synthwave_energy_show",
    },
    {
        "topic": "Graphe de topologie live : surveiller 17 services et conteneurs Proxmox en 200 millisecondes",
        "category": "Gladys & Observabilité",
        "format": "stage3d",
    },
    {
        "topic": "Basculer instantanément entre vue 2D tactique et monde Full 3D PBR à 60 FPS sous Godot 4",
        "category": "Moteur Godot 4 & 3D",
        "format": "stage3d",
    },
    {
        "topic": "LIA — Nexura Domina Climax (Solo Scénique 3D) | LBG Studios",
        "category": "Clip Officiel 3D",
        "format": "music3d",
        "music_preset": "nexura_climax_encore",
    },
    {
        "topic": "Auto-héberger son serveur Mail en Rust avec Stalwart et DNS AdGuard pilotés par IA",
        "category": "Self-Hosting & Réseau",
        "format": "stage3d",
    },
    {
        "topic": "Le système de Karma et de Renaissance inspiré de La Quatrième Prophétie dans notre MMO",
        "category": "Game Design & T4C",
        "format": "stage3d",
    },
    {
        "topic": "Découper la mémoire d'un agent IA en silos JSON de 1,5 Ko pour éliminer les hallucinations",
        "category": "RAG & Cerveau Gladys",
        "format": "stage3d",
    },
]


def replenish_backlog_if_needed(backlog: list[dict[str, Any]]) -> None:
    pending = [item for item in backlog if item.get("status") == "pending"]
    if len(pending) >= 5:
        return

    logger.info("Backlog Shorts bas (%d en attente). Réapprovisionnement multi-piliers...", len(pending))
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

    if added == 0:
        cycle_num = (len(backlog) // max(1, len(REPLENISH_SCHEDULE))) + 1
        for entry in REPLENISH_SCHEDULE[:6]:
            cur_id += 1
            new_item = {
                "id": cur_id,
                "topic": f"{entry['topic']} #{cycle_num}",
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

    logger.info("=== Lancement du Drop 3D [%s] (YouTube + TikTok //) : '%s' ===", style, topic)

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
    tiktok_status = "unknown"
    mp4_path: Path | None = None

    # Extraire le JSON récapitulatif de fin de content_bot.py
    try:
        sep = "=" * 50
        if sep in res.stdout:
            blocks = [b.strip() for b in res.stdout.split(sep) if b.strip().startswith("{")]
            if blocks:
                parsed = json.loads(blocks[-1])
                yt_url = (parsed.get("youtube") or {}).get("video_url")
                tiktok_status = (parsed.get("tiktok") or {}).get("status", "unknown")
                if parsed.get("mp4_path"):
                    mp4_path = Path(parsed["mp4_path"])
    except Exception as exc:
        logger.warning("Lecture JSON sortie content_bot : %s", exc)

    # Filet de sécurité TikTok parallèle : si le 1er essai Playwright a échoué, relancer une fois directement !
    if tiktok_status not in ("success", "ok") and mp4_path and mp4_path.exists():
        logger.warning("Statut TikTok initial = '%s' -> tentative de rattrapage immédiat sur TikTok Studio...", tiktok_status)
        try:
            sys.path.insert(0, str(ENGINE_DIR))
            from tiktok_publisher import upload_local_tiktok

            tags = (
                "#fyp #vtuber #3d #cyberpunk #aiidol #godotengine #lbgstudios"
                if style == "music3d"
                else "#fyp #ia #tech #homelab #dev #godotengine #3d #lbgstudios"
            )
            retry_tt = upload_local_tiktok(mp4_path, caption=f"{topic} {tags}")
            tiktok_status = retry_tt.get("status", tiktok_status)
        except Exception as exc:
            logger.error("Échec retry TikTok : %s", exc)

    next_item["status"] = "published"
    next_item["format"] = style
    next_item["published_at"] = datetime.datetime.now().isoformat()
    next_item["youtube_url"] = yt_url
    next_item["tiktok_status"] = tiktok_status
    save_backlog(backlog)

    logger.info("=== Drop Quotidien Terminé : YouTube=%s | TikTok=%s ===", yt_url, tiktok_status)


if __name__ == "__main__":
    run_daily_drop()
