"""tiktok_auth.py — Script d'authentification TikTok initiale pour LBG Studios.

Ouvre un navigateur Playwright visible sur TikTok Studio.
L'utilisateur se connecte (QR Code, compte Google ou identifiants).
Dès que la session est détectée, les cookies sont sauvegardés dans C:\\Agent_IA\\tiktok_cookies.txt
pour permettre les publications 100% autonomes en tâche de fond.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from tiktok_uploader.auth import save_cookies

DEFAULT_COOKIE_PATH = r"C:\Agent_IA\tiktok_cookies.txt"


def authenticate_and_save_cookies(cookie_path: str = DEFAULT_COOKIE_PATH, timeout_sec: int = 180) -> bool:
    print("=" * 60)
    print("  AUTHENTIFICATION TIKTOK STUDIO (100% AUTOMATION)")
    print("=" * 60)
    print("Ouverture d'un navigateur Chromium...")
    print("Veuillez vous connecter à TikTok (QR Code ou compte).")
    print(f"Délai d'attente max : {timeout_sec}s")
    print("-" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        )
        page = context.new_page()

        try:
            page.goto("https://www.tiktok.com/tiktokstudio/upload", wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"Navigation initiale : {e}")

        start_time = time.time()
        authenticated = False

        while time.time() - start_time < timeout_sec:
            cookies = context.cookies()
            has_session = any(c["name"] == "sessionid" for c in cookies)

            # EXIGER EXPLICITEMENT le cookie de session TikTok
            if has_session:
                time.sleep(3)  # Laisser le temps à tous les cookies de s'établir
                fresh_cookies = context.cookies()
                Path(cookie_path).parent.mkdir(parents=True, exist_ok=True)
                save_cookies(cookie_path, fresh_cookies)
                print(f"\n[SUCCÈS] Session TikTok détectée et cookies sauvegardés dans : {cookie_path}")

                # Copie miroir automatique sur .143 (A:\LBG_Studios\tools\studio_content_engine)
                mirror_143 = Path(r"A:\LBG_Studios\tools\studio_content_engine\tiktok_cookies.txt")
                try:
                    save_cookies(str(mirror_143), fresh_cookies)
                    print(f"[SUCCÈS] Cookies synchronisés en direct sur .143 : {mirror_143}")
                except Exception as e_mirror:
                    print(f"[WARN] Synchro miroir .143 omise : {e_mirror}")

                authenticated = True
                break

            time.sleep(1)
            sys.stdout.write(".")
            sys.stdout.flush()

        time.sleep(1)
        browser.close()

        if not authenticated:
            print("\n[TIMEOUT] Connexion non détectée avant la fin du délai.")
            return False

        return True


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_COOKIE_PATH
    success = authenticate_and_save_cookies(out)
    sys.exit(0 if success else 1)
