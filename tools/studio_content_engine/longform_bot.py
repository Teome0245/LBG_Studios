#!/usr/bin/env python3
"""longform_bot.py — Studio Vidéos Longues 16:9 (4 à 15 min) avec Lia 3D & Slides Animées.

Inspiré du format éditorial @KiaraIAFR (IA locale, Hardware, Benchmarks honnêtes + Coulisses LBG) :
1. Mode Brouillon par défaut (Validation Humaine) :
     python tools/studio_content_engine/longform_bot.py --topic "..." --minutes 6
   -> Génère `script_long.json` + `BROUILLON_A_VALIDER.md` sans lancer le long calcul vidéo.

2. Rendu d'un brouillon validé / retouché :
     python tools/studio_content_engine/longform_bot.py --render tools/studio_content_engine/output/long_xxx

3. Mode 100% Autonome d'une traite (`--auto`) :
     python tools/studio_content_engine/longform_bot.py --auto --minutes 6 --youtube
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import math
import os
import shutil
import subprocess
import sys
import threading
import time
import wave
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from longform_script_builder import export_markdown_review, generate_longform_episode
from stage3d_compositor import (
    HOST_143_LAN_IP,
    OVERLAY_DIR,
    WIN10_AGENT_URL,
    WIN10_MIN_IDLE_SEC,
    _find_free_tcp_port,
    _find_free_x_display,
    _start_stage_http_server,
    compute_audio_telemetry,
    ensure_pcm_wav,
)
from voice_engine import SentenceCue, synthesize_script

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("longform_bot")

DEFAULT_OUTPUT_DIR = CURRENT_DIR / "output"
LONGFORM_HTML_TEMPLATE = CURRENT_DIR / "assets" / "stage3d" / "render_longform_16x9.html"

WIDTH_16X9 = 1920
HEIGHT_16X9 = 1080
FPS = 30


def select_presenter_motion_16x9(
    text: str,
    layout: str,
    sent_idx_in_ch: int,
    is_last_global: bool,
    seed_val: int,
) -> dict[str, Any]:
    """Choisit la posture 3D de Lia adaptée au plateau 16:9 (pointage vers la slide à droite, etc.)."""
    low = text.lower()
    if is_last_global or any(k in low for k in ["abonne-toi", "en commentaire", "retrouve toute"]):
        return {"pose": "fingerHeart", "cam": "hero_bust"}
    if layout == "hero":
        opts = [
            {"file": "wave_right.vrma", "speed": 0.9, "cam": "hero_bust"},
            {"pose": "pointScreen", "cam": "hero_bust"},
            {"file": "Having A Meeting, Female.vrma", "speed": 0.88, "cam": "hero_bust"},
        ]
        return opts[(seed_val + sent_idx_in_ch) % len(opts)]

    # En mode Split-Screen, la slide est à DROITE de l'écran (à la gauche anatomique de Lia face caméra = pointRight dans vrm_pet !)
    if any(k in low for k in ["regarde", "voici", "commande", "tableau", "schéma", "chiffres", "bilan", "mesures"]):
        return {"pose": "pointRight", "cam": "pod_mid"}
    if any(k in low for k in ["problème", "erreur", "attention", "limite", "mur", "sature", "facture"]):
        return {"pose": "think" if sent_idx_in_ch % 2 == 0 else "crossArms", "cam": "pod_close"}
    if any(k in low for k in ["zéro euro", "0 €", "fluidité", "succès", "parfait", "gagne"]):
        return {"pose": "approve", "cam": "pod_bust"}

    presenter_cycle = [
        {"file": "Having A Meeting, Female.vrma", "speed": 0.85, "cam": "pod_bust"},
        {"file": "Standing Using Touchscreen Tablet.vrma", "speed": 0.85, "cam": "pod_mid"},
        {"pose": "focus", "cam": "pod_bust"},
        {"pose": "pointRight", "cam": "pod_mid"},
    ]
    return presenter_cycle[(seed_val + sent_idx_in_ch) % len(presenter_cycle)]


def mix_longform_speech_with_bgm(speech_wav: Path, out_master_wav: Path, seed_key: str = "") -> Path:
    """Mixe la voix longue de Lia avec une nappe synthwave très douce (-20.5 dB) pour le confort d'écoute."""
    bgm_candidates = [
        OVERLAY_DIR / "audio" / "lia_synthwave_energy_instru_60s.wav",
        OVERLAY_DIR / "audio" / "lia_synthwave_30s_instru.wav",
        OVERLAY_DIR / "audio" / "lia_cyberpunk_track_30s.wav",
    ]
    existing = [p for p in bgm_candidates if p.is_file()]
    if not existing:
        shutil.copy2(speech_wav, out_master_wav)
        return out_master_wav

    idx = int(hashlib.md5(seed_key.encode("utf-8")).hexdigest()[:6], 16) % len(existing)
    bgm_path = existing[idx]

    with wave.open(str(speech_wav), "rb") as wf:
        speech_dur = wf.getnframes() / float(wf.getframerate())
    total_dur = speech_dur + 0.8
    fade_out_st = max(0.5, total_dur - 1.8)

    fc = (
        f"[0:a]aresample=44100,pan=stereo|c0=c0|c1=c0,apad=pad_dur=0.8[vox];"
        f"[1:a]aresample=44100,volume=0.095,afade=t=in:st=0:d=0.8,afade=t=out:st={fade_out_st:.2f}:d=1.8[bgm];"
        f"[vox][bgm]amix=inputs=2:duration=first:dropout_transition=0,alimiter=limit=0.95[outa]"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", str(speech_wav),
        "-stream_loop", "-1", "-i", str(bgm_path),
        "-filter_complex", fc,
        "-map", "[outa]",
        "-t", f"{total_dur:.3f}",
        "-c:a", "pcm_s16le",
        str(out_master_wav),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0 or not out_master_wav.exists():
        shutil.copy2(speech_wav, out_master_wav)
    return out_master_wav


def format_yt_timestamp(sec: float) -> str:
    s = max(0, int(sec))
    hrs = s // 3600
    mins = (s % 3600) // 60
    rem = s % 60
    if hrs > 0:
        return f"{hrs}:{mins:02d}:{rem:02d}"
    return f"{mins:02d}:{rem:02d}"


def build_youtube_description_with_chapters(episode: dict[str, Any], chapter_timings: list[dict[str, Any]]) -> str:
    lines = [
        episode.get("subtitle") or episode["title"],
        "",
        "Présenté par Lia (Avatar 3D temps réel Compagnon.vrm) — Contenu, mesures et sources vérifiés par l'équipe LBG Studios.",
        "",
        "⏱️ CHAPITRES DE LA VIDÉO :",
    ]
    for idx, ch in enumerate(chapter_timings):
        ts = "00:00" if idx == 0 else format_yt_timestamp(ch["start"])
        lines.append(f"{ts} - {ch['title']}")

    sources = episode.get("sources") or []
    if sources:
        lines += ["", "📚 SOURCES OFFICIELLES & DOCUMENTATION TECHNIQUE :"]
        for src in sources:
            lines.append(f"• {src}")

    lines += [
        "",
        "🛠️ SOUTENIR & SUIVRE LBG STUDIOS :",
        "• Abonne-toi et active la cloche pour nos prochains guides IA locale, Homelab & Devlog MMO 3D !",
        "• Vitrine officielle & univers Prime : https://laboiteageek.fr",
        "• Dépôt Open Source (Code, Architectures & Benchmarks) : https://github.com/Teome0245/LBG_Studios",
        "",
        "#IALocale #Homelab #SelfHosting #LLM #Ollama #Hardware #GodotEngine #OpenSource #LBGStudios",
    ]
    return "\n".join(lines)


async def _pipe_ws_16x9_to_ffmpeg(
    browser_launcher: Any,
    ws_port: int,
    expected_frames: int,
    master_audio_path: Path,
    output_mp4: Path,
    duration_limit_sec: float,
    timeout_sec: float,
) -> int:
    import websockets

    done_event = asyncio.Event()
    received_frames = 0
    err_box: list[str] = []

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "image2pipe",
        "-vcodec", "mjpeg",
        "-framerate", str(FPS),
        "-i", "-",
        "-i", str(master_audio_path),
        "-t", f"{duration_limit_sec:.3f}",
        "-vf", f"scale={WIDTH_16X9}:{HEIGHT_16X9}:flags=lanczos",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-preset", "fast",
        "-profile:v", "high",
        "-crf", "19",
        "-pix_fmt", "yuv420p",
        "-r", str(FPS),
        "-c:a", "aac",
        "-b:a", "256k",
        "-ar", "44100",
        "-shortest",
        str(output_mp4),
    ]
    ff_proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    async def ws_handler(websocket: Any) -> None:
        nonlocal received_frames
        try:
            async for msg in websocket:
                if isinstance(msg, bytes):
                    if ff_proc.stdin:
                        ff_proc.stdin.write(msg)
                    received_frames += 1
                    if received_frames % 20 == 0 or received_frames >= expected_frames:
                        await websocket.send("ACK")
                    if received_frames % 300 == 0:
                        logger.info(
                            "Rendu 16:9 déterministe : %d / %d frames (%.0f%%)",
                            received_frames,
                            expected_frames,
                            100.0 * received_frames / max(1, expected_frames),
                        )
                elif isinstance(msg, str) and msg == "DONE":
                    done_event.set()
                    break
        except Exception as exc:
            if not done_event.is_set():
                err_box.append(str(exc))
                done_event.set()

    try:
        async with websockets.serve(ws_handler, "0.0.0.0", ws_port, max_size=16 * 1024 * 1024):
            browser_launcher()
            await asyncio.wait_for(done_event.wait(), timeout=timeout_sec)
    finally:
        if ff_proc.stdin:
            try:
                ff_proc.stdin.close()
            except Exception:
                pass
        _, ff_err = ff_proc.communicate(timeout=60.0)

    if err_box:
        raise RuntimeError(f"Erreur WS 16:9 : {err_box[0]}")
    if ff_proc.returncode != 0 or not output_mp4.exists():
        raise RuntimeError(f"Échec FFmpeg 16:9 : {ff_err.decode('utf-8', errors='ignore')[-400:]}")
    return received_frames


async def _capture_single_png_via_ws(browser_launcher: Any, ws_port: int, out_png_1920: Path) -> None:
    import websockets

    done_event = asyncio.Event()
    png_bytes: list[bytes] = []

    async def ws_handler(websocket: Any) -> None:
        async for msg in websocket:
            if isinstance(msg, bytes):
                png_bytes.append(msg)
                await websocket.send("ACK")
            elif isinstance(msg, str) and msg == "DONE":
                done_event.set()
                break

    async with websockets.serve(ws_handler, "0.0.0.0", ws_port, max_size=24 * 1024 * 1024):
        browser_launcher()
        await asyncio.wait_for(done_event.wait(), timeout=45.0)

    if not png_bytes:
        raise RuntimeError("Aucune image miniature reçue via WebSocket.")
    out_png_1920.write_bytes(png_bytes[0])


def render_thumbnail_1280x720(stage_port: int, work_dir: Path, out_thumb_png: Path) -> Path:
    """Génère automatiquement la miniature YouTube 1280x720 haute visibilité avec Lia 3D."""
    disp_num = _find_free_x_display()
    display_str = f":{disp_num}"
    ws_port = _find_free_tcp_port("127.0.0.1")
    chr_profile = work_dir / "chr_thumb_profile"
    chr_profile.mkdir(parents=True, exist_ok=True)

    ws_param = quote(f"ws://127.0.0.1:{ws_port}", safe="")
    thumb_url = f"http://127.0.0.1:{stage_port}/job/render_longform_16x9.html?thumb=1&ws={ws_param}"
    raw_1920 = work_dir / "thumb_raw_1920.png"

    xvfb_proc = subprocess.Popen(
        ["Xvfb", display_str, "-screen", "0", "800x600x24", "-ac", "+extension", "GLX", "+render", "-noreset"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    chr_proc: subprocess.Popen[bytes] | None = None

    def launch_chr() -> None:
        nonlocal chr_proc
        env = dict(os.environ, DISPLAY=display_str)
        chromium_bin = shutil.which("chromium") or "chromium"
        chr_proc = subprocess.Popen(
            [
                chromium_bin,
                "--ozone-platform=x11",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--window-size=800,600",
                "--no-first-run",
                "--no-default-browser-check",
                "--ignore-gpu-blocklist",
                "--enable-webgl",
                "--use-gl=angle",
                "--use-angle=swiftshader",
                "--enable-unsafe-swiftshader",
                f"--user-data-dir={chr_profile}",
                thumb_url,
            ],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    try:
        time.sleep(0.4)
        asyncio.run(_capture_single_png_via_ws(launch_chr, ws_port, raw_1920))
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(raw_1920), "-vf", "scale=1280:720:flags=lanczos", str(out_thumb_png)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        raw_1920.unlink(missing_ok=True)
        return out_thumb_png
    finally:
        if chr_proc is not None:
            try:
                chr_proc.kill()
                chr_proc.wait(timeout=3)
            except Exception:
                pass
        try:
            xvfb_proc.kill()
            xvfb_proc.wait(timeout=3)
        except Exception:
            pass
        shutil.rmtree(chr_profile, ignore_errors=True)


def render_longform_project(
    project_dir: Path,
    voice: str | None = None,
    preview_sec: float | None = None,
    publish_youtube: bool = False,
    privacy: str = "public",
) -> dict[str, Any]:
    """Synthétise la voix par chapitre, rend la vidéo 16:9 30.00 FPS + la miniature 1280x720."""
    t_start = time.time()
    script_json = project_dir / "script_long.json"
    if not script_json.exists():
        raise FileNotFoundError(f"Fichier script_long.json introuvable dans {project_dir}")

    episode = json.loads(script_json.read_text(encoding="utf-8"))
    chapters = episode.get("chapters", [])
    if not chapters:
        raise ValueError("Aucun chapitre dans script_long.json")

    # Aplatir toutes les phrases tout en retenant les frontières exactes de chapitres
    flat_sentences: list[str] = []
    ch_sentence_ranges: list[tuple[int, int]] = []
    for ch in chapters:
        s_list = [str(s).strip() for s in ch.get("sentences", []) if str(s).strip()]
        idx_start = len(flat_sentences)
        flat_sentences.extend(s_list)
        ch_sentence_ranges.append((idx_start, len(flat_sentences)))

    # Si mode aperçu rapide (--preview-sec), ne synthétiser que les phrases nécessaires (+ marge)
    if preview_sec is not None and preview_sec > 0:
        max_sents = max(3, min(len(flat_sentences), int(math.ceil(preview_sec / 4.2)) + 2))
        synth_sentences = flat_sentences[:max_sents]
    else:
        synth_sentences = flat_sentences

    logger.info("=== [1/4] Synthèse Vocale Longue (%d phrases) ===", len(synth_sentences))
    synth_kwargs: dict[str, Any] = {
        "sentences": synth_sentences,
        "work_dir": project_dir / "tts_parts",
        "pause_between": 0.35,
        "initial_silence_sec": 0.4,
    }
    if voice:
        synth_kwargs["voice"] = voice

    speech_wav, cues, speech_dur = synthesize_script(**synth_kwargs)
    master_wav = project_dir / "longform_master_audio.wav"
    mix_longform_speech_with_bgm(speech_wav, master_wav, seed_key=episode.get("title", ""))

    analysis_wav = project_dir / "longform_analysis_mono.wav"
    _, full_audio_dur = ensure_pcm_wav(master_wav, analysis_wav)

    effective_dur = min(full_audio_dur, float(preview_sec)) if (preview_sec and preview_sec > 0) else full_audio_dur
    telemetry, _ = compute_audio_telemetry(analysis_wav, voice_only_wav=speech_wav, fps=FPS)
    max_tel_frames = int(math.ceil(effective_dur * FPS)) + 5
    telemetry = telemetry[:max_tel_frames]

    # Calculer les timestamps exacts de chaque chapitre
    seed_val = int(hashlib.md5(episode["title"].encode("utf-8")).hexdigest()[:6], 16)
    timeline_chapters: list[dict[str, Any]] = []
    motions: list[dict[str, Any]] = []
    subtitles: list[dict[str, Any]] = []

    for c_idx, (ch, (s_i0, s_i1)) in enumerate(zip(chapters, ch_sentence_ranges)):
        valid_cues: list[SentenceCue] = [cues[k] for k in range(s_i0, min(s_i1, len(cues)))]
        if not valid_cues:
            if preview_sec:
                break
            continue
        ch_start = 0.0 if c_idx == 0 else valid_cues[0].start
        ch_end = effective_dur if c_idx == len(chapters) - 1 else valid_cues[-1].end + 0.35
        if ch_start >= effective_dur:
            break
        ch_end = min(effective_dur, ch_end)

        ch_copy = dict(ch)
        ch_copy["index"] = c_idx
        ch_copy["start"] = round(ch_start, 3)
        ch_copy["end"] = round(ch_end, 3)
        timeline_chapters.append(ch_copy)

        for local_idx, cue in enumerate(valid_cues):
            if cue.start >= effective_dur:
                break
            m_end = min(effective_dur, cue.end + 0.35)
            is_last_glob = (s_i0 + local_idx) == (len(cues) - 1)
            m_spec = select_presenter_motion_16x9(
                cue.text,
                ch.get("layout", "split"),
                local_idx,
                is_last_glob,
                seed_val + c_idx,
            )
            m_entry: dict[str, Any] = {
                "start": round(0.0 if (c_idx == 0 and local_idx == 0) else cue.start, 3),
                "end": round(m_end, 3),
                **m_spec,
            }
            motions.append(m_entry)

            # Découper les longues phrases en segments de sous-titres de ~13 mots max pour le bandeau 16:9
            words = cue.words
            chunk_sz = 13
            for wi in range(0, len(words), chunk_sz):
                part_w = words[wi : wi + chunk_sz]
                st = cue.start + cue.duration * (wi / max(1, len(words)))
                en = cue.start + cue.duration * (min(len(words), wi + chunk_sz) / max(1, len(words)))
                if st < effective_dur:
                    subtitles.append({
                        "start": round(st, 3),
                        "end": round(min(effective_dur, en), 3),
                        "text": " ".join(part_w),
                    })

    if timeline_chapters:
        timeline_chapters[-1]["end"] = round(effective_dur, 3)

    timeline_payload = {
        "title": episode["title"],
        "subtitle": episode.get("subtitle", ""),
        "badge_topic": episode.get("badge_topic", "IA LOCALE & HARDWARE"),
        "thumbnail_hook": episode.get("thumbnail_hook", "GUIDE IA LOCALE"),
        "thumbnail_sub": episode.get("thumbnail_sub", "0€ CLOUD • CONCRET"),
        "duration": round(effective_dur, 3),
        "telemetry_fps": FPS,
        "chapters": timeline_chapters,
        "motions": motions,
        "subtitles": subtitles,
        "telemetry": telemetry,
    }
    (project_dir / "longform_timeline.json").write_text(
        json.dumps(timeline_payload, ensure_ascii=False), encoding="utf-8"
    )
    shutil.copy2(LONGFORM_HTML_TEMPLATE, project_dir / "render_longform_16x9.html")

    yt_desc = build_youtube_description_with_chapters(episode, timeline_chapters)
    (project_dir / "youtube_description.txt").write_text(yt_desc, encoding="utf-8")

    out_mp4 = project_dir / f"{project_dir.name}_16x9.mp4"
    out_thumb = project_dir / "thumbnail_1280x720.png"
    expected_frames = max(1, int(math.ceil(effective_dur * FPS)))

    srv, http_port = _start_stage_http_server(project_dir)
    try:
        logger.info("=== [2/4] Génération de la Miniature YouTube HD 1280x720 ===")
        render_thumbnail_1280x720(http_port, project_dir, out_thumb)
        logger.info("Miniature générée : %s", out_thumb)

        logger.info("=== [3/4] Rendu Vidéo Longue 16:9 Déterministe 30.00 FPS (%.1fs = %d frames) ===", effective_dur, expected_frames)
        rendered_on_win10 = False

        if os.environ.get("LBG_STAGE3D_FORCE_143", "0") != "1":
            try:
                with httpx.Client(timeout=2.0) as client:
                    hz = client.get(f"{WIN10_AGENT_URL}/healthz")
                if hz.status_code == 200:
                    ws_port = _find_free_tcp_port("0.0.0.0")
                    ws_param = quote(f"ws://{HOST_143_LAN_IP}:{ws_port}", safe="")
                    stage_url = f"http://{HOST_143_LAN_IP}:{http_port}/job/render_longform_16x9.html?hq3d=1&ws={ws_param}"

                    def _launch_win10() -> None:
                        def _post() -> None:
                            try:
                                with httpx.Client(timeout=max(120.0, effective_dur * 3.0)) as cl:
                                    cl.post(
                                        f"{WIN10_AGENT_URL}/execute",
                                        json={
                                            "action": "render_stage3d_clip",
                                            "parameters": {
                                                "stage_url": stage_url,
                                                "duration_sec": round(effective_dur, 2),
                                                "min_idle_sec": WIN10_MIN_IDLE_SEC,
                                            },
                                        },
                                    )
                            except Exception:
                                pass

                        threading.Thread(target=_post, daemon=True).start()

                    await_timeout = max(90.0, effective_dur * 2.5)
                    asyncio.run(
                        _pipe_ws_16x9_to_ffmpeg(
                            _launch_win10, ws_port, expected_frames, master_wav, out_mp4, effective_dur, await_timeout
                        )
                    )
                    rendered_on_win10 = True
                    logger.info("Rendu 16:9 accéléré GPU .10 réussi !")
            except Exception as exc:
                logger.info("GPU .10 indisponible ou occupé (%s) -> rendu déterministe sur .143.", exc)

        if not rendered_on_win10:
            disp_num = _find_free_x_display()
            display_str = f":{disp_num}"
            ws_port = _find_free_tcp_port("127.0.0.1")
            chr_profile = project_dir / "chr_16x9_profile"
            chr_profile.mkdir(parents=True, exist_ok=True)
            ws_param = quote(f"ws://127.0.0.1:{ws_port}", safe="")
            stage_url = f"http://127.0.0.1:{http_port}/job/render_longform_16x9.html?ws={ws_param}"

            xvfb_proc = subprocess.Popen(
                ["Xvfb", display_str, "-screen", "0", "960x540x24", "-ac", "+extension", "GLX", "+render", "-noreset"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            chr_proc: subprocess.Popen[bytes] | None = None

            def _launch_local() -> None:
                nonlocal chr_proc
                env = dict(os.environ, DISPLAY=display_str)
                chromium_bin = shutil.which("chromium") or "chromium"
                chr_proc = subprocess.Popen(
                    [
                        chromium_bin,
                        "--ozone-platform=x11",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--window-size=900,520",
                        "--no-first-run",
                        "--no-default-browser-check",
                        "--disable-background-timer-throttling",
                        "--disable-renderer-backgrounding",
                        "--disable-backgrounding-occluded-windows",
                        "--ignore-gpu-blocklist",
                        "--enable-webgl",
                        "--use-gl=angle",
                        "--use-angle=swiftshader",
                        "--enable-unsafe-swiftshader",
                        f"--user-data-dir={chr_profile}",
                        stage_url,
                    ],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

            try:
                time.sleep(0.5)
                asyncio.run(
                    _pipe_ws_16x9_to_ffmpeg(
                        _launch_local,
                        ws_port,
                        expected_frames,
                        master_wav,
                        out_mp4,
                        effective_dur,
                        timeout_sec=max(300.0, expected_frames * 0.85),
                    )
                )
            finally:
                if chr_proc is not None:
                    try:
                        chr_proc.kill()
                        chr_proc.wait(timeout=3)
                    except Exception:
                        pass
                try:
                    xvfb_proc.kill()
                    xvfb_proc.wait(timeout=3)
                except Exception:
                    pass
                shutil.rmtree(chr_profile, ignore_errors=True)
    finally:
        srv.shutdown()
        srv.server_close()

    yt_res = None
    if publish_youtube and not preview_sec:
        logger.info("=== [4/4] Publication YouTube Format Long 16:9 + Chapitres + Miniature ===")
        from youtube_publisher import upload_long_video

        yt_res = upload_long_video(
            video_path=out_mp4,
            title=episode["title"],
            description=yt_desc,
            thumbnail_path=out_thumb,
            privacy_status=privacy,
        )

    size_mb = out_mp4.stat().st_size / (1024 * 1024)
    res: dict[str, Any] = {
        "project_dir": str(project_dir),
        "title": episode["title"],
        "mp4_path": str(out_mp4),
        "thumbnail_path": str(out_thumb),
        "description_path": str(project_dir / "youtube_description.txt"),
        "duration_sec": round(effective_dur, 2),
        "chapters_count": len(timeline_chapters),
        "file_size_mb": round(size_mb, 2),
        "render_time_sec": round(time.time() - t_start, 2),
    }
    if yt_res:
        res["youtube"] = yt_res
    return res


def main() -> None:
    parser = argparse.ArgumentParser(description="LBG LongForm 16:9 Studio Bot (4-15 min, façon Kiara + Lia 3D)")
    parser.add_argument("--topic", type=str, default=None, help="Sujet de la vidéo longue (défaut: MoE 8 Go VRAM)")
    parser.add_argument("--minutes", type=float, default=5.5, help="Durée cible en minutes (entre 4 et 15)")
    parser.add_argument("--render", type=str, default=None, help="Dossier d'un brouillon existant à rendre en vidéo")
    parser.add_argument("--auto", action="store_true", help="Génère le script ET lance immédiatement le rendu 16:9")
    parser.add_argument("--preview-sec", type=float, default=None, help="Rend uniquement les N premières secondes pour test rapide")
    parser.add_argument("--voice", type=str, default=None, help="Voix TTS optionnelle")
    parser.add_argument("--youtube", action="store_true", help="Publie sur la chaîne YouTube @LBG-p8k")
    parser.add_argument("--privacy", type=str, default="public", choices=["public", "unlisted", "private"])
    parser.add_argument("--outdir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    if args.render:
        proj_dir = Path(args.render).resolve()
        result = render_longform_project(
            project_dir=proj_dir,
            voice=args.voice,
            preview_sec=args.preview_sec,
            publish_youtube=args.youtube,
            privacy=args.privacy,
        )
        print("\n" + "=" * 60)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("=" * 60)
        return

    # Étape 1 : Création du dossier projet et du brouillon éditable
    run_id = f"long_{int(time.time())}"
    proj_dir = Path(args.outdir) / run_id
    proj_dir.mkdir(parents=True, exist_ok=True)

    episode = generate_longform_episode(topic=args.topic, target_minutes=args.minutes)
    json_path = proj_dir / "script_long.json"
    md_path = proj_dir / "BROUILLON_A_VALIDER.md"

    json_path.write_text(json.dumps(episode, indent=2, ensure_ascii=False), encoding="utf-8")
    export_markdown_review(episode, json_path, md_path)

    logger.info("Brouillon généré : %s (~%.1f min, %d mots)", md_path, episode["estimated_minutes"], episode["word_count"])

    if not args.auto and not args.preview_sec:
        print("\n" + "=" * 60)
        print(json.dumps({
            "mode": "draft_ready_for_review",
            "project_dir": str(proj_dir),
            "title": episode["title"],
            "estimated_minutes": episode["estimated_minutes"],
            "word_count": episode["word_count"],
            "chapters": len(episode["chapters"]),
            "markdown_review": str(md_path),
            "editable_json": str(json_path),
            "next_command_to_render": f"packages/cortex/.venv/bin/python tools/studio_content_engine/longform_bot.py --render {proj_dir}",
        }, indent=2, ensure_ascii=False))
        print("=" * 60)
        return

    result = render_longform_project(
        project_dir=proj_dir,
        voice=args.voice,
        preview_sec=args.preview_sec,
        publish_youtube=args.youtube,
        privacy=args.privacy,
    )
    print("\n" + "=" * 60)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("=" * 60)


if __name__ == "__main__":
    main()
