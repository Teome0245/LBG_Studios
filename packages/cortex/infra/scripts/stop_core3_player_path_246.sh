#!/usr/bin/env bash
# Coupe le chemin joueur Core3 (bots IA + gateway + autonomie) — hub Godot reste l'autorité.
# Ne coupe PAS lbg-hub-runtime (peel HTTP inventaire/quests/auth encore proxifié).
# Ne coupe PAS lbg-prime-hub.
#
# Usage:
#   bash packages/cortex/infra/scripts/stop_core3_player_path_246.sh
#   bash packages/cortex/infra/scripts/stop_core3_player_path_246.sh --also-prime
set -euo pipefail

HOST="${LBG_PRIME_HOST:-192.168.0.246}"
REMOTE="lbg@${HOST}"
ALSO_PRIME=0
[[ "${1:-}" == "--also-prime" ]] && ALSO_PRIME=1

UNITS=(
  lbg-core3-ia-bot-client.service
  lbg-core3-ia-bot-client-nix.service
  lbg-core3-ia-player@mira.service
  lbg-core3-ia-player@kael.service
  lbg-core3-ia-population-autonomy.service
  lbg-core3-ia-sidecar.service
  lbg-gateway.service
)

echo "==> Stop chemin joueur Core3 sur ${HOST}"
ssh -o BatchMode=yes -o ConnectTimeout=12 "${REMOTE}" bash -s <<REMOTE
set -euo pipefail
for u in ${UNITS[*]}; do
  if systemctl list-unit-files "\$u" &>/dev/null || systemctl status "\$u" &>/dev/null; then
    sudo systemctl disable --now "\$u" 2>/dev/null || sudo systemctl stop "\$u" 2>/dev/null || true
    echo "stopped \$u"
  fi
done
if [[ "${ALSO_PRIME}" == "1" ]]; then
  sudo systemctl disable --now lbg-core3-prime.service 2>/dev/null || true
  echo "stopped lbg-core3-prime (lab off)"
fi
echo "--- still running (attendu: prime-hub + hub-runtime peel) ---"
systemctl is-active lbg-prime-hub lbg-hub-runtime 2>/dev/null || true
ss -ltn | grep -E ':8787|:8789|:8797|:50000' || true
REMOTE

echo "OK — joueur = Godot :8787/:8789 ; peel Python :8797 ; Core3 bots/gateway off"
