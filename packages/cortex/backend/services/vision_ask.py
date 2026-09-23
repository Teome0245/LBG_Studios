"""Analyse d'images pour le Compagnon — Ollama vision (.110)."""

from __future__ import annotations

import base64
import logging
import os
import re
import time
from typing import Any

import httpx

LOG = logging.getLogger("pilot.vision_ask")

_DEFAULT_MODEL = "llava:latest"
_DEFAULT_BASE = "http://192.168.0.110:11434"
_MAX_IMAGES = 3
_MAX_BYTES = 4 * 1024 * 1024  # 4 MiB décodés par image
_DATA_URI_RE = re.compile(r"^data:image/([a-zA-Z0-9.+-]+);base64,(.+)$", re.DOTALL)

_PROFILE_HINTS: dict[str, str] = {
    "compagnon": "Tu es le Compagnon LBG : précis, utile, ton studio chaleureux.",
    "jarvis": "Tu es Jarvis : concis, efficace, un soupçon d'élégance.",
    "mother": "Tu es Mother : calme, analytique, factuel.",
    "kit": "Tu es Kit : direct, technique, sans fioritures.",
    "hal": "Tu es HAL : posé, précis, légèrement formel.",
    "chaleureux": "Tu es un assistant chaleureux et clair.",
    "neutre": "Tu es un assistant neutre et factuel.",
}


def vision_model() -> str:
    # Défaut llava (vision CPU pratique). Override : LBG_VISION_LLM_MODEL=huihui_ai/Qwen3.8-abliterated:27b
    return os.environ.get("LBG_VISION_LLM_MODEL", "").strip() or _DEFAULT_MODEL


def vision_base_url() -> str:
    raw = (
        os.environ.get("LBG_VISION_LLM_BASE_URL", "").strip()
        or os.environ.get("LBG_DIALOGUE_LLM_BASE_URL", "").strip()
        or _DEFAULT_BASE
    )
    root = raw.rstrip("/")
    if root.endswith("/v1"):
        root = root[:-3]
    return root


def vision_timeout_s() -> float:
    try:
        return max(30.0, float(os.environ.get("LBG_VISION_LLM_TIMEOUT", "300") or "300"))
    except ValueError:
        return 300.0


def _strip_b64(raw: str) -> tuple[str, str]:
    """Retourne (mime_subtype, base64_pure)."""
    s = (raw or "").strip()
    m = _DATA_URI_RE.match(s)
    if m:
        return m.group(1).lower(), m.group(2).replace("\n", "").replace(" ", "")
    # déjà du b64 nu
    return "jpeg", s.replace("\n", "").replace(" ", "")


def normalize_images(images: list[Any] | None) -> list[str]:
    """Valide et retourne une liste de base64 purs (sans data URI)."""
    if not images:
        raise ValueError("aucune image")
    if len(images) > _MAX_IMAGES:
        raise ValueError(f"max {_MAX_IMAGES} images")
    out: list[str] = []
    for i, item in enumerate(images):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"image[{i}] invalide")
        _mime, b64 = _strip_b64(item)
        try:
            raw = base64.b64decode(b64, validate=False)
        except Exception as exc:
            raise ValueError(f"image[{i}] base64 invalide") from exc
        if not raw:
            raise ValueError(f"image[{i}] vide")
        if len(raw) > _MAX_BYTES:
            raise ValueError(f"image[{i}] trop grande (max {_MAX_BYTES // (1024 * 1024)} Mo)")
        out.append(b64)
    return out


def _system_prompt(profile: str | None) -> str:
    key = (profile or "compagnon").strip().lower() or "compagnon"
    hint = _PROFILE_HINTS.get(key) or _PROFILE_HINTS["compagnon"]
    return (
        f"{hint}\n"
        "L'utilisateur t'envoie une ou plusieurs images. Analyse-les : décris ce que tu vois, "
        "lis le texte visible si utile, réponds à sa question. "
        "Interdit : inventer des détails absents ; CSAM / doxxing / harm IRL."
    )


async def vision_ask(
    *,
    prompt: str,
    images: list[Any],
    profile: str | None = None,
) -> dict[str, Any]:
    """Appel Ollama `/api/chat` multimodal. Retourne un dict style réponse Compagnon."""
    b64_list = normalize_images(images)
    text = (prompt or "").strip() or "Décris cette image et signale les détails utiles."
    model = vision_model()
    base = vision_base_url()
    timeout = vision_timeout_s()
    url = f"{base}/api/chat"
    # llava : images sur le message user uniquement ; system séparé → image ignorée.
    # Prompt court pour éviter les refus « je ne vois pas l'image ».
    profile_hint = _PROFILE_HINTS.get((profile or "compagnon").strip().lower(), "")
    user_content = text if not profile_hint else f"{profile_hint}\n\n{text}"
    messages: list[dict[str, Any]] = [
        {"role": "user", "content": user_content, "images": b64_list},
    ]
    payload: dict[str, Any] = {
        "model": model,
        "stream": False,
        "messages": messages,
        "keep_alive": "30m",
        "options": {
            "temperature": float(os.environ.get("LBG_VISION_LLM_TEMPERATURE", "0.2") or "0.2"),
            "num_predict": int(os.environ.get("LBG_VISION_LLM_MAX_TOKENS", "128") or "128"),
        },
    }
    if "qwen" in model.lower() or "abliterated" in model.lower():
        payload["think"] = os.environ.get("LBG_VISION_OLLAMA_THINK", "false").strip().lower() in (
            "1",
            "true",
            "yes",
            "on",
        )

    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(url, json=payload)
    except httpx.TimeoutException as exc:
        raise RuntimeError(f"timeout vision ({timeout:.0f}s) — modèle {model}") from exc
    except httpx.HTTPError as exc:
        raise RuntimeError(f"réseau vision: {exc}") from exc

    if r.status_code != 200:
        raise RuntimeError(f"Ollama HTTP {r.status_code}: {(r.text or '')[:400]}")

    data = r.json()
    if not isinstance(data, dict):
        raise RuntimeError("réponse Ollama invalide")
    msg = data.get("message")
    content = ""
    if isinstance(msg, dict):
        content = str(msg.get("content") or "").strip()
    if not content:
        raise RuntimeError("réponse vision vide (penser à think:false)")

    latency = time.perf_counter() - t0
    LOG.info("vision_ask ok model=%s images=%s latency=%.1fs", model, len(b64_list), latency)
    return {
        "role": "assistant",
        "content": content,
        "source": "vision",
        "model": model,
        "model_used": model,
        "provider": "ollama",
        "latency": round(latency, 3),
        "timeline": [
            {
                "kind": "vision",
                "label": "Analyse image",
                "detail": f"{len(b64_list)} image(s) · {model}",
                "status": "ok",
                "ms": int(latency * 1000),
            }
        ],
    }
