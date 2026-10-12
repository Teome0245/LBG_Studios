#!/usr/bin/env bash
# Smoke spike hub_runtime (hors Core3) — HTTP + WS zone_state.
# Usage: bash tools/hub_runtime/smoke_hub_runtime.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
export PYTHONPATH="${ROOT}/agents/src:${ROOT}${PYTHONPATH:+:$PYTHONPATH}"
HOST="${LBG_HUB_RUNTIME_HOST:-127.0.0.1}"
PORT="${LBG_HUB_RUNTIME_PORT:-8787}"
BASE="http://${HOST}:${PORT}"
WS="ws://${HOST}:${PORT}/ws"

PY="${ROOT}/.venv/bin/python"
[[ -x "$PY" ]] || PY=python3

echo "=== start hub_runtime ==="
"$PY" -m tools.hub_runtime.server &
PID=$!
cleanup() { kill "$PID" 2>/dev/null || true; }
trap cleanup EXIT
sleep 1.5

echo "=== healthz ==="
curl -sf "${BASE}/healthz" | head -c 200
echo

echo "=== catalog / tick-matrix ==="
curl -sf "${BASE}/catalog?type=skills" | head -c 120
echo
curl -sf "${BASE}/tick-matrix" | head -c 120
echo

echo "=== WS login + zone_state (websockets) ==="
"$PY" - <<PY
import asyncio, json, sys
try:
    import websockets
except ImportError:
    print("SKIP ws: pip install websockets")
    sys.exit(0)

async def main():
    uri = "${WS}"
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"type": "login", "proto": "lbg-ws/2", "session_token": "spike"}))
        r1 = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
        assert r1.get("type") == "login_result" and r1.get("success"), r1
        await ws.send(json.dumps({"type": "enter_world", "proto": "lbg-ws/2", "zone": "scrapaltai"}))
        r2 = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
        assert r2.get("type") == "enter_world", r2
        assert r2.get("your_character_id") == 100001
        ents = r2.get("entities") or []
        names = {e.get("name") for e in ents if isinstance(e, dict)}
        assert "Nix" in names, names
        # wait a few zone_state — Nix must move
        nix0 = next(e for e in ents if e.get("name") == "Nix")
        p0 = list(nix0["pos"])
        moved = False
        for _ in range(25):
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=3))
            if msg.get("type") != "zone_state":
                continue
            for e in msg.get("entities") or []:
                if e.get("name") == "Nix":
                    p1 = e["pos"]
                    if abs(p1[0]-p0[0]) > 0.5 or abs(p1[2]-p0[2]) > 0.5:
                        moved = True
                        print("Nix moved", [round(x,1) for x in p0], "->", [round(x,1) for x in p1])
                        break
            if moved:
                break
        assert moved, "Nix did not move"
        print("OK smoke hub_runtime")

asyncio.run(main())
PY

echo "=== done ==="
