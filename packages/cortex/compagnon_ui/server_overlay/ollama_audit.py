"""
Audit Ollama dual heavy `.110` + light `.111` (Phase C).

Aligné sur Cortex `team/ollama_audit.py` + matrice `docs/local_llm_route_matrix.md`,
sans dépendance au package Cortex (repo séparé).
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx

try:
    from src.http_timeouts import httpx_timeout
    from src.settings import Settings
except ImportError:
    httpx_timeout = None  # type: ignore
    Settings = None  # type: ignore

# Rôles dont le modèle doit être sur le nœud light (111).
_LIGHT_ROLES = frozenset({"reason_router", "reason_json", "reason_fast", "companion"})

# Matrice Cortex 2026-09 — `docs/local_llm_route_matrix.md` + `reason_llm.py`.
# Pas de gemma4:26b / 27B routés ; heavy = gemma-4-abliterated QAT ≤12B.
_ROLE_DEFAULTS: dict[str, dict[str, str]] = {
    "reason_default": {
        "model_env": "LBG_REASON_LOCAL_MODEL",
        "default": "huihui_ai/gemma-4-abliterated:E4b-qat",
        "host": "heavy",
    },
    "reason_forge": {
        "model_env": "LBG_REASON_MODEL_FORGE",
        "default": "huihui_ai/gemma-4-abliterated:E4b-qat",
        "host": "heavy",
    },
    "reason_code": {
        "model_env": "LBG_REASON_MODEL_CODE",
        "default": "huihui_ai/qwen3-coder-abliterated:30b",
        "host": "heavy",
    },
    "reason_pm": {
        "model_env": "LBG_REASON_MODEL_PM",
        "default": "huihui_ai/gemma-4-abliterated:12b-qat",
        "host": "heavy",
    },
    "reason_dialogue": {
        "model_env": "LBG_REASON_MODEL_DIALOGUE",
        "default": "huihui_ai/gemma-4-abliterated:12b-qat",
        "host": "heavy",
    },
    "dialogue_local": {
        "model_env": "LBG_DIALOGUE_LLM_MODEL",
        "default": "huihui_ai/gemma-4-abliterated:12b-qat",
        "host": "heavy",
    },
    "reason_mid": {
        "model_env": "LBG_REASON_MODEL_MID",
        "default": "huihui_ai/gemma-4-abliterated:E4b-qat",
        "host": "heavy",
    },
    "reason_router": {
        "model_env": "LBG_REASON_MODEL_ROUTER",
        "default": "huihui_ai/qwen3.5-abliterated:2B",
        "host": "light",
    },
    "reason_json": {
        "model_env": "LBG_REASON_MODEL_JSON",
        "default": "huihui_ai/qwen3.5-abliterated:2B",
        "host": "light",
    },
    "reason_fast": {
        "model_env": "LBG_REASON_MODEL_FAST",
        "default": "huihui_ai/qwen3.5-abliterated:0.8B",
        "host": "light",
    },
    "jobs_planner": {
        "model_env": "LBG_JOBS_PLANNER_LLM_MODEL",
        "default": "huihui_ai/gemma-4-abliterated:E4b-qat",
        "host": "heavy",
    },
    "companion": {
        "model_env": "LBG_COMPANION_LLM_MODEL",
        "default": "huihui_ai/qwen3.5-abliterated:2B",
        "host": "light",
    },
}


def model_available(name: str, installed: set[str]) -> bool:
    """True si ``name`` est installé ; alias ``:12b`` ↔ ``:12b-qat`` et ``:latest`` implicite."""
    if not name:
        return True
    if name in installed:
        return True
    installed_l = {n.lower() for n in installed}
    needle = name.lower()
    if needle in installed_l:
        return True
    # Support du tag :latest implicite ou explicite sur le même nom de modèle
    if ":" not in needle:
        if f"{needle}:latest" in installed_l or any(n.startswith(f"{needle}:") for n in installed_l):
            return True
    elif needle.endswith(":latest"):
        base = needle[:-7]
        if base in installed_l or any(n.startswith(f"{base}:") for n in installed_l):
            return True
    # Canon QAT : un seul poids — accepter l'ancien tag :12b si :12b-qat est là (et inverse)
    qat_pair = {
        "huihui_ai/gemma-4-abliterated:12b": "huihui_ai/gemma-4-abliterated:12b-qat",
        "huihui_ai/gemma-4-abliterated:12b-qat": "huihui_ai/gemma-4-abliterated:12b",
    }
    alt = qat_pair.get(needle)
    if alt and alt in installed_l:
        return True
    if ":" in needle:
        tag = needle.rsplit(":", 1)[-1]
        family = "gemma" if "gemma" in needle else ("qwen" if "qwen" in needle else "")
        if family and tag in ("12b", "12b-qat", "e4b-qat", "14b", "9b", "2b"):
            for n in installed_l:
                ntag = n.rsplit(":", 1)[-1] if ":" in n else n
                if ntag == tag and family in n:
                    return True
                if {ntag, tag} == {"12b", "12b-qat"} and family in n:
                    return True
    return False


def configured_models() -> dict[str, str]:
    out: dict[str, str] = {}
    for role, meta in _ROLE_DEFAULTS.items():
        env_key = meta["model_env"]
        raw = os.environ.get(env_key, "").strip()
        out[role] = raw or meta["default"]
    return out


def _host_for_role(role: str) -> str:
    meta = _ROLE_DEFAULTS.get(role) or {}
    if role in _LIGHT_ROLES or meta.get("host") == "light":
        return "light"
    return "heavy"


def _is_local_ollama_base(url: str) -> bool:
    u = (url or "").strip().lower()
    if not u:
        return True
    if ":11434" in u:
        return True
    return any(h in u for h in ("192.168.0.110", "192.168.0.111", "127.0.0.1", "localhost"))


async def fetch_ollama_host(
    base_url: str,
    *,
    tier: str,
    read_timeout_s: float,
) -> dict[str, Any]:
    url = f"{str(base_url).rstrip('/')}/api/tags"
    try:
        timeout = httpx_timeout(read=read_timeout_s)
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(url)
        r.raise_for_status()
        data = r.json()
        installed: list[dict[str, Any]] = []
        names: set[str] = set()
        for m in data.get("models") or []:
            if not isinstance(m, dict):
                continue
            name = str(m.get("name") or "")
            if not name:
                continue
            names.add(name)
            details = m.get("details") if isinstance(m.get("details"), dict) else {}
            installed.append(
                {
                    "name": name,
                    "size_gb": round(int(m.get("size") or 0) / 1e9, 2),
                    "params": details.get("parameter_size"),
                    "quant": details.get("quantization_level"),
                    "family": details.get("family"),
                }
            )
        return {
            "ok": True,
            "tier": tier,
            "base_url": str(base_url).rstrip("/"),
            "model_count": len(installed),
            "installed": installed,
            "names": sorted(names),
            "error": None,
        }
    except Exception as e:
        return {
            "ok": False,
            "tier": tier,
            "base_url": str(base_url).rstrip("/"),
            "model_count": 0,
            "installed": [],
            "names": [],
            "error": f"{type(e).__name__}: {e}",
        }


def build_pull_commands(
    missing: list[dict[str, str]],
    *,
    heavy_url: str,
    light_url: str,
) -> list[dict[str, str]]:
    """Commandes `ollama pull` dédupliquées par hôte."""
    seen: set[tuple[str, str]] = set()
    cmds: list[dict[str, str]] = []
    for row in missing:
        model = str(row.get("model") or "").strip()
        host = str(row.get("host") or "heavy")
        if not model:
            continue
        key = (host, model)
        if key in seen:
            continue
        seen.add(key)
        base = light_url if host == "light" else heavy_url
        # Extraire IP/host pour hint SSH (best-effort)
        hint = base.replace("http://", "").replace("https://", "").split("/")[0].split(":")[0]
        cmds.append(
            {
                "host": host,
                "model": model,
                "base_url": base,
                "command": f"OLLAMA_HOST={base} ollama pull {model}",
                "ssh_hint": f"ssh …@{hint} 'ollama pull {model}'",
                "role": str(row.get("role") or ""),
            }
        )
    return cmds


def _recommendations(
    *,
    heavy: dict[str, Any],
    light: dict[str, Any],
    gaps: list[str],
    pull_commands: list[dict[str, str]],
    light_url: str,
) -> list[str]:
    heavy_names = set(heavy.get("names") or [])
    light_names = set(light.get("names") or [])
    recs: list[str] = []

    if gaps:
        recs.append("Corriger modèles manquants : heavy `.110` ou light `.111` (`ollama pull`).")
    for cmd in pull_commands[:8]:
        recs.append(f"Pull {cmd['host']}: `{cmd['command']}`")

    if light_names:
        recs.append(
            f"Routage/JSON sur light {light_url} — modèles : {', '.join(sorted(light_names)[:6])}."
        )
    else:
        recs.append(
            "Light 111 vide/injoignable — pull huihui_ai/qwen3.5-abliterated:2B (Clean) "
            "et huihui_ai/qwen3.5-abliterated:0.8B (Fast) sur le NUC. "
            "Ne pas réintroduire gemma3:4b."
        )

    heavy_l = {str(n).lower() for n in heavy_names}
    if any("e4b-qat" in n and "gemma" in n for n in heavy_l):
        recs.append(
            "Forge/Iris : LBG_REASON_MODEL_FORGE=huihui_ai/gemma-4-abliterated:E4b-qat (heavy 110)."
        )
    if any("qwen2.5-coder" in n for n in heavy_l):
        recs.append(
            "Code spécialisé : LBG_REASON_MODEL_CODE=huihui_ai/qwen3-coder-abliterated:30b sur heavy 110."
        )
    if any("12b-qat" in n and "gemma" in n for n in heavy_l):
        recs.append(
            "PM/dialogue : huihui_ai/gemma-4-abliterated:12b-qat sur heavy 110."
        )
    if any("e4b-qat" in n and "gemma" in n for n in heavy_l):
        recs.append(
            "Interactif / Cline Act : huihui_ai/gemma-4-abliterated:E4b-qat (entre e2b et 12b-qat)."
        )
    if any("26b" in n or "27b" in n for n in heavy_l):
        recs.append("Legacy 26b/27b présent sur disque — ne plus router (matrice ≤12B QAT).")

    recs.append("Matrice : packages/cortex/docs/local_llm_route_matrix.md (source Cortex).")
    return recs


def _resolve_heavy_url(settings: Settings) -> str:
    """Heavy = `.110` — ne jamais confondre avec OLLAMA_BASE_URL light (`.111`)."""
    candidates = [
        str(getattr(settings, "probe_ollama_heavy_url", "") or "").strip(),
        os.environ.get("PROBE_OLLAMA_HEAVY_URL", "").strip(),
        os.environ.get("LBG_REASON_HEAVY_BASE_URL", "").strip(),
        os.environ.get("LBG_TEAM_OPS_OLLAMA_URL", "").strip(),
    ]
    for c in candidates:
        if c:
            return c.rstrip("/")
    base = str(getattr(settings, "ollama_base_url", "") or "").strip().rstrip("/")
    if base and "192.168.0.111" not in base.lower():
        return base
    return "http://192.168.0.110:11434"


def _resolve_light_url(settings: Settings) -> str:
    """Light = `.111`."""
    candidates = [
        str(getattr(settings, "probe_ollama_light_url", "") or "").strip(),
        os.environ.get("PROBE_OLLAMA_LIGHT_URL", "").strip(),
        os.environ.get("LBG_REASON_LIGHT_BASE_URL", "").strip(),
    ]
    for c in candidates:
        if c:
            return c.rstrip("/")
    base = str(getattr(settings, "ollama_base_url", "") or "").strip().rstrip("/")
    if base and "192.168.0.110" not in base.lower():
        return base
    return "http://192.168.0.111:11434"


async def try_proxy_cortex_audit(settings: Settings) -> dict[str, Any] | None:
    """Best-effort : si Cortex orch expose un endpoint audit, le renvoyer tel quel."""
    orch = str(getattr(settings, "cortex_orch_url", "") or "").rstrip("/")
    if not orch:
        return None
    # Endpoints historiques / expérimentaux — ignore si 404
    candidates = [
        f"{orch}/v1/admin/infra/ollama",
        f"{orch}/v1/ops/ollama_audit",
        f"{orch}/team/ops/ollama_audit",
    ]
    timeout = httpx_timeout(read=min(float(settings.httpx_probe_read_s), 8.0))
    async with httpx.AsyncClient(timeout=timeout) as client:
        for url in candidates:
            try:
                r = await client.get(url)
                if r.status_code != 200:
                    continue
                data = r.json()
                if isinstance(data, dict) and ("gaps" in data or data.get("track")):
                    data = dict(data)
                    data["source"] = "cortex_proxy"
                    data["proxy_url"] = url
                    return data
            except Exception:
                continue
    return None


async def audit_ollama_dual(
    *,
    settings: Settings,
    prefer_cortex_proxy: bool = True,
) -> dict[str, Any]:
    """Audit dual 110/111 vs matrice Cortex."""
    t0 = time.perf_counter()

    if prefer_cortex_proxy:
        proxied = await try_proxy_cortex_audit(settings)
        if proxied is not None:
            proxied["built_ms"] = round((time.perf_counter() - t0) * 1000, 1)
            return proxied

    heavy_url = _resolve_heavy_url(settings)
    light_url = _resolve_light_url(settings)
    read_s = float(settings.httpx_probe_read_s)

    heavy = await fetch_ollama_host(heavy_url, tier="heavy", read_timeout_s=read_s)
    light = await fetch_ollama_host(light_url, tier="light", read_timeout_s=read_s)

    config = configured_models()
    gaps: list[str] = []
    missing: list[dict[str, str]] = []

    heavy_names = set(heavy.get("names") or [])
    light_names = set(light.get("names") or [])

    if heavy.get("error"):
        gaps.append(f"heavy injoignable ({heavy_url}): {heavy['error']}")
    if light.get("error"):
        gaps.append(f"light injoignable ({light_url}): {light['error']}")

    for role, model in config.items():
        if not model:
            continue
        # Skip si URL rôle pointe vers cloud (env BASE_URL)
        base_env_map = {
            "dialogue_local": "LBG_DIALOGUE_LLM_BASE_URL",
            "dialogue_fast": "LBG_DIALOGUE_FAST_BASE_URL",
            "companion": "LBG_COMPANION_LLM_BASE_URL",
        }
        env_base = os.environ.get(base_env_map.get(role, ""), "").strip()
        if env_base and not _is_local_ollama_base(env_base):
            continue

        host = _host_for_role(role)
        pool = light_names if host == "light" else heavy_names
        label = "111-light" if host == "light" else "110-heavy"
        role_url = light_url if host == "light" else heavy_url
        if not model_available(model, pool):
            gaps.append(f"{role}: {model} absent sur {label}")
            missing.append(
                {"role": role, "model": model, "base_url": role_url, "host": host, "label": label}
            )

    failover = os.environ.get("LBG_REASON_LIGHT_FAILOVER_HEAVY", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    ok = bool(heavy.get("ok")) and len(heavy_names) > 0
    heavy_blocking = [g for g in gaps if "110-heavy" in g or g.startswith("heavy injoignable")]
    if heavy_blocking:
        ok = False
    if any("111-light" in g or g.startswith("light injoignable") for g in gaps):
        if failover and heavy.get("ok") and len(heavy_names) > 0 and not heavy_blocking:
            ok = True
        else:
            ok = False

    pull_commands = build_pull_commands(missing, heavy_url=heavy_url, light_url=light_url)
    recs = _recommendations(
        heavy=heavy,
        light=light,
        gaps=gaps,
        pull_commands=pull_commands,
        light_url=light_url,
    )

    return {
        "ok": ok,
        "source": "local",
        "track": "ollama_audit_dual_110_111",
        "base_url": heavy_url,
        "light_base_url": light_url,
        "model_count": int(heavy.get("model_count") or 0) + int(light.get("model_count") or 0),
        "heavy": heavy,
        "light": light,
        "configured": config,
        "gaps": gaps,
        "missing_models": missing,
        "pull_commands": pull_commands,
        "recommendations": recs,
        "host_role": "dual_llm_110_heavy_111_light",
        "topology": {
            "heavy": heavy_url,
            "light": light_url,
            "cortex_orch": str(getattr(settings, "cortex_orch_url", "") or ""),
        },
        "built_ms": round((time.perf_counter() - t0) * 1000, 1),
    }
