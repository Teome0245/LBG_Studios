"""Backend REASON — chaîne local 110 (H24) + fallback cloud (Groq/Claude)."""

from __future__ import annotations

import os
import re
from typing import Any

import httpx


# Profils délestés vers le nœud léger (NUC / CT 111) si LBG_REASON_LIGHT_BASE_URL est défini.
_LIGHT_PROFILES = frozenset({"router", "json", "fast"})

# Heavy 110 — code/PM/dialogue ≤12B abliterated QAT ; garde-fous maturité A/B/C.
# Canon : gemma-4-abliterated:12b-qat (pas d'alias :12b — un seul tag).
HEAVY_REASON_DEFAULT = "huihui_ai/gemma-4-abliterated:12b-qat"
FORGE_REASON_DEFAULT = "huihui_ai/gemma-4-abliterated:e2b"
LIGHT_CLEAN_DEFAULT = "huihui_ai/qwen3.5-abliterated:2B"
LIGHT_FAST_DEFAULT = "huihui_ai/qwen3.5-abliterated:0.8B"


CHILL_REASON_DEFAULT = "huihui_ai/gemma-4-abliterated:E4b-qat"


def reason_route_matrix() -> dict[str, dict[str, str]]:
    """Table de routage local prioritaire par usage."""
    return {
        "default": {
            "env": "LBG_REASON_LOCAL_MODEL",
            "default": FORGE_REASON_DEFAULT,
            "tier": "local",
            "usage": "raisonnement_general",
            "host_class": "heavy",
        },
        "forge": {
            "env": "LBG_REASON_MODEL_FORGE",
            "default": FORGE_REASON_DEFAULT,
            "tier": "local",
            "usage": "routage_rapide_et_generation_ciblee",
            "host_class": "heavy",
        },
        "router": {
            "env": "LBG_REASON_MODEL_ROUTER",
            "default": LIGHT_CLEAN_DEFAULT,
            "tier": "local",
            "usage": "routage_agentique_clean",
            "host_class": "light",
        },
        "json": {
            "env": "LBG_REASON_MODEL_JSON",
            "default": LIGHT_CLEAN_DEFAULT,
            "tier": "local",
            "usage": "json_actions_structurees_clean",
            "host_class": "light",
        },
        "code": {
            "env": "LBG_REASON_MODEL_CODE",
            "default": HEAVY_REASON_DEFAULT,
            "tier": "local",
            "usage": "code_et_patchs",
            "host_class": "heavy",
        },
        "pm": {
            "env": "LBG_REASON_MODEL_PM",
            "default": HEAVY_REASON_DEFAULT,
            "tier": "local",
            "usage": "synthese_et_arbitrage",
            "host_class": "heavy",
        },
        "fast": {
            "env": "LBG_REASON_MODEL_FAST",
            "default": LIGHT_FAST_DEFAULT,
            "tier": "local",
            "usage": "triage_rapide_fast",
            "host_class": "light",
        },
        "dialogue": {
            "env": "LBG_REASON_MODEL_DIALOGUE",
            "default": HEAVY_REASON_DEFAULT,
            "tier": "local",
            "usage": "dialogue_secondaire",
            "host_class": "heavy",
        },
        "uncensored": {
            "env": "LBG_REASON_MODEL_UNCENSORED",
            "default": HEAVY_REASON_DEFAULT,
            "tier": "local",
            "usage": "avis_complementaires_hors_cadre",
            "host_class": "heavy",
        },
        "chill": {
            "env": "LBG_REASON_MODEL_CHILL",
            "default": CHILL_REASON_DEFAULT,
            "tier": "local",
            "usage": "philosophie_et_posture_chill",
            "host_class": "heavy",
        },
    }


def reason_llm_enabled() -> bool:
    if os.environ.get("LBG_REASON_LLM_DISABLED", "0").strip().lower() in ("1", "true", "yes", "on"):
        return False
    return bool(reason_routes())


def reason_failover_enabled() -> bool:
    return os.environ.get("LBG_REASON_FAILOVER", "1").strip().lower() in ("1", "true", "yes", "on")


def _resolve_profile(profile: str) -> str:
    p = (profile or "default").strip().lower()
    aliases = {
        "iris": "forge",
        "agentic": "router",
        "agentic_router": "router",
        "router_json": "json",
        "structured": "json",
        "structured_actions": "json",
        "actions": "json",
        "coding": "code",
        "synthesis": "pm",
        "triage": "fast",
        "clean": "json",
        "light_clean": "json",
        "light_fast": "fast",
        "dialogue_uncensored": "uncensored",
        "promethee": "uncensored",
        "contrarian": "uncensored",
        "abliterated": "uncensored",
    }
    return aliases.get(p, p)


def reason_heavy_base_url() -> str:
    """Nœud lourd (110) — code / PM / forge / défaut."""
    return (
        os.environ.get("LBG_REASON_HEAVY_BASE_URL", "").strip()
        or os.environ.get("LBG_REASON_LOCAL_BASE_URL", "").strip()
        or os.environ.get("LBG_REASON_BASE_URL", "").strip()
        or os.environ.get("OLLAMA_BASE_URL", "http://192.168.0.110:11434").strip()
    ).rstrip("/")


def reason_light_base_url() -> str:
    """Nœud léger (111 NUC) — router / json / fast. Vide = même hôte que heavy."""
    return (
        os.environ.get("LBG_REASON_LIGHT_BASE_URL", "").strip()
        or os.environ.get("LBG_REASON_ROUTER_BASE_URL", "").strip()
        or os.environ.get("LBG_REASON_JSON_BASE_URL", "").strip()
    ).rstrip("/")


def reason_local_base_url(*, profile: str = "default") -> str:
    """URL Ollama selon le profil (light 111 vs heavy 110)."""
    resolved = _resolve_profile(profile)
    slot = reason_route_matrix().get(resolved) or {}
    host_class = str(slot.get("host_class") or ("light" if resolved in _LIGHT_PROFILES else "heavy"))
    if host_class == "light" or resolved in _LIGHT_PROFILES:
        light = reason_light_base_url()
        if light:
            return light
    return reason_heavy_base_url()


def reason_local_model(*, profile: str = "default") -> str:
    """Profils : light 111 (fast=llama3.2, clean/json/router=qwen2.5) vs heavy 110 (e2b / abliterated 27b)."""
    resolved = _resolve_profile(profile)
    matrix = reason_route_matrix()
    slot = matrix.get(resolved)
    if slot:
        configured = os.environ.get(slot["env"], "").strip()
        if configured:
            return configured
        if resolved == "uncensored":
            # Optionnel : 2e tag si posé ; sinon même heavy (option 1).
            alt = os.environ.get("LBG_DIALOGUE_LLM_MODEL_UNCENSORED", "").strip()
            if alt:
                return alt
        if resolved in ("default", "code") and os.environ.get("LBG_REASON_LOCAL_MODEL", "").strip():
            return os.environ["LBG_REASON_LOCAL_MODEL"].strip()
        return slot["default"]
    if resolved in ("forge", "fast"):
        return os.environ.get("LBG_REASON_MODEL_FORGE", "").strip() or FORGE_REASON_DEFAULT
    if resolved in ("pm", "dialogue"):
        return os.environ.get("LBG_REASON_MODEL_PM", "").strip() or HEAVY_REASON_DEFAULT
    return (
        os.environ.get("LBG_REASON_LOCAL_MODEL", "").strip()
        or os.environ.get("LBG_REASON_MODEL", "").strip()
        or os.environ.get("LBG_DIALOGUE_LLM_MODEL", "").strip()
        or FORGE_REASON_DEFAULT
    )


def reason_local_model_legacy() -> str:
    return reason_local_model(profile="default")


def reason_cloud_base_url() -> str:
    return (
        os.environ.get("LBG_REASON_CLOUD_BASE_URL", "").strip()
        or os.environ.get("LBG_DIALOGUE_FAST_BASE_URL", "").strip()
    ).rstrip("/")


def reason_cloud_model() -> str:
    return (
        os.environ.get("LBG_REASON_CLOUD_MODEL", "").strip()
        or os.environ.get("LBG_DIALOGUE_FAST_MODEL", "").strip()
        or "qwen/qwen3.8-27b"
    )


def reason_cloud_api_key() -> str:
    return (
        os.environ.get("LBG_REASON_CLOUD_API_KEY", "").strip()
        or os.environ.get("LBG_REASON_API_KEY", "").strip()
        or os.environ.get("LBG_DIALOGUE_FAST_API_KEY", "").strip()
    )


def reason_cloud_uncensored_enabled() -> bool:
    return os.environ.get("LBG_REASON_CLOUD_UNCENSORED_ENABLED", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    ) or os.environ.get("LBG_DIALOGUE_UNCENSORED_CLOUD_ENABLED", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def reason_cloud_uncensored_route() -> dict[str, str] | None:
    """Cloud uncensored (OpenRouter Venice…) — fallback hors Groq filtré pour profils uncensored."""
    if not reason_cloud_uncensored_enabled():
        return None
    base = (
        os.environ.get("LBG_REASON_CLOUD_UNCENSORED_BASE_URL", "").strip()
        or os.environ.get("LBG_DIALOGUE_UNCENSORED_CLOUD_BASE_URL", "").strip()
        or "https://openrouter.ai/api/v1"
    ).rstrip("/")
    model = (
        os.environ.get("LBG_REASON_CLOUD_UNCENSORED_MODEL", "").strip()
        or os.environ.get("LBG_DIALOGUE_UNCENSORED_CLOUD_MODEL", "").strip()
        or "cognitivecomputations/dolphin-mistral-24b-venice-edition"
    )
    key = (
        os.environ.get("LBG_REASON_CLOUD_UNCENSORED_API_KEY", "").strip()
        or os.environ.get("LBG_DIALOGUE_UNCENSORED_CLOUD_API_KEY", "").strip()
        or os.environ.get("OPENROUTER_API_KEY", "").strip()
    )
    if not (base and model and key):
        return None
    return {
        "tier": "cloud_uncensored",
        "base_url": base,
        "model": model,
        "api_key": key,
        "host": "openrouter",
    }


def reason_ephemeral_enabled() -> bool:
    """GPU cloud éphémère (Colab + tunnel) — PoC / laptop sans GPU, pas H24."""
    return os.environ.get("LBG_REASON_EPHEMERAL_ENABLED", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def reason_ephemeral_base_url() -> str:
    return os.environ.get("LBG_REASON_EPHEMERAL_BASE_URL", "").strip().rstrip("/")


def reason_ephemeral_model() -> str:
    # T4-friendly abliterated (même famille que heavy .110, pas le 27B).
    return (
        os.environ.get("LBG_REASON_EPHEMERAL_MODEL", "").strip()
        or "huihui_ai/qwen3.5-abliterated:9b"
    )


def reason_ephemeral_api_key() -> str:
    return os.environ.get("LBG_REASON_EPHEMERAL_API_KEY", "").strip()


def reason_ephemeral_timeout_s() -> float:
    return float(os.environ.get("LBG_REASON_EPHEMERAL_TIMEOUT_S", "45"))


def reason_ephemeral_before_cloud() -> bool:
    """Si true : local → ephemeral → cloud ; sinon local → cloud → ephemeral."""
    return os.environ.get("LBG_REASON_EPHEMERAL_BEFORE_CLOUD", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def reason_ephemeral_route() -> dict[str, str] | None:
    """Route OpenAI-compat vers Ollama Colab (tunnel). Requiert ENABLED + BASE_URL + API_KEY."""
    if not reason_ephemeral_enabled():
        return None
    base = reason_ephemeral_base_url()
    key = reason_ephemeral_api_key()
    if not base or not key:
        return None
    timeout = reason_ephemeral_timeout_s()
    timeout_s = str(int(timeout)) if timeout == int(timeout) else str(timeout)
    return {
        "tier": "ephemeral",
        "base_url": base,
        "model": reason_ephemeral_model(),
        "api_key": key,
        "host": "colab",
        "timeout": timeout_s,
    }


# Compat anciennes vars
def reason_base_url() -> str:
    return reason_local_base_url() or reason_cloud_base_url()


def reason_model() -> str:
    return reason_local_model(profile="default")


def reason_api_key() -> str:
    return reason_cloud_api_key()


def reason_routes(*, prefer_cloud: bool = False, profile: str = "default") -> list[dict[str, str]]:
    """Ordre : local → failover heavy → ephemeral?/cloud? (ordre configurable)."""
    routes: list[dict[str, str]] = []
    resolved = _resolve_profile(profile)
    primary_url = reason_local_base_url(profile=resolved)
    model = reason_local_model(profile=resolved)
    heavy = reason_heavy_base_url()
    light = reason_light_base_url()

    if primary_url and not prefer_cloud:
        routes.append(
            {
                "tier": "local",
                "base_url": primary_url,
                "model": model,
                "api_key": "",
                "profile": resolved,
                "host": "light" if light and primary_url.rstrip("/") == light.rstrip("/") else "heavy",
            }
        )
        # Si le profil part sur 111 et que 111 tombe : retenter 110 avec le modèle forge/e2b.
        failover_heavy = os.environ.get("LBG_REASON_LIGHT_FAILOVER_HEAVY", "1").strip().lower() in (
            "1",
            "true",
            "yes",
            "on",
        )
        if (
            failover_heavy
            and light
            and heavy
            and primary_url.rstrip("/") == light.rstrip("/")
            and heavy.rstrip("/") != light.rstrip("/")
        ):
            fb_model = (
                os.environ.get("LBG_REASON_LIGHT_FAILOVER_MODEL", "").strip()
                or os.environ.get("LBG_REASON_MODEL_FORGE", "").strip()
                or os.environ.get("LBG_REASON_LOCAL_MODEL", "").strip()
                or FORGE_REASON_DEFAULT
            )
            routes.append(
                {
                    "tier": "local",
                    "base_url": heavy,
                    "model": fb_model,
                    "api_key": "",
                    "profile": resolved,
                    "host": "heavy_failover",
                }
            )

    ephemeral = reason_ephemeral_route()
    cloud_unc = reason_cloud_uncensored_route() if resolved == "uncensored" else None
    cloud_url = reason_cloud_base_url()
    cloud_key = reason_cloud_api_key()
    cloud: dict[str, str] | None = None
    if cloud_url and cloud_key:
        cloud = {
            "tier": "cloud",
            "base_url": cloud_url,
            "model": reason_cloud_model(),
            "api_key": cloud_key,
        }

    # Uncensored : cloud Venice/Dolphin avant Groq filtré.
    tail: list[dict[str, str]] = []
    if cloud_unc:
        tail.append(cloud_unc)
    if ephemeral and cloud:
        if reason_ephemeral_before_cloud():
            tail.extend([ephemeral, cloud])
        else:
            tail.extend([cloud, ephemeral])
    elif ephemeral:
        tail.append(ephemeral)
    elif cloud:
        tail.append(cloud)
    routes.extend(tail)

    if prefer_cloud and cloud_unc:
        rest = [r for r in routes if r.get("tier") != "cloud_uncensored"]
        return [cloud_unc] + rest
    if prefer_cloud and cloud:
        rest = [r for r in routes if r["tier"] != "cloud"]
        return [cloud] + rest
    return routes

def _looks_ollama_route(route: dict[str, str], base: str) -> bool:
    return (
        ":11434" in base
        or "ollama" in base.lower()
        or route.get("tier") in ("local", "ephemeral")
        or route.get("host", "").startswith(("light", "heavy", "colab"))
    )


def _chat_completions_url(base: str) -> str:
    b = base.rstrip("/")
    if b.endswith("/v1"):
        return f"{b}/chat/completions"
    if "api.anthropic.com" in b:
        return f"{b}/v1/messages"
    return f"{b}/v1/chat/completions"


def _ollama_native_chat_url(base: str) -> str:
    """Ollama /api/chat — think=false fiable (contrairement à /v1/chat/completions)."""
    b = base.rstrip("/")
    if b.endswith("/v1"):
        b = b[:-3]
    return f"{b}/api/chat"


def _extract_text(data: Any) -> str:
    if not isinstance(data, dict):
        raise RuntimeError("Réponse LLM invalide")
    # Ollama natif /api/chat
    msg_top = data.get("message")
    if isinstance(msg_top, dict):
        content = msg_top.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
    if "content" in data and isinstance(data["content"], list):
        parts: list[str] = []
        for block in data["content"]:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text") or ""))
        text = "".join(parts).strip()
        if text:
            return text
    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        ch = choices[0]
        if isinstance(ch, dict):
            msg = ch.get("message")
            if isinstance(msg, dict):
                content = msg.get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()
            text = ch.get("text")
            if isinstance(text, str) and text.strip():
                return text.strip()
    raise RuntimeError("Réponse LLM vide")


def _ollama_think_enabled() -> bool:
    return os.environ.get("LBG_REASON_OLLAMA_THINK", "false").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _call_route(
    route: dict[str, str],
    *,
    system: str,
    user: str,
    temperature: float,
    max_tokens: int,
    timeout: float,
) -> dict[str, Any]:
    base = route["base_url"]
    model = route["model"]
    key = route.get("api_key") or ""
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    call_timeout = timeout
    if route.get("timeout"):
        try:
            call_timeout = float(route["timeout"])
        except ValueError:
            pass

    if "api.anthropic.com" in base:
        url = _chat_completions_url(base)
        payload: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
            "temperature": temperature,
        }
    elif _looks_ollama_route(route, base):
        # Natif : think=false remplit message.content ; /v1 laisse souvent content vide (reasoning).
        url = _ollama_native_chat_url(base)
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "think": _ollama_think_enabled(),
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if route.get("profile") == "json":
            payload["format"] = "json"
    else:
        url = _chat_completions_url(base)
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if route.get("profile") == "json":
            payload["response_format"] = {"type": "json_object"}

    with httpx.Client(timeout=httpx.Timeout(call_timeout)) as client:
        resp = client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        text = _extract_text(resp.json())
        return {"ok": True, "text": text, "model": model, "base_url": base, "tier": route["tier"]}


def complete_reason(
    *,
    system: str,
    user: str,
    temperature: float | None = None,
    prefer_cloud: bool | None = None,
    profile: str = "forge",
) -> dict[str, Any]:
    """Appel REASON avec failover : Ollama 110 (profil) → cloud si échec."""
    if not reason_llm_enabled():
        return {"ok": False, "error": "LBG_REASON_LLM_DISABLED ou aucune route", "skipped": True}

    prefer = prefer_cloud
    if prefer is None:
        prefer = os.environ.get("LBG_REASON_PREFER_CLOUD", "0").strip().lower() in ("1", "true", "yes", "on")

    temp = temperature if temperature is not None else float(os.environ.get("LBG_REASON_TEMPERATURE", "0.2"))
    max_tokens = int(os.environ.get("LBG_REASON_MAX_TOKENS", "2048"))
    timeout = float(os.environ.get("LBG_REASON_TIMEOUT_S", "90"))

    routes = reason_routes(prefer_cloud=prefer, profile=profile)
    errors: list[str] = []

    for i, route in enumerate(routes):
        try:
            out = _call_route(route, system=system, user=user, temperature=temp, max_tokens=max_tokens, timeout=timeout)
            out["route_index"] = i
            return out
        except Exception as exc:
            errors.append(f"{route['tier']}:{exc}")
            if not reason_failover_enabled() or i == len(routes) - 1:
                break

    return {
        "ok": False,
        "error": "; ".join(errors) or "aucune route REASON",
        "routes_tried": len(routes),
    }


def probe_reason_local(*, profile: str = "default") -> dict[str, Any]:
    """Sonde Ollama (110 heavy ou 111 light selon profil)."""
    url = reason_local_base_url(profile=profile).rstrip("/")
    if url.endswith("/v1"):
        url = url[:-3]
    tags = f"{url}/api/tags"
    host_hint = "111" if "192.168.0.111" in url else ("110" if "192.168.0.110" in url else "local")
    try:
        with httpx.Client(timeout=httpx.Timeout(5.0)) as client:
            r = client.get(tags)
            ok = r.status_code == 200
            return {"ok": ok, "url": tags, "tier": "local", "host": host_hint, "profile": profile}
    except Exception as exc:
        return {"ok": False, "url": tags, "error": str(exc), "tier": "local", "host": host_hint, "profile": profile}


def extract_code_block(text: str, *, lang: str = "gdscript") -> str | None:
    pattern = rf"```{re.escape(lang)}\s*(.*?)```"
    m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    m2 = re.search(r"```\s*(.*?)```", text, re.DOTALL)
    if m2:
        return m2.group(1).strip()
    stripped = text.strip()
    return stripped if stripped.startswith("extends ") or stripped.startswith("#") else None
