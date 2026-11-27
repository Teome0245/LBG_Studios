"""art_auth.py — Script d'authentification interactive DeviantArt & Pinterest (0 dépendance externe).

Ouvre un navigateur Chromium visible sur le bureau Windows (.10).
L'utilisateur valide sa connexion (ou clique sur son profil).
Dès que la session est détectée, les cookies sont sauvegardés dans C:\\Agent_IA\\
et synchronisés immédiatement sur .143 (A:\\LBG_Studios\\tools\\studio_content_engine\\).
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

DEFAULT_AGENT_DIR = Path(r"C:\Agent_IA")
MIRROR_ENGINE_DIR = Path(r"A:\LBG_Studios\tools\studio_content_engine")


def save_netscape_cookies(filepath: Path, cookies: list[dict]) -> None:
    lines = ["# Netscape HTTP Cookie File\n# http://curl.haxx.se/rfc/cookie_spec.html\n\n"]
    for c in cookies:
        domain = c.get("domain", "")
        flag = "TRUE" if domain.startswith(".") else "FALSE"
        path = c.get("path", "/")
        secure = "TRUE" if c.get("secure", False) else "FALSE"
        expires = int(c.get("expires", 0))
        name = c.get("name", "")
        value = c.get("value", "")
        lines.append(f"{domain}\t{flag}\t{path}\t{secure}\t{expires}\t{name}\t{value}")

    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")


def authenticate_deviantart(timeout_sec: int = 180) -> bool:
    print("=" * 60)
    print("  AUTHENTIFICATION DEVIANTART (LBG STUDIOS)")
    print("=" * 60)
    print("Ouverture du navigateur Chromium...")
    print("Veuillez vous connecter a votre compte Teome245 sur DeviantArt.")
    print(f"Delai max : {timeout_sec}s")
    print("-" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        )
        page = context.new_page()

        try:
            page.goto("https://www.deviantart.com/users/login", wait_until="domcontentloaded", timeout=45000)
        except Exception as e:
            print(f"Navigation : {e}")

        start_time = time.time()
        authenticated = False

        while time.time() - start_time < timeout_sec:
            cookies = context.cookies()
            has_auth = any(c["name"] in ("userinfo", "auth_secure", "auth", "_deviantart_session") for c in cookies)

            if has_auth and "login" not in page.url.lower():
                time.sleep(3)
                fresh_cookies = context.cookies()
                local_path = DEFAULT_AGENT_DIR / "deviantart_cookies.txt"
                save_netscape_cookies(local_path, fresh_cookies)
                print(f"\n[SUCCES] Session DeviantArt enregistree : {local_path}")

                mirror_path = MIRROR_ENGINE_DIR / "deviantart_cookies.txt"
                try:
                    save_netscape_cookies(mirror_path, fresh_cookies)
                    print(f"[SUCCES] Cookies synchronises en direct sur .143 : {mirror_path}")
                except Exception as e_m:
                    print(f"[WARN] Synchro miroir .143 : {e_m}")

                authenticated = True
                break

            time.sleep(1)
            sys.stdout.write(".")
            sys.stdout.flush()

        time.sleep(1)
        browser.close()
        return authenticated


def authenticate_pinterest(timeout_sec: int = 180) -> bool:
    print("=" * 60)
    print("  AUTHENTIFICATION PINTEREST (LBG STUDIOS)")
    print("=" * 60)
    print("Ouverture du navigateur Chromium...")
    print("Veuillez vous connecter a votre compte 'La Boite a Geeks' sur Pinterest.")
    print(f"Delai max : {timeout_sec}s")
    print("-" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        )
        page = context.new_page()

        try:
            page.goto("https://www.pinterest.com/login/", wait_until="domcontentloaded", timeout=45000)
        except Exception as e:
            print(f"Navigation : {e}")

        start_time = time.time()
        authenticated = False

        while time.time() - start_time < timeout_sec:
            cookies = context.cookies()
            has_auth = any(c["name"] in ("_auth", "_pinterest_sess") for c in cookies)

            if has_auth and "login" not in page.url.lower():
                time.sleep(3)
                fresh_cookies = context.cookies()
                local_path = DEFAULT_AGENT_DIR / "pinterest_cookies.txt"
                save_netscape_cookies(local_path, fresh_cookies)
                print(f"\n[SUCCES] Session Pinterest enregistree : {local_path}")

                mirror_path = MIRROR_ENGINE_DIR / "pinterest_cookies.txt"
                try:
                    save_netscape_cookies(mirror_path, fresh_cookies)
                    print(f"[SUCCES] Cookies synchronises en direct sur .143 : {mirror_path}")
                except Exception as e_m:
                    print(f"[WARN] Synchro miroir .143 : {e_m}")

                authenticated = True
                break

            time.sleep(1)
            sys.stdout.write(".")
            sys.stdout.flush()

        time.sleep(1)
        browser.close()
        return authenticated


def main() -> None:
    parser = argparse.ArgumentParser(description="Authentification Sociale pour Gladys")
    parser.add_argument("--platform", choices=["deviantart", "pinterest", "all"], required=True)
    args = parser.parse_args()

    if args.platform in ("deviantart", "all"):
        authenticate_deviantart()
    if args.platform in ("pinterest", "all"):
        authenticate_pinterest()


if __name__ == "__main__":
    main()
