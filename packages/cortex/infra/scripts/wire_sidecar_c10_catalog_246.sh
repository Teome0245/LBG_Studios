#!/usr/bin/env bash
# Wire C10/C11 catalog sur sidecar Prime :8791 (agent_catalog.http_get_dispatch).
# Usage: bash infra/scripts/wire_sidecar_c10_catalog_246.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HOST="${LBG_PRIME_HOST:-192.168.0.246}"
SRC="$ROOT/agents/src/lbg_agents/agent_catalog.py"
POI="$ROOT/../prime-client/assets/maps/scrapaltai_pois.json"

[[ -f "$SRC" ]] || { echo "missing $SRC" >&2; exit 1; }
[[ -f "$POI" ]] || { echo "missing $POI" >&2; exit 1; }

scp -o BatchMode=yes -o ConnectTimeout=10 "$SRC" "lbg@${HOST}:/tmp/agent_catalog.py"
scp -o BatchMode=yes -o ConnectTimeout=10 "$POI" "lbg@${HOST}:/tmp/scrapaltai_pois.json"

ssh -o BatchMode=yes -o ConnectTimeout=10 "lbg@${HOST}" bash -s <<'REMOTE'
set -euo pipefail
sudo install -m 644 -o lbg -g lbg /tmp/agent_catalog.py /opt/LBG_IA_MMO/agents/src/lbg_agents/agent_catalog.py
sudo mkdir -p /opt/LBG_IA_MMO/content/maps
sudo install -m 644 -o lbg -g lbg /tmp/scrapaltai_pois.json /opt/LBG_IA_MMO/content/maps/scrapaltai_pois.json
sudo mkdir -p /etc/systemd/system/lbg-core3-ia-sidecar.service.d
sudo tee /etc/systemd/system/lbg-core3-ia-sidecar.service.d/c10-catalog.conf >/dev/null <<EOF
[Service]
Environment=LBG_M10_CATALOG_PATH=/opt/LBG_IA_MMO/content/core3/m10_skills_catalog.json
Environment=LBG_POI_CATALOG_PATH=/opt/LBG_IA_MMO/content/maps/scrapaltai_pois.json
EOF
# Inject routes if absent (idempotent)
PY=/opt/LBG_IA_MMO/tools/core3_ia_sidecar/core3_ia_sidecar.py
if ! grep -q 'http_get_dispatch' "$PY"; then
  echo "ERROR: $PY n'a pas le bloc http_get_dispatch — rejouer le patch sidecar (voir design_c10_c11_catalog_tick.md)." >&2
  exit 2
fi
sudo systemctl daemon-reload
sudo systemctl restart lbg-core3-ia-sidecar
sleep 2
systemctl is-active lbg-core3-ia-sidecar
curl -sf "http://127.0.0.1:8791/catalog?type=skills" | head -c 120
echo
REMOTE

echo "OK wire C10 on ${HOST}:8791"
