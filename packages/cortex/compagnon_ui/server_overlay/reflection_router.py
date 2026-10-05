"""
P1 — Réflexion légère avant dispatch.

Décide : answer | team | audit | ask_user
1) Heuristiques rapides (gratuites)
2) Si ambigu → Ollama light `.111` (qwen2.5:3b), fallback Groq
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Literal

import httpx

from src.http_timeouts import httpx_timeout
from src.services.lan_llm_grounding import wants_factual_lan_answer, wants_lan_llm_context
from src.services.multi_block_dispatch import is_numbered_multi_block
from src.services.team_routing import strip_team_prefix
from src.settings import Settings

try:
    from src.services.chat_intent import (
        is_companion_chat,
        wants_broad_audit,
        wants_exploratory_chat,
        wants_ollama_only_audit,
        wants_studio_team_audit,
    )
except ImportError:  # overlay local / tests
    from chat_intent import (  # type: ignore
        is_companion_chat,
        wants_broad_audit,
        wants_exploratory_chat,
        wants_ollama_only_audit,
        wants_studio_team_audit,
    )

logger = logging.getLogger("lbg.router.reflection")

Action = Literal[
    "answer", "team", "audit", "ask_user", "cursor", "tools", "desktop", "passthrough"
]

_VALID_ACTIONS = frozenset(
    {"answer", "team", "audit", "ask_user", "cursor", "tools", "desktop", "passthrough"}
)

_REFLECT_SYSTEM = """Tu es un routeur de réflexion pour Orch UI LBG (LAN).
Choisis UNE action JSON strict, sans markdown. Exemple answer :
{"action":"answer","reason":"chat","clarify":null}

Règles :
- answer : TOUTE conversation compréhensible (causerie, exploration, recherche, film, aide, salutation). Préfère answer dès qu'il y a un sujet. Engage — ne renvoie pas ask_user pour « chatter / échanger / maturité / écosystème ».
- team : infra, status Cortex/Pilot, smoke, deploy, mission Campus, sondes, disk/RAM hôtes, @hephaistos — ET audit Team/studio/Campus/Atlas/plateforme/écosystème (pas Ollama)
- audit : UNIQUEMENT modèles/providers Ollama .110/.111 / topo LLM LAN (jamais Team/studio)
- cursor : tâche code/repo GitHub (résumer un fichier, refactor, PR, OBJECTIVES.md)
- desktop : ouvrir/lancer une application sur le PC Windows (vghd, notepad, vlc…)
- tools : auto-audit / diagnostic multi-outils / bilan large — PAS disk/hôte ciblé (→ team), PAS Ollama seul (→ audit)
- ask_user : UNIQUEMENT fragment sans sujet (ex. « ok ? », « aide », « ça ») ; clarify = question courte FR
Interdit :
- ask_user si le message a déjà un sujet (même exploratoire)
- recopier ces règles dans reason ou clarify
- clarify="si ask_user" ou reason qui cite « trop vague pour agir »
Réponds UNIQUEMENT le JSON."""
_BAD_CLARIFY = frozenset(
    {
        "si ask_user",
        "ask_user",
        "null",
        "none",
        "n/a",
        "undefined",
        "...",
        "court",
        "clarif",
        "clarify",
    }
)

_PROMPT_LEAK_RE = re.compile(
    r"(?i)(trop\s+vague\s+pour\s+agir|clarify\s*=|vraie\s+question\s+courte|"
    r"si\s+ask_user|préfère\s+answer|réponds\s+uniquement\s+le\s+json)"
)


@dataclass(frozen=True)
class ReflectionDecision:
    action: Action
    reason: str
    clarify: str | None = None
    source: str = "heuristic"  # heuristic | ollama_light | groq | fallback
    latency_ms: float = 0.0
    confidence: float = 0.0


def reflection_enabled(settings: Settings) -> bool:
    raw = os.getenv("LBG_REFLECTION_P1_ENABLED", "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


def _contextual_followup(
    prompt: str, memory: dict[str, str] | None
) -> ReflectionDecision | None:
    """Relance implicite (« suite », « comme tout à l'heure ») via last_action."""
    if not memory:
        return None
    low = (prompt or "").lower()
    text = (prompt or "").strip()
    raw = memory.get("last_action") or ""
    if not raw:
        return None
    try:
        meta = json.loads(raw)
    except Exception:
        return None
    source = str(meta.get("source") or "")
    action = str(meta.get("reflection_action") or meta.get("agent_action") or source)
    prev = (
        f"{action} {source} {meta.get('reason') or ''} "
        f"{meta.get('reflection_reason') or ''} {meta.get('clarify') or ''}"
    ).lower()

    # Relance périmètre après clarif audit (« la partie Team, studio ») — sans cue « suite »
    if len(text) < 90 and re.search(r"(?i)\b(team|studio|campus|atlas|plateforme)\b", text):
        if any(
            k in prev
            for k in ("audit", "ask_user", "clarif", "périmètre", "perimetre", "chatter", "vague")
        ):
            return ReflectionDecision(
                "team",
                "suite périmètre audit → Team/studio (mémoire)",
                None,
                "heuristic",
                0.0,
                0.88,
            )

    cues = (
        "suite",
        "comme avant",
        "tout à l'heure",
        "on venait",
        "relance",
        "recommence",
        "encore",
        "tu te souviens",
        "retrouv",
        "l'id",
        "l id",
        "task id",
        "mission id",
    )
    if not any(c in low for c in cues):
        return None
    mapping = {
        "tools": ("tools", "suite diagnostic (mémoire)"),
        "tool_loop": ("tools", "suite diagnostic (mémoire)"),
        "team": ("team", "suite Team (mémoire)"),
        "campus-mission": ("passthrough", "rappel mission Campus (mémoire)"),
        "campus-status": ("team", "suite status Campus (mémoire)"),
        "audit": ("audit", "suite audit LAN (mémoire)"),
        "cursor": ("cursor", "suite Cursor (mémoire)"),
        "desktop": ("desktop", "suite desktop (mémoire)"),
    }
    model = str(meta.get("model") or "")
    if model in mapping:
        act, reason = mapping[model]
        return ReflectionDecision(act, reason, None, "heuristic", 0.0, 0.82)
    for key, (act, reason) in mapping.items():
        if action == key or source == key:
            return ReflectionDecision(act, reason, None, "heuristic", 0.0, 0.78)
    return None


def _heuristic(prompt: str) -> ReflectionDecision | None:
    """Décision certaine sans LLM. ``None`` = ambigu → LLM light."""
    text = (prompt or "").strip()
    if not text:
        return ReflectionDecision("ask_user", "prompt vide", "Que veux-tu faire ?", "heuristic", 0.0, 1.0)

    # Multi-blocs : déjà géré en amont
    if is_numbered_multi_block(text):
        return ReflectionDecision("passthrough", "multi-bloc numéroté", None, "heuristic", 0.0, 1.0)

    stripped, forced_team = strip_team_prefix(text)

    from src.services.desktop_dispatch import wants_desktop_open

    # Desktop avant team forcé : « team: ouvre vghd… » (sélecteur Agent=Team) → open_app
    if wants_desktop_open(stripped if forced_team else text):
        return ReflectionDecision("desktop", "ouvrir app sur le poste Windows", None, "heuristic", 0.0, 0.95)

    # Préfixe team: forcé par UI (sélecteur Agent=Team) — ne pas piéger le chat identité
    if forced_team and stripped:
        if is_companion_chat(stripped):
            return ReflectionDecision(
                "answer",
                "préfixe team UI + chat identité → answer",
                None,
                "heuristic",
                0.0,
                0.92,
            )
        return ReflectionDecision("team", "préfixe team:/mission:/campus:", None, "heuristic", 0.0, 1.0)

    # Identité / causerie Compagnon (avant infra / tools / LLM light)
    if is_companion_chat(text):
        return ReflectionDecision("answer", "chat identité / causerie", None, "heuristic", 0.0, 0.93)

    # Audit Team/studio AVANT verbes conversationnels (« tu pourrais faire un audit… »)
    if wants_studio_team_audit(text):
        return ReflectionDecision("team", "audit Team/studio", None, "heuristic", 0.0, 0.92)

    if wants_broad_audit(text):
        return ReflectionDecision("tools", "auto-audit / bilan large", None, "heuristic", 0.0, 0.9)

    if wants_ollama_only_audit(text):
        return ReflectionDecision("audit", "audit Ollama / LLM LAN", None, "heuristic", 0.0, 0.92)

    from src.services.cursor_agent_client import strip_cursor_prefix

    cursor_text, forced_cursor = strip_cursor_prefix(text)
    if forced_cursor and cursor_text:
        return ReflectionDecision("cursor", "préfixe cursor:", None, "heuristic", 0.0, 1.0)

    if wants_factual_lan_answer(text):
        return ReflectionDecision("audit", "question factuelle LAN LLM", None, "heuristic", 0.0, 0.95)

    # Disk/RAM hôtes / Proxmox / Prime → Team Héphaïstos (avant tools + chat générique)
    from src.services.team_proxy import wants_infra_lan_brief

    if wants_infra_lan_brief(text):
        return ReflectionDecision(
            "team",
            "Infra LAN disk/RAM / Héphaïstos",
            None,
            "heuristic",
            0.0,
            0.95,
        )

    from src.services.tool_loop import tool_loop_enabled, wants_tool_loop

    if tool_loop_enabled() and wants_tool_loop(text):
        return ReflectionDecision("tools", "diagnostic multi-outils", None, "heuristic", 0.0, 0.9)

    low = text.lower()

    from src.services.cockpit_overview import wants_cockpit_overview

    if wants_cockpit_overview(text):
        return ReflectionDecision("passthrough", "survol cockpit Orch UI", None, "heuristic", 0.0, 0.95)

    from src.services.team_autonomy_plan import wants_team_autonomy_plan

    if wants_team_autonomy_plan(text):
        return ReflectionDecision("passthrough", "plan autonomie Team", None, "heuristic", 0.0, 0.95)

    # Fragments UI copiés (lanMission —, prodDiagnostic —) : demander la ligne complète
    if re.match(r"(?i)^(lan|prod|local)\s*\w*[\s—-]*$", text.strip()) or re.match(
        r"(?i)^(corriger|diagnostic|mission)\s",
        text.strip(),
    ) and len(text) < 40:
        return ReflectionDecision(
            "ask_user",
            "fragment suggestion UI",
            "Recolle la ligne complète entre backticks (ex. `team: status …` ou `fais un diagnostic complet LAN`).",
            "heuristic",
            0.0,
            0.9,
        )

    cursorish = (
        "objectives.md",
        "lbg_studios",
        "refactor",
        "pull request",
        "ouvre une pr",
        "ouvre un pr",
        "github.com/teome0245",
        "monorepo",
        "corrige le bug",
        "dans le repo",
    )
    if any(t in low for t in cursorish):
        return ReflectionDecision("cursor", "termes code/repo Cursor", None, "heuristic", 0.0, 0.85)

    # Confirmations Orch UI / salutations courtes (sans survol / upgrade produit)
    if (
        re.search(
            r"(?i)\b(bonjour|salut|hello|ça va|ca va|fait\s+pas\s+cette\s+tête|"
            r"(?:ça|ca)\s+va\s+aller|t['\u2019]?inqui[èe]te)\b",
            text,
        )
        and len(text) < 90
        and not wants_cockpit_overview(text)
        and not re.search(r"(?i)\b(upgrade|survol|capacit|fonction|cockpit|team|statut|compte)\b", text)
    ):
        return ReflectionDecision("answer", "salutation", None, "heuristic", 0.0, 0.9)

    # Chat / recherche / demande claire (sujet + verbe) → answer, pas ask_user LLM
    # Ne vole pas audit / Team (déjà traités plus haut)
    if (
        len(text) >= 16
        and re.search(
            r"(?i)\b(cherche|trouver|télécharg|telecharg|film|série|serie|torrent|"
            r"explique|comment|pourquoi|aide[- ]?moi|peux[- ]?tu|pourrais|"
            r"dis[- ]?moi|parle[- ]?moi|raconte|montre|liste|résume|resume|"
            r"quoi|où|ou|quand|qui\s+es|chatter|[ée]changer|discut|confondre|"
            r"maturité|maturite|[ée]cosyst[èe]me|mmorpg)\b",
            text,
        )
        and not wants_infra_lan_brief(text)
        and not wants_broad_audit(text)
        and not wants_studio_team_audit(text)
        and not wants_ollama_only_audit(text)
    ):
        reason = (
            "causerie exploratoire"
            if wants_exploratory_chat(text)
            else "demande conversationnelle claire"
        )
        return ReflectionDecision("answer", reason, None, "heuristic", 0.0, 0.86)

    if re.search(r"(?i)(confirme|réponds?\s+depuis|orch\s*ui|ct100)", text) and not wants_lan_llm_context(text):
        if not any(t in low for t in ("status", "smoke", "deploy", "sondes", "health")):
            return ReflectionDecision("answer", "confirmation Orch UI / chat", None, "heuristic", 0.0, 0.85)

    teamish = (
        "status orchestrateur",
        "status cortex",
        "status pilot",
        "smoke",
        "selfcheck",
        "deploy",
        "déploy",
        "spawn",
        "mission",
        "mission campus",
        "campus mission",
        "status campus",
        "campus status",
        "sondes",
        "healthz",
        "argus",
        "proxmox",
        "devops",
        "compte rendu",
        "actions en cours",
        "état de la team",
        "etat de la team",
        "statut de la team",
        "statut team",
        "de la team",
        "de l'équipe",
        "de l'equipe",
        "équipe virtuelle",
        "equipe virtuelle",
    )
    # « campus » nu / « c'est quoi le campus » = explication (answer), pas Team live
    if re.search(
        r"(?i)\b("
        r"c['\u2019]?est\s+quoi|qu['\u2019]?est[- ]ce\s+que|défini[rst]?|explique|"
        r"pour\s+toi|ton\s+avis|pense[- ]?tu"
        r")\b",
        text,
    ) and re.search(r"(?i)\b(campus|compagnon|lyra|team|écosyst[èe]me|ecosysteme)\b", text):
        return ReflectionDecision(
            "answer", "question conceptuelle studio → answer", None, "heuristic", 0.0, 0.9
        )
    if any(t in low for t in teamish):
        return ReflectionDecision("team", "termes infra/Team", None, "heuristic", 0.0, 0.85)
    # campus + ops (status/mission/spawn) seulement
    if re.search(r"(?i)\bcampus\b", low) and re.search(
        r"(?i)\b(status|statut|mission|spawn|jobs?|office|bureau|healthz|smoke)\b",
        low,
    ):
        return ReflectionDecision("team", "Campus ops → Team", None, "heuristic", 0.0, 0.88)
    # « Team » + question de statut (sans les mots ci-dessus)
    if re.search(r"(?i)\b(team|équipe|equipe)\b", low) and re.search(
        r"(?i)\b(status|statut|état|etat|en\s+cours|rapport|compte|tâches|taches|actions?)\b",
        low,
    ):
        return ReflectionDecision("team", "Team + statut", None, "heuristic", 0.0, 0.9)

    if wants_lan_llm_context(text) and not wants_studio_team_audit(text):
        return ReflectionDecision("audit", "contexte LAN LLM", None, "heuristic", 0.0, 0.8)

    from src.services.campus_recall import wants_campus_recall

    if wants_campus_recall(text):
        return ReflectionDecision("passthrough", "rappel ID mission/tâche Campus", None, "heuristic", 0.0, 0.92)

    # Trop vague (sauf identité courte déjà traitée plus haut)
    vague = re.fullmatch(
        r"(?i)\s*(ça\s*marche\s*\??|ok\s*\??|test\s*\??|aide\s*\??|help\s*\??|fais\s+quelque\s+chose\.?)\s*",
        text,
    )
    if vague or (len(text) < 12 and "?" in text and not is_companion_chat(text)):
        return ReflectionDecision(
            "ask_user",
            "demande trop vague",
            "Tu veux un status Team Cortex, un audit Ollama (.110/.111), ou juste chatter ?",
            "heuristic",
            0.0,
            0.8,
        )

    # Ambigu → LLM
    return None


def _parse_llm_json(raw: str) -> ReflectionDecision | None:
    s = (raw or "").strip()
    if not s:
        return None
    # Extraire premier objet JSON
    m = re.search(r"\{[^{}]*\}", s, re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except Exception:
        return None
    action = str(data.get("action") or "").strip().lower()
    if action not in _VALID_ACTIONS:
        return None
    if action == "passthrough":
        action = "answer"
    reason = str(data.get("reason") or "llm")[:200]
    # Fuite du prompt système dans reason/clarify → answer
    if _PROMPT_LEAK_RE.search(reason) or _PROMPT_LEAK_RE.search(str(data.get("clarify") or "")):
        return ReflectionDecision("answer", "prompt leak→answer", None, "llm", 0.0, 0.55)
    clarify_s = _clean_clarify(action, data.get("clarify"))
    # Placeholder / ask_user sans vraie question → answer
    if action == "ask_user" and clarify_s is None:
        raw_c = data.get("clarify")
        raw_s = str(raw_c).strip().lower() if raw_c is not None else ""
        if not raw_s or raw_s in _BAD_CLARIFY or "ask_user" in raw_s or _PROMPT_LEAK_RE.search(raw_s):
            return ReflectionDecision("answer", "ask_user sans clarify→answer", None, "llm", 0.0, 0.55)
    if action == "ask_user" and clarify_s and _PROMPT_LEAK_RE.search(clarify_s):
        return ReflectionDecision("answer", "clarify leak→answer", None, "llm", 0.0, 0.55)
    return ReflectionDecision(action, reason, clarify_s, "llm", 0.0, 0.7)  # type: ignore[arg-type]


def _clean_clarify(action: str, clarify: Any) -> str | None:
    if action != "ask_user":
        return None
    if clarify is None:
        return None
    s = str(clarify).strip()
    if not s:
        return None
    low = s.lower()
    if low in _BAD_CLARIFY:
        return None
    if "ask_user" in low and len(s) < 48:
        return None
    if _PROMPT_LEAK_RE.search(s):
        return None
    return s[:400]


async def _ollama_light_reflect(prompt: str, *, settings: Settings) -> ReflectionDecision | None:
    base = str(settings.probe_ollama_light_url or "").rstrip("/")
    if not base:
        return None
    model = os.getenv("LBG_REFLECTION_MODEL", "").strip() or "qwen2.5:3b"
    body = {
        "model": model,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.1, "num_predict": 120},
        "messages": [
            {"role": "system", "content": _REFLECT_SYSTEM},
            {"role": "user", "content": prompt[:1500]},
        ],
    }
    t0 = time.monotonic()
    try:
        # Cold-start qwen2.5:3b sur .111 peut dépasser 5–8 s
        timeout = httpx_timeout(read=max(min(float(settings.httpx_probe_read_s) * 4, 20.0), 15.0))
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(f"{base}/api/chat", json=body)
        r.raise_for_status()
        data = r.json()
        content = ""
        msg = data.get("message") if isinstance(data, dict) else None
        if isinstance(msg, dict):
            content = str(msg.get("content") or "")
        elif isinstance(data, dict):
            content = str(data.get("response") or "")
        decision = _parse_llm_json(content)
        if decision is None:
            return None
        ms = (time.monotonic() - t0) * 1000
        return ReflectionDecision(
            decision.action,
            decision.reason,
            decision.clarify,
            "ollama_light",
            ms,
            decision.confidence,
        )
    except Exception as e:
        logger.info("reflection ollama_light failed: %s", e)
        return None


async def _groq_reflect(prompt: str, *, settings: Settings) -> ReflectionDecision | None:
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        return None
    model = os.getenv("GROQ_MODEL_FAST", "").strip() or "llama-3.1-8b-instant"
    t0 = time.monotonic()
    try:
        timeout = httpx_timeout(read=min(float(settings.httpx_probe_read_s) * 2, 10.0))
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "model": model,
                    "temperature": 0.1,
                    "max_tokens": 120,
                    "messages": [
                        {"role": "system", "content": _REFLECT_SYSTEM},
                        {"role": "user", "content": prompt[:1500]},
                    ],
                },
            )
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        decision = _parse_llm_json(content)
        if decision is None:
            return None
        ms = (time.monotonic() - t0) * 1000
        return ReflectionDecision(
            decision.action,
            decision.reason,
            decision.clarify,
            "groq",
            ms,
            decision.confidence,
        )
    except Exception as e:
        logger.info("reflection groq failed: %s", e)
        return None


async def reflect_action(
    prompt: str,
    *,
    settings: Settings,
    memory: dict[str, str] | None = None,
) -> ReflectionDecision:
    """Point d'entrée P1."""
    if not reflection_enabled(settings):
        return ReflectionDecision("passthrough", "P1 désactivé", None, "fallback", 0.0, 1.0)

    ctx = _contextual_followup(prompt, memory)
    if ctx is not None:
        return ctx

    h = _heuristic(prompt)
    if h is not None:
        return h

    llm = await _ollama_light_reflect(prompt, settings=settings)
    if llm is not None:
        return llm

    groq = await _groq_reflect(prompt, settings=settings)
    if groq is not None:
        return groq

    # Dernier recours : laisser le pipeline existant
    return ReflectionDecision("passthrough", "réflexion indisponible", None, "fallback", 0.0, 0.3)


def decision_to_meta(d: ReflectionDecision) -> dict[str, Any]:
    return {
        "action": d.action,
        "reason": d.reason,
        "clarify": d.clarify,
        "source": d.source,
        "latency_ms": round(d.latency_ms, 1),
        "confidence": d.confidence,
    }
