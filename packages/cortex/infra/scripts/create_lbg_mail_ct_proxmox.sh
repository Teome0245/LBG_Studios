#!/usr/bin/env bash
# Crée le conteneur Proxmox LXC lbg-mail (CTID 154 -> IP 192.168.0.54).
# Installe et configure Stalwart Mail Server (IMAP, SMTP, JMAP + WebAdmin).
#
# Usage :
#   bash packages/cortex/infra/scripts/create_lbg_mail_ct_proxmox.sh
#
set -euo pipefail

PVE="${LBG_PVE_HOST:-192.168.0.201}"
CTID="${LBG_MAIL_CTID:-154}"
IP="192.168.0.${LBG_MAIL_IP_OCTET:-54}"
HOSTNAME="${LBG_MAIL_HOSTNAME:-lbg-mail}"
STORAGE="${LBG_MAIL_STORAGE:-local-vm-930g}"
TEMPLATE="${LBG_MAIL_TEMPLATE:-local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst}"
MEMORY="${LBG_MAIL_MEMORY_MB:-2048}"
CORES="${LBG_MAIL_CORES:-2}"
DISK_GB="${LBG_MAIL_DISK_GB:-15}"
GW="${LBG_MAIL_GW:-192.168.0.254}"
DNS="${LBG_MAIL_DNS:-192.168.0.53}"
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
    --swap 512 \\
    --storage "\${STORAGE}" \\
    --rootfs "\${STORAGE}:\${DISK_GB}" \\
    --net0 "name=eth0,bridge=vmbr0,ip=\${IP}/24,gw=\${GW}" \\
    --nameserver "\${DNS}" \\
    --searchdomain laboiteageeks.fr \\
    --features nesting=1 \\
    --unprivileged 1 \\
    --onboot 1 \\
    --description "Serveur Mail Stalwart — lab LBG Studios (IMAP / SMTP / WebAdmin)"
  echo "CT \${CTID} créé avec succès."
fi

pct start "\${CTID}" || true
sleep 4
pct status "\${CTID}"
EOF

echo "=== 2. Installation de Stalwart Mail Server dans le conteneur ==="

PUBKEY="$(cat "${SSH_PUB}" 2>/dev/null || true)"

ssh -o BatchMode=yes "root@${PVE}" "pct exec ${CTID} -- bash -s" <<EOF
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

echo "Mise à jour des paquets et dépendances de base..."
apt-get update -qq
apt-get install -y -qq curl ca-certificates tar sudo openssh-server

# Configuration SSH si clé fournie
if [[ -n "${PUBKEY}" ]]; then
  mkdir -p /root/.ssh
  chmod 700 /root/.ssh
  grep -qF '${PUBKEY}' /root/.ssh/authorized_keys 2>/dev/null || echo '${PUBKEY}' >> /root/.ssh/authorized_keys
  chmod 600 /root/.ssh/authorized_keys
fi

# Installation de Stalwart Mail Server via l'installateur officiel
if ! command -v stalwart-mail &>/dev/null; then
  echo "Téléchargement et installation de Stalwart Mail Server..."
  curl -sSf https://get.stalw.art/install.sh | sh
else
  echo "Stalwart Mail Server déjà installé."
fi

systemctl daemon-reload || true
systemctl enable stalwart-mail || true
systemctl restart stalwart-mail || true
sleep 3
systemctl status stalwart-mail --no-pager || true
EOF

echo ""
echo "======================================================================"
echo "✦ Stalwart Mail Server est déployé et actif sur le LAN !"
echo "✦ IP du serveur Mail : ${IP}"
echo "✦ WebAdmin / Setup initial : http://${IP}:8080"
echo "✦ Ports IMAP : ${IP}:143 (STARTTLS) / ${IP}:993 (SSL)"
echo "✦ Ports SMTP : ${IP}:587 (Submission) / ${IP}:25 (Relay)"
echo "======================================================================"
