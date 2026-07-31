#!/usr/bin/env python3
"""
Gabarit Mos Eisley (retail .ws) → Lost Heaven + fusion tailles / refs.

Produit :
  - assets/maps/retail/tatooine/lost_heaven_retail_layout.json (overlay Ctrl+Shift+R)
  - assets/maps/lost_heaven_gabarit_me.json (référence éditable)
  - Met à jour size_m / retail_tmpl sur lost_heaven_buildings.json (sans écraser x/z LH)
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

PRIME = Path(__file__).resolve().parents[2]
ME_LAYOUT = PRIME / "assets/maps/retail/tatooine/mos_eisley_retail_layout.json"
LH_BUILDINGS = PRIME / "assets/maps/lost_heaven_buildings.json"
OUT_OVERLAY = PRIME / "assets/maps/retail/tatooine/lost_heaven_retail_layout.json"
OUT_REF = PRIME / "assets/maps/lost_heaven_gabarit_me.json"

ME_CENTER = (3520.0, -4800.0)
LH_ANCHOR = (4749.0, -737.0)

# tmpl retail → kind Lost Heaven (premier match)
TMPL_TO_KIND: list[tuple[str, str]] = [
    ("cantina_tatooine", "cantina"),
    ("starport", "starport_shuttle"),
    ("shuttleport", "starport_shuttle"),
    ("bank_tatooine", "bank"),
    ("cloning", "clinic"),
    ("hospital", "clinic"),
    ("medical", "clinic"),
    ("capitol", "town_hall"),
    ("guild_commerce", "shops"),
    ("guild_theater", "shops"),
    ("hotel", "inn"),
    ("salon", "inn"),
    ("mission", "mission_terminal"),
    ("lucky_despot", "market"),
    ("filler_building", "npc_housing_block"),
    ("guild_combat", "trainers_combat"),
    ("trainer", "trainers_combat"),
]


def kind_from_tmpl(tmpl: str) -> str:
    low = tmpl.lower()
    for needle, kind in TMPL_TO_KIND:
        if needle in low:
            return kind
    return "shops"


def shift(x: float, z: float) -> tuple[float, float]:
    return (
        round(LH_ANCHOR[0] + (x - ME_CENTER[0]), 2),
        round(LH_ANCHOR[1] + (z - ME_CENTER[1]), 2),
    )


def main() -> None:
    me = json.loads(ME_LAYOUT.read_text(encoding="utf-8"))
    lh_doc = json.loads(LH_BUILDINGS.read_text(encoding="utf-8"))
    lh_buildings: list[dict] = lh_doc.get("buildings", [])

    shifted_buildings: list[dict] = []
    shifted_markers: list[dict] = []
    for item in me.get("buildings", []):
        if not isinstance(item, dict):
            continue
        nx, nz = shift(float(item["x"]), float(item["z"]))
        shifted_buildings.append(
            {
                **item,
                "x": nx,
                "y": float(item.get("y", 5.0)),
                "z": nz,
                "city": "lost_heaven",
                "source_gabarit": "mos_eisley",
                "lh_kind": kind_from_tmpl(str(item.get("tmpl", ""))),
            }
        )
    for item in me.get("markers", []) + me.get("npcs", []):
        if not isinstance(item, dict):
            continue
        nx, nz = shift(float(item["x"]), float(item["z"]))
        kind = str(item.get("kind", "static"))
        rec = {**item, "x": nx, "z": nz, "city": "lost_heaven", "source_gabarit": "mos_eisley"}
        if kind == "npc":
            shifted_markers.append(rec)
        else:
            shifted_markers.append(rec)

    # Tailles retail → POI LH existants (par kind)
    by_kind: dict[str, list[float]] = {}
    for b in shifted_buildings:
        k = str(b.get("lh_kind", ""))
        by_kind.setdefault(k, []).append(float(b.get("size_m", 32.0)))

    kind_avg = {k: round(sum(v) / len(v), 1) for k, v in by_kind.items() if v}

    updated = 0
    for b in lh_buildings:
        k = str(b.get("kind", ""))
        if k in kind_avg:
            old = float(b.get("size_m", 32.0))
            new = max(old, kind_avg[k] * 0.85)
            if abs(new - old) > 0.5:
                b["size_m"] = round(new, 1)
                b["size_from_gabarit_me"] = True
                updated += 1

    lh_doc["buildings"] = lh_buildings
    lh_doc["gabarit_mos_eisley"] = {
        "applied_at": datetime.now(timezone.utc).isoformat(),
        "me_center": {"x": ME_CENTER[0], "z": ME_CENTER[1]},
        "lh_anchor": {"x": LH_ANCHOR[0], "z": LH_ANCHOR[1]},
        "buildings_resized": updated,
    }
    LH_BUILDINGS.write_text(json.dumps(lh_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    overlay = {
        "schema_version": 1,
        "zone": "tatooine",
        "city": "lost_heaven",
        "source": "gabarit_mos_eisley_shifted",
        "counts": {
            "total": len(shifted_buildings) + len(shifted_markers),
            "buildings": len(shifted_buildings),
            "npcs": len([m for m in shifted_markers if m.get("kind") == "npc"]),
            "statics": len([m for m in shifted_markers if m.get("kind") != "npc"]),
        },
        "buildings": shifted_buildings,
        "npcs": [m for m in shifted_markers if m.get("kind") == "npc"],
        "markers": [m for m in shifted_markers if m.get("kind") != "npc"],
    }
    OUT_OVERLAY.write_text(json.dumps(overlay, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    ref = {
        "schema_version": 1,
        "hub": "lost_heaven",
        "notes": "Gabarit ME décalé — comparer avec lost_heaven_buildings.json avant de figer x/z.",
        "anchor": {"x": LH_ANCHOR[0], "z": LH_ANCHOR[1]},
        "me_center": {"x": ME_CENTER[0], "z": ME_CENTER[1]},
        "buildings": shifted_buildings[:120],
    }
    OUT_REF.write_text(json.dumps(ref, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Overlay → {OUT_OVERLAY} ({len(shifted_buildings)} bâtiments ME décalés)")
    print(f"Référence → {OUT_REF}")
    print(f"lost_heaven_buildings.json : {updated} size_m ajustés")


if __name__ == "__main__":
    main()
