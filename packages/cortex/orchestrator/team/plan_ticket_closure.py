"""Clôture propre des tickets plan évolutions (qualité + relaunch).

- Refuse les faux « done » (skip gate, dry-run, timeout traité comme échec).
- Exige `status=done` + evidence non vide dans plan_evolutions.json.
- Sync best-effort du JSON depuis Omarchy .143 (là où OpenCode marque).
- Relance auto (timeout / qualité) avec budget timeout augmenté.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any

from team.models import TeamTask

_SKIP_RE = re.compile(
    r"(?i)("
    r"gate\s+ferm[ée]e|"
    r"je\s+ne\s+d[ée]marre\s+pas|"
    r"ne\s+(?:le\s+)?marque\s+pas\s+done|"
    r"ne\s+pas\s+marquer|"
    r"pr[ée]requis\s+non|"
    r"waiting_plan_deps|"
    r"depends_on\s+non|"
    r"rien\s+[àa]\s+faire|"
    r"skip(?:ped|ping)?\b|"
    r"dry[\s_-]?run\s+only|"
    r"pas\s+de\s+livrable"
    r")"
)

_TIMEOUT_RE = re.compile(r"(?i)\btimeout\b")

_FLUFF_EVIDENCE_RE = re.compile(
    r"(?i)("
    r"i'?ll\s+look|"
    r"let\s+me\s+(?:read|find|check)|"
    r"found\s+the\s+ticket|"
    r"pas\s+healthz|"
    r"reopen:\s*faux\s+done|"
    r"^LIVE\s+ide_cli"
    r")"
)

_PATH_IN_TEXT_RE = re.compile(
    r"(?P<path>(?:packages|docs|tools|infra)/[\w./\-]+\.(?:gd|py|vue|js|ts|sh|yml|yaml|toml|md|json))"
)


def closure_enabled() -> bool:
    return os.environ.get("LBG_TEAM_PLAN_CLOSURE_GATE", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def relaunch_enabled() -> bool:
    return os.environ.get("LBG_TEAM_PLAN_RELAUNCH", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def min_evidence_len() -> int:
    try:
        return max(8, int(os.environ.get("LBG_TEAM_PLAN_EVIDENCE_MIN_LEN", "24")))
    except ValueError:
        return 24


def relaunch_max() -> int:
    try:
        return max(0, min(5, int(os.environ.get("LBG_TEAM_PLAN_RELAUNCH_MAX", "2"))))
    except ValueError:
        return 2


def plan_ticket_id(task: TeamTask) -> str | None:
    ctx = task.context if isinstance(task.context, dict) else {}
    tid = str(ctx.get("plan_ticket") or ctx.get("ticket_id") or "").strip()
    if tid:
        return tid
    if str(ctx.get("plan_id") or "") == "PLAN_PROPOSITIONS_EVOLUTIONS":
        m = re.search(r"(?i)\b(?:ticket\s+plan|plan)\s+(\d+\.\d+)\b", task.objective or "")
        if m:
            return m.group(1)
    return None


def is_plan_ticket_task(task: TeamTask) -> bool:
    return plan_ticket_id(task) is not None


def _plan_json_paths() -> list[Path]:
    paths: list[Path] = []
    env = os.environ.get("LBG_PLAN_EVOLUTIONS_JSON", "").strip()
    if env:
        paths.append(Path(env))
    for p in (
        "/opt/lbg-studios/docs/suivi/plan_evolutions.json",
        "/opt/LBG_IA_MMO/docs/suivi/plan_evolutions.json",
    ):
        paths.append(Path(p))
    return paths


def _load_plan_ticket(ticket_id: str) -> dict[str, Any] | None:
    tid = str(ticket_id or "").strip()
    for path in _plan_json_paths():
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            continue
        for t in data.get("tickets") or []:
            if isinstance(t, dict) and str(t.get("id") or "") == tid:
                return t
    return None


def _desktop_approval_for_sync() -> str:
    return (
        os.environ.get("LBG_DESKTOP_APPROVAL_TOKEN")
        or os.environ.get("LBG_LINUX_APPROVAL_TOKEN")
        or "confirmed"
    ).strip()


def sync_plan_from_omarchy() -> dict[str, Any]:
    """Pull plan_evolutions.json depuis .143 → chemins orch (via agent :5005)."""
    if os.environ.get("LBG_TEAM_PLAN_SYNC_OMARCHY", "1").strip().lower() not in (
        "1",
        "true",
        "yes",
        "on",
    ):
        return {"ok": False, "skipped": True, "reason": "disabled"}
    remote = os.environ.get(
        "LBG_OMARCHY_PLAN_JSON",
        "/home/lbg/projects/LBG_Studios/docs/suivi/plan_evolutions.json",
    ).strip()
    agent_url = (
        os.environ.get("LBG_AGENT_OMARCHY_URL")
        or os.environ.get("LBG_OMARCHY_AGENT_URL")
        or "http://192.168.0.143:5005"
    ).strip().rstrip("/")
    dests = [p for p in _plan_json_paths() if str(p).startswith("/opt/")]
    if not dests:
        dests = [Path("/opt/lbg-studios/docs/suivi/plan_evolutions.json")]

    # 1) Préférer l'agent desktop .143 (pas de SSH)
    try:
        import urllib.request

        payload = json.dumps(
            {
                "actor_id": "system:plan_sync",
                "text": "file_read plan_evolutions",
                "context": {
                    "desktop_target": "omarchy",
                    "desktop_dry_run": False,
                    "desktop_approval": _desktop_approval_for_sync(),
                    "desktop_confirm": True,
                    "desktop_action": {"kind": "file_read", "path": remote, "max_chars": 512_000},
                },
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            f"{agent_url}/invoke",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        raw = str(body.get("text") or "") if isinstance(body, dict) else ""
        if not (isinstance(body, dict) and body.get("ok") and raw.strip()):
            raise RuntimeError(str((body or {}).get("error") or (body or {}).get("outcome") or "file_read_failed")[:240])
        json.loads(raw)  # validate
        for dest in dests:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(raw, encoding="utf-8")
        return {"ok": True, "via": "agent_file_read", "dests": [str(d) for d in dests]}
    except Exception as agent_err:
        agent_error = str(agent_err)

    # 2) Fallback scp si clé SSH dispo
    host = os.environ.get("LBG_OMARCHY_HOST", "192.168.0.143").strip()
    user = os.environ.get("LBG_OMARCHY_USER", "lbg").strip()
    primary = dests[0]
    primary.parent.mkdir(parents=True, exist_ok=True)
    tmp = primary.with_suffix(".json.pull")
    cmd = [
        "scp",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=8",
        "-o",
        "StrictHostKeyChecking=accept-new",
        f"{user}@{host}:{remote}",
        str(tmp),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=40, check=False)
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"ok": False, "error": f"agent:{agent_error}; scp:{e}"}
    if proc.returncode != 0 or not tmp.is_file():
        return {
            "ok": False,
            "error": f"agent:{agent_error}; scp:{(proc.stderr or proc.stdout or 'failed')[:200]}",
            "code": proc.returncode,
        }
    try:
        raw = tmp.read_text(encoding="utf-8")
        json.loads(raw)
        for dest in dests:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(raw, encoding="utf-8")
        tmp.unlink(missing_ok=True)
        return {"ok": True, "via": "scp", "dests": [str(d) for d in dests]}
    except (OSError, ValueError, TypeError) as e:
        return {"ok": False, "error": str(e)}


def _summary_blob(result: dict[str, Any]) -> str:
    parts = [
        str(result.get("human_summary") or ""),
        str(result.get("summary") or ""),
        str(result.get("error") or ""),
    ]
    desk = result.get("desktop") if isinstance(result.get("desktop"), dict) else {}
    parts.append(str(desk.get("reply") or ""))
    parts.append(str(desk.get("error") or ""))
    parts.append(str(desk.get("outcome") or ""))
    return "\n".join(parts)


def looks_like_skip(result: dict[str, Any]) -> bool:
    return bool(_SKIP_RE.search(_summary_blob(result)))


def evidence_is_fluff(evidence: str) -> bool:
    ev = (evidence or "").strip()
    if len(ev) < min_evidence_len():
        return True
    if _FLUFF_EVIDENCE_RE.search(ev) and len(ev) < 120:
        return True
    # Doit citer un artefact concret (fichier, smoke, CI, polys, etc.)
    if not re.search(
        r"(?i)(\.gd\b|\.py\b|\.vue\b|\.sh\b|smoke|ruff|godot|navmesh|sqlite|"
        r"hub_|\.github|workflow|deploy|CT100|polys|OK\b)",
        ev,
    ):
        return True
    return False


def _studio_root() -> str:
    return os.environ.get(
        "LBG_OMARCHY_STUDIO_WORKSPACE",
        "/home/lbg/projects/LBG_Studios",
    ).strip().rstrip("/")


def _agent_invoke(action: dict[str, Any], *, text: str = "plan_closure") -> dict[str, Any]:
    import urllib.request

    agent_url = (
        os.environ.get("LBG_AGENT_OMARCHY_URL")
        or os.environ.get("LBG_OMARCHY_AGENT_URL")
        or "http://192.168.0.143:5005"
    ).strip().rstrip("/")
    payload = json.dumps(
        {
            "actor_id": "system:plan_closure",
            "text": text,
            "context": {
                "desktop_target": "omarchy",
                "desktop_dry_run": False,
                "desktop_approval": _desktop_approval_for_sync(),
                "desktop_confirm": True,
                "desktop_action": action,
            },
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{agent_url}/invoke",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=25) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body if isinstance(body, dict) else {"ok": False, "error": "bad_agent_body"}


def omarchy_path_exists(rel_or_abs: str) -> bool:
    """True si le fichier existe sur .143 (allowlist agent)."""
    path = (rel_or_abs or "").strip()
    if not path:
        return False
    if not path.startswith("/"):
        path = f"{_studio_root()}/{path.lstrip('./')}"
    try:
        out = _agent_invoke({"kind": "file_read", "path": path, "max_chars": 64}, text="path_exists")
        return bool(out.get("ok")) and str(out.get("outcome") or "") == "ok"
    except Exception:
        return False


def _acceptance_paths(ticket: dict[str, Any], evidence: str) -> list[str]:
    acc = ticket.get("acceptance") if isinstance(ticket.get("acceptance"), dict) else {}
    paths: list[str] = []
    for key in ("paths_any", "paths_all"):
        raw = acc.get(key) if isinstance(acc, dict) else None
        if isinstance(raw, list):
            paths.extend(str(p).strip() for p in raw if str(p).strip())
    for m in _PATH_IN_TEXT_RE.finditer(evidence or ""):
        paths.append(m.group("path"))
    # dédup ordre stable
    seen: set[str] = set()
    out: list[str] = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out[:8]


def verify_acceptance_paths(ticket: dict[str, Any], evidence: str) -> dict[str, Any]:
    """Au moins un path_any existant ; tous les paths_all si définis."""
    if os.environ.get("LBG_TEAM_PLAN_PATH_CHECK", "1").strip().lower() not in (
        "1",
        "true",
        "yes",
        "on",
    ):
        return {"ok": True, "skipped": True}
    acc = ticket.get("acceptance") if isinstance(ticket.get("acceptance"), dict) else {}
    paths_any = [str(p).strip() for p in (acc.get("paths_any") or []) if str(p).strip()] if acc else []
    paths_all = [str(p).strip() for p in (acc.get("paths_all") or []) if str(p).strip()] if acc else []
    inferred = _acceptance_paths(ticket, evidence)
    if not paths_any and not paths_all:
        paths_any = inferred[:3]
    if not paths_any and not paths_all:
        # Pas de chemin exigible → OK (evidence textuelle déjà filtrée)
        return {"ok": True, "skipped": True, "reason": "no_paths"}

    checked: dict[str, bool] = {}
    for p in list(dict.fromkeys([*paths_any, *paths_all])):
        checked[p] = omarchy_path_exists(p)

    missing_all = [p for p in paths_all if not checked.get(p)]
    any_ok = any(checked.get(p) for p in paths_any) if paths_any else True
    ok = (not missing_all) and any_ok
    return {
        "ok": ok,
        "checked": checked,
        "paths_any": paths_any,
        "paths_all": paths_all,
        "missing_all": missing_all,
        "any_ok": any_ok,
    }


def is_timeout_failure(result: dict[str, Any]) -> bool:
    desk = result.get("desktop") if isinstance(result.get("desktop"), dict) else {}
    if str(desk.get("outcome") or "").lower() == "timeout":
        return True
    blob = _summary_blob(result)
    if _TIMEOUT_RE.search(blob) and ("après" in blob.lower() or "after" in blob.lower() or "1200" in blob):
        return True
    err = str(desk.get("error") or result.get("error") or "")
    return bool(_TIMEOUT_RE.search(err))


def evaluate_plan_closure(task: TeamTask, result: dict[str, Any]) -> dict[str, Any]:
    """Verdict qualité pour un ticket plan (n'altère pas result)."""
    tid = plan_ticket_id(task)
    reasons: list[str] = []
    if not tid:
        return {"ok": True, "skipped": True, "reasons": ["not_a_plan_ticket"]}

    if result.get("dry_run") is True:
        reasons.append("dry_run_forbidden_for_plan_ticket")

    if looks_like_skip(result):
        reasons.append("skip_or_gate_closed_in_summary")

    if is_timeout_failure(result):
        reasons.append("timeout")

    if result.get("ok") is False:
        reasons.append("executor_ok_false")

    sync = sync_plan_from_omarchy()
    ticket = _load_plan_ticket(tid)
    evidence = ""
    status = ""
    if isinstance(ticket, dict):
        status = str(ticket.get("status") or "").strip().lower()
        evidence = str(ticket.get("evidence") or "").strip()
    else:
        reasons.append("plan_ticket_missing_in_json")

    if status != "done":
        reasons.append(f"plan_status_not_done:{status or '?'}")
    if len(evidence) < min_evidence_len():
        reasons.append(f"evidence_too_short:{len(evidence)}<{min_evidence_len()}")
    elif evidence_is_fluff(evidence):
        reasons.append("evidence_fluff_or_no_artifact")

    path_check: dict[str, Any] = {"ok": True, "skipped": True}
    if status == "done" and evidence and "evidence_too_short" not in ",".join(reasons):
        if isinstance(ticket, dict):
            path_check = verify_acceptance_paths(ticket, evidence)
            if path_check.get("ok") is False:
                reasons.append("acceptance_paths_missing")

    ok = not reasons
    return {
        "ok": ok,
        "plan_ticket": tid,
        "reasons": reasons,
        "plan_status": status,
        "evidence_len": len(evidence),
        "evidence_preview": evidence[:160],
        "path_check": path_check,
        "sync": sync,
        "ts": time.time(),
    }


def mark_plan_ticket(
    ticket_id: str,
    status: str,
    evidence: str,
    *,
    actor_id: str = "system:plan_mark",
) -> dict[str, Any]:
    """Écrit le mark sur tous les JSON plan orch (+ sync reverse non faite)."""
    tid = str(ticket_id or "").strip()
    st = str(status or "").strip().lower()
    ev = (evidence or "").strip()
    if not tid:
        return {"ok": False, "error": "ticket_id_required"}
    if st not in ("done", "in_progress", "blocked", "todo", "relaunch", "cancelled"):
        return {"ok": False, "error": f"status_invalide:{st}"}
    if st == "done":
        if len(ev) < min_evidence_len() or evidence_is_fluff(ev):
            return {"ok": False, "error": "evidence_insufficient"}
    written: list[str] = []
    for path in _plan_json_paths():
        if not path.is_file() and not str(path).startswith("/opt/"):
            continue
        try:
            if path.is_file():
                data = json.loads(path.read_text(encoding="utf-8"))
            else:
                # bootstrap minimal interdit — on exige un fichier existant
                continue
            found = False
            for t in data.get("tickets") or []:
                if isinstance(t, dict) and str(t.get("id") or "") == tid:
                    t["status"] = st
                    if ev:
                        t["evidence"] = ev
                    t["updated_ts"] = time.time()
                    t["marked_by"] = actor_id
                    found = True
                    break
            if not found:
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            written.append(str(path))
        except (OSError, ValueError, TypeError):
            continue
    if not written:
        return {"ok": False, "error": "no_plan_json_writable"}
    return {"ok": True, "ticket_id": tid, "status": st, "written": written, "actor_id": actor_id}


def closure_prompt_addon(task: TeamTask) -> str:
    """Contrat de clôture injecté dans le prompt OpenCode."""
    tid = plan_ticket_id(task)
    if not tid:
        return ""
    ticket = _load_plan_ticket(tid) or {}
    acc = ticket.get("acceptance") if isinstance(ticket.get("acceptance"), dict) else {}
    paths = []
    if isinstance(acc, dict):
        paths = list(acc.get("paths_any") or []) + list(acc.get("paths_all") or [])
    path_line = ", ".join(str(p) for p in paths[:6]) if paths else "(citer chemins packages/… réellement touchés)"
    return (
        f"\n\n[CLOTURE PLAN {tid} — OBLIGATOIRE]\n"
        f"1) Implémenter réellement (pas dry-run, pas « gate fermée »).\n"
        f"2) Fichiers attendus: {path_line}\n"
        f"3) Mark suivi: `python3 tools/suivi_plan_evolutions.py --mark {tid} done "
        f"--evidence '…preuves concrètes (fichiers+smoke)…' --refresh`\n"
        f"4) OU HTTP: `curl -fsS -X POST http://192.168.0.140:8010/v1/team/plan/mark "
        f"-H 'Content-Type: application/json' "
        f"-d '{{\"ticket_id\":\"{tid}\",\"status\":\"done\",\"evidence\":\"…\"}}'`\n"
        f"Sans evidence fichier/smoke ≥24 car., la tâche sera REJECTÉE par le gate qualité.\n"
    )


def apply_plan_closure_gate(task: TeamTask, result: dict[str, Any]) -> dict[str, Any]:
    """Si ticket plan : impose ok=False tant que la clôture n'est pas propre."""
    if not closure_enabled() or not is_plan_ticket_task(task):
        return result
    out = dict(result) if isinstance(result, dict) else {"ok": False, "error": "bad_result"}
    # Pas de gate sur un échec déjà posé — on attache quand même le verdict timeout/skip
    verdict = evaluate_plan_closure(task, out)
    out["plan_closure"] = verdict
    if not verdict.get("ok"):
        out["ok"] = False
        out["error"] = "plan_closure_rejected:" + ",".join(verdict.get("reasons") or [])
        summary = str(out.get("human_summary") or "")
        note = " · clôture plan refusée: " + ", ".join(verdict.get("reasons") or [])
        if note.strip(" ·") not in summary:
            out["human_summary"] = (summary + note).strip()
    return out


def plan_closure_accepted(result: dict[str, Any] | None) -> bool:
    """True si le résultat peut débloquer un depends_on (sibling).

    Sans `plan_closure.ok` → False (évite dry-run / faux done historiques).
    """
    if not isinstance(result, dict):
        return False
    if result.get("dry_run") is True:
        return False
    if result.get("ok") is False:
        return False
    if looks_like_skip(result):
        return False
    kind = str(result.get("kind") or "")
    if kind in ("ops_probe", "ops_health_probe"):
        return False
    nested = result.get("output") if isinstance(result.get("output"), dict) else {}
    if isinstance(nested, dict):
        nest_res = nested.get("result") if isinstance(nested.get("result"), dict) else {}
        nest_meta = nested.get("meta") if isinstance(nested.get("meta"), dict) else {}
        if nest_res.get("dry_run") is True or nest_meta.get("dry_run") is True:
            return False
    pc = result.get("plan_closure")
    if isinstance(pc, dict):
        return pc.get("ok") is True
    # Legacy sans verdict de gate : ne débloque pas
    return False


def _next_timeout_s(task: TeamTask, result: dict[str, Any]) -> int:
    ctx = task.context if isinstance(task.context, dict) else {}
    try:
        cur = int(ctx.get("ide_cli_timeout_s") or result.get("timeout_s") or 1200)
    except (TypeError, ValueError):
        cur = 1200
    bump = int(os.environ.get("LBG_TEAM_PLAN_RELAUNCH_TIMEOUT_BUMP_S", "900"))
    return max(60, min(3600, cur + max(300, bump)))


def maybe_relaunch_plan_ticket(task: TeamTask) -> list[str]:
    """Spawn une reprise LIVE du même ticket (timeout / qualité), max N fois."""
    if not relaunch_enabled() or not is_plan_ticket_task(task):
        return []
    if task.status != "failed":
        return []
    ctx = dict(task.context or {})
    if ctx.get("_plan_relaunch_spawned"):
        return []
    count = int(ctx.get("_plan_relaunch_count") or 0)
    if count >= relaunch_max():
        return []

    result = task.result if isinstance(task.result, dict) else {}
    reasons = []
    pc = result.get("plan_closure") if isinstance(result.get("plan_closure"), dict) else {}
    reasons.extend(list(pc.get("reasons") or []))
    if is_timeout_failure(result):
        reasons.append("timeout")

    # Ne pas boucler sur un skip de dépendances : le conductor reprendra plus tard
    # seulement si on relaunch — OK car depends_on reste dans le context.
    tid = plan_ticket_id(task) or "?"
    timeout_s = _next_timeout_s(task, result)
    new_ctx = {
        k: v
        for k, v in ctx.items()
        if not str(k).startswith("_")
    }
    new_ctx.update(
        {
            "ide_cli": True,
            "ide_cli_live": True,
            "desktop_dry_run": False,
            "ide_cli_timeout_s": timeout_s,
            "plan_ticket": tid,
            "_plan_relaunch_count": count + 1,
            "_plan_relaunch_of": task.id,
            "relaunch_reasons": reasons[:8],
        }
    )
    obj = (
        f"REPRISE plan {tid} (#{count + 1}/{relaunch_max()}) après "
        f"{','.join(reasons[:3]) or 'échec'} — {task.objective}"
    )[:480]

    from team import store as team_store

    child = team_store.create_task(
        role=task.role,
        objective=obj,
        actor_id=os.environ.get("LBG_TEAM_PLAN_RELAUNCH_ACTOR_ID", "system:plan_relaunch").strip(),
        priority="high",
        approval_required=False,
        context=new_ctx,
    )
    team_store.update_task(
        task.id,
        context_patch={
            "_plan_relaunch_spawned": True,
            "_plan_relaunch_task_ids": [child.id],
            "_plan_relaunch_ts": time.time(),
            # évite double triage PM générique inutile
            "_failure_followup_spawned": True,
        },
    )
    return [child.id]
