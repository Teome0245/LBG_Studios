#!/usr/bin/env bash
# Prépare WSL pour l'entraînement LoRA distant (sshd:2222 + clé VM 140).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VM_HOST="${LBG_CORE_VM_HOST:-192.168.0.140}"
VM_USER="${LBG_CORE_VM_USER:-lbg}"
WSL_USER="${LBG_INFOGRAPHISTE_WSL_SSH_USER:-sdesh}"
WSL_PORT="${LBG_INFOGRAPHISTE_WSL_SSH_PORT:-2222}"

echo "=== WSL — OpenSSH port ${WSL_PORT} + clé ${VM_USER}@${VM_HOST} ==="

if ! dpkg -s openssh-server >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo apt-get install -y openssh-server
fi

if ! grep -q "^Port ${WSL_PORT}\$" /etc/ssh/sshd_config 2>/dev/null; then
  sudo sed -i "s/^#Port 22/Port ${WSL_PORT}/" /etc/ssh/sshd_config
  sudo sed -i "s/^Port 22\$/Port ${WSL_PORT}/" /etc/ssh/sshd_config
fi

sudo systemctl disable --now ssh.socket 2>/dev/null || true
sudo systemctl enable ssh.service
sudo systemctl restart ssh.service

PUBKEY="$(ssh -o BatchMode=yes "${VM_USER}@${VM_HOST}" "cat /home/${VM_USER}/.ssh/id_ed25519.pub")"
AUTH="/home/${WSL_USER}/.ssh/authorized_keys"
mkdir -p "/home/${WSL_USER}/.ssh"
chmod 700 "/home/${WSL_USER}/.ssh"
if [[ -f "${AUTH}" ]] && grep -qF "${PUBKEY}" "${AUTH}"; then
  echo "Clé déjà présente dans ${AUTH}"
else
  echo "${PUBKEY}" >> "${AUTH}"
  echo "Clé ajoutée → ${AUTH}"
fi
chmod 600 "${AUTH}"

echo "OK WSL — écoute:"
sudo ss -tlnp | grep "sshd" || true
echo ""
echo "Étape suivante (admin Windows, une fois) :"
echo "  powershell -ExecutionPolicy Bypass -File \"$(wslpath -w "${ROOT_DIR}/infra/scripts/setup_wsl_lora_train_portproxy.ps1")\""
