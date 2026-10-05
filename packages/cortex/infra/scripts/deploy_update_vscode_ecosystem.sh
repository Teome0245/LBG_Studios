#!/usr/bin/env bash
# Déploie la capacité « MAJ VS Code (.143) » pour l’écosystème LBG
# (Compagnon + Orch .140 + linux_agent Omarchy) — reproductible sans Cursor.
#
# Étapes :
#   1) linux_agent .143 (préserve linux.env existant)
#   2) cortex orch/agents → .140 + restart lbg-orchestrator
#   3) Compagnon UI .100 (catalogue Agir)
#   4) smoke dry-run (jamais yay Réel)
#
# Usage (depuis LBG_Studios) :
#   bash packages/cortex/infra/scripts/deploy_update_vscode_ecosystem.sh
#   SKIP_COMPAGNON=1 bash ...   # si .100 indispo
#   SKIP_ORCH=1 bash ...        # agent only
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORTEX_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ROOT="$(cd "${CORTEX_ROOT}/../.." && pwd)"

echo "=== 1/4 Agent Omarchy .143 ==="
bash "${SCRIPT_DIR}/deploy_linux_agent_143.sh"

if [[ "${SKIP_ORCH:-0}" != "1" ]]; then
  echo "=== 2/4 Orch .140 (action_proposal update_vscode) ==="
  bash "${ROOT}/tools/deploy_cortex_140.sh" --full
  ssh -o BatchMode=yes "${LBG_VM_USER:-lbg}@${LBG_VM_HOST:-192.168.0.140}" \
    'sudo -n systemctl restart lbg-orchestrator.service && sleep 2 && systemctl is-active lbg-orchestrator.service'
else
  echo "SKIP orch (.140)"
fi

if [[ "${SKIP_COMPAGNON:-0}" != "1" ]]; then
  echo "=== 3/4 Compagnon .100 ==="
  bash "${SCRIPT_DIR}/deploy_compagnon_100.sh" --smoke || {
    echo "WARN  deploy_compagnon_100 a échoué — UI catalogue peut être stale" >&2
  }
else
  echo "SKIP compagnon (.100)"
fi

echo "=== 4/4 Smoke dry-run ==="
bash "${SCRIPT_DIR}/smoke_update_vscode_143.sh"

echo
echo "OK  écosystème prêt pour Agir : « mets à jour vscode sur omarchy »"
echo "    (confirm L2 · hors Cline critique · Réel = yay visual-studio-code-bin)"
