"""Workflow qa — validation Godot bundle (smokes + résumé humain)."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

from team.godot_soe_probe import probe_soe_m3_login, soe_m3_enabled
from team.godot_supervisor import execute_godot_supervisor
from team.human_summary import format_validation_summary
from team.lbg_ws2_audit import audit_zb0_readiness
from team.models import TeamTask

# Tracks déjà couverts par le rapport superviseur (blocking vs advisory).
# Ne pas re-hard-fail la validation sur un advisory (ex. assets Infographiste).
_ADVISORY_VALIDATION_TRACKS = frozenset({"infographiste_assets"})


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _is_godot_validation(task: TeamTask) -> bool:
    ctx = task.context
    if ctx.get("godot_validation") or ctx.get("validation_bundle"):
        return True
    text = (task.objective or "").lower()
    return bool(
        re.search(
            r"\b(valider|validation|checklist).*\b(godot|client|prime)\b"
            r"|\b(godot|client).*\b(valider|validation)\b",
            text,
        )
    )


def _run_smoke_script(name: str, extra_env: dict[str, str] | None = None) -> dict[str, Any]:
    script = _repo_root() / "infra/scripts" / name
    if not script.is_file():
        return {"track": f"smoke_{name}", "ok": True, "skipped": True, "note": "script absent"}
    env = {**os.environ, **(extra_env or {})}
    try:
        proc = subprocess.run(
            ["bash", str(script)],
            capture_output=True,
            text=True,
            timeout=int(os.environ.get("LBG_TEAM_GODOT_VALIDATION_TIMEOUT_S", "90")),
            cwd=str(_repo_root()),
            env=env,
        )
        return {
            "track": f"smoke_{name.replace('.sh', '')}",
            "ok": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout_tail": (proc.stdout or "")[-600:],
            "stderr_tail": (proc.stderr or "")[-300:],
        }
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"track": f"smoke_{name}", "ok": False, "error": str(e)}


def execute_godot_validation_workflow(task: TeamTask) -> dict[str, object]:
    supervisor = execute_godot_supervisor(
        TeamTask(
            id=task.id,
            role="qa",
            objective=task.objective,
            status="running",
            priority=task.priority,
            approval_required=False,
            actor_id=task.actor_id,
            context={**task.context, "godot_mode": "supervisor"},
        )
    )

    probes: list[dict[str, object]] = list(supervisor.get("tracks") or [])
    probes.append(audit_zb0_readiness())

    if soe_m3_enabled() and task.context.get("godot_validation_soe", True):
        probes.append(probe_soe_m3_login())

    if task.context.get("godot_validation_mirror", True):
        probes.append(_run_smoke_script("smoke_godot_sidecar_mirror_lan.sh"))

    from team.owner_smokes import run_owner_smokes

    owner_bundle = str(task.context.get("owner_smoke_bundle") or "godot_login").strip()
    owner_smokes = (
        run_owner_smokes(bundle=owner_bundle) if task.context.get("run_owner_smokes", True) else None
    )
    if isinstance(owner_smokes, dict):
        for r in owner_smokes.get("results") or []:
            if isinstance(r, dict):
                probes.append(
                    {
                        "track": f"owner_{r.get('owner')}",
                        "ok": bool(r.get("ok")) if not r.get("skipped") else True,
                        "skipped": bool(r.get("skipped")),
                        "exit_code": r.get("exit_code"),
                    }
                )

    required = [p for p in probes if isinstance(p, dict) and not p.get("skipped")]
    supervisor_tracks = {
        str(t.get("track") or "")
        for t in (supervisor.get("tracks") or [])
        if isinstance(t, dict)
    }
    # Aligner sur le superviseur (blocking/advisory) : ne pas échouer sur
    # infographiste_assets si seul KO ; les smokes/owner hors superviseur restent bloquants.
    ok = bool(supervisor.get("ok"))
    for p in required:
        name = str(p.get("track") or "")
        if name in supervisor_tracks or name in _ADVISORY_VALIDATION_TRACKS:
            continue
        if not p.get("ok"):
            ok = False
            break
    if isinstance(owner_smokes, dict) and owner_smokes.get("ok") is False:
        ok = False

    prime_path = os.environ.get(
        "LBG_GODOT_PRIME_CLIENT_PATH",
        "/home/sdesh/projects/LBG_Studios/packages/prime-client",
    )
    lbg_path = _repo_root() / "lbg_client_godot"

    checklist = [
        f"Godot 2D Prime : godot4 --path {prime_path}",
        "Launchpad → J:\\swgemu\\clients\\prime-client (pas new_mmo)",
        "Vérifier bots Lia/Nix + login Teome (M11/M12)",
        "Si tout vert → approuver forge ou ZB L2",
    ]

    human_summary = format_validation_summary(
        title="Argus — validation client Godot (checklist humain)",
        probes=probes,
        checklist=checklist,
    )

    return {
        "kind": "godot_validation_workflow",
        "ok": ok,
        "smoke_ok": ok,
        "supervisor": supervisor,
        "probes": probes,
        "owner_smokes": owner_smokes,
        "human_summary": human_summary,
        "subproject": "client_godot",
        "launch_commands": {
            "prime_2d": f"godot4 --path {prime_path}",
            "lbg_3d": f"godot4 --path {lbg_path}",
            "sidecar_mirror": "bash packages/cortex/infra/scripts/smoke_godot_sidecar_mirror_lan.sh",
        },
    }


def resolve_godot_validation_workflow(task: TeamTask) -> bool:
    return _is_godot_validation(task)
