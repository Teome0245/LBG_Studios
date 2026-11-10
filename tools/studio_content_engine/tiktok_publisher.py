"""tiktok_publisher.py — Module de publication et d'assistance TikTok Studio pour LBG Studios.

Gère la préparation et la publication vers https://www.tiktok.com/tiktokstudio/content :
1. Déclenche sur l'Agent Windows (.10:5005) l'ouverture automatique de TikTok Studio Upload dans le navigateur.
2. Ouvre l'Explorateur Windows avec le fichier vidéo directement sélectionné dans O:\\OneDrive\\Pictures\\IA\\Contenue\\.
3. Copie automatiquement le titre et les hashtags viraux dans le presse-papier Windows (prêt pour Ctrl+V).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import httpx

logger = logging.getLogger("tiktok_publisher")

WINDOWS_AGENT_URL = os.environ.get("LBG_WIN_AGENT_URL", "http://192.168.0.10:5005/execute")


def trigger_tiktok_upload(video_name: str | None = None, caption: str | None = None) -> dict[str, str]:
    """Déclenche la préparation d'upload TikTok sur le poste Windows."""
    params = {}
    if video_name:
        params["video_path"] = f"O:\\OneDrive\\Pictures\\IA\\Contenue\\{video_name}"
    if caption:
        params["caption"] = caption

    logger.info("Envoi de la commande à l'Agent Windows (%s)...", WINDOWS_AGENT_URL)
    with httpx.Client(timeout=10.0) as client:
        res = client.post(
            WINDOWS_AGENT_URL,
            json={"action": "preparer_upload_tiktok", "parameters": params},
        )
        if res.status_code != 200:
            raise RuntimeError(f"Erreur Agent Windows ({res.status_code}): {res.text}")
        data = res.json()
        logger.info("Action TikTok Studio préparée : %s", data)
        return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Assistance publication TikTok Studio")
    parser.add_argument("--video", type=str, default=None, help="Nom du fichier MP4 dans Contenue (optionnel)")
    parser.add_argument("--caption", type=str, default=None, help="Légende personnalisée avec hashtags")
    args = parser.parse_args()

    result = trigger_tiktok_upload(video_name=args.video, caption=args.caption)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

