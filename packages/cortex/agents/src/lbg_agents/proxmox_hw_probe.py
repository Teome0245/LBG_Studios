"""Sonde matériel hyperviseurs Proxmox (BMC/IPMI, PERC/SMART, coretemp) — L1 Héphaïstos."""

from __future__ import annotations

import os
import subprocess
from typing import Any

from lbg_agents.proxmox_storage_probe import proxmox_ssh_identity, proxmox_ssh_user

_DEFAULT_HW_HOSTS = ("192.168.0.200", "192.168.0.201")
_OUTCOME_RANK = {"ok": 0, "degraded": 1, "warn": 2, "critical": 3}

_REMOTE_PROBE_SCRIPT = r"""
set +e
hostname_s=$(hostname -s 2>/dev/null || hostname 2>/dev/null || echo unknown)
product=$(dmidecode -s system-product-name 2>/dev/null | head -1)
serial=$(dmidecode -s system-serial-number 2>/dev/null | head -1)
bios=$(dmidecode -s bios-version 2>/dev/null | head -1)
pve=$(pveversion 2>/dev/null | head -1)
uptime_s=$(cut -d. -f1 /proc/uptime 2>/dev/null)
load=$(cut -d' ' -f1-3 /proc/loadavg)

ipmi_dev=0
[[ -e /dev/ipmi0 || -e /dev/ipmi/0 || -e /dev/ipmidev/0 ]] && ipmi_dev=1
ipmi_si_fail=0
dmesg 2>/dev/null | grep -q 'ipmi_si.*Interface detection failed' && ipmi_si_fail=1
ipmi_mc_ok=0
if [[ "$ipmi_dev" -eq 1 ]]; then
  ipmitool -I open mc info >/dev/null 2>&1 && ipmi_mc_ok=1
fi

perc_present=0
lspci 2>/dev/null | grep -qi 'MegaRAID\|PERC' && perc_present=1
perccli_bin=""
for b in perccli perccli64 storcli storcli64; do
  command -v "$b" >/dev/null 2>&1 && perccli_bin="$b" && break
done

pkg0=""; pkg1=""
for h in /sys/class/hwmon/hwmon*/; do
  [[ "$(cat "$h/name" 2>/dev/null)" == "coretemp" ]] || continue
  for t in "$h"/temp*_input; do
    [[ -f "$t" ]] || continue
    lab=$(cat "${t%_input}_label" 2>/dev/null || true)
    c=$(($(cat "$t")/1000))
    if [[ "$lab" == "Package id 0" ]]; then pkg0=$c; fi
    if [[ "$lab" == "Package id 1" ]]; then pkg1=$c; fi
  done
done

smart_lines=""
smart_warn=0
smart_fail=0
smart_count=0
if [[ "$perc_present" -eq 1 ]]; then
  for i in 0 1 2 3 4 5 6 7 8 9 10 11; do
    out=$(smartctl -i -H -A -d megaraid,$i /dev/sda 2>/dev/null) || continue
    echo "$out" | grep -q 'SMART overall-health\|SMART Health Status' || continue
    model=$(echo "$out" | awk -F': *' '/^Device Model:|^Product:/{print $2; exit}')
    serial_d=$(echo "$out" | awk -F': *' '/^Serial Number:|^Serial number:/{print $2; exit}')
    health=$(echo "$out" | awk -F': *' '/SMART overall-health self-assessment test result|SMART Health Status/{print $2; exit}')
    realloc=$(echo "$out" | awk '/Reallocated_Sector_Ct/{print $NF; exit}')
    temp=$(echo "$out" | awk '/Airflow_Temperature_Cel|Temperature_Celsius/{print $NF; exit}')
    [[ -z "$realloc" ]] && realloc=0
    smart_count=$((smart_count+1))
    echo "$health" | grep -qiE 'PASSED|OK' || smart_fail=$((smart_fail+1))
    if [[ "$realloc" =~ ^[0-9]+$ ]] && [[ "$realloc" -ge 50 ]]; then
      smart_warn=1
    fi
    smart_lines="${smart_lines}${i}|${model}|${serial_d}|${health}|${realloc}|${temp};"
  done
fi

bmc_ok=0
[[ "$ipmi_mc_ok" -eq 1 ]] && bmc_ok=1

echo "HOSTNAME=${hostname_s}"
echo "PRODUCT=${product}"
echo "SERIAL=${serial}"
echo "BIOS=${bios}"
echo "PVE=${pve}"
echo "UPTIME_S=${uptime_s}"
echo "LOAD=${load}"
echo "IPMI_DEV=${ipmi_dev}"
echo "IPMI_SI_FAIL=${ipmi_si_fail}"
echo "IPMI_MC_OK=${ipmi_mc_ok}"
echo "BMC_OK=${bmc_ok}"
echo "PERC_PRESENT=${perc_present}"
echo "PERCCLI=${perccli_bin}"
echo "CPU_PKG0=${pkg0}"
echo "CPU_PKG1=${pkg1}"
echo "SMART_COUNT=${smart_count}"
echo "SMART_WARN=${smart_warn}"
echo "SMART_FAIL=${smart_fail}"
echo "SMART_LINES=${smart_lines}"
"""


def proxmox_hw_ssh_hosts() -> list[str]:
    """Hyperviseurs à sonder pour le HW (NUC 200 + R720 201 par défaut)."""
    raw = (
        os.environ.get("LBG_PROXMOX_HW_SSH_HOSTS")
        or os.environ.get("LBG_PROXMOX_SSH_HOSTS")
        or os.environ.get("LBG_PROXMOX_HOSTS")
        or ""
    ).strip()
    if raw:
        out: list[str] = []
        for part in raw.split(","):
            h = part.strip().removeprefix("https://").removeprefix("http://").split(":", 1)[0]
            if h and h not in out:
                out.append(h)
        if out:
            return out
    return list(_DEFAULT_HW_HOSTS)


def thermal_warn_c() -> int:
    try:
        return max(40, min(100, int(os.environ.get("LBG_PROXMOX_HW_THERMAL_WARN_C", "70"))))
    except ValueError:
        return 70


def thermal_crit_c() -> int:
    try:
        return max(thermal_warn_c() + 1, min(120, int(os.environ.get("LBG_PROXMOX_HW_THERMAL_CRIT_C", "85"))))
    except ValueError:
        return 85


def smart_realloc_warn() -> int:
    try:
        return max(1, int(os.environ.get("LBG_PROXMOX_HW_SMART_REALLOC_WARN", "50")))
    except ValueError:
        return 50


def _parse_kv_block(raw: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in raw.splitlines():
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        out[key.strip()] = val.strip()
    return out


def _ssh_hw_host(host: str, script: str, *, timeout_s: float = 45.0) -> tuple[bool, str, str]:
    user = proxmox_ssh_user()
    cmd = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        f"ConnectTimeout={min(15, int(timeout_s))}",
    ]
    identity = proxmox_ssh_identity()
    if identity:
        cmd.extend(["-i", identity])
    cmd.extend([f"{user}@{host}", "bash", "-s"])
    try:
        proc = subprocess.run(
            cmd,
            input=script,
            capture_output=True,
            text=True,
            timeout=timeout_s + 5,
        )
        return proc.returncode == 0, proc.stdout or "", proc.stderr or ""
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, "", str(exc)


def _as_int(raw: str | None, default: int = 0) -> int:
    if raw is None or raw == "":
        return default
    try:
        return int(float(str(raw).strip()))
    except ValueError:
        return default


def _parse_smart_lines(raw: str) -> list[dict[str, Any]]:
    drives: list[dict[str, Any]] = []
    for chunk in (raw or "").split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = chunk.split("|")
        while len(parts) < 6:
            parts.append("")
        realloc = parts[4]
        temp = parts[5]
        drives.append(
            {
                "megaraid": parts[0],
                "model": parts[1],
                "serial": parts[2],
                "health": parts[3],
                "reallocated": int(realloc) if str(realloc).isdigit() else realloc,
                "temp_c": int(temp) if str(temp).isdigit() else temp,
            }
        )
    return drives


def _outcome_from_kv(kv: dict[str, str]) -> tuple[str, dict[str, Any]]:
    warn_c = thermal_warn_c()
    crit_c = thermal_crit_c()
    realloc_thr = smart_realloc_warn()

    bmc_ok = _as_int(kv.get("BMC_OK")) == 1
    smart_fail = _as_int(kv.get("SMART_FAIL"))
    smart_warn_flag = _as_int(kv.get("SMART_WARN"))
    pkg0 = kv.get("CPU_PKG0") or ""
    pkg1 = kv.get("CPU_PKG1") or ""
    temps = [_as_int(t) for t in (pkg0, pkg1) if str(t).strip().isdigit()]

    # Re-evaluate realloc from SMART_LINES if present
    drives = _parse_smart_lines(kv.get("SMART_LINES", ""))
    if not smart_warn_flag:
        for d in drives:
            r = d.get("reallocated")
            if isinstance(r, int) and r >= realloc_thr:
                smart_warn_flag = 1
                break

    thermal_state = "ok"
    for t in temps:
        if t >= crit_c:
            thermal_state = "critical"
            break
        if t >= warn_c and thermal_state == "ok":
            thermal_state = "warn"

    storage_state = "ok"
    if smart_fail > 0:
        storage_state = "smart_fail"
    elif smart_warn_flag:
        storage_state = "smart_warn"
    elif _as_int(kv.get("PERC_PRESENT")) == 1 and _as_int(kv.get("SMART_COUNT")) == 0:
        storage_state = "perc_no_smart"

    if storage_state == "smart_fail" or thermal_state == "critical":
        outcome = "critical"
    elif storage_state == "smart_warn" or thermal_state == "warn":
        outcome = "warn"
    elif not bmc_ok:
        outcome = "degraded"
    else:
        outcome = "ok"

    detail = {
        "bmc": {
            "ok": bmc_ok,
            "state": "ok" if bmc_ok else "dead",
            "ipmi_dev": _as_int(kv.get("IPMI_DEV")),
            "ipmi_si_fail": _as_int(kv.get("IPMI_SI_FAIL")),
            "mc_ok": _as_int(kv.get("IPMI_MC_OK")),
        },
        "storage": {
            "state": storage_state,
            "perc_present": _as_int(kv.get("PERC_PRESENT")),
            "perccli": (kv.get("PERCCLI") or None) or None,
            "smart_count": _as_int(kv.get("SMART_COUNT")),
            "smart_warn": bool(smart_warn_flag),
            "smart_fail": smart_fail,
            "drives": drives,
        },
        "thermal": {
            "state": thermal_state,
            "package0_c": _as_int(pkg0) if str(pkg0).strip().isdigit() else None,
            "package1_c": _as_int(pkg1) if str(pkg1).strip().isdigit() else None,
            "warn_c": warn_c,
            "crit_c": crit_c,
        },
    }
    return outcome, detail


def probe_proxmox_hw_host(host: str) -> dict[str, Any]:
    """Sonde un hyperviseur Proxmox (BMC / PERC / thermiques) via SSH read-only."""
    ok, stdout, stderr = _ssh_hw_host(host, _REMOTE_PROBE_SCRIPT)
    if not ok:
        return {
            "ok": False,
            "outcome": "critical",
            "error": stderr.strip() or "ssh_proxmox_hw_failed",
            "host": host,
        }

    kv = _parse_kv_block(stdout)
    outcome, detail = _outcome_from_kv(kv)
    return {
        "ok": True,
        "outcome": outcome,
        "host": host,
        "hostname": kv.get("HOSTNAME"),
        "product": kv.get("PRODUCT"),
        "serial": kv.get("SERIAL"),
        "bios": kv.get("BIOS"),
        "pve": kv.get("PVE"),
        "uptime_s": _as_int(kv.get("UPTIME_S")),
        "load": kv.get("LOAD"),
        "raw": {k: kv.get(k) for k in (
            "HOSTNAME", "PRODUCT", "BMC_OK", "PERC_PRESENT", "PERCCLI",
            "CPU_PKG0", "CPU_PKG1", "SMART_COUNT", "SMART_WARN", "SMART_FAIL",
        )},
        **detail,
    }


def _aggregate_hw_probes(hosts: list[dict[str, Any]]) -> dict[str, Any]:
    if not hosts:
        return {
            "ok": False,
            "outcome": "critical",
            "error": "no_proxmox_hw_hosts_configured",
            "hosts": [],
        }

    ok_hosts = [h for h in hosts if h.get("ok")]
    if not ok_hosts:
        first = hosts[0]
        return {
            "ok": False,
            "outcome": "critical",
            "error": first.get("error") or "all_proxmox_hw_probes_failed",
            "host": first.get("host"),
            "hosts": hosts,
        }

    # Worst among all rows (failed SSH counts as critical)
    ranked = hosts
    worst = max(
        ranked,
        key=lambda h: _OUTCOME_RANK.get(str(h.get("outcome") or "critical"), 3),
    )
    outcome = str(worst.get("outcome") or "ok")
    any_fail = any(not h.get("ok") for h in hosts)
    if any_fail and _OUTCOME_RANK.get(outcome, 0) < _OUTCOME_RANK["critical"]:
        outcome = "critical"

    return {
        "ok": not any_fail or bool(ok_hosts),
        "outcome": outcome,
        "host": worst.get("host"),
        "hostname": worst.get("hostname"),
        "product": worst.get("product"),
        "bmc": worst.get("bmc"),
        "storage": worst.get("storage"),
        "thermal": worst.get("thermal"),
        "hosts": hosts,
        "proxmox_hw_hosts": [h.get("host") for h in hosts],
        "thresholds": {
            "thermal_warn_c": thermal_warn_c(),
            "thermal_crit_c": thermal_crit_c(),
            "smart_realloc_warn": smart_realloc_warn(),
        },
    }


def probe_proxmox_hw_local() -> dict[str, Any]:
    """Interroge tous les hyperviseurs HW configurés via SSH."""
    host_list = proxmox_hw_ssh_hosts()
    probes = [probe_proxmox_hw_host(host) for host in host_list]
    return _aggregate_hw_probes(probes)


def format_hw_probe_reply(payload: dict[str, Any]) -> str:
    if not payload.get("ok") and not payload.get("hosts"):
        host = payload.get("host") or "?"
        return f"HW Proxmox ({host}) : sonde KO — {payload.get('error', '?')}"

    host_rows = payload.get("hosts")
    if isinstance(host_rows, list) and host_rows:
        lines = [
            f"Sonde matériel Proxmox — {len(host_rows)} hyperviseur(s)",
            f"Résultat global : {payload.get('outcome')} (pire : {payload.get('host')})",
            "",
        ]
        for row in host_rows:
            if not isinstance(row, dict):
                continue
            if not row.get("ok"):
                lines.append(f"  • {row.get('host')} : ERREUR — {row.get('error', '?')}")
                continue
            bmc = (row.get("bmc") or {}).get("state", "?")
            stor = (row.get("storage") or {}).get("state", "?")
            therm = (row.get("thermal") or {}).get("state", "?")
            t0 = (row.get("thermal") or {}).get("package0_c")
            t1 = (row.get("thermal") or {}).get("package1_c")
            lines.append(
                f"  • {row.get('host')} ({row.get('hostname') or row.get('product') or '?'}) "
                f"[{row.get('outcome')}] BMC={bmc} storage={stor} thermal={therm} "
                f"pkg={t0}/{t1}°C"
            )
        if payload.get("outcome") == "degraded":
            lines.append("→ BMC/iDRAC morte connue sur R720 — surveillance in-band (voir runbook_r720_idrac_hs.md)")
        elif payload.get("outcome") not in ("ok", None):
            lines.append("→ Voir runbook_r720_idrac_hs.md / diagnose_r720_hw_lan.sh")
        return "\n".join(lines)

    return f"HW Proxmox : {payload.get('outcome')} @ {payload.get('host')}"


def run_proxmox_hw_probe(*, actor_id: str = "proxmox_hw_probe", text: str = "") -> dict[str, Any]:
    payload = probe_proxmox_hw_local()
    return {
        "ok": bool(payload.get("ok")),
        "agent": "proxmox_hw_probe",
        "actor_id": actor_id,
        "request_text": text,
        "outcome": payload.get("outcome", "critical" if not payload.get("ok") else "ok"),
        "proxmox_hw": payload,
        "reply": format_hw_probe_reply(payload),
    }


def main() -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Sonde matériel Proxmox (BMC / PERC / thermiques)")
    parser.add_argument("--json", action="store_true", help="Sortie JSON")
    args = parser.parse_args()

    payload = probe_proxmox_hw_local()
    outcome = str(payload.get("outcome") or ("critical" if not payload.get("ok") else "ok"))

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_hw_probe_reply(payload))

    if not payload.get("ok") and outcome == "critical":
        return 3
    if outcome == "critical":
        return 2
    if outcome in ("warn", "degraded"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
