#!/usr/bin/env bash
# Check GPU .10 (WSL :2222) avant un chantier QLoRA E4b-qat.
# Usage :
#   bash packages/cortex/infra/scripts/check_gpu_ft_10.sh
#   bash packages/cortex/infra/scripts/check_gpu_ft_10.sh lbg-wsl-10
set -euo pipefail

TARGET="${1:-${LBG_FT_SSH_HOST:-lbg-wsl-10}}"
# Compat IP nue → alias WSL
if [[ "$TARGET" == "192.168.0.10" ]]; then
  TARGET="lbg-wsl-10"
fi

echo "==> GPU probe @ ${TARGET}"
if [[ "$TARGET" == "127.0.0.1" || "$TARGET" == "localhost" ]]; then
  (command -v nvidia-smi >/dev/null && nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv) \
    || /usr/lib/wsl/lib/nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv
else
  ssh -o BatchMode=yes -o ConnectTimeout=8 "$TARGET" \
    'export PATH="/usr/lib/wsl/lib:$PATH"; nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv'
fi

echo
echo "Repères E4b-qat QLoRA :"
echo "  ≥8 Go VRAM : confortable"
echo "  6–8 Go     : OK serré (batch 1, seq≤2048)"
echo "  4 Go (1050 Ti) : smoke ultra-serré seulement (seq≤512, r=8) — sinon rester Modelfile e4b-v1"
echo
echo "SSH : Host lbg-wsl-10 → sdesh@192.168.0.10:2222"
echo "Suite : packages/cortex/infra/llm_persona_e2b/RUN_ON_10.md"
