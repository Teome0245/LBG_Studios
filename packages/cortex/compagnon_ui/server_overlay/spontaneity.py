"""
Spontanéité Compagnon — propositions d'initiative imprévues + moteur d'évolution.

- Les *gates* (quand offrir) restent côté SPA / Self.
- Ici : réécriture LLM light du *contenu* (message + intents) + mémoire accept/dismiss.
- Jamais d'auto-Réel : intents Agir / discuss / Team L1 seulement.
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

logger = logging.getLogger("lbg.spontaneity")

_lock = threading.RLock()

# --- allowlist / sécurité -------------------------------------------------

_FORBIDDEN_RE = re.compile(
    r"(?i)\b("
    r"rm\s+-rf|format\s+c:|shutdown|reboot|force\s*push|drop\s+table|"
    r"supprime\s+tout|wipe|factory\s*reset|kill\s+-9|"
    r"passwd|credentials?\.json|\.env\b|api[_-]?key"
    r")\b"
)

_SAFE_ACTION_PREFIX = re.compile(
    r"(?i)^("
    r"fais\b|montre\b|regarde\b|ouvre\b|lance\b|vérifie\b|verifie\b|"
    r"team\b|team:|cursor:|mission:|"
    r"quel\b|quels?\b|où\b|ou\b|comment\b|pourquoi\b|"
    r"compile\b|propose\b|résume\b|resume\b|explique\b"
    r")"
)

_HARD_KINDS = frozenset(
    {
        "garde",
        "morning_brief",
        "disk",
        "infra",
    }
)

_SYSTEM = """Tu es le Compagnon LBG (studio LAN). Tu proposes UNE initiative SPONTANÉE.
Spontané ≠ aléatoire destructeur : utile, imprévu, ancré dans le contexte, jamais auto-exec L2.

Réponds UNIQUEMENT un JSON strict :
{"message":"…","themes":["…"],"intents":[{"id":"…","label":"…","sourceText":"…","hint":"…","teamSpawn":false}],"evolution_seed":null}

Règles :
- message : 1–2 phrases FR, ton collègue studio, PAS « En tant qu'IA ».
- 1 ou 2 intents max. sourceText = phrase Agir/discuter actionnable (préfixe fais/ouvre/team/regarde/…).
- teamSpawn true seulement pour une micro-tâche Team L1 lecture seule.
- Interdit : destructive, secrets, reboot, wipe, force push.
- Évite strictement les thèmes / titres listés dans « À éviter ».
- Si mode=message_only : garde les intents fournis, réécris seulement message (plus vivant).
- evolution_seed : null, OU courte idée d'évolution produit Compagnon si vraiment nouvelle (max 120 car).
"""


def spontaneity_enabled() -> bool:
    raw = os.getenv("LBG_SPONTANEITY_ENABLED", "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


def state_path() -> Path:
    return Path(
        os.environ.get("LBG_SPONTANEITY_STATE_PATH", "/var/lib/lbg/spontaneity/state.json").strip()
        or "/var/lib/lbg/spontaneity/state.json"
    )


def cache_ttl_s() -> float:
    try:
        return max(60.0, float(os.getenv("LBG_SPONTANEITY_CACHE_TTL_S", "1200").strip() or "1200"))
    except ValueError:
        return 1200.0


def _default_state() -> dict[str, Any]:
    return {
        "shown": [],
        "feedback": [],
        "theme_scores": {},
        "evolution_seeds": [],
        "cache": {},
        "updated_ts": 0.0,
    }


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def load_state() -> dict[str, Any]:
    path = state_path()
    if not path.is_file():
        return _default_state()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return _default_state()
        base = _default_state()
        base.update({k: data.get(k, base[k]) for k in base})
        return base
    except Exception:
        return _default_state()


def persist_state(st: dict[str, Any]) -> dict[str, Any]:
    st = deepcopy(st)
    st["updated_ts"] = time.time()
    # prune
    cutoff = time.time() - 14 * 86400
    st["shown"] = [x for x in (st.get("shown") or []) if isinstance(x, dict) and float(x.get("ts") or 0) >= cutoff][
        -80:
    ]
    st["feedback"] = [
        x for x in (st.get("feedback") or []) if isinstance(x, dict) and float(x.get("ts") or 0) >= cutoff
    ][-120:]
    st["evolution_seeds"] = [
        x for x in (st.get("evolution_seeds") or []) if isinstance(x, dict) and float(x.get("ts") or 0) >= cutoff
    ][-40:]
    cache = st.get("cache") if isinstance(st.get("cache"), dict) else {}
    now = time.time()
    st["cache"] = {k: v for k, v in cache.items() if isinstance(v, dict) and float(v.get("exp") or 0) > now}
    _atomic_write(state_path(), st)
    return st


def spice_mode_for(offer: dict[str, Any]) -> str:
    """full | message_only — garde / brief critique = message only."""
    kind = str(offer.get("kind") or "").lower()
    offer_type = str(offer.get("offerType") or "").lower()
    oid = str(offer.get("id") or "").lower()
    if offer_type == "garde" or kind in _HARD_KINDS:
        return "message_only"
    if oid.startswith("disk:") or oid.startswith("infra:") or oid.startswith("jobs:l2"):
        return "message_only"
    if "morning_brief" in kind or oid.startswith("studio:morning"):
        # brief utile mais message peut être spontané ; intents restés brief/mail
        return "message_only"
    return "full"


def _themes_to_avoid(st: dict[str, Any], limit: int = 12) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for row in reversed(list(st.get("shown") or [])):
        if not isinstance(row, dict):
            continue
        title = str(row.get("title") or "").strip()
        if title and title.lower() not in seen:
            seen.add(title.lower())
            out.append(title)
        for t in row.get("themes") or []:
            s = str(t).strip().lower()
            if s and s not in seen:
                seen.add(s)
                out.append(s)
        if len(out) >= limit:
            break
    # themes with strong dismiss bias
    scores = st.get("theme_scores") if isinstance(st.get("theme_scores"), dict) else {}
    for theme, score in sorted(scores.items(), key=lambda kv: float(kv[1] or 0)):
        if float(score or 0) <= -1.5:
            s = str(theme).strip().lower()
            if s and s not in seen:
                seen.add(s)
                out.append(s)
        if len(out) >= limit + 6:
            break
    return out[: limit + 6]


def _liked_themes(st: dict[str, Any], limit: int = 8) -> list[str]:
    scores = st.get("theme_scores") if isinstance(st.get("theme_scores"), dict) else {}
    ranked = sorted(
        ((str(k), float(v or 0)) for k, v in scores.items()),
        key=lambda kv: kv[1],
        reverse=True,
    )
    return [k for k, sc in ranked if sc >= 1.0][:limit]


def evolution_snapshot(st: dict[str, Any] | None = None) -> dict[str, Any]:
    data = st or load_state()
    seeds = list(data.get("evolution_seeds") or [])
    top = sorted(
        [s for s in seeds if isinstance(s, dict)],
        key=lambda s: float(s.get("score") or 0),
        reverse=True,
    )[:8]
    return {
        "ok": True,
        "enabled": spontaneity_enabled(),
        "theme_scores": data.get("theme_scores") or {},
        "liked_themes": _liked_themes(data),
        "avoid_themes": _themes_to_avoid(data, 8),
        "evolution_seeds": top,
        "shown_count": len(data.get("shown") or []),
        "feedback_count": len(data.get("feedback") or []),
    }


def _parse_json_blob(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if not text:
        return None
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except Exception:
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            return None
        try:
            data = json.loads(m.group(0))
            return data if isinstance(data, dict) else None
        except Exception:
            return None


def _sanitize_intent(raw: dict[str, Any], idx: int) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    label = str(raw.get("label") or "").strip()[:80]
    source = str(raw.get("sourceText") or raw.get("source_text") or "").strip()
    source = re.sub(r"\s+", " ", source)[:220]
    if len(label) < 2 or len(source) < 10:
        return None
    if _FORBIDDEN_RE.search(label) or _FORBIDDEN_RE.search(source):
        return None
    if not _SAFE_ACTION_PREFIX.search(source) and not source.lower().startswith("http"):
        # force discuss-safe prefix
        source = f"propose : {source}"[:220]
    hint = str(raw.get("hint") or "").strip()[:80]
    team = bool(raw.get("teamSpawn") or raw.get("team_spawn"))
    iid = str(raw.get("id") or f"spont_{idx}").strip()[:48] or f"spont_{idx}"
    out: dict[str, Any] = {
        "id": iid,
        "label": label,
        "sourceText": source,
        "hint": hint or ("Team L1" if team else "spontané"),
    }
    if team:
        out["teamSpawn"] = True
        obj = str(raw.get("teamObjective") or raw.get("team_objective") or source).strip()[:400]
        if obj:
            out["teamObjective"] = obj
        role = str(raw.get("teamRole") or raw.get("team_role") or "qa").strip()[:24]
        out["teamRole"] = role or "qa"
    return out


def _validate_proposal(
    parsed: dict[str, Any],
    *,
    fallback: dict[str, Any],
    mode: str,
) -> dict[str, Any] | None:
    message = str(parsed.get("message") or "").strip()
    message = re.sub(r"\s+", " ", message)
    if len(message) < 16 or len(message) > 280:
        return None
    if _FORBIDDEN_RE.search(message):
        return None
    if re.search(r"(?i)en tant qu['\u2019]?ia|as an ai", message):
        return None

    themes = []
    for t in parsed.get("themes") or []:
        s = str(t).strip().lower()[:40]
        if s and s not in themes:
            themes.append(s)
        if len(themes) >= 5:
            break

    if mode == "message_only":
        intents = list(fallback.get("intents") or [])
    else:
        intents = []
        raw_intents = parsed.get("intents") if isinstance(parsed.get("intents"), list) else []
        for i, it in enumerate(raw_intents[:3]):
            cleaned = _sanitize_intent(it if isinstance(it, dict) else {}, i)
            if cleaned:
                intents.append(cleaned)
        if not intents:
            # keep at least fallback intents if LLM forgot
            intents = list(fallback.get("intents") or [])[:2]
        intents = intents[:2]

    if not intents:
        return None

    seed = parsed.get("evolution_seed")
    evolution_seed = None
    if isinstance(seed, str) and 12 <= len(seed.strip()) <= 160 and not _FORBIDDEN_RE.search(seed):
        evolution_seed = seed.strip()

    return {
        "message": message,
        "themes": themes,
        "intents": intents,
        "primary": intents[0],
        "evolution_seed": evolution_seed,
        "spontaneous": True,
    }


def _ollama_light_url() -> str:
    for key in (
        "LBG_SPONTANEITY_OLLAMA_URL",
        "LBG_PROBE_OLLAMA_LIGHT_URL",
        "OLLAMA_LIGHT_BASE_URL",
    ):
        v = os.getenv(key, "").strip()
        if v:
            return v.rstrip("/")
    try:
        from src.settings import get_settings

        s = get_settings()
        u = str(getattr(s, "probe_ollama_light_url", "") or "").rstrip("/")
        if u:
            return u
    except Exception:
        pass
    return "http://192.168.0.111:11434"


def _ollama_model() -> str:
    return (
        os.getenv("LBG_SPONTANEITY_MODEL", "").strip()
        or os.getenv("LBG_REFLECTION_MODEL", "").strip()
        or "qwen2.5:3b"
    )


def _build_user_prompt(offer: dict[str, Any], *, mode: str, st: dict[str, Any], dials: dict[str, float] | None) -> str:
    avoid = _themes_to_avoid(st)
    liked = _liked_themes(st)
    seeds = [
        str(s.get("text") or "")
        for s in (st.get("evolution_seeds") or [])[-5:]
        if isinstance(s, dict) and s.get("text")
    ]
    dials_bit = ""
    if dials:
        dials_bit = (
            f"Dials: humour={dials.get('humour', 0):.2f} piquant={dials.get('piquant', 0):.2f} "
            f"enthousiasme={dials.get('enthousiasme', 0):.2f}\n"
        )
    ctx = offer.get("context") if isinstance(offer.get("context"), dict) else {}
    return (
        f"mode={mode}\n"
        f"signal_id={offer.get('id')}\n"
        f"kind={offer.get('kind')} offerType={offer.get('offerType')}\n"
        f"message_heuristique={offer.get('message')}\n"
        f"intents_heuristiques={json.dumps(offer.get('intents') or [], ensure_ascii=False)[:900]}\n"
        f"self_line={ctx.get('self_line') or ''}\n"
        f"goal={ctx.get('goal_title') or ''}\n"
        f"{dials_bit}"
        f"À éviter (récent / dismiss) : {', '.join(avoid) or '—'}\n"
        f"Thèmes aimés : {', '.join(liked) or '—'}\n"
        f"Seeds évolution : {'; '.join(seeds) or '—'}\n"
        "Propose quelque chose de SPONTANÉ, utile au studio LBG (Compagnon / Team / LAN / craft)."
    )


async def _call_llm(user_prompt: str) -> tuple[dict[str, Any] | None, float, str]:
    import httpx

    base = _ollama_light_url()
    model = _ollama_model()
    body = {
        "model": model,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.85, "top_p": 0.92, "num_predict": 280},
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": user_prompt[:3500]},
        ],
    }
    t0 = time.monotonic()
    try:
        timeout = httpx.Timeout(connect=3.0, read=18.0, write=5.0, pool=3.0)
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
        parsed = _parse_json_blob(content)
        ms = (time.monotonic() - t0) * 1000
        return parsed, ms, "ollama_light"
    except Exception as e:
        logger.info("spontaneity llm failed: %s", e)
        return None, (time.monotonic() - t0) * 1000, "error"


def _load_dials_safe() -> dict[str, float] | None:
    try:
        from src.services.character_layer import load_dials

        return load_dials(lab=True)
    except Exception:
        try:
            import character_layer as cl

            return cl.load_dials(lab=True)
        except Exception:
            return None


def _record_shown(st: dict[str, Any], *, offer_id: str, message: str, themes: list[str]) -> None:
    st.setdefault("shown", []).append(
        {
            "id": offer_id,
            "title": message[:120],
            "themes": themes[:5],
            "ts": time.time(),
        }
    )


def promote_threshold() -> float:
    try:
        return float(os.getenv("LBG_SPONTANEITY_PROMOTE_SCORE", "1.0").strip() or "1.0")
    except ValueError:
        return 1.0


def _seed_will_id(text: str) -> str:
    import hashlib

    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
    return f"evo:{digest}"


def _orch_will_url() -> str:
    """Préfère Pilot proxy ; sinon orch direct."""
    pilot = os.getenv("LBG_PILOT_BASE_URL", "").strip().rstrip("/")
    if pilot:
        return f"{pilot}/v1/pilot/orchestrator/self/will"
    orch = (
        os.getenv("LBG_ORCHESTRATOR_URL", "").strip()
        or os.getenv("LBG_ORCHESTRATOR_SELF_URL", "").strip()
        or "http://192.168.0.140:8010"
    ).rstrip("/")
    return f"{orch}/v1/self/will"


def _push_will_to_self(seed: dict[str, Any]) -> dict[str, Any]:
    """HTTP sync → Self pending_will. Best-effort."""
    import httpx

    text = str(seed.get("text") or "").strip()
    if len(text) < 12:
        return {"ok": False, "reason": "empty"}
    will_id = str(seed.get("will_id") or _seed_will_id(text))
    body = {
        "id": will_id,
        "title": text[:120],
        "summary": f"Seed évolution spontanée (score {float(seed.get('score') or 0):.1f}).",
        "kind": "evolution",
        "source": "spontaneity",
        "meta": {
            "from_id": seed.get("from_id") or "",
            "score": float(seed.get("score") or 0),
        },
    }
    url = _orch_will_url()
    try:
        with httpx.Client(timeout=httpx.Timeout(connect=2.0, read=6.0, write=3.0, pool=2.0)) as client:
            r = client.post(url, json=body)
        if r.status_code != 200:
            return {"ok": False, "reason": f"http_{r.status_code}", "body": r.text[:200], "url": url}
        data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        return {"ok": True, "will_id": will_id, "url": url, "remote": data}
    except Exception as e:
        logger.info("spontaneity promote self failed: %s", e)
        return {"ok": False, "reason": f"{type(e).__name__}: {e}", "url": url}


def promote_ready_seeds(*, force: bool = False) -> dict[str, Any]:
    """Pousse les seeds scorées vers Self pending_will (anti-doublon promoted_ts)."""
    thr = promote_threshold()
    promoted: list[dict[str, Any]] = []
    skipped: list[str] = []
    with _lock:
        st = load_state()
        seeds = st.setdefault("evolution_seeds", [])
        for seed in seeds:
            if not isinstance(seed, dict):
                continue
            text = str(seed.get("text") or "").strip()
            if len(text) < 12:
                continue
            score = float(seed.get("score") or 0)
            if not force and score < thr:
                skipped.append(text[:40])
                continue
            if seed.get("promoted_ts") and not force:
                skipped.append(f"already:{text[:40]}")
                continue
            result = _push_will_to_self(seed)
            if result.get("ok"):
                seed["promoted_ts"] = time.time()
                seed["will_id"] = result.get("will_id")
                seed["pending"] = False
                promoted.append({"text": text[:80], "will_id": result.get("will_id"), "score": score})
            else:
                skipped.append(f"fail:{result.get('reason')}:{text[:30]}")
        if promoted:
            persist_state(st)
        snap = evolution_snapshot(st)
    snap["promoted"] = promoted
    snap["skipped"] = skipped[:12]
    snap["promote_threshold"] = thr
    return snap


def record_feedback(
    *,
    offer_id: str,
    kind: str,
    themes: list[str] | None = None,
    message: str | None = None,
    evolution_seed: str | None = None,
) -> dict[str, Any]:
    """Accept / dismiss → scores thèmes + seeds d'évolution + promote Self."""
    fb = "accept" if str(kind).lower() in ("accept", "ok", "yes", "agir") else "dismiss"
    themes = [str(t).strip().lower()[:40] for t in (themes or []) if str(t).strip()]
    with _lock:
        st = load_state()
        st.setdefault("feedback", []).append(
            {
                "id": offer_id,
                "kind": fb,
                "themes": themes,
                "message": (message or "")[:160],
                "ts": time.time(),
            }
        )
        scores = st.setdefault("theme_scores", {})
        delta = 1.0 if fb == "accept" else -1.0
        for t in themes or ["untagged"]:
            scores[t] = float(scores.get(t) or 0) + delta
        if fb == "accept" and evolution_seed:
            seed_text = evolution_seed.strip()[:160]
            seeds = st.setdefault("evolution_seeds", [])
            existing = next((s for s in seeds if isinstance(s, dict) and s.get("text") == seed_text), None)
            if existing:
                existing["score"] = float(existing.get("score") or 0) + 1.0
                existing["ts"] = time.time()
                existing.pop("pending", None)
            else:
                seeds.append(
                    {
                        "text": seed_text,
                        "score": 1.0,
                        "from_id": offer_id,
                        "ts": time.time(),
                    }
                )
        elif fb == "accept" and message and len(message) >= 20:
            tip = f"Réitérer l'esprit : {message[:100]}"
            seeds = st.setdefault("evolution_seeds", [])
            if not any(isinstance(s, dict) and tip[:40] in str(s.get("text") or "") for s in seeds):
                seeds.append({"text": tip, "score": 0.5, "from_id": offer_id, "ts": time.time()})
        persist_state(st)

    snap = evolution_snapshot()
    if fb == "accept":
        try:
            promo = promote_ready_seeds()
            snap["promoted"] = promo.get("promoted") or []
            snap["promote_threshold"] = promo.get("promote_threshold")
        except Exception as e:
            logger.info("promote after feedback: %s", e)
            snap["promoted"] = []
    return snap


async def propose_spontaneous(offer: dict[str, Any]) -> dict[str, Any]:
    """Enrichit une offre heuristique. Fallback = offre d'origine."""
    base = {
        "ok": True,
        "spontaneous": False,
        "source": "heuristic",
        "spice_mode": "off",
        "message": offer.get("message"),
        "intents": offer.get("intents") or [],
        "primary": offer.get("primary") or (offer.get("intents") or [None])[0],
        "themes": [],
        "evolution_seed": None,
        "latency_ms": 0.0,
        "id": offer.get("id"),
    }
    if not spontaneity_enabled():
        base["reason"] = "disabled"
        return base
    if not offer.get("offer") and not offer.get("message"):
        base["ok"] = False
        base["reason"] = "no_offer"
        return base

    mode = spice_mode_for(offer)
    cache_key = f"{offer.get('id')}|{mode}|{str(offer.get('message') or '')[:80]}"

    with _lock:
        st = load_state()
        cached = (st.get("cache") or {}).get(cache_key)
        if isinstance(cached, dict) and float(cached.get("exp") or 0) > time.time():
            hit = deepcopy(cached.get("result") or {})
            hit["source"] = "cache"
            hit["ok"] = True
            return hit

    dials = _load_dials_safe()
    user_prompt = _build_user_prompt(offer, mode=mode, st=st, dials=dials)
    parsed, ms, src = await _call_llm(user_prompt)
    if not parsed:
        base["source"] = src
        base["latency_ms"] = ms
        base["spice_mode"] = mode
        base["reason"] = "llm_unavailable"
        return base

    validated = _validate_proposal(parsed, fallback=offer, mode=mode)
    if not validated:
        base["source"] = src
        base["latency_ms"] = ms
        base["spice_mode"] = mode
        base["reason"] = "invalid_llm"
        return base

    out = {
        "ok": True,
        "spontaneous": True,
        "source": src,
        "spice_mode": mode,
        "message": validated["message"],
        "intents": validated["intents"],
        "primary": validated["primary"],
        "themes": validated["themes"],
        "evolution_seed": validated.get("evolution_seed"),
        "latency_ms": ms,
        "id": offer.get("id"),
        "kind": offer.get("kind"),
        "offerType": offer.get("offerType"),
        "goal": offer.get("goal"),
        "fromSelf": offer.get("fromSelf"),
    }

    with _lock:
        st = load_state()
        _record_shown(
            st,
            offer_id=str(offer.get("id") or "unknown"),
            message=out["message"],
            themes=list(out.get("themes") or []),
        )
        st.setdefault("cache", {})[cache_key] = {
            "exp": time.time() + cache_ttl_s(),
            "result": {k: v for k, v in out.items() if k != "latency_ms"},
        }
        # optional: stash evolution_seed as pending (score 0 until accept)
        seed = out.get("evolution_seed")
        if seed:
            seeds = st.setdefault("evolution_seeds", [])
            if not any(isinstance(s, dict) and s.get("text") == seed for s in seeds):
                seeds.append(
                    {
                        "text": seed,
                        "score": 0.0,
                        "pending": True,
                        "from_id": offer.get("id"),
                        "ts": time.time(),
                    }
                )
        persist_state(st)

    return out


def reset_state_for_tests() -> None:
    path = state_path()
    if path.is_file():
        path.unlink()
