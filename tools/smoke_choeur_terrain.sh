#!/usr/bin/env bash
# Smoke Chœur V50–V53 — truth guard offline + P3 live optionnel
# Usage: bash tools/smoke_choeur_terrain.sh [--skip-live]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HUB="${LBG_PRIME_HUB_URL:-http://192.168.0.246:8787}"
HUB="${HUB%/}"
SKIP_LIVE=0
for a in "$@"; do
  [[ "$a" == "--skip-live" ]] && SKIP_LIVE=1
done

echo "== world_truth_guard (offline) =="
cd "$ROOT/packages/cortex/orchestrator"
PYTHONPATH=. "${ROOT}/packages/cortex/.venv/bin/python" -c '
from team.player_ia_world_guard import run_world_truth_guard
g = run_world_truth_guard()
assert g.get("ok") is True, g
print("ok checks=", len(g.get("checks") or []), "enabled=", g.get("enabled"))
for c in g.get("checks") or []:
    if not c.get("ok"):
        raise SystemExit(f"FAIL {c}")
'

echo "== player_ia_probe hub =="
cd "$ROOT/packages/cortex/orchestrator"
LBG_PLAYER_IA_PROBE_MODE=hub LBG_PRIME_HUB_URL="$HUB" \
  PYTHONPATH=. "${ROOT}/packages/cortex/.venv/bin/python" -c '
import os
from team.player_ia_probe import probe_player_ia
r = probe_player_ia()
print("ok=", r.get("ok"), "mode=", r.get("mode"), "online=", r.get("online_count"), "hub=", r.get("hub"))
assert r.get("mode") == "hub", r
tg = [c for c in (r.get("checks") or []) if c.get("kind") == "world_truth_guard"]
assert tg and tg[0].get("ok") is True, tg
# healthz hub requis ; bots soft si LAN offline
hz = [c for c in (r.get("checks") or []) if c.get("kind") == "hub_healthz"]
assert hz, r
if hz[0].get("ok"):
    assert r.get("ok") is True, r
else:
    print("WARN hub offline — truth_guard seul compte pour ce run")
'

if [[ "$SKIP_LIVE" -eq 1 ]]; then
  echo "SMOKE_CHOEUR_TERRAIN_OK (skip-live)"
  exit 0
fi

if curl -sf --max-time 5 "$HUB/healthz" >/dev/null; then
  echo "== P3 dialogue live (V53) =="
  bash "$ROOT/tools/smoke_p3_hub_dialogue.sh" "$HUB"
else
  echo "WARN: hub $HUB unreachable — skip P3 live"
fi

echo "SMOKE_CHOEUR_TERRAIN_OK"
