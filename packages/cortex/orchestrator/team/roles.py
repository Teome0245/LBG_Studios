"""Exécution des rôles équipe virtuelle (phase A : ops, qa, pm)."""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
import uuid
from typing import Callable

from lbg_agents.dispatch import invoke_after_route

from team import store as team_store
from team.models import TeamTask
from team.core3_build_workflow import execute_core3_build_workflow, resolve_core3_build_workflow
from team.dev_game_workflow import execute_dev_game_workflow
from team.godot_client_tracks_workflow import (
    execute_godot_client_tracks_workflow,
    resolve_godot_client_tracks_workflow,
)
from team.m9_map_workflow import execute_m9_map_workflow, resolve_m9_map_workflow
from team.m9_map_followup import (
    auto_run_followup_tasks as m9_auto_run_followup,
    maybe_spawn_after_m9_failure,
)
from team.godot_client_workflow import execute_godot_client_workflow, resolve_godot_client_workflow
from team.godot_dev_workflow import execute_godot_dev_workflow, resolve_godot_dev_workflow
from team.godot_followup import auto_run_followup_tasks as godot_auto_run_followup
from team.godot_followup import maybe_spawn_after_godot_failure
from team.godot_supervisor import execute_godot_supervisor
from team.godot_validation_workflow import execute_godot_validation_workflow, resolve_godot_validation_workflow
from team.infographiste_lora_workflow import execute_infographiste_lora_workflow, resolve_infographiste_lora_workflow
from team.sprites_2d_workflow import execute_sprites_2d_workflow, resolve_sprites_2d_workflow
from team.face_parts_workflow import execute_face_parts_workflow, resolve_face_parts_workflow
from team.infographiste_workflow import execute_infographiste_workflow, resolve_infographiste_workflow
from team.player_ia_exec import execute_player_ia
from team.admin_infra_workflow import execute_admin_infra_workflow
from team.contrarian_workflow import execute_contrarian_workflow
from team.qa_followup import auto_run_followup_tasks, maybe_spawn_after_qa_failure
from team.failure_followup import (
    auto_run_followup_tasks as failure_auto_run_followup,
    maybe_spawn_after_failure,
)
from team.cursor_agent_workflow import run_cursor_cloud_from_task
from team.autoconsult_workflow import execute_autoconsult_workflow, resolve_autoconsult_workflow
from team.evolution_sprint_workflow import (
    execute_evolution_sprint_workflow,
    resolve_evolution_sprint_workflow,
)
from team.evolution_veille_workflow import (
    execute_evolution_veille_workflow,
    resolve_evolution_veille_workflow,
)
from team.role_aliases import role_display

Dispatcher = Callable[..., dict[str, object]]

_dispatch: Dispatcher = invoke_after_route

ROLE_SPECS: dict[str, dict[str, object]] = {
    "ops": {
        "capability": "devops_probe",
        "routed_to": "agent.devops",
        "autonomy": "L1",
        "default_objective": "Sonde santé orchestrateur et backend (read-only)",
    },
    "qa": {
        "capability": "team.qa",
        "routed_to": "agent.devops",
        "autonomy": "L1",
        "default_objective": "Smoke LAN read-only (healthz + systemd via script si configuré)",
    },
    "pm": {
        "capability": "project_pm",
        "routed_to": "agent.pm",
        "autonomy": "L0-L1",
        "default_objective": "Brief jalons et prochaines tâches projet",
    },
    "dev_game": {
        "capability": "prototype_game",
        "routed_to": "agent.pm",
        "autonomy": "L0-L1",
        "default_objective": "Analyser bug gameplay / correctif proposé (hors sandbox mmmorpg gelé)",
    },
    "dev_godot": {
        "capability": "godot_dev_ia",
        "routed_to": "agent.pm",
        "autonomy": "L0-L1",
        "default_objective": "Audit / prototype Godot Prime — Iris (2D UI) ou Hermès (SOE/gateway)",
    },
    "player_ia": {
        "capability": "core3_bot_action",
        "routed_to": "agent.core3",
        "autonomy": "L1",
        "default_objective": (
            "Chœur du monde — sonde joueurs IA Prime 246 (sidecar) ; "
            "à terme garant runtime Bible/M10 Pre-CU-LBG"
        ),
    },
    "admin_infra": {
        "capability": "devops_probe",
        "routed_to": "agent.devops",
        "autonomy": "L1",
        "default_objective": (
            "Responsable plateforme LLM locale : capacite, deploiement, bench, stabilite, "
            "watchdogs, reprise auto, budgets materiels"
        ),
    },
    "contrarian": {
        "capability": "second_opinion",
        "routed_to": "agent.pm",
        "autonomy": "L0",
        "default_objective": (
            "Prométhée — avis complémentaires et alternatives hors cadre "
            "(LLM uncensored, consultatif uniquement)"
        ),
    },
}


def _trace_log(event: dict[str, object]) -> None:
    path = os.environ.get("LBG_TEAM_TRACE_PATH", "").strip()
    if not path:
        state = team_store.db_path()
        parent = os.path.dirname(state) if state and state != ":memory:" else "."
        path = os.path.join(parent or ".", "team_trace.jsonl")
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        line = json.dumps({**event, "ts": time.time()}, ensure_ascii=False)
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def approval_token_valid(token: str | None) -> bool:
    expected = os.environ.get("LBG_TEAM_APPROVAL_TOKEN", "").strip()
    if not expected:
        for fallback in (
            "LBG_DEVOPS_APPROVAL_TOKEN",
            "LBG_JOBS_APPROVAL_TOKEN",
        ):
            expected = os.environ.get(fallback, "").strip()
            if expected:
                break
    if not expected:
        # Soft (tout token non vide) uniquement si explicitement autorisé (tests/lab).
        soft = os.environ.get("LBG_TEAM_APPROVAL_SOFT", "0").strip().lower() in (
            "1",
            "true",
            "yes",
            "on",
        )
        if soft:
            return bool(token and str(token).strip())
        return False
    return bool(token and str(token).strip() == expected)


def _orchestrator_url() -> str:
    return os.environ.get("LBG_ORCHESTRATOR_SELF_URL", "http://127.0.0.1:8010").rstrip("/")


def _backend_url() -> str:
    return os.environ.get("LBG_BACKEND_SELF_URL", "http://127.0.0.1:8000").rstrip("/")


def _inject_devops_approval(ctx: dict[str, object]) -> dict[str, object]:
    """Pour sondes Team L1 (healthz) : injecte le jeton d'approbation DevOps si présent."""
    if ctx.get("devops_approval"):
        return ctx
    tok = os.environ.get("LBG_DEVOPS_APPROVAL_TOKEN", "").strip()
    if tok:
        ctx = dict(ctx)
        ctx["devops_approval"] = tok
    return ctx


def _qa_health_targets() -> list[str]:
    raw = os.environ.get(
        "LBG_TEAM_QA_HEALTH_URLS",
        f"{_orchestrator_url()}/healthz,{_backend_url()}/healthz",
    )
    return [u.strip() for u in raw.split(",") if u.strip()]


def _run_qa_smoke_script() -> dict[str, object]:
    script = os.environ.get("LBG_TEAM_QA_SMOKE_SCRIPT", "").strip()
    if not script or not os.path.isfile(script):
        return {"skipped": True, "reason": "LBG_TEAM_QA_SMOKE_SCRIPT non configuré"}
    timeout = int(os.environ.get("LBG_TEAM_QA_SMOKE_TIMEOUT_S", "120"))
    try:
        proc = subprocess.run(
            ["bash", script],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "exit_code": proc.returncode,
            "stdout_tail": (proc.stdout or "")[-2000:],
            "stderr_tail": (proc.stderr or "")[-1000:],
            "ok": proc.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"timeout après {timeout}s"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _execute_ops(task: TeamTask) -> dict[str, object]:
    ctx = dict(task.context)
    ops_kind = str(ctx.get("ops_kind") or "").strip().lower()

    storage = ctx.get("proxmox_storage")
    if ops_kind == "proxmox_storage" and isinstance(storage, dict):
        outcome = str(storage.get("outcome") or "ok")
        ok = outcome != "critical"
        return {"kind": "ops_storage", "storage": storage, "outcome": outcome, "ok": ok}

    # ops_kind storage sans payload pré-calculé → devops_probe proxmox_storage
    if ops_kind == "proxmox_storage" and not isinstance(ctx.get("devops_action"), dict):
        ctx["devops_action"] = {"kind": "proxmox_storage"}

    hw = ctx.get("proxmox_hw")
    if ops_kind == "proxmox_hw" and isinstance(hw, dict):
        outcome = str(hw.get("outcome") or "ok")
        ok = outcome != "critical"
        return {"kind": "ops_hw", "proxmox_hw": hw, "outcome": outcome, "ok": ok}

    guest_metrics = ctx.get("guest_metrics")
    if ops_kind == "guest_metrics" and isinstance(guest_metrics, dict):
        from lbg_agents.infra_guest_remediation import build_guest_remediation_plan, format_guest_plan_reply

        plan = ctx.get("remediation_plan")
        if not isinstance(plan, dict):
            plan = build_guest_remediation_plan(guest_metrics)
        outcome = str(guest_metrics.get("outcome") or "ok")
        # warn/critical = alerte infra + plan consultatif — pas un échec de l'agent ops
        ok = True
        return {
            "kind": "ops_guest_metrics",
            "guest_metrics": guest_metrics,
            "remediation_plan": plan,
            "outcome": outcome,
            "ok": ok,
            "reply": format_guest_plan_reply(plan),
            "suggested_actions": plan.get("suggested_actions") or [],
        }
    if ops_kind == "guest_metrics" and not isinstance(ctx.get("devops_action"), dict):
        ctx["devops_action"] = {"kind": "guest_metrics"}

    # Guest mur : dispatcher agent.devops (kind=guest_metrics) sans basculer en healthz.
    if ops_kind == "guest_metrics" and isinstance(ctx.get("devops_action"), dict):
        action = ctx.get("devops_action") or {}
        if str(action.get("kind") or "").strip().lower() == "guest_metrics":
            from lbg_agents.infra_guest_remediation import (
                build_guest_remediation_plan,
                format_guest_plan_reply,
            )

            ctx = dict(ctx)
            ctx.setdefault("devops_dry_run", False)
            ctx = _inject_devops_approval(ctx)
            out = _dispatch(
                "agent.devops",
                actor_id=task.actor_id,
                text=task.objective,
                context=ctx,
            )
            res = out.get("result") if isinstance(out.get("result"), dict) else {}
            wall = res.get("guest_metrics") if isinstance(res.get("guest_metrics"), dict) else res
            if not isinstance(wall, dict) or "hosts" not in wall:
                # run_guest_metrics_probe renvoie souvent le wall à la racine du result
                wall = res if isinstance(res, dict) and "hosts" in res else {}
            plan = build_guest_remediation_plan(wall if wall else None)
            outcome = str((wall or {}).get("outcome") or "ok")
            # Sonde + plan OK même si mur critical (remédiation L1, pas hard-fail agent)
            ok = bool(out.get("ok", True))
            if isinstance(out.get("error"), str) and out["error"]:
                ok = False
            if not wall:
                ok = False
            return {
                "kind": "ops_guest_metrics",
                "guest_metrics": wall,
                "remediation_plan": plan,
                "outcome": outcome,
                "ok": ok,
                "reply": format_guest_plan_reply(plan),
                "suggested_actions": plan.get("suggested_actions") or [],
                "output": out,
            }

    guest_lock = ctx.get("proxmox_guest_lock")
    if ops_kind == "proxmox_guest_lock" and isinstance(guest_lock, dict):
        outcome = str(guest_lock.get("outcome") or "ok")
        ok = outcome != "critical"
        return {
            "kind": "ops_guest_lock",
            "proxmox_guest_lock": guest_lock,
            "outcome": outcome,
            "ok": ok,
        }
    if ops_kind == "proxmox_guest_lock" and not isinstance(ctx.get("devops_action"), dict):
        ctx["devops_action"] = {"kind": "proxmox_guest_lock"}

    if ctx.get("m9_ops_sync") or ops_kind == "m9_prime_sync":
        if os.environ.get("LBG_TEAM_OPS_USE_OPENCLAW", "1").strip().lower() in ("1", "true", "yes", "on"):
            from team.openclaw_adapter import run_ops_playbook

            out = run_ops_playbook("m9_prime_sync")
            out["kind"] = "ops_m9_sync"
            return out
        from pathlib import Path

        root = Path(__file__).resolve().parents[2]
        script = root / "infra/scripts/sync_prime_client_assets_vm.sh"
        if not script.is_file():
            return {"kind": "ops_m9_sync", "ok": False, "error": f"script absent: {script}"}
        try:
            proc = subprocess.run(
                ["bash", str(script)],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
            )
            ok = proc.returncode == 0
            return {
                "kind": "ops_m9_sync",
                "ok": ok,
                "returncode": proc.returncode,
                "stdout_tail": (proc.stdout or "")[-500:],
                "stderr_tail": (proc.stderr or "")[-500:],
            }
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {"kind": "ops_m9_sync", "ok": False, "error": str(exc)}

    if ops_kind in ("ollama", "ollama_audit") or ctx.get("ollama_audit"):
        from team.ollama_audit import audit_ollama_lan

        return {"kind": "ops_ollama_audit", **audit_ollama_lan()}

    # Inventaire LAN + diff apparus/disparus (Héphaïstos)
    if ops_kind == "network_inventory" or ctx.get("_team_network_inventory_spawn"):
        pre = ctx.get("network_inventory")
        if isinstance(pre, dict) and (pre.get("diff") is not None or pre.get("devices") is not None):
            diff = pre.get("diff") if isinstance(pre.get("diff"), dict) else {}
            n_app = int(diff.get("n_appeared") or 0)
            n_dis = int(diff.get("n_disappeared") or 0)
            reply = str(pre.get("reply") or "")
            if not reply:
                reply = (
                    f"Inventaire LAN — +{n_app} apparus / −{n_dis} disparus "
                    f"({pre.get('n_present', '?')}/{pre.get('n_devices', '?')} présents)"
                )
            return {
                "kind": "ops_network_inventory",
                "ok": bool(pre.get("ok", True)),
                "network_inventory": pre,
                "diff": diff,
                "by_role": pre.get("by_role"),
                "n_present": pre.get("n_present"),
                "n_devices": pre.get("n_devices"),
                "cast_speakers": pre.get("cast_speakers"),
                "reply": reply,
                "outcome": "changed" if (n_app or n_dis) else "stable",
            }
        inv_ctx = dict(ctx)
        inv_ctx.setdefault("persist_state", True)
        inv_ctx.setdefault("freebox_lan", True)
        inv_ctx.setdefault("cast_probe", True)
        out = _dispatch(
            "agent.network",
            actor_id=task.actor_id,
            text=task.objective,
            context=inv_ctx,
        )
        res = out.get("result") if isinstance(out.get("result"), dict) else out
        if not isinstance(res, dict):
            res = {}
        diff = res.get("diff") if isinstance(res.get("diff"), dict) else {}
        ok = bool(out.get("ok", True)) and bool(res.get("ok", True))
        return {
            "kind": "ops_network_inventory",
            "ok": ok,
            "network_inventory": res,
            "diff": diff,
            "by_role": res.get("by_role"),
            "n_present": res.get("n_present"),
            "n_devices": res.get("n_devices"),
            "cast_speakers": res.get("cast_speakers"),
            "reply": res.get("reply") or out.get("reply"),
            "output": out,
            "outcome": (
                "changed"
                if int(diff.get("n_appeared") or 0) or int(diff.get("n_disappeared") or 0)
                else "stable"
            ),
        }

    orch = _orchestrator_url()
    action = ctx.get("devops_action")
    if not isinstance(action, dict):
        action = {"kind": "http_get", "url": f"{orch}/healthz"}

    # Sonde multi-URL (:8010 + :8000) — http_get n'accepte qu'un `url` string.
    urls: list[str] = []
    raw_urls = action.get("urls")
    if isinstance(raw_urls, list):
        urls = [str(u).strip() for u in raw_urls if str(u).strip()]
    single = action.get("url")
    if isinstance(single, str) and single.strip():
        urls = [single.strip()] + [u for u in urls if u != single.strip()]
    if ops_kind == "health_probe" and not urls:
        urls = [
            f"{_orchestrator_url()}/healthz",
            f"{_backend_url()}/healthz",
        ]
    if not urls:
        urls = [f"{orch}/healthz"]

    # Healthz réels sauf dry-run explicite.
    live_probe = ops_kind == "health_probe" or bool(
        re.search(r"(?i):8010|:8000|healthz|sonde", task.objective or "")
    )
    if live_probe and "devops_dry_run" not in task.context:
        ctx["devops_dry_run"] = False
    else:
        ctx.setdefault("devops_dry_run", True)

    if len(urls) == 1:
        ctx["devops_action"] = {"kind": "http_get", "url": urls[0]}
        if not ctx.get("devops_dry_run"):
            ctx = _inject_devops_approval(ctx)
        out = _dispatch(
            "agent.devops",
            actor_id=task.actor_id,
            text=task.objective,
            context=ctx,
        )
        ok = bool(out.get("ok", True))
        res = out.get("result")
        if isinstance(res, dict) and res.get("ok") is False:
            ok = False
        if isinstance(out.get("error"), str) and out["error"]:
            ok = False
        return {
            "kind": "ops_probe",
            "output": out,
            "ok": ok,
            "human_summary": f"Sonde {urls[0]} → {'ok' if ok else 'KO'}",
        }

    checks: list[dict[str, object]] = []
    all_ok = True
    for url in urls:
        sub = dict(ctx)
        sub["devops_action"] = {"kind": "http_get", "url": url}
        if not sub.get("devops_dry_run"):
            sub = _inject_devops_approval(sub)
        out = _dispatch(
            "agent.devops",
            actor_id=task.actor_id,
            text=f"Sonde {url}",
            context=sub,
        )
        ok = bool(out.get("ok", False))
        res = out.get("result")
        if isinstance(res, dict) and res.get("ok") is True:
            ok = True
        if isinstance(res, dict) and res.get("ok") is False:
            ok = False
        if isinstance(out.get("error"), str) and out["error"]:
            ok = False
        checks.append({"url": url, "ok": ok, "output": out})
        all_ok = all_ok and ok
    summary = "; ".join(f"{c['url']}={'ok' if c['ok'] else 'KO'}" for c in checks)
    return {
        "kind": "ops_health_probe",
        "checks": checks,
        "ok": all_ok,
        "human_summary": f"Sondes healthz — {summary}",
    }


def _qa_health_dry_run() -> bool:
    return os.environ.get("LBG_TEAM_QA_HEALTH_DRY_RUN", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _execute_qa(task: TeamTask) -> dict[str, object]:
    ctx0 = task.context or {}
    wf = str(ctx0.get("workflow") or "").strip().lower()
    if (
        ctx0.get("agent_mutation")
        or ctx0.get("agent_mutation_review")
        or wf in ("agent_mutator", "agent_mutator_review")
    ):
        from team.agent_mutator import execute_mutator_from_task

        return execute_mutator_from_task(task)

    bundle = str(task.context.get("owner_smoke_bundle") or "").strip()
    health_dry = _qa_health_dry_run()
    if bundle:
        from team.owner_smokes import run_owner_smokes

        owner_out = run_owner_smokes(bundle=bundle)
        health_ok = True
        # healthz léger en plus du bundle
        checks: list[dict[str, object]] = []
        for url in _qa_health_targets()[:2]:
            ctx = {
                "devops_action": {"kind": "http_get", "url": url},
                "devops_dry_run": health_dry,
            }
            if not health_dry:
                ctx = _inject_devops_approval(ctx)
            out = _dispatch(
                "agent.devops",
                actor_id=task.actor_id,
                text=f"QA healthz {url}",
                context=ctx,
            )
            ok = bool(out.get("ok", False))
            if not ok:
                res = out.get("result")
                if isinstance(res, dict) and res.get("ok") is True:
                    ok = True
            checks.append({"url": url, "ok": ok})
            health_ok = health_ok and ok
        all_ok = bool(owner_out.get("ok")) and health_ok
        return {
            "kind": "qa_owner_smokes",
            "ok": all_ok,
            "smoke_ok": bool(owner_out.get("ok")),
            "owner_smokes": owner_out,
            "health_checks": checks,
            "bundle": bundle,
        }

    if resolve_godot_validation_workflow(task):
        return execute_godot_validation_workflow(task)
    if task.context.get("godot_supervisor") or str(task.context.get("godot_mode", "")).strip().lower() in (
        "full",
        "supervisor",
        "sidecar",
        "gateway",
        "audit",
    ):
        return execute_godot_supervisor(task)

    checks: list[dict[str, object]] = []
    all_ok = True
    for url in _qa_health_targets():
        ctx = {
            "devops_action": {"kind": "http_get", "url": url},
            "devops_dry_run": health_dry,
        }
        if not health_dry:
            ctx = _inject_devops_approval(ctx)
        out = _dispatch(
            "agent.devops",
            actor_id=task.actor_id,
            text=f"QA healthz {url}",
            context=ctx,
        )
        ok = bool(out.get("ok", False))
        res = out.get("result")
        if isinstance(res, dict) and res.get("ok") is True:
            ok = True
        if isinstance(res, dict) and res.get("ok") is False:
            ok = False
        checks.append({"url": url, "ok": ok, "output": out})
        all_ok = all_ok and ok

    smoke = _run_qa_smoke_script()
    if smoke.get("skipped") is not True:
        all_ok = all_ok and bool(smoke.get("ok"))

    summary = "; ".join(
        f"{c['url']}={'ok' if c['ok'] else 'KO'}" for c in checks
    )
    return {
        "kind": "qa_smoke",
        "health_checks": checks,
        "smoke_script": smoke,
        "ok": all_ok,
        "human_summary": f"Smoke QA healthz — {summary}"
        + ("" if smoke.get("skipped") else f" · script={'ok' if smoke.get('ok') else 'KO'}"),
    }


def _failure_triage_topics(objective: str) -> list[str]:
    text = (objective or "").lower()
    topics: list[str] = []
    mapping = (
        ("scrapaltai", ("scrapaltai", "m9a", "m9 ")),
        ("infographiste", ("infographiste", "infograph", "glb", "lora")),
        ("player_ia", ("player_ia", "joueurs ia", "sidecar", "lia", "nix")),
    )
    for label, keys in mapping:
        if any(k in text for k in keys):
            topics.append(label)
    return topics


def _execute_failure_triage(task: TeamTask) -> dict[str, object]:
    """Thémis — liste les failed récents et propose relance / abandon."""
    topics = _failure_triage_topics(task.objective)
    failed = team_store.list_tasks(status="failed", limit=80)
    items: list[dict[str, object]] = []
    for t in failed:
        blob = f"{t.objective} {t.role} {json.dumps(t.result or {}, ensure_ascii=False)[:400]}".lower()
        if topics and not any(top.replace("_", " ") in blob or top in blob for top in topics):
            # player_ia / scrapaltai / infographiste
            hit = False
            for top in topics:
                keys = {
                    "scrapaltai": ("scrapaltai", "m9a", "m9"),
                    "infographiste": ("infographiste", "glb", "lora", "pipeline assets"),
                    "player_ia": ("player_ia", "joueur", "sidecar", "lia", "nix"),
                }.get(top, (top,))
                if any(k in blob for k in keys):
                    hit = True
                    break
            if not hit:
                continue
        err = ""
        if isinstance(t.result, dict):
            err = str(t.result.get("error") or t.result.get("human_summary") or "")[:180]
        # Heuristique : doublons / même objectif → abandonner ; sinon relancer
        same = sum(
            1
            for o in failed
            if o.objective == t.objective and o.role == t.role
        )
        action = "abandonner" if same >= 3 else "relancer"
        reason = (
            f"{same} échecs identiques — abandonner pour éviter de gonfler la file"
            if action == "abandonner"
            else "échec isolé ou rare — relancer une fois après correctif ciblé"
        )
        items.append(
            {
                "task_id": t.id,
                "role": t.role,
                "objective": (t.objective or "")[:120],
                "error": err,
                "action": action,
                "reason": reason,
                "duplicates": same,
            }
        )
        if len(items) >= 15:
            break

    # Regrouper par action pour le résumé
    to_retry = [i for i in items if i["action"] == "relancer"]
    to_drop = [i for i in items if i["action"] == "abandonner"]
    lines = [
        f"Triage failed ({len(items)} match"
        + (f" topics={','.join(topics)}" if topics else "")
        + ")",
        f"- relancer : {len(to_retry)}",
        f"- abandonner : {len(to_drop)}",
    ]
    for i in items[:8]:
        lines.append(
            f"- [{i['action']}] {i['role']} `{str(i['task_id'])[:8]}` — {i['objective']}"
        )
    return {
        "kind": "failure_triage",
        "ok": True,
        "topics": topics,
        "items": items,
        "retry_ids": [str(i["task_id"]) for i in to_retry],
        "abandon_ids": [str(i["task_id"]) for i in to_drop],
        "human_summary": "\n".join(lines),
    }


def _execute_pm(task: TeamTask) -> dict[str, object]:
    ctx0 = task.context or {}
    wf = str(ctx0.get("workflow") or "").strip().lower()
    from team.docs_write_workflow import execute_docs_only_workflow, resolve_docs_only

    if resolve_docs_only(task):
        return execute_docs_only_workflow(task)
    if (
        ctx0.get("agent_mutation")
        or ctx0.get("agent_mutation_review")
        or wf in ("agent_mutator", "agent_mutator_review")
    ):
        from team.agent_mutator import execute_mutator_from_task

        return execute_mutator_from_task(task)
    if (
        ctx0.get("feature_proposal")
        or ctx0.get("feature_proposal_review")
        or wf in ("feature_proposer", "feature_proposal_review")
    ):
        from team.feature_proposer import execute_proposer_from_task

        return execute_proposer_from_task(task)

    # Veille avant sprint : « évolution » apparaît dans les deux, priorité au brief pistes.
    if resolve_evolution_veille_workflow(task):
        return execute_evolution_veille_workflow(task, _dispatch)
    if resolve_evolution_sprint_workflow(task):
        return execute_evolution_sprint_workflow(task, _dispatch)
    if resolve_autoconsult_workflow(task):
        return execute_autoconsult_workflow(task, _dispatch)

    from team.m11_login_workflow import execute_m11_contract_workflow, resolve_m11_contract_workflow
    from team.subprojects import list_subprojects

    if resolve_m11_contract_workflow(task):
        return execute_m11_contract_workflow(task, _dispatch)

    ctx = dict(task.context)
    if ctx.get("failure_triage") or re.search(
        r"(?i)\btriage\b.{0,40}\bfailed\b|\bfailed\b.{0,40}\b(relancer|abandonner)\b",
        task.objective or "",
    ):
        return _execute_failure_triage(task)

    ctx.setdefault("pm_focus", True)
    ctx.setdefault("project_pm", {"include_plan": True, "include_structure": True})
    reunification = bool(
        ctx.get("reunification_brief")
        or ctx.get("_team_pm_reunification_spawn")
        or re.search(r"\b(réunification|reunification|sous-projets?|thémis)\b", task.objective, re.I)
    )
    if reunification:
        ctx.setdefault("pm_include_plan", True)
        ctx.setdefault("pm_include_structure", True)
        ctx["reunification_brief"] = True
        ctx["subprojects"] = list_subprojects()
    out = _dispatch(
        "agent.pm",
        actor_id=task.actor_id,
        text=task.objective,
        context=ctx,
    )
    result: dict[str, object] = {"kind": "pm_brief", "output": out, "ok": True}
    if reunification:
        result["reunification"] = True
        result["subprojects_count"] = len(ctx.get("subprojects") or [])
    return result


def _execute_dev_godot(task: TeamTask) -> dict[str, object]:
    from team.docs_write_workflow import execute_docs_only_workflow, resolve_docs_only
    from team.ide_cli_workflow import execute_ide_cli_workflow, resolve_ide_cli_workflow

    if resolve_docs_only(task):
        return execute_docs_only_workflow(task)
    if resolve_ide_cli_workflow(task):
        return execute_ide_cli_workflow(task, _dispatch)
    if resolve_godot_dev_workflow(task):
        return execute_godot_dev_workflow(task, _dispatch)
    return execute_godot_dev_workflow(task, _dispatch)


def _execute_dev_game(task: TeamTask) -> dict[str, object]:
    ctx = task.context or {}
    from team.docs_write_workflow import execute_docs_only_workflow, resolve_docs_only
    from team.ide_cli_workflow import execute_ide_cli_workflow, resolve_ide_cli_workflow

    if resolve_docs_only(task):
        return execute_docs_only_workflow(task)
    if resolve_ide_cli_workflow(task):
        return execute_ide_cli_workflow(task, _dispatch)
    if ctx.get("cursor_cloud_agent") or str(ctx.get("workflow") or "").strip().lower() in (
        "cursor_cloud_agent",
        "cursor_agent",
    ):
        return run_cursor_cloud_from_task(task)
    if resolve_infographiste_lora_workflow(task):
        return execute_infographiste_lora_workflow(task, _dispatch)
    if resolve_face_parts_workflow(task):
        return execute_face_parts_workflow(task, _dispatch)
    if resolve_sprites_2d_workflow(task):
        return execute_sprites_2d_workflow(task, _dispatch)
    if resolve_infographiste_workflow(task):
        return execute_infographiste_workflow(task, _dispatch)
    if resolve_core3_build_workflow(task):
        return execute_core3_build_workflow(task, _dispatch)
    if resolve_m9_map_workflow(task):
        return execute_m9_map_workflow(task, _dispatch)
    if resolve_godot_client_tracks_workflow(task):
        return execute_godot_client_tracks_workflow(task, _dispatch)
    if resolve_godot_client_workflow(task):
        return execute_godot_client_workflow(task, _dispatch)
    return execute_dev_game_workflow(task, _dispatch)


def _execute_player_ia(task: TeamTask) -> dict[str, object]:
    return execute_player_ia(task)


def _execute_admin_infra(task: TeamTask) -> dict[str, object]:
    return execute_admin_infra_workflow(task, _dispatch)


def _execute_contrarian(task: TeamTask) -> dict[str, object]:
    return execute_contrarian_workflow(task, _dispatch)


_EXECUTORS: dict[str, Callable[[TeamTask], dict[str, object]]] = {
    "ops": _execute_ops,
    "qa": _execute_qa,
    "pm": _execute_pm,
    "dev_game": _execute_dev_game,
    "dev_godot": _execute_dev_godot,
    "player_ia": _execute_player_ia,
    "admin_infra": _execute_admin_infra,
    "contrarian": _execute_contrarian,
}


def _objective_is_proxmox_storage(text: str) -> bool:
    """Mission Héphaïstos ciblée stockage Proxmox / disk Prime (pas smoke générique)."""
    t = (text or "").lower()
    # Mur guest (df/load) → autre playbook
    if _objective_is_guest_metrics(t):
        return False
    storage_cue = any(
        k in t
        for k in (
            "local-lvm",
            "thin pool",
            "thin_pool",
            "proxmox",
            "stockage",
            "storage",
            "disk",
            "disque",
            "io-error",
        )
    )
    target_cue = any(
        k in t
        for k in (
            "prime",
            "246",
            "hephaistos",
            "héphaïstos",
            "infra lan",
            "infra_lan",
            "surveill",
            "supervis",
            "sond",
            "alerte",
            "remediat",
            "remédiation",
            "attention",
            "point sur",
        )
    )
    return storage_cue and target_cue


def _objective_is_guest_metrics(text: str) -> bool:
    """Mission mur INFRA LAN — disk/load guest (100/140/245/246), pas thin Proxmox."""
    t = (text or "").lower()
    if "local-lvm" in t or "thin pool" in t or "thin_pool" in t or "io-error" in t:
        return False
    wall_cue = any(
        k in t
        for k in (
            "mur infra",
            "guest metrics",
            "guest_metrics",
            "disque guest",
            "disk guest",
            "front web",
            "front-web",
            ".100",
            "192.168.0.100",
            "loadavg",
            "load average",
            "charge cpu",
            "disk/load",
        )
    )
    action_cue = any(
        k in t
        for k in (
            "surveill",
            "supervis",
            "sond",
            "alerte",
            "remediat",
            "remédiation",
            "hephaistos",
            "héphaïstos",
            "attention",
            "point sur",
            "disk",
            "disque",
            "load",
        )
    )
    return wall_cue and action_cue


def _objective_is_network_inventory(text: str) -> bool:
    """Inventaire LAN / cartographie / apparus-disparus (Héphaïstos)."""
    t = (text or "").lower()
    return any(
        k in t
        for k in (
            "inventaire réseau",
            "inventaire reseau",
            "inventaire lan",
            "cartograph",
            "network_inventory",
            "apparus",
            "disparus",
            "déconnect",
            "deconnect",
            "nouveaux appareils",
            "nouvel appareil",
            "freebox lan",
            "scan réseau",
            "scan reseau",
            "scan lan",
        )
    )


def _plan_from_at_mentions(
    objective: str, *, actor_id: str
) -> list[dict[str, object]] | None:
    """Si ≥2 @handles Team connus, une tâche par segment (objectifs NL respectés)."""
    raw = objective or ""
    handle_to_role: dict[str, str] = {
        "argus": "qa",
        "hephaistos": "ops",
        "themis": "pm",
        "dedale": "dev_game",
        "vulcan": "dev_game",
        "iris": "dev_godot",
        "hermes": "dev_godot",
        "pygmalion": "dev_game",
        "choeur": "player_ia",
        "lia": "player_ia",
        "nix": "player_ia",
    }
    hits: list[tuple[str, str, str]] = []
    for m in re.finditer(r"@([a-zA-Z0-9_-]+)\s*([^@]*)", raw):
        handle = m.group(1).lower()
        role = handle_to_role.get(handle)
        if not role or role not in ROLE_SPECS:
            continue
        seg = m.group(2).strip()
        seg = re.sub(r"(?i);?\s*max\s+\d+\s*t[aâ]ches?.*$", "", seg).strip(" \t;,—–-")
        seg = re.sub(r"(?i);?\s*pas\s+de\s+double\s*\S*.*$", "", seg).strip(" \t;,—–-")
        hits.append((handle, role, seg))

    if len(hits) < 2:
        return None

    out: list[dict[str, object]] = []
    for handle, role, seg in hits:
        default = str(ROLE_SPECS[role]["default_objective"])
        obj = seg if len(seg) >= 8 else default
        if handle == "themis" and re.search(r"(?i)\btriage\b|\bfailed\b", obj):
            ctx: dict[str, object] = {
                "failure_triage": True,
                "reunification_brief": True,
                "pm_include_plan": True,
            }
        elif handle == "argus":
            ctx = {}
            if re.search(r"(?i)smoke|healthz|systemd", obj):
                ctx["smoke_lan"] = True
        elif handle == "hephaistos":
            ctx = {}
            if re.search(r"(?i):8010|:8000|healthz|sonde", obj):
                ctx["ops_kind"] = "health_probe"
                ctx["devops_dry_run"] = False
                ctx["devops_action"] = {
                    "kind": "http_get",
                    "urls": [
                        "http://127.0.0.1:8010/healthz",
                        "http://127.0.0.1:8000/healthz",
                    ],
                }
            else:
                ctx["devops_dry_run"] = True
        else:
            ctx = {}
        if handle == "pygmalion":
            ctx = {"infographiste_ia": True, "subproject": "infographiste_ia"}
        if handle == "iris":
            track = "iris_full"
            if re.search(r"(?i)\bm9[abc]?\b|scrapaltai|minimap|carte\s*m\b", obj):
                track = "m9_full"
                if re.search(r"(?i)\bm9c\b", obj):
                    track = "m9c"
                elif re.search(r"(?i)\bm9b\b", obj):
                    track = "m9b"
                elif re.search(r"(?i)\bm9a\b", obj):
                    track = "m9a"
            elif re.search(
                r"(?i)\b(chasse|hunt|palissade|hub|lost\s*heaven|board|porte\s+est|meute|chacal)\b",
                obj,
            ):
                track = "hunt_hub"
            ctx = {
                "godot_dev_persona": "iris",
                "godot_dev_track": track,
                "subproject": "godot_iris",
            }
        row: dict[str, object] = {
            "role": role,
            "objective": obj,
            "priority": "normal",
            "approval_required": False,
            "actor_id": actor_id,
            "capability": ROLE_SPECS[role]["capability"],
            **{k: v for k, v in role_display(role).items() if k in ("alias", "title", "label")},
        }
        if ctx:
            row["context"] = ctx
        out.append(row)
    return out


def plan_from_objective(objective: str, *, actor_id: str = "system:team") -> list[dict[str, object]]:
    """Propose des tâches à partir d'un objectif NL (heuristique phase A)."""
    text = (objective or "").lower()
    proposals: list[dict[str, object]] = []
    suppress_m9 = bool(
        re.search(r"(?i)pas\s+de\s+double\s*m9|pas\s+de\s+m9a|sans\s+m9a", objective or "")
    )
    # Scrapaltai cité seulement dans un triage d'échecs → pas d'audit M9a/Iris.
    triage_failed_only = bool(
        re.search(
            r"(?i)triage.{0,80}failed|failed.{0,40}(scrapaltai|infographiste|player_ia)",
            objective or "",
        )
    )

    def _add(role: str, obj: str, *, context: dict[str, object] | None = None) -> None:
        spec = ROLE_SPECS[role]
        row: dict[str, object] = {
            "role": role,
            "objective": obj,
            "priority": "normal",
            "approval_required": False,
            "actor_id": actor_id,
            "capability": spec["capability"],
            **{k: v for k, v in role_display(role).items() if k in ("alias", "title", "label")},
        }
        if context:
            row["context"] = context
        proposals.append(row)

    mentioned = _plan_from_at_mentions(objective, actor_id=actor_id)
    if mentioned is not None:
        return mentioned

    # --- Veille concurrents / docs-only : plan ciblé (évite coffee-fill playbooks génériques) ---
    if re.search(
        r"(?i)\b(concurrents|docs?\s*only|vague\s*[abc]|focus_concurrents|"
        r"agent_skill_mmo|boite_idees|c1[-–]c12)\b",
        objective or "",
    ):
        wave_m = re.search(r"(?i)vague\s*([abc])", objective or "")
        wave = (wave_m.group(1).upper() if wave_m else "A")
        if wave == "A" or "docs" in text:
            _add(
                "pm",
                "Thémis — plan 72h concurrents (5 lignes) — FOCUS_CONCURRENTS_TEAM",
                context={"concurrents_ticket": "plan_72h", "concurrents_wave": wave, "docs_only": True},
            )
            _add(
                "player_ia",
                "Chœur — brouillon AGENT_SKILL_MMO.md (C9) + schéma mémoire C2 — docs only",
                context={"concurrents_ticket": "C9_C2", "concurrents_wave": wave, "docs_only": True},
            )
            _add(
                "dev_godot",
                "Iris — design C1 suggestions dialogue hub — docs only",
                context={
                    "concurrents_ticket": "C1",
                    "concurrents_wave": wave,
                    "docs_only": True,
                    "godot_dev_persona": "iris",
                    "subproject": "godot_iris",
                },
            )
            _add(
                "dev_game",
                "Dédale — stubs C4 event + C8 POI scrap — JSON content/",
                context={
                    "concurrents_ticket": "C4_C8",
                    "concurrents_wave": wave,
                    "docs_only": True,
                    "subproject": "content_world",
                },
            )
            return proposals
        if wave == "B":
            _add(
                "dev_godot",
                "Iris — C1+C2 dialogue + world_hint (Vague B)",
                context={
                    "concurrents_ticket": "C1_C2",
                    "concurrents_wave": "B",
                    "godot_dev_persona": "iris",
                    "subproject": "godot_iris",
                },
            )
            _add(
                "player_ia",
                "Chœur — C3 compagnon spawn + finaliser C9",
                context={"concurrents_ticket": "C3_C9", "concurrents_wave": "B"},
            )
            _add(
                "qa",
                "Argus — smoke dialogue / hunt Vague B",
                context={
                    "concurrents_ticket": "smoke_B",
                    "concurrents_wave": "B",
                    "owner_smoke_bundle": "godot_login",
                    "_require_owner_smoke": True,
                },
            )
            return proposals
        # Vague C
        _add(
            "dev_godot",
            "Hermès — C10 catalog + C11 tick",
            context={
                "concurrents_ticket": "C10_C11",
                "concurrents_wave": "C",
                "godot_dev_persona": "hermes",
                "subproject": "godot_hermes",
            },
        )
        _add(
            "dev_godot",
            "Iris — C12 dual response",
            context={
                "concurrents_ticket": "C12",
                "concurrents_wave": "C",
                "godot_dev_persona": "iris",
                "subproject": "godot_iris",
            },
        )
        _add(
            "dev_game",
            "Dédale — C5 chronique + C7 marchand",
            context={"concurrents_ticket": "C5_C7", "concurrents_wave": "C"},
        )
        _add(
            "qa",
            "Argus — smoke stubs Vague C",
            context={
                "concurrents_ticket": "smoke_C",
                "concurrents_wave": "C",
                "_require_owner_smoke": True,
            },
        )
        return proposals

    # --- Inventaire LAN / apparus-disparus (Héphaïstos) ---
    if _objective_is_network_inventory(text):
        _add(
            "ops",
            "Héphaïstos — inventaire LAN (Freebox + scan) + diff apparus/disparus",
            context={
                "ops_kind": "network_inventory",
                "persist_state": True,
                "freebox_lan": True,
                "cast_probe": True,
                "presence_agent_id": "studio_ops_hephaistos",
            },
        )
        return proposals

    # --- Mur INFRA LAN guest disk/load (100/140/245/246) ---
    if _objective_is_guest_metrics(text):
        _add(
            "ops",
            "Héphaïstos — sonde guest mur INFRA LAN (disk/load 100/140/245/246) + plan d'actions",
            context={
                "ops_kind": "guest_metrics",
                "devops_action": {"kind": "guest_metrics"},
                "devops_dry_run": True,
                "presence_agent_id": "studio_ops_hephaistos",
            },
        )
        return proposals

    # --- Stockage Proxmox / disk Prime : ops dédié (évite qa smoke + player_ia « prime ») ---
    if _objective_is_proxmox_storage(text):
        _add(
            "ops",
            "Héphaïstos — sonde Proxmox thin local-lvm + statut disk / io-error Prime 246 (read-only)",
            context={
                "ops_kind": "proxmox_storage",
                "devops_action": {"kind": "proxmox_storage"},
                "devops_dry_run": True,
                "presence_agent_id": "studio_ops_hephaistos",
            },
        )
        _add(
            "ops",
            "Héphaïstos — plan remédiation stockage si alerte thin/Prime (consultatif)",
            context={
                "ops_kind": "proxmox_storage",
                "devops_action": {"kind": "storage_remediation_plan"},
                "devops_dry_run": True,
                "presence_agent_id": "studio_ops_hephaistos",
            },
        )
        return proposals

    if any(k in text for k in ("infra", "proxmox", "vm", "ollama", "ops", "sonde", "disque")):
        obj = objective if "ops" in text else str(ROLE_SPECS["ops"]["default_objective"])
        _add("ops", obj)
    if any(k in text for k in ("qa", "smoke", "test", "valide", "vérif", "verif", "lan")):
        obj = objective if "qa" in text else str(ROLE_SPECS["qa"]["default_objective"])
        _add("qa", obj)
    if any(k in text for k in ("pm", "jalon", "roadmap", "plan", "projet", "tâche", "tache", "réunification", "reunification", "sous-projet", "triage")):
        if "triage" in text and ("failed" in text or "échec" in text or "echec" in text):
            obj = objective if "triage" in text else "Triage des tâches failed — relancer ou abandonner"
            _add("pm", obj, context={"failure_triage": True, "reunification_brief": True})
        else:
            obj = objective if "pm" in text or "réunification" in text or "reunification" in text else str(ROLE_SPECS["pm"]["default_objective"])
            _add("pm", obj)
    if any(k in text for k in ("dev", "game", "gameplay", "bug", "correctif", "mmo", "core3")):
        obj = objective if any(k in text for k in ("dev", "bug", "game")) else str(ROLE_SPECS["dev_game"]["default_objective"])
        _add("dev_game", obj)
    # « player_ia » dans une liste de failed à trier ≠ spawn Chœur
    if (
        not triage_failed_only
        and any(k in text for k in ("joueur", "joueurs", "lia", "nix", "bot", "player_ia", "prime", "246"))
    ):
        obj = objective if "joueur" in text or "lia" in text else str(ROLE_SPECS["player_ia"]["default_objective"])
        _add("player_ia", obj)
    if any(
        k in text
        for k in (
            "llm",
            "bench",
            "benchmark",
            "modèle",
            "modele",
            "ollama",
            "latence",
            "observabilité",
            "observabilite",
            "admin infra",
            "routage agentique",
            "json",
        )
    ):
        obj = objective if any(k in text for k in ("llm", "bench", "benchmark", "modèle", "modele")) else str(
            ROLE_SPECS["admin_infra"]["default_objective"]
        )
        _add("admin_infra", obj)
    if any(
        k in text
        for k in (
            "contrarian",
            "prométhée",
            "promethee",
            "hors cadre",
            "hors-cadre",
            "avis alternatif",
            "second avis",
            "second opinion",
            "uncensored",
            "devil advocate",
            "avocat du diable",
        )
    ):
        obj = (
            objective
            if any(k in text for k in ("contrarian", "prométhée", "promethee", "avis", "alternatif"))
            else str(ROLE_SPECS["contrarian"]["default_objective"])
        )
        _add(
            "contrarian",
            obj,
            context={"contrarian": True, "presence_agent_id": "studio_contrarian_promethee"},
        )
    if any(k in text for k in ("godot", "lbg-ws", "lbg_ws", "prime-client", "gateway", "zone.bridge")):
        qa_obj = objective if "godot" in text or "lbg" in text else "Supervise client Godot + sidecar 246 + readiness lbg-ws/2"
        proposals.append(
            {
                "role": "qa",
                "objective": qa_obj,
                "priority": "normal",
                "approval_required": False,
                "actor_id": actor_id,
                "capability": "team.qa",
                "context": {"godot_supervisor": True, "godot_mode": "full"},
                **{k: v for k, v in role_display("qa").items() if k in ("alias", "title", "label")},
            }
        )
        dev_obj = objective if "lbg" in text else "Audit lbg-ws/2 et proposition correctif client Godot Core3"
        proposals.append(
            {
                "role": "dev_game",
                "objective": dev_obj,
                "priority": "normal",
                "approval_required": False,
                "actor_id": actor_id,
                "capability": ROLE_SPECS["dev_game"]["capability"],
                "context": {"godot_track": "lbg_ws2"},
                **{k: v for k, v in role_display("dev_game").items() if k in ("alias", "title", "label")},
            }
        )
    if any(k in text for k in ("face_rig", "import_face_parts", "calques visage", "lyra face", "face parts")):
        proposals.append(
            {
                "role": "dev_game",
                "objective": objective if "face" in text or "calque" in text else "Import face_parts Lyra (Gemini chroma → sheets)",
                "priority": "normal",
                "approval_required": False,
                "actor_id": actor_id,
                "capability": ROLE_SPECS["dev_game"]["capability"],
                "context": {
                    "infographiste_ia": True,
                    "subproject": "infographiste_ia",
                    "face_parts": True,
                    "desktop_dry_run": True,
                },
                **{k: v for k, v in role_display("dev_game").items() if k in ("alias", "title", "label")},
            }
        )
    if (
        not triage_failed_only
        and any(k in text for k in ("infographiste", "infograph", "glb", "blender", "pipeline assets", "assets 3d"))
    ):
        igo = objective if "infograph" in text or "glb" in text else "Audit pipeline assets GLB — manifest Godot et prochain export Blender"
        proposals.append(
            {
                "role": "dev_game",
                "objective": igo,
                "priority": "normal",
                "approval_required": False,
                "actor_id": actor_id,
                "capability": ROLE_SPECS["dev_game"]["capability"],
                "context": {"infographiste_ia": True, "subproject": "infographiste_ia"},
                **{k: v for k, v in role_display("dev_game").items() if k in ("alias", "title", "label")},
            }
        )
    if any(k in text for k in ("soe m3", "soe_m3", "soe live", "soe udp", "soe_handshake")):
        proposals.append(
            {
                "role": "dev_game",
                "objective": objective if "soe" in text else "Audit SOE M3 — login + zone Godot Prime UDP",
                "priority": "normal",
                "approval_required": False,
                "actor_id": actor_id,
                "capability": ROLE_SPECS["dev_game"]["capability"],
                "context": {"godot_track": "soe_m3", "subproject": "client_godot"},
                **{k: v for k, v in role_display("dev_game").items() if k in ("alias", "title", "label")},
            }
        )
    if any(k in text for k in ("soe m5", "soe_m5", "m5 play", "zqsd", "prime_controller")):
        proposals.append(
            {
                "role": "dev_game",
                "objective": objective if "m5" in text or "play" in text else "Audit SOE M5 — play ZQSD prime_controller",
                "priority": "normal",
                "approval_required": False,
                "actor_id": actor_id,
                "capability": ROLE_SPECS["dev_game"]["capability"],
                "context": {"godot_track": "soe_m5", "subproject": "client_godot"},
                **{k: v for k, v in role_display("dev_game").items() if k in ("alias", "title", "label")},
            }
        )
    if any(k in text for k in ("zb-0", "zb0", "zone bridge", "lbgzonebridge", "zone_bridge")):
        proposals.append(
            {
                "role": "dev_game",
                "objective": objective if "zb" in text or "bridge" in text else "Audit ZB-0 LbgZoneBridge C++ readiness",
                "priority": "normal",
                "approval_required": False,
                "actor_id": actor_id,
                "capability": ROLE_SPECS["dev_game"]["capability"],
                "context": {"godot_track": "zb0", "subproject": "client_godot"},
                **{k: v for k, v in role_display("dev_game").items() if k in ("alias", "title", "label")},
            }
        )
    if any(k in text for k in ("client live", "m3 m5", "godot live")):
        proposals.append(
            {
                "role": "dev_game",
                "objective": objective,
                "priority": "high",
                "approval_required": False,
                "actor_id": actor_id,
                "capability": ROLE_SPECS["dev_game"]["capability"],
                "context": {"godot_track": "client_live", "subproject": "client_godot"},
                **{k: v for k, v in role_display("dev_game").items() if k in ("alias", "title", "label")},
            }
        )
    if not suppress_m9 and not triage_failed_only and any(k in text for k in ("m9c", "carte m", "planet map", "waypoint", "locations tree")):
        proposals.append(
            {
                "role": "dev_game",
                "objective": objective if "m9" in text or "carte" in text else "Audit M9c carte planétaire M + waypoints",
                "priority": "normal",
                "approval_required": False,
                "actor_id": actor_id,
                "capability": ROLE_SPECS["dev_game"]["capability"],
                "context": {"m9_track": "m9c", "subproject": "prime_client_2d"},
                **{k: v for k, v in role_display("dev_game").items() if k in ("alias", "title", "label")},
            }
        )
    if not suppress_m9 and not triage_failed_only and any(k in text for k in ("m9b", "minimap", "mini map", "mini-map")):
        proposals.append(
            {
                "role": "dev_game",
                "objective": objective if "minimap" in text else "Audit M9b minimap HUD style SWG",
                "priority": "normal",
                "approval_required": False,
                "actor_id": actor_id,
                "capability": ROLE_SPECS["dev_game"]["capability"],
                "context": {"m9_track": "m9b", "subproject": "prime_client_2d"},
                **{k: v for k, v in role_display("dev_game").items() if k in ("alias", "title", "label")},
            }
        )
    if not suppress_m9 and not triage_failed_only and any(k in text for k in ("m9a", "scrapaltai", "planète scrapaltai", "planete scrapaltai")):
        proposals.append(
            {
                "role": "dev_game",
                "objective": objective if "scrapaltai" in text else "Audit M9a Scrapaltai — texture planète + POI sync",
                "priority": "normal",
                "approval_required": False,
                "actor_id": actor_id,
                "capability": ROLE_SPECS["dev_game"]["capability"],
                "context": {"m9_track": "m9a", "subproject": "prime_client_2d"},
                **{k: v for k, v in role_display("dev_game").items() if k in ("alias", "title", "label")},
            }
        )
    if not suppress_m9 and not triage_failed_only and any(k in text for k in ("jalon m9", "m9 map", "m9 scrapaltai", "map minimap")):
        proposals.append(
            {
                "role": "dev_game",
                "objective": objective if "m9" in text else "Audit M9 complet — Scrapaltai 2D + minimap + carte M",
                "priority": "high",
                "approval_required": False,
                "actor_id": actor_id,
                "capability": ROLE_SPECS["dev_game"]["capability"],
                "context": {"m9_track": "m9_full", "subproject": "prime_client_2d"},
                **{k: v for k, v in role_display("dev_game").items() if k in ("alias", "title", "label")},
            }
        )
    if any(
        k in text
        for k in (
            "evolution_veille",
            "veille évolution",
            "veille evolution",
            "veille lbg",
            "pistes tiktok",
            "faisabilité pour l'écosystème",
            "faisabilite pour l'ecosysteme",
            "faisabilité lbg",
            "faisabilite lbg",
        )
    ):
        proposals.append(
            {
                "role": "pm",
                "objective": objective,
                "priority": "high",
                "approval_required": False,
                "actor_id": actor_id,
                "capability": ROLE_SPECS["pm"]["capability"],
                "context": {
                    "evolution_veille": True,
                    "presence_agent_id": "studio_pm_themis",
                    "silent": True,
                    "browser_open": False,
                },
                **{k: v for k, v in role_display("pm").items() if k in ("alias", "title", "label")},
            }
        )
    if any(
        k in text
        for k in (
            "evolution_sprint",
            "sprint évolution",
            "sprint evolution",
            "audit évolution",
            "amélioration continue",
            "amelioration continue",
            "évolution continue",
            "evolution continue",
        )
    ):
        proposals.append(
            {
                "role": "pm",
                "objective": objective
                if "évolution" in text or "evolution" in text
                else "Sprint évolution 7j — audit full + plan + L1 auto",
                "priority": "high",
                "approval_required": False,
                "actor_id": actor_id,
                "capability": ROLE_SPECS["pm"]["capability"],
                "context": {"evolution_sprint": True, "reunification_brief": True},
                **{k: v for k, v in role_display("pm").items() if k in ("alias", "title", "label")},
            }
        )
    if any(k in text for k in ("autoconsult", "autoconsultation", "round fable", "round équipe", "round equipe")):
        proposals.append(
            {
                "role": "pm",
                "objective": objective if "autoconsult" in text else "Round autoconsultation équipe — synthèse Thémis",
                "priority": "high",
                "approval_required": False,
                "actor_id": actor_id,
                "capability": ROLE_SPECS["pm"]["capability"],
                "context": {"autoconsult_round": True, "reunification_brief": True},
                **{k: v for k, v in role_display("pm").items() if k in ("alias", "title", "label")},
            }
        )
    if any(
        k in text
        for k in (
            "lbg_sa",
            "lbg sa",
            "studios agents",
            "lbg studios",
            "partitions cortex",
            "mémoire équipe",
            "memoire equipe",
            # alias legacy (ancien nom de code Fable5)
            "fable5",
            "fable 5",
            "partitions fable",
            "mémoire fable",
            "memory fable5",
        )
    ):
        hit_lbg = any(
            k in text
            for k in ("lbg_sa", "lbg sa", "studios agents", "lbg studios", "fable5", "fable 5")
        )
        proposals.append(
            {
                "role": "pm",
                "objective": objective
                if hit_lbg
                else "LBG_SA — valider studios Cortex/Corps/Peau et roadmap mémoire",
                "priority": "high",
                "approval_required": False,
                "actor_id": actor_id,
                "capability": ROLE_SPECS["pm"]["capability"],
                "context": {"subproject": "lbg_sa", "lbg_sa_plan": True},
                **{k: v for k, v in role_display("pm").items() if k in ("alias", "title", "label")},
            }
        )
        proposals.append(
            {
                "role": "qa",
                "objective": "LBG_SA — smoke registre modules et mémoire namespacée (tests test_lbg_sa_*)",
                "priority": "normal",
                "approval_required": False,
                "actor_id": actor_id,
                "capability": ROLE_SPECS["qa"]["capability"],
                "context": {"subproject": "lbg_sa", "lbg_sa_plan": True},
                **{k: v for k, v in role_display("qa").items() if k in ("alias", "title", "label")},
            }
        )
    if (
        not suppress_m9
        and not triage_failed_only
        and any(k in text for k in ("iris", "m9", "minimap", "carte m", "scrapaltai", "waypoint", "godot 2d"))
    ):
        iris_track = "m9_full"
        if re.search(
            r"(?i)\b(chasse|hunt|palissade|hub|lost\s*heaven|board|porte\s+est|meute|chacal)\b",
            text,
        ) and not re.search(r"(?i)\bm9[abc]?\b|scrapaltai|minimap|carte\s*m\b", text):
            iris_track = "hunt_hub"
            iris_obj = (
                objective
                if "iris" in text
                else "Iris — hub Lost Heaven → palissade / board chasse"
            )
        else:
            iris_obj = (
                objective
                if "iris" in text or "m9" in text
                else "Iris — audit Godot 2D Prime Client (M9)"
            )
        proposals.append(
            {
                "role": "dev_godot",
                "objective": iris_obj,
                "priority": "normal",
                "approval_required": False,
                "actor_id": actor_id,
                "capability": ROLE_SPECS["dev_godot"]["capability"],
                "context": {
                    "godot_dev_persona": "iris",
                    "godot_dev_track": iris_track,
                    "subproject": "godot_iris",
                },
                **{k: v for k, v in role_display("dev_godot").items() if k in ("alias", "title", "label")},
            }
        )
    if any(k in text for k in ("hermes", "hermès", "soe m3", "soe m5", "lbg-ws", "gateway godot")):
        proposals.append(
            {
                "role": "dev_godot",
                "objective": objective if "hermes" in text or "soe" in text else "Hermès — audit SOE/gateway Godot Prime",
                "priority": "normal",
                "approval_required": False,
                "actor_id": actor_id,
                "capability": ROLE_SPECS["dev_godot"]["capability"],
                "context": {"godot_dev_persona": "hermes", "godot_dev_track": "client_live", "subproject": "godot_hermes"},
                **{k: v for k, v in role_display("dev_godot").items() if k in ("alias", "title", "label")},
            }
        )
    if any(k in text for k in ("valider godot", "validation godot", "validation client")):
        proposals.append(
            {
                "role": "qa",
                "objective": objective if "valider" in text else "Valider client Godot — smokes + checklist humain",
                "priority": "normal",
                "approval_required": False,
                "actor_id": actor_id,
                "capability": ROLE_SPECS["qa"]["capability"],
                "context": {"godot_validation": True},
                **{k: v for k, v in role_display("qa").items() if k in ("alias", "title", "label")},
            }
        )
    if any(k in text for k in ("plan build", "build zb", "core3 build")) and "compiler" not in text:
        proposals.append(
            {
                "role": "dev_game",
                "objective": objective if "build" in text else "Plan build Core3 ZB-0 (dry-run)",
                "priority": "normal",
                "approval_required": False,
                "actor_id": actor_id,
                "capability": ROLE_SPECS["dev_game"]["capability"],
                "context": {"core3_build": True, "subproject": "core3_build"},
                **{k: v for k, v in role_display("dev_game").items() if k in ("alias", "title", "label")},
            }
        )

    if not proposals:
        _add("pm", objective)
    else:
        # Cap anti-dilution : un objectif NL large ne doit pas spawn 6+ playbooks génériques.
        max_n = 4
        m = re.search(r"(?i)max[_ ]?tasks?\s*[=:]?\s*(\d+)", objective or "")
        if m:
            max_n = max(1, min(6, int(m.group(1))))
        if len(proposals) > max_n:
            proposals[:] = proposals[:max_n]

    return proposals


def run_task(task_id: str, *, approval_token: str | None = None) -> TeamTask | None:
    task = team_store.get_task(task_id)
    if task is None:
        return None
    if task.status in ("done", "cancelled"):
        # Ré-émettre pour lever les pastilles Pilot « PRÊT — EXÉCUTER » fantômes.
        try:
            from team import presence as team_presence

            team_presence.emit_from_task(task, event="status_changed")
            team_presence.reconcile_with_store()
        except Exception:
            pass
        return task
    if task.status == "running":
        return task

    if task.approval_required:
        token = approval_token or task.stored_approval_token
        if not approval_token_valid(token):
            # Bloqué tant qu'un humain n'a pas Approuvé (token stocké) ou fourni le jeton au run.
            if task.status != "review":
                team_store.update_task(task_id, status="review")
                _trace_log({"event": "approval_required", "task_id": task_id, "role": task.role})
            return team_store.get_task(task_id)

    trace_id = task.trace_id or str(uuid.uuid4())
    context_patch: dict[str, object] = {"trace_id": trace_id}
    lessons_slice: list = []
    try:
        from team import lessons_learned as team_lessons

        lessons_slice = team_lessons.lessons_slice_for_task(
            role=str(task.role),
            objective=task.objective or "",
        )
        if lessons_slice:
            context_patch["lessons_slice"] = lessons_slice
    except Exception:
        lessons_slice = []
    team_store.update_task(task_id, status="running", context_patch=context_patch)
    # update_task charge sa propre copie : réaligner l'objet passé à l'exécuteur.
    refreshed = team_store.get_task(task_id)
    if refreshed is not None:
        task = refreshed
    _trace_log(
        {
            "event": "run_start",
            "task_id": task_id,
            "role": task.role,
            "trace_id": trace_id,
            "lessons_injected": len(lessons_slice) if isinstance(lessons_slice, list) else 0,
        }
    )

    executor = _EXECUTORS.get(task.role)
    if executor is None:
        team_store.update_task(
            task_id,
            status="failed",
            result={"error": f"rôle non supporté: {task.role}"},
        )
        return team_store.get_task(task_id)

    try:
        result = executor(task)
        if not isinstance(result, dict):
            result = {"ok": False, "error": "executor_non_dict"}
        else:
            result = dict(result)
        ok = bool(result.get("ok", True))
        status = "done" if ok else "failed"
        # Agency A.6 — trace consommation leçons injectées
        try:
            from team import lessons_learned as team_lessons

            result["lessons_trace"] = team_lessons.lessons_trace_from_slice(
                lessons_slice if isinstance(lessons_slice, list) else []
            )
        except Exception:
            result["lessons_trace"] = {"injected_ids": [], "patterns_preview": [], "injected_count": 0}
        # Agency A.1 — hard-fail → leçon (avant post_judge pour anti-double A.3)
        if not ok:
            try:
                from team import lessons_learned as team_lessons

                hf = team_lessons.record_hard_fail_lesson(
                    task_id=task_id,
                    role=str(task.role),
                    objective=task.objective or "",
                    result=result,
                )
                if hf:
                    result["hard_fail_lesson"] = {
                        "id": hf.get("id"),
                        "deduped": bool(hf.get("deduped")),
                        "hit_count": hf.get("hit_count"),
                    }
            except Exception:
                pass
        try:
            from team.post_judge import maybe_judge_task_outcome

            judged = maybe_judge_task_outcome(task, result)
            if judged:
                result["post_judge"] = {
                    "score": judged.get("score"),
                    "pass": judged.get("pass"),
                    "mode": judged.get("mode"),
                    "reasons": (judged.get("reasons") or [])[:4],
                }
        except Exception:
            pass
        team_store.update_task(task_id, status=status, result=result)
        _trace_log(
            {
                "event": "run_end",
                "task_id": task_id,
                "role": task.role,
                "ok": ok,
                "trace_id": trace_id,
                "lessons_injected": (result.get("lessons_trace") or {}).get("injected_count")
                if isinstance(result.get("lessons_trace"), dict)
                else 0,
            }
        )
        if task.role == "qa" and status == "failed":
            refreshed = team_store.get_task(task_id)
            if refreshed is not None:
                res = refreshed.result if isinstance(refreshed.result, dict) else {}
                if res.get("kind") == "godot_supervisor":
                    followups = maybe_spawn_after_godot_failure(refreshed)
                    if followups:
                        _trace_log(
                            {
                                "event": "godot_followup_spawned",
                                "task_id": task_id,
                                "followup_ids": followups,
                                "trace_id": trace_id,
                            }
                        )
                        godot_auto_run_followup(followups)
                else:
                    followups = maybe_spawn_after_qa_failure(refreshed)
                    if followups:
                        _trace_log(
                            {
                                "event": "qa_followup_spawned",
                                "task_id": task_id,
                                "followup_ids": followups,
                                "trace_id": trace_id,
                            }
                        )
                        auto_run_followup_tasks(followups)
        elif task.role in ("dev_game", "dev_godot") and status == "failed":
            refreshed = team_store.get_task(task_id)
            if refreshed is not None:
                res = refreshed.result if isinstance(refreshed.result, dict) else {}
                kind = res.get("kind")
                if kind == "godot_dev_workflow":
                    track = str(res.get("godot_dev_track") or res.get("track") or "")
                    if track.startswith("m9"):
                        followups = maybe_spawn_after_m9_failure(refreshed)
                        if followups:
                            _trace_log(
                                {
                                    "event": "m9_followup_spawned",
                                    "task_id": task_id,
                                    "followup_ids": followups,
                                    "trace_id": trace_id,
                                }
                            )
                            m9_auto_run_followup(followups)
                elif kind == "m9_map_workflow":
                    followups = maybe_spawn_after_m9_failure(refreshed)
                    if followups:
                        _trace_log(
                            {
                                "event": "m9_followup_spawned",
                                "task_id": task_id,
                                "followup_ids": followups,
                                "trace_id": trace_id,
                            }
                        )
                        m9_auto_run_followup(followups)
                elif kind in ("godot_client_workflow", "godot_client_tracks_workflow"):
                    followups = maybe_spawn_after_godot_failure(refreshed)
                    if followups:
                        godot_auto_run_followup(followups)
                else:
                    followups = maybe_spawn_after_failure(refreshed)
                    if followups:
                        _trace_log(
                            {
                                "event": "failure_followup_spawned",
                                "task_id": task_id,
                                "followup_ids": followups,
                                "trace_id": trace_id,
                            }
                        )
                        failure_auto_run_followup(followups)
        elif status == "failed":
            refreshed = team_store.get_task(task_id)
            if refreshed is not None:
                followups = maybe_spawn_after_failure(refreshed)
                if followups:
                    _trace_log(
                        {
                            "event": "failure_followup_spawned",
                            "task_id": task_id,
                            "followup_ids": followups,
                            "trace_id": trace_id,
                        }
                    )
                    failure_auto_run_followup(followups)
    except Exception as e:
        err_result: dict[str, object] = {"ok": False, "error": str(e)}
        try:
            from team import lessons_learned as team_lessons

            err_result["lessons_trace"] = team_lessons.lessons_trace_from_slice(
                lessons_slice if isinstance(lessons_slice, list) else []
            )
            hf = team_lessons.record_hard_fail_lesson(
                task_id=task_id,
                role=str(task.role),
                objective=task.objective or "",
                result=err_result,
            )
            if hf:
                err_result["hard_fail_lesson"] = {
                    "id": hf.get("id"),
                    "deduped": bool(hf.get("deduped")),
                    "hit_count": hf.get("hit_count"),
                }
        except Exception:
            pass
        team_store.update_task(task_id, status="failed", result=err_result)
        _trace_log({"event": "run_error", "task_id": task_id, "error": str(e), "trace_id": trace_id})
        refreshed = team_store.get_task(task_id)
        if refreshed is not None:
            followups = maybe_spawn_after_failure(refreshed)
            if followups:
                _trace_log(
                    {
                        "event": "failure_followup_spawned",
                        "task_id": task_id,
                        "followup_ids": followups,
                        "trace_id": trace_id,
                    }
                )
                failure_auto_run_followup(followups)

    return team_store.get_task(task_id)


def approve_task(task_id: str, token: str) -> TeamTask | None:
    task = team_store.get_task(task_id)
    if task is None:
        return None
    if task.status in ("done", "cancelled", "running"):
        return task
    if not approval_token_valid(token):
        team_store.update_task(
            task_id,
            result={**task.result, "approval_error": "token invalide"},
        )
        return team_store.get_task(task_id)
    # Après approbation : reste en file exécutable (queued) avec jeton stocké.
    # Ne jamais repasser une tâche terminée en queued (régression UI « bloqué »).
    team_store.update_task(
        task_id,
        status="queued",
        stored_approval_token=token,
        context_patch={"approved": True, "approval_error": None},
    )
    _trace_log({"event": "approved", "task_id": task_id})
    return team_store.get_task(task_id)


def cancel_task(task_id: str) -> TeamTask | None:
    task = team_store.get_task(task_id)
    if task is None:
        return None
    if task.status in ("done", "cancelled"):
        return task
    team_store.update_task(task_id, status="cancelled", result={**task.result, "cancelled": True})
    _trace_log({"event": "cancelled", "task_id": task_id})
    return team_store.get_task(task_id)


def set_dispatch_for_tests(fn: Dispatcher | None) -> None:
    global _dispatch
    _dispatch = fn or invoke_after_route  # type: ignore[assignment]
