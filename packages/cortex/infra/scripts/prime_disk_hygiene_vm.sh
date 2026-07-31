#!/usr/bin/env bash
# Nettoyage disque VM Prime (246) — artefacts build Antigravity / logs volumineux.
#
# Usage :
#   bash infra/scripts/prime_disk_hygiene_vm.sh
#   bash infra/scripts/prime_disk_hygiene_vm.sh --dry-run
#   bash infra/scripts/prime_disk_hygiene_vm.sh --remote-only   # déjà SSH sur 246

set -euo pipefail

VM_HOST="${LBG_NEW_MMO_VM_HOST:-${LBG_PRIME_VM_HOST:-192.168.0.246}}"
VM_USER="${LBG_NEW_MMO_VM_USER:-lbg}"
DRY=0
REMOTE_ONLY=0

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    --remote-only) REMOTE_ONLY=1 ;;
  esac
done

run_remote() {
  if [[ "${REMOTE_ONLY}" == "1" ]]; then
    bash -s
  else
    ssh "${VM_USER}@${VM_HOST}" "bash -s"
  fi
}

echo "=== Hygiène disque Prime (${VM_HOST}) ==="

run_remote <<EOF
set -euo pipefail
DRY=${DRY}
freed=0

clean_path() {
  local p="\$1"
  if [[ ! -e "\$p" ]]; then
    return 0
  fi
  local sz
  sz=\$(du -sb "\$p" 2>/dev/null | awk '{print \$1}')
  sz=\${sz:-0}
  if [[ "\$DRY" == "1" ]]; then
    echo "[dry-run] supprimerait \$p (\$(( sz / 1024 / 1024 )) Mo)"
  else
    rm -rf "\$p"
    echo "supprimé \$p (\$(( sz / 1024 / 1024 )) Mo)"
  fi
  freed=\$(( freed + sz ))
}

truncate_log() {
  local p="\$1"
  if [[ ! -f "\$p" ]]; then
    return 0
  fi
  local sz
  sz=\$(stat -c%s "\$p" 2>/dev/null || echo 0)
  if [[ "\$sz" -lt 1048576 ]]; then
    return 0
  fi
  if [[ "\$DRY" == "1" ]]; then
    echo "[dry-run] tronquerait \$p (\$(( sz / 1024 / 1024 )) Mo)"
  else
    : > "\$p"
    echo "tronqué \$p (\$(( sz / 1024 / 1024 )) Mo)"
  fi
  freed=\$(( freed + sz ))
}

clean_path /opt/lbg-antigravity/lbg-mmo/build
truncate_log /tmp/core3-antigravity-build.log

ZARCH="/opt/lbg-new-mmo-clean/MMOCoreORB/bin/log/zArchive"
if [[ -d "\$ZARCH" ]]; then
  if [[ "\$DRY" == "1" ]]; then
    echo "[dry-run] purgerait zArchive .log.1 (\$(du -sh \"\$ZARCH\" 2>/dev/null | awk '{print \$1}'))"
  else
    before=\$(du -sb "\$ZARCH" 2>/dev/null | awk '{print \$1}')
    before=\${before:-0}
    find "\$ZARCH" -type f \( -name '*.log.1' -o -name '*.log.[2-9]' -o -name '*.log.[0-9][0-9]*' \) -delete 2>/dev/null || true
    find "\$ZARCH" -type f -name '*.log.*.gz' -mtime +3 -delete 2>/dev/null || true
    find "\$ZARCH" -type f -name '*.log' -size +30M -exec truncate -s 0 {} + 2>/dev/null || true
    after=\$(du -sb "\$ZARCH" 2>/dev/null | awk '{print \$1}')
    after=\${after:-0}
    echo "zArchive purgé (\$(( (before - after) / 1024 / 1024 )) Mo libérés, reste \$(( after / 1024 / 1024 )) Mo)"
    freed=\$(( freed + before - after ))
  fi
fi

for alog in /var/log/auth.log /var/log/auth.log.1; do
  if [[ -f "\$alog" ]]; then
    sz=\$(stat -c%s "\$alog" 2>/dev/null || echo 0)
    if [[ "\$sz" -gt 1048576 ]]; then
      if [[ "\$DRY" == "1" ]]; then
        echo "[dry-run] tronquerait \$alog (\$(( sz / 1024 / 1024 )) Mo)"
      else
        sudo truncate -s 0 "\$alog" 2>/dev/null || true
        echo "tronqué \$alog (\$(( sz / 1024 / 1024 )) Mo)"
        freed=\$(( freed + sz ))
      fi
    fi
  fi
done

echo "--- df / ---"
df -h / | tail -1
echo "libéré ~\$(( freed / 1024 / 1024 )) Mo (thin pool Proxmox indirectement)"
EOF

if [[ "${REMOTE_ONLY}" != "1" ]]; then
  echo "Conseil : bash infra/scripts/check_proxmox_storage_lan.sh"
fi
