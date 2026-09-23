#!/usr/bin/env bash
# Déploie le lab Open WebUI (Simple Chat) sur .100:3080
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REMOTE="${LBG_OWUI_REMOTE:-lbg@192.168.0.100}"
REMOTE_DIR="${LBG_OWUI_DIR:-/home/lbg/lbg-open-webui}"

echo "==> sync → ${REMOTE}:${REMOTE_DIR}"
ssh "${REMOTE}" "mkdir -p '${REMOTE_DIR}'"
rsync -az \
  "${ROOT}/docker-compose.yml" \
  "${ROOT}/README.md" \
  "${REMOTE}:${REMOTE_DIR}/"

echo "==> docker compose up"
ssh "${REMOTE}" bash -s <<EOF
set -euo pipefail
cd "${REMOTE_DIR}"
docker compose pull
docker compose up -d
sleep 2
docker compose ps
curl -sS -o /dev/null -w "HTTP %{http_code}\\n" --connect-timeout 5 --max-time 30 http://127.0.0.1:3080/ || true
EOF

echo "OK  Simple Chat → http://192.168.0.100:3080/"
