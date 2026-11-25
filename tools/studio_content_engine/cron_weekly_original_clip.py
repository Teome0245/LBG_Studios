#!/usr/bin/env python3
"""cron_weekly_original_clip.py — Usine Hebdomadaire de Clip Musical Original (Samedi).

Chaque semaine (ou à la demande) :
1. Compose un NOUVEAU morceau original inédit de 60 secondes via MusicGen local + paroles Ollama + voix chantée de Lia
   (en faisant tourner les 7 genres de `studio_music_generator_v3.py`).
2. Enregistre 2 presets chorégraphiques verticaux 9:16 (`Part 1 — Couplet Groove 0-30s` et `Part 2 — Drop Climax 30-60s`)
   dans `custom_music_tracks.json` ET les insère en priorité dans `topics_backlog.json` pour diffusion automatique
   sur **TikTok ET YouTube Shorts** !
3. Option `--publish-full-youtube` (actif le samedi) : rend et publie aussi la version intégrale 60s sur YouTube (`@LBG-p8k`)
   avec miniature `1280x720` dédiée !
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("weekly_original_clip")

ENGINE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ENGINE_DIR.parents[1]
OVERLAY_DIR = REPO_ROOT / "packages" / "compagnon-desktop" / "overlay"
AUDIO_VENV_PY = REPO_ROOT / ".venv_audio" / "bin" / "python"
CORTEX_VENV_PY = REPO_ROOT / "packages" / "cortex" / ".venv" / "bin" / "python"

CUSTOM_TRACKS_FILE = ENGINE_DIR / "custom_music_tracks.json"
SHORTS_BACKLOG_FILE = ENGINE_DIR / "topics_backlog.json"

STYLE_ROTATION: list[tuple[str, str, str, int, str]] = [
    ("cyberpunk", "diva", "Neon Pulse", 128, "cyan_rose"),
    ("tatooine_sunset", "diva", "Mirage de Lost Heaven", 124, "amber_cyan"),
    ("synthwave", "autotune", "Horizon 1988", 115, "cyan_rose"),
    ("kpop_energy", "autotune", "Starlight Core", 130, "cyan_rose"),
    ("french_touch", "vocoder", " Midnight Circuit", 120, "amber_cyan"),
    ("dark_techno", "diva", "Subspace Override", 132, "cyan_rose"),
    ("chill_lofi", "whisper", "Pluie sur Proxmox", 85, "cyan_rose"),
]


def compose_new_60s_song(week_idx: int) -> dict[str, Any]:
    style_key, vox_style, base_theme, bpm, palette = STYLE_ROTATION[week_idx % len(STYLE_ROTATION)]
    date_tag = datetime.date.today().strftime("%Y%m%d")
    track_slug = f"orig_{style_key}_{date_tag}"
    song_title = f"LIA — {base_theme.strip()} #{week_idx + 1}"

    py_bin = str(AUDIO_VENV_PY if AUDIO_VENV_PY.exists() else CORTEX_VENV_PY)
    logger.info("=== [1/3] Composition Musicale Originale 60s : %s (%s, %d BPM) ===", song_title, style_key, bpm)

    inline_code = (
        "import sys; sys.path.insert(0, 'tools'); "
        "import studio_music_generator_v3 as mg; "
        f"secs = mg.generate_structured_lyrics('{style_key}', duration=60); "
        f"inst = 'packages/compagnon-desktop/overlay/audio/{track_slug}_instru.wav'; "
        f"mast = 'packages/compagnon-desktop/overlay/audio/{track_slug}_master.wav'; "
        f"mg.generate_instrumental_track(mg.MUSIC_STYLES['{style_key}']['prompt'], duration=60, output_wav=inst); "
        f"vox = mg.synthesize_vocal_sections(secs, vocal_style='{vox_style}'); "
        f"mg.mix_master_v3(inst, vox, mast, duration=60, vocal_style='{vox_style}')"
    )
    subprocess.run([py_bin, "-c", inline_code], cwd=str(REPO_ROOT), check=True)

    rel_audio = f"audio/{track_slug}_master.wav"
    if not (OVERLAY_DIR / rel_audio).exists():
        raise RuntimeError(f"Master audio introuvable après génération : {OVERLAY_DIR / rel_audio}")

    return {
        "slug": track_slug,
        "song_title": song_title,
        "style_key": style_key,
        "bpm": bpm,
        "palette": palette,
        "audio_rel": rel_audio,
    }


def register_two_shorts_from_song(song_info: dict[str, Any]) -> tuple[str, str]:
    """Crée 2 presets chorégraphiés 30s (Part 1 Groove + Part 2 Climax) et les programme sur TikTok & Shorts."""
    slug = song_info["slug"]
    title = song_info["song_title"]
    bpm = song_info["bpm"]
    palette = song_info["palette"]
    audio_rel = song_info["audio_rel"]

    p1_id = f"{slug}_part1"
    p2_id = f"{slug}_part2"

    preset_part1 = {
        "id": p1_id,
        "title": f"{title} (Clip 3D Original • Partie 1)",
        "category": "Single Original IA & 3D",
        "audio_rel": audio_rel,
        "start_offset_sec": 0.0,
        "duration_sec": 30.0,
        "bpm": bpm,
        "palette": palette,
        "motions": [
            {"dur": 4.0, "file": "Female Dance Pose1.vrma", "label": "Ouverture Single", "cam": "push_in", "exp": "mystique", "exp_label": "Intro Inédite"},
            {"dur": 9.0, "file": "Dancing Maraschino Step.vrma", "label": "Maraschino Groove", "cam": "mid", "exp": "idol", "exp_label": "Couplet Original"},
            {"dur": 9.0, "file": "Jazz Dancing3.vrma", "label": "Electro Jazz", "cam": "front_arc", "exp": "diva", "exp_label": "Montée Rythmique"},
            {"dur": 5.0, "file": "swg_poplock_loop.vrma", "label": "Cyber Poplock", "cam": "pull_out", "exp": "climax", "exp_label": "Pré-Drop"},
            {"dur": 3.0, "pose": "fingerHeart", "label": "Signature Lia", "cam": "bust", "exp": "idol", "exp_label": "LBG Music"},
        ],
    }

    preset_part2 = {
        "id": p2_id,
        "title": f"{title} (Drop & Climax 3D • Partie 2)",
        "category": "Single Original IA & 3D",
        "audio_rel": audio_rel,
        "start_offset_sec": 29.5,
        "duration_sec": 30.0,
        "bpm": bpm,
        "palette": palette,
        "motions": [
            {"dur": 4.0, "file": "Crazy Gesture.vrma", "label": "Lancement Drop", "cam": "push_in", "exp": "diva", "exp_label": "Tension Drop"},
            {"dur": 9.5, "file": "Hip Hop Dancing3.vrma", "label": "Drop Hip-Hop Cyber", "cam": "full", "exp": "climax", "exp_label": "Refrain Climax"},
            {"dur": 9.5, "file": "Bellydancing.vrma", "label": "Ondulation Néon", "cam": "drone_arc180", "exp": "diva", "exp_label": "Solo Vocal"},
            {"dur": 4.0, "file": "Pro_Magic_Pack_Standing 2H Cast Spell 01.vrma", "label": "Final Scénique", "cam": "pull_out", "exp": "climax", "exp_label": "Apothéose"},
            {"dur": 3.0, "pose": "fingerHeart", "label": "Cœur Final", "cam": "bust", "exp": "idol", "exp_label": "Single Original LBG"},
        ],
    }

    existing_tracks: list[dict[str, Any]] = []
    if CUSTOM_TRACKS_FILE.exists():
        try:
            existing_tracks = json.loads(CUSTOM_TRACKS_FILE.read_text(encoding="utf-8"))
        except Exception:
            existing_tracks = []
    existing_tracks = [t for t in existing_tracks if t.get("id") not in (p1_id, p2_id)]
    existing_tracks.insert(0, preset_part2)
    existing_tracks.insert(0, preset_part1)
    CUSTOM_TRACKS_FILE.write_text(json.dumps(existing_tracks, indent=2, ensure_ascii=False), encoding="utf-8")

    # Insérer les 2 Shorts en priorité dans topics_backlog.json (avec 1 Short Tech intercalé pour varier le flux)
    backlog: list[dict[str, Any]] = []
    if SHORTS_BACKLOG_FILE.exists():
        backlog = json.loads(SHORTS_BACKLOG_FILE.read_text(encoding="utf-8"))
    cur_id = max((int(x.get("id", 0)) for x in backlog), default=0)

    item1 = {
        "id": cur_id + 1,
        "topic": preset_part1["title"],
        "category": "Single Original IA & 3D",
        "format": "music3d",
        "music_preset": p1_id,
        "status": "pending",
    }
    item2 = {
        "id": cur_id + 2,
        "topic": preset_part2["title"],
        "category": "Single Original IA & 3D",
        "format": "music3d",
        "music_preset": p2_id,
        "status": "pending",
    }

    published = [x for x in backlog if x.get("status") != "pending"]
    pending = [x for x in backlog if x.get("status") == "pending"]
    if pending:
        new_pending = [item1, pending[0], item2] + pending[1:]
    else:
        new_pending = [item1, item2]
    SHORTS_BACKLOG_FILE.write_text(json.dumps(published + new_pending, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("2 Shorts originaux programmés dans topics_backlog.json (TikTok + YouTube Shorts) : %s & %s", p1_id, p2_id)
    return p1_id, p2_id


def render_and_publish_full_60s_clip(song_info: dict[str, Any], publish_youtube: bool = True) -> dict[str, Any]:
    """Rend le clip intégral de 60s et le publie comme vidéo officielle (hors #Shorts) sur YouTube."""
    sys.path.insert(0, str(ENGINE_DIR))
    from longform_bot import render_thumbnail_1280x720
    from stage3d_compositor import (
        FPS,
        _render_on_local_143_deterministic,
        _start_stage_http_server,
        _try_render_on_win10_gpu,
        build_music_timeline_and_audio,
    )

    work_dir = ENGINE_DIR / "output" / f"single_{song_info['slug']}_{int(time.time())}"
    work_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = work_dir / f"{song_info['slug']}_full_60s.mp4"
    out_thumb = work_dir / "thumbnail_1280x720.png"

    full_preset = {
        "id": f"{song_info['slug']}_full60",
        "title": f"{song_info['song_title']} (Clip 3D Officiel Intégral) | LBG Studios",
        "category": "Clip Musical IA Original",
        "audio_rel": song_info["audio_rel"],
        "start_offset_sec": 0.0,
        "duration_sec": 59.5,
        "bpm": song_info["bpm"],
        "palette": song_info["palette"],
        "motions": [
            {"dur": 5.0, "file": "Female Dance Pose1.vrma", "label": "Intro Scénique", "cam": "push_in", "exp": "mystique", "exp_label": "Ouverture Live"},
            {"dur": 11.0, "file": "Dancing Maraschino Step.vrma", "label": "Couplet 1 Groove", "cam": "mid", "exp": "idol", "exp_label": "Chant Original"},
            {"dur": 11.0, "file": "Bellydancing.vrma", "label": "Refrain 1 Néon", "cam": "drone_arc180", "exp": "climax", "exp_label": "Refrain 1"},
            {"dur": 10.0, "file": "swg_poplock_loop.vrma", "label": "Pont Cyber SWG", "cam": "front_arc", "exp": "diva", "exp_label": "Solo Synthé"},
            {"dur": 11.5, "file": "Hip Hop Dancing3.vrma", "label": "Drop Climax", "cam": "full", "exp": "climax", "exp_label": "Drop Final"},
            {"dur": 6.5, "file": "Jazz Dancing3.vrma", "label": "Encore Scénique", "cam": "pull_out", "exp": "diva", "exp_label": "Outro Live"},
            {"dur": 4.5, "pose": "fingerHeart", "label": "Signature Lia", "cam": "bust", "exp": "idol", "exp_label": "LBG Studios"},
        ],
    }

    timeline, master_wav, actual_dur = build_music_timeline_and_audio(work_dir, full_preset)
    (work_dir / "stage_timeline.json").write_text(json.dumps(timeline, ensure_ascii=False), encoding="utf-8")
    shutil.copy2(ENGINE_DIR / "assets" / "stage3d" / "render_stage3d.html", work_dir / "render_stage3d.html")

    # Préparer aussi la miniature 1280x720
    thumb_tl = {
        "title": full_preset["title"],
        "badge_topic": f"SINGLE ORIGINAL • {song_info['bpm']} BPM",
        "thumbnail_hook": song_info["song_title"].replace("LIA — ", "").upper(),
        "thumbnail_sub": "CLIP 3D OFFICIEL INTÉGRAL",
        "duration": 5.0,
        "telemetry_fps": FPS,
        "chapters": [{"index": 0, "start": 0, "end": 5, "layout": "hero", "title": "Clip"}],
        "motions": [{"start": 0, "end": 5, "file": "Female Dance Pose1.vrma", "cam": "hero_bust"}],
    }
    (work_dir / "longform_timeline.json").write_text(json.dumps(thumb_tl, ensure_ascii=False), encoding="utf-8")
    shutil.copy2(ENGINE_DIR / "assets" / "stage3d" / "render_longform_16x9.html", work_dir / "render_longform_16x9.html")

    srv, port = _start_stage_http_server(work_dir)
    try:
        render_thumbnail_1280x720(port, work_dir, out_thumb)
        if not _try_render_on_win10_gpu(port, actual_dur, master_wav, out_mp4):
            _render_on_local_143_deterministic(port, actual_dur, work_dir, master_wav, out_mp4)
    finally:
        srv.shutdown()
        srv.server_close()

    yt_res = None
    if publish_youtube:
        from youtube_publisher import upload_long_video

        desc = (
            f"{full_preset['title']}\n\n"
            f"🎵 Composition instrumentale originale ({song_info['bpm']} BPM) générée localement sous MusicGen + chant Lia & chorégraphie Three-VRM.\n\n"
            "⏱️ CHAPITRES DU CLIP :\n"
            "00:00 - Ouverture & Couplet 1\n"
            "00:16 - Premier Refrain Néon\n"
            "00:27 - Pont Cyber & Danses Mocap\n"
            "00:37 - Drop Climax & Final Idol\n\n"
            "📚 Sources & Technologies Open Source utilisées :\n"
            "• AudioCraft / MusicGen (Meta Research) : https://github.com/facebookresearch/audiocraft\n"
            "• Standard Avatar 3D Three-VRM : https://github.com/pixiv/three-vrm\n"
            "• Studio & Projet MMO Prime : https://laboiteageek.fr\n"
            "• Dépôt GitHub LBG Studios : https://github.com/Teome0245/LBG_Studios\n\n"
            "#AIMusic #VTuber #3DAnimation #Cyberpunk #Synthwave #OpenSource #LBGStudios"
        )
        # Remuxer en 16:9 letterbox flouté cinématique pour que YouTube le traite en vraie vidéo (et non en Short !)
        out_16x9_mp4 = work_dir / f"{song_info['slug']}_youtube_16x9.mp4"
        blur_fc = (
            "[0:v]split=2[bg][fg];"
            "[bg]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,boxblur=28:4,eq=brightness=-0.18[bgb];"
            "[fg]scale=-2:1080:flags=lanczos[fgs];"
            "[bgb][fgs]overlay=(W-w)/2:0[vout]"
        )
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(out_mp4),
                "-filter_complex", blur_fc,
                "-map", "[vout]", "-map", "0:a:0",
                "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
                "-c:a", "copy", str(out_16x9_mp4),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        yt_res = upload_long_video(
            video_path=out_16x9_mp4,
            title=full_preset["title"],
            description=desc,
            tags=["ai music", "vtuber fr", "clip 3d", "synthwave", "cyberpunk", "musicgen", "lbg studios"],
            thumbnail_path=out_thumb,
            privacy_status="public",
        )

    return {
        "song": song_info,
        "mp4_9x16": str(out_mp4),
        "thumbnail": str(out_thumb),
        "youtube": yt_res,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Usine Hebdomadaire de Single Musical Original + Clip 3D + 2 Shorts")
    parser.add_argument("--shorts-only", action="store_true", help="Compose le morceau et programme les 2 Shorts sans publier le clip 16:9 complet")
    parser.add_argument("--no-youtube", action="store_true", help="Génère le clip complet localement sans upload YouTube")
    args = parser.parse_args()

    iso_year, iso_week, _ = datetime.date.today().isocalendar()
    week_idx = iso_year * 53 + iso_week

    song_info = compose_new_60s_song(week_idx)
    p1, p2 = register_two_shorts_from_song(song_info)

    result: dict[str, Any] = {"song": song_info, "scheduled_shorts": [p1, p2]}
    if not args.shorts_only:
        clip_res = render_and_publish_full_60s_clip(song_info, publish_youtube=not args.no_youtube)
        result["full_clip"] = clip_res

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
