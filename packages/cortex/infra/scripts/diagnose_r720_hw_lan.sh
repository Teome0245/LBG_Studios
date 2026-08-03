#!/usr/bin/env bash
# Diagnostic matériel hyperviseurs Proxmox depuis l'OS (in-band).
# Utile quand l'iDRAC est HS : IPMI KCS, PERC/smartctl, coretemp.
# Boucle sur LBG_PROXMOX_HW_SSH_HOSTS (défaut 192.168.0.200,192.168.0.201).
#
# Usage :
#   bash infra/scripts/diagnose_r720_hw_lan.sh
#   bash infra/scripts/diagnose_r720_hw_lan.sh --json
#   LBG_PROXMOX_HW_SSH_HOSTS=192.168.0.201 bash infra/scripts/diagnose_r720_hw_lan.sh
#   LBG_PROXMOX_SSH_HOST=192.168.0.201 bash infra/scripts/diagnose_r720_hw_lan.sh
#
# Codes sortie : 0 OK, 1 warn/degraded, 2 critical, 3 erreur sonde

set -euo pipefail

JSON=0
[[ "${1:-}" == "--json" ]] && JSON=1
USER="${LBG_PROXMOX_SSH_USER:-root}"

if [[ -n "${LBG_PROXMOX_HW_SSH_HOSTS:-}" ]]; then
  HOSTS_CSV="${LBG_PROXMOX_HW_SSH_HOSTS}"
elif [[ -n "${LBG_PROXMOX_SSH_HOST:-${LBG_PROXMOX_HOST:-}}" ]]; then
  HOSTS_CSV="${LBG_PROXMOX_SSH_HOST:-${LBG_PROXMOX_HOST}}"
else
  HOSTS_CSV="192.168.0.200,192.168.0.201"
fi

IFS=',' read -r -a _RAW_HOSTS <<< "${HOSTS_CSV}"
HOSTS=()
for h in "${_RAW_HOSTS[@]}"; do
  h="${h#"${h%%[![:space:]]*}"}"
  h="${h%"${h##*[![:space:]]}"}"
  [[ -n "$h" ]] && HOSTS+=("$h")
done

GLOBAL_SEVERITY=0
TMPDIR_JSON="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_JSON"' EXIT
IDX=0

diagnose_one() {
  local HOST="$1"
  local SSH=(ssh -o BatchMode=yes -o ConnectTimeout=8 "${USER}@${HOST}")
  local SEVERITY=0

  if ! "${SSH[@]}" 'true' >/dev/null 2>&1; then
    echo "ERREUR: SSH ${USER}@${HOST} impossible (BatchMode)." >&2
    if [[ "$JSON" -eq 1 ]]; then
      printf '%s\n' "{\"host\":\"${HOST}\",\"ok\":false,\"error\":\"ssh_failed\",\"severity\":3}" > "${TMPDIR_JSON}/${IDX}.json"
    fi
    [[ $GLOBAL_SEVERITY -lt 3 ]] && GLOBAL_SEVERITY=3
    return 0
  fi

  local REMOTE_OUT
  REMOTE_OUT="$("${SSH[@]}" 'bash -s' <<'REMOTE'
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
REMOTE
)"

  local HOSTNAME="" PRODUCT="" SERIAL="" BIOS="" PVE="" UPTIME_S="" LOAD=""
  local IPMI_DEV=0 IPMI_SI_FAIL=0 IPMI_MC_OK=0 BMC_OK=0
  local PERC_PRESENT=0 PERCCLI="" CPU_PKG0="" CPU_PKG1=""
  local SMART_COUNT=0 SMART_WARN=0 SMART_FAIL=0 SMART_LINES=""

  eval "$(echo "$REMOTE_OUT" | sed -n 's/^\([A-Z0-9_]*\)=\(.*\)$/\1=\2/p' | while IFS= read -r line; do
    key="${line%%=*}"
    val="${line#*=}"
    printf '%s=%q\n' "$key" "$val"
  done)"

  local BMC_STATE="ok"
  [[ "${BMC_OK:-0}" -ne 1 ]] && BMC_STATE="dead" && SEVERITY=1

  local STORAGE_STATE="ok"
  if [[ "${PERC_PRESENT:-0}" -eq 1 ]]; then
    if [[ "${SMART_FAIL:-0}" -gt 0 ]]; then
      STORAGE_STATE="smart_fail"
      SEVERITY=2
    elif [[ "${SMART_WARN:-0}" -eq 1 ]]; then
      STORAGE_STATE="smart_warn"
      [[ $SEVERITY -lt 1 ]] && SEVERITY=1
    fi
  else
    STORAGE_STATE="no_perc"
  fi

  local THERMAL_STATE="ok"
  for t in "${CPU_PKG0:-}" "${CPU_PKG1:-}"; do
    [[ -n "$t" && "$t" =~ ^[0-9]+$ ]] || continue
    if [[ "$t" -ge 85 ]]; then
      THERMAL_STATE="critical"
      SEVERITY=2
    elif [[ "$t" -ge 70 && "$THERMAL_STATE" == "ok" ]]; then
      THERMAL_STATE="warn"
      [[ $SEVERITY -lt 1 ]] && SEVERITY=1
    fi
  done

  [[ $SEVERITY -gt $GLOBAL_SEVERITY ]] && GLOBAL_SEVERITY=$SEVERITY

  if [[ "$JSON" -eq 1 ]]; then
    HOST="$HOST" BMC_STATE="$BMC_STATE" STORAGE_STATE="$STORAGE_STATE" THERMAL_STATE="$THERMAL_STATE" \
    SEVERITY="$SEVERITY" PRODUCT="${PRODUCT:-}" SERIAL="${SERIAL:-}" BIOS="${BIOS:-}" PVE="${PVE:-}" \
    UPTIME_S="${UPTIME_S:-0}" LOAD="${LOAD:-}" IPMI_DEV="${IPMI_DEV:-0}" IPMI_SI_FAIL="${IPMI_SI_FAIL:-0}" \
    IPMI_MC_OK="${IPMI_MC_OK:-0}" PERC_PRESENT="${PERC_PRESENT:-0}" PERCCLI="${PERCCLI:-}" \
    SMART_COUNT="${SMART_COUNT:-0}" SMART_LINES="${SMART_LINES:-}" CPU_PKG0="${CPU_PKG0:-}" CPU_PKG1="${CPU_PKG1:-}" \
    OUT_FILE="${TMPDIR_JSON}/${IDX}.json" \
    python3 - <<'PY'
import json, os
drives = []
for chunk in os.environ.get("SMART_LINES", "").split(";"):
    chunk = chunk.strip()
    if not chunk:
        continue
    parts = chunk.split("|")
    while len(parts) < 6:
        parts.append("")
    drives.append({
        "megaraid": parts[0],
        "model": parts[1],
        "serial": parts[2],
        "health": parts[3],
        "reallocated": int(parts[4]) if str(parts[4]).isdigit() else parts[4],
        "temp_c": int(parts[5]) if str(parts[5]).isdigit() else parts[5],
    })
pkg0 = os.environ.get("CPU_PKG0", "")
pkg1 = os.environ.get("CPU_PKG1", "")
payload = {
    "host": os.environ["HOST"],
    "ok": True,
    "product": os.environ.get("PRODUCT", ""),
    "serial": os.environ.get("SERIAL", ""),
    "bios": os.environ.get("BIOS", ""),
    "pve": os.environ.get("PVE", ""),
    "uptime_s": int(os.environ.get("UPTIME_S") or 0),
    "load": os.environ.get("LOAD", ""),
    "bmc": {
        "state": os.environ["BMC_STATE"],
        "ipmi_dev": int(os.environ.get("IPMI_DEV") or 0),
        "ipmi_si_fail": int(os.environ.get("IPMI_SI_FAIL") or 0),
        "mc_ok": int(os.environ.get("IPMI_MC_OK") or 0),
    },
    "storage": {
        "state": os.environ["STORAGE_STATE"],
        "perc_present": int(os.environ.get("PERC_PRESENT") or 0),
        "perccli": os.environ.get("PERCCLI") or None,
        "smart_count": int(os.environ.get("SMART_COUNT") or 0),
        "drives": drives,
    },
    "thermal": {
        "state": os.environ["THERMAL_STATE"],
        "package0_c": int(pkg0) if pkg0.isdigit() else None,
        "package1_c": int(pkg1) if pkg1.isdigit() else None,
    },
    "severity": int(os.environ["SEVERITY"]),
}
with open(os.environ["OUT_FILE"], "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False)
PY
    return 0
  fi

  echo "=== Hardware Proxmox (${USER}@${HOST}) ==="
  echo "Produit     : ${PRODUCT:-?}  SN=${SERIAL:-?}  BIOS=${BIOS:-?}  host=${HOSTNAME:-?}"
  echo "Proxmox     : ${PVE:-?}"
  echo "Uptime/load : ${UPTIME_S:-?}s  load ${LOAD:-?}"
  echo
  echo "--- BMC / iDRAC (in-band) ---"
  echo "État        : ${BMC_STATE}"
  echo "ipmi device : ${IPMI_DEV:-0}  si_fail=${IPMI_SI_FAIL:-0}  mc_ok=${IPMI_MC_OK:-0}"
  if [[ "${BMC_STATE}" == "dead" ]]; then
    echo "Note        : pas de régulation fans / PSU / KVM IP depuis l'OS."
  fi
  echo
  echo "--- Stockage PERC ---"
  echo "État        : ${STORAGE_STATE}  perc=${PERC_PRESENT:-0}  perccli=${PERCCLI:-absent}"
  if [[ -n "${SMART_LINES:-}" ]]; then
    printf '%-4s %-28s %-20s %-8s %6s %5s\n' ID MODEL SERIAL HEALTH REALOC TEMP
    local IFS=';'
    local chunk id model serial_d health realloc temp
    for chunk in ${SMART_LINES}; do
      [[ -z "$chunk" ]] && continue
      IFS='|' read -r id model serial_d health realloc temp <<<"$chunk"
      printf '%-4s %-28s %-20s %-8s %6s %5s\n' "$id" "${model:0:28}" "${serial_d:0:20}" "$health" "$realloc" "$temp"
    done
  fi
  echo
  echo "--- Thermique CPU (coretemp) ---"
  echo "État        : ${THERMAL_STATE}  pkg0=${CPU_PKG0:-?}C  pkg1=${CPU_PKG1:-?}C"
  echo
  echo "Sévérité    : ${SEVERITY} (0=ok 1=warn/degraded 2=critical)"
  echo "Doc         : packages/cortex/docs/runbook_r720_idrac_hs.md / timer lbg-team-ops-hw-job"
  echo
}

for HOST in "${HOSTS[@]}"; do
  diagnose_one "$HOST"
  IDX=$((IDX + 1))
done

if [[ "$JSON" -eq 1 ]]; then
  python3 - "$TMPDIR_JSON" <<'PY'
import json, sys
from pathlib import Path
d = Path(sys.argv[1])
items = []
for p in sorted(d.glob("*.json"), key=lambda x: int(x.stem)):
    items.append(json.loads(p.read_text(encoding="utf-8")))
sev = max((i.get("severity", 0) for i in items), default=0)
print(json.dumps({"hosts": items, "severity": sev, "count": len(items)}, ensure_ascii=False, indent=2))
PY
fi

exit "$GLOBAL_SEVERITY"
