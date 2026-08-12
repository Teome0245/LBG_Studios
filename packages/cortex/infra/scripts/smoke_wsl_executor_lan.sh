#!/usr/bin/env bash
# Smoke pont WSL executor — GET /v1/team/wsl/health sur orchestrateur LAN.
#
# Usage :
#   bash infra/scripts/smoke_wsl_executor_lan.sh
#   bash infra/scripts/smoke_wsl_executor_lan.sh http://192.168.0.140:8010
#
# Codes sortie :
#   0 — endpoint OK ; enabled=true
#   1 — endpoint injoignable ou JSON invalide
#   2 — endpoint OK mais enabled=false ou token requis sans header
set -euo pipefail

BASE="${1:-${LBG_ORCHESTRATOR_URL:-http://192.168.0.140:8010}}"
BASE="${BASE%/}"
URL="${BASE}/v1/team/wsl/health"

body="$(mktemp)"
trap 'rm -f "${body}"' EXIT

hdr=()
if [[ -n "${LBG_WSL_EXECUTOR_TOKEN:-}" ]]; then
  hdr=(-H "X-LBG-WSL-TOKEN: ${LBG_WSL_EXECUTOR_TOKEN}")
fi

code="$(curl -sS -o "${body}" -w "%{http_code}" --connect-timeout 5 --max-time 15 "${hdr[@]}" "${URL}" 2>/dev/null)" || {
  echo "KO  wsl/health  curl_fail  ${URL}"
  exit 1
}

if [[ "${code}" == "401" ]]; then
  echo "KO  wsl/health  HTTP 401 — définir LBG_WSL_EXECUTOR_TOKEN pour le smoke"
  exit 2
fi

if [[ "${code}" != "200" ]]; then
  echo "KO  wsl/health  HTTP ${code}  ${URL}"
  head -c 300 "${body}"; echo
  exit 1
fi

python3 - "${body}" <<'PY'
import json, sys
path = sys.argv[1]
with open(path, encoding="utf-8") as f:
    d = json.load(f)
enabled = bool(d.get("enabled"))
skills = d.get("skills_allowlist") or []
pending = d.get("pending")
print(
    f"OK  wsl/health  enabled={enabled} skills={len(skills)} pending={pending} "
    f"token_required={bool(d.get('token_required'))}"
)
if not enabled:
    print("WARN  enabled=false")
    sys.exit(2)
if "diag_godot_supervisor" not in skills:
    print("WARN  diag_godot_supervisor absent de l'allowlist")
    sys.exit(2)
PY
