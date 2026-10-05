#!/usr/bin/env bash
# Déploie linux_agent (worker desktop) sur Omarchy `.143`.
#
# Même contrat HTTP que Windows `.10:5005` : GET /healthz · POST /invoke
# Cible Agir : desktop_target=omarchy | « sur omarchy » | 192.168.0.143
#
# Usage :
#   bash packages/cortex/infra/scripts/deploy_linux_agent_143.sh
#
# Notes :
#   - Ne réécrit PAS linux.env s’il existe déjà (préserve APP_ALLOWLIST studio, mail…).
#   - Seed initial inclut code/vscode pour le poste éditeur.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORTEX_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SRC="${CORTEX_ROOT}/linux_agent/Agent_IA"
SECRETS="${CORTEX_ROOT}/infra/secrets/omarchy-143.env.local"

HOST="${LBG_OMARCHY_HOST:-192.168.0.143}"
USER="${LBG_OMARCHY_USER:-lbg}"
PORT="${LBG_OMARCHY_AGENT_PORT:-5005}"
REMOTE_DIR="${LBG_OMARCHY_AGENT_DIR:-/home/${USER}/Agent_IA}"

# Local short-circuit : si on tourne déjà sur .143, pas besoin de SSH.
LOCAL=0
if ip -4 addr show 2>/dev/null | grep -q '192\.168\.0\.143/'; then
  LOCAL=1
fi

if [[ ! -d "${SRC}" ]]; then
  echo "ERR: linux_agent introuvable: ${SRC}" >&2
  exit 1
fi

TOKEN=""
if [[ -f "${SECRETS}" ]]; then
  TOKEN="$(grep -E '^LBG_OMARCHY_LINUX_APPROVAL_TOKEN=' "${SECRETS}" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '\r' || true)"
fi
if [[ -z "${TOKEN}" ]]; then
  TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
  mkdir -p "$(dirname "${SECRETS}")"
  if [[ -f "${SECRETS}" ]] && grep -q '^LBG_OMARCHY_LINUX_APPROVAL_TOKEN=' "${SECRETS}"; then
    sed -i "s|^LBG_OMARCHY_LINUX_APPROVAL_TOKEN=.*|LBG_OMARCHY_LINUX_APPROVAL_TOKEN=${TOKEN}|" "${SECRETS}"
  elif [[ -f "${SECRETS}" ]]; then
    printf '\nLBG_OMARCHY_LINUX_APPROVAL_TOKEN=%s\n' "${TOKEN}" >>"${SECRETS}"
  else
    printf 'LBG_OMARCHY_LINUX_APPROVAL_TOKEN=%s\n' "${TOKEN}" >"${SECRETS}"
  fi
  echo "==> Token écrit dans ${SECRETS} (gitignoré)"
fi

TMP_ENV="$(mktemp)"
trap 'rm -f "${TMP_ENV}"' EXIT
cat >"${TMP_ENV}" <<ENV
# Omarchy .143 — linux_agent (hot-reload) — seed initial seulement
# Écosystème-first : pas de gate agent (contre-pouvoir Compagnon/orch)
LBG_LINUX_DRY_RUN=0
LBG_LINUX_URL_ALLOWLIST=
LBG_LINUX_URL_HOST_ALLOWLIST=google.com,duckduckgo.com,github.com,192.168.0.100,192.168.0.140
LBG_LINUX_FILE_ALLOWLIST_DIRS=/tmp,/var/tmp,/home/lbg
LBG_LINUX_APP_ALLOWLIST=chromium,code,cursor,firefox,htop,kitty,vscode,xdg-open,foot,claude,opencode,codex,copilot
LBG_LINUX_APP_MAP_JSON={"chromium":["/usr/bin/chromium"],"firefox":["/usr/bin/firefox"],"htop":["/usr/bin/htop"],"kitty":["/usr/bin/kitty"],"xdg-open":["/usr/bin/xdg-open"],"code":["/usr/bin/code"],"vscode":["/usr/bin/code"],"cursor":["/usr/bin/code"],"foot":["/usr/bin/foot"],"claude":["claude"],"opencode":["opencode"],"codex":["codex"],"copilot":["copilot"]}
LBG_LINUX_LEARN_ENABLED=1
LBG_LINUX_LEARN_APP_ALLOWLIST=
LBG_LINUX_AUDIT_LOG_PATH=${REMOTE_DIR}/logs/linux_agent_audit.jsonl
LBG_LINUX_AUDIT_STDOUT=1
LBG_LINUX_FACE_PARTS_ENABLED=0
LBG_LINUX_APPROVAL_MODE=off
LBG_DESKTOP_APPROVAL_MODE=off
ENV


echo "==> Sync Agent_IA → ${USER}@${HOST}:${REMOTE_DIR} (local=${LOCAL})"
if [[ "${LOCAL}" -eq 1 ]]; then
  mkdir -p "${REMOTE_DIR}/logs" "${HOME}/.config/systemd/user"
  rsync -az --delete \
    --exclude '.venv/' \
    --exclude '__pycache__/' \
    --exclude 'linux.env' \
    --exclude 'logs/' \
    "${SRC}/" "${REMOTE_DIR}/"
  if [[ ! -f "${REMOTE_DIR}/linux.env" ]]; then
    cp "${TMP_ENV}" "${REMOTE_DIR}/linux.env"
    echo "==> Seed linux.env (nouveau)"
  else
    echo "==> Conserve linux.env existant (pas d’écrasement)"
  fi
else
  ssh -o BatchMode=yes "${USER}@${HOST}" "mkdir -p '${REMOTE_DIR}/logs' ~/.config/systemd/user"
  rsync -az --delete \
    --exclude '.venv/' \
    --exclude '__pycache__/' \
    --exclude 'linux.env' \
    --exclude 'logs/' \
    -e "ssh -o BatchMode=yes" \
    "${SRC}/" "${USER}@${HOST}:${REMOTE_DIR}/"
  if ssh -o BatchMode=yes "${USER}@${HOST}" "test -f '${REMOTE_DIR}/linux.env'"; then
    echo "==> Conserve linux.env distant (pas d’écrasement)"
  else
    rsync -az -e "ssh -o BatchMode=yes" "${TMP_ENV}" "${USER}@${HOST}:${REMOTE_DIR}/linux.env"
    echo "==> Seed linux.env (nouveau)"
  fi
fi

echo "==> Venv + systemd --user"
REMOTE_SETUP=$(cat <<EOF
set -euo pipefail
cd '${REMOTE_DIR}'
if [[ ! -x .venv/bin/pip ]]; then
  python3 -m venv .venv
fi
.venv/bin/pip install -q -U pip
.venv/bin/pip install -q -r requirements.txt

cat > ~/.config/systemd/user/lbg-omarchy-agent.service <<UNIT
[Unit]
Description=LBG Omarchy linux_agent (:${PORT})
After=network-online.target graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
WorkingDirectory=${REMOTE_DIR}
Environment=LBG_LINUX_ENV_PATH=${REMOTE_DIR}/linux.env
Environment=XDG_RUNTIME_DIR=/run/user/\$(id -u)
ExecStart=${REMOTE_DIR}/.venv/bin/uvicorn main:app --host 0.0.0.0 --port ${PORT}
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
UNIT

systemctl --user daemon-reload
systemctl --user enable --now lbg-omarchy-agent.service
systemctl --user restart lbg-omarchy-agent.service
loginctl enable-linger "\$(whoami)" 2>/dev/null || true
if command -v ufw >/dev/null 2>&1; then
  sudo ufw allow from 192.168.0.0/16 to any port ${PORT} proto tcp comment omarchy-linux-agent >/dev/null 2>&1 || true
fi
sleep 2
systemctl --user is-active lbg-omarchy-agent.service
curl -fsS "http://127.0.0.1:${PORT}/healthz"
echo
EOF
)
if [[ "${LOCAL}" -eq 1 ]]; then
  bash -c "${REMOTE_SETUP}"
else
  ssh -o BatchMode=yes "${USER}@${HOST}" bash -s <<<"${REMOTE_SETUP}"
fi

echo "==> Smoke LAN (open_app + update_vscode dry-run)"
curl -fsS -m 8 "http://${HOST}:${PORT}/healthz"
echo
curl -fsS -m 15 -X POST "http://${HOST}:${PORT}/invoke" \
  -H 'Content-Type: application/json' \
  -d '{"actor_id":"ui:compagnon","text":"dry","context":{"desktop_dry_run":true,"desktop_action":{"kind":"open_app","app":"chromium","args":[]}}}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('open_app', d.get('ok'), d.get('outcome'), d.get('error'))"
curl -fsS -m 150 -X POST "http://${HOST}:${PORT}/invoke" \
  -H 'Content-Type: application/json' \
  -d '{"actor_id":"ui:compagnon","text":"dry","context":{"desktop_dry_run":true,"desktop_action":{"kind":"update_vscode"}}}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); st=d.get('status') or {}; print('update_vscode', d.get('ok'), d.get('outcome'), st.get('current'), '→', st.get('available'))"

echo "OK  Agent Omarchy http://${HOST}:${PORT}/  · desktop_target=omarchy"
echo "    Token : LBG_OMARCHY_LINUX_APPROVAL_TOKEN → infra/secrets/omarchy-143.env.local (optionnel)"
echo "    Agir MAJ : « mets à jour vscode sur omarchy » (dry-run → confirm orch)"
echo "    Smoke    : bash packages/cortex/infra/scripts/smoke_update_vscode_143.sh"
