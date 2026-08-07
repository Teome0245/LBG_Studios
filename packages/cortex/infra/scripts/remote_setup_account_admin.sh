#!/usr/bin/env bash
# Exécuté sur la VM 245 par start_core3_account_admin_vm.sh.
# Surface PreCU isolée : pastille swgemu + DB locale uniquement.
set -euo pipefail

PRECU_HOST="${PRECU_HOST:-192.168.0.245}"
REMOTE_DIR="${REMOTE_DIR:-/home/lbg/tools/core3_account_admin}"
TOKEN="${TOKEN:-lbg-core3-admin-change-me}"
VM_HOST="${VM_HOST:-192.168.0.245}"
DB_PASS="${CORE3_DB_PASS:-123456}"

cd "${REMOTE_DIR}"
python3 -m pip install --user -q -r requirements.txt 2>/dev/null || pip3 install --user -r requirements.txt -q

sudo tee /etc/lbg-core3-account-admin.env >/dev/null <<ENV
CORE3_DB_PASS=${DB_PASS}
CORE3_ADMIN_TOKEN=${TOKEN}
CORE3_LOCAL_SERVER_ID=precu
CORE3_PRIME_DB_ENABLED=0
CORE3_PRECU_CLIENT_IP=${PRECU_HOST}
ENV
sudo cp /tmp/lbg-core3-account-admin.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable lbg-core3-account-admin.service
sudo systemctl restart lbg-core3-account-admin.service
sleep 1
systemctl is-active lbg-core3-account-admin.service
echo "UI PreCU : http://${VM_HOST}:8792/ (swgemu seul)"
echo "Token : ${TOKEN}"
