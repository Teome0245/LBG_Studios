#!/usr/bin/env python3
"""content_bot.py — Studio Content Engine : Générateur autonome de vidéos courtes TikTok/Shorts (0€).

Pipeline unifié :
1. Génération de script viral (Hook, Problème, Solution, CTA) via Ollama local (.110 / .111).
2. Synthèse vocale Piper TTS instantanée (.111:8098/v1/tts).
3. Génération des sous-titres dynamiques stylisés TikTok (.ass).
4. Composition vidéo 9:16 (1080x1920) à 30 FPS avec avatar 3D Mia synchronisé.
5. Export MP4 final prêt pour les réseaux sociaux.

Usage :
    python tools/studio_content_engine/content_bot.py --demo
    python tools/studio_content_engine/content_bot.py --topic "Pourquoi faire tourner ses LLM en local"
    python tools/studio_content_engine/content_bot.py --topic "Simuler un MMORPG avec Godot 4.6 headless"
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any

# Résolution des imports locaux
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from script_generator import generate_tech_script
from video_compositor import render_video
from voice_engine import generate_tiktok_ass_subtitles, synthesize_script

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("studio_content_bot")

DEFAULT_OUTPUT_DIR = CURRENT_DIR / "output"
COMPAGNON_ASSETS_DIR = CURRENT_DIR / "assets" / "compagnon"
MIA_ASSETS_DIR = CURRENT_DIR / "assets" / "mia"
PILOT_DROPS_DIR = Path("packages/cortex/pilot_web/public/drops")


def build_short_video(
    topic: str | None = None,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    model: str = "qwen2.5:3b",
    avatar_dir: Path = COMPAGNON_ASSETS_DIR,
    voice: str | None = None,
    silence_sec: float | None = None,
    deploy_pilot: bool = True,
    publish_youtube: bool = False,
    publish_tiktok: bool = False,
) -> dict[str, str | float]:
    """Exécute la pipeline complète de création de contenu."""
    start_time = time.time()
    run_id = f"drop_{int(start_time)}"
    work_dir = output_dir / run_id
    work_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=== [1/4] Écriture du Script Viral Tech ===")
    script_data = generate_tech_script(topic=topic, model=model)
    script_file = work_dir / "script.json"
    with open(script_file, "w", encoding="utf-8") as f:
        json.dump(script_data, f, indent=2, ensure_ascii=False)
    logger.info("Titre : « %s » (%s)", script_data.get("title"), script_data.get("category"))
    for idx, s in enumerate(script_data.get("sentences", [])):
        logger.info("  [%d] %s", idx + 1, s)

    logger.info("=== [2/4] Synthèse Vocale Piper TTS (.111:8098) ===")
    synth_kwargs: dict[str, Any] = {
        "sentences": script_data.get("sentences", []),
        "work_dir": work_dir,
    }
    if voice:
        synth_kwargs["voice"] = voice
    if silence_sec is not None:
        synth_kwargs["initial_silence_sec"] = silence_sec

    audio_path, cues, audio_duration = synthesize_script(**synth_kwargs)
    logger.info("Audio généré : %s (durée: %.2fs)", audio_path.name, audio_duration)

    logger.info("=== [3/4] Génération des sous-titres TikTok (.ass) ===")
    ass_path = work_dir / "subtitles.ass"
    generate_tiktok_ass_subtitles(cues, ass_path)
    logger.info("Sous-titres ASS générés : %s", ass_path.name)

    logger.info("=== [4/4] Rendu & Composition Vidéo 1080x1920 (Avatar 3D) ===")
    out_mp4 = work_dir / f"{run_id}_tiktok.mp4"
    render_video(
        audio_path=audio_path,
        ass_path=ass_path,
        output_mp4=out_mp4,
        avatar_dir=avatar_dir,
        title=script_data.get("title", "VEILLE TECH LBG"),
        category=script_data.get("category", "IA & DEV LOCAL"),
    )

    elapsed = time.time() - start_time
    file_size_mb = out_mp4.stat().st_size / (1024 * 1024)

    logger.info("=== PIPELINE TERMINÉE AVEC SUCCÈS ===")
    logger.info("Fichier final : %s (%.2f Mo, durée %.1fs, calculé en %.1fs)", out_mp4, file_size_mb, audio_duration, elapsed)

    # Synchronisation automatique vers O:\OneDrive\Pictures\IA\Contenue via l'Agent Windows
    try:
        import httpx
        with httpx.Client(timeout=10.0) as client:
            res = client.post(
                "http://192.168.0.10:5005/execute",
                json={"action": "copier_video_vers_onedrive", "parameters": {}},
            )
            if res.status_code == 200 and res.json().get("status") == "success":
                logger.info("Vidéo synchronisée avec succès vers O:\\OneDrive\\Pictures\\IA\\Contenue !")
    except Exception as e:
        logger.warning("Synchronisation OneDrive ignorée : %s", e)

    # Déploiement optionnel dans Pilot Web drops pour prévisualisation immédiate
    if deploy_pilot and PILOT_DROPS_DIR.exists():
        try:
            dest_mp4 = PILOT_DROPS_DIR / f"{run_id}.mp4"
            shutil.copy2(out_mp4, dest_mp4)
            logger.info("Vidéo déployée sur Pilot Web : %s", dest_mp4)
        except Exception as e:
            logger.warning("Déploiement Pilot Web omis : %s", e)

    # Publication YouTube Shorts (@LBG-p8k)
    yt_result = None
    if publish_youtube:
        try:
            from youtube_publisher import upload_short_video
            yt_result = upload_short_video(
                video_path=out_mp4,
                title=script_data.get("title", "Veille IA LBG Studios"),
            )
        except Exception as e:
            logger.error("Échec publication YouTube : %s", e)

    # Préparation publication TikTok Studio
    tt_result = None
    if publish_tiktok:
        try:
            from tiktok_publisher import trigger_tiktok_upload
            caption = f"{script_data.get('title', 'Veille Tech')} #fyp #ia #tech #dev #lbgstudios"
            tt_result = trigger_tiktok_upload(video_name=f"{run_id}_tiktok.mp4", caption=caption)
        except Exception as e:
            logger.error("Échec préparation TikTok : %s", e)

    res_dict: dict[str, Any] = {
        "run_id": run_id,
        "title": script_data.get("title", ""),
        "category": script_data.get("category", ""),
        "mp4_path": str(out_mp4),
        "file_size_mb": round(file_size_mb, 2),
        "duration_sec": round(audio_duration, 2),
        "render_time_sec": round(elapsed, 2),
    }
    if yt_result:
        res_dict["youtube"] = yt_result
    if tt_result:
        res_dict["tiktok"] = tt_result

    return res_dict


def main() -> None:
    parser = argparse.ArgumentParser(description="Studio Content Bot — Pipeline Vidéo Avatar 0€")
    parser.add_argument("--topic", type=str, default=None, help="Sujet de la vidéo tech")
    parser.add_argument("--demo", action="store_true", help="Génère la vidéo démo avec script canonique")
    parser.add_argument("--voice", type=str, default=None, help="Voix TTS (défaut: fr-FR-VivienneMultilingualNeural, fallback: fr_FR-siwis-medium)")
    parser.add_argument("--silence", type=float, default=None, help="Secondes de silence au début (défaut: 0.3s)")
    parser.add_argument("--model", type=str, default="qwen2.5:3b", help="Modèle Ollama")
    parser.add_argument("--outdir", type=str, default=str(DEFAULT_OUTPUT_DIR), help="Dossier de sortie")
    parser.add_argument("--youtube", action="store_true", help="Publie sur la chaîne YouTube @LBG-p8k")
    parser.add_argument("--tiktok", action="store_true", help="Prépare la publication sur TikTok Studio")
    args = parser.parse_args()

    topic = args.topic
    if args.demo and not topic:
        topic = None

    result = build_short_video(
        topic=topic,
        output_dir=Path(args.outdir),
        model=args.model,
        voice=args.voice,
        silence_sec=args.silence,
        publish_youtube=args.youtube,
        publish_tiktok=args.tiktok,
    )
    print("\n" + "=" * 50)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("=" * 50)


if __name__ == "__main__":
    main()

