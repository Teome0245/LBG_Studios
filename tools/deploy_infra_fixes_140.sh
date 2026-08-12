#!/usr/bin/env bash
# Déploie correctifs infra : Ollama audit + pont WSL + re-smoke.
#
# Depuis le monorepo (WSL poste dev) :
#   bash tools/deploy_infra_fixes_140.sh
#
# Flux : rsync code → patch /etc/lbg-ia-mmo.env → pull gemma4:e2b sur 111 → restart → smoke
# Note : .140 n'est pas un clone git (/opt/LBG_IA_MMO = rsync). Pour GitHub :
#   1) commit + push depuis ce poste
#   2) bash tools/deploy_infra_fixes_140.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CORTEX="${ROOT}/packages/cortex"
VM_HOST="${LBG_VM_HOST:-192.168.0.140}"
VM_USER="${LBG_VM_USER:-lbg}"
REMOTE_DIR="${LBG_REMOTE_DIR:-/opt/LBG_IA_MMO}"
LIGHT_OLLAMA="${LBG_OLLAMA_LIGHT_URL:-http://192.168.0.111:11434}"
PULL_MODEL="${LBG_OLLAMA_PULL_MODEL:-gemma4:e2b}"

SSH_OPTS=(-o BatchMode=yes -o ConnectTimeout=8)
[[ -n "${LBG_SSH_IDENTITY:-}" ]] && SSH_OPTS+=(-i "${LBG_SSH_IDENTITY}")

echo "=== 1/5 deploy WSL bridge (orchestrator + scripts) ==="
bash "${ROOT}/tools/deploy_wsl_bridge_140.sh" --no-env

echo ""
echo "=== 2/5 patch Ollama env sur .140 ==="
SNIPPET="$(mktemp)"
trap 'rm -f "${SNIPPET}"' EXIT
cat > "${SNIPPET}" <<'EOF'
# --- Ollama audit fix (deploy_infra_fixes_140.sh) ---
LBG_COMPANION_LLM_MODEL="gemma4:e2b"
LBG_REASON_MODEL_FAST="gemma4:e2b"
LBG_REASON_LIGHT_BASE_URL="http://192.168.0.111:11434"
LBG_REASON_LIGHT_FAILOVER_HEAVY="1"
EOF
REMOTE_SNIP="ollama-audit-snippet.$$"
scp "${SSH_OPTS[@]}" "${SNIPPET}" "${VM_USER}@${VM_HOST}:/tmp/${REMOTE_SNIP}"
ssh "${SSH_OPTS[@]}" "${VM_USER}@${VM_HOST}" "bash -s" <<REMOTE
set -euo pipefail
ENV_FILE="/etc/lbg-ia-mmo.env"
TMP="\$(mktemp)"
sudo -n grep -Ev '^(LBG_COMPANION_LLM_MODEL=|LBG_REASON_MODEL_FAST=|LBG_REASON_LIGHT_BASE_URL=|LBG_REASON_LIGHT_FAILOVER_HEAVY=)' "\${ENV_FILE}" > "\${TMP}" || true
cat "/tmp/${REMOTE_SNIP}" >> "\${TMP}"
sudo -n install -m 640 -o root -g lbg "\${TMP}" "\${ENV_FILE}"
rm -f "\${TMP}" "/tmp/${REMOTE_SNIP}"
grep -E 'LBG_COMPANION_LLM_MODEL|LBG_REASON_MODEL_FAST|LBG_REASON_LIGHT' "\${ENV_FILE}" | head -5
REMOTE

echo ""
echo "=== 3/5 pull ${PULL_MODEL} sur 111-light ==="
bash "${CORTEX}/infra/scripts/pull_ollama_model_lan.sh" "${PULL_MODEL}" "${LIGHT_OLLAMA}" || {
  echo "WARN: pull 111 échoué — failover heavy reste actif" >&2
}

echo ""
echo "=== 4/5 restart orchestrateur + audit live ==="
ssh "${SSH_OPTS[@]}" "${VM_USER}@${VM_HOST}" \
  "sudo -n systemctl restart lbg-orchestrator.service && sleep 3 && \
   set -a && . /etc/lbg-ia-mmo.env && set +a && \
   cd ${REMOTE_DIR}/orchestrator && PYTHONPATH=. ${REMOTE_DIR}/.venv/bin/python3 -c \"
from team.ollama_audit import audit_ollama_lan
import json
o=audit_ollama_lan()
print('audit ok', o.get('ok'))
print('blocking', o.get('blocking_gaps'))
print('warnings', o.get('warnings'))
\""

echo ""
echo "=== 5/5 re-smoke pont WSL ==="
bash "${CORTEX}/infra/scripts/lbg_wsl_executor.sh" --enqueue diag_godot_supervisor "Re-smoke pont WSL post-fix"
bash "${CORTEX}/infra/scripts/lbg_wsl_executor.sh" --once || true

echo ""
echo "Done — infra fixes déployés sur ${VM_HOST}"
echo "GitHub : commit + push depuis ce poste, puis relancer ce script pour propager."
