"""Sonde métriques guest (disque / load / RAM) — mur INFRA LAN (100/140/245/246).

Read-only via SSH ``lbg@host`` (ou local si hôte = core courant).
"""

from __future__ import annotations

import os
import socket
import subprocess
from typing import Any

from lbg_agents.infra_guest_remediation import build_guest_remediation_plan, format_guest_plan_reply


_PROBE_SCRIPT = r"""
disk_pct=$(df -P / 2>/dev/null | awk 'NR==2 {gsub(/%/,"",$5); print $5}')
load1=$(cut -d' ' -f1 /proc/loadavg 2>/dev/null)
nproc=$(nproc 2>/dev/null || echo 1)
mem_pct=$(free 2>/dev/null | awk '/^Mem:/ { if ($2>0) printf "%.0f", ($3/$2)*100; else print 0 }')
echo "disk_pct=${disk_pct:-}"
echo "load1=${load1:-}"
echo "nproc=${nproc:-1}"
echo "mem_pct=${mem_pct:-}"
"""


def disk_warn_pct() -> int:
    try:
        return max(1, min(99, int(os.environ.get("LBG_GUEST_DISK_WARN_PCT", "70"))))
    except ValueError:
        return 70


def disk_crit_pct() -> int:
    try:
        return max(disk_warn_pct() + 1, min(100, int(os.environ.get("LBG_GUEST_DISK_CRIT_PCT", "85"))))
    except ValueError:
        return 85


def load_warn_ratio() -> float:
    try:
        return max(0.1, float(os.environ.get("LBG_GUEST_LOAD_WARN_RATIO", "1.0")))
    except ValueError:
        return 1.0


def load_crit_ratio() -> float:
    try:
        return max(load_warn_ratio() + 0.1, float(os.environ.get("LBG_GUEST_LOAD_CRIT_RATIO", "2.0")))
    except ValueError:
        return 2.0


def ssh_user() -> str:
    return os.environ.get("LBG_SSH_USER", "lbg").strip() or "lbg"


def ssh_identity() -> str:
    return (os.environ.get("LBG_SSH_IDENTITY") or "").strip()


def _precu_optional() -> bool:
    return os.environ.get("LBG_GUEST_METRICS_PRECU_REQUIRED", "0").strip().lower() not in (
        "1",
        "true",
        "yes",
        "on",
    )


def default_wall_hosts() -> list[dict[str, str]]:
    """Hôtes du mur INFRA LAN (labels Pilot / Cockpit)."""
    return [
        {"id": "web", "label": "Front web", "host": os.environ.get("LBG_LAN_HOST_WEB", "192.168.0.100").strip() or "192.168.0.100"},
        {"id": "core", "label": "Core", "host": os.environ.get("LBG_LAN_HOST_CORE", "192.168.0.140").strip() or "192.168.0.140"},
        {
            "id": "precu",
            "label": "Core3 SWG",
            "host": os.environ.get("LBG_LAN_HOST_PRECU", "192.168.0.245").strip() or "192.168.0.245",
            "optional": "1" if _precu_optional() else "0",
        },
        {"id": "prime", "label": "Prime monde", "host": os.environ.get("LBG_LAN_HOST_MMO", "192.168.0.246").strip() or "192.168.0.246"},
    ]


def wall_hosts() -> list[dict[str, str]]:
    """Override : ``LBG_GUEST_METRICS_HOSTS=id:host[:label],...``."""
    raw = os.environ.get("LBG_GUEST_METRICS_HOSTS", "").strip()
    if not raw:
        return default_wall_hosts()
    out: list[dict[str, str]] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        bits = part.split(":")
        if len(bits) < 2:
            continue
        hid, host = bits[0].strip(), bits[1].strip()
        label = bits[2].strip() if len(bits) >= 3 else hid
        if hid and host:
            out.append({"id": hid, "label": label, "host": host})
    return out or default_wall_hosts()


def _local_ips() -> set[str]:
    ips = {"127.0.0.1", "localhost"}
    try:
        ips.add(socket.gethostbyname(socket.gethostname()))
    except OSError:
        pass
    core = os.environ.get("LBG_LAN_HOST_CORE", "192.168.0.140").strip().split(":")[0]
    if core:
        ips.add(core)
    return ips


def _parse_kv(raw: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in raw.splitlines():
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _run_probe_local() -> tuple[bool, str, str]:
    try:
        proc = subprocess.run(
            ["bash", "-c", _PROBE_SCRIPT],
            capture_output=True,
            text=True,
            timeout=8,
        )
        return proc.returncode == 0, proc.stdout or "", proc.stderr or ""
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, "", str(exc)


def _run_probe_ssh(host: str, *, timeout_s: float = 12.0) -> tuple[bool, str, str]:
    user = ssh_user()
    cmd = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        f"ConnectTimeout={int(timeout_s)}",
        "-o",
        "LogLevel=ERROR",
    ]
    identity = ssh_identity()
    if identity:
        cmd.extend(["-i", identity])
    cmd.extend([f"{user}@{host}", "bash", "-s"])
    try:
        proc = subprocess.run(
            cmd,
            input=_PROBE_SCRIPT,
            capture_output=True,
            text=True,
            timeout=timeout_s + 5,
        )
        return proc.returncode == 0, proc.stdout or "", proc.stderr or ""
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, "", str(exc)


def _outcome_for_metrics(
    *,
    disk_pct: float | None,
    load1: float | None,
    nproc: int,
    warn_disk: int,
    crit_disk: int,
    warn_load: float,
    crit_load: float,
) -> tuple[str, list[str]]:
    alerts: list[str] = []
    rank = 0  # 0 ok, 1 warn, 2 critical
    if disk_pct is not None:
        if disk_pct >= crit_disk:
            rank = max(rank, 2)
            alerts.append(f"disk {disk_pct:.0f}% ≥ crit {crit_disk}%")
        elif disk_pct >= warn_disk:
            rank = max(rank, 1)
            alerts.append(f"disk {disk_pct:.0f}% ≥ warn {warn_disk}%")
    if load1 is not None and nproc > 0:
        ratio = load1 / float(nproc)
        # Load seul → warn max par défaut (évite hard-fail digest / spam Héphaïstos).
        # Opt-in critique : LBG_GUEST_LOAD_CAN_CRIT=1
        load_can_crit = os.environ.get("LBG_GUEST_LOAD_CAN_CRIT", "0").strip().lower() in (
            "1",
            "true",
            "yes",
            "on",
        )
        if ratio >= crit_load:
            if load_can_crit:
                rank = max(rank, 2)
                alerts.append(f"load {load1:.2f}/{nproc}={ratio:.2f} ≥ crit {crit_load}")
            else:
                rank = max(rank, 1)
                alerts.append(
                    f"load {load1:.2f}/{nproc}={ratio:.2f} ≥ crit {crit_load} (soft→warn)"
                )
        elif ratio >= warn_load:
            rank = max(rank, 1)
            alerts.append(f"load {load1:.2f}/{nproc}={ratio:.2f} ≥ warn {warn_load}")
    outcome = {0: "ok", 1: "warn", 2: "critical"}[rank]
    return outcome, alerts


def probe_guest_host(spec: dict[str, str]) -> dict[str, Any]:
    """Sonde un hôte guest (SSH ou local)."""
    host = str(spec.get("host") or "").strip()
    hid = str(spec.get("id") or host).strip()
    label = str(spec.get("label") or hid).strip()
    warn_d, crit_d = disk_warn_pct(), disk_crit_pct()
    warn_l, crit_l = load_warn_ratio(), load_crit_ratio()

    base: dict[str, Any] = {
        "ok": False,
        "id": hid,
        "label": label,
        "host": host,
        "outcome": "critical",
        "disk_percent": None,
        "load1": None,
        "nproc": None,
        "load_ratio": None,
        "mem_percent": None,
        "alerts": [],
        "thresholds": {
            "disk_warn": warn_d,
            "disk_crit": crit_d,
            "load_warn_ratio": warn_l,
            "load_crit_ratio": crit_l,
        },
    }
    if not host:
        base["error"] = "host manquant"
        return base

    local = host in _local_ips() or host in ("127.0.0.1", "localhost")
    if local:
        ok, stdout, stderr = _run_probe_local()
        base["transport"] = "local"
    else:
        ok, stdout, stderr = _run_probe_ssh(host)
        base["transport"] = "ssh"

    if not ok:
        err_msg = (stderr or stdout or "probe failed").strip()[:400]
        if str(spec.get("optional") or "").strip().lower() in ("1", "true", "yes", "on"):
            base.update(
                {
                    "ok": True,
                    "optional": True,
                    "outcome": "off",
                    "error": err_msg,
                    "alerts": [],
                }
            )
            return base
        base["error"] = err_msg
        base["alerts"] = [f"sonde KO: {base['error']}"]
        return base

    kv = _parse_kv(stdout)
    try:
        disk_pct = float(kv["disk_pct"]) if kv.get("disk_pct") not in (None, "") else None
    except ValueError:
        disk_pct = None
    try:
        load1 = float(kv["load1"]) if kv.get("load1") not in (None, "") else None
    except ValueError:
        load1 = None
    try:
        nproc = max(1, int(float(kv.get("nproc") or "1")))
    except ValueError:
        nproc = 1
    try:
        mem_pct = float(kv["mem_pct"]) if kv.get("mem_pct") not in (None, "") else None
    except ValueError:
        mem_pct = None

    if disk_pct is None and load1 is None:
        base["error"] = "métriques absentes"
        base["alerts"] = ["sortie sonde vide / non parsable"]
        return base

    outcome, alerts = _outcome_for_metrics(
        disk_pct=disk_pct,
        load1=load1,
        nproc=nproc,
        warn_disk=warn_d,
        crit_disk=crit_d,
        warn_load=warn_l,
        crit_load=crit_l,
    )
    load_ratio = (load1 / float(nproc)) if load1 is not None else None
    base.update(
        {
            "ok": True,
            "outcome": outcome,
            "disk_percent": disk_pct,
            "load1": load1,
            "nproc": nproc,
            "load_ratio": round(load_ratio, 3) if load_ratio is not None else None,
            "mem_percent": mem_pct,
            "alerts": alerts,
        }
    )
    return base


_OUTCOME_RANK = {"ok": 0, "off": 0, "warn": 1, "critical": 2}


def _aggregate(hosts: list[dict[str, Any]]) -> dict[str, Any]:
    if not hosts:
        return {
            "ok": False,
            "outcome": "critical",
            "hosts": [],
            "alerts": ["aucun hôte configuré"],
            "stressed": [],
        }
    worst = "ok"
    alerts: list[str] = []
    stressed: list[dict[str, Any]] = []
    any_ok = False
    for row in hosts:
        if row.get("ok"):
            any_ok = True
        oc = str(row.get("outcome") or "critical")
        if _OUTCOME_RANK.get(oc, 2) > _OUTCOME_RANK.get(worst, 0):
            worst = oc
        for a in row.get("alerts") or []:
            alerts.append(f"{row.get('id')}: {a}")
        if oc in {"warn", "critical"} or not row.get("ok"):
            stressed.append(row)
    return {
        "ok": any_ok,
        "outcome": worst if any_ok else "critical",
        "hosts": hosts,
        "stressed": stressed,
        "alerts": alerts,
        "thresholds": {
            "disk_warn": disk_warn_pct(),
            "disk_crit": disk_crit_pct(),
            "load_warn_ratio": load_warn_ratio(),
            "load_crit_ratio": load_crit_ratio(),
        },
    }


def probe_guest_metrics_wall() -> dict[str, Any]:
    """Sonde le mur INFRA LAN et agrège le pire outcome."""
    rows = [probe_guest_host(spec) for spec in wall_hosts()]
    return _aggregate(rows)


def format_guest_metrics_reply(payload: dict[str, Any]) -> str:
    lines = [f"Sonde guest mur INFRA LAN — {payload.get('outcome')}"]
    for row in payload.get("hosts") or []:
        if not isinstance(row, dict):
            continue
        disk = row.get("disk_percent")
        load = row.get("load1")
        nproc = row.get("nproc")
        disk_s = f"{disk:.0f}%" if isinstance(disk, (int, float)) else "?"
        load_s = f"{load:.2f}" if isinstance(load, (int, float)) else "?"
        lines.append(
            f"  {row.get('label') or row.get('id')} ({row.get('host')}) "
            f"disk={disk_s} load={load_s}/{nproc or '?'} → {row.get('outcome')}"
        )
    for a in payload.get("alerts") or []:
        lines.append(f"  ⚠ {a}")
    return "\n".join(lines)


def run_guest_metrics_probe(*, actor_id: str = "system", text: str = "") -> dict[str, Any]:
    """Entrée devops / ops — sonde + plan de remédiation consultatif."""
    wall = probe_guest_metrics_wall()
    plan = build_guest_remediation_plan(wall)
    return {
        "agent": "guest_metrics_probe",
        "actor_id": actor_id,
        "request_text": text,
        "ok": bool(wall.get("ok")),
        "outcome": wall.get("outcome"),
        "guest_metrics": wall,
        "remediation_plan": plan,
        "reply": format_guest_metrics_reply(wall) + "\n\n" + format_guest_plan_reply(plan),
    }
