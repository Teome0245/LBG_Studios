#!/usr/bin/env python3
"""Exporte agent_catalog(type=poi) → packages/prime-hub/data/catalog_poi.json (G5)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

CORTEX = Path(__file__).resolve().parents[2]
AGENTS_SRC = CORTEX / "agents" / "src"
HUB_OUT = CORTEX.parent / "prime-hub" / "data" / "catalog_poi.json"


def main() -> int:
    sys.path.insert(0, str(AGENTS_SRC))
    from lbg_agents.agent_catalog import catalog  # noqa: E402

    payload = catalog("poi")
    if not isinstance(payload, dict) or not payload.get("ok"):
        print(f"ERR catalog poi: {payload}", file=sys.stderr)
        return 1
    count = int(payload.get("count") or 0)
    if count < 1:
        print("ERR: catalog poi count=0", file=sys.stderr)
        return 1
    HUB_OUT.parent.mkdir(parents=True, exist_ok=True)
    HUB_OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    ids = [str(i.get("id")) for i in (payload.get("items") or []) if isinstance(i, dict)]
    print(f"OK wrote {HUB_OUT} count={count}")
    for want in ("poi:lh_hunt_chacal", "poi:player_spawn", "poi:lh_scrap_pile"):
        print(f"  {'OK' if want in ids else 'MISS'} {want}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
