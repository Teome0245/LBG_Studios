"""Brief matinal Compagnon — agrégat read-only (Self / Jobs L2 / LAN / mails), sans LLM.

P4 vague Agir : synthèse ≤15 lignes + 1–2 suggestions Agir (jamais auto-exécutées).
Le brief lui-même reste lecture seule (`auto_real` soft OK).
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from lbg_agents.factual_status_common import (
    fetch_json,
    orchestrator_base,
    probe_http_health,
    status_result,
)

BRIEF_SCHEMA_VERSION = 1
_MAX_REPLY_LINES = 15


def _tz() -> ZoneInfo:
    raw = os.environ.get("LBG_MORNING_BRIEF_TZ", "Europe/Paris").strip() or "Europe/Paris"
    try:
        return ZoneInfo(raw)
    except Exception:
        return ZoneInfo("Europe/Paris")


def morning_window_hours() -> tuple[int, int]:
    """Fenêtre locale inclusive [start, end) pour l'initiative matinale."""
    try:
        start = int(os.environ.get("LBG_MORNING_BRIEF_HOUR_START", "7").strip() or "7")
    except ValueError:
        start = 7
    try:
        end = int(os.environ.get("LBG_MORNING_BRIEF_HOUR_END", "10").strip() or "10")
    except ValueError:
        end = 10
    start = max(0, min(23, start))
    end = max(start + 1, min(24, end))
    return start, end


def is_morning_window(*, now: datetime | None = None) -> bool:
    local = now or datetime.now(_tz())
    if local.tzinfo is None:
        local = local.replace(tzinfo=_tz())
    else:
        local = local.astimezone(_tz())
    start, end = morning_window_hours()
    return start <= local.hour < end


def brief_day_key(*, now: datetime | None = None) -> str:
    local = now or datetime.now(_tz())
    if local.tzinfo is None:
        local = local.replace(tzinfo=_tz())
    else:
        local = local.astimezone(_tz())
    return local.strftime("%Y-%m-%d")


def _fetch_proactive() -> dict[str, Any] | None:
    payload = fetch_json(f"{orchestrator_base()}/v1/proactive/status", timeout=3.0)
    return payload if isinstance(payload, dict) else None


def _fetch_self() -> dict[str, Any] | None:
    payload = fetch_json(
        f"{orchestrator_base()}/v1/self/status?ensure_goals=0",
        timeout=3.0,
    )
    return payload if isinstance(payload, dict) else None


def _fetch_jobs_l2() -> dict[str, Any]:
    """Jobs en attente d’approbation (lecture seule)."""
    payload = fetch_json(f"{orchestrator_base()}/v1/jobs", timeout=3.0)
    jobs: list[dict[str, Any]] = []
    if isinstance(payload, list):
        jobs = [j for j in payload if isinstance(j, dict)]
    elif isinstance(payload, dict):
        raw = payload.get("jobs") or payload.get("items") or []
        if isinstance(raw, list):
            jobs = [j for j in raw if isinstance(j, dict)]
    waiting = [
        j
        for j in jobs
        if str(j.get("status") or "").strip().lower() in ("waiting_approval", "review")
        or (j.get("approval_required") and str(j.get("status") or "").lower() in ("queued", "waiting_approval"))
    ]
    samples = []
    for j in waiting[:3]:
        samples.append(
            {
                "id": str(j.get("id") or "")[:40],
                "title": str(j.get("title") or j.get("objective") or j.get("kind") or "job")[:60],
                "status": j.get("status"),
            }
        )
    return {
        "ok": payload is not None,
        "n_total": len(jobs),
        "n_waiting": len(waiting),
        "samples": samples,
    }


def _network_lan_snapshot() -> dict[str, Any]:
    """Diff LAN depuis state inventaire (pas de scan)."""
    raw = os.environ.get("LBG_NETWORK_INVENTORY_STATE", "").strip()
    path = Path(raw) if raw else Path("/var/lib/lbg/network_inventory/state.json")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"ok": False, "available": False}
    if not isinstance(data, dict):
        return {"ok": False, "available": False}
    diff = data.get("last_diff") if isinstance(data.get("last_diff"), dict) else {}
    return {
        "ok": True,
        "available": True,
        "n_present": data.get("n_present"),
        "n_hosts": data.get("n_hosts"),
        "n_appeared": int(diff.get("n_appeared") or 0),
        "n_disappeared": int(diff.get("n_disappeared") or 0),
    }


def _infra_probe_urls() -> list[str]:
    orch = orchestrator_base()
    urls = [f"{orch}/healthz"]
    backend = os.environ.get("LBG_BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
    if backend:
        urls.append(f"{backend}/healthz")
    companion = os.environ.get("LBG_COMPANION_HEALTH_URL", "").strip()
    if companion:
        urls.append(companion)
    else:
        urls.append("http://192.168.0.100:3000/health")
    desktop = os.environ.get("LBG_AGENT_DESKTOP_URL", "http://192.168.0.10:5005").rstrip("/")
    if desktop:
        urls.append(f"{desktop}/healthz")
    return urls[:6]


def collect_morning_signals(*, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Collecte best-effort — chaque source peut être absente sans faire échouer le brief."""
    ctx = context if isinstance(context, dict) else {}
    now = datetime.now(_tz())
    proactive = _fetch_proactive()
    self_payload = _fetch_self()
    self_state = (
        self_payload.get("state")
        if isinstance(self_payload, dict) and isinstance(self_payload.get("state"), dict)
        else None
    )
    probes = [probe_http_health(u) for u in _infra_probe_urls()]
    ok_count = sum(1 for p in probes if p.get("ok"))
    jobs = _fetch_jobs_l2()
    lan = _network_lan_snapshot()

    mail_hint = ctx.get("mail_preview") if isinstance(ctx.get("mail_preview"), dict) else None
    extra_notes = ctx.get("brief_notes") if isinstance(ctx.get("brief_notes"), list) else []

    return {
        "schema_version": BRIEF_SCHEMA_VERSION,
        "generated_at": now.isoformat(),
        "day_key": brief_day_key(now=now),
        "morning_window": is_morning_window(now=now),
        "proactive": {
            "enabled": bool(proactive.get("enabled")) if proactive else False,
            "ok": proactive is not None,
            "mode": (proactive or {}).get("mode"),
            "tension": (proactive or {}).get("tension"),
            "curiosite": (proactive or {}).get("curiosite"),
            "silence_seconds_est": (proactive or {}).get("silence_seconds_est"),
            "last_job_id": (proactive or {}).get("last_job_id"),
            "infra_signals": (proactive or {}).get("infra_signals")
            if isinstance((proactive or {}).get("infra_signals"), dict)
            else {},
        },
        "self": {
            "enabled": bool(self_payload.get("enabled")) if self_payload else False,
            "ok": bool(self_payload.get("ok")) if self_payload else False,
            "drives": (self_state or {}).get("drives")
            if isinstance((self_state or {}).get("drives"), dict)
            else {},
            "intent": (self_state or {}).get("intent")
            if isinstance((self_state or {}).get("intent"), dict)
            else {},
            "pending_will_count": len((self_state or {}).get("pending_will") or [])
            if isinstance((self_state or {}).get("pending_will"), list)
            else 0,
            "goals_active_count": (self_state or {}).get("goals_active_count"),
        },
        "infra": {
            "ok_count": ok_count,
            "total": len(probes),
            "probes": probes,
        },
        "jobs_l2": jobs,
        "lan": lan,
        "mail": {
            "available": bool(mail_hint),
            "hint": "Agir « regarde mes mails récents » (IMAP RO).",
            "preview": mail_hint,
            "matched_count": (mail_hint or {}).get("matched_count") if mail_hint else None,
        },
        "deferred": {
            "devis": "connecteur métier non branché",
            "ventes": "connecteur métier non branché",
            "social": "analytics réseaux non branchées",
        },
        "notes": [str(n)[:200] for n in extra_notes if n][:4],
    }


def pick_next_agir(signals: dict[str, Any]) -> list[dict[str, str]]:
    """1–2 propositions du jour (suggestions, jamais exécutées par le brief)."""
    picks: list[dict[str, str]] = []
    jobs = signals.get("jobs_l2") if isinstance(signals.get("jobs_l2"), dict) else {}
    lan = signals.get("lan") if isinstance(signals.get("lan"), dict) else {}
    infra = signals.get("infra") if isinstance(signals.get("infra"), dict) else {}
    proactive = signals.get("proactive") if isinstance(signals.get("proactive"), dict) else {}
    infra_sig = (
        proactive.get("infra_signals") if isinstance(proactive.get("infra_signals"), dict) else {}
    )

    if int(jobs.get("n_waiting") or 0) > 0:
        picks.append(
            {
                "id": "jobs_l2",
                "sourceText": "ouvre http://192.168.0.140:8080/#/jobs dans le navigateur",
            }
        )
    if int(lan.get("n_appeared") or 0) or int(lan.get("n_disappeared") or 0):
        picks.append(
            {
                "id": "network_inventory",
                "sourceText": "fais un inventaire réseau LAN",
            }
        )
    ok = int(infra.get("ok_count") or 0)
    total = int(infra.get("total") or 0)
    if total and ok < total:
        picks.append(
            {
                "id": "selfcheck",
                "sourceText": "fais un diagnostic infra selfcheck LAN",
            }
        )
    elif infra_sig.get("disk_critical") or infra_sig.get("disk_high"):
        picks.append(
            {
                "id": "selfcheck",
                "sourceText": "fais un diagnostic infra selfcheck LAN",
            }
        )

    # Toujours proposer mails si place (P1 OK)
    if len(picks) < 2:
        picks.append({"id": "mail", "sourceText": "regarde mes mails récents"})
    if len(picks) < 2 and not any(p["id"] == "selfcheck" for p in picks):
        picks.append(
            {
                "id": "selfcheck",
                "sourceText": "fais un diagnostic infra selfcheck LAN",
            }
        )
    return picks[:2]


def format_morning_brief_reply(signals: dict[str, Any] | None = None) -> str:
    s = signals or collect_morning_signals()
    proactive = s.get("proactive") if isinstance(s.get("proactive"), dict) else {}
    self_blk = s.get("self") if isinstance(s.get("self"), dict) else {}
    infra = s.get("infra") if isinstance(s.get("infra"), dict) else {}
    jobs = s.get("jobs_l2") if isinstance(s.get("jobs_l2"), dict) else {}
    lan = s.get("lan") if isinstance(s.get("lan"), dict) else {}
    mail = s.get("mail") if isinstance(s.get("mail"), dict) else {}
    drives = self_blk.get("drives") if isinstance(self_blk.get("drives"), dict) else {}
    intent = self_blk.get("intent") if isinstance(self_blk.get("intent"), dict) else {}
    infra_sig = (
        proactive.get("infra_signals") if isinstance(proactive.get("infra_signals"), dict) else {}
    )
    next_agir = pick_next_agir(s)

    def _pct(key: str) -> str:
        try:
            v = float(drives.get(key))
            if v <= 1.0:
                return f"{int(round(v * 100))}%"
            return f"{int(round(v))}%"
        except (TypeError, ValueError):
            return "—"

    lines: list[str] = [
        f"**Brief matinal** `{s.get('day_key')}` — lecture seule · 0 auto-Réel d’actions",
        f"- Infra : **{infra.get('ok_count', 0)}/{infra.get('total', 0)}** healthz"
        + (" · ⚠ disque" if infra_sig.get("disk_critical") or infra_sig.get("disk_high") else ""),
        f"- Self : `{intent.get('primary') or '—'}` · curiosité {_pct('curiosity')}"
        f" · envies {self_blk.get('pending_will_count', 0)}",
        f"- Jobs L2 : **{jobs.get('n_waiting', 0)}** en attente"
        + (f" ({', '.join(x.get('title') or x.get('id') or '?' for x in (jobs.get('samples') or [])[:2])})"
           if jobs.get("samples")
           else ""),
    ]

    if lan.get("available"):
        n_app = int(lan.get("n_appeared") or 0)
        n_dis = int(lan.get("n_disappeared") or 0)
        lines.append(
            f"- LAN : {lan.get('n_present', '?')}/{lan.get('n_hosts', '?')} présents"
            + (f" · +{n_app}/−{n_dis}" if (n_app or n_dis) else " · stable")
        )
    else:
        lines.append("- LAN : inventaire non dispo (timer Héphaïstos)")

    if mail.get("available") and mail.get("matched_count") is not None:
        lines.append(f"- Mails (ctx) : {mail.get('matched_count')} aperçus")
    else:
        lines.append("- Mails : via Agir IMAP (pas d’auto-fetch)")

    lines.append("")
    lines.append("**Propositions du jour** (à valider en Agir) :")
    for i, a in enumerate(next_agir, 1):
        lines.append(f"{i}. `{a.get('sourceText')}`")

    notes = s.get("notes") if isinstance(s.get("notes"), list) else []
    for n in notes[:1]:
        if len(lines) < _MAX_REPLY_LINES:
            lines.append(f"- Note : {n}")

    # Plafond strict ≤15 lignes
    clipped = lines[:_MAX_REPLY_LINES]
    return "\n".join(clipped)


def build_brief_payload(*, context: dict[str, Any] | None = None) -> dict[str, Any]:
    signals = collect_morning_signals(context=context)
    reply = format_morning_brief_reply(signals)
    next_agir = pick_next_agir(signals)
    return {
        "schema_version": BRIEF_SCHEMA_VERSION,
        "kind": "morning_brief",
        "day_key": signals.get("day_key"),
        "spoken_text": reply,
        "reply": reply,
        "signals": signals,
        "next_agir": next_agir,
        "auto_execute_next": False,
        "line_count": len(reply.splitlines()),
    }


def run_morning_brief(*, actor_id: str, text: str, context: dict[str, Any]) -> dict[str, Any]:
    del text
    payload = build_brief_payload(context=context)
    reply = str(payload.get("reply") or "")
    return status_result(
        agent="morning_brief",
        handler="morning_brief",
        actor_id=actor_id,
        reply=reply,
        status=payload,
        source="deterministic_morning_brief",
    )
