"""LLM mince pour hub_runtime — Ollama OpenAI-compat (répliques courtes)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

# Défauts LAN : Ollama .110 (fast enough pour say 1 phrase)
_DEFAULT_BASE = os.environ.get(
    "LBG_HUB_LLM_BASE_URL",
    os.environ.get("LBG_DIALOGUE_LLM_BASE_URL", "http://192.168.0.110:11434/v1"),
).rstrip("/")
_DEFAULT_MODEL = os.environ.get(
    "LBG_HUB_LLM_MODEL",
    os.environ.get("LBG_DIALOGUE_LLM_MODEL", "huihui_ai/gemma-4-abliterated:e2b"),
)
_DISABLED = os.environ.get("LBG_HUB_LLM_DISABLED", "").strip() in {"1", "true", "yes"}
_TIMEOUT = float(os.environ.get("LBG_HUB_LLM_TIMEOUT", "18"))


def enabled() -> bool:
    return not _DISABLED and bool(_DEFAULT_BASE)


def complete(
    *,
    system: str,
    user: str,
    max_tokens: int = 80,
    temperature: float = 0.7,
    timeout: float | None = None,
) -> str | None:
    """Retourne une réplique courte ou None si indispo / timeout."""
    if not enabled():
        return None
    wait = float(timeout) if timeout is not None else _TIMEOUT
    # Prefer native Ollama /api/chat (plus fiable que /v1 sur certaines builds)
    native_base = _DEFAULT_BASE
    if native_base.endswith("/v1"):
        native_base = native_base[: -len("/v1")]
    native_url = f"{native_base}/api/chat"
    native_body = {
        "model": _DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system.strip()},
            {"role": "user", "content": user.strip()},
        ],
        "stream": False,
        "think": False,
        "options": {"num_predict": max_tokens, "temperature": temperature},
    }
    data_n = json.dumps(native_body).encode("utf-8")
    req_n = urllib.request.Request(
        native_url,
        data=data_n,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req_n, timeout=wait) as resp:
            raw_n = json.loads(resp.read().decode("utf-8"))
        text = str((raw_n.get("message") or {}).get("content") or "").strip()
        if text:
            for marker in ("</think>", "<think>"):
                if marker in text:
                    text = text.split(marker)[-1].strip()
            text = text.replace("\n", " ").strip()
            if len(text) > 200:
                text = text[:197] + "…"
            return text or None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError):
        pass

    url = f"{_DEFAULT_BASE}/chat/completions"
    body: dict[str, Any] = {
        "model": _DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system.strip()},
            {"role": "user", "content": user.strip()},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=wait) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError):
        return None
    try:
        text = str(raw["choices"][0]["message"]["content"]).strip()
    except (KeyError, IndexError, TypeError):
        return None
    for marker in ("</think>", "<think>"):
        if marker in text:
            text = text.split(marker)[-1].strip()
    text = text.replace("\n", " ").strip()
    if len(text) > 200:
        text = text[:197] + "…"
    return text or None


def bot_line(*, name: str, goal: str, near_human: str = "", place: str = "") -> str | None:
    who = near_human or "un voyageur"
    sys = (
        "Tu es un joueur IA dans le MMO Lost Heaven (Scrapaltai). "
        "Une seule phrase courte en français. Pas de SWG/Tatooine/Mos Eisley. "
        "Pas de guillemets. Ton naturel, vivant."
    )
    user = (
        f"Personnage: {name}. Lieu: {place or 'hub'}. Objectif actuel: {goal}. "
        f"Humain proche: {who}. Dis quelque chose d'in-world (action ou réflexion)."
    )
    return complete(system=sys, user=user, max_tokens=60, temperature=0.85, timeout=16.0)


def npc_line(*, name: str, role_hint: str, player_text: str, place: str = "") -> str | None:
    sys = (
        f"Tu es le PNJ {name} à Lost Heaven ({place or 'hub'}). "
        f"Rôle: {role_hint or 'habitant'}. "
        "Réponds en 1–2 phrases courtes FR. Canon Scrapaltai uniquement. "
        "Pas de SWG. Pas de guillemets."
    )
    user = player_text.strip() or "Bonjour."
    # dialogue joueur : timeout court + fallback stub côté caller
    return complete(system=sys, user=user, max_tokens=90, temperature=0.7, timeout=8.0)
