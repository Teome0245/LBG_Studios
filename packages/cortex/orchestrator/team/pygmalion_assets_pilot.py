"""Playbook Pygmalion Assets — brief → ensure Comfy si besoin → tâche L2 (F2).

Avant toute requête : si ComfyUI est down, ``comfyui_ensure`` via agent desktop
(``C:\\Users\\sdesh\\ComfyUI`` · ``python main.py --listen 0.0.0.0 --port 8188 --lowvram``).
Queue / effets Comfy restent L2. Dry-run par défaut.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def _truthy(raw: str) -> bool:
    return (raw or "").strip().lower() in ("1", "true", "yes", "on")


def auto_ensure_enabled() -> bool:
    return _truthy(os.environ.get("LBG_PYGMALION_COMFY_AUTO_ENSURE", "1"))


def state_path() -> Path:
    raw = os.environ.get("LBG_PYGMALION_ASSETS_PILOT_STATE", "").strip()
    if raw:
        return Path(raw)
    return Path("/var/lib/lbg/pygmalion_assets_pilot/state.json")


def _load_state() -> dict[str, Any]:
    path = state_path()
    try:
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def _save_state(data: dict[str, Any]) -> None:
    path = state_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass


def last_run() -> dict[str, Any]:
    st = _load_state()
    last = st.get("last_run")
    return last if isinstance(last, dict) else {}


def _pilot_base_url() -> str:
    return (
        os.environ.get("LBG_PILOT_PUBLIC_URL", "").strip()
        or os.environ.get("LBG_BACKEND_URL", "").strip()
        or "http://192.168.0.140:8080"
    ).rstrip("/")


def _comfy_base() -> str:
    return (
        os.environ.get("LBG_COMFYUI_BASE_URL", "").strip()
        or "http://192.168.0.10:8188"
    ).rstrip("/")


def probe_comfy(*, timeout_s: float = 4.0) -> dict[str, Any]:
    """Sonde HTTP read-only ComfyUI (system_stats ou /)."""
    base = _comfy_base()
    urls = [f"{base}/system_stats", f"{base}/"]
    last_err = "unreachable"
    for url in urls:
        req = urllib.request.Request(url, method="GET", headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                code = int(resp.status)
                body = resp.read(400).decode("utf-8", errors="replace")
            return {
                "ok": code < 400,
                "url": url,
                "status": code,
                "base": base,
                "body_preview": body[:120],
            }
        except urllib.error.HTTPError as e:
            last_err = f"http_{e.code}"
            if e.code < 500:
                return {"ok": True, "url": url, "status": int(e.code), "base": base, "note": "http_error_as_up"}
        except (urllib.error.URLError, OSError, TimeoutError) as e:
            last_err = str(e)[:160]
    return {"ok": False, "base": base, "error": last_err}


def _find_open_assets_task(brief_key: str) -> dict[str, Any] | None:
    try:
        from team import store as team_store

        if not team_store.team_enabled():
            return None
        for t in team_store.list_tasks(limit=200):
            ctx = t.context if isinstance(t.context, dict) else {}
            if not ctx.get("pygmalion_assets_pilot"):
                continue
            if str(t.status or "") in ("done", "cancelled", "failed"):
                continue
            if brief_key and ctx.get("brief_key") == brief_key:
                return {
                    "id": t.id,
                    "status": t.status,
                    "objective": t.objective,
                }
    except Exception:
        return None
    return None


def _brief_key(brief: str) -> str:
    import hashlib

    return hashlib.sha256((brief or "").strip().lower().encode("utf-8")).hexdigest()[:16]


def ensure_comfy_via_desktop(
    *,
    dry_run: bool,
    actor_id: str = "pilot:pygmalion_assets",
) -> dict[str, Any]:
    """Appelle ``comfyui_ensure`` sur l'agent Windows (.10) si auto-ensure actif."""
    if dry_run:
        return {
            "ok": True,
            "skipped": True,
            "reason": "dry_run",
            "would": "comfyui_ensure",
            "root": r"C:\Users\sdesh\ComfyUI",
            "args": ["--listen", "0.0.0.0", "--port", "8188", "--lowvram"],
        }
    try:
        from lbg_agents.dispatch import invoke_after_route
    except Exception as exc:
        return {"ok": False, "error": f"dispatch_import:{exc}"}

    # Token optionnel : agents Windows pas encore sync (ensure sans HITL) acceptent encore approval.
    approval = (
        os.environ.get("LBG_DESKTOP_APPROVAL_TOKEN", "").strip()
        or os.environ.get("LBG_TEAM_APPROVAL_TOKEN", "").strip()
        or os.environ.get("LBG_DEVOPS_APPROVAL_TOKEN", "").strip()
    )
    ctx: dict[str, Any] = {
        "desktop_action": {"kind": "comfyui_ensure"},
        "desktop_target": "pc",
        "desktop_dry_run": False,
        "_pygmalion_brief": True,
    }
    if approval:
        ctx["desktop_approval"] = approval
    try:
        out = invoke_after_route(
            "agent.desktop",
            actor_id=actor_id,
            text="ensure ComfyUI (auto avant brief Pygmalion)",
            context=ctx,
        )
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    if not isinstance(out, dict):
        return {"ok": False, "error": "ensure_bad_payload", "raw": str(out)[:200]}
    return {
        "ok": bool(out.get("ok")),
        "outcome": out.get("outcome"),
        "running": out.get("running"),
        "error": out.get("error"),
        "start": out.get("start"),
        "probe": out.get("probe"),
        "desktop_url": out.get("desktop_url"),
    }


def run_pygmalion_assets_pilot(
    *,
    brief: str,
    dry_run: bool = True,
    notify: bool | None = None,
    spawn_l2: bool = True,
    propose_comfy_ensure: bool = True,
    auto_ensure: bool | None = None,
    actor_id: str = "pilot:pygmalion_assets",
) -> dict[str, Any]:
    """Brief NL → ensure Comfy si besoin → (optionnel) tâche Team L2 Pygmalion + HITL."""
    t0 = time.perf_counter()
    text = (brief or "").strip()
    if not text:
        return {"ok": False, "error": "brief_empty", "dry_run": dry_run}

    do_notify = bool(notify) if notify is not None else (not dry_run)
    do_ensure = auto_ensure_enabled() if auto_ensure is None else bool(auto_ensure)
    steps: list[dict[str, Any]] = []

    # 1. Perception Comfy
    comfy = probe_comfy()
    steps.append({"id": "comfy_probe", **comfy})

    # 1b. Relancer Comfy si down (avant toute requête assets)
    ensure_out: dict[str, Any] = {"ok": True, "skipped": True, "reason": "comfy_already_up"}
    if do_ensure and not comfy.get("ok"):
        ensure_out = ensure_comfy_via_desktop(dry_run=dry_run, actor_id=actor_id)
        if not dry_run and ensure_out.get("ok"):
            # Laisser le temps au /system_stats ; re-sonde
            time.sleep(1.0)
            comfy = probe_comfy(timeout_s=6.0)
            ensure_out["reprobe"] = {"ok": comfy.get("ok"), "base": comfy.get("base")}
        steps.append({"id": "comfy_ensure", **ensure_out})
    else:
        steps.append({"id": "comfy_ensure", **ensure_out})

    # 2. Décision — assets = toujours L2 pour exec ; dry propose seulement
    decision = "spawn_l2" if spawn_l2 else "probe_only"
    summary = (
        f"pygmalion_assets · comfy={'OK' if comfy.get('ok') else 'KO'} · "
        f"{comfy.get('base')}"
        f"{' · ensure=' + str(ensure_out.get('outcome') or ensure_out.get('would') or 'skip') if do_ensure else ''}"
        f"\nBrief: {text[:280]}"
    )
    steps.append(
        {
            "id": "decision",
            "ok": True,
            "decision": decision,
            "comfy_ok": bool(comfy.get("ok")),
        }
    )

    # 3. Tâche L2
    bkey = _brief_key(text)
    rem_task_id: str | None = None
    l2: dict[str, Any] = {"ok": True, "skipped": True}
    proposed_action = {"kind": "comfyui_ensure"} if propose_comfy_ensure else {"kind": "comfyui_status"}

    if spawn_l2:
        existing = _find_open_assets_task(bkey)
        if existing:
            rem_task_id = str(existing["id"])
            l2 = {
                "ok": True,
                "skipped": False,
                "deduped": True,
                "task_id": rem_task_id,
                "status": existing.get("status"),
                "approval_required": True,
            }
        elif dry_run:
            l2 = {
                "ok": True,
                "skipped": True,
                "reason": "dry_run",
                "would_create": {
                    "role": "dev_game",
                    "approval_required": True,
                    "objective": f"Pygmalion Assets L2 — {text[:160]}",
                    "desktop_action": proposed_action,
                    "infographiste_ia": True,
                },
            }
        else:
            try:
                from team import store as team_store

                task = team_store.create_task(
                    role="dev_game",
                    objective=f"Pygmalion Assets L2 — {text[:400]}",
                    actor_id=actor_id,
                    approval_required=True,
                    context={
                        "pygmalion_assets_pilot": True,
                        "infographiste_ia": True,
                        "subproject": "infographiste_ia",
                        "parent_playbook": "pygmalion_assets_pilot",
                        "brief": text[:2000],
                        "brief_key": bkey,
                        "comfy_probe": comfy,
                        # Proposition structurée — exécution seulement après approve + run
                        "desktop_action": proposed_action,
                        "desktop_dry_run": False,
                        "human_summary": summary[:500],
                    },
                )
                rem_task_id = task.id
                l2 = {
                    "ok": True,
                    "skipped": False,
                    "deduped": False,
                    "task_id": task.id,
                    "status": task.status,
                    "approval_required": True,
                }
                try:
                    from lbg_agents.ops_notify import send_l2_pending

                    hitl = send_l2_pending(
                        {
                            "id": task.id,
                            "role": "pygmalion",
                            "role_alias": "Pygmalion",
                            "objective": task.objective,
                            "status": task.status,
                            "actor_id": task.actor_id,
                            "approval_required": True,
                        }
                    )
                    l2["hitl"] = hitl
                except Exception as exc:
                    l2["hitl"] = {"ok": False, "error": str(exc)}
            except Exception as exc:
                l2 = {"ok": False, "skipped": False, "error": str(exc)}
    steps.append({"id": "assets_l2", **l2})

    # 4. Notify résumé
    notify_out: dict[str, Any] = {"ok": True, "skipped": True}
    if do_notify and not dry_run and rem_task_id:
        try:
            from lbg_agents.ops_notify import send_text

            pilot = _pilot_base_url()
            msg = (
                "🎨 Pygmalion Assets Pilot — brief L2\n"
                f"{summary}\n"
                f"• tâche : {rem_task_id}\n"
                f"• approve : {pilot}/pilot/#/team?task={rem_task_id}\n"
                f"• action proposée : {proposed_action.get('kind')} (après HITL)"
            )
            notify_out = send_text(msg)
            if not isinstance(notify_out, dict):
                notify_out = {"ok": True, "raw": notify_out}
            notify_out["skipped"] = False
        except Exception as exc:
            notify_out = {"ok": False, "error": str(exc), "skipped": False}
    elif dry_run:
        notify_out = {
            "ok": True,
            "skipped": True,
            "reason": "dry_run",
            "would_notify": bool(spawn_l2),
        }
    steps.append({"id": "notify", **notify_out})

    # 5. Lesson (live only)
    lesson: dict[str, Any] = {"ok": True, "skipped": True}
    if not dry_run and rem_task_id:
        try:
            from team import lessons_learned

            entry = lessons_learned.append_lesson(
                agent_role="pygmalion",
                pattern="pygmalion_assets_pilot brief→L2",
                context=summary[:800],
                failure_or_success="success",
                do_not_repeat="Ne pas queue Comfy / desktop sans tâche L2 approuvée.",
                refs=["pygmalion_assets_pilot", f"task:{rem_task_id}", "plan_combler_gaps_agentiques"],
            )
            lesson = {
                "ok": True,
                "skipped": False,
                "lesson_id": (entry or {}).get("id") if isinstance(entry, dict) else None,
            }
        except Exception as exc:
            lesson = {"ok": False, "skipped": False, "error": str(exc)}
    steps.append({"id": "lesson", **lesson})

    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    out = {
        "ok": True,
        "playbook": "pygmalion_assets_pilot",
        "dry_run": dry_run,
        "decision": decision,
        "brief": text[:500],
        "comfy_ok": bool(comfy.get("ok")),
        "summary": summary,
        "remediation_task_id": rem_task_id,
        "l2_task_id": rem_task_id,
        "proposed_desktop_action": proposed_action,
        "steps": steps,
        "elapsed_ms": elapsed_ms,
        "docs": [
            "docs/plan_combler_gaps_agentiques.md",
            "docs/desktop_hybride.md",
            "docs/runbook_ops_health_pilot.md",
        ],
    }
    if not dry_run:
        st = _load_state()
        st["last_run"] = {
            "ts": time.time(),
            "decision": decision,
            "dry_run": False,
            "comfy_ok": out["comfy_ok"],
            "l2_task_id": rem_task_id,
            "brief": text[:200],
            "summary": summary[:400],
            "elapsed_ms": elapsed_ms,
        }
        _save_state(st)
    return out
