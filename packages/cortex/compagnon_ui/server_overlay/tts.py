"""Proxy TTS Compagnon — Edge (DeniseNeural) + fallback Piper LAN.

Env :
  LBG_TTS_ENABLED=0|1              (défaut 1)
  LBG_TTS_PROVIDER=edge|piper      (défaut edge — même famille que Hermes)
  LBG_TTS_FALLBACK=piper|none      (défaut piper si provider=edge)
  LBG_EDGE_VOICE=fr-FR-DeniseNeural
  LBG_PIPER_URL=http://192.168.0.111:8098
  LBG_PIPER_VOICE=fr_FR-siwis-medium
  LBG_TTS_TIMEOUT_S=45
  LBG_TTS_MAX_CHARS=500
"""

from __future__ import annotations

import os
import re
from typing import Any

_MD_FENCE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
_MD_INLINE = re.compile(r"`([^`]+)`")
_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_MD_BOLD = re.compile(r"[*_~]{1,3}")
_WS = re.compile(r"\s+")


def _httpx():
    import httpx

    return httpx


def tts_enabled() -> bool:
    return os.environ.get("LBG_TTS_ENABLED", "1").strip().lower() not in (
        "0",
        "false",
        "off",
        "no",
    )


def tts_provider() -> str:
    raw = os.environ.get("LBG_TTS_PROVIDER", "edge").strip().lower() or "edge"
    return raw if raw in ("edge", "piper") else "edge"


def tts_fallback() -> str:
    raw = os.environ.get("LBG_TTS_FALLBACK", "piper").strip().lower() or "piper"
    return raw if raw in ("piper", "none", "off", "") else "piper"


def piper_base_url() -> str:
    return os.environ.get("LBG_PIPER_URL", "http://192.168.0.111:8098").rstrip("/")


def piper_default_voice() -> str:
    return os.environ.get("LBG_PIPER_VOICE", "fr_FR-siwis-medium").strip() or "fr_FR-siwis-medium"


def edge_default_voice() -> str:
    return (
        os.environ.get("LBG_EDGE_VOICE", "fr-FR-DeniseNeural").strip() or "fr-FR-DeniseNeural"
    )


def default_voice() -> str:
    if tts_provider() == "piper":
        return piper_default_voice()
    return edge_default_voice()


def max_chars() -> int:
    try:
        return max(80, min(int(os.environ.get("LBG_TTS_MAX_CHARS", "500")), 2000))
    except ValueError:
        return 500


def timeout_s() -> float:
    try:
        return max(5.0, min(float(os.environ.get("LBG_TTS_TIMEOUT_S", "45")), 120.0))
    except ValueError:
        return 45.0


def sanitize_for_speech(text: str, *, limit: int | None = None) -> str:
    lim = limit if limit is not None else max_chars()
    s = str(text or "")
    s = _MD_FENCE.sub(" ", s)
    s = _MD_LINK.sub(r"\1", s)
    s = _MD_INLINE.sub(r"\1", s)
    s = _MD_BOLD.sub("", s)
    s = s.replace("|", " ").replace("#", " ")
    s = _WS.sub(" ", s).strip()
    if len(s) > lim:
        cut = s[: lim - 1]
        for sep in (". ", "! ", "? ", "; ", ", "):
            idx = cut.rfind(sep)
            if idx >= max(40, lim // 3):
                cut = cut[: idx + 1]
                break
        s = cut.rstrip(" ,;:") + "…"
    return s


def _edge_import_ok() -> tuple[bool, str | None]:
    try:
        import edge_tts  # noqa: F401

        return True, None
    except ImportError as exc:
        return False, f"edge_tts_missing:{exc}"


async def piper_health() -> dict[str, Any]:
    if not tts_enabled():
        return {"ok": False, "enabled": False, "reason": "LBG_TTS_ENABLED=0"}
    httpx = _httpx()
    url = f"{piper_base_url()}/healthz"
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(connect=2.0, read=4.0, write=2.0, pool=2.0)
        ) as client:
            r = await client.get(url)
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            return {
                "ok": r.is_success and bool(data.get("ok", True)),
                "enabled": True,
                "provider": "piper",
                "piper_url": piper_base_url(),
                "voice": data.get("voice") or piper_default_voice(),
                "upstream_status": r.status_code,
                "upstream": data if isinstance(data, dict) else {},
            }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "enabled": True,
            "provider": "piper",
            "piper_url": piper_base_url(),
            "voice": piper_default_voice(),
            "error": str(exc)[:200],
        }


async def edge_health() -> dict[str, Any]:
    if not tts_enabled():
        return {"ok": False, "enabled": False, "reason": "LBG_TTS_ENABLED=0"}
    ok, err = _edge_import_ok()
    out: dict[str, Any] = {
        "ok": ok,
        "enabled": True,
        "provider": "edge",
        "voice": edge_default_voice(),
        "module": "edge_tts",
    }
    if err:
        out["error"] = err
    return out


async def tts_health() -> dict[str, Any]:
    """Health du provider actif (+ dispo fallback Piper si configuré)."""
    provider = tts_provider()
    if provider == "piper":
        return await piper_health()

    primary = await edge_health()
    fb = tts_fallback()
    out: dict[str, Any] = {
        "ok": bool(primary.get("ok")),
        "enabled": tts_enabled(),
        "provider": "edge",
        "voice": edge_default_voice(),
        "upstream": primary,
        "fallback": fb,
    }
    if fb == "piper":
        piper = await piper_health()
        out["piper"] = piper
        # OK si Edge dispo OU Piper fallback dispo
        out["ok"] = bool(primary.get("ok")) or bool(piper.get("ok"))
    return out


async def synthesize_piper(text: str, *, voice: str | None = None) -> tuple[bytes, dict[str, str]]:
    """Retourne (wav_bytes, headers_meta). Raise httpx/RuntimeError."""
    if not tts_enabled():
        raise RuntimeError("tts_disabled")
    spoken = sanitize_for_speech(text)
    if not spoken:
        raise ValueError("empty_after_sanitize")
    vid = (voice or piper_default_voice()).strip() or piper_default_voice()
    httpx = _httpx()
    url = f"{piper_base_url()}/v1/tts"
    timeout = httpx.Timeout(connect=3.0, read=timeout_s(), write=5.0, pool=3.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, json={"text": spoken, "voice": vid})
        if r.status_code >= 400:
            detail = (r.text or "")[:240]
            raise RuntimeError(f"piper_http_{r.status_code}:{detail}")
        meta = {
            "voice": r.headers.get("X-LBG-TTS-Voice") or vid,
            "chars": r.headers.get("X-LBG-TTS-Chars") or str(len(spoken)),
            "content_type": r.headers.get("content-type") or "audio/wav",
            "provider": "piper",
        }
        return r.content, meta


async def synthesize_edge(text: str, *, voice: str | None = None) -> tuple[bytes, dict[str, str]]:
    """Synthèse Microsoft Edge TTS → audio/mpeg."""
    if not tts_enabled():
        raise RuntimeError("tts_disabled")
    spoken = sanitize_for_speech(text)
    if not spoken:
        raise ValueError("empty_after_sanitize")
    vid = (voice or edge_default_voice()).strip() or edge_default_voice()
    ok, err = _edge_import_ok()
    if not ok:
        raise RuntimeError(err or "edge_tts_missing")
    import edge_tts

    communicate = edge_tts.Communicate(spoken, vid)
    chunks: list[bytes] = []
    try:
        async for chunk in communicate.stream():
            if chunk.get("type") == "audio" and chunk.get("data"):
                chunks.append(chunk["data"])
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"edge_tts_stream:{exc}") from exc
    if not chunks:
        raise RuntimeError("edge_tts_empty_audio")
    return b"".join(chunks), {
        "voice": vid,
        "chars": str(len(spoken)),
        "content_type": "audio/mpeg",
        "provider": "edge",
    }


async def synthesize(text: str, *, voice: str | None = None) -> tuple[bytes, dict[str, str]]:
    """Dispatch provider + fallback Piper optionnel."""
    provider = tts_provider()
    if provider == "piper":
        return await synthesize_piper(text, voice=voice)

    try:
        return await synthesize_edge(text, voice=voice)
    except Exception as first:  # noqa: BLE001
        if tts_fallback() != "piper":
            raise
        wav, meta = await synthesize_piper(text, voice=None)
        meta = dict(meta)
        meta["fallback_from"] = "edge"
        meta["edge_error"] = str(first)[:160]
        return wav, meta
