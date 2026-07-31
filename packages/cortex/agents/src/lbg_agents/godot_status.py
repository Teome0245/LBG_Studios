"""Statut factuel — Godot / ZB-0 / ZB-1 / M9 (audits repo locaux)."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from lbg_agents.factual_status_common import fetch_team_tasks, status_result


def _try_godot_probes() -> dict[str, Any]:
    orch = os.environ.get("LBG_ORCHESTRATOR_ROOT", "").strip()
    candidates = []
    if orch:
        candidates.append(Path(orch))
    here = Path(__file__).resolve()
    candidates.append(here.parents[3] / "orchestrator")
    candidates.append(Path("/opt/LBG_IA_MMO/orchestrator"))

    for root in candidates:
        if not (root / "team" / "lbg_ws2_audit.py").is_file():
            continue
        p = str(root)
        if p not in sys.path:
            sys.path.insert(0, p)
        try:
            from team.lbg_ws2_audit import audit_lbg_ws2_readiness, audit_zb0_readiness, audit_zb1_readiness
            from team.m9_map_probe import audit_m9_full_readiness

            return {
                "zb0": audit_zb0_readiness(),
                "zb1": audit_zb1_readiness(probe_live_feed=False),
                "lbg_ws2": audit_lbg_ws2_readiness(),
                "m9": audit_m9_full_readiness(),
                "probe_root": p,
            }
        except Exception as e:
            return {"probe_error": f"{type(e).__name__}: {e}", "probe_root": p}
    return {"probe_error": "audits Godot indisponibles (orchestrator/team absent)"}


def collect_godot_status() -> dict[str, Any]:
    probes = _try_godot_probes()
    qa_tasks = fetch_team_tasks(limit=6, role="qa")
    dev_tasks = fetch_team_tasks(limit=4, role="dev_godot")
    return {
        "probes": probes,
        "qa_tasks_recent": len(qa_tasks),
        "dev_godot_tasks_recent": len(dev_tasks),
    }


def _probe_line(label: str, probe: dict[str, Any] | None) -> str:
    if not isinstance(probe, dict):
        return f"- {label} : indisponible"
    ok = probe.get("ok")
    track = probe.get("track") or label
    score = probe.get("readiness_score")
    gaps = probe.get("gaps") if isinstance(probe.get("gaps"), list) else []
    gap_txt = f" — écarts : {len(gaps)}" if gaps else ""
    score_txt = f", score={score}" if score is not None else ""
    return f"- `{track}` : ok=**{ok}**{score_txt}{gap_txt}"


def format_godot_status_reply(status: dict[str, Any] | None = None) -> str:
    s = status or collect_godot_status()
    probes = s.get("probes") if isinstance(s.get("probes"), dict) else {}
    lines = [
        "État **réel** Godot / Zone Bridge / M9 (audits repo + tâches team) :",
        "",
    ]
    if probes.get("probe_error"):
        lines.append(f"- ⚠ {probes['probe_error']}")
    else:
        lines.append(_probe_line("ZB-0", probes.get("zb0") if isinstance(probes.get("zb0"), dict) else None))
        lines.append(_probe_line("ZB-1", probes.get("zb1") if isinstance(probes.get("zb1"), dict) else None))
        lines.append(_probe_line("lbg-ws/2", probes.get("lbg_ws2") if isinstance(probes.get("lbg_ws2"), dict) else None))
        lines.append(_probe_line("M9", probes.get("m9") if isinstance(probes.get("m9"), dict) else None))
        na = probes.get("zb1", {}).get("next_actions") if isinstance(probes.get("zb1"), dict) else None
        if isinstance(na, list) and na:
            lines.append(f"- Prochaine action ZB-1 : {na[0]}")
    lines.append(f"- Tâches QA récentes listées : **{s.get('qa_tasks_recent', 0)}**")
    lines.extend(
        [
            "",
            "Timers typiques VM 140 : `lbg-team-parallel-prime`, `godot-client-tracks`, `godot-sidecar-mirror`.",
            "Pas de lien JIRA — données locales uniquement.",
        ]
    )
    return "\n".join(lines)


def run_godot_status(*, actor_id: str, text: str, context: dict[str, Any]) -> dict[str, Any]:
    del text, context
    status = collect_godot_status()
    reply = format_godot_status_reply(status)
    return status_result(
        agent="godot_status",
        handler="godot_status",
        actor_id=actor_id,
        reply=reply,
        status=status,
        source="deterministic_godot_status",
    )
