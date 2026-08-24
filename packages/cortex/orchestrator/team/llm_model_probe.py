"""Probe & failover des modèles LLM cloud (Groq, OpenAI-compat).

Interroge /v1/models périodiquement, compare avec la config active,
et propose un modèle de remplacement si le modèle configuré n'est plus disponible.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

logger = logging.getLogger("lbg.llm_model_probe")

# Modèles Groq retirés ou obsolètes — Atlas doit alerter + recommander push_secrets_vm.sh.
_LEGACY_GROQ_MODELS = frozenset(
    {
        "llama-3.1-8b-instant",
        "llama3-8b-8192",
        "llama-3.1-70b-versatile",
    }
)

_CANONICAL_GROQ_FAST = "qwen/qwen3.6-27b"

# Priorité de sélection si le modèle configuré n'est plus dispo.
# Ordre : préféré → fallback. On privilégie les modèles rapides/petits pour le fast,
# et les gros pour smart/balanced.
_GROQ_PREFERENCE = [
    "qwen/qwen3.6-27b",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "meta-llama/llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "allam-2-7b",
]


@dataclass
class ProbeResult:
    provider: str
    base_url: str
    available_models: list[str] = field(default_factory=list)
    configured_model: str = ""
    configured_available: bool = False
    recommended_model: str = ""
    error: str = ""
    probed_at: float = 0.0

    @property
    def needs_update(self) -> bool:
        return bool(self.available_models) and not self.configured_available and bool(self.recommended_model)


def probe_cloud_models(
    *,
    base_url: str = "",
    api_key: str = "",
    configured_model: str = "",
    preference: list[str] | None = None,
    timeout: float = 10.0,
    provider: str = "groq",
) -> ProbeResult:
    """Interroge /v1/models et vérifie la disponibilité du modèle configuré."""
    base = (base_url or os.environ.get("LBG_DIALOGUE_FAST_BASE_URL", "")).rstrip("/")
    key = api_key or os.environ.get("GROQ_API_KEY", "") or os.environ.get("LBG_DIALOGUE_FAST_API_KEY", "")
    model = configured_model or os.environ.get("GROQ_MODEL_FAST", "")

    if not base or not key:
        return ProbeResult(provider=provider, base_url=base, error="missing base_url or api_key")

    models_url = f"{base}/models" if base.endswith("/v1") else f"{base}/v1/models"
    result = ProbeResult(provider=provider, base_url=base, configured_model=model, probed_at=time.time())

    try:
        with httpx.Client(timeout=httpx.Timeout(timeout)) as client:
            resp = client.get(models_url, headers={"Authorization": f"Bearer {key}"})
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        result.error = str(exc)
        logger.warning("probe_cloud_models %s failed: %s", provider, exc)
        return result

    model_ids: list[str] = []
    for m in data.get("data", []):
        mid = m.get("id", "")
        if mid:
            model_ids.append(mid)
    result.available_models = sorted(model_ids)
    result.configured_available = model in model_ids

    if not result.configured_available and model_ids:
        pref = preference or _GROQ_PREFERENCE
        for candidate in pref:
            if candidate in model_ids:
                result.recommended_model = candidate
                break
        if not result.recommended_model:
            result.recommended_model = model_ids[0]
        logger.warning(
            "Model %r NOT available on %s. Available: %s. Recommend: %s",
            model, provider, model_ids, result.recommended_model,
        )
    elif result.configured_available:
        logger.info("Model %r OK on %s", model, provider)

    return result


def _groq_credentials() -> tuple[str, str]:
    base = os.environ.get("LBG_DIALOGUE_FAST_BASE_URL", "").strip().rstrip("/")
    key = (
        os.environ.get("GROQ_API_KEY", "").strip()
        or os.environ.get("LBG_DIALOGUE_FAST_API_KEY", "").strip()
    )
    return base, key


def _is_truthy(raw: str) -> bool:
    return raw.strip().lower() in ("1", "true", "yes", "on")


def audit_dialogue_fast_cloud(*, probe: bool = True) -> dict[str, Any]:
    """Audit route dialogue PNJ ``fast`` (Groq) — ``LBG_DIALOGUE_FAST_MODEL`` vs catalogue.

    Contrôle aussi l'alignement avec ``GROQ_MODEL_*`` et signale les modèles legacy retirés.
    Atlas / admin_infra : corriger ``infra/secrets/lbg.env`` puis ``push_secrets_vm.sh``.
    """
    enabled = _is_truthy(os.environ.get("LBG_DIALOGUE_FAST_ENABLED", "0"))
    fast_model = os.environ.get("LBG_DIALOGUE_FAST_MODEL", "").strip()
    groq_fast = os.environ.get("GROQ_MODEL_FAST", "").strip()
    base, key = _groq_credentials()

    gaps: list[str] = []
    warnings: list[str] = []
    recommendations: list[str] = []
    probe_payload: dict[str, Any] | None = None

    if not enabled:
        return {
            "ok": True,
            "skipped": True,
            "track": "dialogue_fast_groq",
            "reason": "LBG_DIALOGUE_FAST_ENABLED désactivé",
            "enabled": False,
            "configured_model": fast_model,
            "groq_model_fast": groq_fast,
            "gaps": gaps,
            "warnings": warnings,
            "recommendations": recommendations,
            "probe": None,
        }

    if not fast_model:
        gaps.append("dialogue_fast: LBG_DIALOGUE_FAST_MODEL vide")
        recommendations.append(
            f"Définir LBG_DIALOGUE_FAST_MODEL={_CANONICAL_GROQ_FAST} dans infra/secrets/lbg.env"
        )

    if fast_model in _LEGACY_GROQ_MODELS:
        gaps.append(f"dialogue_fast: modèle legacy Groq retiré ({fast_model})")
        recommendations.append(
            f"Remplacer LBG_DIALOGUE_FAST_MODEL par {_CANONICAL_GROQ_FAST}, "
            "aligner GROQ_MODEL_* si besoin, puis bash infra/scripts/push_secrets_vm.sh"
        )

    if groq_fast and fast_model and groq_fast != fast_model:
        gaps.append(
            "dialogue_fast: désalignement "
            f"LBG_DIALOGUE_FAST_MODEL={fast_model} vs GROQ_MODEL_FAST={groq_fast}"
        )
        recommendations.append(
            "Aligner LBG_DIALOGUE_FAST_MODEL et GROQ_MODEL_FAST sur le même modèle Groq, "
            "puis bash infra/scripts/push_secrets_vm.sh"
        )

    configured_available = True
    if probe and base and key and fast_model:
        r = probe_cloud_models(base_url=base, api_key=key, configured_model=fast_model, provider="groq_dialogue_fast")
        probe_payload = {
            "provider": r.provider,
            "configured": r.configured_model,
            "available": r.configured_available,
            "recommended": r.recommended_model,
            "models_count": len(r.available_models),
            "error": r.error,
        }
        configured_available = r.configured_available
        if r.error:
            warnings.append(f"dialogue_fast probe Groq: {r.error}")
        elif not r.configured_available:
            gaps.append(f"dialogue_fast: {fast_model} absent du catalogue Groq")
            target = r.recommended_model or _CANONICAL_GROQ_FAST
            recommendations.append(
                f"Mettre LBG_DIALOGUE_FAST_MODEL={target} dans infra/secrets/lbg.env "
                "puis bash infra/scripts/push_secrets_vm.sh (140/245/246/110)"
            )
    elif probe and enabled and fast_model and (not base or not key):
        warnings.append("dialogue_fast: Groq activé mais LBG_DIALOGUE_FAST_BASE_URL ou clé API absente")

    ok = not gaps and (not probe or configured_available or not fast_model)

    return {
        "ok": ok,
        "skipped": False,
        "track": "dialogue_fast_groq",
        "enabled": enabled,
        "configured_model": fast_model,
        "groq_model_fast": groq_fast,
        "base_url": base,
        "gaps": gaps,
        "warnings": warnings,
        "recommendations": recommendations,
        "probe": probe_payload,
    }


def probe_all_cloud() -> list[ProbeResult]:
    """Probe tous les providers cloud configurés."""
    results: list[ProbeResult] = []
    groq_url, groq_key = _groq_credentials()
    if not groq_url or not groq_key:
        return results

    seen: set[str] = set()

    # Priorité : modèle réellement utilisé par l'agent dialogue (route fast PNJ).
    dialogue_fast = os.environ.get("LBG_DIALOGUE_FAST_MODEL", "").strip()
    if dialogue_fast:
        results.append(
            probe_cloud_models(
                base_url=groq_url,
                api_key=groq_key,
                configured_model=dialogue_fast,
                provider="groq_dialogue_fast",
            )
        )
        seen.add(dialogue_fast)

    for env_var, tier in [
        ("GROQ_MODEL_FAST", "fast"),
        ("GROQ_MODEL_BALANCED", "balanced"),
        ("GROQ_MODEL_SMART", "smart"),
    ]:
        model = os.environ.get(env_var, "").strip()
        if not model or model in seen:
            continue
        results.append(
            probe_cloud_models(
                base_url=groq_url,
                api_key=groq_key,
                configured_model=model,
                provider=f"groq_{tier}",
            )
        )
        seen.add(model)

    return results


def auto_fix_env(results: list[ProbeResult] | None = None) -> dict[str, Any]:
    """Si un modèle n'est plus dispo, met à jour os.environ en runtime.

    Ne persiste PAS sur disque — juste le process courant.
    Retourne un résumé des changements appliqués.
    """
    if results is None:
        results = probe_all_cloud()

    changes: dict[str, str] = {}
    for r in results:
        if not r.needs_update:
            continue
        old = r.configured_model
        new = r.recommended_model
        env_vars_to_patch = [
            "GROQ_MODEL_FAST", "GROQ_MODEL_BALANCED", "GROQ_MODEL_SMART",
            "LBG_DIALOGUE_FAST_MODEL", "LBG_ORCHESTRATOR_INTENT_LLM_MODEL",
        ]
        for ev in env_vars_to_patch:
            current = os.environ.get(ev, "").strip()
            if current == old:
                os.environ[ev] = new
                changes[ev] = f"{old} -> {new}"
                logger.warning("auto_fix_env: %s = %s (was %s)", ev, new, old)

    return {
        "patched": bool(changes),
        "changes": changes,
        "probes": [
            {
                "provider": r.provider,
                "configured": r.configured_model,
                "available": r.configured_available,
                "recommended": r.recommended_model,
                "models_count": len(r.available_models),
            }
            for r in results
        ],
    }
