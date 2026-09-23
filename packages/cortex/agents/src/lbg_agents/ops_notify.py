"""Canal ops unifié — Slack (cible) + Element/Matrix (backup). ADR 0021.

Usage::

    from lbg_agents.ops_notify import send_text
    send_text("⚠️ Atlas — hôte KO")

Backend : ``LBG_OPS_NOTIFY_BACKEND=matrix|slack|both`` (défaut ``both``).
"""

from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


_TRUE = ("1", "true", "yes", "on")
_DEFAULT_MAX_CHARS = 5500


def max_chars_limit() -> int:
    raw = os.environ.get("LBG_OPS_NOTIFY_MAX_CHARS", str(_DEFAULT_MAX_CHARS)).strip()
    try:
        n = int(raw)
    except ValueError:
        n = _DEFAULT_MAX_CHARS
    return max(500, min(n, 60000))


def notify_disabled() -> bool:
    return os.environ.get("LBG_OPS_NOTIFY_DISABLE", "0").strip().lower() in _TRUE


def resolve_backend() -> str:
    raw = os.environ.get("LBG_OPS_NOTIFY_BACKEND", "both").strip().lower()
    if raw in ("matrix", "element", "slack", "both"):
        return "matrix" if raw == "element" else raw
    return "both"


def slack_webhook_url() -> str:
    return (
        os.environ.get("LBG_SLACK_WEBHOOK_OPS", "").strip()
        or os.environ.get("LBG_SLACK_WEBHOOK_URL", "").strip()
    )


def slack_configured() -> bool:
    return bool(slack_webhook_url()) or bool(os.environ.get("LBG_SLACK_BOT_TOKEN", "").strip())


def slack_bot_token() -> str:
    return os.environ.get("LBG_SLACK_BOT_TOKEN", "").strip()


def slack_channel_ops() -> str:
    return (
        os.environ.get("LBG_SLACK_CHANNEL_OPS", "").strip()
        or os.environ.get("LBG_SLACK_CHANNEL_ID", "").strip()
    )


def load_env_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        key, val = s.split("=", 1)
        out[key.strip()] = val.strip().strip('"').strip("'")
    return out


def _truncate(message: str, *, max_chars: int | None = None) -> str:
    limit = max_chars if max_chars is not None else max_chars_limit()
    text = (message or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def send_slack_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Envoie via bot ``chat.postMessage`` (préféré) ou Incoming Webhook."""
    token = slack_bot_token()
    channel = slack_channel_ops()
    if token and channel:
        body = dict(payload)
        body.setdefault("channel", channel)
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            "https://slack.com/api/chat.postMessage",
            data=data,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15.0) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                code = int(resp.status)
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", errors="replace")
            return {"ok": False, "backend": "slack_bot", "error": f"http_{e.code}", "body": raw[:300]}
        except (urllib.error.URLError, OSError, TimeoutError) as e:
            return {"ok": False, "backend": "slack_bot", "error": f"slack_unreachable:{e}"}
        try:
            parsed = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            parsed = {"raw": raw[:200]}
        if isinstance(parsed, dict) and parsed.get("ok"):
            return {"ok": True, "backend": "slack_bot", "status": code, "ts": parsed.get("ts")}
        err = parsed.get("error") if isinstance(parsed, dict) else "slack_api_error"
        return {"ok": False, "backend": "slack_bot", "error": err, "body": parsed}

    url = slack_webhook_url()
    if not url:
        return {"ok": False, "skipped": True, "backend": "slack", "error": "slack_webhook_missing"}

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            code = int(resp.status)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        return {
            "ok": False,
            "backend": "slack",
            "error": f"http_{e.code}",
            "body": raw[:300],
        }
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        return {"ok": False, "backend": "slack", "error": f"slack_unreachable:{e}"}

    ok = code < 400 and (not raw or raw.strip().lower() in ("ok", "ok\n"))
    return {"ok": ok, "backend": "slack", "status": code, "body": raw[:200]}


def send_slack_text(message: str) -> dict[str, Any]:
    """POST texte Slack (bot ou webhook)."""
    return send_slack_payload({"text": _truncate(message)})


def send_l2_pending(task: dict[str, Any]) -> dict[str, Any]:
    """Push HITL L2 : Block Kit si possible, sinon texte + fan-out Matrix."""
    from lbg_agents.slack_hitl_format import format_l2_pending_blocks, format_l2_pending_text

    text = format_l2_pending_text(task)
    blocks = format_l2_pending_blocks(task)
    # Webhook : boutons action ne marchent pas sans interactivity → garder lien Pilot + texte
    # Bot token : boutons action_id (poll/socket les traitent)
    slack_out = send_slack_payload({"text": text, "blocks": blocks})

    backend = resolve_backend()
    results: dict[str, Any] = {"slack": slack_out}
    if backend in ("matrix", "both"):
        results["matrix"] = send_matrix_text(text)
    any_ok = any(bool(r.get("ok")) and not r.get("skipped") for r in results.values())
    return {
        "ok": any_ok,
        "backend": backend,
        "results": results,
        "kind": "l2_pending",
        "task_id": str(task.get("id") or ""),
    }


def send_matrix_text(message: str) -> dict[str, Any]:
    """Envoie via client Matrix P03 (même pattern qu'admin_infra_element)."""
    try:
        from lbg_agents.matrix_config import MatrixConfig  # type: ignore
        from lbg_agents.matrix_client import MatrixClient  # type: ignore

        cfg = MatrixConfig.from_env()
        if not getattr(cfg, "configured", False):
            return {"ok": False, "skipped": True, "backend": "matrix", "error": "matrix_not_configured"}
        if hasattr(cfg, "enabled") and not cfg.enabled:
            return {"ok": False, "skipped": True, "backend": "matrix", "error": "matrix_disabled"}
        out = MatrixClient(cfg.homeserver, access_token=cfg.access_token, user_id=cfg.user_id).send_text(
            cfg.room_id, _truncate(message)
        )
        return {"ok": bool(out.get("ok")), "backend": "matrix", **{k: v for k, v in out.items() if k != "ok"}}
    except ImportError:
        pass

    p03_root = Path(os.environ.get("LBG_P03_ROOT", "/opt/lbg_project_03"))
    p03_py = p03_root / ".venv/bin/python"
    env_file = Path(os.environ.get("LBG_P03_ENV", "/etc/lbg-project-03.env"))
    if not p03_py.is_file():
        return {
            "ok": False,
            "skipped": True,
            "backend": "matrix",
            "error": f"p03_venv_absent:{p03_py}",
        }

    env = os.environ.copy()
    env.update(load_env_file(env_file))
    env["PYTHONPATH"] = str(p03_root)
    code = (
        "from lbg_agents.matrix_config import MatrixConfig\n"
        "from lbg_agents.matrix_client import MatrixClient\n"
        "import os, sys\n"
        "msg = os.environ.get('LBG_OPS_NOTIFY_MSG', '')\n"
        "cfg = MatrixConfig.from_env()\n"
        "if not cfg.configured:\n"
        "    print({'ok': False, 'error': 'matrix_not_configured'}); sys.exit(1)\n"
        "out = MatrixClient(cfg.homeserver, access_token=cfg.access_token, user_id=cfg.user_id)"
        ".send_text(cfg.room_id, msg)\n"
        "print(out); sys.exit(0 if out.get('ok') else 1)\n"
    )
    proc = subprocess.run(
        [str(p03_py), "-c", code],
        env={**env, "LBG_OPS_NOTIFY_MSG": _truncate(message)},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if proc.returncode != 0:
        return {
            "ok": False,
            "backend": "matrix",
            "stderr": (proc.stderr or "")[-500:],
            "stdout": (proc.stdout or "")[-500:],
        }
    lines = [ln for ln in (proc.stdout or "").strip().splitlines() if ln.strip()]
    if not lines:
        return {"ok": True, "backend": "matrix", "raw": ""}
    try:
        parsed = json.loads(lines[-1])
        if isinstance(parsed, dict):
            return {"backend": "matrix", **parsed, "ok": bool(parsed.get("ok", True))}
    except json.JSONDecodeError:
        pass
    return {"ok": True, "backend": "matrix", "raw": (proc.stdout or "")[-200:]}


def send_text(message: str, *, channel: str = "ops", max_chars: int | None = None) -> dict[str, Any]:
    """Fan-out vers Matrix et/ou Slack selon ``LBG_OPS_NOTIFY_BACKEND``.

    ``channel`` est réservé (MVP : seul ``ops`` / webhook unique).
    ``max_chars`` surcharge la troncature (digests équipe via ``matrix_notify``).
    """
    _ = channel  # phase 2 : map channel → webhook/room
    if notify_disabled():
        return {"ok": True, "skipped": True, "reason": "LBG_OPS_NOTIFY_DISABLE"}

    text = _truncate(message, max_chars=max_chars)
    if not text:
        return {"ok": False, "skipped": True, "error": "empty_message"}

    backend = resolve_backend()
    results: dict[str, Any] = {}
    targets: list[str] = []
    if backend in ("matrix", "both"):
        targets.append("matrix")
    if backend in ("slack", "both"):
        targets.append("slack")

    for name in targets:
        if name == "matrix":
            results["matrix"] = send_matrix_text(text)
        else:
            results["slack"] = send_slack_text(text)

    any_ok = any(bool(r.get("ok")) and not r.get("skipped") for r in results.values())
    all_skipped = bool(results) and all(bool(r.get("skipped")) for r in results.values())
    return {
        "ok": any_ok,
        "skipped": all_skipped and not any_ok,
        "backend": backend,
        "results": results,
        "any_ok": any_ok,
        "all_skipped": all_skipped,
    }


# Alias historiques
send_ops_text = send_text
