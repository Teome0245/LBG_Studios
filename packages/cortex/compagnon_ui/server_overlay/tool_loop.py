"""
P2 — Boucle outils légère + timeline.

Outils LAN disponibles (pas de shell arbitraire) :
  - team_status
  - ollama_audit
  - providers_catalog
  - cursor_health
"""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Any, Callable, Awaitable

from src.http_timeouts import httpx_timeout
from src.settings import Settings, get_settings

logger = logging.getLogger("lbg.router.tool_loop")

ToolFn = Callable[..., Awaitable[dict[str, Any]]]


def tool_loop_enabled() -> bool:
    return os.getenv("LBG_TOOL_LOOP_ENABLED", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def wants_tool_loop(prompt: str) -> bool:
    # 1.1 — causerie design / collègue : jamais armer les outils infra
    try:
        from src.services.chat_intent import is_companion_chat, is_design_brainstorm
    except ImportError:  # pragma: no cover
        try:
            from chat_intent import is_companion_chat, is_design_brainstorm  # type: ignore
        except ImportError:
            is_companion_chat = None  # type: ignore
            is_design_brainstorm = None  # type: ignore
    if is_design_brainstorm and is_design_brainstorm(prompt):
        return False
    if is_companion_chat and is_companion_chat(prompt):
        return False

    low = (prompt or "").lower()
    triggers = (
        "diagnostic",
        "bilan",
        "état complet",
        "etat complet",
        "check lan",
        "check complet",
        "sondes et",
        "audit et status",
        "status et audit",
        "tout vérifier",
        "verifier tout",
        "vérifier tout",
        "cockpit",
        "vue d'ensemble",
        "vue densemble",
        "auto-audit",
        "auto audit",
        "autoaudit",
    )
    return any(t in low for t in triggers)


def enrich_response(
    result: Any,
    *,
    reflection: dict[str, Any] | None = None,
    timeline: list[dict[str, Any]] | None = None,
    cursor: dict[str, Any] | None = None,
) -> Any:
    if not isinstance(result, dict):
        return result
    if reflection and "reflection" not in result:
        result["reflection"] = reflection
    if timeline:
        existing = result.get("timeline")
        if isinstance(existing, list):
            result["timeline"] = existing + timeline
        else:
            result["timeline"] = timeline
    if cursor and "cursor" not in result:
        result["cursor"] = cursor
    from src.services.post_followup import apply_post_followup

    return apply_post_followup(result)


def timeline_step(
    *,
    kind: str,
    label: str,
    status: str = "ok",
    detail: str | None = None,
    ms: float | None = None,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "label": label,
        "status": status,
        "detail": detail,
        "ms": round(ms, 1) if ms is not None else None,
    }


async def _tool_team_status(*, conversation_id: str = "default") -> dict[str, Any]:
    from src.services.team_proxy import _format_campus_status, _get_campus_status
    from src.settings import get_settings

    settings = get_settings()
    base = str(settings.cortex_pilot_url or "").rstrip("/")
    t0 = time.monotonic()
    try:
        if not base:
            raise RuntimeError("CORTEX_PILOT_URL non configuré")
        timeout = httpx_timeout(read=float(settings.cortex_pilot_timeout_s))
        data = await _get_campus_status(base, timeout)
        content = _format_campus_status(data)
        return {
            "ok": data.get("ok", True) is not False,
            "tool": "team_status",
            "summary": content[:700],
            "ms": (time.monotonic() - t0) * 1000,
        }
    except Exception as e:
        return {
            "ok": False,
            "tool": "team_status",
            "summary": f"{type(e).__name__}: {e}",
            "ms": (time.monotonic() - t0) * 1000,
        }


async def _tool_ollama_audit(*, settings: Settings) -> dict[str, Any]:
    from src.services.lan_llm_grounding import format_direct_lan_answer, load_lan_llm_audit

    t0 = time.monotonic()
    try:
        audit = await load_lan_llm_audit(settings=settings)
        return {
            "ok": bool(audit.get("ok", True)),
            "tool": "ollama_audit",
            "summary": format_direct_lan_answer(audit)[:700],
            "ms": (time.monotonic() - t0) * 1000,
            "gaps": audit.get("gaps") or [],
        }
    except Exception as e:
        return {
            "ok": False,
            "tool": "ollama_audit",
            "summary": f"{type(e).__name__}: {e}",
            "ms": (time.monotonic() - t0) * 1000,
        }


async def _tool_providers_catalog(*, settings: Settings) -> dict[str, Any]:
    from src.services.provider_catalog import build_provider_catalog_payload

    t0 = time.monotonic()
    try:
        payload = await build_provider_catalog_payload(
            settings=settings,
            latest_monitor=None,
            include_ollama_audit=False,
        )
        rows = payload.get("providers") or []
        ups = [p["id"] for p in rows if p.get("status") == "up"]
        downs = [p["id"] for p in rows if p.get("status") == "down"]
        return {
            "ok": True,
            "tool": "providers_catalog",
            "summary": f"up={','.join(ups) or '—'} · down={','.join(downs) or '—'}",
            "ms": (time.monotonic() - t0) * 1000,
            "up": ups,
            "down": downs,
        }
    except Exception as e:
        return {
            "ok": False,
            "tool": "providers_catalog",
            "summary": f"{type(e).__name__}: {e}",
            "ms": (time.monotonic() - t0) * 1000,
        }


async def _tool_cursor_health() -> dict[str, Any]:
    from src.services.cursor_agent_client import cursor_health

    t0 = time.monotonic()
    try:
        h = await cursor_health()
        return {
            "ok": bool(h.get("ready")),
            "tool": "cursor_health",
            "summary": (
                f"ready={h.get('ready')} key={h.get('api_key_configured')} "
                f"repo={h.get('repo')}"
            ),
            "ms": (time.monotonic() - t0) * 1000,
        }
    except Exception as e:
        return {
            "ok": False,
            "tool": "cursor_health",
            "summary": f"{type(e).__name__}: {e}",
            "ms": (time.monotonic() - t0) * 1000,
        }


def plan_tools(prompt: str) -> list[str]:
    """Sélection heuristique d'outils (ordre d'exécution)."""
    low = (prompt or "").lower()
    tools: list[str] = []
    studioish = any(
        t in low
        for t in (
            "team",
            "studio",
            "cortex",
            "pilot",
            "sondes",
            "status",
            "orch",
            "campus",
            "atlas",
            "plateforme",
            "écosystème",
            "ecosysteme",
            "maturité",
            "maturite",
        )
    )
    ollamaish = any(
        t in low
        for t in (
            "ollama",
            ".110",
            ".111",
            "llm local",
            "modèle",
            "modele",
            "providers llm",
            "topo llm",
        )
    )
    # « audit » seul ou avec Team/studio → Team d'abord ; Ollama seulement si explicite
    if studioish or ("audit" in low and not ollamaish):
        tools.append("team_status")
    if ollamaish or (
        "audit" in low and not studioish and any(t in low for t in ("llm", "modèle", "modele", "ollama"))
    ):
        tools.append("ollama_audit")
    if any(t in low for t in ("provider", "catalogue", "groq", "gemini", "mistral")):
        tools.append("providers_catalog")
    if any(t in low for t in ("cursor", "repo", "github", "objectives")):
        tools.append("cursor_health")
    # Diagnostic générique → Team + (Ollama si pas audit studio pur)
    if not tools or wants_tool_loop(prompt):
        for t in ("team_status", "ollama_audit", "providers_catalog", "cursor_health"):
            if t not in tools:
                # Audit studio/Team : ne pas forcer ollama_audit
                if t == "ollama_audit" and studioish and not ollamaish:
                    continue
                tools.append(t)
    return tools[:4]


async def run_tool_loop(
    *,
    prompt: str,
    settings: Settings | None = None,
    conversation_id: str = "default",
) -> dict[str, Any]:
    """Exécute 1–4 outils puis synthétise une réponse + timeline."""
    s = settings or get_settings()
    planned = plan_tools(prompt)
    timeline: list[dict[str, Any]] = [
        timeline_step(kind="plan", label="Plan outils", detail=", ".join(planned), status="ok")
    ]
    results: list[dict[str, Any]] = []

    runners: dict[str, Any] = {
        "team_status": lambda: _tool_team_status(conversation_id=conversation_id),
        "ollama_audit": lambda: _tool_ollama_audit(settings=s),
        "providers_catalog": lambda: _tool_providers_catalog(settings=s),
        "cursor_health": lambda: _tool_cursor_health(),
    }

    for name in planned:
        fn = runners.get(name)
        if not fn:
            continue
        out = await fn()
        results.append(out)
        timeline.append(
            timeline_step(
                kind="tool",
                label=name,
                status="ok" if out.get("ok") else "error",
                detail=str(out.get("summary") or "")[:180],
                ms=out.get("ms"),
            )
        )

    # Synthèse déterministe (pas de LLM) pour rester fiable
    lines = ["## Diagnostic cockpit (boucle outils)", ""]
    for r in results:
        mark = "✓" if r.get("ok") else "✗"
        lines.append(f"### {mark} `{r.get('tool')}`")
        lines.append(str(r.get("summary") or ""))
        lines.append("")
    lines.append("_Synthèse automatique P2 — outils LAN uniquement._")
    content = "\n".join(lines).strip()
    timeline.append(timeline_step(kind="synthesize", label="Synthèse", status="ok"))

    return {
        "role": "assistant",
        "content": content,
        "response": content,
        "source": "tool_loop",
        "model": "tool_loop_p2",
        "model_used": "tool_loop_p2",
        "provider": "tools",
        "latency": sum(float(r.get("ms") or 0) for r in results) / 1000.0,
        "score": 0.9,
        "agent_action": None,
        "timeline": timeline,
        "tools": [{"tool": r.get("tool"), "ok": r.get("ok")} for r in results],
    }
