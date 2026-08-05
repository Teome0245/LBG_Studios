#!/usr/bin/env bash
# Sync Cursor Cloud Agent (CURSOR_API_KEY + allowlist) vers VM core 140 uniquement.
#
# Ne pousse pas tout lbg.env — patch idempotent de /etc/lbg-ia-mmo.env + pip cursor-sdk
# + restart lbg-orchestrator + smoke GET /v1/team/cursor/health.
#
# Prérequis : SSH lbg@192.168.0.140 (BatchMode ou agent).
#
# Usage :
#   CURSOR_API_KEY=cursor_... bash tools/push_cursor_secrets_140.sh
#   bash tools/push_cursor_secrets_140.sh   # lit CURSOR_API_KEY dans infra/secrets/lbg.env si présent
#
# Options :
#   LBG_VM_HOST          défaut 192.168.0.140
#   LBG_VM_USER          défaut lbg
#   LBG_REMOTE_DIR       défaut /opt/LBG_IA_MMO
#   LBG_CURSOR_AGENT_ENABLED   défaut 1
#   LBG_CURSOR_AGENT_REPOS     défaut Teome0245/LBG_Studios,Teome0245/new_mmo
#   LBG_CURSOR_AGENT_MODEL     défaut composer-2.5
#   LBG_CURSOR_SKIP_SMOKE=1    ne pas curl health après push
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CORTEX="${ROOT}/packages/cortex"
LOCAL_ENV="${CORTEX}/infra/secrets/lbg.env"

VM_HOST="${LBG_VM_HOST:-192.168.0.140}"
VM_USER="${LBG_VM_USER:-lbg}"
REMOTE_DIR="${LBG_REMOTE_DIR:-/opt/LBG_IA_MMO}"
ENABLED="${LBG_CURSOR_AGENT_ENABLED:-1}"
REPOS="${LBG_CURSOR_AGENT_REPOS:-Teome0245/LBG_Studios,Teome0245/new_mmo}"
MODEL="${LBG_CURSOR_AGENT_MODEL:-composer-2.5}"
SKIP_REVIEWER="${LBG_CURSOR_AGENT_SKIP_REVIEWER:-1}"

read_api_key() {
  if [[ -n "${CURSOR_API_KEY:-}" ]]; then
    return 0
  fi
  if [[ -f "${LOCAL_ENV}" ]]; then
    local line
    line="$(grep -E '^CURSOR_API_KEY=' "${LOCAL_ENV}" | tail -1 || true)"
    if [[ -n "${line}" ]]; then
      CURSOR_API_KEY="${line#CURSOR_API_KEY=}"
      CURSOR_API_KEY="${CURSOR_API_KEY%\"}"
      CURSOR_API_KEY="${CURSOR_API_KEY#\"}"
      CURSOR_API_KEY="${CURSOR_API_KEY//\"/}"
    fi
  fi
}

read_api_key
if [[ -z "${CURSOR_API_KEY:-}" ]]; then
  echo "ERROR: CURSOR_API_KEY manquante." >&2
  echo "  export CURSOR_API_KEY=cursor_... && bash tools/push_cursor_secrets_140.sh" >&2
  echo "  ou ajouter CURSOR_API_KEY=... dans ${LOCAL_ENV}" >&2
  exit 1
fi

SSH_OPTS=(
  -o BatchMode=yes
  -o ConnectTimeout=8
  -o ControlMaster=auto
  -o ControlPersist=5m
  -o "ControlPath=/tmp/lbg_cursor_%r@%h:%p"
)

SNIPPET="$(mktemp)"
trap 'rm -f "${SNIPPET}"' EXIT
cat > "${SNIPPET}" <<EOF
# --- Cursor Cloud Agent (sync tools/push_cursor_secrets_140.sh) ---
LBG_CURSOR_AGENT_ENABLED="${ENABLED}"
CURSOR_API_KEY="${CURSOR_API_KEY}"
LBG_CURSOR_AGENT_REPOS="${REPOS}"
LBG_CURSOR_AGENT_MODEL="${MODEL}"
LBG_CURSOR_AGENT_SKIP_REVIEWER="${SKIP_REVIEWER}"
EOF

REMOTE_SNIP="cursor-agent-snippet.$$"

echo "=== Sync Cursor Cloud Agent → ${VM_USER}@${VM_HOST} ==="

scp "${SSH_OPTS[@]}" "${SNIPPET}" "${VM_USER}@${VM_HOST}:/tmp/${REMOTE_SNIP}"

ssh "${SSH_OPTS[@]}" "${VM_USER}@${VM_HOST}" "bash -s" <<REMOTE
set -euo pipefail
ENV_FILE="/etc/lbg-ia-mmo.env"
TMP="\$(mktemp)"
if sudo -n test -f "\${ENV_FILE}"; then
  sudo -n grep -Ev '^(LBG_CURSOR_AGENT_|CURSOR_API_KEY=)' "\${ENV_FILE}" > "\${TMP}" || true
else
  : > "\${TMP}"
fi
cat "/tmp/${REMOTE_SNIP}" >> "\${TMP}"
sudo -n install -m 640 -o root -g lbg "\${TMP}" "\${ENV_FILE}"
rm -f "\${TMP}" "/tmp/${REMOTE_SNIP}"
echo "OK: patched \${ENV_FILE} (Cursor block)"
REMOTE

echo "=== pip cursor-sdk (orchestrator venv) ==="
ssh "${SSH_OPTS[@]}" "${VM_USER}@${VM_HOST}" "bash -lc '
  set -euo pipefail
  VENV=\"${REMOTE_DIR}/.venv/bin/pip\"
  if [[ ! -x \"\${VENV}\" ]]; then
    echo \"WARN: venv absent — lancer install_local.sh sur 140\" >&2
    exit 0
  fi
  \"\${VENV}\" install -q \"cursor-sdk>=0.1\"
  \"\${VENV}\" show cursor-sdk | grep -E \"^Name:|^Version:\" || true
'"

echo "=== restart lbg-orchestrator ==="
ssh "${SSH_OPTS[@]}" "${VM_USER}@${VM_HOST}" "sudo -n systemctl restart lbg-orchestrator.service && sleep 2 && sudo -n systemctl is-active lbg-orchestrator.service"

if [[ "${LBG_CURSOR_SKIP_SMOKE:-0}" != "1" ]]; then
  echo "=== smoke GET /v1/team/cursor/health ==="
  if bash "${CORTEX}/infra/scripts/smoke_cursor_agent_lan.sh" "http://${VM_HOST}:8010"; then
    echo "OK smoke cursor health (ready=true)"
  else
    rc=$?
    if [[ "${rc}" -eq 2 ]]; then
      echo "WARN smoke: endpoint OK mais ready=false" >&2
      exit 1
    fi
    echo "WARN smoke cursor health — vérifier journalctl -u lbg-orchestrator sur 140" >&2
    exit 1
  fi
fi

echo "Done — Cursor Cloud Agent configuré sur ${VM_HOST}"
