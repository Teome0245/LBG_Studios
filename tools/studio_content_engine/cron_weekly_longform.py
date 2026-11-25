#!/usr/bin/env python3
"""cron_weekly_longform.py — Planificateur hebdomadaire (3 vidéos longues 16:9 / semaine : Mar, Jeu, Dim).

Modes :
- Par défaut (`--draft`) : prépare le prochain sujet de `longform_backlog.json` en brouillon Markdown.
- Avec `--auto` : génère, calcule la vidéo 16:9 30 FPS + miniature 1280x720 et publie sur YouTube `@LBG-p8k`.
- Réapprovisionne automatiquement `longform_backlog.json` lorsqu'il reste moins de 3 épisodes en attente.
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("weekly_longform")

ENGINE_DIR = Path(__file__).resolve().parent
BACKLOG_FILE = ENGINE_DIR / "longform_backlog.json"
VENV_PYTHON = ENGINE_DIR.parents[1] / "packages" / "cortex" / ".venv" / "bin" / "python"

REPLENISH_LONGFORM_POOL: list[dict[str, Any]] = [
    {
        "topic": "Quantification Q4_K_M vs Q8_0 vs IQ4_XS : combien d'intelligence perd vraiment une IA locale ?",
        "minutes": 6.5,
        "category": "Optimisation & LLM Local",
    },
    {
        "topic": "Monter un serveur Proxmox silencieux et basse consommation pour héberger ses IA H24",
        "minutes": 7.0,
        "category": "Homelab & Énergie",
    },
    {
        "topic": "Architecture d'un Compagnon IA 3D temps réel : Three-VRM, synthèse vocale ONNX et mémoire épisodique",
        "minutes": 6.5,
        "category": "Compagnon IA 3D",
    },
    {
        "topic": "Pourquoi la bande passante mémoire compte plus que les TFLOPS pour faire tourner un LLM chez soi",
        "minutes": 6.0,
        "category": "Hardware & Architecture",
    },
    {
        "topic": "Créer une économie vivante de troc et d'artisanat dans un MMO avec des marchands IA bornés",
        "minutes": 7.0,
        "category": "Game Design & IA",
    },
    {
        "topic": "Remplacer ses abonnements SaaS par une stack IA auto-hébergée (RAG, Mail, DNS, Agents)",
        "minutes": 7.5,
        "category": "Self-Hosting & Souveraineté",
    },
    {
        "topic": "Animer 220 mouvements mocap sur un avatar VRM dans le navigateur sans moteur lourd",
        "minutes": 5.5,
        "category": "WebGL & Animation 3D",
    },
    {
        "topic": "Automatiser la maintenance et l'auto-réparation d'un réseau Linux avec de petits modèles 3B/4B",
        "minutes": 6.5,
        "category": "DevOps & Agents Locaux",
    },
    {
        "topic": "SQLite en mode WAL face à PostgreSQL et Redis : jusqu'où peut aller un fichier unique en production ?",
        "minutes": 6.0,
        "category": "Bases de Données & Perf",
    },
    {
        "topic": "Quel PC ou Mac Mini choisir entre 500 € et 1 200 € pour débuter sérieusement en IA locale ?",
        "minutes": 8.0,
        "category": "Guide Achat Matériel",
    },
]


def replenish_longform_if_needed(backlog: list[dict[str, Any]]) -> None:
    pending = [item for item in backlog if item.get("status") == "pending"]
    if len(pending) >= 3:
        return

    logger.info("Backlog long bas (%d restants). Réapprovisionnement automatique...", len(pending))
    existing = {str(item.get("topic", "")).lower().strip() for item in backlog}
    cur_id = max((int(item.get("id", 0)) for item in backlog), default=0)

    added = 0
    for entry in REPLENISH_LONGFORM_POOL:
        key = entry["topic"].lower().strip()
        if key not in existing:
            cur_id += 1
            backlog.append({
                "id": cur_id,
                "topic": entry["topic"],
                "minutes": entry["minutes"],
                "category": entry["category"],
                "status": "pending",
            })
            existing.add(key)
            added += 1

    if added == 0:
        cycle = (len(backlog) // max(1, len(REPLENISH_LONGFORM_POOL))) + 1
        for entry in REPLENISH_LONGFORM_POOL[:4]:
            cur_id += 1
            backlog.append({
                "id": cur_id,
                "topic": f"{entry['topic']} (Édition #{cycle})",
                "minutes": entry["minutes"],
                "category": entry["category"],
                "status": "pending",
            })

    BACKLOG_FILE.write_text(json.dumps(backlog, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Planificateur Hebdo Vidéos Longues 16:9")
    parser.add_argument("--auto", action="store_true", help="Rendu complet + publication YouTube directe")
    parser.add_argument("--privacy", type=str, default="public", choices=["public", "unlisted", "private"])
    args = parser.parse_args()

    if not BACKLOG_FILE.exists():
        logger.error("Fichier %s introuvable.", BACKLOG_FILE)
        sys.exit(1)

    backlog: list[dict[str, Any]] = json.loads(BACKLOG_FILE.read_text(encoding="utf-8"))
    replenish_longform_if_needed(backlog)

    next_ep = next((item for item in backlog if item.get("status") == "pending"), None)
    if not next_ep:
        logger.error("Aucun épisode disponible après réapprovisionnement.")
        sys.exit(1)

    cmd = [
        str(VENV_PYTHON),
        str(ENGINE_DIR / "longform_bot.py"),
        "--topic",
        str(next_ep["topic"]),
        "--minutes",
        str(next_ep.get("minutes", 6.0)),
    ]
    if args.auto:
        cmd += ["--auto", "--youtube", "--privacy", args.privacy]

    logger.info("Exécution épisode long #%s : %s (mode=%s)", next_ep.get("id"), next_ep["topic"], "auto" if args.auto else "draft")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        logger.error("Échec longform_bot.py :\n%s\n%s", res.stdout, res.stderr)
        sys.exit(res.returncode)

    print(res.stdout)
    yt_url = None
    for line in res.stdout.splitlines():
        if "https://www.youtube.com/watch?v=" in line:
            parts = line.split("https://www.youtube.com/watch?v=")
            if len(parts) > 1:
                vid_id = parts[1].strip().split()[0].replace('"', "").replace(",", "")
                yt_url = f"https://www.youtube.com/watch?v={vid_id}"

    next_ep["status"] = "published" if args.auto else "draft_generated"
    next_ep["updated_at"] = datetime.datetime.now().isoformat()
    if yt_url:
        next_ep["youtube_url"] = yt_url
    BACKLOG_FILE.write_text(json.dumps(backlog, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
