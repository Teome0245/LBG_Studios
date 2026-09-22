#!/usr/bin/env bash
# Installe laya-serve (System One) sur le nœud light .111 — port 8097.
#
# Usage :
#   bash infra/scripts/install_laya_serve_111.sh
#   bash infra/scripts/install_laya_serve_111.sh 192.168.0.111
#   bash infra/scripts/install_laya_serve_111.sh 192.168.0.111 --fake     # sans poids (CI / smoke API)
#   bash infra/scripts/install_laya_serve_111.sh 192.168.0.111 --enable-orch  # active flags sur .140
#
# Endpoints : GET /healthz · GET /v1/models · POST /v1/systemone
# Doc : packages/cortex/docs/laya_system_one.md
#
set -euo pipefail

HOST="${1:-192.168.0.111}"
shift || true
MODE=laya
ENABLE_ORCH=0
for arg in "$@"; do
  case "$arg" in
    --fake) MODE=fake ;;
    --enable-orch) ENABLE_ORCH=1 ;;
    *)
      echo "arg inconnu: $arg" >&2
      exit 2
      ;;
  esac
done

REMOTE_DIR=/opt/lbg-laya-serve
ORCH_HOST="${LBG_ORCH_HOST:-${LBG_CORE_VM_HOST:-192.168.0.140}}"
ORCH_USER="${LBG_ORCH_USER:-${LBG_CORE_VM_USER:-lbg}}"
ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
UNIT_SRC="${ROOT_DIR}/infra/systemd/lbg-laya-serve.service"

SSH=(ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=8)
SCP=(scp -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=8)

echo "==> Install laya-serve (${MODE}) → root@${HOST}:${REMOTE_DIR} :8097"

"${SSH[@]}" "root@${HOST}" "mkdir -p ${REMOTE_DIR}/hf-cache"
"${SCP[@]}" "${UNIT_SRC}" "root@${HOST}:/tmp/lbg-laya-serve.service"

"${SSH[@]}" "root@${HOST}" bash -s <<REMOTE
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a
cd ${REMOTE_DIR}

if ! command -v python3 >/dev/null; then
  apt-get update -qq
  apt-get install -y -qq python3-venv python3-pip >/dev/null
fi

python3 -m venv .venv
. .venv/bin/activate
pip install -q -U pip wheel
# fake = API seule ; laya = torch + poids HF (long)
if [[ "${MODE}" == "fake" ]]; then
  pip install -q "laya-serve==0.1.0"
else
  pip install -q "laya-serve[inference]==0.1.0"
fi

cat >/etc/lbg-laya-serve.env <<ENV
# Généré par install_laya_serve_111.sh — ${MODE}
USE_TF=0
HF_HOME=${REMOTE_DIR}/hf-cache
TRANSFORMERS_CACHE=${REMOTE_DIR}/hf-cache
LAYA_SERVE_BACKEND=${MODE}
LAYA_SERVE_PRELOAD=$([ "${MODE}" = "laya" ] && echo true || echo false)
LAYA_SERVE_DEVICE=cpu
LAYA_SERVE_SERVING_MODEL=laya-english
LAYA_SERVE_MAX_LOADED=2
ENV

cp /tmp/lbg-laya-serve.service /etc/systemd/system/lbg-laya-serve.service
# Aligner le backend du unit avec --fake si besoin
if [[ "${MODE}" == "fake" ]]; then
  sed -i 's/^Environment=LAYA_SERVE_BACKEND=.*/Environment=LAYA_SERVE_BACKEND=fake/' /etc/systemd/system/lbg-laya-serve.service
  sed -i 's/^Environment=LAYA_SERVE_PRELOAD=.*/Environment=LAYA_SERVE_PRELOAD=false/' /etc/systemd/system/lbg-laya-serve.service
fi

systemctl daemon-reload
systemctl enable --now lbg-laya-serve.service
systemctl --no-pager -l status lbg-laya-serve.service | head -20

echo "==> healthz"
for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -sf --max-time 3 http://127.0.0.1:8097/healthz; then
    echo
    break
  fi
  sleep 3
  if [[ \$i -eq 10 ]]; then
    echo "healthz timeout — journalctl -u lbg-laya-serve -n 80" >&2
    journalctl -u lbg-laya-serve -n 40 --no-pager || true
    exit 1
  fi
done

echo "==> models"
curl -sf http://127.0.0.1:8097/v1/models | head -c 500
echo

echo "==> systemone smoke"
curl -sf -X POST http://127.0.0.1:8097/v1/systemone \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "laya-latest",
    "state": {"text": "vérifie healthz backend et orchestrateur"},
    "questions": {
      "intent": {
        "type": "choice",
        "instructions": "Intention ?",
        "criteria": {
          "devops_probe": "infra, healthz, diagnostic",
          "npc_dialogue": "parler PNJ",
          "unknown": "ambigu"
        }
      }
    }
  }' | head -c 800
echo
REMOTE

echo "==> Public: http://${HOST}:8097/healthz"

if [[ "${ENABLE_ORCH}" -eq 1 ]]; then
  echo "==> Active flags orchestrateur sur ${ORCH_USER}@${ORCH_HOST}"
  "${SSH[@]}" "${ORCH_USER}@${ORCH_HOST}" bash -s <<ORCH
set -euo pipefail
ENVF=/etc/lbg-ia-mmo.env
HOST_LAYA="${HOST}"
sudo touch "\$ENVF"
if sudo grep -q '^LBG_ORCHESTRATOR_INTENT_LAYA=' "\$ENVF" 2>/dev/null; then
  sudo sed -i 's|^LBG_ORCHESTRATOR_INTENT_LAYA=.*|LBG_ORCHESTRATOR_INTENT_LAYA=1|' "\$ENVF"
else
  echo 'LBG_ORCHESTRATOR_INTENT_LAYA=1' | sudo tee -a "\$ENVF" >/dev/null
fi
if sudo grep -q '^LBG_ORCHESTRATOR_INTENT_LAYA_BASE_URL=' "\$ENVF" 2>/dev/null; then
  sudo sed -i "s|^LBG_ORCHESTRATOR_INTENT_LAYA_BASE_URL=.*|LBG_ORCHESTRATOR_INTENT_LAYA_BASE_URL=http://\${HOST_LAYA}:8097|" "\$ENVF"
else
  echo "LBG_ORCHESTRATOR_INTENT_LAYA_BASE_URL=http://\${HOST_LAYA}:8097" | sudo tee -a "\$ENVF" >/dev/null
fi
if sudo grep -q '^LBG_ORCHESTRATOR_INTENT_LAYA_MODEL=' "\$ENVF" 2>/dev/null; then
  sudo sed -i 's|^LBG_ORCHESTRATOR_INTENT_LAYA_MODEL=.*|LBG_ORCHESTRATOR_INTENT_LAYA_MODEL=laya-latest|' "\$ENVF"
else
  echo 'LBG_ORCHESTRATOR_INTENT_LAYA_MODEL=laya-latest' | sudo tee -a "\$ENVF" >/dev/null
fi
sudo systemctl restart lbg-orchestrator
systemctl is-active lbg-orchestrator
grep -E '^LBG_ORCHESTRATOR_INTENT_LAYA' "\$ENVF" || sudo grep -E '^LBG_ORCHESTRATOR_INTENT_LAYA' "\$ENVF"
ORCH
  echo "==> Orchestrateur pointe vers http://${HOST}:8097"
fi

echo "OK"
