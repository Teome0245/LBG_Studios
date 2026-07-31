#!/usr/bin/env bash
# Installe Nginx Pilot sur la VM core 140 (statique + proxy API locale).
#
# Usage (poste de dev) :
#   cd LBG_IA_MMO && bash infra/scripts/install_nginx_pilot_140.sh
#
# Variables :
#   LBG_LAN_HOST_FRONT / LBG_VM_HOST   défaut : 192.168.0.140
#   LBG_VM_USER                        défaut : lbg
#   LBG_NGINX_PILOT_PORT               défaut : 8080
#   LBG_SSH_IDENTITY                   optionnel

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VM_USER="${LBG_VM_USER:-lbg}"
VM_HOST="${LBG_LAN_HOST_FRONT:-${LBG_VM_HOST:-192.168.0.140}}"
LISTEN_PORT="${LBG_NGINX_PILOT_PORT:-8080}"
CONF_LOCAL="${ROOT_DIR}/infra/nginx/pilot_web_140.conf.example"
REMOTE_TMP="lbg-pilot-nginx-140.$$"
SITE="lbg-pilot-140"

SSH_OPTS=( -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new )
if [[ "${LBG_SSH_BATCH:-1}" == "1" ]]; then
  SSH_OPTS+=( -o BatchMode=yes )
fi
if [[ -n "${LBG_SSH_IDENTITY:-}" ]]; then
  [[ -f "${LBG_SSH_IDENTITY}" ]] || { echo "Fichier clé absent : ${LBG_SSH_IDENTITY}" >&2; exit 1; }
  SSH_OPTS=( -i "${LBG_SSH_IDENTITY}" "${SSH_OPTS[@]}" )
fi
SSH_OPTS+=(
  -o ControlMaster=auto
  -o ControlPersist=5m
  -o "ControlPath=/tmp/lbg_ia_mmo_%r@%h:%p"
)

if [[ ! -f "${CONF_LOCAL}" ]]; then
  echo "Fichier introuvable : ${CONF_LOCAL}" >&2
  exit 1
fi

TMP_CONF="$(mktemp)"
trap 'rm -f "${TMP_CONF}"' EXIT
sed "s/listen 8080;/listen ${LISTEN_PORT};/" "${CONF_LOCAL}" > "${TMP_CONF}"

echo "Nginx Pilot → ${VM_USER}@${VM_HOST}:${LISTEN_PORT}"

scp "${SSH_OPTS[@]}" "${TMP_CONF}" "${VM_USER}@${VM_HOST}:/tmp/${REMOTE_TMP}"

REMOTE_SCRIPT=$(cat <<EOS
set -euo pipefail
if ! sudo -n true 2>/dev/null; then
  echo "ERROR: sudo NOPASSWD requis sur ${VM_HOST}" >&2
  exit 10
fi
sudo -n apt-get update -qq
# Évite le prompt interactif needrestart (sinon le script SSH bloque).
sudo -n env DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a \
  apt-get install -y -qq nginx
sudo -n install -m 644 /tmp/${REMOTE_TMP} /etc/nginx/sites-available/${SITE}
sudo -n rm -f /tmp/${REMOTE_TMP}
sudo -n rm -f /etc/nginx/sites-enabled/default
sudo -n ln -sf /etc/nginx/sites-available/${SITE} /etc/nginx/sites-enabled/${SITE}
if [[ -d /opt/LBG_IA_MMO ]]; then
  sudo -n chmod o+x /opt /opt/LBG_IA_MMO 2>/dev/null || true
fi
if [[ -d /opt/LBG_IA_MMO/pilot_web ]]; then
  sudo -n chmod -R o+rX /opt/LBG_IA_MMO/pilot_web
fi
sudo -n nginx -t
sudo -n systemctl enable nginx
if ! sudo -n systemctl restart nginx; then
  echo "=== Échec restart nginx ===" >&2
  sudo -n ss -tlnp 2>/dev/null | grep -E ':80|:8080' || true
  sudo -n journalctl -xeu nginx.service --no-pager -n 40 >&2 || true
  exit 1
fi
echo "OK: Nginx :${LISTEN_PORT} -> /opt/LBG_IA_MMO/pilot_web (proxy API 127.0.0.1:8000)"
EOS
)

ssh -tt "${SSH_OPTS[@]}" "${VM_USER}@${VM_HOST}" "bash -lc $(printf '%q' "${REMOTE_SCRIPT}")"

echo ""
echo "Pilot canonique : http://${VM_HOST}:${LISTEN_PORT}/"
echo "Rappel CORS (si UI hors proxy) : inclure http://${VM_HOST}:${LISTEN_PORT}"
echo "Legacy .112:8080 peut rester jusqu'à bascule bookmarks / Traefik."
