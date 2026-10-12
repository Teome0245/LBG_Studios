"""Plan 3.2 — Convergence de la mémoire relationnelle (jeu ↔ bureau).

Passerelle bilatérale entre la mémoire de jeu (`players_state.json` / `relation_memory`
sur prime-hub :8787) et le Compagnon Studio (Cortex / bureau).

Permet au Compagnon de connaître les interactions de Teome avec les PNJ (Jax, Nix, Daan)
et d'adapter sa familiarité, ses références et son ton.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

logger = logging.getLogger("lbg.relation_memory")

# Détection de requêtes portant sur les relations ou la réputation en jeu
_RELATION_QUERY_RE = re.compile(
    r"(?i)\b("
    r"relations?\s+(?:avec\s+)?(?:les\s+pnj|jax|nix|daan|mira|lost\s+heaven|en\s+jeu|au\s+hub)|"
    r"liens?\s+(?:avec\s+)?(?:les\s+pnj|jax|nix|daan|mira|en\s+jeu)|"
    r"familiarit[ée]\s+(?:avec\s+)?(?:les\s+pnj|jax|nix|daan|mira)|"
    r"qui\s+me\s+conna[îi]t\s+(?:en\s+jeu|au\s+hub|à\s+lost\s+heaven)|"
    r"qui\s+se\s+souvient\s+de\s+moi\s+(?:en\s+jeu|au\s+hub)|"
    r"ce\s+que\s+pensent\s+les\s+pnj|"
    r"ce\s+que\s+(?:(?:jax|nix|daan|mira)\s+pense|pense\s+(?:jax|nix|daan|mira))\s+de\s+moi|"
    r"r[ée]putation\s+(?:avec\s+)?(?:jax|nix|daan|mira|en\s+jeu|au\s+hub|à\s+lost\s+heaven)|"
    r"m[ée]moire\s+relationnelle\s+(?:jeu|hub|mmo)"
    r")\b"
)

# Cache mémoire pour éviter de saturer prime-hub
_CACHE: dict[str, Any] = {
    "player": "",
    "data": None,
    "exp": 0.0,
}
_CACHE_TTL_S = 15.0

# Libellés humains pour les types d'interactions
_KIND_LABELS: dict[str, str] = {
    "gift": "Pourboire / Don",
    "tip": "Pourboire",
    "trade": "Commerce / Bar",
    "quest_accept": "Quête acceptée",
    "quest_complete": "Quête accomplie",
    "escort": "Escorte",
    "met": "Rencontre",
    "chat": "Dialogue",
}


def relation_memory_enabled(*, lab: bool = False) -> bool:
    raw = (os.getenv("LBG_COMPAGNON_RELATION_MEMORY") or "1").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    return True


def wants_relation_memory(prompt: str) -> bool:
    text = (prompt or "").strip()
    if not text or len(text) > 400:
        return False
    return bool(_RELATION_QUERY_RE.search(text))


def hub_relation_memory_url(player: str = "Teome", npc_id: str = "") -> str:
    base = (
        os.getenv("LBG_PRIME_HUB_URL")
        or os.getenv("LBG_HUB_HTTP_URL")
        or "http://192.168.0.246:8787"
    ).strip().rstrip("/")
    q = urllib.parse.urlencode({"player": player, "npc_id": npc_id})
    return f"{base}/v1/relation-memory?{q}"


def hub_relation_append_url() -> str:
    base = (
        os.getenv("LBG_PRIME_HUB_URL")
        or os.getenv("LBG_HUB_HTTP_URL")
        or "http://192.168.0.246:8787"
    ).strip().rstrip("/")
    return f"{base}/v1/relation-memory/append"


def fetch_relation_memory(
    player: str = "Teome",
    npc_id: str = "",
    *,
    timeout: float = 1.5,
    use_cache: bool = True,
) -> dict[str, Any]:
    """Interroge la mémoire relationnelle de prime-hub pour un joueur."""
    global _CACHE
    now = time.time()
    if (
        use_cache
        and not npc_id
        and _CACHE["player"] == player
        and _CACHE["data"] is not None
        and now < _CACHE["exp"]
    ):
        return _CACHE["data"]

    url = hub_relation_memory_url(player=player, npc_id=npc_id)
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw) if raw.strip() else {}
        if isinstance(data, dict):
            if not npc_id and bool(data.get("ok", True)):
                _CACHE["player"] = player
                _CACHE["data"] = data
                _CACHE["exp"] = now + _CACHE_TTL_S
            return data
        return {"ok": False, "error": "invalid_json", "entries": []}
    except Exception as e:
        logger.debug("relation_memory fetch failed (%s): %s", url, e)
        if _CACHE["data"] is not None and _CACHE["player"] == player:
            return _CACHE["data"]
        return {"ok": False, "error": str(e)[:120], "entries": []}


def append_relation_memory(
    player: str = "Teome",
    npc_id: str = "",
    kind: str = "chat",
    note: str = "",
    detail: dict[str, Any] | None = None,
    *,
    timeout: float = 2.0,
) -> dict[str, Any]:
    """Enregistre bilatéralement une note relationnelle vers prime-hub."""
    url = hub_relation_append_url()
    payload = {
        "player": player,
        "npc_id": npc_id,
        "kind": kind,
        "note": note,
        "value": (detail or {}).get("value"),
        "quest_id": (detail or {}).get("quest_id", ""),
        "item_id": (detail or {}).get("item_id", ""),
    }
    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw) if raw.strip() else {}
        return data if isinstance(data, dict) else {"ok": False}
    except Exception as e:
        logger.warning("relation_memory append failed: %s", e)
        return {"ok": False, "error": str(e)[:120]}


def format_relation_memory_block(player: str = "Teome", limit: int = 4) -> str:
    """Bloc injecté dans le prompt système pour donner conscience des liens MMO."""
    data = fetch_relation_memory(player=player, timeout=1.2)
    entries = data.get("entries") if isinstance(data.get("entries"), list) else []
    if not entries:
        return ""

    lines = [f"[Mémoire relationnelle in-game (Lost Heaven) — Joueur : {player}]"]
    for row in entries[:limit]:
        if not isinstance(row, dict):
            continue
        npc = str(row.get("npc_name") or row.get("npc_id") or "PNJ").replace("npc:core3_", "").replace("_", " ").title()
        kind = str(row.get("kind", ""))
        label = _KIND_LABELS.get(kind, kind)
        note = str(row.get("note", "")).strip()
        if note:
            lines.append(f"- Avec {npc} ({label}) : {note}")
        else:
            lines.append(f"- Avec {npc} ({label})")

    lines.append("Consigne : utilise ces références avec familiarité si le sujet du MMO ou des PNJ est abordé.")
    return "\n".join(lines)


def format_relation_report(data: dict[str, Any], player: str = "Teome") -> str:
    """Réponse collègue quand l'utilisateur demande ses relations in-game."""
    if not data.get("ok"):
        err = str(data.get("error") or "hub injoignable")
        return (
            f"Je n'ai pas pu joindre la mémoire relationnelle de prime-hub ({err}). "
            "Vérifie que le serveur Godot `:8787` est actif."
        )

    entries = data.get("entries") if isinstance(data.get("entries"), list) else []
    if not entries:
        return (
            f"Aucune trace d'interaction persistée pour **{player}** pour le moment. "
            "Passe voir Jax à La Perle ou prends une quête auprès de Daan pour créer du lien."
        )

    bits = [f"Voici l'état de tes relations in-game sur Lost Heaven (**{player}**) :"]
    for row in entries[:6]:
        if not isinstance(row, dict):
            continue
        npc = str(row.get("npc_name") or row.get("npc_id") or "PNJ").replace("npc:core3_", "").replace("_", " ").title()
        kind = str(row.get("kind", ""))
        label = _KIND_LABELS.get(kind, kind)
        note = str(row.get("note", "")).strip()
        desc = f" : {note}" if note else ""
        bits.append(f"- **{npc}** [{label}]{desc}")

    bits.append("Ces liens nourrissent ma familiarité avec ton parcours en jeu. On enchaîne sur quoi ?")
    return "\n".join(bits)


async def attach_relation_memory_if_needed(
    result: Any,
    *,
    prompt: str,
    lab: bool = False,
    player: str = "Teome",
) -> Any:
    if not isinstance(result, dict):
        return result
    if not relation_memory_enabled(lab=lab):
        return result
    if not wants_relation_memory(prompt):
        return result
    if result.get("relation_memory"):
        return result

    data = fetch_relation_memory(player=player, use_cache=False)
    content = format_relation_report(data, player=player)
    out = {
        **result,
        "content": content,
        "response": content,
        "source": "relation_memory",
        "model": "relation_memory",
        "model_used": "relation_memory",
        "relation_memory": {
            "ok": bool(data.get("ok")),
            "entries_count": len(data.get("entries") or []),
            "player": player,
        },
    }
    return out
