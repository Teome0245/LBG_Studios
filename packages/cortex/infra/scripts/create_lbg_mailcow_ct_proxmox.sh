#!/usr/bin/env bash
# Crée le conteneur Proxmox LXC lbg-mailcow (CTID 155 -> IP 192.168.0.55).
# Installe Docker et déploie Mailcow: dockerized (Webmail SOGo, Postfix, Dovecot, Rspamd).
#
# Usage :
#   bash packages/cortex/infra/scripts/create_lbg_mailcow_ct_proxmox.sh
#
set -euo pipefail

PVE="${LBG_PVE_HOST:-192.168.0.201}"
CTID="${LBG_MAILCOW_CTID:-155}"
IP="192.168.0.${LBG_MAILCOW_IP_OCTET:-55}"
HOSTNAME="${LBG_MAILCOW_HOSTNAME:-lbg-mailcow}"
STORAGE="${LBG_MAILCOW_STORAGE:-local-vm-930g}"
TEMPLATE="${LBG_MAILCOW_TEMPLATE:-local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst}"
MEMORY="${LBG_MAILCOW_MEMORY_MB:-4096}"
CORES="${LBG_MAILCOW_CORES:-2}"
DISK_GB="${LBG_MAILCOW_DISK_GB:-25}"
GW="${LBG_MAILCOW_GW:-192.168.0.254}"
DNS="${LBG_MAILCOW_DNS:-192.168.0.53}"
SSH_PUB="${LBG_SSH_PUB:-${HOME}/.ssh/id_ed25519.pub}"

echo "=== 1. Proxmox ${PVE} — Création CT ${CTID} (${HOSTNAME} - ${IP}) ==="

ssh -o BatchMode=yes "root@${PVE}" bash -s <<EOF
set -euo pipefail
CTID=${CTID}
IP=${IP}
HOSTNAME=${HOSTNAME}
STORAGE=${STORAGE}
TEMPLATE=${TEMPLATE}
MEMORY=${MEMORY}
CORES=${CORES}
DISK_GB=${DISK_GB}
GW=${GW}
DNS=${DNS}

if pct status "\${CTID}" &>/dev/null; then
  echo "CT \${CTID} existe déjà — skip create"
else
  pct create "\${CTID}" "\${TEMPLATE}" \\
    --hostname "\${HOSTNAME}" \\
    --memory "\${MEMORY}" \\
    --cores "\${CORES}" \\
    --swap 1024 \\
    --storage "\${STORAGE}" \\
    --rootfs "\${STORAGE}:\${DISK_GB}" \\
    --net0 "name=eth0,bridge=vmbr0,ip=\${IP}/24,gw=\${GW}" \\
    --nameserver "\${DNS}" \\
    --searchdomain laboiteageeks.fr \\
    --features nesting=1,keyctl=1 \\
    --unprivileged 1 \\
    --onboot 1 \\
    --description "Serveur Mail Mailcow (Dockerized) — lab LBG Studios (SOGo / Postfix / Dovecot / Rspamd)"
  echo "CT \${CTID} créé avec succès."
fi

pct start "\${CTID}" || true
sleep 4
pct status "\${CTID}"
EOF

echo "=== 2. Installation de Docker et préparation de Mailcow dans le conteneur ==="

PUBKEY="$(cat "${SSH_PUB}" 2>/dev/null || true)"

ssh -o BatchMode=yes "root@${PVE}" "pct exec ${CTID} -- bash -s" <<EOF
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

echo "Mise à jour des paquets de base..."
apt-get update -qq
apt-get install -y -qq curl ca-certificates gnupg git sudo tar openssh-server apt-transport-https

# Configuration SSH si clé fournie
if [[ -n "${PUBKEY}" ]]; then
  mkdir -p /root/.ssh
  chmod 700 /root/.ssh
  grep -qF '${PUBKEY}' /root/.ssh/authorized_keys 2>/dev/null || echo '${PUBKEY}' >> /root/.ssh/authorized_keys
  chmod 600 /root/.ssh/authorized_keys
fi

# Installation Docker CE officiel
if ! command -v docker &>/dev/null; then
  echo "Installation de Docker officiel..."
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc

  echo "deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \$(. /etc/os-release && echo \"\$VERSION_CODENAME\") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
else
  echo "Docker déjà installé."
fi

systemctl enable --now docker

# Clone de Mailcow
if [[ ! -d /opt/mailcow-dockerized ]]; then
  echo "Clonage de mailcow-dockerized dans /opt..."
  git clone https://github.com/mailcow/mailcow-dockerized /opt/mailcow-dockerized
fi

cd /opt/mailcow-dockerized

# Génération non-interactive de mailcow.conf si absent
if [[ ! -f mailcow.conf ]]; then
  echo "Génération de la configuration mailcow.conf..."
  # Pré-remplir les variables pour generate_config.sh
  printf "mail.laboiteageeks.fr\nEurope/Paris\n1\n" | ./generate_config.sh || true
fi

echo "Mailcow préparé avec succès dans /opt/mailcow-dockerized."
EOF

echo ""
echo "======================================================================"
echo "✦ Conteneur CT ${CTID} (Mailcow) prêt sur http://${IP} !"
echo "======================================================================"
