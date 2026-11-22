"""tiktok_publisher.py — Module de publication TikTok Studio 100% automatisée (Playwright).

Utilise le moteur Playwright natif pour neutraliser les bannières/joyrides et publier
de façon totalement autonome et déterministe.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import httpx

from tiktok_playwright_direct import upload_tiktok_native

logger = logging.getLogger("tiktok_publisher")

LOCAL_COOKIES = Path(__file__).parent / "tiktok_cookies.txt"
WINDOWS_AGENT_URL = os.environ.get("LBG_WIN_AGENT_URL", "http://192.168.0.10:5005/execute")


def upload_local_tiktok(video_path: Path, caption: str | None = None) -> dict[str, Any]:
    """Publie la vidéo directement depuis la machine locale (.143) via le moteur natif Playwright."""
    logger.info("Upload direct TikTok depuis .143 avec Playwright natif...")
    try:
        final_caption = caption or "Veille Tech LBG Studios #fyp #tech #ia #dev #lbgstudios"
        return upload_tiktok_native(
            video_path=video_path,
            caption=final_caption,
            cookie_file=LOCAL_COOKIES,
            headless=True,
        )
    except Exception as e:
        logger.exception("Erreur upload local .143 : %s", e)
        return {"status": "error", "mode": "local_143", "error": str(e)}


def trigger_tiktok_upload(video_name: str | None = None, caption: str | None = None, local_video_path: Path | None = None) -> dict[str, Any]:
    """Déclenche la publication TikTok Playwright (priorité locale .143 si cookies présents)."""
    # 1. Priorité absolue : Upload direct local sur .143 si les cookies existent
    if LOCAL_COOKIES.exists() and local_video_path and local_video_path.exists():
        return upload_local_tiktok(local_video_path, caption=caption)

    # 2. Fallback éventuel sur Windows si chemin local non fourni mais nom disponible
    params = {}
    if video_name:
        params["video_path"] = f"O:\\OneDrive\\Pictures\\IA\\Contenue\\{video_name}"
    if caption:
        params["caption"] = caption

    logger.info("Délégation à l'Agent Windows (%s)...", WINDOWS_AGENT_URL)
    with httpx.Client(timeout=15.0) as client:
        res = client.post(
            WINDOWS_AGENT_URL,
            json={"action": "preparer_upload_tiktok", "parameters": params},
        )
        if res.status_code != 200:
            raise RuntimeError(f"Erreur Agent Windows ({res.status_code}): {res.text}")
        data = res.json()
        logger.info("Résultat TikTok Studio : %s", data)
        return data


def trigger_tiktok_auth() -> dict[str, str]:
    """Ouvre la fenêtre Playwright pour connecter TikTok une seule fois."""
    with httpx.Client(timeout=10.0) as client:
        res = client.post(
            WINDOWS_AGENT_URL,
            json={"action": "auth_tiktok", "parameters": {}},
        )
        return res.json()


def main() -> None:
    parser = argparse.ArgumentParser(description="Assistance publication TikTok Studio")
    parser.add_argument("--video", type=str, default=None, help="Chemin MP4 local ou nom dans Contenue")
    parser.add_argument("--caption", type=str, default=None, help="Légende personnalisée avec hashtags")
    args = parser.parse_args()

    v_path = Path(args.video) if args.video and Path(args.video).exists() else None
    v_name = args.video if not v_path else None

    result = trigger_tiktok_upload(video_name=v_name, caption=args.caption, local_video_path=v_path)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
