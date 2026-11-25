#!/usr/bin/env python3
"""cron_weekly_longform.py — Planificateur hebdomadaire (1 à 2 vidéos longues 16:9 / semaine).

Modes :
- Par défaut (`--draft`) : prépare le prochain sujet de `longform_backlog.json` en brouillon Markdown
  prêt à relire/valider (façon Kiara).
- Avec `--auto` : génère, calcule la vidéo 16:9 30 FPS + miniature 1280x720 et publie sur YouTube `@LBG-p8k`.
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Planificateur Hebdo Vidéos Longues 16:9")
    parser.add_argument("--auto", action="store_true", help="Rendu complet + publication YouTube directe sans étape brouillon")
    parser.add_argument("--privacy", type=str, default="public", choices=["public", "unlisted", "private"])
    args = parser.parse_args()

    if not BACKLOG_FILE.exists():
        logger.error("Fichier %s introuvable.", BACKLOG_FILE)
        sys.exit(1)

    backlog: list[dict[str, Any]] = json.loads(BACKLOG_FILE.read_text(encoding="utf-8"))
    next_ep = next((item for item in backlog if item.get("status") == "pending"), None)
    if not next_ep:
        logger.info("Tous les sujets de longform_backlog.json ont déjà été traités.")
        return

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
    next_ep["status"] = "published" if args.auto else "draft_generated"
    next_ep["updated_at"] = datetime.datetime.now().isoformat()
    BACKLOG_FILE.write_text(json.dumps(backlog, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
