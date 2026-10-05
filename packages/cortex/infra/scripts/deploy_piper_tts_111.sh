#!/usr/bin/env bash
# Déploie Piper TTS (voice_local) sur CT `.111` → :8098
#
# Usage (depuis la racine LBG_Studios ou packages/cortex) :
#   bash packages/cortex/infra/scripts/deploy_piper_tts_111.sh
#   bash packages/cortex/infra/scripts/deploy_piper_tts_111.sh --smoke
#
# Prérequis : SSH root@192.168.0.111
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORTEX_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SRC="${CORTEX_ROOT}/voice_local"
UNIT="${CORTEX_ROOT}/infra/systemd/lbg-piper-tts.service"

REMOTE_USER="${LBG_PIPER_USER:-root}"
REMOTE_HOST="${LBG_PIPER_HOST:-192.168.0.111}"
REMOTE="${REMOTE_USER}@${REMOTE_HOST}"
REMOTE_DIR="${LBG_PIPER_DIR:-/opt/lbg-piper-tts}"
VOICE="${LBG_PIPER_VOICE:-fr_FR-siwis-medium}"
# HuggingFace rhasspy/piper-voices — fr/siwis/medium
HF_BASE="${LBG_PIPER_HF_BASE:-https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium}"
SMOKE=0
[[ "${1:-}" == "--smoke" ]] && SMOKE=1

if [[ ! -f "${SRC}/app.py" ]]; then
  echo "ERR: voice_local introuvable: ${SRC}" >&2
  exit 1
fi
if [[ ! -f "${UNIT}" ]]; then
  echo "ERR: unit systemd manquante: ${UNIT}" >&2
  exit 1
fi

echo "==> Sync Piper TTS → ${REMOTE}:${REMOTE_DIR}"
ssh -o BatchMode=yes "${REMOTE}" "mkdir -p ${REMOTE_DIR}/models"
rsync -az --delete \
  --exclude '.venv/' \
  --exclude '__pycache__/' \
  --exclude 'models/' \
  "${SRC}/" "${REMOTE}:${REMOTE_DIR}/"
rsync -az "${UNIT}" "${REMOTE}:/etc/systemd/system/lbg-piper-tts.service"

echo "==> venv + modèles (${VOICE})"
ssh -o BatchMode=yes "${REMOTE}" bash -s <<EOF
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a
cd "${REMOTE_DIR}"
apt-get update -qq
apt-get install -y -qq python3-venv python3-pip curl ca-certificates
python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt

MODELS="${REMOTE_DIR}/models"
ONNX="\${MODELS}/${VOICE}.onnx"
CFG="\${MODELS}/${VOICE}.onnx.json"
mkdir -p "\${MODELS}"
if [[ ! -f "\${ONNX}" ]]; then
  echo "Téléchargement ${VOICE}.onnx …"
  curl -fsSL --retry 3 -o "\${ONNX}" "${HF_BASE}/${VOICE}.onnx"
fi
if [[ ! -f "\${CFG}" ]]; then
  echo "Téléchargement ${VOICE}.onnx.json …"
  curl -fsSL --retry 3 -o "\${CFG}" "${HF_BASE}/${VOICE}.onnx.json"
fi
ls -lh "\${ONNX}" "\${CFG}"

systemctl daemon-reload
systemctl enable --now lbg-piper-tts.service
systemctl restart lbg-piper-tts.service
sleep 2
systemctl is-active lbg-piper-tts
EOF

if [[ "$SMOKE" -eq 1 ]]; then
  echo "==> Smoke Piper :8098"
  curl -fsS "http://${REMOTE_HOST}:8098/healthz" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print('health', d.get('ok'), d.get('voice'), 'model', d.get('model_present'))"
  curl -fsS -X POST "http://${REMOTE_HOST}:8098/v1/tts" \
    -H 'Content-Type: application/json' \
    -d '{"text":"Bonjour, je suis le Compagnon du studio."}' \
    -o /tmp/lbg-piper-smoke.wav
  python3 - <<'PY'
import wave
from pathlib import Path
p = Path("/tmp/lbg-piper-smoke.wav")
assert p.is_file() and p.stat().st_size > 1000, p
with wave.open(str(p), "rb") as w:
    print("wav", "ch", w.getnchannels(), "rate", w.getframerate(), "frames", w.getnframes(), "bytes", p.stat().st_size)
PY
fi

echo "OK  Piper TTS http://${REMOTE_HOST}:8098/healthz"
