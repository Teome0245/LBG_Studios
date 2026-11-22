"""tiktok_uploader_playwright.py — Upload autonome TikTok Studio via Playwright.

Publie directement la vidéo avec sa légende et hashtags sur TikTok Studio
sans ouvrir de fenêtres parasites à répétition.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from tiktok_uploader.upload import upload_video

logger = logging.getLogger("tiktok_playwright")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DEFAULT_COOKIE_PATH = r"C:\Agent_IA\tiktok_cookies.txt"


def upload_single_video(
    video_path: str,
    caption: str,
    cookie_path: str = DEFAULT_COOKIE_PATH,
    headless: bool = True,
) -> dict:
    if not os.path.exists(video_path):
        return {"status": "error", "error": f"Fichier vidéo introuvable : {video_path}"}

    if not os.path.exists(cookie_path):
        return {
            "status": "needs_auth",
            "error": f"Cookies manquants ({cookie_path}). Lancez tiktok_auth.py pour vous connecter une première fois.",
        }

    logger.info("Lancement de l'upload Playwright pour : %s", video_path)
    try:
        failed = upload_video(
            filename=video_path,
            description=caption,
            cookies=cookie_path,
            browser="chromium",
            headless=headless,
        )

        if not failed:
            logger.info("Upload TikTok terminé avec SUCCÈS !")
            return {"status": "success", "video": video_path, "caption": caption}
        else:
            logger.error("Échec d'upload TikTok : %s", failed)
            return {"status": "error", "error": f"TikTok upload failed: {failed}"}

    except Exception as e:
        logger.exception("Exception pendant l'upload Playwright : %s", e)
        return {"status": "error", "error": str(e)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload TikTok via Playwright")
    parser.add_argument("--video", required=True, help="Chemin complet de la vidéo MP4")
    parser.add_argument("--caption", default="Veille Tech LBG Studios #fyp #tech #ia", help="Légende et hashtags")
    parser.add_argument("--cookies", default=DEFAULT_COOKIE_PATH, help="Chemin du fichier de cookies")
    parser.add_argument("--headful", action="store_true", help="Afficher le navigateur pendant l'upload")
    args = parser.parse_args()

    res = upload_single_video(
        video_path=args.video,
        caption=args.caption,
        cookie_path=args.cookies,
        headless=not args.headful,
    )
    print(json.dumps(res, ensure_ascii=False))
    if res.get("status") != "success":
        sys.exit(1)


if __name__ == "__main__":
    main()
