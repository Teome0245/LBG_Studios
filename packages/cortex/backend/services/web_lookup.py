"""Lookup web serveur pour le chat Orch (autonomie — anti-interrogatoire).

Injecté par le proxy Pilot ``POST /v1/pilot/orch/ask`` : recherche bornée
(Wikipedia FR + DuckDuckGo Instant Answer), puis préfixe du prompt amont.
"""

from __future__ import annotations

import os
import re
import time
from typing import Any
from urllib.parse import quote

import httpx

_UA = "LBG-Studios-Cortex/1.0 (pilot web_lookup; +https://github.com/Teome0245/LBG_Studios)"

_OPS_BLOCK = re.compile(
    r"(?i)\b("
    r"team\s*:|mission\s*:|campus\s*:|cursor\s*:|"
    r"healthz|selfcheck|systemd|deploy|ollama|"
    r"\.110|\.111|pilot\s+#|smoke\s+lan|"
    r"ouvre|ouvrir|lance|lancer|notepad|vghd|desktop"
    r")\b"
)

_LOOKUP_INTENT = re.compile(
    r"(?i)\b("
    r"cherche|chercher|recherche|rechercher|trouve|trouver|"
    r"retrouver|identifier|c['\u2019]est\s+quoi|qui\s+est|"
    r"quel\s+(?:est\s+)?(?:le\s+)?titre|aide[- ]?moi\s+[àa]\s+(?:le\s+)?trouver"
    r")\b"
)

_CULTURE = re.compile(
    r"(?i)\b("
    r"film|films|animation|anim[eé]|dessin\s+anim[eé]|cartoon|"
    r"s[eé]rie|series|manga|anime|livre|roman|bande\s+dessin[eé]e|bd|"
    r"acteur|actrice|r[eé]alisateur|chanson|album|jeu\s+vid[eé]o|"
    r"titre|personnage|h[eé]ros"
    r")\b"
)

_QUOTED = re.compile(r"[«\"“]([^»\"”]{3,120})[»\"”]")
_AFTER_VERB = re.compile(
    r"(?i)(?:cherche|chercher|recherche|rechercher|trouve|trouver|retrouver)"
    r"(?:\s+(?:un|une|le|la|les|du|de|des|ce|cet|cette))?"
    r"\s+(.+)$"
)


def web_lookup_enabled() -> bool:
    raw = os.environ.get("LBG_ORCH_WEB_LOOKUP", "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


def wants_web_lookup(prompt: str) -> bool:
    text = (prompt or "").strip()
    if len(text) < 12:
        return False
    if _OPS_BLOCK.search(text):
        return False
    if _LOOKUP_INTENT.search(text) and _CULTURE.search(text):
        return True
    if _CULTURE.search(text) and _QUOTED.search(text):
        return True
    if _LOOKUP_INTENT.search(text) and _QUOTED.search(text):
        return True
    return False


_TITLEISH = re.compile(
    r"\b((?:[Ll]e|[Ll]a|[Ll]es|[Ll]['\u2019])\s+[A-ZÉÈÊÀÂÎÔÛÄÖÜ][\w'’\-]+(?:\s+[\w'’\-À-ÿ]+){1,14})"
)
_CULTURE_PREFIX = re.compile(
    r"(?i)^(un|une|le|la|les|du|de|des|ce|cet|cette)?\s*"
    r"(?:vieux|vieille|ancien|ancienne|petit|petite)?\s*"
    r"(?:film|films|animation|anim[eé]|dessin\s+anim[eé]|s[eé]rie|livre|titre)"
    r"(?:\s+d['\u2019]animation)?\s*[:\-–,]?\s*"
)


def extract_lookup_query(prompt: str) -> str:
    text = (prompt or "").strip()
    if not text:
        return ""
    m = _QUOTED.search(text)
    if m:
        return m.group(1).strip()[:220]

    # Titre type « Le Voyage d'Edgar… » n'importe où dans le message
    titles = _TITLEISH.findall(text)
    if titles:
        # Préférer le plus long (souvent le titre complet)
        best = max((t.strip(" ?!.…,:;") for t in titles), key=len)
        if len(best) >= 8:
            return best[:220]

    # Après « : » — souvent le titre candidat
    if ":" in text:
        after = text.rsplit(":", 1)[-1].strip(" ?!.…")
        after = _CULTURE_PREFIX.sub("", after).strip()
        if len(after) >= 8:
            return after[:220]

    # Dernière phrase / fragment capitalisé après « ? » souvent = titre candidat
    parts = re.split(r"[?!.]\s+", text)
    for part in reversed(parts):
        p = part.strip(" ?!.…")
        if len(p) < 8:
            continue
        if re.search(r"[A-ZÉÈÊÀÂÎÔÛÄÖÜ][\w'’\-]+(?:\s+[\w'’\-]+){2,}", p):
            # Évite de garder toute la politesse
            if not re.match(r"(?i)^(bonjour|salut|hello|merci|svp|s['\u2019]il)", p):
                cleaned = re.sub(
                    r"(?i)^(je\s+)?(cherche|recherche|trouve)\s+",
                    "",
                    p,
                ).strip()
                cleaned = _CULTURE_PREFIX.sub("", cleaned).strip()
                if len(cleaned) >= 8:
                    return cleaned[:220]
    m2 = _AFTER_VERB.search(text)
    if m2:
        q = m2.group(1).strip()
        q = _CULTURE_PREFIX.sub("", q).strip()
        q = re.sub(r"(?i)^(un|une|le|la|les|du|de|des)\s+", "", q).strip()
        q = re.sub(r"[?!.…]+$", "", q).strip()
        if len(q) >= 6:
            return q[:220]
    return text[:220]


def format_web_lookup_grounding(
    *,
    query: str,
    hits: list[dict[str, str]],
    sources: list[str],
) -> str:
    """Bloc compact **sans sauts de ligne** — Orch traite les multi-lignes comme command_batch."""
    if hits:
        consignes = (
            "Consignes: utilise les hits web ci-dessous; "
            "réponds avec 1 à 3 hypothèses étiquetées (probable/possible/douteux); "
            "au plus une question courte; interdit interrogatoire."
        )
        bits: list[str] = []
        for h in hits[:6]:
            title = (h.get("title") or "").strip() or "(sans titre)"
            snippet = (h.get("snippet") or "").strip()
            url = (h.get("url") or "").strip()
            piece = title
            if snippet:
                piece += f" — {snippet[:160]}"
            if url:
                piece += f" ({url})"
            bits.append(piece)
        hits_txt = " | ".join(bits)
    else:
        consignes = (
            "Consignes: aucun hit web; propose 1 à 3 hypothèses étiquetées comme telles; "
            "au plus une question; interdit interrogatoire."
        )
        hits_txt = "(aucun hit)"
    src = ",".join(sources) if sources else "aucune"
    return (
        f"(Contexte recherche web query=«{query}» sources={src}) "
        f"{consignes} Hits: {hits_txt}"
    )


async def _wiki_opensearch(client: httpx.AsyncClient, query: str) -> list[dict[str, str]]:
    url = (
        "https://fr.wikipedia.org/w/api.php"
        f"?action=opensearch&search={quote(query)}&limit=5&namespace=0&format=json"
    )
    r = await client.get(url, headers={"User-Agent": _UA, "Accept": "application/json"})
    if r.status_code != 200:
        return []
    data = r.json()
    if not isinstance(data, list) or len(data) < 4:
        return []
    titles = data[1] if isinstance(data[1], list) else []
    descs = data[2] if isinstance(data[2], list) else []
    urls = data[3] if isinstance(data[3], list) else []
    out: list[dict[str, str]] = []
    for i, title in enumerate(titles[:5]):
        out.append(
            {
                "title": str(title),
                "snippet": str(descs[i]) if i < len(descs) else "",
                "url": str(urls[i]) if i < len(urls) else "",
                "source": "wikipedia_fr",
            }
        )
    return out


async def _ddg_instant(client: httpx.AsyncClient, query: str) -> list[dict[str, str]]:
    url = f"https://api.duckduckgo.com/?q={quote(query)}&format=json&no_html=1&skip_disambig=1"
    r = await client.get(url, headers={"User-Agent": _UA, "Accept": "application/json"})
    if r.status_code != 200:
        return []
    try:
        data = r.json()
    except Exception:
        return []
    if not isinstance(data, dict):
        return []
    out: list[dict[str, str]] = []
    heading = str(data.get("Heading") or "").strip()
    abstract = str(data.get("AbstractText") or data.get("Abstract") or "").strip()
    abs_url = str(data.get("AbstractURL") or "").strip()
    if heading or abstract:
        out.append(
            {
                "title": heading or "DuckDuckGo",
                "snippet": abstract[:400],
                "url": abs_url,
                "source": "duckduckgo",
            }
        )
    related = data.get("RelatedTopics")
    if isinstance(related, list):
        for item in related[:4]:
            if not isinstance(item, dict):
                continue
            text = str(item.get("Text") or "").strip()
            first_url = ""
            first = item.get("FirstURL")
            if isinstance(first, str):
                first_url = first
            if text:
                out.append(
                    {
                        "title": text.split(" - ", 1)[0][:120],
                        "snippet": text[:280],
                        "url": first_url,
                        "source": "duckduckgo",
                    }
                )
    return out


def _dedupe_hits(hits: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for h in hits:
        key = (h.get("title") or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(h)
    return out


async def fetch_web_lookup(query: str, *, timeout_s: float = 4.0) -> dict[str, Any]:
    q = (query or "").strip()
    t0 = time.monotonic()
    if not q:
        return {"ok": False, "query": "", "hits": [], "sources": [], "ms": 0.0, "error": "empty_query"}
    hits: list[dict[str, str]] = []
    sources: list[str] = []
    errors: list[str] = []
    try:
        async with httpx.AsyncClient(timeout=timeout_s, follow_redirects=True) as client:
            try:
                wiki = await _wiki_opensearch(client, q)
                if wiki:
                    hits.extend(wiki)
                    sources.append("wikipedia_fr")
            except Exception as e:
                errors.append(f"wikipedia:{type(e).__name__}")
            try:
                ddg = await _ddg_instant(client, q)
                if ddg:
                    hits.extend(ddg)
                    sources.append("duckduckgo")
            except Exception as e:
                errors.append(f"duckduckgo:{type(e).__name__}")
    except Exception as e:
        return {
            "ok": False,
            "query": q,
            "hits": [],
            "sources": [],
            "ms": round((time.monotonic() - t0) * 1000, 1),
            "error": f"{type(e).__name__}: {e}",
        }
    hits = _dedupe_hits(hits)
    return {
        "ok": bool(hits),
        "query": q,
        "hits": hits[:6],
        "sources": sources,
        "ms": round((time.monotonic() - t0) * 1000, 1),
        "error": "; ".join(errors) if errors and not hits else None,
    }


def format_direct_lookup_reply(*, query: str, hits: list[dict[str, str]], sources: list[str]) -> str:
    """Réponse déterministe quand des hits web existent — évite ask_user Orch."""
    if not hits:
        return (
            f"Je n’ai pas trouvé de source fiable pour « {query} ». "
            "Donne un détail mémorable (époque, pays, scène) — une seule piste suffit."
        )
    top = hits[0]
    title = (top.get("title") or query).strip()
    snippet = (top.get("snippet") or "").strip()
    url = (top.get("url") or "").strip()
    src = ",".join(sources) if sources else "web"
    lines = [
        f"Probable : **{title}**",
    ]
    if snippet:
        lines.append(snippet[:320])
    if url:
        lines.append(f"Source ({src}) : {url}")
    alts = [h for h in hits[1:3] if (h.get("title") or "").strip()]
    if alts:
        alt_txt = "; ".join(
            f"{(h.get('title') or '').strip()}"
            + (f" ({h.get('url')})" if h.get("url") else "")
            for h in alts
        )
        lines.append(f"Autres pistes : {alt_txt}")
    lines.append("Si ce n’est pas ça, un seul détail en plus (année, pays, scène) suffit.")
    return "\n".join(lines)


async def enrich_ask_prompt(prompt: str) -> tuple[str, dict[str, Any] | None]:
    """Si intention lookup : contexte web + meta (hits) pour réponse directe éventuelle."""
    if not web_lookup_enabled() or not wants_web_lookup(prompt):
        return prompt, None
    query = extract_lookup_query(prompt)
    result = await fetch_web_lookup(query)
    hits_raw = result.get("hits") if isinstance(result.get("hits"), list) else []
    hits: list[dict[str, str]] = [h for h in hits_raw if isinstance(h, dict)]
    sources = list(result.get("sources") or []) if isinstance(result.get("sources"), list) else []
    block = format_web_lookup_grounding(query=query, hits=hits, sources=sources)
    user = " ".join((prompt or "").split())
    enriched = f"{user} — {block}"
    meta: dict[str, Any] = {
        "query": query,
        "hit_count": len(hits),
        "sources": sources,
        "ms": result.get("ms"),
        "ok": bool(result.get("ok")),
        "error": result.get("error"),
        "hits": hits[:6],
        "direct_reply": format_direct_lookup_reply(query=query, hits=hits, sources=sources)
        if hits
        else None,
    }
    return enriched, meta
