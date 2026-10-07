"""Dialogue PNJ hub — stub hors Core3 / hors Pilot 8020 (Phase C)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_CORTEX = Path(__file__).resolve().parents[2]
_REGISTRY_CANDIDATES = [
    _CORTEX / "agents" / "src" / "lbg_agents" / "npc_registry.json",
    Path("/opt/LBG_IA_MMO/agents/src/lbg_agents/npc_registry.json"),
]

# Répliques courtes FR — Lost Heaven (Bible, pas de SWG)
_GREETINGS: dict[str, str] = {
    "npc:core3_daan_oth": (
        "Daan Oth. Bureau des missions — contrats de survie, chasse, courses. "
        "Dis-moi ce que tu cherches."
    ),
    "npc:core3_barman_jax": (
        "Bienvenue à La Perle. Jax au comptoir — un verre, une rumeur, ou juste t'asseoir ?"
    ),
    "npc:guide_quartier": (
        "Guide de quartier. Starport à l'ouest, marché au sud, porte est vers le désert. "
        "Tu te perds, tu cries."
    ),
    "npc:core3_medic_trainer_c": (
        "Odo Merr — clinique. Kits de terrain, stabilisation. Tu saignes, tu rentres."
    ),
    "npc:core3_scout_trainer_c": (
        "Yara Nis. Prospection et pistes hors remparts. Le désert ne pardonne pas."
    ),
    "npc:core3_artisan_trainer_c": (
        "Kell Asa. Atelier — outils, kits, pièces. Rien de neuf ici, tout se récupère."
    ),
    "npc:core3_talen_ress": (
        "Talen Ress. Formation scène à l'auberge — danse, musique, moral. Pas Kisreudi."
    ),
    "npc:scribe": (
        "Scribe de la mairie. Chroniques de session, pas de légendes inventées. Tu notes ?"
    ),
    "npc:habitue_cantina": "Toujours la même table à La Perle. Qu'est-ce que tu bois ?",
    "npc:videur": "Pas de bagarre devant La Perle. Jax s'occupe du verre, moi de la porte.",
    "npc:sergent_rue": "Sergent de rue. Porte est sous surveillance — meute ou pas.",
    "npc:rumeuriste": "Au marché on entend tout. Tu veux une rumeur… ou un prix ?",
    "npc:core3_brawler_trainer_c": "Tobin Ress. Poing avant paroles — hall d'entraînement.",
    "npc:core3_marksman_trainer_c": "Unar Tek. Visée. Respire, tire.",
    "npc:core3_pilot_imperial_a": "Garr Vek. Pilotage shuttle — apron propre.",
}

# Suggestions embarquées (si registry absent sur la VM)
_DEFAULT_MOVES: dict[str, list[dict[str, Any]]] = {
    "npc:core3_daan_oth": [
        {"id": "move:daan_offres", "label": "Voir les offres", "utterance": "Quelles missions as-tu ?", "kind": "ui", "action": {"name": "open_mission_board"}},
        {"id": "move:daan_desert", "label": "Survivre au désert", "utterance": "Un conseil pour tenir hors des murs ?", "kind": "info"},
        {"id": "move:daan_perle", "label": "Tip scène", "utterance": "Je veux soutenir le show à La Perle.", "kind": "quest"},
    ],
    "npc:core3_barman_jax": [
        {"id": "move:perle_boisson", "label": "Une boisson", "utterance": "Un verre, Jax — qu'est-ce que tu sers ce soir ?", "kind": "social"},
        {"id": "move:perle_show", "label": "Spectacle ce soir", "utterance": "Il y a un spectacle à La Perle ce soir ?", "kind": "info"},
        {"id": "move:perle_daan", "label": "Missions", "utterance": "Où trouver des contrats ?", "kind": "info"},
    ],
    "npc:guide_quartier": [
        {"id": "move:guide_map", "label": "Orientation", "utterance": "Où est le marché ?", "kind": "info"},
        {"id": "move:guide_gate", "label": "Porte est", "utterance": "Comment sortir vers le désert ?", "kind": "info"},
    ],
    "npc:core3_medic_trainer_c": [
        {"id": "move:odo_kit", "label": "Kits", "utterance": "Tu as des kits de terrain ?", "kind": "info"},
    ],
    "npc:core3_scout_trainer_c": [
        {"id": "move:yara_piste", "label": "Pistes", "utterance": "Une piste sûre hors remparts ?", "kind": "info"},
    ],
    "npc:core3_artisan_trainer_c": [
        {"id": "move:kell_craft", "label": "Craft", "utterance": "Que puis-je assembler ici ?", "kind": "info"},
    ],
    "npc:core3_talen_ress": [
        {"id": "move:talen_scene", "label": "Scène", "utterance": "Tu formes à la danse ?", "kind": "info"},
    ],
    "npc:scribe": [
        {"id": "move:scribe_note", "label": "Chronique", "utterance": "Tu tiens une chronique de session ?", "kind": "info"},
    ],
}

_FALLBACK_REPLIES: list[tuple[str, str]] = [
    ("mission", "Le board a des offres près du bureau. Daan Oth te dira lesquelles tiennent."),
    ("désert", "Hors murs : eau, ombre, et ne reste pas seul après le crépuscule."),
    ("desert", "Hors murs : eau, ombre, et ne reste pas seul après le crépuscule."),
    ("boisson", "À La Perle, Jax sert ce qu'on a — chaud, amer, honnête."),
    ("verre", "Un verre ? Jax te fixe ça au comptoir de La Perle."),
    ("spectacle", "La scène, c'est Talen Ress et l'artiste de La Perle — pas le scientifique."),
    ("show", "La scène, c'est Talen Ress et l'artiste de La Perle — pas le scientifique."),
    ("craft", "Kell Asa à l'atelier : combine ce que tu ramasses."),
    ("soin", "Clinique, Odo Merr. Pas de miracle — des kits."),
    ("porte", "Porte est = désert. Porte ouest = Zalem. Les remparts tiennent… pour l'instant."),
    ("nix", "Nix, Lia, Mira tournent le hub — joueurs IA, pas PNJ de comptoir."),
    ("lia", "Lia fait auberge / port / cantina. Elle parle court."),
    ("mira", "Mira couvre le board et le marché. Contrats avant bavardage."),
]


def _load_registry() -> dict[str, dict[str, Any]]:
    for path in _REGISTRY_CANDIDATES:
        if not path.is_file():
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        npcs = raw.get("npcs") if isinstance(raw, dict) else None
        if not isinstance(npcs, list):
            continue
        out: dict[str, dict[str, Any]] = {}
        for n in npcs:
            if isinstance(n, dict) and n.get("id"):
                out[str(n["id"])] = n
        if out:
            return out
    return {}


_REGISTRY = _load_registry()


def _normalize_npc_id(raw: str) -> str:
    s = str(raw or "").strip()
    while s.startswith("npc:npc:"):
        s = "npc:" + s[8:]
    if s.startswith("core3_") and not s.startswith("npc:"):
        s = "npc:" + s
    return s


def _suggested_moves(npc_id: str) -> list[dict[str, Any]]:
    entry = _REGISTRY.get(npc_id) or {}
    raw = entry.get("suggestion_templates") or []
    out: list[dict[str, Any]] = []
    if isinstance(raw, list):
        for item in raw[:3]:
            if not isinstance(item, dict):
                continue
            mid = str(item.get("id") or "").strip()
            label = str(item.get("label") or "").strip()
            if not mid or not label:
                continue
            move: dict[str, Any] = {
                "id": mid,
                "label": label[:28],
                "utterance": str(item.get("utterance") or label).strip()[:160],
            }
            kind = str(item.get("kind") or "").strip()
            if kind:
                move["kind"] = kind
            if isinstance(item.get("action"), dict):
                move["action"] = dict(item["action"])
            out.append(move)
    if out:
        return out
    # fallback embarqué
    for item in _DEFAULT_MOVES.get(npc_id, [])[:3]:
        out.append(dict(item))
    return out


def _pick_reply(npc_id: str, npc_name: str, player_text: str) -> str:
    t = (player_text or "").strip().lower()
    greeting_keys = {"", "bonjour", "bonjour.", "salut", "hello", "hey"}
    greet_cfg = "bonjour — parle-moi de lost heaven"
    is_greet = (
        not t
        or t in greeting_keys
        or t.startswith("bonjour")
        or greet_cfg in t
    )
    # LLM d'abord (timeout court) — fallback stub
    try:
        from tools.hub_runtime import llm_chat

        entry = _REGISTRY.get(npc_id) or {}
        role = str(entry.get("role") or entry.get("summary") or "habitant hub")
        place = str(entry.get("zone") or "Lost Heaven")
        llm = llm_chat.npc_line(
            name=npc_name or str(entry.get("name") or "PNJ"),
            role_hint=role[:120],
            player_text=player_text,
            place=place,
        )
        if llm:
            return llm
    except Exception:
        pass
    if is_greet and npc_id in _GREETINGS:
        return _GREETINGS[npc_id]
    for key, reply in _FALLBACK_REPLIES:
        if key in t:
            return reply
    entry = _REGISTRY.get(npc_id) or {}
    tone = str(entry.get("tone") or "").strip()
    zone = str(entry.get("zone") or "Lost Heaven").strip()
    who = npc_name or str(entry.get("name") or "PNJ")
    if tone:
        return f"{who} ({zone}) — je t'écoute. Reste court, on est au hub."
    return f"{who} : je suis là. Qu'est-ce qu'il te faut à Lost Heaven ?"


def invoke(body: dict[str, Any]) -> dict[str, Any]:
    ctx = body.get("context") if isinstance(body.get("context"), dict) else {}
    npc_id = _normalize_npc_id(str(ctx.get("world_npc_id") or body.get("world_npc_id") or ""))
    npc_name = str(ctx.get("npc_name") or body.get("npc_name") or "").strip()
    player_text = str(body.get("text") or "").strip()
    if not npc_name and npc_id in _REGISTRY:
        npc_name = str(_REGISTRY[npc_id].get("name") or "")
    if not npc_id and npc_name:
        for eid, ent in _REGISTRY.items():
            if str(ent.get("name", "")).lower() == npc_name.lower():
                npc_id = eid
                break
    reply = _pick_reply(npc_id, npc_name, player_text)
    moves = _suggested_moves(npc_id)
    return {
        "ok": True,
        "reply": reply,
        "suggested_moves": moves,
        "meta": {
            "lyra_engagement_resolved": "hub_runtime_stub",
            "dialogue_profile_resolved": "hub_spike",
            "suggested_moves_source": "registry_template" if moves else "none",
            "world_npc_id": npc_id,
            "npc_name": npc_name,
            "source": "hub_runtime",
        },
    }
