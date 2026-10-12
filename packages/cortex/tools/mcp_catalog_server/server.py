#!/usr/bin/env python3
"""MCP Studio — catalog C10 / tick C11 (read-only).

Outils :
  - ``catalog(type)`` — skills | recipes | npcs | poi
  - ``get_guide(playstyle)`` — guide hub
  - ``tick_matrix()`` — queries free vs mutations

Source de vérité : ``lbg_agents.agent_catalog`` (même contrat que ``:8020`` / ``:8791``).

Lancer (stdio — Cursor / Cline) ::

    cd packages/cortex
    PYTHONPATH=agents/src .venv/bin/python tools/mcp_catalog_server/server.py

Cursor ``mcp.json`` (extrait) ::

    {
      "mcpServers": {
        "lbg-catalog": {
          "command": "/home/lbg/Projets/LBG_Studios/packages/cortex/.venv/bin/python",
          "args": ["tools/mcp_catalog_server/server.py"],
          "cwd": "/home/lbg/Projets/LBG_Studios/packages/cortex",
          "env": { "PYTHONPATH": "agents/src" }
        }
      }
    }
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# packages/cortex/tools/mcp_catalog_server/server.py → cortex root
_CORTEX = Path(__file__).resolve().parents[2]
_AGENTS_SRC = _CORTEX / "agents" / "src"
if str(_AGENTS_SRC) not in sys.path:
    sys.path.insert(0, str(_AGENTS_SRC))

from mcp.server.fastmcp import FastMCP  # noqa: E402

from lbg_agents import agent_catalog as ac  # noqa: E402

mcp = FastMCP("lbg-catalog")


@mcp.tool()
def catalog(type: str = "skills") -> str:
    """Catalogue MMO read-only (C10). type ∈ skills|recipes|npcs|poi. tick_cost=free."""
    payload = ac.catalog(type)
    return json.dumps(payload, ensure_ascii=False, indent=2)


@mcp.tool()
def get_guide(playstyle: str = "prospecteur") -> str:
    """Guide playstyle hub (C10). playstyle ∈ prospecteur|artisan|scene|medecin|scout."""
    payload = ac.get_guide(playstyle)
    return json.dumps(payload, ensure_ascii=False, indent=2)


@mcp.tool()
def tick_matrix() -> str:
    """Table C11 : actions query (free) vs mutation (requires_tick)."""
    payload = ac.tick_matrix_payload()
    return json.dumps(payload, ensure_ascii=False, indent=2)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
