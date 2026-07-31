"""Sonde factuelle LoRA / tri images (Pygmalion) — sans LLM."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def _lora_state_path() -> Path:
    raw = os.environ.get("LBG_TEAM_INFOGRAPHISTE_LORA_STATE", "").strip()
    if raw:
        return Path(raw)
    return Path("/var/lib/lbg/team_infographiste/lora_pipeline.json")


def _load_pipeline_state() -> dict[str, Any]:
    p = _lora_state_path()
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _fetch_recent_lora_tasks(limit: int = 3) -> list[dict[str, Any]]:
    base = os.environ.get("LBG_ORCHESTRATOR_URL", "http://127.0.0.1:8010").rstrip("/")
    url = f"{base}/v1/team/tasks?limit={limit}&actor_id=system:team_infographiste_lora"
    try:
        with urllib.request.urlopen(url, timeout=4) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, TimeoutError, json.JSONDecodeError, ValueError):
        return []
    tasks = payload.get("tasks") if isinstance(payload, dict) else None
    return [t for t in tasks if isinstance(t, dict)] if isinstance(tasks, list) else []


def collect_lora_status() -> dict[str, Any]:
    state = _load_pipeline_state()
    tasks = _fetch_recent_lora_tasks()
    last = tasks[0] if tasks else {}
    result = last.get("result") if isinstance(last.get("result"), dict) else {}
    pipeline = result.get("pipeline") if isinstance(result.get("pipeline"), dict) else {}
    buckets = pipeline.get("buckets") if isinstance(pipeline.get("buckets"), dict) else {}
    if not buckets and isinstance(state.get("buckets"), dict):
        buckets = state["buckets"]

    unclassified = pipeline.get("unclassified")
    if unclassified is None:
        unclassified = state.get("last_unclassified")
    if unclassified is None and buckets:
        unclassified = buckets.get("unclassified")

    return {
        "phase": pipeline.get("phase") or state.get("last_phase"),
        "unclassified": unclassified,
        "batches_total": state.get("batches_total"),
        "buckets": buckets,
        "last_task_id": last.get("id"),
        "last_task_status": last.get("status"),
        "last_task_ok": result.get("ok"),
        "state_path": str(_lora_state_path()),
        "has_state": bool(state),
    }


def format_lora_status_reply(status: dict[str, Any] | None = None) -> str:
    s = status or collect_lora_status()
    lines: list[str] = [
        "Voici l'état **réel** (Pygmalion / pipeline LoRA) — sans approximation :",
        "",
    ]
    phase = s.get("phase") or "inconnu"
    lines.append(f"- Phase pipeline : `{phase}`")
    if s.get("batches_total") is not None:
        lines.append(f"- Lots vision déjà lancés : **{s.get('batches_total')}**")
    if s.get("unclassified") is not None:
        lines.append(f"- Images encore `unclassified` : **{s.get('unclassified')}** (cible ~150–200)")

    buckets = s.get("buckets") if isinstance(s.get("buckets"), dict) else {}
    if buckets:
        lines.append("- Buckets triés :")
        for name in sorted(buckets.keys()):
            lines.append(f"  - `{name}` : {buckets[name]}")

    if s.get("last_task_id"):
        tid = str(s["last_task_id"])[:8]
        lines.append(
            f"- Dernière tâche team : `{tid}…` — status **{s.get('last_task_status')}** "
            f"(ok={s.get('last_task_ok')})"
        )

    if not s.get("has_state") and not buckets:
        lines.append(
            "- Pas encore de fichier d'état `/var/lib/lbg/team_infographiste/lora_pipeline.json` "
            "ni de buckets dans la dernière tâche — le timer LoRA n'a peut‑être pas tourné."
        )

    lines.extend(
        [
            "",
            "LoRA connus :",
            "- `mmorpg_insp_lora` — déjà présent sur le poste GPU (entraînement antérieur).",
            "- `prime_sprite_2d` / thèmes fins — en attente que le tri remplisse les buckets.",
            "",
            "Suivi : Pilot `#/team` → filtre `actor:system:team_infographiste_lora`.",
        ]
    )
    return "\n".join(lines)


def run_infographiste_status(
    *,
    actor_id: str,
    text: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    del text, context
    status = collect_lora_status()
    reply = format_lora_status_reply(status)
    return {
        "agent": "infographiste_status",
        "handler": "infographiste_status",
        "ok": True,
        "actor_id": actor_id,
        "status": status,
        # Même forme que dialogue → affichage Pilot `remote.reply`
        "remote": {"reply": reply, "source": "deterministic_lora_status"},
        "reply": reply,
    }
