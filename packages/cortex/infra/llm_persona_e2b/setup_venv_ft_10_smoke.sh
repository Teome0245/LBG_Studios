#!/usr/bin/env bash
# Setup venv FT smoke 4Go — peft/bnb sans Unsloth (plus léger / fiable 1050 Ti).
# Usage sur .10 WSL :
#   bash setup_venv_ft_10_smoke.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="${LBG_FT_VENV:-$ROOT/.venv-ft}"
export PATH="/usr/lib/wsl/lib:${PATH}"

echo "==> GPU"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv || exit 1

echo "==> venv ${VENV}"
python3 -m venv "${VENV}"
# shellcheck disable=SC1091
source "${VENV}/bin/activate"
pip install -U pip wheel setuptools

echo "==> torch cu124 (WSL)"
pip install --index-url https://download.pytorch.org/whl/cu124 \
  torch torchvision torchaudio

echo "==> peft / bnb / trl"
pip install "transformers>=4.51" accelerate peft bitsandbytes trl datasets sentencepiece protobuf

python - <<'PY'
import torch
print("torch", torch.__version__, "cuda", torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)
PY
echo "OK — source ${VENV}/bin/activate"
