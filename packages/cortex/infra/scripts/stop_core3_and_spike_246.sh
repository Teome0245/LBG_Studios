#!/usr/bin/env bash
# Coupe COMPLÈTEMENT Core3 + spike Python hub_runtime sur .246.
# Conserve : lbg-prime-hub (Godot :8787) + lbg-client-patch (:8080) + MCP.
#
# Usage:
#   bash packages/cortex/infra/scripts/stop_core3_and_spike_246.sh
#   bash packages/cortex/infra/scripts/stop_core3_and_spike_246.sh --keep-account-admin
set -euo pipefail

HOST="${LBG_PRIME_HOST:-192.168.0.246}"
REMOTE="lbg@${HOST}"
KEEP_ADMIN=0
[[ "${1:-}" == "--keep-account-admin" ]] && KEEP_ADMIN=1

TIMERS=(
  lbg-core3-ia-bots-ensure.timer
  lbg-core3-prime-watchdog.timer
  lbg-core3-prime-soe-login-watchdog.timer
  lbg-core3-inventory-export.timer
  lbg-world-export-agent.timer
)

UNITS=(
  lbg-hub-runtime.service
  lbg-gateway.service
  lbg-core3-ia-bot-client.service
  lbg-core3-ia-bot-client-nix.service
  lbg-core3-ia-population-autonomy.service
  lbg-core3-ia-sidecar.service
  lbg-core3-ia-bots-ensure.service
  lbg-core3-prime-watchdog.service
  lbg-core3-prime-soe-login-watchdog.service
  lbg-core3-inventory-export.service
  lbg-world-export-agent.service
  lbg-core3-prime.service
)

echo "==> Cut Core3 + spike Python sur ${HOST}"
ssh -o BatchMode=yes -o ConnectTimeout=12 "${REMOTE}" bash -s <<REMOTE
set -euo pipefail
for t in ${TIMERS[*]}; do
  sudo systemctl disable --now "\$t" 2>/dev/null || true
  echo "timer off \$t"
done
# instances template
for u in lbg-core3-ia-player@mira.service lbg-core3-ia-player@kael.service; do
  sudo systemctl disable --now "\$u" 2>/dev/null || true
done
for u in ${UNITS[*]}; do
  sudo systemctl disable --now "\$u" 2>/dev/null || sudo systemctl stop "\$u" 2>/dev/null || true
  echo "stopped \$u"
done
if [[ "${KEEP_ADMIN}" != "1" ]]; then
  sudo systemctl disable --now lbg-core3-account-admin.service 2>/dev/null || true
  echo "stopped lbg-core3-account-admin"
fi
echo "--- attendu: prime-hub + patch (+ mcp) ---"
systemctl is-active lbg-prime-hub lbg-client-patch lbg-mcp-linux 2>/dev/null || true
systemctl is-active lbg-hub-runtime lbg-core3-prime lbg-gateway lbg-core3-ia-sidecar 2>/dev/null || true
ss -ltn | grep -E ':8787|:8080|:8791|:8792|:8797|:50000|:8765' || true
curl -sf --max-time 3 http://127.0.0.1:8787/healthz | head -c 180 || true
echo
REMOTE

echo "OK — joueur = Godot :8787 only ; Core3 + spike Python coupés"
