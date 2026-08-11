#!/usr/bin/env bash
# Diagnostic Argus depuis poste dev WSL → SSH VM core 140 (env LAN + sidecar 246).
#
# Usage (terminal Ubuntu WSL) :
#   bash infra/scripts/diag_godot_supervisor_wsl.sh
#   bash infra/scripts/diag_godot_supervisor_wsl.sh --json
#
# Prérequis : accès LAN 192.168.0.0/24, clé SSH vers lbg@140 (voir docs/ops_vm_user.md)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CORE_HOST="${LBG_CORE_VM_HOST:-192.168.0.140}"
CORE_USER="${LBG_CORE_VM_USER:-lbg}"

SSH_OPTS=(-o ConnectTimeout=10 -o BatchMode=yes)
if [[ -n "${LBG_SSH_IDENTITY:-}" && -f "${LBG_SSH_IDENTITY}" ]]; then
  SSH_OPTS+=(-i "${LBG_SSH_IDENTITY}")
fi
if [[ -n "${LBG_SSH_KNOWN_HOSTS_FILE:-}" ]]; then
  SSH_OPTS+=(-o "UserKnownHostsFile=${LBG_SSH_KNOWN_HOSTS_FILE}")
fi

if grep -qi microsoft /proc/version 2>/dev/null; then
  echo "[wsl] poste Windows/WSL détecté — cible ${CORE_USER}@${CORE_HOST}"
else
  echo "[info] pas WSL Microsoft — tentative SSH ${CORE_USER}@${CORE_HOST} quand même"
fi

# Ping rapide (non bloquant)
if ping -c 1 -W 2 "${CORE_HOST}" >/dev/null 2>&1; then
  echo "[lan] ${CORE_HOST} joignable"
else
  echo "[warn] ${CORE_HOST} ne répond pas au ping — SSH peut quand même marcher" >&2
fi

exec bash "${ROOT_DIR}/infra/scripts/diag_godot_supervisor.sh" --ssh "$@"
