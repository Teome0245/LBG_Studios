"""youtube_publisher.py — Module de publication automatique YouTube Shorts (@LBG-p8k).

Utilise l'API officielle Google YouTube Data API v3 (0 €).
- Upload vidéo MP4 1080x1920 (format Shorts automatique grâce à la durée < 60s et au ratio 9:16).
- Gestion du snippet (titre, description avec hashtags #Shorts, tags, catégorie Tech).
- Gestion du statut de confidentialité (public, non répertorié ou privé).
- OAuth 2.0 avec persistance du refresh token dans token.json.

Configuration requise :
  Déposer le fichier client_secret.json obtenu depuis Google Cloud Console dans :
  tools/studio_content_engine/config/client_secret.json
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import wsgiref.simple_server
from pathlib import Path
from typing import Any

import httpx
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import (
    InstalledAppFlow,
    _RedirectWSGIApp,
    _WSGIRequestHandler,
)
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger("youtube_publisher")

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]

CONFIG_DIR = Path(__file__).resolve().parent / "config"
CLIENT_SECRET_FILE = CONFIG_DIR / "client_secret.json"
TOKEN_FILE = CONFIG_DIR / "youtube_token.json"
WINDOWS_AGENT_URL = os.environ.get("LBG_WIN_AGENT_URL", "http://192.168.0.10:5005/execute")


def _run_oauth_flow(flow: InstalledAppFlow, port: int = 8088) -> Credentials:
    """Exécute le serveur local OAuth avec pont automatique vers le poste Windows."""
    success_msg = (
        "<html><body style='font-family:sans-serif;text-align:center;padding:50px;'>"
        "<h2 style='color:#10b981;'>Authentification YouTube Réussie !</h2>"
        "<p>LBG Studio Content Engine est connecté à la chaîne YouTube @LBG-p8k.</p>"
        "<p>Tu peux maintenant fermer cette fenêtre.</p>"
        "</body></html>"
    )
    wsgi_app = _RedirectWSGIApp(success_msg)
    local_server = wsgiref.simple_server.make_server(
        "0.0.0.0",
        port,
        wsgi_app,
        handler_class=_WSGIRequestHandler,
    )

    try:
        flow.redirect_uri = f"http://localhost:{port}/"
        auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")

        print("\n" + "=" * 70)
        print("⚡ AUTHENTIFICATION YOUTUBE SHORTS (@LBG-p8k) REQUISE")
        print("=" * 70)
        print(f"Lien d'autorisation Google :\n{auth_url}\n")
        print("=" * 70)

        # Déclenchement du pont TCP et ouverture de Firefox sur le poste Windows
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.post(
                    WINDOWS_AGENT_URL,
                    json={
                        "action": "lancer_pont_et_firefox",
                        "parameters": {
                            "port": port,
                            "target_host": "192.168.0.143",
                            "target_port": port,
                            "url": auth_url,
                        },
                    },
                )
                if resp.status_code == 200:
                    print(" Firefox lancé sur Windows avec pont localhost:8088 actif.")
        except Exception as e:
            logger.warning("Pont Windows non disponible (%s), ouvre le lien manuellement.", e)

        print(" En attente de l'autorisation dans Firefox (délai: 10 min)...", flush=True)
        local_server.timeout = 600
        local_server.handle_request()

        auth_response = getattr(wsgi_app, "last_request_uri", None)
        if not auth_response:
            raise TimeoutError("Délai dépassé ou aucune réponse reçue du navigateur.")

        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(auth_response)
        clean_auth_response = urlunparse((
            "https",
            f"localhost:{port}",
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        ))
        flow.fetch_token(authorization_response=clean_auth_response)
        return flow.credentials

    finally:
        local_server.server_close()


def get_authenticated_service() -> Any:
    """Authentifie et retourne le client YouTube Data API v3."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    creds = None

    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception as e:
            logger.warning("Erreur lecture token existant: %s", e)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Rafraîchissement du token YouTube...")
            creds.refresh(Request())
        else:
            if not CLIENT_SECRET_FILE.exists():
                raise FileNotFoundError(
                    f"Fichier de configuration OAuth manquant : {CLIENT_SECRET_FILE}\n"
                    "1. Va sur https://console.cloud.google.com/\n"
                    "2. Active l'API 'YouTube Data API v3'\n"
                    "3. Crée un identifiant 'OAuth 2.0 Client ID' (Application pour ordinateur de bureau)\n"
                    f"4. Télécharge le JSON et enregistre-le sous : {CLIENT_SECRET_FILE}"
                )

            logger.info("Lancement du flux d'authentification OAuth pour @LBG-p8k...")
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_FILE), SCOPES)
            creds = _run_oauth_flow(flow, port=8088)

        with open(TOKEN_FILE, "w", encoding="utf-8") as token_out:
            token_out.write(creds.to_json())
        logger.info("Identifiants YouTube enregistrés dans %s", TOKEN_FILE)

    return build("youtube", "v3", credentials=creds)


def upload_short_video(
    video_path: Path,
    title: str,
    description: str | None = None,
    tags: list[str] | None = None,
    privacy_status: str = "public",
) -> dict[str, str]:
    """Upload un Short vertical sur la chaîne YouTube @LBG-p8k."""
    if not video_path.exists():
        raise FileNotFoundError(f"Fichier vidéo introuvable : {video_path}")

    youtube = get_authenticated_service()

    # Assurer que le titre ou la description contient #Shorts pour le référencement
    clean_title = title if "#Shorts" in title else f"{title} #Shorts"
    if len(clean_title) > 100:
        clean_title = clean_title[:90] + "... #Shorts"

    default_desc = (
        f"{title}\n\n"
        "⚡ Vidéo 100% générée par le Studio Content Engine de LBG Studios (0€ Cloud).\n"
        "🔗 GitHub du projet : https://github.com/Teome0245/LBG_Studios\n\n"
        "#Shorts #IA #Tech #IntelligenceArtificielle #GodotEngine #OpenSource #Dev"
    )
    final_desc = description if description else default_desc

    default_tags = ["shorts", "ia", "tech", "lbg studios", "développement", "godot 4", "open source"]
    final_tags = tags if tags else default_tags

    body = {
        "snippet": {
            "title": clean_title,
            "description": final_desc,
            "tags": final_tags,
            "categoryId": "28",  # 28 = Science & Technology
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    logger.info("Upload du Short vers YouTube (@LBG-p8k)...")
    media = MediaFileUpload(str(video_path), mimetype="video/mp4", resumable=True, chunksize=1024 * 1024)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            logger.info("Upload en cours : %d%%...", int(status.progress() * 100))

    video_id = response.get("id")
    video_url = f"https://www.youtube.com/shorts/{video_id}"
    logger.info("Short publié avec succès ! Lien : %s", video_url)

    return {
        "status": "published",
        "video_id": video_id,
        "video_url": video_url,
        "title": clean_title,
        "privacy": privacy_status,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Publication YouTube Shorts @LBG-p8k")
    parser.add_argument("--setup", action="store_true", help="Lance la première authentification OAuth")
    parser.add_argument("--video", type=str, help="Chemin du fichier MP4 à uploader")
    parser.add_argument("--title", type=str, default="Veille IA & Tech LBG Studios", help="Titre de la vidéo")
    parser.add_argument("--privacy", type=str, default="public", choices=["public", "unlisted", "private"], help="Statut")
    args = parser.parse_args()

    if args.setup:
        try:
            get_authenticated_service()
            print("Authentification YouTube réussie ! Le token est prêt.")
        except Exception as e:
            print(f"Erreur d'authentification : {e}")
            sys.exit(1)
        return

    if not args.video:
        print("Spécifiez un fichier vidéo avec --video ou lancez --setup")
        sys.exit(1)

    result = upload_short_video(
        video_path=Path(args.video),
        title=args.title,
        privacy_status=args.privacy,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

