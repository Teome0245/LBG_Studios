#!/usr/bin/env bash
# Active le train LoRA distant 140 → WSL (vision timer + SSH GPU).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VM_HOST="${LBG_CORE_VM_HOST:-192.168.0.140}"
VM_USER="${LBG_CORE_VM_USER:-lbg}"

echo "=== 1/4 WSL — sshd:2222 + clé VM 140 ==="
bash "${ROOT_DIR}/infra/scripts/setup_wsl_lora_train_wsl.sh"

echo ""
echo "=== 2/4 Windows — portproxy 2222 (admin requis, UAC) ==="
PS1_WIN="$(wslpath -w "${ROOT_DIR}/infra/scripts/setup_wsl_lora_train_portproxy.ps1")"
powershell.exe -NoProfile -Command "Start-Process powershell -Verb RunAs -Wait -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"${PS1_WIN}\"'" || true

echo ""
echo "=== 3/4 Push secrets → ${VM_HOST} ==="
LBG_VM_HOST="${VM_HOST}" LBG_RESTART_SERVICES=0 bash "${ROOT_DIR}/infra/scripts/push_secrets_vm.sh"

echo ""
echo "=== 4/4 Install timer LoRA sur ${VM_HOST} ==="
bash "${ROOT_DIR}/infra/scripts/install_team_infographiste_lora_job_vm.sh"

echo ""
echo "=== Smoke SSH depuis ${VM_HOST} ==="
ssh -o BatchMode=yes "${VM_USER}@${VM_HOST}" "ssh -o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new -i /home/lbg/.ssh/id_ed25519 -p 2222 sdesh@192.168.0.10 'echo WSL_TRAIN_OK && test -x /home/sdesh/projects/Infographiste_IA/scripts/train_lora_by_style.sh && echo SCRIPT_OK'" || {
  echo ""
  echo "ATTENTION: SSH 140→WSL non OK — relancer en admin Windows:"
  echo "  powershell -ExecutionPolicy Bypass -File \"${PS1_WIN}\""
  exit 2
}

echo ""
echo "OK — train distant actif (LBG_INFOGRAPHISTE_LORA_TRAIN_ENABLED=1 sur 140)"
