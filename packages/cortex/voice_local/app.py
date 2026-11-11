#!/usr/bin/env python3
"""TTS local Piper — sidecar Compagnon sur CT `.111`.

Port : **8098** (8095=web-enrich, 8096=petri, 8097=laya).

Exemples :
  curl -s http://192.168.0.111:8098/healthz
  curl -s -X POST http://192.168.0.111:8098/v1/tts \\
    -H 'Content-Type: application/json' \\
    -d '{"text":"Bonjour, je suis le Compagnon."}' -o /tmp/out.wav
"""

from __future__ import annotations

import io
import os
import re
import wave
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

app = FastAPI(title="LBG Piper TTS", version="0.1.0")

MODELS_DIR = Path(os.environ.get("LBG_PIPER_MODELS_DIR", "/opt/lbg-piper-tts/models")).resolve()
DEFAULT_VOICE = os.environ.get("LBG_PIPER_VOICE", "fr_FR-siwis-medium")
MAX_CHARS = int(os.environ.get("LBG_PIPER_MAX_CHARS", "500"))
SPEAKER_ID = os.environ.get("LBG_PIPER_SPEAKER")  # optional multi-speaker

_MD_FENCE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
_MD_INLINE = re.compile(r"`([^`]+)`")
_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_MD_BOLD = re.compile(r"[*_~]{1,3}")
_WS = re.compile(r"\s+")


class TtsRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    voice: str | None = None
    length_scale: float | None = Field(default=None, description="Facteur de vitesse (>0, ex 0.9 = 10% plus rapide)")


def sanitize_for_speech(text: str, *, max_chars: int = MAX_CHARS) -> str:
    """Retire markdown / bruit pour une phrase orale courte."""
    s = str(text or "")
    s = _MD_FENCE.sub(" ", s)
    s = _MD_LINK.sub(r"\1", s)
    s = _MD_INLINE.sub(r"\1", s)
    s = _MD_BOLD.sub("", s)
    s = s.replace("|", " ").replace("#", " ")
    s = _WS.sub(" ", s).strip()
    if len(s) > max_chars:
        cut = s[: max_chars - 1]
        # couper sur ponctuation si possible
        for sep in (". ", "! ", "? ", "; ", ", "):
            idx = cut.rfind(sep)
            if idx >= max(40, max_chars // 3):
                cut = cut[: idx + 1]
                break
        s = cut.rstrip(" ,;:") + "…"
    return s


def _voice_paths(voice: str) -> tuple[Path, Path]:
    onnx = MODELS_DIR / f"{voice}.onnx"
    cfg = MODELS_DIR / f"{voice}.onnx.json"
    return onnx, cfg


@lru_cache(maxsize=4)
def _load_voice(voice: str):
    try:
        from piper import PiperVoice  # type: ignore
    except ImportError as exc:
        raise RuntimeError("piper-tts non installé (pip install piper-tts)") from exc

    onnx, cfg = _voice_paths(voice)
    if not onnx.is_file():
        raise FileNotFoundError(f"modèle manquant: {onnx}")
    if cfg.is_file():
        return PiperVoice.load(str(onnx), config_path=str(cfg))
    return PiperVoice.load(str(onnx))


def synthesize_wav(text: str, *, voice: str | None = None, length_scale: float | None = None) -> bytes:
    spoken = sanitize_for_speech(text)
    if not spoken:
        raise ValueError("texte vide après sanitize")
    vid = (voice or DEFAULT_VOICE).strip() or DEFAULT_VOICE
    try:
        piper_voice = _load_voice(vid)
    except FileNotFoundError as exc:
        raise
    except Exception as exc:  # noqa: BLE001 — surface claire pour l'API
        raise RuntimeError(f"load_voice:{exc}") from exc

    buf = io.BytesIO()
    syn_config = None
    spk_id = None
    if SPEAKER_ID is not None and str(SPEAKER_ID).strip() != "":
        try:
            spk_id = int(SPEAKER_ID)
        except ValueError:
            pass

    if length_scale is not None or spk_id is not None:
        try:
            from piper.config import SynthesisConfig
            syn_config = SynthesisConfig(speaker_id=spk_id, length_scale=length_scale)
        except Exception:
            pass

    with wave.open(buf, "wb") as wf:
        # piper-tts ≥1.2 : synthesize_wav(text, wav_file)
        # fallback : synthesize() générateur de chunks PCM
        if hasattr(piper_voice, "synthesize_wav"):
            piper_voice.synthesize_wav(spoken, wf, syn_config=syn_config)
        else:
            syn = getattr(piper_voice, "synthesize", None)
            if syn is None:
                raise RuntimeError("piper_api_missing")
            # Première passe : collecter samples pour connaître rate/channels
            chunks: list[bytes] = []
            sample_rate = int(getattr(piper_voice.config, "sample_rate", 22050))
            sample_width = 2
            channels = 1
            for audio in syn(spoken, syn_config=syn_config):
                # AudioChunk (audio_int16_bytes) ou bytes
                raw = getattr(audio, "audio_int16_bytes", None)
                if raw is None:
                    raw = bytes(audio) if not isinstance(audio, (bytes, bytearray)) else bytes(audio)
                chunks.append(raw)
                rate = getattr(audio, "sample_rate", None)
                if rate:
                    sample_rate = int(rate)
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(sample_rate)
            wf.writeframes(b"".join(chunks))
    return buf.getvalue()


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    onnx, cfg = _voice_paths(DEFAULT_VOICE)
    ready = onnx.is_file()
    return {
        "ok": ready,
        "service": "lbg-piper-tts",
        "voice": DEFAULT_VOICE,
        "models_dir": str(MODELS_DIR),
        "model_present": ready,
        "config_present": cfg.is_file(),
        "max_chars": MAX_CHARS,
    }


@app.get("/v1/voices")
def list_voices() -> dict[str, Any]:
    found = sorted({p.stem.replace(".onnx", "") for p in MODELS_DIR.glob("*.onnx")})
    # stem of foo.onnx is foo — but foo.onnx.json would be foo.onnx — handle:
    voices = sorted({p.name[: -len(".onnx")] for p in MODELS_DIR.glob("*.onnx") if p.name.endswith(".onnx")})
    return {"ok": True, "default": DEFAULT_VOICE, "voices": voices or found}


@app.post("/v1/tts")
def tts(body: TtsRequest) -> Response:
    try:
        wav = synthesize_wav(body.text, voice=body.voice, length_scale=body.length_scale)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"tts_error:{exc}") from exc
    return Response(
        content=wav,
        media_type="audio/wav",
        headers={
            "Cache-Control": "no-store",
            "X-LBG-TTS-Voice": (body.voice or DEFAULT_VOICE),
            "X-LBG-TTS-Chars": str(len(sanitize_for_speech(body.text))),
        },
    )
