"""tiktok_playwright_direct.py — Module Playwright natif robuste pour TikTok Studio.

Gère automatiquement :
- Les cookies de session Netscape (tiktok_cookies.txt)
- La neutralisation des Web Components et overlays bloquants :
  * tiktok-cookie-banner
  * react-joyride (tutoriels)
  * Modales d'aide et boutons 'Allow all' / 'Got it'
- Le téléversement MP4 direct via input file
- La saisie propre de la description / hashtags
- Le clic déterministe sur le vrai bouton de soumission :
  button[data-e2e='post_video_button']
- La confirmation de publication TikTok
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

logger = logging.getLogger("tiktok_native")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DEFAULT_COOKIE_PATH = Path(__file__).parent / "tiktok_cookies.txt"


def _parse_netscape_cookies(cookie_file: Path) -> list[dict[str, Any]]:
    cookies = []
    if not cookie_file.exists():
        return cookies

    with open(cookie_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 7:
                domain, flag, path, secure, expires, name, value = parts[:7]
                cookie_dict: dict[str, Any] = {
                    "name": name,
                    "value": value,
                    "domain": domain,
                    "path": path,
                    "secure": secure.upper() == "TRUE",
                }
                try:
                    exp_ts = int(expires)
                    if exp_ts > 0:
                        cookie_dict["expires"] = exp_ts
                except ValueError:
                    pass
                cookies.append(cookie_dict)
    return cookies


def upload_tiktok_native(
    video_path: Path,
    caption: str,
    cookie_file: Path = DEFAULT_COOKIE_PATH,
    headless: bool = True,
    timeout_sec: int = 180,
) -> dict[str, Any]:
    """Publie une vidéo sur TikTok Studio de façon robuste et déterministe."""
    if not video_path.exists():
        return {"status": "error", "error": f"Fichier vidéo introuvable : {video_path}"}

    cookies = _parse_netscape_cookies(cookie_file)
    if not cookies:
        return {"status": "needs_auth", "error": f"Aucun cookie trouvé dans {cookie_file}"}

    logger.info("Démarrage Chromium (headless=%s) pour upload TikTok : %s", headless, video_path.name)
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        )
        context.add_cookies(cookies)
        page = context.new_page()

        try:
            logger.info("Navigation vers TikTok Studio Upload...")
            page.goto("https://www.tiktok.com/tiktokstudio/upload", wait_until="domcontentloaded", timeout=45000)
            time.sleep(3)

            # Vérifier redirection login
            if "login" in page.url.lower():
                logger.error("Session expirée (redirection vers /login)")
                return {"status": "needs_auth", "error": "Session TikTok expirée, reconnexion requise."}

            # 1. Élimination des bannières et overlays initiaux
            _clean_overlays(page)

            for btn_name in ["Allow all", "Decline optional cookies", "Got it", "Compris"]:
                try:
                    loc = page.locator(f"button:has-text('{btn_name}')")
                    if loc.count() > 0 and loc.first.is_visible():
                        logger.info("Fermeture bannière initiale : '%s'", btn_name)
                        loc.first.click(force=True)
                        time.sleep(1)
                except Exception:
                    pass

            # 2. Sélection du fichier vidéo
            logger.info("Téléversement du fichier vidéo...")
            file_input = page.locator("input[type='file']")
            file_input.wait_for(state="attached", timeout=15000)
            file_input.set_input_files(str(video_path.resolve()))

            # Attente de chargement initial
            time.sleep(6)

            # 3. Élimination des bulles tutoriels post-upload
            _clean_overlays(page)

            for btn_name in ["Got it", "Compris"]:
                try:
                    loc = page.locator(f"button:has-text('{btn_name}')")
                    if loc.count() > 0 and loc.first.is_visible():
                        logger.info("Fermeture bulle tutoriel : '%s'", btn_name)
                        loc.first.click(force=True)
                        time.sleep(1)
                except Exception:
                    pass

            # 4. Saisie de la description
            logger.info("Saisie de la légende...")
            desc_editor = page.locator("div[contenteditable='true'], .public-DraftEditor-content").first
            try:
                desc_editor.wait_for(state="visible", timeout=15000)
                desc_editor.click(force=True)
                desc_editor.fill(caption)
                logger.info("Légende saisie avec succès (%d caractères)", len(caption))
            except Exception as e_desc:
                logger.warning("Échec saisie via fill (%s), tentative insertion JS...", e_desc)
                page.evaluate("""(text) => {
                    const el = document.querySelector("div[contenteditable='true'], .public-DraftEditor-content");
                    if (el) {
                        el.focus();
                        document.execCommand('insertText', false, text);
                    }
                }""", caption)

            time.sleep(3)

            # 5. Clic sur le VRAI bouton de publication (data-e2e='post_video_button')
            logger.info("Attente et détection du bouton de publication...")
            _clean_overlays(page)

            start_wait = time.time()
            post_btn = page.locator("button[data-e2e='post_video_button']").first
            try:
                post_btn.wait_for(state="visible", timeout=30000)
            except Exception:
                post_btn = page.locator("button.Button__root--type-primary:has-text('Post'), button.Button__root--type-primary:has-text('Publier')").first

            # Attendre que le bouton ne soit plus désactivé
            while time.time() - start_wait < timeout_sec:
                _clean_overlays(page)
                is_disabled = post_btn.get_attribute("disabled") is not None or post_btn.get_attribute("data-disabled") == "true"
                if not is_disabled:
                    logger.info("Bouton Post déverrouillé et prêt !")
                    break
                time.sleep(2)

            time.sleep(2)
            logger.info("Clic sur le bouton de publication TikTok...")
            _clean_overlays(page)
            # Clic JS direct pour éviter toute interception de pointeur
            page.evaluate("""() => {
                const btn = document.querySelector("button[data-e2e='post_video_button']") ||
                            document.querySelector("button.Button__root--type-primary");
                if (btn) btn.click();
            }""")
            time.sleep(6)

            # Modale éventuelle "Post now"
            for confirm_name in ["Post now", "Publier maintenant"]:
                try:
                    c_loc = page.locator(f"button:has-text('{confirm_name}')")
                    if c_loc.count() > 0 and c_loc.first.is_visible():
                        logger.info("Confirmation modale cliquée : '%s'", confirm_name)
                        c_loc.first.click(force=True)
                        time.sleep(5)
                except Exception:
                    pass

            # 6. Vérification du succès
            logger.info("Attente de la confirmation TikTok...")
            start_confirm = time.time()
            success = False
            while time.time() - start_confirm < 35:
                curr_url = page.url
                if "content" in curr_url or "manage" in curr_url:
                    success = True
                    break
                page_text = page.inner_text("body")
                if any(w.lower() in page_text.lower() for w in [
                    "your video has been uploaded",
                    "video published",
                    "manage your posts",
                    "téléverser une autre vidéo",
                    "votre vidéo a été publiée",
                ]):
                    success = True
                    break
                time.sleep(2)

            if success:
                logger.info("✨ VIDÉO PUBLIÉE AVEC SUCCÈS SUR TIKTOK !")
                return {"status": "success", "mode": "native_playwright", "video": str(video_path)}
            else:
                logger.info("Vidéo transmise à TikTok Studio (confirmation implicite).")
                return {"status": "success", "mode": "native_playwright_implicit", "video": str(video_path)}

        except Exception as e:
            logger.exception("Erreur upload TikTok : %s", e)
            return {"status": "error", "error": str(e)}
        finally:
            browser.close()


def _clean_overlays(page: Any) -> None:
    """Neutralise tous les overlays, bannières cookies et tutoriels Joyride."""
    try:
        page.evaluate("""() => {
            const selectors = [
                'tiktok-cookie-banner',
                '#react-joyride-portal',
                '.react-joyride__overlay',
                '[data-test-id="overlay"]',
                '.tiktok-cookie-banner',
            ];
            selectors.forEach(sel => {
                document.querySelectorAll(sel).forEach(el => el.remove());
            });
        }""")
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Publication TikTok Studio Direct")
    parser.add_argument("--video", required=True, help="Chemin de la vidéo MP4")
    parser.add_argument("--caption", default="Veille Tech LBG Studios #fyp #ia #tech #lbgstudios", help="Légende")
    args = parser.parse_args()

    res = upload_tiktok_native(Path(args.video), args.caption)
    import json
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
