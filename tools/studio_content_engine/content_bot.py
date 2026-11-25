#!/usr/bin/env python3
"""content_bot.py — Studio Content Engine : Générateur autonome de vidéos courtes TikTok/Shorts (0€).

Modes de rendu supportés (9:16 - 1080x1920 @ 30 FPS) :
- `stage3d` (DÉFAUT) : Scène 3D WebGL Three-VRM style Nexura Domina, Lia 3D animée face caméra,
  mouvements de caméra mobiles, sous-titres karaoké courts pop néon, égaliseur FFT 24 bandes et BGM synthwave.
- `music3d` : Clip Musical / Chorégraphie 3D style Nexura Domina (micro 3D néon, danses mocap `.vrma`,
  caméras drone, master stéréo 128 BPM).
- `jrpg` : Style rétro boîte de dialogue JRPG (legacy).
- `standard` : Compositeur Pillow 2D + infographies (legacy).

Exécution : GPU Windows `.10` si le poste est libre (`idle >= 180s`), sinon repli automatique `.143` (`Xvfb`).
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
import time
from pathlib import Path
from typing import Any

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from jrpg_compositor import render_jrpg_video
from script_generator import generate_tech_script
from stage3d_compositor import render_stage3d_music_video, render_stage3d_tech_video
from video_compositor import render_video
from voice_engine import generate_tiktok_ass_subtitles, synthesize_script

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("studio_content_bot")

DEFAULT_OUTPUT_DIR = CURRENT_DIR / "output"
COMPAGNON_ASSETS_DIR = CURRENT_DIR / "assets" / "compagnon"
PILOT_DROPS_DIR = Path("packages/cortex/pilot_web/public/drops")


def build_short_video(
    topic: str | None = None,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    model: str = "qwen2.5:3b",
    avatar_dir: Path = COMPAGNON_ASSETS_DIR,
    voice: str | None = None,
    silence_sec: float | None = None,
    style: str = "stage3d",
    music_preset: str | None = None,
    deploy_pilot: bool = True,
    publish_youtube: bool = False,
    publish_tiktok: bool = False,
) -> dict[str, Any]:
    """Exécute la pipeline complète de création de contenu (Tech parlé 3D ou Clip Musical 3D)."""
    start_time = time.time()
    run_id = f"drop_{int(start_time)}"
    work_dir = output_dir / run_id
    work_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = work_dir / f"{run_id}_tiktok.mp4"

    if style == "music3d":
        logger.info("=== [CLIP MUSICAL 3D] Rendu Concert WebGL Three-VRM (Style Nexura Domina) ===")
        _, music_meta, video_duration = render_stage3d_music_video(
            output_mp4=out_mp4,
            work_dir=work_dir,
            preset_or_topic=music_preset or topic,
            custom_title=topic if (topic and "—" in topic) else None,
        )
        script_data: dict[str, Any] = {
            "title": music_meta["title"],
            "category": music_meta["category"],
            "preset_id": music_meta["preset_id"],
            "mode": "music3d",
        }
        with open(work_dir / "script.json", "w", encoding="utf-8") as f:
            json.dump(script_data, f, indent=2, ensure_ascii=False)
    else:
        logger.info("=== [1/4] Écriture du Script Viral Tech ===")
        script_data = generate_tech_script(topic=topic, model=model)
        script_file = work_dir / "script.json"
        with open(script_file, "w", encoding="utf-8") as f:
            json.dump(script_data, f, indent=2, ensure_ascii=False)
        logger.info("Titre : « %s » (%s)", script_data.get("title"), script_data.get("category"))
        for idx, s in enumerate(script_data.get("sentences", [])):
            logger.info("  [%d] %s", idx + 1, s)

        logger.info("=== [2/4] Synthèse Vocale Lia ===")
        synth_kwargs: dict[str, Any] = {
            "sentences": script_data.get("sentences", []),
            "work_dir": work_dir,
        }
        if voice:
            synth_kwargs["voice"] = voice
        if silence_sec is not None:
            synth_kwargs["initial_silence_sec"] = silence_sec

        audio_path, cues, video_duration = synthesize_script(**synth_kwargs)
        logger.info("Audio généré : %s (durée: %.2fs)", audio_path.name, video_duration)

        logger.info("=== [3/4] Génération des sous-titres (.ass & cues karaoké) ===")
        ass_path = work_dir / "subtitles.ass"
        generate_tiktok_ass_subtitles(cues, ass_path)

        if style == "stage3d":
            logger.info("=== [4/4] Rendu Scène 3D WebGL Three-VRM (Style Nexura Domina + Karaoké) ===")
            render_stage3d_tech_video(
                audio_path=audio_path,
                script_data=script_data,
                cues=cues,
                output_mp4=out_mp4,
                work_dir=work_dir,
            )
        elif style == "jrpg":
            logger.info("=== [4/4] Rendu & Composition Vidéo JRPG Rétro ===")
            render_jrpg_video(
                audio_path=audio_path,
                script_data=script_data,
                cues=cues,
                output_mp4=out_mp4,
            )
        else:
            logger.info("=== [4/4] Rendu & Composition Vidéo 1080x1920 (Avatar 2D Standard) ===")
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
    logger.info(
        "Fichier final : %s (%.2f Mo, durée %.1fs, calculé en %.1fs)",
        out_mp4,
        file_size_mb,
        video_duration,
        elapsed,
    )

    # Synchronisation automatique vers O:\OneDrive\Pictures\IA\Contenue via l'Agent Windows
    try:
        import httpx

        with httpx.Client(timeout=10.0) as client:
            res = client.post(
                "http://192.168.0.10:5005/execute",
                json={
                    "action": "copier_video_vers_onedrive",
                    "parameters": {"video_name": out_mp4.name, "run_id": run_id},
                },
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
                title=script_data.get("title", "Lia 3D — LBG Studios"),
            )
        except Exception as e:
            logger.error("Échec publication YouTube : %s", e)

    # Publication TikTok Studio
    tt_result = None
    if publish_tiktok:
        try:
            from tiktok_publisher import trigger_tiktok_upload

            if style == "music3d":
                tags = "#fyp #vtuber #3d #cyberpunk #aiidol #godotengine #lbgstudios"
            else:
                tags = "#fyp #ia #tech #dev #godotengine #3d #lbgstudios"
            caption = f"{script_data.get('title', 'LBG Studios 3D')} {tags}"
            tt_result = trigger_tiktok_upload(
                video_name=f"{run_id}_tiktok.mp4",
                caption=caption,
                local_video_path=out_mp4,
            )
        except Exception as e:
            logger.error("Échec préparation TikTok : %s", e)

    res_dict: dict[str, Any] = {
        "run_id": run_id,
        "style": style,
        "title": script_data.get("title", ""),
        "category": script_data.get("category", ""),
        "mp4_path": str(out_mp4),
        "file_size_mb": round(file_size_mb, 2),
        "duration_sec": round(video_duration, 2),
        "render_time_sec": round(elapsed, 2),
    }
    if yt_result:
        res_dict["youtube"] = yt_result
    if tt_result:
        res_dict["tiktok"] = tt_result

    return res_dict


def main() -> None:
    parser = argparse.ArgumentParser(description="Studio Content Bot — Pipeline Vidéo Avatar 3D 0€")
    parser.add_argument("--topic", type=str, default=None, help="Sujet Tech/MMO ou titre/preset musical")
    parser.add_argument("--demo", action="store_true", help="Génère la vidéo démo avec script canonique")
    parser.add_argument("--voice", type=str, default=None, help="Voix TTS (défaut: fr-FR-VivienneMultilingualNeural)")
    parser.add_argument("--silence", type=float, default=None, help="Secondes de silence au début (défaut: 0.3s)")
    parser.add_argument(
        "--style",
        type=str,
        default="stage3d",
        choices=["stage3d", "music3d", "jrpg", "standard"],
        help="Style de rendu vidéo (défaut: stage3d inspiré de Nexura Domina)",
    )
    parser.add_argument("--music-preset", type=str, default=None, help="Identifiant du preset musical pour music3d")
    parser.add_argument("--model", type=str, default="qwen2.5:3b", help="Modèle Ollama")
    parser.add_argument("--outdir", type=str, default=str(DEFAULT_OUTPUT_DIR), help="Dossier de sortie")
    parser.add_argument("--youtube", action="store_true", help="Publie sur la chaîne YouTube @LBG-p8k")
    parser.add_argument("--tiktok", action="store_true", help="Publie sur TikTok Studio")
    parser.add_argument("--pilot", action="store_true", help="Déploie la vidéo dans Pilot Web drops")
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
        style=args.style,
        music_preset=args.music_preset,
        publish_youtube=args.youtube,
        publish_tiktok=args.tiktok,
        deploy_pilot=args.pilot,
    )
    print("\n" + "=" * 50)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("=" * 50)


if __name__ == "__main__":
    main()
