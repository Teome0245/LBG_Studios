"""Voix conversationnelle LBG-IA — persona + mention légère de la compétence routée."""

from __future__ import annotations

import re
from typing import Any

FIRST_CONTACT_REPLY = (
    "Je suis **votre Compagnon** LBG Studios — présent pour dialoguer, concevoir, et "
    "**agir** sur le studio et l’infra sous votre validation (dry-run, approvals).\n\n"
    "Je délègue à l’équipe virtuelle quand il faut (PM, DevOps, code, assets), "
    "et je reste transparent sur ce que je peux exécuter seul.\n\n"
    "Tout est prêt : **quel est le premier objectif ?**"
)

_FIRST_TURN_BRIDGE = "Parfait, allons-y."

_GREETING_ONLY_RE = re.compile(
    r"^(?:"
    r"bonjour|salut|hello|hi|hey|coucou|bonsoir|"
    r"comment\s+(?:ça\s+)?va|ca\s+va|"
    r"qui\s+es-tu|qui\s+êtes-vous|presente\s+toi|présente\s+toi"
    r")[\s!.?,]*$",
    re.IGNORECASE,
)

# intent → (libellé humain, une ligne sur ce que fait la compétence)
SKILL_LABELS: dict[str, tuple[str, str]] = {
    "team_status": (
        "Équipe virtuelle",
        "lecture directe des tâches SQLite et du campus Lyra",
    ),
    "project_status": (
        "Point projet",
        "plan de route local + synthèse des tâches team",
    ),
    "infographiste_status": (
        "Infographiste / LoRA",
        "état réel du tri d'images et des entraînements",
    ),
    "godot_status": (
        "Godot & client Prime",
        "audits ZB-0 / ZB-1 / sidecar sans invention",
    ),
    "sprites_status": (
        "Sprites 2D",
        "suivi des assets Prime client",
    ),
    "infra_status": (
        "Infra & DevOps",
        "sondes healthz et services locaux",
    ),
    "devops_probe": (
        "Sonde DevOps",
        "diagnostic réseau / HTTP configuré",
    ),
    "project_pm": (
        "Chef de projet",
        "jalons, backlog et planification",
    ),
    "desktop_control": (
        "Poste de travail",
        "actions desktop allowlistées (dry-run par défaut)",
    ),
    "prototype_game": (
        "Forge prototype",
        "génération jeu sandbox isolée",
    ),
    "npc_dialogue": (
        "Dialogue",
        "réponse persona / LLM dialogue",
    ),
    "assistant_chat": (
        "Accueil",
        "premier contact et alignement",
    ),
    "unknown": (
        "Orientation",
        "aide au choix de la bonne compétence",
    ),
}


def is_first_turn(context: dict[str, Any] | None) -> bool:
    ctx = context if isinstance(context, dict) else {}
    if ctx.get("_lbg_ia_greeted") is True:
        return False
    if ctx.get("_skip_lbg_ia_voice") is True:
        return False
    history = ctx.get("history")
    if isinstance(history, list) and history:
        return False
    turns = ctx.get("conversation_turn")
    if isinstance(turns, int) and turns > 0:
        return False
    return True


def is_greeting_only(text: str) -> bool:
    t = (text or "").strip()
    if not t or len(t) > 80:
        return False
    return bool(_GREETING_ONLY_RE.match(t))


def skill_footer(*, intent: str, routed_to: str) -> str:
    label, hint = SKILL_LABELS.get(intent) or (
        intent.replace("_", " ").title() or "Système",
        f"routé via `{routed_to}`",
    )
    return f"_→ Compétence **{label}** · {hint}_"


def unknown_capability_reply(text: str) -> str:
    snippet = (text or "").strip()
    if len(snippet) > 120:
        snippet = snippet[:117] + "…"
    return (
        "Je n'ai pas encore trouvé de compétence exacte pour cette demande"
        + (f" (« {snippet} »)" if snippet else "")
        + ". Voici ce que je peux activer concrètement :\n\n"
        "- **Équipe** — compte rendu des actions en cours, mission campus, approbations L2\n"
        "- **Projet** — point d'avancement, plan de route, jalons\n"
        "- **Godot / Prime** — statut client, ZB-1, smokes\n"
        "- **Infographiste** — LoRA, tri d'images, Kohya\n"
        "- **Infra** — healthz, systemd, sonde DevOps\n"
        "- **Desktop** — ouvrir une app, notepad, recherche web (dry-run d'abord)\n\n"
        "Reformule en une phrase ce que tu veux accomplir, ou précise le domaine "
        "(ex. « compte rendu de la team », « où en est Godot ? »)."
    )


def wrap_operational_reply(
    body: str,
    *,
    intent: str,
    routed_to: str,
    text: str,
    context: dict[str, Any] | None = None,
    include_skill_footer: bool = True,
) -> str:
    """Enveloppe une réponse factuelle / opérationnelle avec la voix LBG-IA."""
    ctx = context if isinstance(context, dict) else {}
    core = (body or "").strip()
    if not core:
        return unknown_capability_reply(text)

    parts: list[str] = []
    first = is_first_turn(ctx)
    if first and is_greeting_only(text):
        return FIRST_CONTACT_REPLY

    if first and intent not in {"assistant_chat", "unknown"}:
        parts.append(_FIRST_TURN_BRIDGE)
        parts.append("")

    parts.append(core)

    if include_skill_footer and intent not in {"assistant_chat", "unknown", "npc_dialogue"}:
        parts.append("")
        parts.append(skill_footer(intent=intent, routed_to=routed_to))

    return "\n".join(parts)


def try_greeting_response(
    *,
    actor_id: str,
    text: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Premier tour + salutation pure → intro persona sans appeler un agent."""
    ctx = context if isinstance(context, dict) else {}
    if ctx.get("_skip_lbg_ia_voice") is True:
        return None
    if not is_first_turn(ctx):
        return None
    if not is_greeting_only(text):
        return None
    reply = FIRST_CONTACT_REPLY
    return {
        "agent": "lbg_ia_voice",
        "handler": "assistant_chat",
        "ok": True,
        "actor_id": actor_id,
        "reply": reply,
        "remote": {"reply": reply, "source": "lbg_ia_first_contact"},
        "voice": {
            "first_contact": True,
            "intent": "assistant_chat",
            "routed_to": "agent.lbg_ia_voice",
        },
    }


def apply_voice_to_agent_output(
    output: dict[str, Any],
    *,
    intent: str,
    routed_to: str,
    text: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Applique la voix LBG-IA sur la sortie agent si un reply est présent ou constructible."""
    ctx = context if isinstance(context, dict) else {}
    if ctx.get("_skip_lbg_ia_voice") is True:
        return output

    out = dict(output)
    raw_reply = ""
    if isinstance(out.get("reply"), str) and out["reply"].strip():
        raw_reply = out["reply"].strip()
    else:
        remote = out.get("remote")
        if isinstance(remote, dict) and isinstance(remote.get("reply"), str):
            raw_reply = remote["reply"].strip()

    if not raw_reply and routed_to == "agent.fallback":
        raw_reply = unknown_capability_reply(text)

    if not raw_reply:
        return out

    wrapped = wrap_operational_reply(
        raw_reply,
        intent=intent,
        routed_to=routed_to,
        text=text,
        context=ctx,
        include_skill_footer=intent not in {"npc_dialogue"},
    )
    out["reply"] = wrapped
    remote = out.get("remote")
    if isinstance(remote, dict):
        remote = dict(remote)
        remote["reply"] = wrapped
        out["remote"] = remote
    else:
        out["remote"] = {"reply": wrapped, "source": "lbg_ia_voice"}

    voice_meta = {
        "intent": intent,
        "routed_to": routed_to,
        "first_turn": is_first_turn(ctx),
        "skill": SKILL_LABELS.get(intent, (intent, ""))[0],
    }
    out["voice"] = voice_meta
    return out
