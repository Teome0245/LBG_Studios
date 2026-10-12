#!/usr/bin/env bash
# Remet marche visible + autonomie Lia/Nix sur Prime 246.
# Usage: bash infra/scripts/enable_ia_visible_walk_246.sh
set -euo pipefail
HOST="${LBG_PRIME_HOST:-192.168.0.246}"
BIN="${LBG_CORE3_BIN:-/opt/lbg-new-mmo-clean/MMOCoreORB/bin}"

ssh -o BatchMode=yes -o ConnectTimeout=10 "lbg@${HOST}" bash -s <<REMOTE
set -euo pipefail
BIN="${BIN}"
echo "=== movement_mode → walk ==="
echo walk | sudo tee "\${BIN}/ia_bridge/movement_mode" >/dev/null
cat "\${BIN}/ia_bridge/movement_mode"

# Env hub bot walk
sudo mkdir -p /etc/systemd/system/lbg-core3-ia-lia-autonomy.service.d
sudo mkdir -p /etc/systemd/system/lbg-core3-ia-player-autonomy@.service.d
sudo tee /etc/systemd/system/lbg-core3-ia-lia-autonomy.service.d/walk.conf >/dev/null <<EOF
[Service]
Environment=LBG_QUEST_HUB_BOT=1
Environment=LBG_QUEST_HUB_BOT_MOVEMENT=walk
Environment=LBG_CORE3_LIA_AUTONOMY_ENABLED=1
EOF
sudo tee /etc/systemd/system/lbg-core3-ia-player-autonomy@.service.d/walk.conf >/dev/null <<EOF
[Service]
Environment=LBG_QUEST_HUB_BOT=1
Environment=LBG_QUEST_HUB_BOT_MOVEMENT=walk
Environment=LBG_CORE3_PLAYER_AUTONOMY_ENABLED=1
EOF

sudo systemctl daemon-reload

echo "=== services ==="
for u in \\
  lbg-core3-ia-sidecar \\
  lbg-core3-ia-bot-client \\
  lbg-core3-ia-bot-client-nix \\
  lbg-core3-ia-lia-autonomy \\
  lbg-core3-ia-player-autonomy@nix \\
  lbg-core3-ia-population-autonomy
do
  if systemctl cat "\$u" &>/dev/null; then
    sudo systemctl enable --now "\$u" 2>/dev/null || sudo systemctl restart "\$u" || true
    echo -n "\$u: "; systemctl is-active "\$u" || true
  else
    echo "\$u: absent"
  fi
done

if systemctl list-timers --all | grep -q bots-ensure; then
  sudo systemctl start lbg-core3-ia-bots-ensure.timer 2>/dev/null || true
fi

sleep 2
echo "=== snapshots ==="
curl -sf "http://127.0.0.1:8791/healthz" | head -c 80; echo
for p in Nix Lia; do
  curl -sf "http://127.0.0.1:8791/v1/player-snapshot?player=\$p" 2>/dev/null | head -c 160 || echo "\$p: no snap"
  echo
done

echo "=== enqueue smoke Nix → marché ==="
curl -sf -X POST "http://127.0.0.1:8791/v1/enqueue" \\
  -H 'Content-Type: application/json' \\
  -d '{"action":"move_to","player":"Nix","x":4859.3,"y":-1008.3,"z":32,"message":"hub_visible_walk_smoke"}' || true
echo
echo "OK — reconnecte Godot ; Lia/Nix doivent bouger (pas serveur walk)."
REMOTE

echo "Done on ${HOST}"
