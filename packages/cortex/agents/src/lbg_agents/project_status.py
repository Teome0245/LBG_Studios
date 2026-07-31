"""Statut factuel — vue projet (plan de route + équipe, sans LLM)."""

from __future__ import annotations

from typing import Any

from lbg_agents.factual_status_common import status_result
from lbg_agents.pm_stub import _extract_etape_actuelle, _extract_file_attente, _read_plan_text
from lbg_agents.team_status import collect_team_status


def collect_project_status() -> dict[str, Any]:
    plan = _read_plan_text()
    etape = _extract_etape_actuelle(plan) if isinstance(plan, str) else None
    file_attente = _extract_file_attente(plan) if isinstance(plan, str) else None
    team = collect_team_status()
    return {
        "current_step": etape,
        "file_attente": file_attente,
        "plan_found": isinstance(plan, str),
        "team": team,
    }


def format_project_status_reply(status: dict[str, Any] | None = None) -> str:
    s = status or collect_project_status()
    lines = [
        "Point **réel** projet LBG (plan local + tâches team) — je n'invente pas de JIRA ni de code projet fictif :",
        "",
    ]
    if s.get("plan_found"):
        if s.get("current_step"):
            lines.append(f"- {s['current_step']}")
        else:
            lines.append("- Plan de route trouvé mais pas de ligne « Étape actuelle » extraite.")
        if s.get("file_attente"):
            lines.append(f"- {s['file_attente']}")
    else:
        lines.append(
            "- `docs/plan_de_route.md` non lisible ici — configurer `LBG_PM_PLAN_PATH` ou déployer le repo."
        )
    team = s.get("team") if isinstance(s.get("team"), dict) else {}
    running = team.get("running_count", 0)
    lines.append(f"- Tâches team listées : **{team.get('tasks_total', 0)}** (dont {running} en `running`)")
    if team.get("running"):
        for r in team.get("running") or []:
            if isinstance(r, dict):
                lines.append(f"  - en cours : [{r.get('role')}] {r.get('objective')}")
    lines.extend(
        [
            "",
            "Pour un détail ciblé, précisez : LoRA/tri images, Godot/ZB-1, sprites 2D, ou infra/DevOps.",
            "Documentation : `docs/plan_de_route.md` — suivi opérationnel : Pilot `#/team`.",
        ]
    )
    return "\n".join(lines)


def run_project_status(*, actor_id: str, text: str, context: dict[str, Any]) -> dict[str, Any]:
    del text, context
    status = collect_project_status()
    reply = format_project_status_reply(status)
    return status_result(
        agent="project_status",
        handler="project_status",
        actor_id=actor_id,
        reply=reply,
        status=status,
        source="deterministic_project_status",
    )
