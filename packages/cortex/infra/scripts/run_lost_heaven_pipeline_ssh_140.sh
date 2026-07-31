#!/usr/bin/env bash
# Sync scripts/workflow LH vers 140 et lance pipeline + Element.
set -euo pipefail
LOCAL_MMORPG="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VM_HOST="${LBG_CORE_VM_HOST:-192.168.0.140}"
VM_USER="${LBG_CORE_VM_USER:-lbg}"
REMOTE_MMORPG="${LBG_REMOTE_MMORPG_ROOT:-/opt/LBG_IA_MMO}"
SSH=(ssh -o ConnectTimeout=10 "${VM_USER}@${VM_HOST}")

echo "=== rsync LH spawn → ${VM_USER}@${VM_HOST}:${REMOTE_MMORPG} ==="
rsync -az \
  "${LOCAL_MMORPG}/infra/scripts/spawn_team_lost_heaven_map.py" \
  "${LOCAL_MMORPG}/infra/scripts/spawn_team_lost_heaven_map.sh" \
  "${LOCAL_MMORPG}/infra/scripts/spawn_team_lost_heaven_map_pipeline.sh" \
  "${LOCAL_MMORPG}/infra/scripts/spawn_team_lost_heaven_full_pipeline_140.sh" \
  "${LOCAL_MMORPG}/infra/scripts/spawn_team_lost_heaven_code.py" \
  "${LOCAL_MMORPG}/infra/scripts/spawn_team_lost_heaven_code.sh" \
  "${LOCAL_MMORPG}/infra/scripts/team_spawn_phases.py" \
  "${VM_USER}@${VM_HOST}:${REMOTE_MMORPG}/infra/scripts/"

rsync -az \
  "${LOCAL_MMORPG}/orchestrator/team/lost_heaven_code_workflow.py" \
  "${LOCAL_MMORPG}/orchestrator/team/godot_dev_workflow.py" \
  "${VM_USER}@${VM_HOST}:${REMOTE_MMORPG}/orchestrator/team/"

"${SSH[@]}" "chmod +x ${REMOTE_MMORPG}/infra/scripts/spawn_team_lost_heaven_*.sh ${REMOTE_MMORPG}/infra/scripts/spawn_team_lost_heaven_full_pipeline_140.sh 2>/dev/null || true"

echo "=== restart orchestrateur 140 (charge lost_heaven_code_workflow) ==="
"${SSH[@]}" "sudo systemctl restart lbg-orchestrator.service && sleep 3 && curl -sfS --max-time 5 http://127.0.0.1:8010/healthz"

LOCAL_PRIME_DOCS="${LBG_LOCAL_PRIME_DOCS:-/home/sdesh/projects/new_mmo/prime-client/docs}"
REMOTE_PRIME_DOCS="${LBG_REMOTE_PRIME_DOCS:-/opt/new_mmo/prime-client/docs}"
SYNC_DOCS_BACK="${LBG_LH_SYNC_DOCS_BACK:-1}"

echo "=== pipeline sur 140 (orchestrateur local + matrix_notify) ==="
"${SSH[@]}" "set -a; [ -f /etc/lbg-ia-mmo.env ] && . /etc/lbg-ia-mmo.env; [ -f /etc/lbg-project-03.env ] && . /etc/lbg-project-03.env; set +a; \
  export LBG_ORCHESTRATOR_URL=http://127.0.0.1:8010; \
  export LBG_TEAM_SPAWN_STATE=/var/lib/lbg/spawn_lh_state.json; \
  export LBG_PRIME_CLIENT_ROOT=\${LBG_PRIME_CLIENT_ROOT:-/opt/new_mmo/prime-client}; \
  export LBG_PROJECT_03_ROOT=\${LBG_PROJECT_03_ROOT:-/opt/LBG_Project_03}; \
  sudo mkdir -p /var/lib/lbg && sudo chown \$(whoami) /var/lib/lbg 2>/dev/null || true; \
  bash ${REMOTE_MMORPG}/infra/scripts/spawn_team_lost_heaven_full_pipeline_140.sh"

if [[ "${SYNC_DOCS_BACK}" == "1" ]]; then
  echo "=== rsync docs CODE 140 → WSL (${LOCAL_PRIME_DOCS}) ==="
  mkdir -p "${LOCAL_PRIME_DOCS}"
  BACKUP="${LOCAL_PRIME_DOCS}/.lh_sync_backup_$(date +%Y%m%d_%H%M%S)"
  if compgen -G "${LOCAL_PRIME_DOCS}/*.md" >/dev/null; then
    mkdir -p "${BACKUP}"
    cp -a "${LOCAL_PRIME_DOCS}"/*.md "${BACKUP}/" 2>/dev/null || true
    echo "Backup local → ${BACKUP}"
  fi
  rsync -az --itemize-changes \
    "${VM_USER}@${VM_HOST}:${REMOTE_PRIME_DOCS}/" \
    "${LOCAL_PRIME_DOCS}/"
  echo "OK sync docs → ${LOCAL_PRIME_DOCS}"
else
  echo "Skip sync docs (LBG_LH_SYNC_DOCS_BACK=0)"
fi
