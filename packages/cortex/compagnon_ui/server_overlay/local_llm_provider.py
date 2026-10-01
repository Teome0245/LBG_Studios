# Overlay Compagnon — LocalLLMProvider compatible messages OpenAI + défaut gemma-4-abliterated:e2b
# Greffé sur .100 : backend/src/providers/local_llm_provider.py
#
# Garde-fous 504 :
# - think:false (sinon content vide + thinking → retry long)
# - timeout chat configurable (défaut 120s LAB local-only — plus de bascule Groq)
# - content vide → error pour enchaîner le provider local suivant

from __future__ import annotations

import json
import os
import time
from typing import Any

import httpx

from src.http_timeouts import httpx_timeout, httpx_timeout_stream
from src.settings import get_settings


def _flatten_messages(messages: list[Any]) -> str:
    parts: list[str] = []
    for m in messages:
        if isinstance(m, str) and m.strip():
            parts.append(m.strip())
            continue
        if not isinstance(m, dict):
            continue
        role = str(m.get("role") or "").strip()
        content = m.get("content")
        if isinstance(content, list):
            texts = []
            for part in content:
                if isinstance(part, str):
                    texts.append(part)
                elif isinstance(part, dict) and isinstance(part.get("text"), str):
                    texts.append(part["text"])
            content = "\n".join(texts)
        if not isinstance(content, str) or not content.strip():
            continue
        prefix = f"{role}: " if role else ""
        parts.append(f"{prefix}{content.strip()}")
    return "\n\n".join(parts)


def _as_chat_messages(prompt: str | list[Any]) -> list[dict[str, str]]:
    if isinstance(prompt, list):
        out: list[dict[str, str]] = []
        for m in prompt:
            if not isinstance(m, dict):
                continue
            role = str(m.get("role") or "user").strip() or "user"
            content = m.get("content")
            if isinstance(content, list):
                texts = []
                for part in content:
                    if isinstance(part, str):
                        texts.append(part)
                    elif isinstance(part, dict) and isinstance(part.get("text"), str):
                        texts.append(part["text"])
                content = "\n".join(texts)
            if isinstance(content, str) and content.strip():
                out.append({"role": role, "content": content.strip()})
        return out or [{"role": "user", "content": "Bonjour"}]
    text = str(prompt or "").strip() or "Bonjour"
    return [{"role": "user", "content": text}]


def _heavy_base_url() -> str:
    return (
        os.getenv("LBG_REASON_HEAVY_BASE_URL", "").strip()
        or os.getenv("OLLAMA_HEAVY_BASE_URL", "").strip()
        or "http://192.168.0.110:11434"
    ).rstrip("/")


def _model_needs_heavy(model: str | None) -> bool:
    """Route vers Ollama heavy (.110).

    e2b (abliterated) vit sur light ``.111`` — causerie Compagnon.
    Heavy = 9b / 12b / 12b-qat / E4b uniquement.
    """
    m = (model or "").lower()
    return any(x in m for x in (":9b", ":12b", "12b-qat", ":e4b"))


def _model_needs_long_timeout(model: str | None) -> bool:
    """Timeout long seulement pour 9b/12b (pas e2b — sinon hang UI)."""
    m = (model or "").lower()
    return any(x in m for x in (":9b", ":12b", "12b-qat"))


def _chat_read_timeout_s(model: str | None = None) -> float:
    """Timeout LLM local (chat). LAB / local-only : plus patient (pas de failover Groq)."""
    raw = os.getenv("LBG_LOCAL_LLM_CHAT_TIMEOUT_S", "").strip()
    base = None
    if raw:
        try:
            base = max(20.0, float(raw))
        except ValueError:
            base = None
    lab = (os.getenv("LBG_COMPAGNON_LAB") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    local_only = (os.getenv("LBG_COMPAGNON_LOCAL_ONLY") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    if base is None:
        # LAB : 90s pour e2b/2B ; cascade locale gère le reste
        if lab or local_only:
            base = 90.0
        else:
            s = get_settings()
            base = max(45.0, min(float(getattr(s, "httpx_stream_read_timeout_s", 600.0) or 90.0), 90.0))
    # 9b/12b CPU sur .110 : plus patient
    if _model_needs_long_timeout(model):
        return max(base, 180.0)
    # e2b : plafond 75s pour fail-fast cascade
    m = (model or "").lower()
    if "e2b" in m:
        return min(max(base, 45.0), 75.0)
    return base


def _num_predict() -> int:
    raw = os.getenv("LBG_LOCAL_LLM_NUM_PREDICT", "").strip()
    if raw:
        try:
            return max(32, min(int(raw), 1024))
        except ValueError:
            pass
    lab = (os.getenv("LBG_COMPAGNON_LAB") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    # LAB : réponses structurées (légal + Agir) — 192 tronquait souvent
    return 448 if lab else 256


def _extract_assistant_text(msg: dict[str, Any] | None) -> str:
    if not isinstance(msg, dict):
        return ""
    content = str(msg.get("content") or "").strip()
    if content:
        return content
    # Certains modèles (gemma4 / qwen) remplissent « thinking » si think non désactivé
    thinking = str(msg.get("thinking") or msg.get("reasoning") or "").strip()
    if thinking and len(thinking) < 4000:
        # Ne pas renvoyer le raisonnement brut ; signaler vide pour failover / retry
        return ""
    return ""


class LocalLLMProvider:
    def __init__(
        self,
        base_url: str | None = None,
        default_model: str = "huihui_ai/gemma-4-abliterated:e2b",
    ):
        settings = get_settings()
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.default_model = default_model
        # cache par hôte (light .111 / heavy .110)
        self._tags_cache: dict[str, tuple[float, list[str]]] = {}

    def base_url_for_model(self, model: str | None) -> str:
        if _model_needs_heavy(model):
            return _heavy_base_url()
        return self.base_url

    async def list_models(self, ttl_seconds: int = 30, *, base_url: str | None = None) -> list[str]:
        url = (base_url or self.base_url).rstrip("/")
        now = time.time()
        cached_entry = self._tags_cache.get(url)
        if cached_entry:
            ts, cached = cached_entry
            if (now - ts) < ttl_seconds:
                return cached

        try:
            s = get_settings()
            async with httpx.AsyncClient(
                timeout=httpx_timeout(read=s.httpx_agent_capabilities_read_s)
            ) as client:
                r = await client.get(f"{url}/api/tags")
                data = r.json()
                models = [m.get("name") for m in data.get("models", []) if isinstance(m, dict)]
                models = [m for m in models if isinstance(m, str) and m]
                self._tags_cache[url] = (now, models)
                return models
        except Exception:
            return []

    async def generate(self, prompt: str | list[Any] | None = None, model: str | None = None) -> dict:
        """Accepte un prompt str OU une liste messages (comme les providers cloud)."""
        selected_model = model or self.default_model
        host = self.base_url_for_model(selected_model)

        available = await self.list_models(base_url=host)
        if available and selected_model not in available:
            # Ne pas rétrograder un modèle heavy vers le default light d'un autre hôte
            if self.default_model in available:
                selected_model = self.default_model
                host = self.base_url_for_model(selected_model)
            else:
                selected_model = available[0]
                host = self.base_url_for_model(selected_model)

        messages = _as_chat_messages(prompt if prompt is not None else "")
        read_s = _chat_read_timeout_s(selected_model)
        n_predict = _num_predict()
        prefer_generate = os.getenv("LBG_LOCAL_LLM_PREFER_GENERATE", "").strip().lower() in (
            "1",
            "true",
            "yes",
            "on",
        )

        async def _via_generate() -> str:
            flat = _flatten_messages(messages)
            async with httpx.AsyncClient(timeout=httpx_timeout(read=read_s)) as client:
                r2 = await client.post(
                    f"{host}/api/generate",
                    json={
                        "model": selected_model,
                        "prompt": flat,
                        "stream": False,
                        "think": False,
                        "keep_alive": "30m",
                        "options": {"num_predict": n_predict, "temperature": 0.3},
                    },
                )
            if r2.status_code != 200:
                return ""
            d2 = r2.json()
            return str((d2 or {}).get("response") or "").strip()

        try:
            content = ""
            data: dict[str, Any] = {}

            if prefer_generate:
                content = await _via_generate()

            if not content:
                payload: dict[str, Any] = {
                    "model": selected_model,
                    "messages": messages,
                    "stream": False,
                    "think": False,
                    "keep_alive": "30m",
                    "options": {
                        "num_predict": n_predict,
                        "temperature": 0.3,
                    },
                }
                try:
                    async with httpx.AsyncClient(timeout=httpx_timeout(read=read_s)) as client:
                        r = await client.post(f"{host}/api/chat", json=payload)
                    if r.status_code == 200:
                        data = r.json() if r.content else {}
                        msg = data.get("message") if isinstance(data, dict) else None
                        content = _extract_assistant_text(msg if isinstance(msg, dict) else None)
                    else:
                        data = {"http_status": r.status_code, "body": (r.text or "")[:300]}
                except Exception:
                    # /api/chat hang fréquent sur certains tags Qwen — bascule generate
                    content = ""

            if not content:
                content = await _via_generate()

            if not content:
                return {
                    "model_used": selected_model,
                    "content": "",
                    "error": True,
                    "message": f"Ollama content vide (think/timeout) host={host} — failover",
                }
            return {
                "model_used": selected_model,
                "content": content,
                "raw": data if isinstance(data, dict) else {},
                "ollama_host": host,
            }
        except Exception as exc:
            return {
                "model_used": selected_model,
                "content": "",
                "error": True,
                "message": str(exc),
            }
