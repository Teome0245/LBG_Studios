"""Plan 3.1 — Live World Stream Hub → Compagnon (pont monde ↔ bureau).

Fetch léger `/v1/world/stream` sur :8787 (prime-hub Godot).
Enrichit le greeting / causerie Compagnon avec les événements récents marquants
(boss abattu, convoi ferraille, escorte de Nix, etc.).
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger("lbg.world_stream")

# Détection de questions sur le monde live
_WORLD_STREAM_QUERY_RE = re.compile(
    r"(?i)\b("
    r"quoi\s+de\s+neuf\s+(?:en\s+jeu|dans\s+le\s+monde|au\s+hub|sur\s+lost\s+heaven|sur\s+scrapalta[ïi])|"
    r"qu[''\u2019]est[- ]ce\s+qui\s+se\s+passe\s+(?:en\s+jeu|au\s+hub|[àa]\s+lost\s+heaven|dans\s+le\s+monde|sur\s+scrapalta[ïi])|"
    r"comment\s+(?:s[''\u2019]en\s+sortent|vont|évoluent|tournent)\s+(?:les\s+)?(?:pnj|habitants|citoyens|colons)|"
    r"(?:des\s+)?nouvelles\s+des\s+(?:pnj|habitants|colons)|"
    r"état\s+des\s+pnj|"
    r"sur\s+scrapalta[ïi]|"
    r"[ée]v[ée]nements?\s+(?:du\s+monde|en\s+jeu|live\s+world|r[ée]cents?)|"
    r"live\s+world\s+stream|"
    r"flux\s+(?:du\s+monde|monde|hub)|"
    r"nouvelles\s+(?:du\s+hub|du\s+monde|de\s+lost\s+heaven|du\s+jeu|de\s+scrapalta[ïi])|"
    r"(?:derniers?\s+)?faits?\s+marquants?\s+(?:en\s+jeu|du\s+monde|du\s+hub)"
    r")\b"
)

# Cache mémoire court pour éviter les requêtes redondantes
_CACHE: dict[str, Any] = {
    "data": None,
    "exp": 0.0,
}
_CACHE_TTL_S = 10.0


def world_stream_enabled(*, lab: bool = False) -> bool:
    raw = (os.getenv("LBG_COMPAGNON_WORLD_STREAM") or "1").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    return True


def wants_world_stream(prompt: str) -> bool:
    text = (prompt or "").strip()
    if not text or len(text) > 400:
        return False
    return bool(_WORLD_STREAM_QUERY_RE.search(text))


def hub_world_stream_url(since: int = 0, limit: int = 20) -> str:
    base = (
        os.getenv("LBG_PRIME_HUB_URL")
        or os.getenv("LBG_HUB_HTTP_URL")
        or "http://192.168.0.246:8787"
    ).strip().rstrip("/")
    return f"{base}/v1/world/stream?since={since}&limit={limit}"


def fetch_world_stream(
    *,
    since: int = 0,
    limit: int = 20,
    timeout: float = 1.5,
    use_cache: bool = True,
) -> dict[str, Any]:
    global _CACHE
    now = time.time()
    if use_cache and since == 0 and _CACHE["data"] is not None and now < _CACHE["exp"]:
        return _CACHE["data"]

    url = hub_world_stream_url(since=since, limit=limit)
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw) if raw.strip() else {}
        if isinstance(data, dict):
            if since == 0 and bool(data.get("ok", True)):
                _CACHE["data"] = data
                _CACHE["exp"] = now + _CACHE_TTL_S
            return data
        return {"ok": False, "error": "invalid_json"}
    except Exception as e:
        logger.debug("world_stream fetch failed (%s): %s", url, e)
        # Si un cache expiré existe, servir en dégradation douce
        if _CACHE["data"] is not None:
            return _CACHE["data"]
        return {"ok": False, "error": str(e)[:120], "events": []}


def _event_priority(ev: dict[str, Any]) -> int:
    kind = str(ev.get("kind", ""))
    if "boss_defeated" in kind:
        return 100
    if "event.activate" in kind or "scrap_fall" in kind:
        return 90
    if "companion.escort" in kind:
        return 80
    if "beast_defeated" in kind:
        return 70
    if "event.end" in kind:
        return 50
    return 40


def latest_world_highlight(
    stream_data: dict[str, Any] | None = None,
    *,
    max_age_s: float = 7200.0,
) -> dict[str, Any] | None:
    data = stream_data or fetch_world_stream(since=0, limit=20)
    raw_events = data.get("events") if isinstance(data.get("events"), list) else []
    try:
        from src.services.world_notif_prefs import filter_events
    except ImportError:
        try:
            from world_notif_prefs import filter_events  # type: ignore
        except ImportError:
            filter_events = None  # type: ignore
    events = filter_events(raw_events) if filter_events else raw_events
    if not events:
        return None

    now = time.time()
    candidates: list[tuple[int, float, dict[str, Any]]] = []
    for ev in events:
        if not isinstance(ev, dict):
            continue
        ts = float(ev.get("ts", 0) or 0)
        # Filtre sur l'âge si ts valide
        if ts > 0 and (now - ts) > max_age_s:
            continue
        prio = _event_priority(ev)
        candidates.append((prio, ts, ev))

    if not candidates:
        last_ev = events[-1]
        return last_ev if isinstance(last_ev, dict) else None

    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return candidates[0][2]


def format_world_greeting(
    event: dict[str, Any] | None = None,
    *,
    player: str = "Teome",
) -> str | None:
    """Enrichit la salutation sociale avec le fait marquant du monde (Ticket 3.1)."""
    ev = event or latest_world_highlight()
    if not ev or not isinstance(ev, dict):
        return None
    text = str(ev.get("text", "")).strip()
    if not text:
        return None
    kind = str(ev.get("kind", ""))

    if "boss_defeated" in kind:
        world_snippet = f"La cour de Lost Heaven a été agitée tout à l'heure : {text}"
    elif "event.activate" in kind or "scrap_fall" in kind:
        world_snippet = f"Il y a du mouvement sur Lost Heaven : {text}"
    elif "companion.escort" in kind:
        world_snippet = f"Ça bougeait près du hub tout à l'heure : {text}"
    else:
        world_snippet = f"Du nouveau sur Lost Heaven : {text}"

    return (
        f"Salut — ça va de mon côté ! {world_snippet} "
        f"Je t'écoute, collègue studio. Tu voulais qu'on avance sur quoi aujourd'hui ?"
    )


def format_world_context_block(*, limit: int = 3) -> str:
    """Bloc injecté dans le contexte LLM pour la causerie studio."""
    data = fetch_world_stream(since=0, limit=max(1, limit * 2))
    events = data.get("events") if isinstance(data.get("events"), list) else []
    try:
        from src.services.world_notif_prefs import filter_events
    except ImportError:
        try:
            from world_notif_prefs import filter_events  # type: ignore
        except ImportError:
            filter_events = None  # type: ignore
    if filter_events:
        events = filter_events(events)
    if not events:
        return ""
    lines = ["[Derniers événements monde Lost Heaven (prime-hub :8787)]"]
    for ev in events[-limit:]:
        if not isinstance(ev, dict):
            continue
        t = str(ev.get("text", "")).strip()
        z = str(ev.get("zone", "")).strip()
        if t:
            zone_tag = f" ({z})" if z else ""
            lines.append(f"- {t}{zone_tag}")
    return "\n".join(lines)


def fetch_hub_health(*, timeout: float = 1.5) -> dict[str, Any]:
    """Récupère l'état agrégé du hub (:8787/healthz)."""
    base = (
        os.getenv("LBG_PRIME_HUB_URL")
        or os.getenv("LBG_HUB_HTTP_URL")
        or "http://192.168.0.246:8787"
    ).strip().rstrip("/")
    url = f"{base}/healthz"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else {}
    except Exception as e:
        logger.debug("hub health fetch failed (%s): %s", url, e)
        return {}


def format_world_stream_report(data: dict[str, Any]) -> str:
    """Réponse collègue quand l'utilisateur demande des nouvelles du monde."""
    health = fetch_hub_health()
    clock = (health.get("active_event") or {}).get("world_clock") or {}
    life = health.get("life") or {}
    npc_count = health.get("npc_count", 0)

    bits = []
    if clock and clock.get("game_day"):
        day = clock.get("game_day")
        hour_str = clock.get("time_string", "10:00")
        phase_label = clock.get("day_phase_label", "Plein jour")
        weather = ((health.get("active_event") or {}).get("weather") or {}).get("label", "Ciel dégagé")
        work_n = life.get("work", 0)
        leisure_n = life.get("leisure", 0)
        rest_n = life.get("rest", 0)
        bits.append(
            f"Sur Scrapaltaï, la simulation tourne à plein régime ! Nous sommes au **Jour {day}** ({phase_label}, {hour_str}). "
            f"Météo : {weather}. La planète compte actuellement **{npc_count} PNJ actifs** "
            f"({work_n} au travail, {leisure_n} à La Perle / loisir, {rest_n} au repos)."
        )
    elif not data.get("ok"):
        err = str(data.get("error") or "hub injoignable")
        return (
            f"Je n'ai pas pu joindre le flux d'événements du hub ({err}). "
            "Vérifie que `prime-hub` tourne sur le port `:8787`."
        )

    events = data.get("events") if isinstance(data.get("events"), list) else []
    try:
        from src.services.world_notif_prefs import filter_events
    except ImportError:
        try:
            from world_notif_prefs import filter_events  # type: ignore
        except ImportError:
            filter_events = None  # type: ignore
    if filter_events:
        events = filter_events(events)

    if events:
        bits.append("\n**Derniers faits marquants récents :**")
        for ev in events[-5:]:
            if not isinstance(ev, dict):
                continue
            t = str(ev.get("text", "")).strip()
            if t:
                bits.append(f"- {t}")

    bits.append("\nJe t'écoute, tu voulais observer un quartier particulier ou travailler sur le studio ?")
    return "\n".join(bits)


async def attach_world_stream_if_needed(
    result: Any,
    *,
    prompt: str,
    lab: bool = False,
) -> Any:
    if not isinstance(result, dict):
        return result
    if not world_stream_enabled(lab=lab):
        return result
    if not wants_world_stream(prompt):
        return result
    if result.get("world_stream"):
        return result

    data = fetch_world_stream(since=0, limit=10, use_cache=False)
    content = format_world_stream_report(data)
    out = {
        **result,
        "content": content,
        "response": content,
        "source": "world_stream",
        "model": "world_stream",
        "model_used": "world_stream",
        "world_stream": {
            "ok": bool(data.get("ok")),
            "events_count": len(data.get("events") or []),
            "seq": data.get("seq", 0),
        },
    }
    return out
