"""
Classifieur d'intention System One via Laya (HTTP Jev-compatible).

Même espace d'intents « texte seul » que le classifieur LLM — pas de desktop /
world / opengame sans action structurée (le routeur les gère avant).
"""

from __future__ import annotations

import os
from typing import Any

from introspection.llm_intent_classifier import ALLOWED_INTENTS
from services.laya_client import (
    extract_choice,
    extract_noul,
    laya_base_url,
    systemone_predict,
)

# Critères FR alignés sur SYSTEM_PROMPT du classifieur LLM (≤15 options : OK pour Laya).
INTENT_CRITERIA: dict[str, str] = {
    "npc_dialogue": "parler à un personnage, jeu de rôle, conversation dans le monde fictif",
    "quest_request": "quête, mission, objectif à accomplir dans le jeu",
    "combat_action": "combat, attaque, affrontement",
    "devops_probe": "infrastructure, santé des services, diagnostic technique, logs, systemd",
    "project_pm": "chef de projet, jalons, roadmap, vision produit, planning",
    "infographiste_status": "où en est LoRA, tri images, Kohya, Pygmalion, buckets",
    "sprites_status": "sprites 2D Prime Client, déploiement PNG",
    "godot_status": "client Godot, ZB-0/ZB-1, sidecar, Scrapaltai",
    "team_status": "équipe virtuelle, tâches team, timers",
    "infra_status": "état infra, healthz, Ollama, VM, déploiement",
    "project_status": "point d'avancement projet global",
    "unknown": "rien ne correspond clairement ou trop ambigu",
}

assert set(INTENT_CRITERIA) == set(ALLOWED_INTENTS)


def intent_laya_env_enabled() -> bool:
    v = os.environ.get("LBG_ORCHESTRATOR_INTENT_LAYA", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def should_use_laya_intent(context: dict[str, Any]) -> bool:
    raw = context.get("_intent_classify")
    if isinstance(raw, str):
        s = raw.strip().lower()
        if s in ("deterministic", "llm"):
            return False
        if s == "laya":
            return True
    return intent_laya_env_enabled()


def _accept_conf() -> float:
    try:
        return float(os.environ.get("LBG_ORCHESTRATOR_INTENT_LAYA_ACCEPT_CONF", "0.30").strip())
    except ValueError:
        return 0.30


def _override_conf() -> float:
    try:
        return float(os.environ.get("LBG_ORCHESTRATOR_INTENT_LAYA_OVERRIDE_CONF", "0.85").strip())
    except ValueError:
        return 0.85


def _needs_llm_thresh() -> float:
    try:
        return float(os.environ.get("LBG_ORCHESTRATOR_INTENT_LAYA_NEEDS_LLM_THRESH", "0.70").strip())
    except ValueError:
        return 0.70


def intent_questions() -> dict[str, Any]:
    return {
        "intent": {
            "type": "choice",
            "instructions": (
                "Quelle intention utilisateur pour l'orchestrateur multi-agents "
                "LBG Studios (MMO + Studio Compagnon) ?"
            ),
            "criteria": dict(INTENT_CRITERIA),
        },
        "needs_llm": {
            "type": "noul",
            "instructions": (
                "La requête est-elle trop ambiguë ou trop riche pour une décision "
                "System 1 seule, et devrait-elle être escaladée à un LLM ?"
            ),
            "criteria": {
                "true": "ambiguë, multi-intent, ou nécessite du raisonnement ouvert",
                "false": "intention claire parmi les options listées",
            },
        },
    }


def classify_intent_laya(user_text: str) -> tuple[str, float, dict[str, Any]] | None:
    """
    Appelle Laya (HTTP). Retourne (intent, confidence, meta) ou None si indisponible.

    ``confidence`` exposée = max(entropie Laya, proba top) pour ne pas rejeter
    des choix clairs en haute cardinalité (12 intents).
    """
    if not laya_base_url():
        return None
    text = user_text.strip()[:4000]
    if not text:
        return None
    state = {"text": text, "source": "orchestrator.intent"}
    resp = systemone_predict(state=state, questions=intent_questions())
    if resp is None:
        return None
    label, conf, probs = extract_choice(resp, "intent")
    if not label or label not in ALLOWED_INTENTS:
        label = "unknown"
        conf = min(conf, 0.4) if conf else 0.4
    top_prob = max(probs.values()) if probs else 0.0
    # Score d'acceptation : le plus fort entre confidence Laya et P(top).
    score = max(conf, top_prob)
    needs_llm = extract_noul(resp, "needs_llm")
    meta: dict[str, Any] = {
        "intent_source": "laya",
        "laya_model": resp.get("model"),
        "laya_probabilities": probs,
        "laya_confidence_raw": conf,
        "laya_top_prob": top_prob,
    }
    if needs_llm is not None:
        meta["laya_needs_llm"] = needs_llm
    return label, score, meta


def laya_should_accept(
    *,
    det_intent: str,
    laya_intent: str,
    laya_conf: float,
    needs_llm: float | None,
) -> bool:
    """Règles d'acceptation vs déterministe + escalade LLM."""
    if needs_llm is not None and needs_llm >= _needs_llm_thresh():
        return False
    if laya_conf < _accept_conf():
        return False
    if det_intent == "unknown":
        return True
    return laya_conf >= _override_conf()
