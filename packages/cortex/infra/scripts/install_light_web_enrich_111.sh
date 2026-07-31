#!/usr/bin/env bash
# Installe light_web_enrich sur CT 111 (Ollama light).
# Usage (depuis le monorepo) :
#   bash infra/scripts/install_light_web_enrich_111.sh
#
# Prérequis : root@192.168.0.200 (Proxmox NUC) + pct 111 running.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PVE="${LBG_PVE_NUC:-192.168.0.200}"
CTID="${LBG_OLLAMA_LIGHT_CT:-111}"
REMOTE_DIR="/opt/lbg-light-web-enrich"

echo "=== sync → ${PVE} CT ${CTID}:${REMOTE_DIR} ==="
ssh -o BatchMode=yes "root@${PVE}" "pct exec ${CTID} -- mkdir -p ${REMOTE_DIR}"
rsync -az -e "ssh -o BatchMode=yes" \
  --exclude '__pycache__/' --exclude '.venv/' \
  "${ROOT}/services/light_web_enrich/" \
  "root@${PVE}:/tmp/lbg-light-web-enrich/"
scp -o BatchMode=yes \
  "${ROOT}/infra/systemd/lbg-light-web-enrich.service" \
  "root@${PVE}:/tmp/lbg-light-web-enrich.service"

ssh -o BatchMode=yes "root@${PVE}" "pct push ${CTID} /tmp/lbg-light-web-enrich/app.py ${REMOTE_DIR}/app.py" 2>/dev/null || true

ssh -o BatchMode=yes "root@${PVE}" bash -s <<EOF
set -euo pipefail
pct exec ${CTID} -- bash -lc '
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a
mkdir -p ${REMOTE_DIR}
'
# copy tree via tar over pct exec
tar czf /tmp/lbg-lwe.tgz -C /tmp/lbg-light-web-enrich .
pct exec ${CTID} -- bash -lc "mkdir -p ${REMOTE_DIR} && tar xzf - -C ${REMOTE_DIR}" < /tmp/lbg-lwe.tgz
pct push ${CTID} /tmp/lbg-light-web-enrich.service /etc/systemd/system/lbg-light-web-enrich.service
pct exec ${CTID} -- bash -lc '
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a
apt-get update -qq
apt-get install -y -qq python3-venv python3-pip
cd ${REMOTE_DIR}
python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
systemctl daemon-reload
systemctl enable --now lbg-light-web-enrich.service
systemctl restart lbg-light-web-enrich.service
sleep 2
systemctl is-active lbg-light-web-enrich
curl -sf http://127.0.0.1:8095/healthz
echo
'
EOF

echo ""
echo "OK — http://192.168.0.111:8095/healthz"
echo "Chat enrichi : POST http://192.168.0.111:8095/v1/chat"
