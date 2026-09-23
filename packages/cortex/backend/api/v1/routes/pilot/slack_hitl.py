"""HITL Slack — interactions Block Kit → Team approve/reject (ADR 0021 S2)."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from typing import Any
from urllib.parse import parse_qs

from fastapi import APIRouter, Request, Response

router = APIRouter()

_TRUE = ("1", "true", "yes", "on")


def _signing_secret() -> str:
    return os.environ.get("LBG_SLACK_SIGNING_SECRET", "").strip()


def _verify_slack_signature(request: Request, raw_body: bytes) -> bool:
    secret = _signing_secret()
    if not secret:
        return os.environ.get("LBG_SLACK_HITL_ALLOW_UNSIGNED", "0").strip().lower() in _TRUE
    ts = request.headers.get("X-Slack-Request-Timestamp", "")
    sig = request.headers.get("X-Slack-Signature", "")
    try:
        if abs(time.time() - float(ts)) > 60 * 5:
            return False
    except ValueError:
        return False
    base = f"v0:{ts}:{raw_body.decode('utf-8')}".encode("utf-8")
    digest = "v0=" + hmac.new(secret.encode("utf-8"), base, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, sig)


@router.post("/slack/interactions", tags=["pilot"])
async def pilot_slack_interactions(request: Request) -> Response:
    """Endpoint Interactivity Slack (Request URL) — boutons Approve/Reject."""
    raw = await request.body()
    if not _verify_slack_signature(request, raw):
        return Response(
            content='{"ok":false,"error":"invalid_signature"}',
            status_code=401,
            media_type="application/json",
        )

    form = parse_qs(raw.decode("utf-8"))
    payload_raw = (form.get("payload") or [""])[0]
    try:
        payload = json.loads(payload_raw) if payload_raw else {}
    except json.JSONDecodeError:
        return Response(
            content='{"ok":false,"error":"bad_payload"}',
            status_code=400,
            media_type="application/json",
        )

    if not isinstance(payload, dict):
        return Response(content='{"ok":false}', status_code=400, media_type="application/json")

    from lbg_agents.slack_hitl import handle_block_interaction, parse_block_action

    if not parse_block_action(payload):
        return Response(content="", status_code=200)

    try:
        result_wrap = handle_block_interaction(payload)
        text = str(result_wrap.get("text") or "OK")
    except Exception as e:
        text = f"❌ {e}"

    body = {"response_type": "ephemeral", "replace_original": False, "text": text}
    return Response(content=json.dumps(body), media_type="application/json")


@router.post("/slack/commands", tags=["pilot"])
async def pilot_slack_commands(request: Request) -> dict[str, Any]:
    """Slash commands : /lbg-approve <id>, /lbg-reject <id>."""
    raw = await request.body()
    if not _verify_slack_signature(request, raw):
        return {"ok": False, "error": "invalid_signature"}

    form = parse_qs(raw.decode("utf-8"))
    command = (form.get("command") or [""])[0].strip()
    text = (form.get("text") or [""])[0].strip()
    user_id = (form.get("user_id") or [""])[0].strip()

    from lbg_agents.slack_hitl import handle_hitl_action, handle_text_command

    if command in ("/lbg-approve", "/lbg_approve") or text.lower().startswith("approve"):
        ref = text.split()[0] if text else ""
        result = handle_hitl_action(action="approve", task_ref=ref, user_id=user_id)
    elif command in ("/lbg-reject", "/lbg_reject"):
        ref = text.split()[0] if text else ""
        result = handle_hitl_action(action="reject", task_ref=ref, user_id=user_id)
    else:
        result = handle_text_command(text=f"{command} {text}".strip(), user_id=user_id)
        if result is None:
            return {
                "response_type": "ephemeral",
                "text": "Usage : `/lbg-approve <id>` · `/lbg-reject <id>` · ou `approve <id>` dans #lbg-ops",
            }

    if result.get("ok"):
        msg = f"OK `{result.get('short_id')}` — {result.get('action')}"
    else:
        msg = f"Erreur : {result.get('error')}"
    return {"response_type": "ephemeral", "text": msg}
