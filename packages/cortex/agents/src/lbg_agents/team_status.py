"""Statut factuel — tâches équipe virtuelle Pygmalion."""

from __future__ import annotations

from collections import Counter
from typing import Any

from lbg_agents.factual_status_common import fetch_team_tasks, status_result


def collect_team_status() -> dict[str, Any]:
    tasks = fetch_team_tasks(limit=20)
    by_status = Counter(str(t.get("status") or "unknown") for t in tasks)
    by_role = Counter(str(t.get("role") or "unknown") for t in tasks)
    running = [t for t in tasks if str(t.get("status")) == "running"]
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
        "running": [
            {
                "id": str(t.get("id", ""))[:8],
                "role": t.get("role"),
                "objective": (str(t.get("objective") or ""))[:80],
            }
            for t in running[:5]
        ],
        "recent": recent,
    }


def format_team_status_reply(status: dict[str, Any] | None = None) -> str:
    s = status or collect_team_status()
    lines = [
        "État **réel** de l'équipe virtuelle (lecture `/v1/team/tasks`) — sans invention :",
        "",
        f"- Tâches listées : **{s.get('tasks_total', 0)}**",
    ]
    by_status = s.get("by_status") if isinstance(s.get("by_status"), dict) else {}
    if by_status:
        parts = [f"`{k}`={v}" for k, v in sorted(by_status.items())]
        lines.append(f"- Par statut : {', '.join(parts)}")
    if s.get("running_count"):
        lines.append(f"- En cours (`running`) : **{s['running_count']}**")
        for r in s.get("running") or []:
            if isinstance(r, dict):
                lines.append(f"  - `{r.get('id')}…` [{r.get('role')}] {r.get('objective')}")
    recent = s.get("recent") if isinstance(s.get("recent"), list) else []
    if recent:
        lines.append("- Dernières tâches :")
        for r in recent:
            if isinstance(r, dict):
                lines.append(
                    f"  - `{r.get('id')}…` **{r.get('status')}** [{r.get('role')}] — {r.get('objective')}"
                )
    if not s.get("tasks_total"):
        lines.append(
            "- Aucune tâche récupérée (orchestrateur injoignable ou base vide). "
            "Vérifier `LBG_ORCHESTRATOR_URL` et Pilot `#/team`."
        )
    lines.extend(["", "Suivi : Pilot `#/team` — pas de JIRA externe dans ce pipeline."])
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
