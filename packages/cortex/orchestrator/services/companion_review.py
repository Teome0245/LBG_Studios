"""Contre-pouvoir Compagnon — revue avant dry-run→réel (pas Lyra).

Lyra = présence / jauges. Ici = validateur de décision/action (Prométhée-like).
Déterministe d'abord ($0, rapide) ; LLM optionnel profil ``json`` (.111) si activé.
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any

from pydantic import BaseModel, Field

# Lecture seule / sonde — dry-run auto OK, réel soft
_SOFT_KINDS = frozenset(
    {
        "http_get",
        "systemd_is_active",
        "selfcheck",
        "vm_memory_probe",
        "proxmox_status",
        "proxmox_guest_lock",
        "infra_watchdog",
        "memory_remediation_plan",
        "remediation_plan",
        "remediation_validate",
        "default_browser_info",
        "agent_session_status",
        "mail_imap_preview",
        "comfyui_status",
        "comfyui_history",
        "comfyui_view",
    }
)

# Réel toujours verrouillé jusqu'à override humain explicite
_HARD_BLOCK_REAL = frozenset(
    {
        "fix_session0",
        "click_xy",
        "move_xy",
        "drag_xy",
        "type_text",
        "hotkey",
        "run_steps",
        "remediation_apply",
        "systemd_restart",
        "ssh_run",
        "comfyui_restart",
        "comfyui_patch_and_queue",
        "notepad_append",
    }
)

_SYSTEM = """Tu es le contre-pouvoir Studio LBG (garde / Prométhée-gate).
Tu critiques la proposition d'action du Compagnon AVANT exécution réelle.
Français. Un seul objet JSON, pas de markdown.

Schéma :
{
  "pass": true,
  "block_real": false,
  "summary": "1 phrase",
  "risks": ["…"],
  "alternatives": ["…"],
  "confidence": 0.0
}

Règles :
- pass=false seulement si illégal / hors périmètre LAB / clairement absurde.
- block_real=true si effet de bord desktop/infra non trivial (ouvrir app, écrire, réparer session, restart…).
- Lecture seule (mail preview, status, selfcheck) → pass=true, block_real=false.
- Tu ne décides pas à la place de l'humain : tu avertis.
Max 4 risks, 3 alternatives. confidence 0..1.
"""


class CompanionReview(BaseModel):
    ok: bool = True
    pass_: bool = Field(True, alias="pass")
    block_real: bool = False
    auto_dry_run: bool = False
    summary: str = ""
    risks: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    confidence: float = 0.7
    source: str = "deterministic"  # deterministic | llm | fallback
    latency_ms: int = 0
    model: str | None = None
    error: str | None = None

    model_config = {"populate_by_name": True}


def _env_truthy(name: str, default: str = "1") -> bool:
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes", "on")


def companion_review_enabled() -> bool:
    return _env_truthy("LBG_COMPANION_REVIEW", "1")


def companion_review_llm_enabled() -> bool:
    return _env_truthy("LBG_COMPANION_REVIEW_LLM", "0")


def _action_kind(proposal: dict[str, Any] | None) -> str:
    if not isinstance(proposal, dict):
        return ""
    action = proposal.get("action")
    if isinstance(action, dict):
        return str(action.get("kind") or "").strip()
    return ""


def _risk_level(proposal: dict[str, Any] | None) -> str:
    if not isinstance(proposal, dict):
        return ""
    return str(proposal.get("risk_level") or "").strip().lower()


def _extract_json(text: str) -> dict[str, Any] | None:
    raw = (text or "").strip()
    if not raw:
        return None
    m = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL | re.IGNORECASE)
    if m:
        raw = m.group(1).strip()
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        pass
    start, end = raw.find("{"), raw.rfind("}")
    if start >= 0 and end > start:
        try:
            data = json.loads(raw[start : end + 1])
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            return None
    return None


def _deterministic_review(proposal: dict[str, Any] | None, source_text: str) -> CompanionReview:
    kind = _action_kind(proposal)
    risk = _risk_level(proposal)
    summary = ""
    if isinstance(proposal, dict):
        summary = str(proposal.get("summary") or proposal.get("capability") or "")[:200]

    if kind in _SOFT_KINDS or risk in ("low", "read"):
        return CompanionReview(
            **{
                "pass": True,
                "block_real": False,
                "auto_dry_run": True,
                "summary": f"Lecture / sonde OK — {summary or kind or 'action douce'}",
                "risks": [],
                "alternatives": [],
                "confidence": 0.9,
                "source": "deterministic",
            }
        )

    if kind in _HARD_BLOCK_REAL or risk == "high":
        return CompanionReview(
            **{
                "pass": True,
                "block_real": True,
                "auto_dry_run": True,
                "summary": f"Contre-pouvoir : réel verrouillé — {kind or risk or 'risque élevé'}",
                "risks": [
                    "Effet de bord possible sur poste / infra",
                    "Exiger dry-run puis jeton + override humain",
                ],
                "alternatives": [
                    "Lancer Dry-run d'abord",
                    "Réduire le scope (lecture seule)",
                ],
                "confidence": 0.95,
                "source": "deterministic",
            }
        )

    # Moyen : dry-run auto, réel possible avec jeton (pas de block sauf LLM)
    return CompanionReview(
        **{
            "pass": True,
            "block_real": False,
            "auto_dry_run": True,
            "summary": f"Revue déterministe — {summary or kind or source_text[:80] or 'OK'}",
            "risks": ["Vérifier la cible (desktop_target / host) avant Réel"],
            "alternatives": [],
            "confidence": 0.75,
            "source": "deterministic",
        }
    )


def _llm_enrich(base: CompanionReview, proposal: dict[str, Any] | None, source_text: str) -> CompanionReview:
    """Enrichit avec avis LLM (profil json / .111) — ne remplace pas le hard-block déterministe."""
    try:
        from team.reason_llm import complete_reason, reason_llm_enabled
    except Exception as exc:  # pragma: no cover
        base.error = f"import_reason: {exc}"
        return base

    if not reason_llm_enabled():
        base.error = "reason_llm_disabled"
        return base

    started = time.time()
    user = (
        f"source_text: {(source_text or '')[:1500]}\n"
        f"proposal: {json.dumps(proposal or {}, ensure_ascii=False)[:2500]}"
    )
    llm = complete_reason(system=_SYSTEM, user=user, temperature=0.2, profile="json")
    text = str(llm.get("text") or "") if isinstance(llm, dict) else ""
    parsed = _extract_json(text) or {}
    latency = int((time.time() - started) * 1000)

    if not (isinstance(llm, dict) and llm.get("ok")):
        base.error = str((llm or {}).get("error") or "llm_failed")
        base.latency_ms = latency
        return base

    # Hard block déterministe ne peut pas être levé par le LLM
    block = bool(base.block_real) or bool(parsed.get("block_real"))
    risks = [str(x).strip() for x in (parsed.get("risks") or []) if str(x).strip()][:4]
    alts = [str(x).strip() for x in (parsed.get("alternatives") or []) if str(x).strip()][:3]
    if base.risks:
        risks = list(dict.fromkeys([*base.risks, *risks]))[:4]
    if base.alternatives:
        alts = list(dict.fromkeys([*base.alternatives, *alts]))[:3]

    conf = parsed.get("confidence")
    try:
        conf_f = float(conf) if conf is not None else base.confidence
    except (TypeError, ValueError):
        conf_f = base.confidence

    return CompanionReview(
        **{
            "pass": bool(parsed.get("pass", base.pass_)),
            "block_real": block,
            "auto_dry_run": base.auto_dry_run,
            "summary": str(parsed.get("summary") or base.summary)[:400],
            "risks": risks or base.risks,
            "alternatives": alts or base.alternatives,
            "confidence": max(0.0, min(1.0, conf_f)),
            "source": "llm",
            "latency_ms": latency,
            "model": llm.get("model") if isinstance(llm, dict) else None,
            "error": None,
        }
    )


def review_companion_proposal(
    proposal: dict[str, Any] | None,
    *,
    source_text: str = "",
    force_llm: bool = False,
) -> CompanionReview:
    """Revue contre-pouvoir. Toujours un verdict (même si LLM off / KO)."""
    if not companion_review_enabled():
        return CompanionReview(
            **{
                "pass": True,
                "block_real": False,
                "auto_dry_run": False,
                "summary": "Contre-pouvoir désactivé (LBG_COMPANION_REVIEW=0)",
                "source": "fallback",
                "confidence": 0.0,
            }
        )

    base = _deterministic_review(proposal, source_text)
    use_llm = force_llm or companion_review_llm_enabled()
    if use_llm and not base.block_real:
        # Même si hard-block, on peut enrichir les risques — mais on appelle aussi si block
        pass
    if use_llm:
        return _llm_enrich(base, proposal, source_text)
    return base
