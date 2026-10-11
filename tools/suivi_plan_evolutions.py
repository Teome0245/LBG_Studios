#!/usr/bin/env python3
"""Suivi plan d'évolutions — bloquants / à relancer / réalisés.

Lit docs/suivi/plan_evolutions.json, croise la Team (.140), écrit:
  - docs/suivi/PLAN_EVOLUTIONS_STATUS.md  (compte rendu humain)
  - met à jour updated_ts + signaux Team dans le JSON

Usage:
  python3 tools/suivi_plan_evolutions.py --refresh
  python3 tools/suivi_plan_evolutions.py --json          # stdout résumé
  python3 tools/suivi_plan_evolutions.py --mark 1.2 in_progress --evidence "Métis…"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TRACK_PATH = ROOT / "docs" / "suivi" / "plan_evolutions.json"
STATUS_MD = ROOT / "docs" / "suivi" / "PLAN_EVOLUTIONS_STATUS.md"
DEFAULT_TEAM = "http://192.168.0.140:8010"

VALID = frozenset(
    {"todo", "in_progress", "done", "blocked", "relaunch", "cancelled"}
)


def _http_json(url: str, timeout: float = 20.0) -> Any:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def load_track() -> dict[str, Any]:
    data = json.loads(TRACK_PATH.read_text(encoding="utf-8"))
    if not isinstance(data.get("tickets"), list):
        raise SystemExit("plan_evolutions.json: tickets manquants")
    return data


def save_track(data: dict[str, Any]) -> None:
    data["updated_ts"] = time.time()
    TRACK_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def fetch_team_tasks(base: str, limit: int = 80) -> list[dict[str, Any]]:
    url = f"{base.rstrip('/')}/v1/team/tasks?limit={limit}"
    try:
        raw = _http_json(url)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        print(f"WARN Team injoignable: {e}", file=sys.stderr)
        return []
    tasks = raw.get("tasks") if isinstance(raw, dict) else raw
    return list(tasks or []) if isinstance(tasks, list) else []


def _ticket_match(ticket: dict[str, Any], task: dict[str, Any]) -> bool:
    # Objectif + context plan_ticket seulement (évite IPs 192.168… qui matchent « 1.2 »)
    ctx = task.get("context") if isinstance(task.get("context"), dict) else {}
    plan_ticket = str(ctx.get("plan_ticket") or ctx.get("ticket_id") or "").lower()
    tid = str(ticket.get("id") or "").lower()
    if tid and plan_ticket == tid:
        return True
    obj = str(task.get("objective") or "").lower()
    # id ticket explicite : « 1.2 », «#1.2», «[1.2]», «ticket 1.2»
    if tid and re.search(
        rf"(?:ticket\s+|plan\s+|#|\[){re.escape(tid)}\b|(?:^|[\s]){re.escape(tid)}(?:\s|\]|:|,|$)",
        obj,
    ):
        return True
    for kw in ticket.get("keywords") or []:
        k = str(kw).lower().strip()
        if not k or k == tid:
            continue
        # Mots courts / numériques : boundaries strictes
        if len(k) <= 3 or re.fullmatch(r"\d+\.\d+", k):
            if re.search(rf"(?<![\w.]){re.escape(k)}(?![\w.])", obj):
                return True
            continue
        if k in obj:
            return True
    return False


def classify_team_signals(
    tickets: list[dict[str, Any]], tasks: list[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    """Attache signaux Team par ticket (ne force pas le status done manuel)."""
    by_id: dict[str, list[dict[str, Any]]] = {str(t["id"]): [] for t in tickets}
    orphan_failed: list[dict[str, Any]] = []

    for task in tasks:
        st = str(task.get("status") or "").lower()
        matched = False
        for ticket in tickets:
            if not _ticket_match(ticket, task):
                continue
            matched = True
            by_id[str(ticket["id"])].append(
                {
                    "task_id": task.get("id"),
                    "status": st,
                    "role": task.get("role"),
                    "objective": (task.get("objective") or "")[:160],
                    "approval_required": bool(task.get("approval_required")),
                    "pilot": f"http://192.168.0.140:8080/pilot/#/team?task={task.get('id')}",
                }
            )
        if not matched and st == "failed":
            obj = (task.get("objective") or "").lower()
            if any(
                k in obj
                for k in (
                    "plan evol",
                    "métis",
                    "metis",
                    "opencode",
                    "presence_brief",
                    "plan_propositions",
                )
            ):
                orphan_failed.append(
                    {
                        "task_id": task.get("id"),
                        "status": st,
                        "role": task.get("role"),
                        "objective": (task.get("objective") or "")[:160],
                        "pilot": f"http://192.168.0.140:8080/pilot/#/team?task={task.get('id')}",
                    }
                )
    return {"by_ticket": by_id, "orphan_failed": orphan_failed}


def apply_auto_status(ticket: dict[str, Any], signals: list[dict[str, Any]]) -> str:
    """Propose un statut opérationnel sans écraser un done manuel sans signal contraire."""
    current = str(ticket.get("status") or "todo")
    if current == "cancelled":
        return current

    failed = [s for s in signals if s.get("status") == "failed"]
    running = [s for s in signals if s.get("status") == "running"]
    review = [
        s
        for s in signals
        if s.get("status") in ("review",) or (
            s.get("approval_required") and s.get("status") in ("queued", "review")
        )
    ]
    queued = [s for s in signals if s.get("status") == "queued"]
    done_sigs = [s for s in signals if s.get("status") == "done"]

    # Échec sans succès plus récent sur le même fil → à relancer
    if failed and current != "done":
        # Si un done existe aussi, garder relaunch seulement s'il n'y a pas
        # de done dont l'objectif porte clairement le ticket (preuve partielle).
        if not done_sigs:
            return "relaunch"
        # done + failed : rester todo/in_progress plutôt que relaunch bruyant
        # sauf si le ticket est encore todo (travail SSE jamais livré).
        if current == "todo":
            return "relaunch"
    if review and current != "done":
        return "blocked"
    if running or queued:
        return "in_progress"
    return current


def resolve_dependency_blocks(
    tickets: list[dict[str, Any]],
) -> None:
    """Prérequis non done → blocked ; dès que tous sont done → débloque (todo)."""
    by_id = {str(t["id"]): t for t in tickets}
    for t in tickets:
        st = str(t.get("status") or "todo")
        if st in ("done", "cancelled", "relaunch"):
            continue
        deps = [by_id[d] for d in (t.get("blocked_by") or []) if d in by_id]
        pending = [d for d in deps if str(d.get("status")) != "done"]
        if pending:
            t["status"] = "blocked"
            t["block_reason"] = "prérequis non done: " + ", ".join(
                str(d.get("id")) for d in pending
            )
            continue
        # Prérequis satisfaits : sortir de blocked (ne pas écraser in_progress).
        if st == "blocked":
            t["status"] = "todo"
            t.pop("block_reason", None)
        elif "block_reason" in t and st in ("todo", "in_progress"):
            t.pop("block_reason", None)


def build_summary(data: dict[str, Any], team_base: str) -> dict[str, Any]:
    tickets = list(data.get("tickets") or [])
    tasks = fetch_team_tasks(team_base)
    signals = classify_team_signals(tickets, tasks)

    for t in tickets:
        tid = str(t["id"])
        sigs = signals["by_ticket"].get(tid) or []
        t["team_signals"] = sigs
        auto = apply_auto_status(t, sigs)
        # Ne downgrade pas un done sauf relaunch explicite (failed récent)
        if str(t.get("status")) == "done" and auto != "relaunch":
            pass
        else:
            t["status"] = auto

    resolve_dependency_blocks(tickets)

    buckets: dict[str, list[dict[str, Any]]] = {
        "done": [],
        "in_progress": [],
        "relaunch": [],
        "blocked": [],
        "todo": [],
        "cancelled": [],
    }
    for t in tickets:
        buckets.setdefault(str(t.get("status") or "todo"), []).append(
            {
                "id": t.get("id"),
                "title": t.get("title"),
                "horizon": t.get("horizon"),
                "evidence": t.get("evidence"),
                "block_reason": t.get("block_reason"),
                "team_signals": t.get("team_signals") or [],
            }
        )

    plan_complete = bool(tickets) and all(
        str(t.get("status")) in ("done", "cancelled") for t in tickets
    )

    return {
        "ok": True,
        "plan_id": data.get("plan_id"),
        "source_doc": data.get("source_doc"),
        "updated_ts": time.time(),
        "plan_complete": plan_complete,
        "counts": {k: len(v) for k, v in buckets.items()},
        "buckets": buckets,
        "orphan_failed": signals["orphan_failed"],
        "pilot_team": "http://192.168.0.140:8080/pilot/#/team",
    }


def render_markdown(summary: dict[str, Any]) -> str:
    ts = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")
    counts = summary.get("counts") or {}
    lines = [
        "# Suivi — Plan d'évolutions Studio / Jeu",
        "",
        f"**Généré** : {ts}  ",
        f"**Plan** : `{summary.get('plan_id')}` · source [`{summary.get('source_doc')}`](../PLAN_PROPOSITIONS_EVOLUTIONS.md)  ",
        f"**Pilot** : [{summary.get('pilot_team')}]({summary.get('pilot_team')})  ",
        f"**Plan entièrement réalisé** : {'✅ OUI' if summary.get('plan_complete') else '❌ non'}",
        "",
        "## Synthèse",
        "",
        f"| Done | En cours | À relancer | Bloqué | Todo |",
        f"|:---:|:---:|:---:|:---:|:---:|",
        f"| {counts.get('done', 0)} | {counts.get('in_progress', 0)} | {counts.get('relaunch', 0)} | {counts.get('blocked', 0)} | {counts.get('todo', 0)} |",
        "",
    ]

    def section(title: str, key: str, empty: str) -> None:
        items = (summary.get("buckets") or {}).get(key) or []
        lines.append(f"## {title}")
        lines.append("")
        if not items:
            lines.append(empty)
            lines.append("")
            return
        for it in items:
            lines.append(f"### `{it.get('id')}` — {it.get('title')}")
            if it.get("block_reason"):
                lines.append(f"- **Blocage** : {it['block_reason']}")
            if it.get("evidence"):
                lines.append(f"- **Preuve** : {it['evidence']}")
            sigs = it.get("team_signals") or []
            if sigs:
                lines.append("- **Team** :")
                for s in sigs[:5]:
                    lines.append(
                        f"  - `{s.get('status')}` [{(s.get('task_id') or '')[:8]}]({s.get('pilot')}) "
                        f"— {(s.get('objective') or '')[:100]}"
                    )
            lines.append("")

    section("Réalisés", "done", "_Aucun encore._")
    section("En cours", "in_progress", "_Rien en cours._")
    section("À relancer (échecs Team)", "relaunch", "_Rien à relancer._")
    section("Bloqués (prérequis / L2)", "blocked", "_Aucun blocage._")
    section("Todo", "todo", "_File vide._")

    orphans = summary.get("orphan_failed") or []
    lines.append("## Échecs Team liés au plan (hors ticket)")
    lines.append("")
    if not orphans:
        lines.append("_Aucun._")
        lines.append("")
    else:
        for s in orphans[:10]:
            lines.append(
                f"- `{s.get('status')}` [{(s.get('task_id') or '')[:8]}]({s.get('pilot')}) "
                f"— {(s.get('objective') or '')[:120]}"
            )
        lines.append("")

    lines.extend(
        [
            "## Rafraîchir",
            "",
            "```bash",
            "python3 tools/suivi_plan_evolutions.py --refresh",
            "python3 tools/suivi_plan_evolutions.py --mark 1.2 done --evidence 'SSE live + smoke'",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def cmd_mark(ticket_id: str, status: str, evidence: str) -> None:
    if status not in VALID:
        raise SystemExit(f"status invalide: {status} (attendu {sorted(VALID)})")
    ev = (evidence or "").strip()
    if status == "done" and len(ev) < 24:
        raise SystemExit(
            "mark done refuse : --evidence requis (≥24 car., preuve concrète "
            "fichier/smoke/CI — pas un dry-run)."
        )
    data = load_track()
    found = False
    for t in data["tickets"]:
        if str(t.get("id")) == ticket_id:
            t["status"] = status
            if ev:
                t["evidence"] = ev
            found = True
            break
    if not found:
        raise SystemExit(f"ticket inconnu: {ticket_id}")
    save_track(data)
    print(f"OK marked {ticket_id} → {status}")


def persist_summary(data: dict[str, Any], summary: dict[str, Any]) -> None:
    by = {str(t["id"]): t for t in data["tickets"]}
    for bucket, items in (summary.get("buckets") or {}).items():
        for it in items:
            tid = str(it.get("id"))
            if tid not in by:
                continue
            by[tid]["status"] = bucket
            if it.get("block_reason"):
                by[tid]["block_reason"] = it["block_reason"]
            elif "block_reason" in by[tid] and bucket != "blocked":
                by[tid].pop("block_reason", None)
            by[tid]["team_signals"] = it.get("team_signals") or []
    save_track(data)
    STATUS_MD.write_text(render_markdown(summary), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--refresh", action="store_true", help="Croise Team + réécrit STATUS.md")
    ap.add_argument("--json", action="store_true", help="Imprime le résumé JSON")
    ap.add_argument("--team-base", default=DEFAULT_TEAM)
    ap.add_argument("--mark", nargs=2, metavar=("ID", "STATUS"), help="Force un statut ticket")
    ap.add_argument("--evidence", default="", help="Preuve avec --mark")
    args = ap.parse_args()

    if args.mark:
        cmd_mark(args.mark[0], args.mark[1], args.evidence)

    data = load_track()
    summary = build_summary(data, args.team_base)

    if args.refresh or args.mark:
        persist_summary(data, summary)
        print(f"OK wrote {STATUS_MD.relative_to(ROOT)}")

    if args.json or not args.refresh:
        print(json.dumps(summary, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
