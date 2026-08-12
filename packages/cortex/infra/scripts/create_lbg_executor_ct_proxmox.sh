#!/usr/bin/env bash
# Crée le CT Proxmox lbg-executor (CTID = dernier octet IP, ex. 141 → .141).
#
# Usage (depuis poste dev WSL) :
#   bash infra/scripts/create_lbg_executor_ct_proxmox.sh
#   LBG_PVE_HOST=192.168.0.201 LBG_EXECUTOR_CTID=141 bash infra/scripts/create_lbg_executor_ct_proxmox.sh
#
# Puis :
#   LBG_EXECUTOR_HOST=192.168.0.141 bash infra/scripts/install_lbg_executor_ct.sh --remote
#
set -euo pipefail

PVE="${LBG_PVE_HOST:-192.168.0.201}"
CTID="${LBG_EXECUTOR_CTID:-141}"
IP="192.168.0.${CTID}"
HOSTNAME="${LBG_EXECUTOR_HOSTNAME:-lbg-executor}"
STORAGE="${LBG_EXECUTOR_STORAGE:-local-vm-930g}"
TEMPLATE="${LBG_EXECUTOR_TEMPLATE:-local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst}"
MEMORY="${LBG_EXECUTOR_MEMORY_MB:-2048}"
CORES="${LBG_EXECUTOR_CORES:-2}"
DISK_GB="${LBG_EXECUTOR_DISK_GB:-12}"
GW="${LBG_EXECUTOR_GW:-192.168.0.254}"
DNS="${LBG_EXECUTOR_DNS:-192.168.0.254}"
SSH_PUB="${LBG_EXECUTOR_SSH_PUB:-${HOME}/.ssh/id_ed25519.pub}"

[[ -f "${SSH_PUB}" ]] || { echo "Clé SSH absente : ${SSH_PUB}" >&2; exit 2; }

echo "=== Proxmox ${PVE} — CT ${CTID} (${IP}) ==="

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
    --description "LBG LAN executor — poll Team WSL (remplace poste .10)"
  echo "CT \${CTID} créé"
fi

pct start "\${CTID}" || true
sleep 5
pct status "\${CTID}"
EOF

# Bootstrap user lbg + paquets (root via pct exec)
PUBKEY="$(cat "${SSH_PUB}")"
ssh -o BatchMode=yes "root@${PVE}" "pct exec ${CTID} -- bash -s" <<EOF
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a
apt-get update -qq
apt-get install -y -qq curl python3 rsync openssh-client sudo ca-certificates

if ! id lbg &>/dev/null; then
  useradd -m -s /bin/bash -G sudo lbg
fi
mkdir -p /home/lbg/.ssh
chmod 700 /home/lbg/.ssh
grep -qF '${PUBKEY}' /home/lbg/.ssh/authorized_keys 2>/dev/null || echo '${PUBKEY}' >> /home/lbg/.ssh/authorized_keys
chmod 600 /home/lbg/.ssh/authorized_keys
chown -R lbg:lbg /home/lbg/.ssh
echo 'lbg ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/lbg-lbg
chmod 440 /etc/sudoers.d/lbg-lbg

# Clé SSH CT → orchestrateur .140 (diag_godot_supervisor)
if [[ ! -f /home/lbg/.ssh/id_ed25519 ]]; then
  sudo -u lbg ssh-keygen -t ed25519 -N '' -f /home/lbg/.ssh/id_ed25519 -C 'lbg-executor-ct'
fi
cat /home/lbg/.ssh/id_ed25519.pub
EOF

CT_PUBKEY="$(ssh -o BatchMode=yes "root@${PVE}" "pct exec ${CTID} -- cat /home/lbg/.ssh/id_ed25519.pub")"
echo "=== Autoriser CT sur lbg@192.168.0.140 ==="
ssh -o BatchMode=yes lbg@192.168.0.140 "grep -qF '${CT_PUBKEY}' ~/.ssh/authorized_keys 2>/dev/null || echo '${CT_PUBKEY}' >> ~/.ssh/authorized_keys"

echo "=== known_hosts CT → .140 ==="
ssh -o BatchMode=yes "root@${PVE}" "pct exec ${CTID} -- sudo -u lbg bash -lc 'ssh-keyscan -H 192.168.0.140 >> ~/.ssh/known_hosts 2>/dev/null'"

echo ""
echo "OK — CT ${CTID} prêt (${IP})"
echo "  ssh lbg@${IP}"
echo "  LBG_EXECUTOR_HOST=${IP} bash infra/scripts/install_lbg_executor_ct.sh --remote"
