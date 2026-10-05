#!/usr/bin/env bash
# Setup venv FT Compagnon E4b sur la machine GPU (.10).
# Usage (sur .10) :
#   cd /chemin/LBG_Studios
#   bash packages/cortex/infra/llm_persona_e2b/setup_venv_ft_10.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="${LBG_FT_VENV:-$ROOT/.venv-ft}"
PYTHON="${LBG_FT_PYTHON:-python3}"

echo "==> nvidia-smi"
nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv || {
  echo "ERR: pas de GPU NVIDIA visible — arrêter ici." >&2
  exit 1
}

echo "==> venv ${VENV}"
"${PYTHON}" -m venv "${VENV}"
# shellcheck disable=SC1091
source "${VENV}/bin/activate"
pip install -U pip wheel setuptools

echo "==> deps (torch CUDA + unsloth stack — versions à ajuster si besoin)"
# Torch : laisser l'index CUDA officiel si besoin
#   pip install torch --index-url https://download.pytorch.org/whl/cu124
pip install torch
pip install "datasets" "accelerate" "peft" "trl" "transformers>=4.51" "sentencepiece" "protobuf"
# Unsloth : best-effort (API évolue vite avec Gemma 4)
pip install "unsloth[cu124-torch250] @ git+https://github.com/unslothai/unsloth.git" \
  || pip install unsloth \
  || echo "WARN: unsloth install failed — le script train tentera peft/transformers seuls"

echo "==> ok"
echo "source ${VENV}/bin/activate"
echo "python ${ROOT}/train_qlora_e4b.py --help"
