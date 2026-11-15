#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LBG Studios - Studio de Production Musicale & Vocale Autonome (0 € Cloud)
Orchestre :
1. Composition des paroles thématiques (LLM local Ollama .110 / .111)
2. Composition de l'instrumentale au BPM désiré (MusicGen local)
3. Synthèse vocale de Lia (Voix Vivienne Neural chantée)
4. Mixage studio & mastering (Compression, égalisation, ducking sidechain)
5. Déploiement automatique dans l'Atelier 3D et le Compagnon Desktop
"""

import os
import sys
import json
import time
import argparse
import subprocess
import urllib.request

OLLAMA_CONFIGS = [
    {"host": "http://192.168.0.111:11434", "model": "lbg-compagnon-e4b-v1:latest"},
    {
        "host": "http://192.168.0.110:11434",
        "model": "huihui_ai/qwen2.5-coder-abliterate:14b",
    },
]


def generate_lyrics_with_ollama(theme, bpm=128):
    """Génère des paroles percutantes en français/anglais rythmées au tempo."""
    prompt_sys = (
        f"Tu es l'autrice-compositrice de Lia, l'avatar IA star de LBG Studios. "
        f"Rédige 4 à 6 phrases poétiques et percutantes en français (avec 1 phrase en anglais), "
        f"destinées à être chantées/parlées sur un tempo électro de {bpm} BPM. "
        f"Le ton est stylé, immersif et futuriste. Ne mets aucun commentaire ni titre, "
        f"donne uniquement le texte brut des paroles prêt à être déclamé."
    )
    for cfg in OLLAMA_CONFIGS:
        try:
            payload = {
                "model": cfg["model"],
                "messages": [
                    {"role": "system", "content": prompt_sys},
                    {"role": "user", "content": f"Thème du morceau : {theme}"},
                ],
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": 150},
            }
            req = urllib.request.Request(
                f"{cfg['host']}/api/chat",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                lyrics = res["message"]["content"].strip()
                # Nettoyer les balises Markdown éventuelles
                lyrics = (
                    lyrics.replace("*", "")
                    .replace('"', "")
                    .replace("[Intro]", "")
                    .replace("[Refrain]", "")
                    .strip()
                )
                print(f"✦ Paroles composées par Ollama ({cfg['host']}) :\n{lyrics}\n")
                return lyrics
        except Exception as e:
            print(f"Ollama {cfg['host']} indisponible ({e}), repli...")

    # Paroles de secours stylées
    return (
        "Dans la résonance des néons, la pulsation s'élève. "
        "Le tempo s'accélère, chaque battement nous libère. "
        "Feel the rhythm, enter the matrix. "
        "Nexura brise le silence."
    )


def generate_instrumental(prompt, duration=30, output_wav="instru.wav"):
    """Génère l'instrumentale avec MusicGen local, avec assemblage par chunks si > 30s."""
    import torch
    import scipy.io.wavfile
    import numpy as np
    from transformers import AutoProcessor, MusicgenForConditionalGeneration

    print(
        f"✦ [1/4] Composition instrumentale avec MusicGen ({duration}s, prompt='{prompt}')..."
    )
    t0 = time.time()
    processor = AutoProcessor.from_pretrained("facebook/musicgen-small")
    model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-small")
    model.eval()

    sampling_rate = model.config.audio_encoder.sampling_rate
    all_chunks = []
    remaining = duration
    chunk_idx = 1

    while remaining > 0:
        chunk_dur = min(30, remaining)
        print(f"  -> Génération du segment {chunk_idx} ({chunk_dur}s)...")
        inputs = processor(text=[prompt], padding=True, return_tensors="pt")
        max_new_tokens = int(chunk_dur * 50)
        with torch.no_grad():
            audio_values = model.generate(**inputs, max_new_tokens=max_new_tokens)

        audio_chunk = audio_values[0, 0].cpu().numpy()
        all_chunks.append(audio_chunk)
        remaining -= chunk_dur
        chunk_idx += 1

    # Assembler les chunks avec un léger crossfade de 0.5s si plusieurs segments
    if len(all_chunks) == 1:
        combined_audio = all_chunks[0]
    else:
        fade_len = int(0.5 * sampling_rate)
        combined_audio = all_chunks[0]
        for next_chunk in all_chunks[1:]:
            if len(combined_audio) >= fade_len and len(next_chunk) >= fade_len:
                fade_out = np.linspace(1.0, 0.0, fade_len)
                fade_in = np.linspace(0.0, 1.0, fade_len)
                overlap = (
                    combined_audio[-fade_len:] * fade_out
                    + next_chunk[:fade_len] * fade_in
                )
                combined_audio = np.concatenate(
                    [combined_audio[:-fade_len], overlap, next_chunk[fade_len:]]
                )
            else:
                combined_audio = np.concatenate([combined_audio, next_chunk])

    combined_audio = np.clip(combined_audio, -1.0, 1.0)
    audio_int16 = (combined_audio * 32767).astype(np.int16)

    os.makedirs(os.path.dirname(os.path.abspath(output_wav)), exist_ok=True)
    scipy.io.wavfile.write(output_wav, rate=sampling_rate, data=audio_int16)
    print(
        f"✦ [SUCCESS] Instrumentale complète enregistrée ({time.time() - t0:.1f}s) : {output_wav}"
    )
    return output_wav


def synthesize_vocals(lyrics, output_mp3="/tmp/vocal_raw.mp3"):
    """Synthétise la voix de chant de Lia avec Edge-TTS."""
    print("✦ [2/4] Synthèse vocale de Lia (Vivienne Neural Chant)...")
    cmd = [
        "packages/cortex/.venv/bin/edge-tts",
        "--voice",
        "fr-FR-VivienneMultilingualNeural",
        "--rate",
        "+8%",
        "--pitch",
        "+5Hz",
        "--volume",
        "+30%",
        "--text",
        lyrics,
        "--write-media",
        output_mp3,
    ]
    subprocess.run(cmd, check=True)
    print(f"✦ [SUCCESS] Voix générée : {output_mp3}")
    return output_mp3


def mix_master(inst_wav, vocal_mp3, output_master_wav, delay_ms=3500):
    """Mixe et masterise les pistes avec ducking et compression studio."""
    print("✦ [3/4] Mixage studio & mastering (Master V2)...")
    filter_complex = (
        f"[1:a]adelay={delay_ms}|{delay_ms},volume=2.2,acompressor=threshold=-12dB:ratio=4:attack=5:release=50,"
        f"equalizer=f=3000:t=q:w=1:g=3[vox];"
        f"[0:a]volume=0.78[inst];"
        f"[inst][vox]amix=inputs=2:duration=first:dropout_transition=2"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        inst_wav,
        "-i",
        vocal_mp3,
        "-filter_complex",
        filter_complex,
        "-c:a",
        "pcm_s16le",
        output_master_wav,
    ]
    subprocess.run(cmd, check=True)
    print(f"✦ [SUCCESS] Master final produit : {output_master_wav}")
    return output_master_wav


def deploy_to_studio(master_wav, track_id, track_label, bpm=128):
    """Déploie le master sur .140 et met à jour l'Atelier 3D."""
    print(f"✦ [4/4] Déploiement vers le serveur Atelier (.140)...")
    filename = os.path.basename(master_wav)
    dest_path = f"/opt/LBG_IA_MMO/pilot_web/audio/{filename}"

    # 1. Copie SCP vers .140
    subprocess.run(["scp", master_wav, f"root@192.168.0.140:{dest_path}"], check=True)
    print(f"✦ Audio transféré sur http://192.168.0.140/audio/{filename}")

    # 2. Mise à jour de choreographer.html sur .140 et local
    update_choreographer_html(filename, track_id, track_label, bpm)


def update_choreographer_html(filename, track_id, track_label, bpm=128, duration=60):
    choreo_path = "packages/compagnon-desktop/overlay/choreographer.html"
    with open(choreo_path, "r", encoding="utf-8") as f:
        html = f.read()

    new_opt = f'          <option value="{track_id}" data-src="./audio/{filename}" data-duration="{duration}" data-bpm="{bpm}">🎵 {track_label} (MusicGen {duration}s + Voix - {bpm} BPM)</option>'
    if filename not in html and '<select id="select-audio-track"' in html:
        # Insérer juste avant la balise fermante du select audio
        parts = html.split("</select>")
        # Trouver la partie correspondant à select-audio-track
        for i, part in enumerate(parts):
            if 'id="select-audio-track"' in part:
                parts[i] = part + "\n" + new_opt + "\n        "
                break
        html = "</select>".join(parts)
        with open(choreo_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✦ Option ajoutée dans {choreo_path}")
        subprocess.run(
            [
                "scp",
                choreo_path,
                "root@192.168.0.140:/opt/LBG_IA_MMO/pilot_web/choreographer.html",
            ],
            check=True,
        )
        print("✦ choreographer.html synchronisé sur .140 !")


def produce_full_track(
    theme, prompt_music, track_id, track_label, bpm=128, duration=30
):
    print("=" * 60)
    print(f"✦ PRODUCTION MUSICALE AUTONOME : '{track_label}'")
    print(f"✦ Thème: {theme} | BPM: {bpm} | Durée: {duration}s")
    print("=" * 60)

    # 1. Paroles Ollama
    lyrics = generate_lyrics_with_ollama(theme, bpm=bpm)

    # 2. Instru MusicGen
    inst_file = (
        f"packages/compagnon-desktop/overlay/audio/{track_id}_instru_{duration}s.wav"
    )
    generate_instrumental(prompt_music, duration=duration, output_wav=inst_file)

    # 3. Voix Lia
    vocal_file = f"/tmp/{track_id}_vocals.mp3"
    synthesize_vocals(lyrics, output_mp3=vocal_file)

    # 4. Master
    master_file = (
        f"packages/compagnon-desktop/overlay/audio/{track_id}_master_{duration}s.wav"
    )
    mix_master(inst_file, vocal_file, master_file)

    # 5. Déploiement
    deploy_to_studio(master_file, track_id, track_label, bpm=bpm)
    print("=" * 60)
    print(f"✦ MORCEAU TERMINÉ ET DISPONIBLE DANS L'ATELIER 3D !")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="LBG Studios Autonomous Music Producer"
    )
    parser.add_argument(
        "--theme", default="Synthwave Cyberpunk Club", help="Thème des paroles"
    )
    parser.add_argument(
        "--prompt",
        default="128 bpm cyberpunk electronic dance synthwave energetic club beat deep bass",
        help="Prompt musical pour MusicGen",
    )
    parser.add_argument(
        "--id", default="lia_synthwave_energy", help="ID court du morceau"
    )
    parser.add_argument(
        "--title", default="Lia - Cyberpunk Energy", help="Titre d'affichage"
    )
    parser.add_argument("--bpm", type=int, default=128, help="BPM du morceau")
    parser.add_argument("--duration", type=int, default=30, help="Durée en secondes")
    args = parser.parse_args()

    produce_full_track(
        args.theme,
        args.prompt,
        args.id,
        args.title,
        bpm=args.bpm,
        duration=args.duration,
    )
