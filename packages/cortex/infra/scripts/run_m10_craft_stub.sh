#!/usr/bin/env bash
# Lance le stub M10 craft (catalogue Studios + inventaire + combine).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
export LBG_M10_STUB_HOST="${LBG_M10_STUB_HOST:-127.0.0.1}"
export LBG_M10_STUB_PORT="${LBG_M10_STUB_PORT:-8791}"
export LBG_M10_CATALOG_JSON="${LBG_M10_CATALOG_JSON:-$ROOT/content/m10/m10_skills_catalog.json}"
export LBG_CORE3_IA_BRIDGE_DIR="${LBG_CORE3_IA_BRIDGE_DIR:-$ROOT/content/core3/ia_bridge}"
exec python3 "$ROOT/tools/m10_craft_stub/m10_craft_stub.py"
