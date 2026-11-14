#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LBG Studios - Générateur Musical Local (0 € Cloud)
- Paroles & Structure : LLM Ollama local (.110 / .111)
- Composition Instrumentale : MusicGen (facebook/musicgen-small)
- Export direct pour l'Atelier de Chorégraphie 3D et le Compagnon
"""

import os
import sys
import json
import time
import argparse
import urllib.request
import scipy.io.wavfile
import numpy as np

OLLAMA_CONFIGS = [
    {"host": "http://192.168.0.111:11434", "model": "lbg-compagnon-e4b-v1:latest"},
    {"host": "http://192.168.0.110:11434", "model": "huihui_ai/qwen2.5-coder-abliterate:14b"}
]

def generate_lyrics(prompt_theme, style_bpm=128):
    """Génère des paroles structurées adaptées au tempo et au style via Ollama local."""
    system_prompt = (
        f"Tu es l'autrice-compositrice de Lia, l'avatar IA de LBG Studios. "
        f"Compose des paroles percutantes en français (avec quelques hooks en anglais) "
        f"pour un morceau au tempo de {style_bpm} BPM. "
        f"Format strict requis :\n"
        f"[Intro]\n...\n"
        f"[Couplet 1]\n...\n"
        f"[Refrain]\n...\n"
        f"[Couplet 2]\n...\n"
        f"[Refrain]\n...\n"
        f"[Outro]\n..."
    )
    
    for cfg in OLLAMA_CONFIGS:
        host = cfg["host"]
        model = cfg["model"]
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Thème : {prompt_theme}"}
            ],
            "stream": False,
            "options": {"temperature": 0.7, "num_predict": 400}
        }
        try:
            req = urllib.request.Request(
                f"{host}/api/chat",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["message"]["content"]
        except Exception as e:
            print(f"Warning: {host} with model {model} failed ({e}), trying next host...")
    
    return "[Intro]\nDans la nuit néon...\n[Refrain]\nNexura s'éveille, au rythme du son..."

def generate_instrumental(prompt, duration_seconds=15, output_wav="studio_output.wav"):
    """Génère une piste instrumentale via MusicGen."""
    import torch
    from transformers import AutoProcessor, MusicgenForConditionalGeneration

    print(f"✦ Chargement de MusicGen (facebook/musicgen-small)...")
    processor = AutoProcessor.from_pretrained("facebook/musicgen-small")
    model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-small")
    model.eval()

    print(f"✦ Composition du morceau pour prompt : '{prompt}' ({duration_seconds}s)...")
    inputs = processor(
        text=[prompt],
        padding=True,
        return_tensors="pt",
    )

    # MusicGen génère 50 tokens audio par seconde de musique
    max_new_tokens = int(duration_seconds * 50)
    with torch.no_grad():
        audio_values = model.generate(**inputs, max_new_tokens=max_new_tokens)

    sampling_rate = model.config.audio_encoder.sampling_rate
    audio_data = audio_values[0, 0].cpu().numpy()

    # Normalisation et sauvegarde WAV 16-bit PCM
    audio_data = np.clip(audio_data, -1.0, 1.0)
    audio_int16 = (audio_data * 32767).astype(np.int16)
    
    os.makedirs(os.path.dirname(os.path.abspath(output_wav)), exist_ok=True)
    scipy.io.wavfile.write(output_wav, rate=sampling_rate, data=audio_int16)
    print(f"✦ [SUCCESS] Morceau généré avec succès : {output_wav} ({sampling_rate} Hz, {duration_seconds}s)")
    return output_wav

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LBG Studios - Générateur Musical Local")
    parser.add_argument("--prompt", type=str, default="128 bpm cyberpunk electronic dance track, heavy synth bassline, energetic drums, neon melody", help="Prompt musical")
    parser.add_argument("--duration", type=int, default=15, help="Durée en secondes")
    parser.add_argument("--output", type=str, default="/home/lbg/Projets/LBG_Studios/packages/compagnon-desktop/overlay/audio/track_musicgen_v1.wav", help="Fichier de sortie")
    parser.add_argument("--theme", type=str, default="Lia Nexura Domina, souveraine de la matrice cyberpunk", help="Thème pour les paroles")
    args = parser.parse_args()

    print("=== LBG STUDIOS : GÉNÉRATEUR MUSICAL & PAROLES AUTONOME ===")
    print(f"Thème : {args.theme}")
    print(f"Style : {args.prompt}")
    
    print("\n--- 1. GÉNÉRATION DES PAROLES VIA OLLAMA LOCAL (.110/.111) ---")
    lyrics = generate_lyrics(args.theme)
    print(lyrics)

    print("\n--- 2. COMPOSITION INSTRUMENTALE LOCALE VIA MUSICGEN ---")
    generate_instrumental(args.prompt, duration_seconds=args.duration, output_wav=args.output)
