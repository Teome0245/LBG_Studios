#!/usr/bin/env bash
# Smoke Cursor Cloud Agent — GET /v1/team/cursor/health sur orchestrateur LAN.
#
# Usage :
#   bash infra/scripts/smoke_cursor_agent_lan.sh
#   bash infra/scripts/smoke_cursor_agent_lan.sh http://192.168.0.140:8010
#
# Codes de sortie :
#   0 — endpoint OK ; ready=true (clé + sdk + enabled)
#   1 — endpoint injoignable ou JSON invalide
#   2 — endpoint OK mais ready=false (config incomplète — attendu avant sync clé)
set -euo pipefail

BASE="${1:-${LBG_ORCHESTRATOR_URL:-http://192.168.0.140:8010}}"
BASE="${BASE%/}"
URL="${BASE}/v1/team/cursor/health"

body="$(mktemp)"
trap 'rm -f "${body}"' EXIT

code="$(curl -sS -o "${body}" -w "%{http_code}" --connect-timeout 5 --max-time 15 "${URL}" 2>/dev/null)" || {
  echo "KO  cursor/health  curl_fail  ${URL}"
  exit 1
}

if [[ "${code}" != "200" ]]; then
  echo "KO  cursor/health  HTTP ${code}  ${URL}"
  head -c 300 "${body}"; echo
  exit 1
fi

python3 - "${body}" <<'PY'
import json, sys
path = sys.argv[1]
with open(path, encoding="utf-8") as f:
    d = json.load(f)
enabled = bool(d.get("enabled"))
key_ok = bool(d.get("api_key_configured"))
sdk_ok = bool(d.get("sdk_installed"))
ready = bool(d.get("ready"))
repos = d.get("repos_allowlist") or []
print(
    f"OK  cursor/health  enabled={enabled} api_key={key_ok} sdk={sdk_ok} "
    f"ready={ready} repos={len(repos)}"
)
if not ready:
    missing = []
    if not enabled:
        missing.append("LBG_CURSOR_AGENT_ENABLED")
    if not key_ok:
        missing.append("CURSOR_API_KEY")
    if not sdk_ok:
        missing.append("cursor-sdk")
    if missing:
        print(f"WARN  ready=false — manque: {', '.join(missing)}")
    sys.exit(2)
PY
