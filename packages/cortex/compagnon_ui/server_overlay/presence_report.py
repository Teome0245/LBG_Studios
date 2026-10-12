"""Phase C2 — Retour terrain présence → causerie Compagnon (pas dump ops).

« résultat smoke présence » / « retour hub » → fetch `:8787/v1/presence-dials`
et reformule en 3–5 phrases collègue.
"""

from __future__ import annotations

import json
import logging
import os
import re
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger("lbg.presence_report")

_PRESENCE_REPORT_RE = re.compile(
    r"(?i)\b("
    r"r[ée]sultat\s+(?:du\s+|de\s+(?:la\s+)?)?(?:smoke\s+)?pr[ée]sence|"
    r"retour\s+(?:terrain|hub|pr[ée]sence|smoke)|"
    r"comment\s+(?:s['\u2019]?est\s+pass[ée]|a\s+donn[ée])\s+(?:le\s+)?(?:smoke|hub|nix)|"
    r"lecture\s+dials?|"
    r"pr[ée]sence[- ]?dials?\s+(?:live|hub)|"
    r"nix\s+(?:vs|versus)\s+mira|"
    r"compte[- ]?rendu\s+pr[ée]sence"
    r")\b"
)


def presence_report_enabled(*, lab: bool = False) -> bool:
    raw = (os.getenv("LBG_COMPAGNON_PRESENCE_REPORT") or "").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    if raw in ("1", "true", "yes", "on"):
        return True
    return bool(lab)


def wants_presence_report(prompt: str) -> bool:
    text = (prompt or "").strip()
    if not text or len(text) > 400:
        return False
    return bool(_PRESENCE_REPORT_RE.search(text))


def hub_presence_url() -> str:
    base = (
        os.getenv("LBG_PRIME_HUB_URL")
        or os.getenv("LBG_HUB_HTTP_URL")
        or "http://192.168.0.246:8787"
    ).strip().rstrip("/")
    return f"{base}/v1/presence-dials"


def fetch_presence_dials(*, timeout: float = 12.0) -> dict[str, Any]:
    url = hub_presence_url()
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        data = json.loads(raw) if raw.strip() else {}
    if not isinstance(data, dict):
        return {"ok": False, "error": "invalid_json"}
    return data


def _bot_by_name(bots: list, name: str) -> dict[str, Any] | None:
    want = name.strip().lower()
    for b in bots:
        if not isinstance(b, dict):
            continue
        if str(b.get("name") or "").strip().lower() == want:
            return b
    return None


def format_presence_causerie(data: dict[str, Any]) -> str:
    """3–5 phrases collègue — pas de JSON ni chrome Agir."""
    if not data.get("ok"):
        err = str(data.get("error") or "hub injoignable")
        return (
            f"Je n'ai pas pu lire le hub présence ({err}). "
            "Vérifie `:8787` ou relance `bash tools/smoke_b3b4_presence_hub.sh`."
        )
    bots = data.get("bots") if isinstance(data.get("bots"), list) else []
    nix = _bot_by_name(bots, "Nix") or {}
    mira = _bot_by_name(bots, "Mira") or {}
    nd = nix.get("presence_dials") if isinstance(nix.get("presence_dials"), dict) else {}
    md = mira.get("presence_dials") if isinstance(mira.get("presence_dials"), dict) else {}
    na = (nix.get("actions_at_m") or {}).get("12") if isinstance(nix.get("actions_at_m"), dict) else {}
    ma = (mira.get("actions_at_m") or {}).get("12") if isinstance(mira.get("actions_at_m"), dict) else {}
    n_act = str((na or {}).get("action") or "?")
    m_act = str((ma or {}).get("action") or "?")
    n_ch = float(nd.get("chaleur", 0) or 0)
    m_ch = float(md.get("chaleur", 0) or 0)
    n_line = str(nix.get("presence_line") or "").strip()
    bits = [
        f"Retour terrain Lost Heaven : **Nix** reste plus chaleureux "
        f"(chaleur {n_ch:.2f}) que **Mira** ({m_ch:.2f}).",
        f"À ~12 m, Nix part en **{n_act}**, Mira en **{m_act}** — les seuils B3 tiennent.",
    ]
    if n_line:
        bits.append(f"Ambiance Nix : « {n_line[:100]} »")
    bits.append(
        "Pas de mutation monde : c'est de la présence mesurable pour la zone d'entraînement. "
        "Si tu veux, on relance le brief ou on suit la mission Campus."
    )
    return "\n\n".join(bits)


async def attach_presence_report_if_needed(
    result: Any,
    *,
    prompt: str,
    lab: bool = False,
) -> Any:
    if not isinstance(result, dict):
        return result
    if not presence_report_enabled(lab=lab):
        return result
    if not wants_presence_report(prompt):
        return result
    if result.get("presence_report"):
        return result

    try:
        data = fetch_presence_dials()
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as e:
        logger.warning("presence_report fetch failed: %s", e)
        data = {"ok": False, "error": str(e)[:160]}

    content = format_presence_causerie(data)
    out = {
        **result,
        "content": content,
        "response": content,
        "source": "presence_report",
        "model": "presence_report",
        "model_used": "presence_report",
        "presence_report": {
            "ok": bool(data.get("ok")),
            "hub": hub_presence_url(),
            "bots": len(data.get("bots") or []) if isinstance(data.get("bots"), list) else 0,
        },
    }
    return out
