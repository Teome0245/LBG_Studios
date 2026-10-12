"""HITL L2 Slack — approve / reject via Pilot (ADR 0021 S2).

Canaux d'entrée :
- poll ``#lbg-ops`` (texte ``approve <id>``) — LAN, bot token
- interactions Block Kit (HTTP / Socket Mode) — boutons

Allowlist : ``LBG_SLACK_ALLOWLIST`` (IDs Slack ``U…``, virgule).
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from lbg_agents.slack_hitl_format import short_task_id

_TRUE = ("1", "true", "yes", "on")

_APPROVE_RE = re.compile(
    r"^\s*(?:approve|valider|ok)\s+([a-f0-9-]{6,36})\s*$",
    re.I,
)
_REJECT_RE = re.compile(
    r"^\s*(?:reject|refuse|annuler|cancel)\s+([a-f0-9-]{6,36})\s*$",
    re.I,
)


def hitl_enabled() -> bool:
    if os.environ.get("LBG_SLACK_HITL_DISABLE", "0").strip().lower() in _TRUE:
        return False
    return os.environ.get("LBG_SLACK_HITL", "1").strip().lower() in _TRUE


def slack_bot_token() -> str:
    return os.environ.get("LBG_SLACK_BOT_TOKEN", "").strip()


def approval_token() -> str:
    return (
        os.environ.get("LBG_TEAM_APPROVAL_TOKEN", "").strip()
        or os.environ.get("LBG_DEVOPS_APPROVAL_TOKEN", "").strip()
        or os.environ.get("LBG_JOBS_APPROVAL_TOKEN", "").strip()
    )


def pilot_base_url() -> str:
    return (
        os.environ.get("LBG_P03_BACKEND_URL", "").strip()
        or os.environ.get("LBG_BACKEND_URL", "").strip()
        or "http://127.0.0.1:8000"
    ).rstrip("/")


def orch_base_url() -> str:
    return (
        os.environ.get("LBG_ORCHESTRATOR_URL", "").strip()
        or "http://127.0.0.1:8010"
    ).rstrip("/")


def allowlist() -> set[str]:
    raw = os.environ.get("LBG_SLACK_ALLOWLIST", "").strip()
    if not raw:
        # Défaut : propriétaire workspace (Steve) — surcharger via env
        raw = os.environ.get("LBG_SLACK_ALLOWLIST_DEFAULT", "U0BLV3859NY").strip()
    return {p.strip() for p in raw.replace(";", ",").split(",") if p.strip()}


def is_allowed(user_id: str) -> bool:
    uid = (user_id or "").strip()
    if not uid:
        return False
    allowed = allowlist()
    if not allowed:
        return False
    return uid in allowed or uid.upper() in {a.upper() for a in allowed}


def parse_hitl_command(text: str) -> tuple[str, str] | None:
    """Retourne (action, task_ref) ou None. action ∈ approve|reject."""
    raw = (text or "").strip()
    # ignorer mentions bot
    raw = re.sub(r"<@[^>]+>\s*", "", raw).strip()
    m = _APPROVE_RE.match(raw)
    if m:
        return "approve", m.group(1)
    m = _REJECT_RE.match(raw)
    if m:
        return "reject", m.group(1)
    return None


def _http_json(
    method: str,
    url: str,
    *,
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout_s: float = 30.0,
) -> tuple[int, dict[str, Any]]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    hdrs = {"Accept": "application/json", "Content-Type": "application/json"}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            code = int(resp.status)
    except urllib.error.HTTPError as e:
        code = int(e.code)
        raw = e.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        return 502, {"ok": False, "error": str(e)}
    try:
        parsed = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        parsed = {"raw": raw[:500]}
    if not isinstance(parsed, dict):
        parsed = {"payload": parsed}
    return code, parsed


def resolve_task_id(task_ref: str) -> tuple[str | None, str | None]:
    """Résout un id court ou complet via liste Team orchestrateur."""
    ref = (task_ref or "").strip()
    if not ref:
        return None, "réf vide"
    if len(ref) >= 32 or ref.count("-") >= 4:
        return ref, None

    code, body = _http_json("GET", f"{orch_base_url()}/v1/team/tasks?limit=100", timeout_s=15.0)
    if code >= 400:
        return None, f"list tasks HTTP {code}"
    tasks = body.get("tasks") if isinstance(body.get("tasks"), list) else []
    matches = [
        str(t.get("id"))
        for t in tasks
        if isinstance(t, dict) and str(t.get("id") or "").startswith(ref)
    ]
    if len(matches) == 1:
        return matches[0], None
    if not matches:
        return None, f"aucune tâche pour `{ref}`"
    return None, f"ambigu `{ref}` → {len(matches)} tâches"


def resolve_job_id(job_ref: str) -> tuple[str | None, str | None]:
    """Résout un id job court ou complet via ``GET /v1/jobs``."""
    ref = (job_ref or "").strip()
    if not ref:
        return None, "réf vide"
    if len(ref) >= 32:
        return ref, None

    code, body = _http_json("GET", f"{orch_base_url()}/v1/jobs", timeout_s=15.0)
    if code >= 400:
        return None, f"list jobs HTTP {code}"
    jobs = body.get("jobs") if isinstance(body.get("jobs"), list) else []
    matches = [
        str(j.get("id"))
        for j in jobs
        if isinstance(j, dict) and str(j.get("id") or "").startswith(ref)
    ]
    if len(matches) == 1:
        return matches[0], None
    if not matches:
        return None, f"aucun job pour `{ref}`"
    return None, f"ambigu job `{ref}` → {len(matches)}"


def resolve_hitl_target(ref: str) -> tuple[str | None, str | None, str | None]:
    """Retourne ``(kind, id, error)`` — kind ∈ ``task``|``job``."""
    tid, terr = resolve_task_id(ref)
    if tid and not terr:
        return "task", tid, None
    jid, jerr = resolve_job_id(ref)
    if jid and not jerr:
        return "job", jid, None
    return None, None, terr or jerr or "introuvable"


def approve_job(job_ref: str) -> dict[str, Any]:
    token = approval_token()
    if not token:
        return {"ok": False, "error": "LBG_TEAM_APPROVAL_TOKEN manquant"}
    jid, err = resolve_job_id(job_ref)
    if err or not jid:
        return {"ok": False, "error": err or "introuvable", "kind": "job"}
    code, body = _http_json(
        "POST",
        f"{orch_base_url()}/v1/jobs/{urllib.parse.quote(jid)}/approve",
        body={"token": token},
        timeout_s=30.0,
    )
    if code >= 400:
        return {"ok": False, "error": f"job approve HTTP {code}", "body": body, "job_id": jid}
    return {
        "ok": True,
        "action": "approve_job",
        "kind": "job",
        "job_id": jid,
        "task_id": jid,
        "short_id": short_task_id(jid),
        "job": body,
    }


def reject_job(job_ref: str) -> dict[str, Any]:
    jid, err = resolve_job_id(job_ref)
    if err or not jid:
        return {"ok": False, "error": err or "introuvable", "kind": "job"}
    code, body = _http_json(
        "POST",
        f"{orch_base_url()}/v1/jobs/{urllib.parse.quote(jid)}/cancel",
        body={},
        timeout_s=20.0,
    )
    if code >= 400:
        return {"ok": False, "error": f"job cancel HTTP {code}", "body": body, "job_id": jid}
    return {
        "ok": True,
        "action": "reject_job",
        "kind": "job",
        "job_id": jid,
        "task_id": jid,
        "short_id": short_task_id(jid),
        "job": body,
    }


def approve_and_run(task_ref: str) -> dict[str, Any]:
    token = approval_token()
    if not token:
        return {"ok": False, "error": "LBG_TEAM_APPROVAL_TOKEN manquant"}

    kind, tid, err = resolve_hitl_target(task_ref)
    if err or not kind or not tid:
        return {"ok": False, "error": err or "introuvable"}
    if kind == "job":
        return approve_job(tid)

    code_a, body_a = _http_json(
        "POST",
        f"{orch_base_url()}/v1/team/tasks/{urllib.parse.quote(tid)}/approve",
        body={"token": token},
        timeout_s=20.0,
    )
    if code_a >= 400:
        job_try = approve_job(task_ref)
        if job_try.get("ok"):
            return job_try
        return {"ok": False, "error": f"approve HTTP {code_a}", "body": body_a, "task_id": tid}

    code_r, body_r = _http_json(
        "POST",
        f"{orch_base_url()}/v1/team/tasks/{urllib.parse.quote(tid)}/run",
        body={"approval_token": token},
        timeout_s=300.0,
    )
    if code_r >= 400:
        return {"ok": False, "error": f"run HTTP {code_r}", "body": body_r, "task_id": tid, "approved": True}
    return {
        "ok": True,
        "action": "approve_run",
        "kind": "task",
        "task_id": tid,
        "short_id": short_task_id(tid),
        "task": body_r,
    }


def reject_task(task_ref: str) -> dict[str, Any]:
    kind, tid, err = resolve_hitl_target(task_ref)
    if err or not kind or not tid:
        return {"ok": False, "error": err or "introuvable"}
    if kind == "job":
        return reject_job(tid)

    code, body = _http_json(
        "POST",
        f"{orch_base_url()}/v1/team/tasks/{urllib.parse.quote(tid)}/cancel",
        body={},
        timeout_s=20.0,
    )
    if code >= 400:
        job_try = reject_job(task_ref)
        if job_try.get("ok"):
            return job_try
        return {"ok": False, "error": f"cancel HTTP {code}", "body": body, "task_id": tid}
    return {
        "ok": True,
        "action": "reject",
        "kind": "task",
        "task_id": tid,
        "short_id": short_task_id(tid),
        "task": body,
    }


def handle_hitl_action(*, action: str, task_ref: str, user_id: str) -> dict[str, Any]:
    if not hitl_enabled():
        return {"ok": False, "error": "LBG_SLACK_HITL=0"}
    if not is_allowed(user_id):
        return {"ok": False, "error": "user_not_allowlisted", "user_id": user_id}
    if action == "approve":
        return approve_and_run(task_ref)
    if action == "reject":
        return reject_task(task_ref)
    return {"ok": False, "error": f"action inconnue: {action}"}


def handle_text_command(*, text: str, user_id: str) -> dict[str, Any] | None:
    parsed = parse_hitl_command(text)
    if not parsed:
        return None
    action, ref = parsed
    return handle_hitl_action(action=action, task_ref=ref, user_id=user_id)


def slack_api(method: str, payload: dict[str, Any]) -> dict[str, Any]:
    token = slack_bot_token()
    if not token:
        return {"ok": False, "error": "LBG_SLACK_BOT_TOKEN manquant"}
    code, body = _http_json(
        "POST",
        f"https://slack.com/api/{method}",
        body=payload,
        headers={"Authorization": f"Bearer {token}"},
        timeout_s=30.0,
    )
    if code >= 400:
        return {"ok": False, "error": f"slack_http_{code}", "body": body}
    if not body.get("ok"):
        return {"ok": False, "error": body.get("error") or "slack_api_error", "body": body}
    return body


def reply_in_channel(channel: str, text: str, *, thread_ts: str = "") -> dict[str, Any]:
    payload: dict[str, Any] = {"channel": channel, "text": text}
    if thread_ts:
        payload["thread_ts"] = thread_ts
    return slack_api("chat.postMessage", payload)


def parse_block_action(payload: dict[str, Any]) -> tuple[str, str, str] | None:
    """(action, task_ref, user_id) depuis payload Block Kit interactive."""
    user = payload.get("user") if isinstance(payload.get("user"), dict) else {}
    user_id = str(user.get("id") or "")
    actions = payload.get("actions") if isinstance(payload.get("actions"), list) else []
    if not actions:
        return None
    act = actions[0] if isinstance(actions[0], dict) else {}
    action_id = str(act.get("action_id") or "")
    value = str(act.get("value") or "")
    if action_id == "lbg_l2_approve":
        return "approve", value, user_id
    if action_id == "lbg_l2_reject":
        return "reject", value, user_id
    return None


def handle_block_interaction(payload: dict[str, Any]) -> dict[str, Any]:
    """Traite un clic Approve/Reject ; répond via response_url ou channel."""
    parsed = parse_block_action(payload)
    if not parsed:
        return {"ok": True, "skipped": True, "reason": "not_lbg_action"}
    action, task_ref, user_id = parsed
    result = handle_hitl_action(action=action, task_ref=task_ref, user_id=user_id)
    if result.get("ok"):
        text = (
            f"✅ Approve+run `{result.get('short_id')}` OK"
            if action == "approve"
            else f"⏹ Reject `{result.get('short_id')}` OK"
        )
    else:
        text = f"❌ HITL : {result.get('error')}"

    response_url = str(payload.get("response_url") or "").strip()
    if response_url:
        code, body = _http_json(
            "POST",
            response_url,
            body={"replace_original": False, "text": text},
            timeout_s=15.0,
        )
        return {"ok": result.get("ok"), "result": result, "reply": {"http": code, "body": body}, "text": text}

    channel = ""
    ch = payload.get("channel")
    if isinstance(ch, dict):
        channel = str(ch.get("id") or "")
    elif isinstance(ch, str):
        channel = ch
    if channel:
        reply_in_channel(channel, text)
    return {"ok": result.get("ok"), "result": result, "text": text}


def slack_app_token() -> str:
    return os.environ.get("LBG_SLACK_APP_TOKEN", "").strip()

