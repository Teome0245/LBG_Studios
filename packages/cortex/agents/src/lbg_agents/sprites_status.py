"""Statut factuel — sprites 2D Prime Client."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from lbg_agents.factual_status_common import fetch_team_tasks, status_result


def _sprites_state_path() -> Path:
    raw = os.environ.get("LBG_TEAM_INFOGRAPHISTE_SPRITES_STATE", "").strip()
    if raw:
        return Path(raw)
    return Path("/var/lib/lbg/team_infographiste/sprites_job_state.json")


def _load_job_state() -> dict[str, Any]:
    p = _sprites_state_path()
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _try_sprites_probe() -> dict[str, Any] | None:
    orch = os.environ.get("LBG_ORCHESTRATOR_ROOT", "").strip()
    candidates = []
    if orch:
        candidates.append(Path(orch))
    candidates.append(Path(__file__).resolve().parents[3] / "orchestrator")
    candidates.append(Path("/opt/LBG_IA_MMO/orchestrator"))
    for root in candidates:
        if not (root / "team" / "sprites_2d_pipeline.py").is_file():
            continue
        p = str(root)
        if p not in sys.path:
            sys.path.insert(0, p)
        try:
            from team.sprites_2d_pipeline import probe_sprites_2d_readiness

            return probe_sprites_2d_readiness()
        except Exception:
            return None
    return None


def collect_sprites_status() -> dict[str, Any]:
    probe = _try_sprites_probe() or {}
    state = _load_job_state()
    tasks = fetch_team_tasks(limit=3, actor_id="system:team_infographiste_sprites")
    last = tasks[0] if tasks else {}
    return {
        "probe": probe,
        "job_state": state,
        "last_task_id": last.get("id"),
        "last_task_status": last.get("status"),
        "state_path": str(_sprites_state_path()),
    }


def format_sprites_status_reply(status: dict[str, Any] | None = None) -> str:
    s = status or collect_sprites_status()
    probe = s.get("probe") if isinstance(s.get("probe"), dict) else {}
    lines = [
        "État **réel** sprites 2D Prime (sonde PNG + timer team) :",
        "",
    ]
    if probe:
        lines.append(
            f"- Readiness : **{probe.get('readiness', 'inconnu')}** "
            f"({probe.get('present_count', '?')}/{probe.get('expected_count', '?')} PNG)"
        )
        missing = probe.get("missing") if isinstance(probe.get("missing"), list) else []
        if missing:
            lines.append(f"- Manquants : `{', '.join(str(m) for m in missing[:8])}`")
        if probe.get("units_dir"):
            lines.append(f"- Dossier : `{probe.get('units_dir')}`")
    else:
        lines.append("- Sonde PNG indisponible depuis cet agent (orchestrator/team absent).")
    if s.get("last_task_id"):
        lines.append(
            f"- Dernière tâche sprites : `{str(s['last_task_id'])[:8]}…` — **{s.get('last_task_status')}**"
        )
    job = s.get("job_state") if isinstance(s.get("job_state"), dict) else {}
    if job.get("last_ok") is not None:
        lines.append(f"- Dernier run timer : ok={job.get('last_ok')}")
    lines.extend(["", "Suivi : filtre Pilot `#/team` → `actor:system:team_infographiste_sprites`."])
    return "\n".join(lines)


def run_sprites_status(*, actor_id: str, text: str, context: dict[str, Any]) -> dict[str, Any]:
    del text, context
    status = collect_sprites_status()
    reply = format_sprites_status_reply(status)
    return status_result(
        agent="sprites_status",
        handler="sprites_status",
        actor_id=actor_id,
        reply=reply,
        status=status,
        source="deterministic_sprites_status",
    )
