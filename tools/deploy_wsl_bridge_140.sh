#!/usr/bin/env bash
# Déploie le pont Cloud ↔ WSL (orchestrateur + scripts) sur VM core 140.
#
# - rsync orchestrator (wsl_executor + routes /v1/team/wsl/*)
# - rsync infra/scripts (diag_godot_supervisor_wsl.sh, lbg_wsl_executor.sh)
# - patch /etc/lbg-ia-mmo.env (LBG_WSL_EXECUTOR_*)
# - restart lbg-orchestrator + smoke GET /v1/team/wsl/health
#
# Usage :
#   bash tools/deploy_wsl_bridge_140.sh
#   LBG_WSL_EXECUTOR_TOKEN='secret' bash tools/deploy_wsl_bridge_140.sh
#   bash tools/deploy_wsl_bridge_140.sh --no-env   # rsync + restart seulement
#
# Options :
#   LBG_VM_HOST              défaut 192.168.0.140
#   LBG_VM_USER              défaut lbg
#   LBG_REMOTE_DIR           défaut /opt/LBG_IA_MMO
#   LBG_WSL_EXECUTOR_ENABLED défaut 1
#   LBG_WSL_SKIP_SMOKE=1     ne pas curl health après deploy
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CORTEX="${ROOT}/packages/cortex"
PATCH_ENV=1
[[ "${1:-}" == "--no-env" ]] && PATCH_ENV=0

VM_HOST="${LBG_VM_HOST:-192.168.0.140}"
VM_USER="${LBG_VM_USER:-lbg}"
REMOTE_DIR="${LBG_REMOTE_DIR:-/opt/LBG_IA_MMO}"
ENABLED="${LBG_WSL_EXECUTOR_ENABLED:-1}"

SSH_OPTS=(
  -o BatchMode=yes
  -o ConnectTimeout=8
  -o ControlMaster=auto
  -o ControlPersist=5m
  -o "ControlPath=/tmp/lbg_wsl_%r@%h:%p"
)
if [[ -n "${LBG_SSH_IDENTITY:-}" ]]; then
  SSH_OPTS+=(-i "${LBG_SSH_IDENTITY}")
fi

read_wsl_token() {
  if [[ -n "${LBG_WSL_EXECUTOR_TOKEN:-}" ]]; then
    return 0
  fi
  local env_file="${CORTEX}/infra/secrets/lbg.env"
  if [[ -f "${env_file}" ]]; then
    local line
    line="$(grep -E '^LBG_WSL_EXECUTOR_TOKEN=' "${env_file}" | tail -1 || true)"
    if [[ -n "${line}" ]]; then
      LBG_WSL_EXECUTOR_TOKEN="${line#LBG_WSL_EXECUTOR_TOKEN=}"
      LBG_WSL_EXECUTOR_TOKEN="${LBG_WSL_EXECUTOR_TOKEN%\"}"
      LBG_WSL_EXECUTOR_TOKEN="${LBG_WSL_EXECUTOR_TOKEN#\"}"
      LBG_WSL_EXECUTOR_TOKEN="${LBG_WSL_EXECUTOR_TOKEN//\"/}"
    fi
  fi
}

read_wsl_token

echo "=== Deploy pont WSL → ${VM_USER}@${VM_HOST}:${REMOTE_DIR} ==="

echo "=== rsync orchestrator ==="
rsync -az --delete \
  --exclude '__pycache__/' --exclude '.venv/' --exclude '*.pyc' --exclude 'tests/' \
  -e "ssh ${SSH_OPTS[*]}" \
  "${CORTEX}/orchestrator/" \
  "${VM_USER}@${VM_HOST}:${REMOTE_DIR}/orchestrator/"

echo "=== rsync infra/scripts (wsl + diag) ==="
ssh "${SSH_OPTS[@]}" "${VM_USER}@${VM_HOST}" "mkdir -p '${REMOTE_DIR}/infra/scripts'"
rsync -az \
  -e "ssh ${SSH_OPTS[*]}" \
  "${CORTEX}/infra/scripts/diag_godot_supervisor_wsl.sh" \
  "${CORTEX}/infra/scripts/lbg_wsl_executor.sh" \
  "${CORTEX}/infra/scripts/smoke_wsl_executor_lan.sh" \
  "${VM_USER}@${VM_HOST}:${REMOTE_DIR}/infra/scripts/"

ssh "${SSH_OPTS[@]}" "${VM_USER}@${VM_HOST}" "chmod +x '${REMOTE_DIR}/infra/scripts/diag_godot_supervisor_wsl.sh' '${REMOTE_DIR}/infra/scripts/lbg_wsl_executor.sh' '${REMOTE_DIR}/infra/scripts/smoke_wsl_executor_lan.sh'"

if [[ "${PATCH_ENV}" -eq 1 ]]; then
  SNIPPET="$(mktemp)"
  trap 'rm -f "${SNIPPET}"' EXIT
  cat > "${SNIPPET}" <<EOF
# --- Pont WSL executor (sync tools/deploy_wsl_bridge_140.sh) ---
LBG_WSL_EXECUTOR_ENABLED="${ENABLED}"
LBG_WSL_EXECUTOR_TOKEN="${LBG_WSL_EXECUTOR_TOKEN:-}"
EOF
  REMOTE_SNIP="wsl-bridge-snippet.$$"
  scp "${SSH_OPTS[@]}" "${SNIPPET}" "${VM_USER}@${VM_HOST}:/tmp/${REMOTE_SNIP}"
  ssh "${SSH_OPTS[@]}" "${VM_USER}@${VM_HOST}" "bash -s" <<REMOTE
set -euo pipefail
ENV_FILE="/etc/lbg-ia-mmo.env"
TMP="\$(mktemp)"
if sudo -n test -f "\${ENV_FILE}"; then
  sudo -n grep -Ev '^(LBG_WSL_EXECUTOR_)' "\${ENV_FILE}" > "\${TMP}" || true
else
  : > "\${TMP}"
fi
cat "/tmp/${REMOTE_SNIP}" >> "\${TMP}"
sudo -n install -m 640 -o root -g lbg "\${TMP}" "\${ENV_FILE}"
rm -f "\${TMP}" "/tmp/${REMOTE_SNIP}"
echo "OK: patched \${ENV_FILE} (WSL bridge block)"
REMOTE
fi

echo "=== restart lbg-orchestrator ==="
ssh "${SSH_OPTS[@]}" "${VM_USER}@${VM_HOST}" \
  "sudo -n systemctl restart lbg-orchestrator.service && sleep 2 && sudo -n systemctl is-active lbg-orchestrator.service"

echo "=== attente healthz orchestrateur ==="
for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -sf --connect-timeout 3 --max-time 5 "http://${VM_HOST}:8010/healthz" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if [[ "${LBG_WSL_SKIP_SMOKE:-0}" != "1" ]]; then
  echo "=== smoke GET /v1/team/wsl/health ==="
  export LBG_WSL_EXECUTOR_TOKEN="${LBG_WSL_EXECUTOR_TOKEN:-}"
  if bash "${CORTEX}/infra/scripts/smoke_wsl_executor_lan.sh" "http://${VM_HOST}:8010"; then
    echo "OK smoke wsl/health"
  else
    rc=$?
    echo "WARN smoke wsl/health exit=${rc} — journalctl -u lbg-orchestrator sur 140" >&2
    exit "${rc}"
  fi
fi

echo ""
echo "Done — pont WSL sur ${VM_HOST}"
echo "  WSL : export LBG_WSL_EXECUTOR_TOKEN=\"<même secret si défini>\""
echo "        bash packages/cortex/infra/scripts/lbg_wsl_executor.sh --loop"
echo "  Doc : packages/cortex/docs/pont_cloud_local.md"
