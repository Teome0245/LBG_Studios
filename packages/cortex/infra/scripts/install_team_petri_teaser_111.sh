#!/usr/bin/env bash
# Installe le teaser bureau Team sur 111 (port 8096).
set -euo pipefail

HOST="${1:-192.168.0.111}"
REMOTE_DIR=/opt/lbg-team-petri-teaser
SRC_DIR="$(cd "$(dirname "$0")/../.." && pwd)/services/team_petri_teaser"

echo "==> Sync teaser → ${HOST}:${REMOTE_DIR}"
SSH=(ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new)
"${SSH[@]}" "root@${HOST}" "mkdir -p ${REMOTE_DIR}"
tar -C "${SRC_DIR}" -czf - . | "${SSH[@]}" "root@${HOST}" "tar -C ${REMOTE_DIR} -xzf -"

"${SSH[@]}" "root@${HOST}" bash -s <<'REMOTE'
set -euo pipefail
cd /opt/lbg-team-petri-teaser
export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a
apt-get install -y -qq python3-venv python3-pip >/dev/null
python3 -m venv .venv
. .venv/bin/activate
pip install -q -r requirements.txt

cat >/etc/systemd/system/lbg-team-petri-teaser.service <<'UNIT'
[Unit]
Description=LBG Team Petri teaser (office UI mock)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/lbg-team-petri-teaser
Environment=LBG_PETRI_MOCK=1
Environment=LBG_PETRI_TICK_SEC=4
ExecStart=/opt/lbg-team-petri-teaser/.venv/bin/uvicorn app:app --host 0.0.0.0 --port 8096
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now lbg-team-petri-teaser.service
systemctl is-active lbg-team-petri-teaser.service
curl -sf http://127.0.0.1:8096/healthz
echo
REMOTE

echo "==> Teaser: http://${HOST}:8096/"
