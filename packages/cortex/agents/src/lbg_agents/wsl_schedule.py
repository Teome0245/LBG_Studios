"""Fenêtre d'indisponibilité WSL (poste GPU .10) — nuit 22h→7h + sonde joignabilité.

Les timers Pygmalion (LoRA / sprites / assets) doivent **skip** pendant la fenêtre
nuit (PC volontairement éteint), sauf forçage explicite. En journée, un avis
est poussé sur le WSL pour ne pas couper la machine.
"""

from __future__ import annotations

import os
import subprocess
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo


def truthy(raw: str | None) -> bool:
    return (raw or "").strip().lower() in {"1", "true", "yes", "on"}


def tz_name() -> str:
    return os.environ.get("LBG_WSL_TZ", "Europe/Paris").strip() or "Europe/Paris"


def quiet_start_hour() -> int:
    try:
        return int(os.environ.get("LBG_WSL_QUIET_START_H", "22"))
    except ValueError:
        return 22


def quiet_end_hour() -> int:
    try:
        return int(os.environ.get("LBG_WSL_QUIET_END_H", "7"))
    except ValueError:
        return 7


def now_local(now: datetime | None = None) -> datetime:
    if now is not None:
        if now.tzinfo is None:
            return now.replace(tzinfo=ZoneInfo(tz_name()))
        return now.astimezone(ZoneInfo(tz_name()))
    return datetime.now(ZoneInfo(tz_name()))


def in_quiet_hours(now: datetime | None = None) -> bool:
    """True si dans [start, 24) ∪ [0, end) — défaut 22h→7h Europe/Paris."""
    dt = now_local(now)
    start = quiet_start_hour() % 24
    end = quiet_end_hour() % 24
    h = dt.hour
    if start == end:
        return False
    if start > end:
        return h >= start or h < end
    return start <= h < end


def force_requested(*, env: bool | None = None, context: dict[str, Any] | None = None) -> bool:
    if env is None:
        env = truthy(os.environ.get("LBG_WSL_FORCE"))
    if env:
        return True
    ctx = context or {}
    return bool(
        ctx.get("force_wsl")
        or ctx.get("wsl_force")
        or ctx.get("ignore_wsl_quiet_hours")
        or ctx.get("_force_wsl")
    )


def quiet_hours_label() -> str:
    return f"{quiet_start_hour():02d}h→{quiet_end_hour():02d}h ({tz_name()})"


def wsl_ssh_host() -> str:
    return os.environ.get("LBG_INFOGRAPHISTE_WSL_SSH_HOST", "192.168.0.10").strip() or "192.168.0.10"


def wsl_ssh_port() -> int:
    try:
        return int(os.environ.get("LBG_INFOGRAPHISTE_WSL_SSH_PORT", "2222"))
    except ValueError:
        return 2222


def wsl_ssh_user() -> str:
    return os.environ.get("LBG_INFOGRAPHISTE_WSL_SSH_USER", "sdesh").strip() or "sdesh"


def wsl_ssh_identity() -> str:
    for key in ("LBG_INFOGRAPHISTE_LORA_TRAIN_SSH_IDENTITY", "LBG_SSH_IDENTITY"):
        val = os.environ.get(key, "").strip()
        if val:
            return val
    return "/home/lbg/.ssh/id_ed25519"


def probe_wsl_reachable(*, timeout_s: float = 8.0) -> dict[str, Any]:
    """Sonde SSH courte — BatchMode, pas de prompt."""
    host = wsl_ssh_host()
    port = wsl_ssh_port()
    user = wsl_ssh_user()
    identity = wsl_ssh_identity()
    cmd = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        f"ConnectTimeout={max(2, int(timeout_s))}",
        "-i",
        identity,
        "-p",
        str(port),
        f"{user}@{host}",
        "echo",
        "WSL_OK",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s + 2.0)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "host": host, "port": port, "error": str(exc)}
    ok = proc.returncode == 0 and "WSL_OK" in (proc.stdout or "")
    return {
        "ok": ok,
        "host": host,
        "port": port,
        "error": None if ok else ((proc.stderr or proc.stdout or "ssh failed").strip()[:240]),
    }


def daytime_keepalive_notice_text() -> str:
    return (
        "=== LBG Studios — WSL poste GPU (.10) ===\n"
        f"Merci de laisser cette machine allumée / joignable en journée "
        f"(hors fenêtre nuit {quiet_hours_label()}).\n"
        "Les jobs Pygmalion (LoRA / sprites) tournent depuis le core 140 via SSH :2222.\n"
        "Fenêtre d'extinction prévue : "
        f"{quiet_hours_label()} — les timers skipent automatiquement.\n"
        "Forçage hors créneau : LBG_WSL_FORCE=1 ou context force_wsl=true.\n"
    )


def push_daytime_keepalive_notice() -> dict[str, Any]:
    """Écrit ~/LBG_KEEP_ONLINE.txt sur le WSL (avis anti-coupure journée)."""
    if in_quiet_hours():
        return {
            "ok": True,
            "skipped": True,
            "outcome": "quiet_hours",
            "reply": f"Fenêtre nuit {quiet_hours_label()} — pas d'avis keepalive",
        }
    text = daytime_keepalive_notice_text()
    # Écrit via SSH (python) pour éviter les soucis de quoting shell.
    remote = (
        "import pathlib\n"
        "p = pathlib.Path.home() / 'LBG_KEEP_ONLINE.txt'\n"
        f"p.write_text({text!r}, encoding='utf-8')\n"
        "motd = pathlib.Path('/etc/motd')\n"
        "print('wrote', p)\n"
    )
    host = wsl_ssh_host()
    try:
        proc = subprocess.run(
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                "-o",
                "StrictHostKeyChecking=accept-new",
                "-o",
                "ConnectTimeout=8",
                "-i",
                wsl_ssh_identity(),
                "-p",
                str(wsl_ssh_port()),
                f"{wsl_ssh_user()}@{host}",
                "python3",
                "-",
            ],
            input=remote,
            capture_output=True,
            text=True,
            timeout=20.0,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "outcome": "error", "error": str(exc), "host": host}
    if proc.returncode != 0:
        return {
            "ok": False,
            "outcome": "error",
            "host": host,
            "error": (proc.stderr or proc.stdout or "ssh failed")[:300],
        }
    return {
        "ok": True,
        "outcome": "written",
        "host": host,
        "path": "~/LBG_KEEP_ONLINE.txt",
        "reply": (proc.stdout or "").strip() or "keepalive notice written",
    }


def should_skip_wsl_dependent_job(
    *,
    force: bool = False,
    context: dict[str, Any] | None = None,
    probe_reachability: bool = True,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Décide si un timer LoRA/sprites doit skip (sans créer de tâche failed)."""
    if force or force_requested(context=context):
        return {"skip": False, "outcome": "forced", "reply": "WSL forcé (ignore quiet hours)"}

    if in_quiet_hours(now):
        return {
            "skip": True,
            "outcome": "wsl_quiet_hours",
            "reply": (
                f"WSL fenêtre nuit {quiet_hours_label()} — "
                "job Pygmalion reporté (pas d'échec). "
                "Forcer : LBG_WSL_FORCE=1"
            ),
        }

    if not probe_reachability:
        return {"skip": False, "outcome": "daytime", "reply": "hors fenêtre nuit"}

    probe = probe_wsl_reachable()
    if probe.get("ok"):
        return {
            "skip": False,
            "outcome": "wsl_online",
            "reply": f"WSL joignable {probe.get('host')}:{probe.get('port')}",
            "probe": probe,
        }

    return {
        "skip": True,
        "outcome": "wsl_offline",
        "reply": (
            f"WSL offline ({probe.get('host')}:{probe.get('port')}) — "
            f"{probe.get('error') or 'ssh KO'}. "
            "Job reporté sans tâche failed (évite spam CR)."
        ),
        "probe": probe,
    }
