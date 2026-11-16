#!/usr/bin/env bash
# Crée le conteneur Proxmox LXC lbg-dns-adguard (CTID 153 -> IP 192.168.0.53).
#
# Usage :
#   bash packages/cortex/infra/scripts/create_lbg_dns_ct_proxmox.sh
#
set -euo pipefail

PVE="${LBG_PVE_HOST:-192.168.0.201}"
CTID="${LBG_DNS_CTID:-153}"
IP="192.168.0.${LBG_DNS_IP_OCTET:-53}"
HOSTNAME="${LBG_DNS_HOSTNAME:-lbg-dns-adguard}"
STORAGE="${LBG_DNS_STORAGE:-local-vm-930g}"
TEMPLATE="${LBG_DNS_TEMPLATE:-local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst}"
MEMORY="${LBG_DNS_MEMORY_MB:-1024}"
CORES="${LBG_DNS_CORES:-1}"
DISK_GB="${LBG_DNS_DISK_GB:-6}"
GW="${LBG_DNS_GW:-192.168.0.254}"
UPSTREAM_DNS="${LBG_UPSTREAM_DNS:-192.168.0.254}"
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
DNS=${UPSTREAM_DNS}

if pct status "\${CTID}" &>/dev/null; then
  echo "CT \${CTID} existe déjà — skip create"
else
  pct create "\${CTID}" "\${TEMPLATE}" \\
    --hostname "\${HOSTNAME}" \\
    --memory "\${MEMORY}" \\
    --cores "\${CORES}" \\
    --swap 256 \\
    --storage "\${STORAGE}" \\
    --rootfs "\${STORAGE}:\${DISK_GB}" \\
    --net0 "name=eth0,bridge=vmbr0,ip=\${IP}/24,gw=\${GW}" \\
    --nameserver "\${DNS}" \\
    --searchdomain laboiteageeks.fr \\
    --features nesting=1 \\
    --unprivileged 1 \\
    --onboot 1 \\
    --description "Serveur DNS Local AdGuard Home — lab LBG Studios (résilience LAN)"
  echo "CT \${CTID} créé avec succès."
fi

pct start "\${CTID}" || true
sleep 4
pct status "\${CTID}"
EOF

echo "=== 2. Installation d'AdGuard Home dans le conteneur ==="

PUBKEY="$(cat "${SSH_PUB}" 2>/dev/null || true)"

ssh -o BatchMode=yes "root@${PVE}" "pct exec ${CTID} -- bash -s" <<EOF
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

echo "Mise à jour des paquets et dépendances..."
apt-get update -qq
apt-get install -y -qq curl ca-certificates tar sudo openssh-server systemd-resolved

# Configuration SSH basique si clé fournie
if [[ -n "${PUBKEY}" ]]; then
  mkdir -p /root/.ssh
  chmod 700 /root/.ssh
  grep -qF '${PUBKEY}' /root/.ssh/authorized_keys 2>/dev/null || echo '${PUBKEY}' >> /root/.ssh/authorized_keys
  chmod 600 /root/.ssh/authorized_keys
fi

# Libérer le port 53 si systemd-resolved écoute dessus (stub resolver Ubuntu)
if systemctl is-active systemd-resolved &>/dev/null; then
  mkdir -p /etc/systemd/resolved.conf.d
  cat <<'RESOLV_CONF' > /etc/systemd/resolved.conf.d/adguard.conf
[Resolve]
DNSStubListener=no
RESOLV_CONF
  systemctl restart systemd-resolved || true
fi

# Installation d'AdGuard Home via le script officiel officiel
if [[ ! -d /opt/AdGuardHome ]]; then
  echo "Téléchargement et installation d'AdGuard Home..."
  curl -s -S -L 'https://raw.githubusercontent.com/AdguardTeam/AdGuardHome/master/scripts/install.sh' | sh -s -- -v
else
  echo "AdGuard Home déjà installé dans /opt/AdGuardHome"
fi

systemctl status AdGuardHome --no-pager || true
EOF

echo ""
echo "======================================================================"
echo "✦ AdGuard Home est déployé et actif sur le LAN !"
echo "✦ IP du serveur DNS : ${IP}"
echo "✦ Assistant initial : http://${IP}:3000"
echo "✦ Une fois le compte initial créé sur :3000, l'interface web sera sur : http://${IP}/"
echo "✦ Port DNS : ${IP}:53"
echo "======================================================================"
