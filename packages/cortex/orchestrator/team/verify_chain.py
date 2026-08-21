"""Chaîne de vérification Argus (smoke L1) après mutation / feature proposal.

Spawn une tâche QA liée au parent ; exécution auto optionnelle.
N'écrit rien sur main / Core3 — A2 smoke only.
"""

from __future__ import annotations

import os
from typing import Any


def verify_smoke_enabled() -> bool:
    return os.environ.get("LBG_TEAM_VERIFY_SMOKE_CHAIN", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def verify_smoke_auto_run() -> bool:
    return os.environ.get("LBG_TEAM_VERIFY_SMOKE_AUTO_RUN", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def maybe_spawn_argus_smoke(
    *,
    parent_kind: str,
    parent_ref: str = "",
    manifest_path: str = "",
    actor_id: str = "system:verify_chain",
    objective: str = "",
) -> dict[str, Any]:
    """Crée une tâche QA smoke LAN (L1). Retourne ``{ok, smoke_task_id, auto_run, ...}``."""
    if not verify_smoke_enabled():
        return {"ok": False, "skipped": True, "reason": "verify smoke chain disabled"}

    from team import store as team_store

    kind = (parent_kind or "meta").strip()
    obj = (objective or "").strip() or (
        f"Smoke Argus post-{kind}"
        + (f" — {parent_ref}" if parent_ref else "")
        + " (vérif santé après staging)"
    )
    ctx: dict[str, object] = {
        "smoke_lan": True,
        "verify_chain": True,
        "verify_parent_kind": kind,
        "parent_ref": (parent_ref or "")[:120],
    }
    if manifest_path:
        ctx["manifest_path"] = manifest_path

    task = team_store.create_task(
        role="qa",
        objective=obj[:400],
        actor_id=actor_id,
        priority="normal",
        approval_required=False,
        context=ctx,
    )
    out: dict[str, Any] = {
        "ok": True,
        "smoke_task_id": task.id,
        "auto_run": False,
        "status": task.status,
    }
    if verify_smoke_auto_run():
        try:
            from team import roles as team_roles

            ran = team_roles.run_task(task.id)
            out["auto_run"] = True
            if ran is not None:
                out["status"] = ran.status
                out["smoke_ok"] = bool((ran.result or {}).get("ok", ran.status == "done"))
        except Exception as exc:
            out["auto_run_error"] = str(exc)[:200]
    return out
