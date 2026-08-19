#!/usr/bin/env bash
# Installe linux_agent (mains) sur un CT Debian — ne pas confondre avec lbg-lan-executor (.141).
#
# Usage distant :
#   LBG_HANDS_HOST=192.168.0.142 bash packages/cortex/infra/scripts/install_lbg_hands_ct.sh --remote
#
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REMOTE=0
HOST="${LBG_HANDS_HOST:-}"
USER="${LBG_HANDS_USER:-lbg}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --remote) REMOTE=1; shift ;;
    -h|--help)
      sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) echo "Option inconnue: $1" >&2; exit 2 ;;
  esac
done

_install_local() {
  set -euo pipefail
  local agent_dir="/opt/LBG_Studios/packages/cortex/linux_agent/Agent_IA"
  local script_dir="/opt/Infographiste_IA/scripts"
  sudo mkdir -p /var/lib/lbg-hands/inbox "${script_dir}" /var/log/lbg
  sudo chown -R lbg:lbg /var/lib/lbg-hands /opt/Infographiste_IA /opt/LBG_Studios /var/log/lbg
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3-venv python3-pip python3-full >/dev/null
  if [[ ! -x "${agent_dir}/.venv/bin/pip" ]]; then
    rm -rf "${agent_dir}/.venv"
    python3 -m venv "${agent_dir}/.venv"
  fi
  "${agent_dir}/.venv/bin/pip" install -q -U pip
  "${agent_dir}/.venv/bin/pip" install -q -r "${agent_dir}/requirements.txt" pillow
  if [[ ! -f "${agent_dir}/linux.env" ]]; then
    cp "${agent_dir}/linux.env.example" "${agent_dir}/linux.env"
  fi
  python3 - <<'PY'
from pathlib import Path
p = Path("/opt/LBG_Studios/packages/cortex/linux_agent/Agent_IA/linux.env")
keys = {
    "LBG_LINUX_FACE_PARTS_ENABLED": "1",
    "LBG_LINUX_FACE_PARTS_INBOX": "/var/lib/lbg-hands/inbox",
    "LBG_LINUX_FACE_PARTS_SCRIPT": "/opt/Infographiste_IA/scripts/import_face_parts.py",
    "LBG_LINUX_FILE_ALLOWLIST_DIRS": "/var/lib/lbg-hands,/opt/Infographiste_IA,/tmp,/var/tmp",
}
text = p.read_text(encoding="utf-8") if p.is_file() else ""
lines = text.splitlines()
for k, v in keys.items():
    found = False
    for i, ln in enumerate(lines):
        if ln.startswith(k + "=") or ln.startswith("# " + k + "=") or ln.startswith("#" + k + "="):
            lines[i] = f"{k}={v}"
            found = True
            break
    if not found:
        lines.append(f"{k}={v}")
p.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
PY
  if command -v ufw >/dev/null 2>&1; then
    sudo ufw allow 6001/tcp >/dev/null 2>&1 || true
  fi
  sudo cp "${ROOT_DIR}/infra/systemd/lbg-linux-agent.service" /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable --now lbg-linux-agent.service
  sleep 2
  systemctl is-active lbg-linux-agent.service
  curl -fsS "http://127.0.0.1:6001/healthz" | head -c 400 || true
  echo
}

if [[ "${REMOTE}" -eq 1 ]]; then
  [[ -n "${HOST}" ]] || { echo "LBG_HANDS_HOST requis" >&2; exit 2; }
  INFO_ROOT="$(cd "${ROOT_DIR}/../../../Infographiste_IA" && pwd)"
  echo "=== Rsync hands → ${USER}@${HOST} ==="
  ssh -o BatchMode=yes "${USER}@${HOST}" "sudo mkdir -p /opt/LBG_Studios/packages/cortex/linux_agent/Agent_IA /opt/LBG_Studios/packages/cortex/infra/systemd /opt/Infographiste_IA/scripts /var/lib/lbg-hands/inbox && sudo chown -R ${USER}:${USER} /opt/LBG_Studios /opt/Infographiste_IA /var/lib/lbg-hands"
  rsync -az --delete --exclude '.venv/' --exclude '__pycache__/' \
    "${ROOT_DIR}/linux_agent/Agent_IA/" \
    "${USER}@${HOST}:/opt/LBG_Studios/packages/cortex/linux_agent/Agent_IA/"
  rsync -az "${ROOT_DIR}/infra/systemd/lbg-linux-agent.service" \
    "${USER}@${HOST}:/opt/LBG_Studios/packages/cortex/infra/systemd/"
  rsync -az "${ROOT_DIR}/infra/scripts/install_lbg_hands_ct.sh" \
    "${USER}@${HOST}:/opt/LBG_Studios/packages/cortex/infra/scripts/"
  if [[ -f "${INFO_ROOT}/scripts/import_face_parts.py" ]]; then
    rsync -az "${INFO_ROOT}/scripts/import_face_parts.py" \
      "${USER}@${HOST}:/opt/Infographiste_IA/scripts/"
  fi
  ssh -o BatchMode=yes "${USER}@${HOST}" "cd /opt/LBG_Studios/packages/cortex && sudo bash infra/scripts/install_lbg_hands_ct.sh"
else
  _install_local
fi

echo "OK — linux_agent :6001 sur ${HOST:-localhost}"
