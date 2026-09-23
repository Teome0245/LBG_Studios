#!/usr/bin/env bash
# Crée la VM QEMU Omarchy sur le NUC Proxmox (.200) — lab Linux desktop LAN.
#
# Usage (depuis poste dev) :
#   bash infra/scripts/create_omarchy_vm_proxmox.sh
#   bash infra/scripts/create_omarchy_vm_proxmox.sh --download-iso
#   bash infra/scripts/create_omarchy_vm_proxmox.sh --start
#   LBG_OMARCHY_PASSWORD='…' bash infra/scripts/create_omarchy_vm_proxmox.sh --unattended --start
#
# Defaults : PVE=192.168.0.200 · VMID=143 · IP cible=192.168.0.143 · storage=local-lvm
#
# Après install interactive : console Proxmox → https://192.168.0.200:8006/
# Doc : packages/cortex/docs/omarchy_vm_143.md
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORTEX_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

PVE="${LBG_PVE_HOST:-192.168.0.200}"
VMID="${LBG_OMARCHY_VMID:-143}"
IP="192.168.0.${VMID}"
HOSTNAME="${LBG_OMARCHY_HOSTNAME:-lbg-omarchy}"
STORAGE="${LBG_OMARCHY_STORAGE:-local-lvm}"
ISO_STORAGE="${LBG_OMARCHY_ISO_STORAGE:-local}"
MEMORY="${LBG_OMARCHY_MEMORY_MB:-8192}"
CORES="${LBG_OMARCHY_CORES:-4}"
DISK_GB="${LBG_OMARCHY_DISK_GB:-60}"
BRIDGE="${LBG_OMARCHY_BRIDGE:-vmbr0}"
GW="${LBG_OMARCHY_GW:-192.168.0.254}"
DNS="${LBG_OMARCHY_DNS:-192.168.0.254}"
SSH_PUB="${LBG_OMARCHY_SSH_PUB:-${HOME}/.ssh/id_ed25519.pub}"
ISO_VERSION="${LBG_OMARCHY_ISO_VERSION:-4.0.3}"
ISO_URL="${LBG_OMARCHY_ISO_URL:-https://iso.omarchy.org/omarchy-${ISO_VERSION}.iso}"
ISO_SHA256="${LBG_OMARCHY_ISO_SHA256:-03d60bc74306dca51f96e1a84b690871d8d606826b260edd0208962da8507d14}"
ISO_NAME="omarchy-${ISO_VERSION}.iso"
MAC="${LBG_OMARCHY_MAC:-BC:24:11:43:00:01}"
USERNAME="${LBG_OMARCHY_USER:-lbg}"
TIMEZONE="${LBG_OMARCHY_TIMEZONE:-Europe/Paris}"
KB_LAYOUT="${LBG_OMARCHY_KB:-fr}"
ONBOOT="${LBG_OMARCHY_ONBOOT:-0}"

DO_DOWNLOAD=0
DO_START=0
DO_UNATTENDED=0
DRY_RUN=0

usage() {
  sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
  echo "Options : --download-iso  --start  --unattended  --dry-run  -h"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --download-iso) DO_DOWNLOAD=1 ;;
    --start) DO_START=1 ;;
    --unattended) DO_UNATTENDED=1 ;;
    --dry-run) DRY_RUN=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Option inconnue : $1" >&2; usage; exit 2 ;;
  esac
  shift
done

# Par défaut : préparer ISO. Unattended implique start.
if [[ "${DO_DOWNLOAD}" -eq 0 && "${DO_START}" -eq 0 && "${DO_UNATTENDED}" -eq 0 ]]; then
  DO_DOWNLOAD=1
fi
if [[ "${DO_UNATTENDED}" -eq 1 ]]; then
  DO_DOWNLOAD=1
  DO_START=1
fi

[[ -f "${SSH_PUB}" ]] || { echo "Clé SSH absente : ${SSH_PUB}" >&2; exit 2; }

echo "=== Proxmox ${PVE} — VM ${VMID} (${IP}) Omarchy ${ISO_VERSION} ==="
echo "  storage=${STORAGE}  iso=${ISO_STORAGE}:${ISO_NAME}"
echo "  ${CORES} vCPU / ${MEMORY} Mo / ${DISK_GB} Go  mac=${MAC}"

if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo "(dry-run) stop"
  exit 0
fi

ssh -o BatchMode=yes -o ConnectTimeout=10 "root@${PVE}" "true" \
  || { echo "SSH root@${PVE} KO" >&2; exit 1; }

# --- espace disque ---
ssh -o BatchMode=yes "root@${PVE}" bash -s <<EOF
set -euo pipefail
# pvesm Available est en KiB
avail_kib=\$(pvesm status -storage ${STORAGE} 2>/dev/null | awk 'NR==2 {print \$6}')
need_kib=\$(( ${DISK_GB} * 1024 * 1024 ))
if [[ -n "\${avail_kib}" && "\${avail_kib}" =~ ^[0-9]+$ && "\${avail_kib}" -lt "\${need_kib}" ]]; then
  echo "Stockage ${STORAGE} insuffisant : \${avail_kib} KiB dispo < \${need_kib} KiB" >&2
  exit 3
fi
root_avail_mb=\$(df -BM --output=avail /var/lib/vz | awk 'NR==2 {gsub(/M/,""); print}')
if [[ "${DO_DOWNLOAD}" -eq 1 && -n "\${root_avail_mb}" && "\${root_avail_mb}" -lt 7000 ]]; then
  echo "Espace ISO (/var/lib/vz) insuffisant : \${root_avail_mb} Mo < 7000 Mo" >&2
  exit 3
fi
echo "OK espace ${STORAGE} + ISO store"
EOF

# --- download ISO ---
if [[ "${DO_DOWNLOAD}" -eq 1 ]]; then
  echo "=== ISO ${ISO_NAME} ==="
  ssh -o BatchMode=yes "root@${PVE}" bash -s <<EOF
set -euo pipefail
ISO_DIR="/var/lib/vz/template/iso"
mkdir -p "\${ISO_DIR}"
cd "\${ISO_DIR}"
if [[ -f "${ISO_NAME}" ]]; then
  echo -n "${ISO_SHA256}  ${ISO_NAME}" | sha256sum -c - && { echo "ISO déjà OK"; exit 0; }
  echo "Checksum KO — re-téléchargement"
  rm -f "${ISO_NAME}"
fi
echo "Téléchargement ${ISO_URL} (~6 Go)…"
curl -fL --retry 3 --continue-at - -o "${ISO_NAME}.part" "${ISO_URL}"
mv -f "${ISO_NAME}.part" "${ISO_NAME}"
echo -n "${ISO_SHA256}  ${ISO_NAME}" | sha256sum -c -
ls -lh "${ISO_NAME}"
EOF
fi

# --- cidata (unattended) ---
CIDATA_ATTACH=""
if [[ "${DO_UNATTENDED}" -eq 1 ]]; then
  PASS="${LBG_OMARCHY_PASSWORD:-}"
  SECRETS_FILE="${CORTEX_ROOT}/infra/secrets/omarchy-${VMID}.env.local"
  if [[ -z "${PASS}" && -f "${SECRETS_FILE}" ]]; then
    # shellcheck disable=SC1090
    PASS="$(grep -E '^LBG_OMARCHY_PASSWORD=' "${SECRETS_FILE}" | head -1 | cut -d= -f2-)"
  fi
  if [[ -z "${PASS}" ]]; then
    PASS="$(openssl rand -base64 18 | tr -d '/+=' | head -c 20)"
    umask 077
    cat >"${SECRETS_FILE}" <<SECRETS
# Généré $(date -Iseconds) — ne pas committer
LBG_OMARCHY_HOST=${IP}
LBG_OMARCHY_USER=${USERNAME}
LBG_OMARCHY_PASSWORD=${PASS}
LBG_OMARCHY_SSH_PUB=${SSH_PUB}
SECRETS
    echo "Mot de passe généré → ${SECRETS_FILE}"
  else
    echo "Mot de passe : env / ${SECRETS_FILE}"
  fi

  PASS_HASH="$(printf '%s' "${PASS}" | openssl passwd -6 -stdin)"
  PUBKEY="$(cat "${SSH_PUB}")"
  # VirtIO-SCSI Proxmox → /dev/sda (pas /dev/vda). Surcharge : LBG_OMARCHY_DISK_DEV.
  DISK_DEV="${LBG_OMARCHY_DISK_DEV:-/dev/sda}"
  # VirtIO disk Proxmox = scsi → /dev/sda ; layout Omarchy (boot 2 GiB + btrfs)
  DISK_BYTES=$((DISK_GB * 1024 * 1024 * 1024))
  MIB=$((1024 * 1024))
  GIB=$((MIB * 1024))
  DISK_SIZE_IN_MIB=$((DISK_BYTES / MIB * MIB))
  BOOT_START=${MIB}
  BOOT_SIZE=$((2 * GIB))
  MAIN_START=$((BOOT_SIZE + BOOT_START))
  MAIN_SIZE=$((DISK_SIZE_IN_MIB - MAIN_START - MIB))

  TMP_CIDATA="$(mktemp -d)"
  trap 'rm -rf "${TMP_CIDATA}"' EXIT

  cat >"${TMP_CIDATA}/user_configuration.json" <<JSON
{
  "app_config": null,
  "archinstall-language": "English",
  "auth_config": {},
  "audio_config": { "audio": "pipewire" },
  "bootloader": "Limine",
  "custom_commands": [],
  "disk_config": {
    "btrfs_options": {
      "snapshot_config": { "type": "Snapper" }
    },
    "config_type": "default_layout",
    "device_modifications": [
      {
        "device": "${DISK_DEV}",
        "partitions": [
          {
            "btrfs": [],
            "dev_path": null,
            "flags": ["boot", "esp"],
            "fs_type": "fat32",
            "mount_options": [],
            "mountpoint": "/boot",
            "obj_id": "ea21d3f2-82bb-49cc-ab5d-6f81ae94e18d",
            "size": {
              "sector_size": { "unit": "B", "value": 512 },
              "unit": "B",
              "value": ${BOOT_SIZE}
            },
            "start": {
              "sector_size": { "unit": "B", "value": 512 },
              "unit": "B",
              "value": ${BOOT_START}
            },
            "status": "create",
            "type": "primary"
          },
          {
            "btrfs": [
              { "mountpoint": "/", "name": "@" },
              { "mountpoint": "/home", "name": "@home" },
              { "mountpoint": "/var/log", "name": "@log" },
              { "mountpoint": "/var/cache/pacman/pkg", "name": "@pkg" }
            ],
            "dev_path": null,
            "flags": [],
            "fs_type": "btrfs",
            "mount_options": ["compress=zstd"],
            "mountpoint": null,
            "obj_id": "8c2c2b92-1070-455d-b76a-56263bab24aa",
            "size": {
              "sector_size": { "unit": "B", "value": 512 },
              "unit": "B",
              "value": ${MAIN_SIZE}
            },
            "start": {
              "sector_size": { "unit": "B", "value": 512 },
              "unit": "B",
              "value": ${MAIN_START}
            },
            "status": "create",
            "type": "primary"
          }
        ],
        "wipe": true
      }
    ]
  },
  "hostname": "${HOSTNAME}",
  "kernels": ["linux"],
  "network_config": { "type": "iso" },
  "ntp": true,
  "parallel_downloads": 8,
  "script": null,
  "services": [],
  "swap": true,
  "timezone": "${TIMEZONE}",
  "locale_config": {
    "kb_layout": "${KB_LAYOUT}",
    "sys_enc": "UTF-8",
    "sys_lang": "fr_FR.UTF-8"
  },
  "mirror_config": {
    "custom_repositories": [],
    "custom_servers": [
      {"url": "https://mirror.omarchy.org/\$repo/os/\$arch"},
      {"url": "https://mirror.rackspace.com/archlinux/\$repo/os/\$arch"},
      {"url": "https://geo.mirror.pkgbuild.com/\$repo/os/\$arch"}
    ],
    "mirror_regions": {},
    "optional_repositories": []
  },
  "packages": ["base-devel", "git", "omarchy-keyring", "snapper", "qemu-guest-agent"],
  "profile_config": {
    "gfx_driver": null,
    "greeter": null,
    "profile": {}
  },
  "version": "3.0.9"
}
JSON

  python3 -c '
import json, sys
enc, user = sys.argv[1], sys.argv[2]
json.dump({
  "root_enc_password": enc,
  "users": [{"enc_password": enc, "groups": [], "sudo": True, "username": user}],
}, sys.stdout, indent=2)
print()
' "${PASS_HASH}" "${USERNAME}" >"${TMP_CIDATA}/user_credentials.json"

  printf 'false\n' >"${TMP_CIDATA}/user_encrypt_installation.txt"
  printf 'LBG Omarchy\n' >"${TMP_CIDATA}/user_full_name.txt"
  printf 'lbg@laboiteageeks.fr\n' >"${TMP_CIDATA}/user_email_address.txt"
  printf '%s\n' "${PUBKEY}" >"${TMP_CIDATA}/authorized_keys"

  MKISO="$(command -v genisoimage || command -v mkisofs || true)"
  if [[ -z "${MKISO}" ]]; then
    echo "genisoimage/mkisofs requis pour cidata (apt install genisoimage)" >&2
    exit 2
  fi
  (
    cd "${TMP_CIDATA}"
    "${MKISO}" -quiet -output cidata.iso -volid cidata -joliet -rock \
      user_configuration.json user_credentials.json \
      user_encrypt_installation.txt user_full_name.txt \
      user_email_address.txt authorized_keys
  )

  scp -o BatchMode=yes "${TMP_CIDATA}/cidata.iso" \
    "root@${PVE}:/var/lib/vz/template/iso/omarchy-${VMID}-cidata.iso"
  CIDATA_ATTACH=1
  DO_START=1
  echo "cidata attaché (install unattended + SSH key)"
fi

# --- create VM ---
ssh -o BatchMode=yes "root@${PVE}" bash -s <<EOF
set -euo pipefail
VMID=${VMID}
HOSTNAME=${HOSTNAME}
STORAGE=${STORAGE}
ISO_STORAGE=${ISO_STORAGE}
ISO_NAME=${ISO_NAME}
MEMORY=${MEMORY}
CORES=${CORES}
DISK_GB=${DISK_GB}
BRIDGE=${BRIDGE}
MAC=${MAC}
ONBOOT=${ONBOOT}
CIDATA_ATTACH=${CIDATA_ATTACH:-0}

if qm status "\${VMID}" &>/dev/null; then
  echo "VM \${VMID} existe déjà — skip create"
  qm config "\${VMID}" | head -20
else
  qm create "\${VMID}" \\
    --name "\${HOSTNAME}" \\
    --memory "\${MEMORY}" \\
    --cores "\${CORES}" \\
    --sockets 1 \\
    --cpu host \\
    --bios ovmf \\
    --machine q35 \\
    --ostype l26 \\
    --scsihw virtio-scsi-single \\
    --efidisk0 "\${STORAGE}:1,efitype=4m,pre-enrolled-keys=0" \\
    --scsi0 "\${STORAGE}:\${DISK_GB},iothread=1,discard=on" \\
    --net0 "virtio,bridge=\${BRIDGE},macaddr=\${MAC}" \\
    --vga virtio,memory=64 \\
    --serial0 socket \\
    --agent enabled=1 \\
    --tablet 1 \\
    --onboot "\${ONBOOT}" \\
    --description "LBG Omarchy lab — IP cible ${IP} — docs/omarchy_vm_143.md"

  qm set "\${VMID}" --ide2 "\${ISO_STORAGE}:iso/\${ISO_NAME},media=cdrom"
  if [[ "\${CIDATA_ATTACH}" == "1" ]]; then
    qm set "\${VMID}" --ide3 "\${ISO_STORAGE}:iso/omarchy-\${VMID}-cidata.iso,media=cdrom"
    qm set "\${VMID}" --boot "order=scsi0;ide2;ide3"
  else
    qm set "\${VMID}" --boot "order=ide2;scsi0"
  fi
  echo "VM \${VMID} créée"
fi

qm config "\${VMID}"
EOF

if [[ "${DO_START}" -eq 1 ]]; then
  echo "=== Démarrage VM ${VMID} ==="
  ssh -o BatchMode=yes "root@${PVE}" "qm start ${VMID} || true; sleep 2; qm status ${VMID}"
fi

cat <<MSG

OK — VM ${VMID} sur ${PVE}
  Console : https://${PVE}:8006/ → ${HOSTNAME} (${VMID})
  IP cible (post-install) : ${IP}/24 gw ${GW} dns ${DNS}
  MAC réservation DHCP : ${MAC}

Post-install (dans le guest, une fois joignable) :
  sudo pacman -S --noconfirm qemu-guest-agent
  sudo systemctl enable --now qemu-guest-agent
  # IP fixe (NetworkManager) :
  #   nmcli con show
  #   sudo nmcli con mod <id> ipv4.method manual \\
  #     ipv4.addresses ${IP}/24 ipv4.gateway ${GW} ipv4.dns ${DNS}
  #   sudo nmcli con up <id>

Après install réussie (boot disque) :
  ssh root@${PVE} "qm set ${VMID} --ide2 none,media=cdrom --boot order=scsi0"
  # et détacher cidata si présent :
  # ssh root@${PVE} "qm set ${VMID} --delete ide3"

Doc : ${CORTEX_ROOT}/docs/omarchy_vm_143.md
MSG
