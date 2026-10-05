from __future__ import annotations

import json
import os
import re
from typing import Literal

from pydantic import BaseModel, Field

from shared_registry import capability_registry

from lbg_agents.desktop_apps import (
    enrich_open_app_action,
    extract_exe_path_from_goal,
    repair_app_deps_action_from_goal,
    resolve_second_avis_concurrent,
    sanitize_desktop_app_slug,
    second_avis_open_app_action,
)
from lbg_agents.desktop_targets import infer_desktop_target_from_text

from services.lia_jobs import (
    LIA_ACTOR_ID,
    lia_core3_context_patch,
    lia_core3_plan_action,
    lia_tick_prompt_from_objective,
    objective_mentions_lia_mmo,
)


ProposalSource = Literal["deterministic", "mmo_session_bridge", "team_dev_game", "llm_map"]

# Lecture seule / URL / sondes — pas de Validation L2 ni case soft-confirm en LAB
_SOFT_DESKTOP_KINDS = frozenset(
    {
        "mail_imap_preview",
        "open_url",
        "search_web_open",
        "default_browser_info",
        "agent_session_status",
    }
)


class ActionProposal(BaseModel):
    capability: str
    routed_to: str
    action_context_key: str
    action: dict[str, object]
    context_patch: dict[str, object] = Field(default_factory=dict)
    summary: str
    risk_level: str
    requires_review: bool = True
    confidence: float = Field(..., ge=0.0, le=1.0)
    source: ProposalSource = "deterministic"
    mmo_trace: dict[str, object] | None = None


class ActionProposalResult(BaseModel):
    proposal: ActionProposal | None = None
    reason: str | None = None


def propose_action_from_text(text: str, context: dict[str, object] | None = None) -> ActionProposalResult:
    ctx = context if isinstance(context, dict) else {}
    raw = text.strip()
    normalized = _normalize(raw)
    if not normalized:
        return ActionProposalResult(reason="Texte vide.")

    proposal = _propose_deterministic(raw, normalized, ctx)
    if proposal is None:
        # Réflexion LLM → phrase canonique re-passée au déterministe (pas d'exécution libre).
        proposal = _propose_llm_assisted(raw, normalized, ctx)
    if proposal is None:
        return ActionProposalResult(
            reason="Aucune action sûre reconnue ; rester en conversation ou demander une précision."
        )
    return ActionProposalResult(proposal=proposal)


def _propose_deterministic(
    raw: str, normalized: str, ctx: dict[str, object]
) -> ActionProposal | None:
    return (
        _propose_notepad(raw, normalized, ctx)
        or _propose_mail_preview(raw, normalized)
        or _propose_morning_brief(raw, normalized)
        or _propose_memory_recall(raw, normalized)
        or _propose_agent_session_status(raw, normalized)
        or _propose_fix_session0(raw, normalized)
        or _propose_update_vscode(raw, normalized)
        or _propose_second_avis(raw, normalized)
        or _propose_core3_lia(raw, normalized)
        or _propose_capabilities_inventory(normalized)
        or _propose_network_inventory(normalized)
        or _propose_infra_selfcheck(normalized)
        or _propose_dialogue_consult(normalized, raw)
        or _propose_project_pm_consult(normalized)
        or _propose_web_search(raw, normalized)
        or _propose_job_synthesis(normalized)
        or _propose_vm_memory_probe(normalized)
        or _propose_proxmox_status(normalized)
        or _propose_repair_app_deps(raw, normalized)
        or _propose_open_url(raw, normalized)
        or _propose_default_browser(raw, normalized)
        or _propose_open_app(raw, normalized)
        or _propose_team_dev_game_forge(raw, normalized, ctx)
        or _propose_mmo_dev_plan(raw, normalized, ctx)
        or _propose_useful_default(normalized)
    )


def _action_proposal_llm_enabled() -> bool:
    return os.environ.get("LBG_ACTION_PROPOSAL_LLM", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


_LLM_MAP_SYSTEM = """Tu es le routeur d'actions du Compagnon LBG (ops studio / poste / LAN).
Réponds UNIQUEMENT avec un objet JSON valide, une seule ligne, sans markdown ni texte autour :
{"intent":"<id>","canonical_text":"<phrase FR>","why":"<raison courte>"}

intent autorisés uniquement :
mail_imap_preview | morning_brief | memory_recall | selfcheck | network_inventory | search_web_open | open_app | open_url | default_browser_info | jobs_l2 | fix_session0 | agent_session_status | update_vscode | second_avis | none

Exemples :
- "regarde mon inbox" → {"intent":"mail_imap_preview","canonical_text":"regarde mes mails récents","why":"aperçu IMAP"}
- "fais mon brief du matin" → {"intent":"morning_brief","canonical_text":"fais mon brief du matin","why":"point studio RO"}
- "montre ta mémoire / ce que tu retiens" → {"intent":"memory_recall","canonical_text":"montre ce que tu retiens (mémoire agent)","why":"Self + leçons"}
- "check le LAN" → {"intent":"selfcheck","canonical_text":"fais un diagnostic infra selfcheck LAN","why":"sonde read-only"}
- "ouvre vghd" → {"intent":"open_app","canonical_text":"ouvre vghd sur mon pc","why":"lancer app"}
- "jobs en attente" → {"intent":"jobs_l2","canonical_text":"ouvre http://192.168.0.140:8080/#/jobs dans le navigateur","why":"revue L2"}
- "les apps ne s'ouvrent pas / session 0" → {"intent":"fix_session0","canonical_text":"répare session 0 de l agent desktop","why":"UI invisible"}
- "mets à jour vscode" → {"intent":"update_vscode","canonical_text":"mets à jour vscode sur omarchy","why":"MAJ IDE .143"}
- "second avis / deuxième avis" → {"intent":"second_avis","canonical_text":"second avis claude code sur omarchy","why":"concurrent IDE ADR 0023"}

Interdit : piraterie, torrents de contenus protégés, fraude → intent=none.
Conversation pure sans action poste/LAN → intent=none.
canonical_text doit être une phrase courte exécutable (pas la demande brute si elle est ambiguë).
"""


_INTENT_CANONICAL_FALLBACK: dict[str, str] = {
    "mail_imap_preview": "regarde mes mails récents",
    "morning_brief": "fais mon brief du matin",
    "memory_recall": "montre ce que tu retiens (mémoire agent)",
    "selfcheck": "fais un diagnostic infra selfcheck LAN",
    "network_inventory": "fais un inventaire réseau LAN cartographie des appareils",
    "search_web_open": "cherche sur internet LBG Studios",
    "open_app": "ouvre vghd sur mon pc",
    "open_url": "ouvre http://192.168.0.140:8080/#/jobs dans le navigateur",
    "default_browser_info": "quel est mon navigateur par défaut",
    "jobs_l2": "ouvre http://192.168.0.140:8080/#/jobs dans le navigateur",
    "fix_session0": "répare session 0 de l agent desktop",
    "agent_session_status": "vérifie la session de l agent desktop",
    "update_vscode": "mets à jour vscode sur omarchy",
    "second_avis": "second avis claude code sur omarchy",
}


def _extract_json_object(text: str) -> dict[str, object] | None:
    raw = (text or "").strip()
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def _propose_llm_assisted(
    raw: str, normalized: str, ctx: dict[str, object]
) -> ActionProposal | None:
    """Mappe une intention libre vers une action allowlistée via LLM léger (.111 json)."""
    if not _action_proposal_llm_enabled():
        return None
    if len(normalized) < 6:
        return None
    # Évite un 2e appel LLM si déjà une reformulation interne.
    if ctx.get("_llm_map_skip"):
        return None
    try:
        from team.reason_llm import complete_reason, reason_llm_enabled
    except Exception:
        return None
    if not reason_llm_enabled():
        return None

    prev_timeout = os.environ.get("LBG_REASON_TIMEOUT_S")
    prev_tokens = os.environ.get("LBG_REASON_MAX_TOKENS")
    prev_failover_heavy = os.environ.get("LBG_REASON_LIGHT_FAILOVER_HEAVY")
    prev_failover = os.environ.get("LBG_REASON_FAILOVER")
    try:
        # AGIR snappy : light .111 only (pas de failover heavy / cloud / colab).
        os.environ["LBG_REASON_TIMEOUT_S"] = os.environ.get(
            "LBG_ACTION_PROPOSAL_LLM_TIMEOUT_S", "10"
        )
        os.environ["LBG_REASON_MAX_TOKENS"] = os.environ.get(
            "LBG_ACTION_PROPOSAL_LLM_MAX_TOKENS", "180"
        )
        os.environ["LBG_REASON_LIGHT_FAILOVER_HEAVY"] = "0"
        os.environ["LBG_REASON_FAILOVER"] = "0"
        out = complete_reason(
            system=_LLM_MAP_SYSTEM,
            user=f"Demande utilisateur : {raw[:500]}",
            temperature=0.1,
            prefer_cloud=False,
            profile="json",
        )
    finally:
        if prev_timeout is None:
            os.environ.pop("LBG_REASON_TIMEOUT_S", None)
        else:
            os.environ["LBG_REASON_TIMEOUT_S"] = prev_timeout
        if prev_tokens is None:
            os.environ.pop("LBG_REASON_MAX_TOKENS", None)
        else:
            os.environ["LBG_REASON_MAX_TOKENS"] = prev_tokens
        if prev_failover_heavy is None:
            os.environ.pop("LBG_REASON_LIGHT_FAILOVER_HEAVY", None)
        else:
            os.environ["LBG_REASON_LIGHT_FAILOVER_HEAVY"] = prev_failover_heavy
        if prev_failover is None:
            os.environ.pop("LBG_REASON_FAILOVER", None)
        else:
            os.environ["LBG_REASON_FAILOVER"] = prev_failover

    if not out.get("ok"):
        return None
    data = _extract_json_object(str(out.get("text") or ""))
    if not data:
        return None
    intent = str(data.get("intent") or "").strip().lower()
    if intent in ("", "none", "null", "conversation"):
        return None
    # Toujours préférer la phrase canonique connue (le petit modèle echo souvent la demande).
    canonical = _INTENT_CANONICAL_FALLBACK.get(intent, "")
    llm_can = str(data.get("canonical_text") or "").strip()
    if llm_can and _normalize(llm_can) != normalized and intent not in _INTENT_CANONICAL_FALLBACK:
        canonical = llm_can
    elif intent in ("search_web_open", "open_app", "open_url") and llm_can and _normalize(llm_can) != normalized:
        canonical = llm_can
    if not canonical:
        return None

    mapped = _propose_deterministic(canonical, _normalize(canonical), {**ctx, "_llm_map_skip": True})
    if mapped is None:
        return None
    # Préserver la cible desktop déduite du texte utilisateur (ex. « sur omarchy »).
    src_target = infer_desktop_target_from_text(raw)
    if src_target and not mapped.context_patch.get("desktop_target"):
        mapped.context_patch = {**mapped.context_patch, "desktop_target": src_target}
    why = str(data.get("why") or "").strip()
    if why:
        mapped.summary = f"{mapped.summary} (réflexion : {why[:160]})"
    mapped.source = "llm_map"
    mapped.confidence = min(0.85, max(0.55, float(mapped.confidence) * 0.92))
    return mapped


def _propose_agent_session_status(raw: str, normalized: str) -> ActionProposal | None:
    if not re.search(
        r"\b("
        r"session\s+(?:de\s+l['']?)?agent|"
        r"statut\s+agent\s+desktop|"
        r"agent\s+(?:en\s+)?session|"
        r"v[eé]rif(?:ie|ier)\s+(?:la\s+)?session|"
        r"gui\s+ready|wayland|"
        r"session\s+sur\s+omarchy"
        r")\b",
        normalized,
    ):
        return None
    # Ne pas confondre avec remédiation Session 0
    if re.search(r"\b(r[eé]pare?|fix|heal)\b", normalized) and re.search(
        r"\b(session\s*0|session0)\b", normalized
    ):
        return None
    return _desktop_proposal(
        action={"kind": "agent_session_status"},
        summary="Lire la session de l’agent desktop (Windows Session 0 / Omarchy Wayland).",
        confidence=0.9,
        text=raw,
    )


def _propose_fix_session0(raw: str, normalized: str) -> ActionProposal | None:
    """Remédiation agent desktop — Windows Session 0 ou heal Omarchy .143."""
    if not re.search(
        r"\b(session\s*0|session0|agent\s+invisible|apps?\s+invisibles?|"
        r"rien\s+(?:ne\s+)?s['']?ouvre|fen[eê]tres?\s+invisibles?|"
        r"r[eé]pare?\s+(?:l['']?)?agent|fix\s+session|heal\s+(?:l['']?)?agent|"
        r"omarchy\s+(?:down|ko|mort))\b",
        normalized,
    ):
        return None
    return _desktop_proposal(
        action={"kind": "fix_session0"},
        summary=(
            "Remédier l’agent desktop : Session 0 (Windows .10) ou restart+GUI "
            "(Omarchy .143) selon la cible."
        ),
        confidence=0.88,
        text=raw,
    )


def _propose_update_vscode(raw: str, normalized: str) -> ActionProposal | None:
    """MAJ paquet VS Code sur Omarchy .143 (yay visual-studio-code-bin)."""
    if not re.search(
        r"\b(m(?:ets?|ettre)\s+[àa]\s+jour|update|upgrade|mise\s+[àa]\s+jour)\b",
        normalized,
    ):
        return None
    ide = bool(
        re.search(
            r"\b(vs\s*code|vscode|visual\s+studio\s+code|codium)\b",
            normalized,
        )
    )
    code_omarchy = bool(re.search(r"\bcode\b", normalized) and re.search(r"\bomarchy\b", normalized))
    if not ide and not code_omarchy:
        return None
    # Cible forcément .143 (paquet AUR local) — forcer omarchy si non déduit.
    text = raw if re.search(r"\bomarchy\b", normalized) else f"{raw} sur omarchy"
    return _desktop_proposal(
        action={"kind": "update_vscode"},
        summary=(
            "Mettre à jour VS Code sur Omarchy (.143) via yay "
            "(visual-studio-code-bin). À faire hors session Cline critique."
        ),
        confidence=0.9,
        text=text,
    )


def _propose_second_avis(raw: str, normalized: str) -> ActionProposal | None:
    """Ouvre un outil concurrent pour second avis (ADR 0023) — défaut Claude Code sur .143."""
    if not re.search(
        r"\b(second\s+avis|deuxi[eè]me\s+avis|2(?:e|eme|\u00e8me)\s+avis|"
        r"second\s+opinion|avis\s+concurrent)\b",
        normalized,
    ):
        return None
    app_id, label, status = resolve_second_avis_concurrent(raw)
    action = second_avis_open_app_action(raw)
    text = raw if re.search(r"\bomarchy\b", normalized) else f"{raw} sur omarchy"
    status_fr = "autorisé" if status == "autorise" else "expérimentation"
    summary = (
        f"Second avis : ouvrir « {label} » ({status_fr}) sur Omarchy (.143), "
        f"workspace studio — concurrent de Cline (ADR 0023). "
        f"Une session bornée ; pas d’écriture parallèle non revue."
    )
    proposal = _desktop_proposal(
        action=action,
        summary=summary,
        confidence=0.9,
        text=text,
    )
    # Garantir cible éditeur même si le texte omet « omarchy »
    if not proposal.context_patch.get("desktop_target"):
        proposal.context_patch = {**proposal.context_patch, "desktop_target": "omarchy"}
    proposal.context_patch = {
        **proposal.context_patch,
        "second_avis": {
            "concurrent": app_id,
            "label": label,
            "status": status,
            "primary_hint": "cline",
        },
    }
    return proposal


def _propose_notepad(raw: str, normalized: str, context: dict[str, object]) -> ActionProposal | None:
    if not re.search(r"\b(notepad|bloc[- ]?notes?|bloc note|editeur|éditeur)\b", normalized):
        return None
    if not re.search(r"\b(ecris|écris|ecrire|écrire|note|ajoute|append|dicte|dictée|dictee)\b", normalized):
        return None
    content = _extract_after(
        raw,
        ("écris", "ecris", "écrire", "ecrire", "note", "ajoute", "append", "dicte", "dictée", "dictee"),
    )
    if not content:
        content = raw
    path = context.get("desktop_default_notepad_path")
    path_s = path.strip() if isinstance(path, str) and path.strip() else r"C:\Users\Public\lbg_desktop.txt"
    return _desktop_proposal(
        action={"kind": "notepad_append", "path": path_s, "text": content.rstrip() + "\n"},
        summary="Préparer une écriture bornée dans un fichier ouvert avec Notepad.",
        confidence=0.82,
        text=raw,
    )


def _propose_project_pm_consult(normalized: str) -> ActionProposal | None:
    """Questions projet / chemins doc — agent PM (jalons, docs/, plan de route)."""
    if not re.search(
        r"\b(chef de projet|jalon|roadmap|plan de route|vision produit|état d'avancement|"
        r"statut du projet|docs/|documentation)\b",
        normalized,
    ):
        if not (
            re.search(r"\b(chemin|fichier|fichiers|path|repo|modifier|éditer|editer)\b", normalized)
            and re.search(r"\b(donne|indique|montre|quel|quelle|où|ou)\b", normalized)
        ):
            return None
    cap = capability_registry.get("project_pm")
    assert cap is not None
    return ActionProposal(
        capability=cap.name,
        routed_to=cap.routed_to,
        action_context_key=cap.action_context_key or "project_pm",
        action={},
        context_patch={"pm_focus": True},
        summary="Consulter le chef de projet (jalons, docs, chemins de fichiers documentés).",
        risk_level=cap.risk_level,
        confidence=0.78,
    )


def _propose_core3_lia(raw: str, normalized: str) -> ActionProposal | None:
    """Pilotage Lia en MMO via sidecar Core3 (player_think + incarnation)."""
    if not objective_mentions_lia_mmo(normalized):
        return None
    cap = capability_registry.get("core3_bot_action")
    assert cap is not None
    prompt = lia_tick_prompt_from_objective(raw)
    patch = lia_core3_context_patch(prompt=prompt)
    patch["_lia_job_actor"] = LIA_ACTOR_ID
    return ActionProposal(
        capability=cap.name,
        routed_to=cap.routed_to,
        action_context_key=cap.action_context_key or "core3_action",
        action=lia_core3_plan_action(prompt=prompt),
        context_patch=patch,
        summary="Faire jouer Lia en MMO (incarnation orchestrateur, action enqueue via sidecar).",
        risk_level=cap.risk_level,
        confidence=0.84,
    )


def _propose_capabilities_inventory(normalized: str) -> ActionProposal | None:
    """Liste / inventaire des agents (handlers) et capabilities du registry orchestrateur."""
    has_agents = re.search(r"\b(agents?|handlers?|services?)\b", normalized)
    has_caps = re.search(r"\b(capabilit[eé]s?|capabilities|fonctionnalit[eé]s?)\b", normalized)
    list_intent = re.search(
        r"\b(liste|lister|[eé]tablir|[eé]tablie|[eé]tablis|inventaire|disponible|disponibles|"
        r"registry|registre|quels?|quelles?|[eé]num[eè]re|affiche|montre)\b",
        normalized,
    )
    if not ((has_agents and has_caps) or (list_intent and (has_agents or has_caps))):
        return None
    cap = capability_registry.get("npc_dialogue")
    assert cap is not None
    return ActionProposal(
        capability=cap.name,
        routed_to=cap.routed_to,
        action_context_key=cap.action_context_key or "",
        action={},
        context_patch={"_capabilities_inventory": True},
        summary="Inventaire direct du registry (agents routed_to + capabilities), sans LLM.",
        risk_level=cap.risk_level,
        confidence=0.82,
    )


def _propose_network_inventory(normalized: str) -> ActionProposal | None:
    """Cartographie LAN / appareils — sondes read-only sur hôtes connus."""
    has_scope = re.search(
        r"\b(réseau|reseau|réseaux|reseaux|infra|infrastructure|appareil|appareils|"
        r"lan|vm|machines?|topologie|hôtes?|hotes?)\b",
        normalized,
    )
    has_intent = re.search(
        r"\b(inventaire|cartographie|cartograph|sond|découvr|decouvr|recens|"
        r"présents?|presents?|établir|établie|établis|analys|audit|carte)\b",
        normalized,
    )
    if not (has_scope and has_intent):
        return None
    cap = capability_registry.get("network_inventory")
    assert cap is not None
    return ActionProposal(
        capability=cap.name,
        routed_to=cap.routed_to,
        action_context_key=cap.action_context_key or "network_inventory",
        action={"kind": "network_inventory"},
        context_patch={"network_inventory": True},
        summary="Inventaire réseau LAN (sondes HTTP/TCP read-only sur core/front/mmo/desktop).",
        risk_level=cap.risk_level,
        confidence=0.8,
    )


def _propose_dialogue_consult(normalized: str, raw: str) -> ActionProposal | None:
    """Conseil / plan / explication sans action desktop ou devops destructive."""
    if re.search(
        r"\b(internet|recherche web|sur le web|ouvre|lance|sonde|selfcheck|healthz|notepad|vghd|"
        r"systemctl|ssh|desktop)\b",
        normalized,
    ):
        return None
    logs_intent = re.search(r"\b(logs?|journal|journalisation|logging|audit)\b", normalized) and re.search(
        r"\b(ajoute|ajouter|mettre|implémente|implemente|créer|creer|système|systeme|"
        r"débogage|debug|rétention|retention|facilit)\b",
        normalized,
    )
    advice_intent = re.search(
        r"\b(conseil|recommand|explique|décris|decris|propose|plan)\b.*\b(comment|quoi|où|ou)\b",
        normalized,
    ) or re.search(r"\b(comment|pourquoi)\b", normalized)
    if not (logs_intent or advice_intent):
        return None
    cap = capability_registry.get("npc_dialogue")
    assert cap is not None
    summary = (
        "Proposer un plan de journalisation (fichiers, format, rétention)."
        if logs_intent
        else "Répondre en langage naturel (conseil / orientation repo)."
    )
    return ActionProposal(
        capability=cap.name,
        routed_to=cap.routed_to,
        action_context_key=cap.action_context_key or "",
        action={},
        context_patch={"_dialogue_consult": True},
        summary=summary,
        risk_level=cap.risk_level,
        confidence=0.75,
    )


def _propose_web_search(raw: str, normalized: str) -> ActionProposal | None:
    if not re.search(r"\b(cherche|chercher|recherche|rechercher|trouve|internet|web|site)\b", normalized):
        return None
    # « chemin du fichier à modifier » n'est pas une recherche web.
    if re.search(r"\b(chemin|fichier|fichiers|path)\b", normalized) and not re.search(
        r"\b(internet|recherche web|sur le web|site web|google|duckduckgo)\b", normalized
    ):
        return None
    if re.search(
        r"\b(mails?|e-?mails?|courriels?|courriers?|inbox|imap|bo[iî]te(?:\s+mail)?)\b",
        normalized,
    ):
        return None
    query = _extract_after(raw, ("cherche sur internet", "recherche sur internet", "cherche", "recherche", "trouve"))
    query = re.sub(r"^\s*(le\s+)?site\s+(de|du|d'|des)?\s*", "", query, flags=re.IGNORECASE).strip()
    if not query:
        query = raw
    return _desktop_proposal(
        action={"kind": "search_web_open", "query": query[:220]},
        summary="Préparer une recherche web via le moteur allowlisté du worker desktop.",
        confidence=0.8,
    )


def _propose_mail_preview(raw: str, normalized: str) -> ActionProposal | None:
    # Pluriels FR/EN + synonymes (inbox / courrier / boîte) — sinon AGIR échoue.
    if not re.search(
        r"\b(mails?|e-?mails?|courriels?|courriers?|inbox|imap|bo[iî]te(?:\s+mail)?)\b",
        normalized,
    ):
        return None
    sender = _extract_mail_filter(raw)
    action: dict[str, object] = {
        "kind": "mail_imap_preview",
        "max_messages": 3,
        "max_body_chars": 800,
        "max_scan": 200,
    }
    if sender:
        action["from_contains"] = sender[:80]
    else:
        # Aperçu INBOX récent : le worker exigeait un filtre — mode recent_ok
        # (max_messages borné) sans from/subject.
        action["recent"] = True
    return _desktop_proposal(
        action=action,
        summary="Préparer un aperçu IMAP INBOX en lecture seule, borné et filtré.",
        confidence=0.78 if sender else 0.72,
    )


def _propose_morning_brief(raw: str, normalized: str) -> ActionProposal | None:
    del raw
    if not re.search(
        r"\b("
        r"brief\s+(?:du\s+)?matin(?:al)?|briefing\s+(?:du\s+)?matin|"
        r"point\s+(?:du\s+)?matin|r[eé]sum[eé]\s+matinal|"
        r"jarvis|fais\s+mon\s+brief"
        r")\b",
        normalized,
    ):
        return None
    cap = capability_registry.get("morning_brief")
    assert cap is not None
    return ActionProposal(
        capability=cap.name,
        routed_to=cap.routed_to,
        action_context_key=cap.action_context_key or "",
        action={"kind": "morning_brief"},
        context_patch={},
        summary="Compiler le brief matinal studio (Self / proactive / infra, lecture seule).",
        risk_level=cap.risk_level,
        confidence=0.88,
        requires_review=False,
    )


def _propose_memory_recall(raw: str, normalized: str) -> ActionProposal | None:
    """Mémoire agent / leçons / conscience — jamais sonde RAM VM."""
    del raw
    # Exclure clairement la supervision mémoire machine
    if re.search(
        r"\b(ram|swap|vm\s+m[eé]moire|m[eé]moire\s+vm|m[eé]moire\s+(?:des\s+)?h[oô]tes?|"
        r"sonde\s+(?:la\s+)?m[eé]moire|free\s+-|consommation\s+(?:ram|m[eé]moire))\b",
        normalized,
    ):
        return None
    if not re.search(
        r"\b("
        r"(?:ta|ma|sa|notre)\s+m[eé]moire|"
        r"m[eé]moire\s+(?:agent|self|studio|conversation|leçons?|lessons)|"
        r"ce\s+que\s+tu\s+(?:retiens|sais|connais|as\s+appris)|"
        r"leçons?\s+apprises|lessons[_\s-]?learned|"
        r"rappelle[- ]?moi\s+(?:ta\s+)?m[eé]moire|"
        r"montre\s+(?:moi\s+)?(?:ta\s+)?m[eé]moire|"
        r"synth[eè]se\s+(?:de\s+)?(?:ta\s+)?m[eé]moire|"
        r"conscience\s+(?:de\s+l['\u2019])?(?:écosystème|ecosysteme|self)|"
        r"renforce(?:r)?\s+(?:ta\s+)?m[eé]moire"
        r")\b",
        normalized,
    ):
        return None
    cap = capability_registry.get("memory_recall")
    assert cap is not None
    return ActionProposal(
        capability=cap.name,
        routed_to=cap.routed_to,
        action_context_key=cap.action_context_key or "",
        action={"kind": "memory_recall"},
        context_patch={},
        summary="Synthèse mémoire agent (Self + leçons) — lecture seule, pas de sonde VM.",
        risk_level=cap.risk_level,
        confidence=0.9,
        requires_review=False,
    )


def _mmo_session_bridge_active(context: dict[str, object]) -> bool:
    """Pont volontaire MMO : exige un résumé non vide et une trace explicite côté client."""
    raw_ss = context.get("session_summary")
    if not isinstance(raw_ss, dict) or not raw_ss:
        return False
    bridge = context.get("mmo_bridge")
    if not isinstance(bridge, dict):
        return False
    return str(bridge.get("source") or "").strip() == "mmo_session_summary"


def _session_summary_prompt_fragment(context: dict[str, object]) -> str:
    raw_ss = context.get("session_summary")
    if not isinstance(raw_ss, dict):
        return ""
    parts: list[str] = []
    for key in ("tracked_quest", "last_npc", "player_note", "session_mood", "quest_snapshot", "memory_hint"):
        val = raw_ss.get(key)
        if isinstance(val, str) and val.strip():
            parts.append(f"{key}: {val.strip()[:400]}")
    out = "\n".join(parts)
    return out[:1200]


def _qa_failure_prompt_fragment(context: dict[str, object]) -> str:
    raw = context.get("qa_failure_summary")
    if not isinstance(raw, dict):
        return ""
    parts: list[str] = []
    for key in ("kind", "smoke_ok", "smoke_exit_code", "failed_health_urls"):
        val = raw.get(key)
        if val is not None and val != "" and val != []:
            parts.append(f"{key}: {val}")
    return "\n".join(parts)[:800]


def _propose_team_dev_game_forge(raw: str, normalized: str, context: dict[str, object]) -> ActionProposal | None:
    """
    Forge OpenGame pour le rôle équipe dev_game (QA followup ou focus explicite).
    Dry-run obligatoire via context_patch ; pas de merge automatique.
    """
    if not (context.get("dev_game_focus") or context.get("_qa_followup")):
        return None
    if not re.search(
        r"\b(forge|forger|prototype|sandbox|opengame|correctif|bug|gameplay|investig|smoke|patch)\b"
        r'|\bplan\b.*\b(mmo|monde|jeu)\b',
        normalized,
    ):
        return None
    cap = capability_registry.get("prototype_game")
    assert cap is not None
    prompt_parts = [
        "Prototype sandbox équipe dev_game (hors tronc MMO / sandbox mmmorpg gelé ADR 0005).",
        _session_summary_prompt_fragment(context),
        _qa_failure_prompt_fragment(context),
        f"Objectif équipe : {raw.strip()[:700]}",
    ]
    prompt = "\n\n".join(p for p in prompt_parts if p).strip()[:2000]
    project = "team_dev_game"
    if context.get("_qa_followup"):
        project = "team_qa_followup_forge"
    action: dict[str, object] = {
        "kind": "generate_prototype",
        "project_name": project,
        "prompt": prompt,
    }
    trace: dict[str, object] = {"origin": "team_dev_game"}
    if context.get("_qa_followup"):
        trace["qa_followup"] = True
    parent = context.get("parent_task_id")
    if isinstance(parent, str) and parent.strip():
        trace["parent_task_id"] = parent.strip()
    return ActionProposal(
        capability=cap.name,
        routed_to=cap.routed_to,
        action_context_key=cap.action_context_key or "opengame_action",
        action=action,
        context_patch={
            "opengame_action": action,
            "opengame_dry_run": True,
        },
        summary=(
            "Proposition forge OpenGame (dry-run) pour dev_game — revue humaine avant exécution réelle."
        ),
        risk_level=cap.risk_level,
        confidence=0.68,
        source="team_dev_game",
        mmo_trace=trace,
    )


def _propose_mmo_dev_plan(raw: str, normalized: str, context: dict[str, object]) -> ActionProposal | None:
    """
    Proposition de forge OpenGame en dry-run, motivée par une session MMO importée volontairement.
    Pas d'exécution réelle ni merge : le contexte force opengame_dry_run jusqu'au choix utilisateur.
    """
    if not _mmo_session_bridge_active(context):
        return None
    if not re.search(
        r"\b(forge|forger|prototype|opengame|sandbox|évolution|evolution|patch)\b"
        r'|\bplan\b.*\b(mmo|monde|jeu)\b|\b(idée|idee)\b.*\bmmo\b',
        normalized,
    ):
        return None
    cap = capability_registry.get("prototype_game")
    assert cap is not None
    prompt = (
        "Prototype sandbox (hors tronc MMO canon), à planifier sans merge automatique.\n\n"
        f"{_session_summary_prompt_fragment(context)}\n\n"
        f"Demande utilisateur : {raw.strip()[:700]}"
    )
    action: dict[str, object] = {
        "kind": "generate_prototype",
        "project_name": "mmo_bridge_idea",
        "prompt": prompt,
    }
    bridge = context.get("mmo_bridge") if isinstance(context.get("mmo_bridge"), dict) else {}
    trace = {
        "origin": "session_summary",
        "bridge_source": "mmo_session_summary",
        "imported_at": bridge.get("imported_at"),
        "session_summary_keys": sorted(
            k for k in (context.get("session_summary") or {}).keys() if isinstance(k, str)
        ),
    }
    return ActionProposal(
        capability=cap.name,
        routed_to=cap.routed_to,
        action_context_key=cap.action_context_key or "opengame_action",
        action=action,
        context_patch={
            "opengame_action": action,
            "opengame_dry_run": True,
        },
        summary="Préparer une génération OpenGame en sandbox (dry-run), à partir d'un résumé MMO importé volontairement — pas de merge automatique.",
        risk_level=cap.risk_level,
        confidence=0.71,
        source="mmo_session_bridge",
        mmo_trace=trace,
    )


_OPEN_APP_VERB_RE = re.compile(
    r"\b(?:ouvrir|ouvre|ouvrez|lancer|lance|lancez|demarrer|démarrer|demarrez|démarrez|start|launch|open)\b",
    re.IGNORECASE,
)


def _extract_http_url(text: str) -> str | None:
    m = re.search(r"https?://[^\s\"'<>\]\)]+", text or "", flags=re.IGNORECASE)
    if not m:
        return None
    return m.group(0).rstrip(".,);]")


def _propose_open_url(raw: str, normalized: str) -> ActionProposal | None:
    """Ouvre une URL via le navigateur **par défaut** (open_url), pas Firefox forcé."""
    url = _extract_http_url(raw)
    if not url:
        return None
    if not re.search(
        r"\b(ouvre|ouvrir|lance|lancer|navigateur|browser|url|onglet|page|lien|"
        r"firefox|chrome|edge|brave|msedge)\b",
        normalized,
    ):
        return None
    # Forcer une app précise : « ouvre dans firefox » → open_app (sinon défaut)
    if re.search(r"\b(avec|dans|via)\s+(firefox|chrome|msedge|edge|brave)\b", normalized):
        if not re.search(r"\bnavigateur\s+par\s+d[eé]faut\b", normalized):
            return None
    host = url.split("//", 1)[-1].split("/", 1)[0]
    path = ""
    if "#" in url:
        # Garder le slash avant le hash : « host/#/jobs » (pas « host#/jobs »)
        frag = url.split("#", 1)[1][:48]
        path = "/#" + frag
    elif "/" in url.split("//", 1)[-1]:
        path = "/" + url.split("//", 1)[-1].split("/", 1)[1][:48]
    label = f"{host}{path}" if path else host
    if "jobs" in url.lower():
        tip = "Jobs L2 / approbations"
    elif "cockpit" in url.lower():
        tip = "mur infra Cockpit"
    elif ":5174" in url:
        tip = "Compagnon Orch"
    else:
        tip = "navigateur par défaut — pas Firefox forcé"
    return _desktop_proposal(
        action={"kind": "open_url", "url": url},
        summary=f"Ouvrir « {label} » ({tip}).",
        confidence=0.88,
        text=raw,
    )


def _propose_useful_default(normalized: str) -> ActionProposal | None:
    """Demande vague « propose une action utile » → selfcheck LAN (safe, concrète)."""
    if not re.search(
        r"\b(propose|suggestion|suggestions|agir|utile|utiles|que\s+faire|quoi\s+faire|"
        r"autre\s+action|actions?\s+utiles?|que\s+peux[- ]?tu\s+faire)\b",
        normalized,
    ):
        return None
    cap = capability_registry.get("devops_probe")
    assert cap is not None
    return ActionProposal(
        capability=cap.name,
        routed_to=cap.routed_to,
        action_context_key=cap.action_context_key or "devops_action",
        action={"kind": "selfcheck"},
        context_patch={"devops_action": {"kind": "selfcheck"}},
        summary=(
            "Selfcheck LAN read-only (action utile par défaut). "
            "Autres pistes via Ctrl+K : mails, inventaire réseau, VGHD, Jobs L2, Cockpit."
        ),
        risk_level=cap.risk_level,
        confidence=0.7,
    )


def _propose_default_browser(raw: str, normalized: str) -> ActionProposal | None:
    """Lecture seule : quel est le navigateur HTTP par défaut sur Windows."""
    if not re.search(
        r"\b(navigateur\s+par\s+d[eé]faut|default\s+browser|quel\s+navigateur|"
        r"navigateur\s+par\s+defaut|browser\s+par\s+d[eé]faut)\b",
        normalized,
    ):
        return None
    return _desktop_proposal(
        action={"kind": "default_browser_info"},
        summary="Lire le navigateur HTTP par défaut du poste (lecture seule, utile avant d’ouvrir une URL).",
        confidence=0.9,
        text=raw,
    )


def _propose_repair_app_deps(raw: str, normalized: str) -> ActionProposal | None:
    """Réparation deps locales (VGHD Qt5Sql) via worker desktop."""
    action = repair_app_deps_action_from_goal(raw)
    if action is None:
        return None
    app_label = action.get("app", "vghd")
    return _desktop_proposal(
        action=action,
        summary=f"Réparer les dépendances de « {app_label} » sur le poste (Qt5Sql / sidecars).",
        confidence=0.9,
        text=raw,
    )


def _propose_open_app(raw: str, normalized: str) -> ActionProposal | None:
    """
    Ouverture / lancement d'une application locale (``kind``: ``open_app`` côté worker).
    """
    if not _OPEN_APP_VERB_RE.search(normalized):
        return None
    matches = list(_OPEN_APP_VERB_RE.finditer(raw))
    if not matches:
        return None
    last_match = matches[-1]
    tail = raw[last_match.end() :].strip()
    if not tail:
        return None
    tail = re.sub(
        r"^\s*(?:l['′'])?\s*(?:application|appli|prog|programme)\s+",
        "",
        tail,
        flags=re.IGNORECASE,
    ).strip()
    tail_chunk = re.split(r"\s+(?:sur|on|avec|pour|dans)\s+", tail, maxsplit=1)[0].strip()
    slug = sanitize_desktop_app_slug(tail_chunk)
    if not slug:
        return None
    # Enrichissement rapatrié de P03 : alias (notepad→notepadpp, swg→swgemu…),
    # chemin .exe fourni dans l'objectif, et learn:true par défaut (allowlist auto sur le worker).
    action: dict[str, object] = {"kind": "open_app", "app": slug, "args": []}
    exe = extract_exe_path_from_goal(raw)
    if exe:
        action["command"] = exe
    action = enrich_open_app_action(action)
    app_label = action.get("app", slug)
    target = infer_desktop_target_from_text(raw)
    summary = f"Préparer l'ouverture de « {app_label} » via desktop_control (dry-run jusqu'à exécution)."
    if target == "ad":
        summary = f"Préparer l'ouverture de « {app_label} » sur le serveur AD (desktop_control, dry-run)."
    return _desktop_proposal(
        action=action,
        summary=summary,
        confidence=0.84,
        text=raw,
    )


def _propose_job_synthesis(normalized: str) -> ActionProposal | None:
    """Synthèse NL après une étape technique (ex. selfcheck) — le job injecte les résultats précédents."""
    if not re.search(
        r"\b(dis[- ]?moi|dire|explique|résume|resume|synthèse|synthese|amélior|amelior|recommand|liste|présente|presente)\b",
        normalized,
    ):
        return None
    if not re.search(
        r"\b(ce\s+qui|quoi|comment|pistes|suggestions|résultat|resultat|checkup|selfcheck|étapes?|infra|devops|"
        r"état|etat|l['\u2019]état|l['\u2019]etat)\b",
        normalized,
    ):
        return None
    cap = capability_registry.get("npc_dialogue")
    assert cap is not None
    return ActionProposal(
        capability=cap.name,
        routed_to=cap.routed_to,
        action_context_key=cap.action_context_key or "",
        action={},
        context_patch={"_job_synthesis": True},
        summary="Synthèse en français à partir des résultats des étapes précédentes du job.",
        risk_level=cap.risk_level,
        confidence=0.8,
    )


_AGENT_MEMORY_INTENT_RE = re.compile(
    r"\b(ta|ma|sa|notre)\s+(mémoire|memoire)\b|"
    r"\b(mémoire|memoire)\s+(agent|self|équipe|equipe|studio|conversation|leçons?|lessons)\b|"
    r"\b(conscience|écosystème|ecosysteme)\b|"
    r"\b(incarner|incarnation|t['\u2019]incarner)\b|"
    r"\b(self[\s_-]?state|leçons?\s+apprises|lessons[_\s-]?learned)\b",
    re.IGNORECASE,
)


def _is_agent_memory_intent(normalized: str) -> bool:
    """Mémoire agent / Self / conscience — pas RAM VM."""
    return bool(_AGENT_MEMORY_INTENT_RE.search(normalized or ""))


def _propose_vm_memory_probe(normalized: str) -> ActionProposal | None:
    if _is_agent_memory_intent(normalized):
        return None
    if not re.search(r"\b(mémoire|memoire|memory|ram|swap|consommation)\b", normalized):
        return None
    # Exige signal VM/hôte/ops — pas « analyser ta mémoire » seul.
    if not re.search(
        r"\b(vm|hôte|hote|serveur|prime|246|245|110|140|ssh|"
        r"supervis|surveill|contrôl|control|sond|fuites?|libér|liber|"
        r"swap|ram)\b",
        normalized,
    ):
        return None
    if not re.search(
        r"\b(supervis|surveill|contrôl|control|sond|analys|audit|compare|état|etat|"
        r"fuites?|libér|liber|charge|chargement|vm|hôte|hote|serveur|prime|"
        r"246|245|110|140)\b",
        normalized,
    ):
        return None
    cap = capability_registry.get("devops_probe")
    assert cap is not None
    return ActionProposal(
        capability=cap.name,
        routed_to=cap.routed_to,
        action_context_key=cap.action_context_key or "devops_action",
        action={"kind": "vm_memory_probe"},
        context_patch={"devops_action": {"kind": "vm_memory_probe"}},
        summary="Sonde mémoire read-only (SSH) sur Prime 246, PreCU 245, front 110, core 140.",
        risk_level=cap.risk_level,
        confidence=0.84,
    )


def _propose_proxmox_status(normalized: str) -> ActionProposal | None:
    if not re.search(r"\b(proxmox|hyperviseur|hypervisor|pve)\b", normalized):
        return None
    if not re.search(
        r"\b(état|etat|status|supervis|surveill|vm|cluster|ressources?|charge)\b",
        normalized,
    ):
        return None
    cap = capability_registry.get("devops_probe")
    assert cap is not None
    return ActionProposal(
        capability=cap.name,
        routed_to=cap.routed_to,
        action_context_key=cap.action_context_key or "devops_action",
        action={"kind": "proxmox_status"},
        context_patch={"devops_action": {"kind": "proxmox_status"}},
        summary="Sonde Proxmox read-only (cluster, VMs LAN core/front/precu/prime).",
        risk_level=cap.risk_level,
        confidence=0.83,
    )


def _propose_infra_selfcheck(normalized: str) -> ActionProposal | None:
    # « résume l'état » etc. → synthèse dialogue, pas un second selfcheck.
    if re.search(r"\b(résume|resume|synthèse|synthese|explique|dis[- ]?moi)\b", normalized):
        return None
    # Formulations courantes « auto checkup / bilan » (sans mot « devops » explicite).
    if re.search(
        r"\b(auto[-\s]?check[-\s]?up|check[-\s]?up|checkup|bilan\s+(?:de\s+)?santé|bilan\s+sante)\b",
        normalized,
    ):
        cap = capability_registry.get("devops_probe")
        assert cap is not None
        return ActionProposal(
            capability=cap.name,
            routed_to=cap.routed_to,
            action_context_key=cap.action_context_key or "devops_action",
            action={"kind": "selfcheck"},
            context_patch={"devops_action": {"kind": "selfcheck"}},
            summary="Préparer un selfcheck DevOps read-only (formulation checkup/bilan).",
            risk_level=cap.risk_level,
            confidence=0.82,
        )
    # « le réseau / LAN a l'air bizarre → vérifier » (initiative ops sans jargon).
    if re.search(r"\b(r[eé]seau|lan|infra|sondes?)\b", normalized) and re.search(
        r"\b(v[eé]rif(?:ie|ier)|check|bizarre|probl[eè]me|souci|suspect|down|ko|tombe)\b",
        normalized,
    ):
        cap = capability_registry.get("devops_probe")
        assert cap is not None
        return ActionProposal(
            capability=cap.name,
            routed_to=cap.routed_to,
            action_context_key=cap.action_context_key or "devops_action",
            action={"kind": "selfcheck"},
            context_patch={"devops_action": {"kind": "selfcheck"}},
            summary="Préparer un selfcheck LAN read-only (signal réseau / infra).",
            risk_level=cap.risk_level,
            confidence=0.74,
        )
    if not re.search(r"\b(selfcheck|devops|infra|healthz|santé|sante|état|etat|status|statut|backend|orchestrateur)\b", normalized):
        return None
    if not re.search(r"\b(vérifie|verifie|check|sonde|diagnostic|état|etat|status|statut|santé|sante|healthz|selfcheck)\b", normalized):
        return None
    cap = capability_registry.get("devops_probe")
    assert cap is not None
    return ActionProposal(
        capability=cap.name,
        routed_to=cap.routed_to,
        action_context_key=cap.action_context_key or "devops_action",
        action={"kind": "selfcheck"},
        context_patch={"devops_action": {"kind": "selfcheck"}},
        summary="Préparer un selfcheck DevOps read-only sur les sondes allowlistées.",
        risk_level=cap.risk_level,
        confidence=0.76,
    )


def _desktop_proposal(
    *,
    action: dict[str, object],
    summary: str,
    confidence: float,
    text: str = "",
) -> ActionProposal:
    cap = capability_registry.get("desktop_control")
    assert cap is not None
    patch: dict[str, object] = {"desktop_action": action, "desktop_dry_run": True}
    target = infer_desktop_target_from_text(text)
    if target:
        patch["desktop_target"] = target
    kind = str(action.get("kind") or "").strip()
    soft = kind in _SOFT_DESKTOP_KINDS
    return ActionProposal(
        capability=cap.name,
        routed_to=cap.routed_to,
        action_context_key=cap.action_context_key or "desktop_action",
        action=action,
        context_patch=patch,
        summary=summary,
        risk_level="low" if soft else cap.risk_level,
        requires_review=not soft,
        confidence=confidence,
    )


def _normalize(value: str) -> str:
    return value.strip().lower()


def _extract_after(raw: str, markers: tuple[str, ...]) -> str:
    lower = raw.lower()
    best: tuple[int, int, str] | None = None
    for marker in sorted(markers, key=len, reverse=True):
        idx = lower.find(marker.lower())
        if idx < 0:
            continue
        end = idx + len(marker)
        if best is None or idx < best[0] or (idx == best[0] and end > best[1]):
            best = (idx, end, marker)
    if best is None:
        return ""
    return raw[best[1] :].strip(" :,-\"'")


def _extract_mail_filter(raw: str) -> str:
    patterns = (
        r"\b(?:de|from)\s+[\"']?([^\"',.;!?]+)",
        r"\b(?:mail|email|e-mail|courriel)\s+(?:de|from)\s+[\"']?([^\"',.;!?]+)",
    )
    for pattern in patterns:
        m = re.search(pattern, raw, flags=re.IGNORECASE)
        if m:
            value = m.group(1).strip()
            value = re.sub(r"\b(et|qui|avec|contenant|sujet)\b.*$", "", value, flags=re.IGNORECASE).strip()
            if value:
                return value
    quoted = re.search(r"[\"']([^\"']{2,80})[\"']", raw)
    if quoted:
        return quoted.group(1).strip()
    return ""
