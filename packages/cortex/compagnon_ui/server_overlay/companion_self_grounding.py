"""Ancrage Self — injecte conscience studio (drives / intent / memory_refs) dans le chat.

Best-effort HTTP vers Pilot `.140` (proxy slim) ou Orch direct.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

logger = logging.getLogger("lbg.companion_self_grounding")

_SELF_HINTS = re.compile(
    r"(?i)("
    r"\b(ta|ma|sa|notre)\s+(mémoire|memoire)\b|"
    r"\b(mémoire|memoire)\s+(agent|self|équipe|equipe|studio)\b|"
    r"\b(conscience|self[\s_-]?state|pending[_\s-]?will)\b|"
    r"\b(leçons?\s+apprises|lessons[_\s-]?learned|memory_refs)\b|"
    r"\b(curiosité|curiosite|tension|envies?|buts?\s+internes?)\b|"
    r"\bce\s+que\s+tu\s+(sais|retiens|connais)\b"
    r")"
)


def wants_self_memory_context(prompt: str) -> bool:
    return bool(_SELF_HINTS.search(prompt or ""))


def _orch_self_urls() -> list[str]:
    urls: list[str] = []
    pilot = (
        os.getenv("CORTEX_PILOT_URL", "").strip()
        or os.getenv("LBG_PILOT_BASE_URL", "").strip()
    ).rstrip("/")
    if pilot:
        urls.append(f"{pilot}/v1/pilot/orchestrator/self/status?ensure_goals=0")
    orch = (
        os.getenv("CORTEX_ORCH_URL", "").strip()
        or os.getenv("LBG_ORCHESTRATOR_URL", "").strip()
        or os.getenv("LBG_ORCHESTRATOR_SELF_URL", "").strip()
        or "http://192.168.0.140:8010"
    ).rstrip("/")
    urls.append(f"{orch}/v1/self/status?ensure_goals=0")
    # dédup en conservant l'ordre
    seen: set[str] = set()
    out: list[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


async def load_self_status(*, timeout_s: float = 2.5) -> dict[str, Any] | None:
    """Charge Self slim. None si indispo / désactivé."""
    try:
        import httpx
    except ImportError:  # pragma: no cover
        return None

    last_err: str | None = None
    for url in _orch_self_urls():
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(connect=1.2, read=timeout_s, write=1.5, pool=1.0)
            ) as client:
                r = await client.get(url)
            if r.status_code != 200:
                last_err = f"http_{r.status_code}"
                continue
            data = r.json()
            if not isinstance(data, dict):
                continue
            if data.get("ok") is False:
                last_err = str(data.get("error") or "ok_false")
                continue
            return data
        except Exception as exc:  # pragma: no cover — réseau
            last_err = f"{type(exc).__name__}: {exc}"
            continue
    if last_err:
        logger.debug("self status unavailable: %s", last_err)
    return None


def _pct(v: object) -> str | None:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    if x <= 1.0:
        x *= 100.0
    return f"{int(round(x))}%"


def format_self_grounding(
    payload: dict[str, Any] | None,
    *,
    compact: bool = False,
) -> str:
    """Bloc système compact — faits Self uniquement."""
    if not payload:
        return ""
    enabled = payload.get("enabled")
    state = payload.get("state") if isinstance(payload.get("state"), dict) else {}
    if not state and not enabled:
        return ""

    identity = state.get("identity") if isinstance(state.get("identity"), dict) else {}
    drives = state.get("drives") if isinstance(state.get("drives"), dict) else {}
    intent = state.get("intent") if isinstance(state.get("intent"), dict) else {}
    refs = state.get("memory_refs") if isinstance(state.get("memory_refs"), dict) else {}
    will = state.get("pending_will") if isinstance(state.get("pending_will"), list) else []
    name = str(identity.get("display_name") or "Cortex")
    mode = str(identity.get("mode") or "studio")
    incarn = identity.get("incarnations") if isinstance(identity.get("incarnations"), dict) else {}
    studio = incarn.get("studio") or "lyra"
    mmo = incarn.get("mmo") or "lia"
    primary = str(intent.get("primary") or "monitor")
    narrative = str(intent.get("narrative") or "").strip()[:80]

    gauge_bits: list[str] = []
    for key, label in (
        ("curiosity", "curiosité"),
        ("tension", "tension"),
        ("social_hunger", "social"),
        ("confidence", "confiance"),
    ):
        p = _pct(drives.get(key))
        if p is not None:
            gauge_bits.append(f"{label} {p}")

    lessons_n = refs.get("lessons_count")
    last_lesson = refs.get("last_lesson_id")
    goals_n = state.get("goals_active_count")
    if goals_n is None:
        goals = state.get("goals") if isinstance(state.get("goals"), list) else []
        active_goals = [
            g
            for g in goals
            if isinstance(g, dict)
            and str(g.get("status") or "").lower() in ("active", "pending", "open")
        ]
        # Fallback orch brut : ne jamais compter les thousands de goals done
        goals_n = len(active_goals)

    if compact:
        bits = [f"SELF {name}", f"intent={primary}"]
        if gauge_bits[:2]:
            bits.append(" · ".join(gauge_bits[:2]))
        if isinstance(lessons_n, int) and lessons_n >= 0:
            bits.append(f"{lessons_n} leçons")
        return " · ".join(bits)

    lines = [
        "SELF (conscience studio — faits internes, ne pas inventer hors de ce bloc) :",
        f"- identité : {name} · mode {mode} · incarnations studio={studio} / mmo={mmo}",
        f"- intent : {primary}" + (f" — {narrative}" if narrative else ""),
    ]
    if gauge_bits:
        lines.append(f"- drives : {' · '.join(gauge_bits)}")
    mem_bits: list[str] = []
    if isinstance(lessons_n, int):
        mem_bits.append(f"{lessons_n} leçons")
    if last_lesson:
        mem_bits.append(f"dernier={str(last_lesson)[:24]}")
    if mem_bits:
        lines.append(f"- mémoire agent : {' · '.join(mem_bits)} (≠ RAM VM)")
    else:
        lines.append("- mémoire agent : refs indisponibles (≠ RAM VM)")
    lines.append(
        f"- envies pending : {len(will)} · buts actifs : {int(goals_n) if goals_n is not None else 0}"
    )
    if enabled is False:
        lines.append("- flag Self : désactivé (projection lecture seule / défaut)")
    return "\n".join(lines)
