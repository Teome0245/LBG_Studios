"""Statut factuel — infra / DevOps (healthz locaux, sans LLM)."""

from __future__ import annotations

import os
from typing import Any

from lbg_agents.factual_status_common import orchestrator_base, probe_http_health, status_result


def _health_urls() -> list[str]:
    urls: list[str] = []
    orch = orchestrator_base()
    urls.append(f"{orch}/healthz")
    backend = os.environ.get("LBG_BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
    urls.append(f"{backend}/healthz")
    for key in ("LBG_AGENT_DIALOGUE_URL", "LBG_AGENT_PM_URL"):
        raw = os.environ.get(key, "").strip().rstrip("/")
        if raw:
            urls.append(f"{raw}/healthz")
    ollama = os.environ.get("LBG_OLLAMA_BASE_URL", os.environ.get("OLLAMA_BASE_URL", "")).strip().rstrip("/")
    if ollama:
        urls.append(f"{ollama}/api/tags")
    # Dédupliquer en gardant l'ordre
    seen: set[str] = set()
    out: list[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def collect_infra_status() -> dict[str, Any]:
    probes = [probe_http_health(u) for u in _health_urls()]
    ok_count = sum(1 for p in probes if p.get("ok"))
    return {
        "probes": probes,
        "ok_count": ok_count,
        "total": len(probes),
        "orchestrator_url": orchestrator_base(),
    }


def format_infra_status_reply(status: dict[str, Any] | None = None) -> str:
    s = status or collect_infra_status()
    lines = [
        "État **réel** infra (sondes HTTP locales) — pas d'accès JIRA ni outil externe inventé :",
        "",
        f"- Orchestrateur : `{s.get('orchestrator_url')}`",
        f"- Sondes OK : **{s.get('ok_count', 0)}/{s.get('total', 0)}**",
    ]
    for p in s.get("probes") or []:
        if not isinstance(p, dict):
            continue
        mark = "✓" if p.get("ok") else "✗"
        st = p.get("status")
        lines.append(f"  {mark} `{p.get('url')}` → HTTP {st if st is not None else '—'}")
        if not p.get("ok") and p.get("error"):
            lines.append(f"    ({p.get('error')})")
    lines.extend(
        [
            "",
            "Pour un diagnostic plus poussé : intent `devops_probe` avec `devops_action` ou preset selfcheck Pilot.",
        ]
    )
    return "\n".join(lines)


def run_infra_status(*, actor_id: str, text: str, context: dict[str, Any]) -> dict[str, Any]:
    del text, context
    status = collect_infra_status()
    reply = format_infra_status_reply(status)
    return status_result(
        agent="infra_status",
        handler="infra_status",
        actor_id=actor_id,
        reply=reply,
        status=status,
        source="deterministic_infra_status",
    )
