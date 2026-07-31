#!/usr/bin/env python3
"""
Export layouts retail Tatooine (snapshot .ws) → JSON Godot par ville.

Les emprises vertes du client retail viennent surtout des bâtiments + objets
statiques du World Snapshot ; les PNJ dynamiques nécessitent un export serveur
(snapshots / scripts) en complément.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

# Villes Tatooine (centre Core3 x/z — calage SWG / city_regions)
CITIES: dict[str, dict[str, float]] = {
    "mos_eisley": {"x": 3520.0, "z": -4800.0, "radius_m": 520.0},
    "bestine": {"x": -1200.0, "z": -3700.0, "radius_m": 450.0},
    "anchorhead": {"x": -100.0, "z": -5300.0, "radius_m": 380.0},
    "mos_espa": {"x": -2900.0, "z": 2200.0, "radius_m": 480.0},
    "mos_entha": {"x": 1200.0, "z": 3200.0, "radius_m": 450.0},
    "mos_taike": {"x": 3800.0, "z": 2300.0, "radius_m": 400.0},
    "wayfar": {"x": -5200.0, "z": -6500.0, "radius_m": 350.0},
}

SIZE_M_HINTS: list[tuple[str, float]] = [
    ("starport", 64.0),
    ("shuttleport", 48.0),
    ("cantina", 36.0),
    ("cloning", 28.0),
    ("hospital", 36.0),
    ("medical", 32.0),
    ("bank", 32.0),
    ("hotel", 36.0),
    ("guild", 40.0),
    ("capitol", 44.0),
    ("salon", 28.0),
    ("tavern", 32.0),
    ("market", 48.0),
    ("parking", 40.0),
    ("wall_pristine", 12.0),
    ("pillar", 8.0),
    ("filler", 24.0),
]


def _import_parser():
    root = Path(__file__).resolve().parents[2]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from tools.retail.ws_core3_parser import parse_ws_file

    return parse_ws_file


def _quat_yaw_deg(qw: float, qx: float, qy: float, qz: float) -> float:
    return math.degrees(math.atan2(2.0 * (qw * qy + qx * qz), 1.0 - 2.0 * (qy * qy + qz * qz)))


@dataclass
class Transform:
    x: float
    y: float
    z: float
    yaw: float

    def compose(self, local_x: float, local_z: float, local_y: float, local_yaw: float) -> "Transform":
        cy = math.cos(math.radians(self.yaw))
        sy = math.sin(math.radians(self.yaw))
        wx = self.x + local_x * cy - local_z * sy
        wz = self.z + local_x * sy + local_z * cy
        wy = self.y + local_y
        return Transform(wx, wy, wz, self.yaw + local_yaw)


def _size_for_template(tmpl: str) -> float:
    low = tmpl.lower()
    for key, sz in SIZE_M_HINTS:
        if key in low:
            return sz
    if "/building/" in low:
        return 32.0
    if "/mobile/" in low:
        return 4.0
    return 10.0


def _kind_for_template(tmpl: str) -> str:
    low = tmpl.lower()
    if "/building/" in low or "shared_building" in low:
        return "building"
    if "/mobile/" in low or "/creature/" in low or "dressed_" in low:
        return "npc"
    if "terminal" in low or "mission" in low or "bank" in low:
        return "terminal"
    if "/static/" in low or "/tangible/" in low:
        return "static"
    return "other"


def _label_from_template(tmpl: str) -> str:
    base = tmpl.split("/")[-1].replace(".iff", "")
    base = re.sub(r"^shared_", "", base)
    return base.replace("_", " ")


def _assign_city(x: float, z: float) -> str:
    best = "wilderness"
    best_d = 1.0e12
    for cid, c in CITIES.items():
        dx = x - c["x"]
        dz = z - c["z"]
        d = math.hypot(dx, dz)
        if d <= c["radius_m"] and d < best_d:
            best_d = d
            best = cid
    return best


def _walk_world(node, parent: Transform, out: list[dict]) -> None:
    local_yaw = node.heading_deg
    world = parent.compose(node.x, node.z, node.y, local_yaw)
    tmpl = node.template
    kind = _kind_for_template(tmpl)
    if tmpl and node.cell_id == 0:
        out.append(
            {
                "id": node.object_id,
                "parent_id": node.parent_id,
                "tmpl": tmpl,
                "label": _label_from_template(tmpl),
                "kind": kind,
                "x": round(world.x, 2),
                "y": round(world.y, 2),
                "z": round(world.z, 2),
                "size_m": _size_for_template(tmpl),
                "heading_deg": round(world.yaw, 1),
                "city": _assign_city(world.x, world.z),
            }
        )
    child_tf = Transform(world.x, world.y, world.z, world.yaw)
    for ch in node.children:
        _walk_world(ch, child_tf, out)


def export_planet(ws_path: Path, out_dir: Path) -> dict[str, int]:
    parse_ws_file = _import_parser()
    roots, _templates = parse_ws_file(ws_path)
    flat: list[dict] = []
    for root in roots:
        if root.cell_id != 0:
            continue
        tmpl = root.template
        if not tmpl:
            continue
        kind = _kind_for_template(tmpl)
        if kind not in ("building", "npc", "terminal"):
            continue
        flat.append(
            {
                "id": root.object_id,
                "parent_id": root.parent_id,
                "tmpl": tmpl,
                "label": _label_from_template(tmpl),
                "kind": kind,
                "x": round(root.x, 2),
                "y": round(root.y, 2),
                "z": round(root.z, 2),
                "size_m": _size_for_template(tmpl),
                "heading_deg": root.heading_deg,
                "city": _assign_city(root.x, root.z),
            }
        )

    by_city: dict[str, list[dict]] = defaultdict(list)
    for item in flat:
        by_city[item["city"]].append(item)

    out_dir.mkdir(parents=True, exist_ok=True)
    summary: dict[str, int] = {}
    for city, items in sorted(by_city.items()):
        buildings = [i for i in items if i["kind"] == "building"]
        npcs = [i for i in items if i["kind"] == "npc"]
        statics = [i for i in items if i["kind"] in ("static", "terminal")]
        payload = {
            "schema_version": 1,
            "zone": "tatooine",
            "city": city,
            "source": "retail_world_snapshot",
            "ws_file": str(ws_path.name),
            "counts": {
                "total": len(items),
                "buildings": len(buildings),
                "npcs": len(npcs),
                "statics": len(statics),
            },
            "buildings": buildings,
            "npcs": npcs,
            "markers": statics,
        }
        out_path = out_dir / f"{city}_retail_layout.json"
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        summary[city] = len(items)

    all_path = out_dir / "tatooine_retail_all.json"
    all_path.write_text(
        json.dumps(
            {"schema_version": 1, "zone": "tatooine", "objects": flat, "cities": summary},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description="Export snapshot retail → JSON villes Godot")
    ap.add_argument("ws_file", type=Path, help="snapshot/tatooine.ws")
    ap.add_argument(
        "-o",
        "--out",
        type=Path,
        default=Path("assets/maps/retail/tatooine"),
        help="Dossier sortie (relatif prime-client)",
    )
    args = ap.parse_args()
    if not args.ws_file.is_file():
        raise SystemExit(f"Fichier absent: {args.ws_file}")
    summary = export_planet(args.ws_file, args.out)
    print(f"Export OK → {args.out}")
    for city, n in sorted(summary.items(), key=lambda x: -x[1]):
        print(f"  {city}: {n} objets")


if __name__ == "__main__":
    main()
