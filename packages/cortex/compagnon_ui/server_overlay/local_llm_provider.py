# Overlay Compagnon — LocalLLMProvider compatible messages OpenAI + défaut gemma4:e2b
# Greffé sur .100 : backend/src/providers/local_llm_provider.py
#
# Garde-fous 504 :
# - think:false (sinon content vide + thinking → retry long)
# - timeout chat court (90s) pour failover Groq avant nginx
# - content vide → error pour enchaîner le provider suivant

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


def _chat_read_timeout_s() -> float:
    """Timeout LLM local (chat) — assez court pour basculer Groq avant un 504 nginx."""
    raw = os.getenv("LBG_LOCAL_LLM_CHAT_TIMEOUT_S", "").strip()
    if raw:
        try:
            return max(20.0, float(raw))
        except ValueError:
            pass
    s = get_settings()
    # Ne pas utiliser le stream 600s : un Ollama coincé bloquait /ask jusqu'au 504.
    return max(45.0, min(float(getattr(s, "httpx_stream_read_timeout_s", 600.0) or 90.0), 90.0))


def _num_predict() -> int:
    raw = os.getenv("LBG_LOCAL_LLM_NUM_PREDICT", "").strip()
    if raw:
        try:
            return max(32, min(int(raw), 512))
        except ValueError:
            pass
    return 192


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
        self._tags_cache: tuple[float, list[str]] | None = None

    async def list_models(self, ttl_seconds: int = 30) -> list[str]:
        now = time.time()
        if self._tags_cache:
            ts, cached = self._tags_cache
            if (now - ts) < ttl_seconds:
                return cached

        try:
            s = get_settings()
            async with httpx.AsyncClient(
                timeout=httpx_timeout(read=s.httpx_agent_capabilities_read_s)
            ) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                data = r.json()
                models = [m.get("name") for m in data.get("models", []) if isinstance(m, dict)]
                models = [m for m in models if isinstance(m, str) and m]
                self._tags_cache = (now, models)
                return models
        except Exception:
            return []

    async def generate(self, prompt: str | list[Any] | None = None, model: str | None = None) -> dict:
        """Accepte un prompt str OU une liste messages (comme les providers cloud)."""
        selected_model = model or self.default_model

        available = await self.list_models()
        if available and selected_model not in available:
            if self.default_model in available:
                selected_model = self.default_model
            else:
                selected_model = available[0]

        messages = _as_chat_messages(prompt if prompt is not None else "")
        read_s = _chat_read_timeout_s()
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
                    f"{self.base_url}/api/generate",
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
                        r = await client.post(f"{self.base_url}/api/chat", json=payload)
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
                    "message": "Ollama content vide (think/timeout) — failover",
                }
            return {
                "model_used": selected_model,
                "content": content,
                "raw": data if isinstance(data, dict) else {},
            }
        except Exception as exc:
            return {
                "model_used": selected_model,
                "content": "",
                "error": True,
                "message": str(exc),
            }
