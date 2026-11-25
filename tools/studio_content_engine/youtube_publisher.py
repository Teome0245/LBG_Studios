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
import time
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
WINDOWS_AGENT_URL = os.environ.get(
    "LBG_WIN_AGENT_URL", "http://192.168.0.10:5005/execute"
)


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
            logger.warning(
                "Pont Windows non disponible (%s), ouvre le lien manuellement.", e
            )

        print(
            " En attente de l'autorisation Google (en écoute sur le port 8088, délai: 2h)...",
            flush=True,
        )
        local_server.timeout = 5
        start_wait = time.time()
        auth_response = None
        while time.time() - start_wait < 7200:
            local_server.handle_request()
            req = getattr(wsgi_app, "last_request_uri", None)
            if req and ("code=" in req or "error=" in req):
                auth_response = req
                break

        if not auth_response:
            raise TimeoutError("Délai dépassé ou aucune réponse reçue du navigateur.")

        from urllib.parse import urlparse, urlunparse

        parsed = urlparse(auth_response)
        clean_auth_response = urlunparse(
            (
                "https",
                f"localhost:{port}",
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment,
            )
        )
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
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.warning(
                    "Échec rafraîchissement token (%s), ré-authentification requise.", e
                )
                creds = None

        if not creds or not creds.valid:
            if not CLIENT_SECRET_FILE.exists():
                raise FileNotFoundError(
                    f"Fichier de configuration OAuth manquant : {CLIENT_SECRET_FILE}\n"
                    "1. Va sur https://console.cloud.google.com/\n"
                    "2. Active l'API 'YouTube Data API v3'\n"
                    "3. Crée un identifiant 'OAuth 2.0 Client ID' (Application pour ordinateur de bureau)\n"
                    f"4. Télécharge le JSON et enregistre-le sous : {CLIENT_SECRET_FILE}"
                )

            logger.info("Lancement du flux d'authentification OAuth pour @LBG-p8k...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRET_FILE), SCOPES
            )
            creds = _run_oauth_flow(flow, port=8088)

        with open(TOKEN_FILE, "w", encoding="utf-8") as token_out:
            token_out.write(creds.to_json())
        logger.info("Identifiants YouTube enregistrés dans %s", TOKEN_FILE)

    return build("youtube", "v3", credentials=creds)


def build_dynamic_tags(title: str, base_tags: list[str] | None = None) -> list[str]:
    """Génère des tags riches et ciblés en fonction du sujet de la vidéo."""
    tags = (
        list(base_tags)
        if base_tags
        else ["shorts", "ia", "tech", "lbg studios", "développement", "open source"]
    )
    title_lower = title.lower()

    keyword_map = {
        "godot": ["godot 4", "gamedev", "godot engine", "indiedev", "headless"],
        "bot": ["ia autonome", "agents ia", "simulation 3d", "gaming"],
        "sqlite": ["sqlite wal", "database", "backend", "performances", "redis"],
        "rust": ["rustlang", "architecture", "c++", "benchmark"],
        "cloud": ["0€ cloud", "self hosting", "infrastructure", "linux"],
        "obsidian": ["second brain", "rag", "productivité", "ia locale"],
        "windows": ["fastapi", "devops", "automation", "python"],
        "llm": ["ollama", "ia locale", "piper tts", "open source ai"],
    }

    for key, related in keyword_map.items():
        if key in title_lower:
            for r in related:
                if r not in tags:
                    tags.append(r)

    return tags[
        :15
    ]  # YouTube accepte jusqu'à 500 caractères, ~15 tags ciblés est idéal


def clean_title_for_shorts(title: str, max_len: int = 95) -> str:
    """Nettoie et tronque proprement le titre sans jamais couper au milieu d'un mot."""
    clean = title.strip()
    suffix = " #Shorts"
    if "#Shorts" in clean or "#shorts" in clean:
        suffix = ""

    target_len = max_len - len(suffix)
    if len(clean) > target_len:
        truncated = clean[:target_len]
        last_space = truncated.rfind(" ")
        if last_space > 30:
            truncated = truncated[:last_space]
        clean = truncated.strip() + "..."

    return f"{clean}{suffix}"


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

    # Nettoyage intelligent du titre
    clean_title = clean_title_for_shorts(title)

    default_desc = (
        f"{title}\n\n"
        "⚡ Vidéo 100% générée par le Studio Content Engine de LBG Studios (0€ Cloud).\n"
        "💬 Donnez votre avis en commentaire : vous utilisez quelle stack chez vous ?\n\n"
        "🔗 GitHub du projet : https://github.com/Teome0245/LBG_Studios\n\n"
        "#Shorts #IA #Tech #IntelligenceArtificielle #GodotEngine #OpenSource #Dev #SelfHosting"
    )
    final_desc = description if description else default_desc
    final_tags = build_dynamic_tags(title, tags)

    body = {
        "snippet": {
            "title": clean_title,
            "description": final_desc,
            "tags": final_tags,
            "categoryId": "28",  # 28 = Science & Technology
            "defaultLanguage": "fr",
            "defaultAudioLanguage": "fr",
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    logger.info("Upload du Short vers YouTube (@LBG-p8k)...")
    media = MediaFileUpload(
        str(video_path), mimetype="video/mp4", resumable=True, chunksize=1024 * 1024
    )
    request = youtube.videos().insert(
        part="snippet,status", body=body, media_body=media
    )

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


def upload_long_video(
    video_path: Path,
    title: str,
    description: str,
    tags: list[str] | None = None,
    thumbnail_path: Path | None = None,
    privacy_status: str = "public",
) -> dict[str, str]:
    """Upload une vidéo longue 16:9 (1920x1080) avec chapitres horodatés et miniature 1280x720."""
    if not video_path.exists():
        raise FileNotFoundError(f"Fichier vidéo introuvable : {video_path}")

    youtube = get_authenticated_service()

    clean_title = title.strip()
    if len(clean_title) > 98:
        truncated = clean_title[:95]
        sp = truncated.rfind(" ")
        clean_title = (truncated[:sp] if sp > 40 else truncated).strip() + "..."

    base_long_tags = [
        "ia locale",
        "homelab",
        "self hosting",
        "llm local",
        "hardware ia",
        "ollama",
        "lbg studios",
        "open source",
    ]
    final_tags = build_dynamic_tags(clean_title, tags or base_long_tags)

    body = {
        "snippet": {
            "title": clean_title,
            "description": description,
            "tags": final_tags,
            "categoryId": "28",
            "defaultLanguage": "fr",
            "defaultAudioLanguage": "fr",
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    logger.info("Upload de la Vidéo Longue 16:9 vers YouTube (@LBG-p8k)...")
    media = MediaFileUpload(
        str(video_path), mimetype="video/mp4", resumable=True, chunksize=2 * 1024 * 1024
    )
    request = youtube.videos().insert(
        part="snippet,status", body=body, media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            logger.info("Upload vidéo longue : %d%%...", int(status.progress() * 100))

    video_id = response.get("id")
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    logger.info("Vidéo longue publiée avec succès : %s", video_url)

    thumb_status = "skipped"
    if thumbnail_path and thumbnail_path.exists():
        try:
            thumb_media = MediaFileUpload(str(thumbnail_path), mimetype="image/png")
            youtube.thumbnails().set(videoId=video_id, media_body=thumb_media).execute()
            thumb_status = "uploaded"
            logger.info("Miniature personnalisée 1280x720 appliquée avec succès !")
        except Exception as exc:
            thumb_status = f"warning: {exc}"
            logger.warning("Miniature personnalisée non appliquée (%s)", exc)

    return {
        "status": "published",
        "video_id": video_id,
        "video_url": video_url,
        "title": clean_title,
        "thumbnail": thumb_status,
        "privacy": privacy_status,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Publication YouTube Shorts @LBG-p8k")
    parser.add_argument(
        "--setup", action="store_true", help="Lance la première authentification OAuth"
    )
    parser.add_argument("--video", type=str, help="Chemin du fichier MP4 à uploader")
    parser.add_argument(
        "--title",
        type=str,
        default="Veille IA & Tech LBG Studios",
        help="Titre de la vidéo",
    )
    parser.add_argument(
        "--privacy",
        type=str,
        default="public",
        choices=["public", "unlisted", "private"],
        help="Statut",
    )
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
