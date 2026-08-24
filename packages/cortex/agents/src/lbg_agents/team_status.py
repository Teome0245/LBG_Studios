"""Statut factuel — tâches équipe virtuelle Pygmalion."""

from __future__ import annotations

from collections import Counter
from typing import Any

from lbg_agents.factual_status_common import fetch_campus_status, fetch_team_tasks, status_result


def collect_team_status(*, task_limit: int = 20) -> dict[str, Any]:
    tasks = fetch_team_tasks(limit=task_limit)
    campus = fetch_campus_status()
    by_status = Counter(str(t.get("status") or "unknown") for t in tasks)
    by_role = Counter(str(t.get("role") or "unknown") for t in tasks)
    running = [t for t in tasks if str(t.get("status")) == "running"]
    queued = [t for t in tasks if str(t.get("status")) == "queued"]
    failed = [t for t in tasks if str(t.get("status")) == "failed"]
    recent = []
    for t in tasks[:8]:
        recent.append(
            {
                "id": str(t.get("id", ""))[:8],
                "role": t.get("role"),
                "status": t.get("status"),
                "objective": (str(t.get("objective") or ""))[:100],
            }
        )
    return {
        "tasks_total": len(tasks),
        "by_status": dict(by_status),
        "by_role": dict(by_role),
        "running_count": len(running),
        "queued_count": len(queued),
        "failed_count": len(failed),
        "running": [
            {
                "id": str(t.get("id", ""))[:8],
                "role": t.get("role"),
                "objective": (str(t.get("objective") or ""))[:80],
                "actor_id": t.get("actor_id"),
            }
            for t in running[:8]
        ],
        "queued": [
            {
                "id": str(t.get("id", ""))[:8],
                "role": t.get("role"),
                "objective": (str(t.get("objective") or ""))[:80],
            }
            for t in queued[:5]
        ],
        "recent": recent,
        "campus": campus if isinstance(campus, dict) else None,
    }


def _format_task_line(item: dict[str, Any], *, prefix: str = "-") -> str:
    role = item.get("role") or "?"
    objective = (str(item.get("objective") or "")).strip() or "—"
    tid = item.get("id") or "?"
    actor = item.get("actor_id")
    line = f"{prefix} **`{tid}…`** [{role}] {objective}"
    if actor:
        line += f" _(agent `{actor}`)_"
    return line


def format_team_status_reply(status: dict[str, Any] | None = None) -> str:
    s = status or collect_team_status()
    campus = s.get("campus") if isinstance(s.get("campus"), dict) else {}
    lines = [
        "Voici le **compte rendu réel** de l'équipe virtuelle — je lis les tâches et le campus "
        "directement, sans inventer de JIRA ni de codes projet fictifs.",
        "",
    ]

    if campus.get("ok") is True:
        dec = campus.get("decision") if isinstance(campus.get("decision"), dict) else {}
        miss = campus.get("mission") if isinstance(campus.get("mission"), dict) else {}
        mode = dec.get("mode") or "—"
        reason = dec.get("reason") or "—"
        lines.append(f"**Campus Lyra** — mode `{mode}` ({reason})")
        lines.append(
            f"- En cours : **{campus.get('running_count', s.get('running_count', 0))}** · "
            f"file d'attente : **{campus.get('queued_count', s.get('queued_count', 0))}** · "
            f"agents occupés : **{campus.get('busy_agent_count', '?')}**"
        )
        if miss.get("id"):
            obj = (str(miss.get("objective") or ""))[:140]
            lines.append(
                f"- Mission ouverte : **{miss.get('status', '?')}** — {obj or '—'}"
            )
        lr = campus.get("last_report") if isinstance(campus.get("last_report"), dict) else {}
        if lr.get("outcome"):
            lines.append(
                f"- Dernier rapport : **{lr.get('outcome')}** "
                f"({lr.get('acted_as') or '—'})"
            )
        failed_agents = campus.get("failed_agents")
        if isinstance(failed_agents, list) and failed_agents:
            names = [
                str(a.get("display_name") or a.get("agent_id") or "?")
                for a in failed_agents[:4]
                if isinstance(a, dict)
            ]
            if names:
                lines.append(f"- Agents en échec récent : {', '.join(names)}")
        lines.append("")

    running = s.get("running") if isinstance(s.get("running"), list) else []
    if running:
        lines.append("**Actions en cours**")
        for item in running:
            if isinstance(item, dict):
                lines.append(_format_task_line(item))
        lines.append("")
    elif s.get("running_count", 0) == 0:
        lines.append("**Actions en cours** — aucune tâche `running` pour le moment.")
        lines.append("")

    queued = s.get("queued") if isinstance(s.get("queued"), list) else []
    if queued:
        lines.append("**Prochaines tâches en file**")
        for item in queued:
            if isinstance(item, dict):
                lines.append(_format_task_line(item))
        lines.append("")

    by_status = s.get("by_status") if isinstance(s.get("by_status"), dict) else {}
    if by_status:
        parts = [f"`{k}`={v}" for k, v in sorted(by_status.items())]
        lines.append(f"**Vue d'ensemble** ({s.get('tasks_total', 0)} tâches listées) : {', '.join(parts)}")

    recent = s.get("recent") if isinstance(s.get("recent"), list) else []
    if recent and not running:
        lines.append("")
        lines.append("**Dernières activités**")
        for item in recent:
            if isinstance(item, dict):
                st = item.get("status") or "?"
                lines.append(
                    f"- `{item.get('id')}…` **{st}** [{item.get('role')}] — {item.get('objective')}"
                )

    if not s.get("tasks_total") and campus.get("ok") is not True:
        lines.extend(
            [
                "",
                "Je n'ai pas pu récupérer de tâches (orchestrateur injoignable ou base vide). "
                "Vérifier `LBG_ORCHESTRATOR_URL` et Pilot `#/team`.",
            ]
        )

    lines.extend(
        [
            "",
            "Tu veux le détail d'une tâche, lancer une mission ou valider une approbation L2 ? "
            "Dis-le-moi, ou ouvre Pilot `#/team` / `#/team/office`.",
        ]
    )
    return "\n".join(lines)


def run_team_status(*, actor_id: str, text: str, context: dict[str, Any]) -> dict[str, Any]:
    del text, context
    status = collect_team_status()
    reply = format_team_status_reply(status)
    return status_result(
        agent="team_status",
        handler="team_status",
        actor_id=actor_id,
        reply=reply,
        status=status,
        source="deterministic_team_status",
    )
