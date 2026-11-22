#!/usr/bin/env bash
# Crée le conteneur Proxmox LXC lbg-dc (CTID 150 -> IP 192.168.0.150).
# Déploie un Contrôleur de Domaine Active Directory natif avec Samba 4 (AD-DC).
#
# Usage :
#   bash packages/cortex/infra/scripts/create_lbg_dc_ct_proxmox.sh
#
set -euo pipefail

PVE="${LBG_PVE_HOST:-192.168.0.201}"
CTID="${LBG_DC_CTID:-150}"
IP="192.168.0.${LBG_DC_IP_OCTET:-150}"
HOSTNAME="${LBG_DC_HOSTNAME:-lbg-dc}"
STORAGE="${LBG_DC_STORAGE:-local-vm-930g}"
TEMPLATE="${LBG_DC_TEMPLATE:-local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst}"
MEMORY="${LBG_DC_MEMORY_MB:-2048}"
CORES="${LBG_DC_CORES:-2}"
DISK_GB="${LBG_DC_DISK_GB:-15}"
GW="${LBG_DC_GW:-192.168.0.254}"
DNS="${LBG_DC_DNS:-192.168.0.53}"
REALM="LABOITEAGEEKS.FR"
DOMAIN="LABOITEAGEEKS"
ADMIN_PASS="${LBG_AD_ADMIN_PASS:-0245++Nabucho}"
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
    --features nesting=1,keyctl=1 \\
    --unprivileged 0 \\
    --onboot 1 \\
    --description "Contrôleur de Domaine Active Directory Samba 4 — lab LBG Studios (laboiteageeks.fr)"
  echo "CT \${CTID} créé avec succès."
fi

pct start "\${CTID}" || true
sleep 4
pct status "\${CTID}"
EOF

echo "=== 2. Installation et Provisionnement de Samba 4 AD-DC ==="

PUBKEY="$(cat "${SSH_PUB}" 2>/dev/null || true)"

ssh -o BatchMode=yes "root@${PVE}" "pct exec ${CTID} -- bash -s" <<EOF
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

echo "Mise à jour et installation des paquets Samba AD..."
apt-get update -qq
apt-get install -y -qq samba smbclient winbind libpam-winbind libnss-winbind krb5-user krb5-config acl attr dnsutils curl sudo openssh-server

# Configuration SSH si clé fournie
if [[ -n "${PUBKEY}" ]]; then
  mkdir -p /root/.ssh
  chmod 700 /root/.ssh
  grep -qF '${PUBKEY}' /root/.ssh/authorized_keys 2>/dev/null || echo '${PUBKEY}' >> /root/.ssh/authorized_keys
  chmod 600 /root/.ssh/authorized_keys
fi

# Arrêt et masquage des services standard
echo "Désactivation des daemons standalone..."
systemctl stop smbd nmbd winbind || true
systemctl disable smbd nmbd winbind || true
systemctl mask smbd nmbd winbind || true

# Suppression de la config standard
rm -f /etc/samba/smb.conf
rm -f /etc/krb5.conf

# Provisionnement du domaine AD
echo "Provisionnement du domaine ${REALM}..."
samba-tool domain provision \
  --server-role=dc \
  --use-rfc2307 \
  --dns-backend=SAMBA_INTERNAL \
  --realm="${REALM}" \
  --domain="${DOMAIN}" \
  --adminpass="${ADMIN_PASS}"

# Ajout du DNS forwarder (AdGuard Home) dans smb.conf
sed -i '/\[global\]/a \tdns forwarder = 192.168.0.53' /etc/samba/smb.conf

# Configuration Kerberos
cp /var/lib/samba/private/krb5.conf /etc/krb5.conf

# Lancement du service Active Directory
systemctl unmask samba-ad-dc
systemctl enable --now samba-ad-dc

# Configuration du résolveur local sur lui-même
cat <<RESOLV > /etc/resolv.conf
nameserver 127.0.0.1
nameserver 192.168.0.53
search laboiteageeks.fr
RESOLV

echo "Vérification de l'état du domaine AD..."
sleep 3
samba-tool domain level show
smbclient -L localhost -U "Administrator%${ADMIN_PASS}"
EOF

echo ""
echo "======================================================================"
echo "✦ Contrôleur de Domaine Active Directory ${REALM} actif sur http://${IP} !"
echo "======================================================================"
