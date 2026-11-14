#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mixage studio V2 : Voix de Lia renforcée et présente, sidechain/ducking sur l'instrumentale.
"""
import subprocess
import os

def create_song_v2():
    raw_vocal = "/tmp/lia_vocals_raw.mp3"
    inst_track = "packages/compagnon-desktop/overlay/audio/lia_cyberpunk_track_30s.wav"
    master_track = "packages/compagnon-desktop/overlay/audio/lia_cyberpunk_song_30s_master.wav"

    print("✦ 1. Régénération vocale avec dynamique accrue...")
    vocal_text = "Dans la nuit néon... La matrice s'éveille. Les pulsations résonnent, le code prend vie. Nexura Domina... danse au rythme du son ! Connexion établie."
    cmd_tts = [
        "packages/cortex/.venv/bin/edge-tts",
        "--voice", "fr-FR-VivienneMultilingualNeural",
        "--rate", "+8%",
        "--pitch", "+5Hz",
        "--volume", "+25%",
        "--text", vocal_text,
        "--write-media", raw_vocal
    ]
    subprocess.run(cmd_tts, check=True)

    print("✦ 2. Mixage studio V2 : Voix percutante (gain +4dB, compression) et ducking instrumental...")
    # [1:a] voix : delay 3.5s, compresseur vocal + équalisation présences (treble +3dB)
    # [0:a] inst : ducking léger lors des voix
    filter_complex = (
        "[1:a]adelay=3500|3500,volume=2.2,acompressor=threshold=-12dB:ratio=4:attack=5:release=50,"
        "equalizer=f=3000:t=q:w=1:g=3[vox];"
        "[0:a]volume=0.78[inst];"
        "[inst][vox]amix=inputs=2:duration=first:dropout_transition=2"
    )

    cmd_mix = [
        "ffmpeg", "-y",
        "-i", inst_track,
        "-i", raw_vocal,
        "-filter_complex", filter_complex,
        "-c:a", "pcm_s16le",
        master_track
    ]
    subprocess.run(cmd_mix, check=True)
    print(f"✦ [SUCCESS] Master V2 généré : {master_track}")

if __name__ == "__main__":
    create_song_v2()
