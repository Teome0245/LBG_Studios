#!/usr/bin/env bash
# Installe le LAN executor (poll Team) sur une VM/CT Debian (remplace WSL .10).
#
# Usage (sur la cible, après rsync monorepo vers /opt/LBG_IA_MMO) :
#   sudo bash infra/scripts/install_lbg_executor_ct.sh
#
# Depuis poste dev (push + install distant) :
#   LBG_EXECUTOR_HOST=192.168.0.141 bash infra/scripts/install_lbg_executor_ct.sh --remote
#
# Prérequis CT :
#   - Debian/Ubuntu, user lbg, /opt/LBG_IA_MMO (rsync ou git clone)
#   - curl, python3, accès LAN .140 et .246
#   - clé SSH lbg@192.168.0.140 pour diag_godot_supervisor_wsl.sh
#
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REMOTE=0
HOST="${LBG_EXECUTOR_HOST:-}"
USER="${LBG_EXECUTOR_USER:-lbg}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --remote) REMOTE=1; shift ;;
    -h|--help)
      sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) echo "Option inconnue: $1" >&2; exit 2 ;;
  esac
done

_install_local() {
  set -euo pipefail
  sudo cp "${ROOT_DIR}/infra/systemd/lbg-lan-executor.service" /etc/systemd/system/
  sudo chmod +x "${ROOT_DIR}/infra/scripts/lbg_wsl_executor.sh"
  sudo chmod +x "${ROOT_DIR}/infra/scripts/diag_godot_supervisor_wsl.sh"
  sudo chmod +x "${ROOT_DIR}/infra/scripts/smoke_wsl_executor_lan.sh" 2>/dev/null || true
  sudo systemctl daemon-reload
  sudo systemctl enable lbg-lan-executor.service
  sudo systemctl restart lbg-lan-executor.service
  sleep 2
  systemctl is-active lbg-lan-executor.service
  journalctl -u lbg-lan-executor -n 8 --no-pager
}

if [[ "${REMOTE}" -eq 1 ]]; then
  [[ -n "${HOST}" ]] || { echo "LBG_EXECUTOR_HOST requis" >&2; exit 2; }
  echo "=== Rsync executor → ${USER}@${HOST} ==="
  ssh -o BatchMode=yes "${USER}@${HOST}" "sudo mkdir -p /opt/LBG_IA_MMO/infra/scripts /opt/LBG_IA_MMO/infra/systemd"
  rsync -az \
    "${ROOT_DIR}/infra/scripts/lbg_wsl_executor.sh" \
    "${ROOT_DIR}/infra/scripts/diag_godot_supervisor_wsl.sh" \
    "${ROOT_DIR}/infra/scripts/smoke_wsl_executor_lan.sh" \
    "${ROOT_DIR}/infra/scripts/smoke_godot_m11_login_lan.sh" \
    "${ROOT_DIR}/infra/scripts/smoke_godot_m12_ws_lan.sh" \
    "${ROOT_DIR}/infra/scripts/smoke_godot_owners.sh" \
    "${ROOT_DIR}/infra/scripts/smoke_cursor_agent_lan.sh" \
    "${USER}@${HOST}:/opt/LBG_IA_MMO/infra/scripts/"
  rsync -az "${ROOT_DIR}/infra/systemd/lbg-lan-executor.service" \
    "${USER}@${HOST}:/opt/LBG_IA_MMO/infra/systemd/"
  ssh -o BatchMode=yes "${USER}@${HOST}" "cd /opt/LBG_IA_MMO && sudo bash infra/scripts/install_lbg_executor_ct.sh"
else
  _install_local
fi

echo "OK — LAN executor actif (poll http://192.168.0.140:8010/v1/team/wsl/poll)"
