"""Spawn mission Team — D7 Session Island (Compagnon Desktop).

Vagues :
  P0 — cadrage docs (Thémis ADR + Métis schéma events) — **après clarifs Compagnon**
  P1 — MVP code (Métis emitter/overlay + Argus smoke) — **après GO + décisions remplies**

Gate : lit ``docs/SESSION_ISLAND_D7_DECISIONS.json`` (relatif monorepo) sauf override
``LBG_TEAM_SESSION_ISLAND_DECISIONS``.

Usage::

    # Dry-run (recommandé d'abord)
    LBG_ORCHESTRATOR_URL=http://192.168.0.140:8010 \\
      LBG_TEAM_SESSION_ISLAND_WAVE=P0 \\
      LBG_TEAM_SESSION_ISLAND_DRY_RUN=1 \\
      python -m lbg_agents.spawn_team_session_island_d7_job

    # Spawn réel P0
    LBG_TEAM_SESSION_ISLAND_WAVE=P0 \\
      LBG_TEAM_SESSION_ISLAND_DRY_RUN=0 \\
      python -m lbg_agents.spawn_team_session_island_d7_job

    # Phase 1 (code) — exige décisions complètes
    LBG_TEAM_SESSION_ISLAND_WAVE=P1 \\
      python -m lbg_agents.spawn_team_session_island_d7_job

Réf. : docs/PLAN_SESSION_ISLAND_D7.md · ADR 0027 · SESSION_ISLAND_D7_COMPAGNON_CLARIFS.md
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
from pathlib import Path
from typing import Any

from lbg_agents.team_job_spawn import (
    cooldown_active,
    create_and_run_team_task,
    load_json_state,
    save_json_state,
    task_run_summary,
    truthy,
)

_REPO_ROOT = Path(__file__).resolve().parents[5]  # …/LBG_Studios
_DEFAULT_DECISIONS = _REPO_ROOT / "docs" / "SESSION_ISLAND_D7_DECISIONS.json"

PLAN_REF = "docs/PLAN_SESSION_ISLAND_D7.md"
ADR_REF = "packages/cortex/docs/adr/0027-session-island-d7.md"
CLARIFS_REF = "docs/SESSION_ISLAND_D7_COMPAGNON_CLARIFS.md"

WAVE_TASKS: dict[str, list[tuple[str, str, dict[str, Any]]]] = {
    "P1B": [
        (
            "dev_studio",
            "Métis — Présence Agents P1b RÉEL (pas dry-run) : compléter / review le code déjà dans "
            "LBG_Studios : packages/cortex/linux_agent/Agent_IA/session_emitter.py + routes "
            "/session/* dans main.py + instrumentation run_cli_agent. "
            "Activer LBG_SESSION_ISLAND_ENABLED sur .143. Contrat session_island_events_v1.md. "
            "ide_cli_live=true · desktop_dry_run=false · jeton desktop_approval requis.",
            {
                "session_island_d7": True,
                "session_island_wave": "P1B",
                "product_name": "Présence Agents",
                "ide_cli": True,
                "ide_cli_live": True,
                "desktop_dry_run": False,
                "docs_only": False,
                "subproject": "linux_agent",
                "target_host": "omarchy",
                "ide_cli_cwd": "/home/lbg/projects/LBG_Studios",
            },
        ),
        (
            "dev_studio",
            "Métis — Présence Agents P1b RÉEL : finaliser compagnon-desktop sessionIsland "
            "(main.js SSE, overlay Allow/Deny, config) + client minimal "
            "linux_agent/Agent_IA/tools/presence_agents_client.py. "
            "ide_cli_live=true · desktop_dry_run=false · pas de dry-run.",
            {
                "session_island_d7": True,
                "session_island_wave": "P1B",
                "product_name": "Présence Agents",
                "ide_cli": True,
                "ide_cli_live": True,
                "desktop_dry_run": False,
                "docs_only": False,
                "subproject": "compagnon_desktop",
                "ide_cli_cwd": "/home/lbg/projects/LBG_Studios",
            },
        ),
        (
            "qa",
            "Argus — Présence Agents P1b : smoke ciblé session/status + stream (flags on) "
            "après Métis ; runbook_session_island_d7.md. Ne pas lancer smoke LAN générique "
            "si emitter absent. Block close si régression D6.",
            {
                "session_island_d7": True,
                "session_island_wave": "P1B",
                "product_name": "Présence Agents",
                "_require_owner_smoke": True,
            },
        ),
    ],
    "P0": [
        (
            "pm",
            "Thémis — D7 Session Island P0 : figer ADR 0027 (statut proposé→accepté si GO) "
            f"selon {CLARIFS_REF} + décisions JSON. Amender PLAN §9. "
            "Pas de code. Lister conditions si go_conditional. "
            f"Réf. {ADR_REF} · {PLAN_REF}.",
            {
                "session_island_d7": True,
                "session_island_wave": "P0",
                "docs_only": True,
                "adr": "0027",
            },
        ),
        (
            "dev_studio",
            "Métis — D7 P0 : publier le schéma JSON events v1 + 3 exemples "
            "(start / approval_needed / stop) sous packages/cortex/docs/ "
            "(ex. session_island_events_v1.md). Aligner bus_v1 depuis DECISIONS.json. "
            "Pas d’impl worker/Electron encore. "
            f"Réf. {PLAN_REF} §3.",
            {
                "session_island_d7": True,
                "session_island_wave": "P0",
                "docs_only": True,
                "subproject": "cortex_studio",
            },
        ),
    ],
    "P1": [
        (
            "dev_studio",
            "Métis — Présence Agents P1 : session_emitter + SSE GET /session/stream + POST /session/decision "
            "+ Unix socket $XDG_RUNTIME_DIR/lbg-presence-agents.sock dans linux_agent (.143). "
            "Instrumenter run_cli_agent (start/stop/error a minima). "
            "Flags LBG_SESSION_ISLAND_* opt-in off ; fail-open ; timeout 60s. "
            "Contrat : packages/cortex/docs/session_island_events_v1.md · ADR 0027 · ADR 0025. "
            "ide_cli=true · pas Godot · pas docs_only générique.",
            {
                "session_island_d7": True,
                "session_island_wave": "P1",
                "product_name": "Présence Agents",
                "ide_cli": True,
                "docs_only": False,
                "subproject": "linux_agent",
                "target_host": "omarchy",
            },
        ),
        (
            "dev_studio",
            "Métis — Présence Agents P1 : overlay Electron compagnon-desktop (.10) "
            "(ticker + Allow/Deny/Always-session + config sessionIsland.*) "
            "+ client minimal Omarchy .143 (SSE ou socket). Opt-in. "
            "Pas de dashboard ; pas de chat multi-LLM dans l’island. "
            f"Réf. {PLAN_REF} · session_island_events_v1.md. ide_cli=true.",
            {
                "session_island_d7": True,
                "session_island_wave": "P1",
                "product_name": "Présence Agents",
                "ide_cli": True,
                "docs_only": False,
                "subproject": "compagnon_desktop",
            },
        ),
        (
            "qa",
            "Argus — Présence Agents P1 : smoke LAN (flags on/off, Deny, timeout 60s fail-open, dual bus) "
            "+ runbook_session_island_d7.md. Miroir Pilot best-effort (ne bloque pas close). "
            "Block close si régression D6/Agir. "
            f"Réf. {PLAN_REF} §10 · ADR 0027.",
            {
                "session_island_d7": True,
                "session_island_wave": "P1",
                "product_name": "Présence Agents",
                "_require_owner_smoke": True,
            },
        ),
    ],
}


def job_enabled() -> bool:
    return truthy(os.environ.get("LBG_TEAM_SESSION_ISLAND_JOB_ENABLED", "1"))


def wave_id() -> str:
    raw = os.environ.get("LBG_TEAM_SESSION_ISLAND_WAVE", "P0").strip().upper()
    return raw if raw in WAVE_TASKS else "P0"


def _inject_approval(ctx: dict[str, Any]) -> dict[str, Any]:
    """Passe LBG_DESKTOP_APPROVAL_TOKEN / LBG_LINUX_APPROVAL_TOKEN si présent dans l'env spawn."""
    tok = (
        os.environ.get("LBG_DESKTOP_APPROVAL_TOKEN")
        or os.environ.get("LBG_LINUX_APPROVAL_TOKEN")
        or ""
    ).strip()
    if tok and ctx.get("ide_cli_live"):
        ctx = {**ctx, "desktop_approval": tok}
    return ctx


def spawn_actor_id() -> str:
    return os.environ.get("LBG_TEAM_SESSION_ISLAND_ACTOR_ID", "system:team_session_island_d7").strip()


def state_path() -> Path:
    raw = os.environ.get("LBG_TEAM_SESSION_ISLAND_STATE", "").strip()
    if raw:
        return Path(raw)
    return Path("/var/lib/lbg/team_session_island_d7/state.json")


def decisions_path() -> Path:
    raw = os.environ.get("LBG_TEAM_SESSION_ISLAND_DECISIONS", "").strip()
    if raw:
        return Path(raw)
    return _DEFAULT_DECISIONS


def cooldown_s() -> float:
    try:
        return max(300.0, float(os.environ.get("LBG_TEAM_SESSION_ISLAND_COOLDOWN_S", "3600")))
    except ValueError:
        return 3600.0


def load_decisions() -> dict[str, Any]:
    path = decisions_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def gate_reason(wave: str, decisions: dict[str, Any]) -> str | None:
    """None = OK à spawner. Sinon message d’erreur gate."""
    go = decisions.get("go")
    gate = (decisions.get("spawn_gate") or {}) if isinstance(decisions.get("spawn_gate"), dict) else {}

    if wave == "P0":
        allowed = gate.get("P0_allowed_go") or ["go", "go_conditional"]
        required = gate.get("P0_requires") or ["go"]
        for key in required:
            if decisions.get(key) in (None, ""):
                return (
                    f"gate P0 : '{key}' manquant — passer par le Compagnon "
                    f"({CLARIFS_REF}) puis remplir {decisions_path()}"
                )
        if go not in allowed:
            return f"gate P0 : go={go!r} non autorisé (attendu {allowed})"
        return None

    if wave in ("P1", "P1B"):
        allowed = gate.get("P1_allowed_go") or ["go", "go_conditional"]
        required = gate.get("P1_requires") or [
            "go",
            "bus_v1",
            "island_targets",
            "pilot_mirror_p1",
            "product_name",
        ]
        missing = [k for k in required if decisions.get(k) in (None, "")]
        if missing:
            return f"gate {wave} : décisions manquantes {missing} — {CLARIFS_REF}"
        if go not in allowed:
            return f"gate {wave} : go={go!r} non autorisé (attendu {allowed})"
        return None

    return f"vague inconnue {wave!r}"


def run_spawn(*, persist: bool = True, run_tasks: bool | None = None) -> dict[str, Any]:
    if not job_enabled():
        return {"ok": True, "outcome": "skipped", "spawned": False, "agent": "spawn_team_session_island_d7_job"}

    wave = wave_id()
    dry_run = truthy(os.environ.get("LBG_TEAM_SESSION_ISLAND_DRY_RUN", "0"))
    bypass_gate = truthy(os.environ.get("LBG_TEAM_SESSION_ISLAND_BYPASS_GATE", "0"))
    if run_tasks is None:
        run_tasks = truthy(os.environ.get("LBG_TEAM_SESSION_ISLAND_RUN_TASKS", "1")) and not dry_run

    decisions = load_decisions()
    result: dict[str, Any] = {
        "ok": True,
        "agent": "spawn_team_session_island_d7_job",
        "wave": wave,
        "dry_run": dry_run,
        "spawned": False,
        "task_ids": [],
        "tasks": [],
        "decisions_path": str(decisions_path()),
        "go": decisions.get("go"),
    }

    if not bypass_gate:
        blocked = gate_reason(wave, decisions)
        if blocked:
            result["ok"] = False
            result["outcome"] = "gate_blocked"
            result["error"] = blocked
            result["hint"] = (
                "Remplir docs/SESSION_ISLAND_D7_DECISIONS.json via Compagnon, "
                "ou LBG_TEAM_SESSION_ISLAND_BYPASS_GATE=1 (lab only)."
            )
            return result

    st = load_json_state(state_path()) if persist else {}
    cool_key = f"last_spawn_ts_{wave}"
    if persist and not dry_run and cooldown_active(st, key=cool_key, cooldown_s=cooldown_s()):
        result["outcome"] = "cooldown"
        result["cooldown_key"] = cool_key
        return result

    mid = f"session_island_d7_{wave}_{int(time.time())}"
    actor = spawn_actor_id()
    specs = WAVE_TASKS[wave]
    ctx_decisions = {
        "bus_v1": decisions.get("bus_v1"),
        "island_targets": decisions.get("island_targets"),
        "pilot_mirror_p1": decisions.get("pilot_mirror_p1"),
        "product_name": decisions.get("product_name"),
        "approval_timeout_s": decisions.get("approval_timeout_s"),
        "always_allow_scope": decisions.get("always_allow_scope"),
    }

    if dry_run:
        result["outcome"] = "dry_run"
        result["mission_tag"] = mid
        result["planned"] = [
            {"role": r, "objective": o[:200], "context_keys": sorted(c.keys())} for r, o, c in specs
        ]
        result["decisions_snapshot"] = ctx_decisions
        return result

    try:
        for role, objective, extra in specs:
            ctx = _inject_approval(
                {
                    "_campus_mission_id": mid,
                    "_campus_mission_objective": f"D7 Session Island Vague {wave}",
                    "focus": "PLAN_SESSION_ISLAND_D7",
                    "adr": "0027",
                    **ctx_decisions,
                    **extra,
                }
            )
            payload = create_and_run_team_task(
                role=role,
                objective=objective,
                actor_id=actor,
                context=ctx,
                run=run_tasks,
                timeout=300,
            )
            summary = task_run_summary(payload) if run_tasks else {"task_id": payload.get("task_id")}
            result["tasks"].append({"role": role, **summary})
            tid = summary.get("task_id")
            if tid:
                result["task_ids"].append(tid)

        result["spawned"] = True
        result["mission_tag"] = mid
        result["outcome"] = "ran" if run_tasks else "queued"
        if persist:
            save_json_state(
                state_path(),
                {
                    **st,
                    cool_key: time.time(),
                    "last_wave": wave,
                    "last_mission_tag": mid,
                    "last_task_ids": result["task_ids"],
                },
            )
    except (urllib.error.URLError, OSError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
        result["ok"] = False
        result["outcome"] = "error"
        result["error"] = str(exc)

    return result


def main() -> int:
    result = run_spawn()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("outcome") == "gate_blocked":
        return 2
    return 0 if result.get("ok") else 3


if __name__ == "__main__":
    raise SystemExit(main())
