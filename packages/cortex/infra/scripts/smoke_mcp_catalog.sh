#!/usr/bin/env bash
# Smoke MCP catalog (même logique outils, sans daemon stdio).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
export PYTHONPATH="${ROOT}/agents/src${PYTHONPATH:+:${PYTHONPATH}}"
PY="${ROOT}/.venv/bin/python"
[[ -x "$PY" ]] || PY=python3

"$PY" -c '
import json
from lbg_agents import agent_catalog as ac
c = ac.catalog("skills")
assert c.get("ok") and c.get("tick_cost") == "free", c
g = ac.get_guide("artisan")
assert g.get("ok"), g
t = ac.tick_matrix_payload()
assert t.get("ok") and t.get("count", 0) >= 10, t
# import MCP server module (registers tools)
import importlib.util
spec = importlib.util.spec_from_file_location(
    "mcp_catalog_server",
    "tools/mcp_catalog_server/server.py",
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
assert hasattr(mod, "catalog") and hasattr(mod, "get_guide") and hasattr(mod, "tick_matrix")
print("SMOKE_MCP_CATALOG_OK", json.dumps({
    "skills": c["count"],
    "guide": g["guide"]["playstyle"],
    "tick": t["count"],
}))
'
