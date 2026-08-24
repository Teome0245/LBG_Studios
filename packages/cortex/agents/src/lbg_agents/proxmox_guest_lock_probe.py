"""Sonde locks Proxmox + snapshots vzdump orphelins + disque root hyperviseur (SSH).

Détecte le scénario « backup snapshot raté → lock snapshot-delete collé »
(ex. CT 111 après vzdump NAS plein).
"""

from __future__ import annotations

import os
import re
from typing import Any

from lbg_agents.proxmox_client import proxmox_hosts
from lbg_agents.proxmox_storage_probe import _parse_kv_block, _ssh_proxmox_host, proxmox_ssh_hosts


_OUTCOME_RANK = {"ok": 0, "warn": 1, "critical": 2}


def root_warn_pct() -> int:
    try:
        return max(1, min(99, int(os.environ.get("LBG_PROXMOX_ROOT_WARN_PCT", "90"))))
    except ValueError:
        return 90


def root_crit_pct() -> int:
    try:
        return max(root_warn_pct() + 1, min(100, int(os.environ.get("LBG_PROXMOX_ROOT_CRIT_PCT", "95"))))
    except ValueError:
        return 95


def _worst(*levels: str) -> str:
    worst = "ok"
    for lv in levels:
        if _OUTCOME_RANK.get(lv, 0) > _OUTCOME_RANK.get(worst, 0):
            worst = lv
    return worst


def _parse_csv_rows(raw: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in (raw or "").splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        # kind=lxc vmid=111 lock=snapshot-delete name=ollama-light
        parts = line.split()
        row: dict[str, str] = {}
        for part in parts:
            if "=" not in part:
                continue
            k, v = part.split("=", 1)
            row[k.strip()] = v.strip()
        if row:
            rows.append(row)
    return rows


def probe_proxmox_guest_lock_host(host: str) -> dict[str, Any]:
    """Sonde un hyperviseur via SSH (read-only)."""
    warn = root_warn_pct()
    crit = root_crit_pct()
    script = r"""
set -euo pipefail
root_pct=$(df -P / 2>/dev/null | awk 'NR==2 {gsub(/%/,"",$5); print $5}')
echo "root_pct=${root_pct:-na}"

# Locks LXC / QEMU depuis conf PVE (plus fiable que le formatage de pct/qm list)
for conf in /etc/pve/lxc/*.conf; do
  [ -f "$conf" ] || continue
  vmid=$(basename "$conf" .conf)
  lock=$(awk -F: '/^lock:/{print $2; exit}' "$conf" | tr -d ' ')
  [ -n "${lock:-}" ] || continue
  name=$(awk -F: '/^hostname:/{print $2; exit}' "$conf" | tr -d ' ')
  echo "locked kind=lxc vmid=${vmid} lock=${lock} name=${name:-?}"
done
for conf in /etc/pve/qemu-server/*.conf; do
  [ -f "$conf" ] || continue
  vmid=$(basename "$conf" .conf)
  lock=$(awk -F: '/^lock:/{print $2; exit}' "$conf" | tr -d ' ')
  [ -n "${lock:-}" ] || continue
  name=$(awk -F: '/^name:/{print $2; exit}' "$conf" | tr -d ' ')
  echo "locked kind=qemu vmid=${vmid} lock=${lock} name=${name:-?}"
done

# Snapshots LVM temporaire vzdump non nettoyés
while read -r lv origin; do
  [ -n "${lv:-}" ] || continue
  echo "orphan_snap lv=${lv} origin=${origin:-?}"
done < <(lvs -o lv_name,origin --noheadings --separator=' ' 2>/dev/null | awk '/vzdump/ {print $1,$2}')
"""
    ok, stdout, stderr = _ssh_proxmox_host(host, script, timeout_s=15.0)
    if not ok:
        return {
            "ok": False,
            "outcome": "critical",
            "error": stderr.strip() or "ssh_proxmox_failed",
            "host": host,
            "locked_guests": [],
            "orphan_snaps": [],
        }

    kv = _parse_kv_block(stdout)
    root_raw = kv.get("root_pct", "na")
    m = re.match(r"^(\d+(?:\.\d+)?)", str(root_raw))
    root_pct = float(m.group(1)) if m else None

    locked: list[dict[str, str]] = []
    orphans: list[dict[str, str]] = []
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("locked "):
            row = _parse_csv_rows(line.removeprefix("locked "))
            if row:
                locked.append(row[0])
        elif line.startswith("orphan_snap "):
            row = _parse_csv_rows(line.removeprefix("orphan_snap "))
            if row:
                orphans.append(row[0])

    alerts: list[str] = []
    outcome = "ok"
    if root_pct is not None and root_pct >= crit:
        outcome = "critical"
        alerts.append(f"root:/{root_pct}% (crit>={crit})")
    elif root_pct is not None and root_pct >= warn:
        outcome = _worst(outcome, "warn")
        alerts.append(f"root:/{root_pct}% (warn>={warn})")

    sticky_locks = {"snapshot-delete", "backup", "migrate", "clone", "rollback", "snapshot"}
    for g in locked:
        lock = str(g.get("lock") or "")
        label = f"{g.get('kind')}:{g.get('vmid')}({g.get('name') or '?'})"
        alerts.append(f"lock:{label}={lock}")
        if lock in sticky_locks or lock.startswith("snapshot"):
            outcome = _worst(outcome, "critical")
        else:
            outcome = _worst(outcome, "warn")

    for snap in orphans:
        alerts.append(f"orphan_snap:{snap.get('lv')}(origin={snap.get('origin')})")
        outcome = _worst(outcome, "critical")

    return {
        "ok": True,
        "outcome": outcome,
        "host": host,
        "root_pct": root_pct,
        "locked_guests": locked,
        "orphan_snaps": orphans,
        "alerts": alerts,
        "thresholds": {"root_warn": warn, "root_crit": crit},
    }


def _aggregate(hosts: list[dict[str, Any]]) -> dict[str, Any]:
    if not hosts:
        return {
            "ok": False,
            "outcome": "critical",
            "error": "no_proxmox_hosts_configured",
            "hosts": [],
            "alerts": ["proxmox_guest_lock: no hosts"],
        }
    ok_any = any(h.get("ok") for h in hosts)
    outcome = "ok"
    alerts: list[str] = []
    locked: list[dict[str, Any]] = []
    orphans: list[dict[str, Any]] = []
    for h in hosts:
        host = str(h.get("host") or "?")
        if not h.get("ok"):
            outcome = _worst(outcome, "critical")
            alerts.append(f"{host}: {h.get('error', 'ssh_failed')}")
            continue
        outcome = _worst(outcome, str(h.get("outcome") or "ok"))
        for a in h.get("alerts") or []:
            alerts.append(f"{host}:{a}")
        for g in h.get("locked_guests") or []:
            locked.append({"host": host, **g})
        for s in h.get("orphan_snaps") or []:
            orphans.append({"host": host, **s})

    lines = [
        f"Proxmox guest locks: outcome={outcome} hosts={len(hosts)} "
        f"locked={len(locked)} orphan_snaps={len(orphans)}"
    ]
    for g in locked:
        lines.append(
            f"  lock {g.get('host')} {g.get('kind')}/{g.get('vmid')} "
            f"{g.get('name')} → {g.get('lock')}"
        )
    for s in orphans:
        lines.append(f"  orphan_snap {s.get('host')} {s.get('lv')} (origin={s.get('origin')})")
    if alerts:
        lines.append("Alertes: " + "; ".join(alerts))

    return {
        "ok": ok_any,
        "outcome": outcome,
        "hosts": hosts,
        "locked_guests": locked,
        "orphan_snaps": orphans,
        "alerts": alerts,
        "reply": "\n".join(lines),
    }


def probe_proxmox_guest_lock_local() -> dict[str, Any]:
    hosts = proxmox_ssh_hosts() or proxmox_hosts()
    return _aggregate([probe_proxmox_guest_lock_host(h) for h in hosts])


def run_proxmox_guest_lock_probe(
    *,
    actor_id: str = "ops",
    text: str = "",
) -> dict[str, Any]:
    _ = actor_id, text
    inner = probe_proxmox_guest_lock_local()
    return {
        "ok": bool(inner.get("ok")),
        "outcome": inner.get("outcome"),
        "agent": "proxmox_guest_lock_probe",
        "guest_lock": inner,
        "alerts": inner.get("alerts") or [],
        "reply": inner.get("reply") or "",
    }
