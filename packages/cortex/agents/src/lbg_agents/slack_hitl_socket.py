"""Socket Mode Slack — boutons Approve/Reject L2 (ADR 0021 S2).

Prérequis app Slack :
- Socket Mode **enabled**
- App-Level Token ``xapp-…`` avec scope ``connections:write`` → ``LBG_SLACK_APP_TOKEN``
- Interactivity enabled (Request URL peut rester vide en Socket Mode)
- Bot token ``LBG_SLACK_BOT_TOKEN``

Usage::

    PYTHONPATH=agents/src python -m lbg_agents.slack_hitl_socket
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.request
from typing import Any

from lbg_agents.slack_hitl import handle_block_interaction, handle_text_command, slack_app_token

logger = logging.getLogger("lbg.slack_hitl_socket")


def _open_connection() -> str:
    tok = slack_app_token()
    if not tok:
        raise RuntimeError("LBG_SLACK_APP_TOKEN manquant (xapp-…)")
    req = urllib.request.Request(
        "https://slack.com/api/apps.connections.open",
        data=b"{}",
        headers={
            "Authorization": f"Bearer {tok}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        out = json.loads(resp.read().decode("utf-8"))
    if not out.get("ok") or not out.get("url"):
        raise RuntimeError(f"apps.connections.open failed: {out.get('error') or out}")
    return str(out["url"])


def _ack(ws: Any, envelope_id: str, *, payload: dict[str, Any] | None = None) -> None:
    msg: dict[str, Any] = {"envelope_id": envelope_id}
    if payload is not None:
        msg["payload"] = payload
    ws.send(json.dumps(msg))


def _handle_envelope(ws: Any, data: dict[str, Any]) -> None:
    etype = str(data.get("type") or "")
    envelope_id = str(data.get("envelope_id") or "")

    if etype == "hello":
        logger.info("socket hello")
        return

    if etype == "disconnect":
        logger.warning("socket disconnect reason=%s", data.get("reason"))
        if envelope_id:
            _ack(ws, envelope_id)
        raise ConnectionError("slack_disconnect")

    if not envelope_id:
        return

    # Toujours ACK rapidement (<3s)
    if etype == "interactive":
        payload = data.get("payload")
        if isinstance(payload, dict):
            try:
                out = handle_block_interaction(payload)
                logger.info("interactive handled=%s", out.get("ok"))
            except Exception:
                logger.exception("interactive handler failed")
        _ack(ws, envelope_id)
        return

    if etype == "slash_commands":
        payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
        text = str(payload.get("text") or "")
        user_id = str(payload.get("user_id") or "")
        command = str(payload.get("command") or "")
        try:
            result = handle_text_command(text=f"{command} {text}".strip(), user_id=user_id)
            reply = (
                f"OK `{result.get('short_id')}`"
                if result and result.get("ok")
                else f"Erreur : {(result or {}).get('error', 'commande inconnue')}"
            )
        except Exception as e:
            reply = f"Erreur : {e}"
        _ack(ws, envelope_id, payload={"text": reply})
        return

    # events_api / autres : ACK only
    _ack(ws, envelope_id)


def run_forever() -> None:
    import websocket

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    backoff = 1.0
    while True:
        try:
            url = _open_connection()
            logger.info("connecting socket mode…")
            ws = websocket.create_connection(url, timeout=30, ping_interval=20, ping_timeout=10)
            backoff = 1.0
            logger.info("socket connected")
            while True:
                raw = ws.recv()
                if not raw:
                    raise ConnectionError("empty frame")
                data = json.loads(raw)
                if not isinstance(data, dict):
                    continue
                _handle_envelope(ws, data)
        except KeyboardInterrupt:
            logger.info("stop")
            return
        except Exception as e:
            logger.warning("socket error: %s — retry in %.0fs", e, backoff)
            time.sleep(backoff)
            backoff = min(60.0, backoff * 2)


def main() -> None:
    if os.environ.get("LBG_SLACK_HITL_SOCKET_ONCE", "0").strip() in ("1", "true", "yes"):
        # smoke : open connection then exit
        url = _open_connection()
        print(json.dumps({"ok": True, "url_prefix": url[:40]}))
        return
    run_forever()


if __name__ == "__main__":
    main()
