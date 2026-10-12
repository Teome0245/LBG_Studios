#!/usr/bin/env bash
# Smoke visuel statique Prime Client : mode runtime sprites/portraits + manifests.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PRIME_ROOT="${LBG_PRIME_CLIENT_ROOT:-${ROOT_DIR}/../prime-client}"

if [[ ! -d "${PRIME_ROOT}" ]]; then
  echo "FAIL: prime-client introuvable: ${PRIME_ROOT}" >&2
  exit 2
fi

CFG="${PRIME_ROOT}/assets/maps/scrapaltai_map_config.json"
SPRITES="${PRIME_ROOT}/config/sprite_manifest.json"
PORTRAITS="${PRIME_ROOT}/config/dialogue_portraits.json"

python3 - <<'PY' "${CFG}" "${SPRITES}" "${PORTRAITS}"
import json
import sys
from pathlib import Path

cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
sprites = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
portraits = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))

style = str(((cfg.get("world_render") or {}).get("entity_markers")) or "").strip()
if style not in {"runtime_sprite", "sprite"}:
    raise SystemExit(f"FAIL: entity_markers={style!r} (attendu runtime_sprite/sprite)")

sprite_ok = bool(sprites.get("sprites"))
portrait_ok = bool((portraits.get("portraits") or {}).get("npc_default_neutral"))
if not sprite_ok:
    raise SystemExit("FAIL: sprite_manifest sans sprites")
if not portrait_ok:
    raise SystemExit("FAIL: dialogue_portraits sans npc_default_neutral")

print(f"OK visual smoke — entity_markers={style} sprites=yes portraits=yes")
PY
