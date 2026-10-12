"""Collision Lost Heaven — AABB bâtiments + remparts (aligné ZoneLayers)."""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _default_buildings_path() -> Path:
    env = os.environ.get("LBG_HUB_BUILDINGS_JSON", "").strip()
    if env:
        return Path(env)
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "prime-client" / "assets" / "maps" / "lost_heaven_buildings.json",
        Path("/opt/lbg-hub-runtime/data/lost_heaven_buildings.json"),
    ]
    for p in candidates:
        if p.is_file():
            return p
    return candidates[0]


def _default_props_path() -> Path:
    env = os.environ.get("LBG_HUB_PROPS_JSON", "").strip()
    if env:
        return Path(env)
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "prime-client" / "assets" / "maps" / "lost_heaven_props.json",
        Path("/opt/lbg-hub-runtime/data/lost_heaven_props.json"),
    ]
    for p in candidates:
        if p.is_file():
            return p
    return candidates[0]


@dataclass
class BuildingBlock:
    id: str
    min_x: float
    max_x: float
    min_z: float
    max_z: float
    door: dict[str, float] | None = None

    def contains(self, x: float, z: float) -> bool:
        return self.min_x <= x <= self.max_x and self.min_z <= z <= self.max_z

    def in_door(self, x: float, z: float) -> bool:
        if not self.door:
            return False
        d = self.door
        return d["min_x"] <= x <= d["max_x"] and d["min_z"] <= z <= d["max_z"]


def _door_corridor(
    door: dict[str, Any], cx: float, cz: float, half: float
) -> dict[str, float]:
    face = str(door.get("face", "south")).lower()
    hw = float(door.get("width_m", 12.0)) * 0.5
    depth = float(door.get("depth_m", 14.0))
    apron = float(door.get("apron_m", 8.0))
    if face == "north":
        return {
            "min_x": cx - hw,
            "max_x": cx + hw,
            "min_z": cz + half - depth,
            "max_z": cz + half + apron,
        }
    if face == "south":
        return {
            "min_x": cx - hw,
            "max_x": cx + hw,
            "min_z": cz - half - apron,
            "max_z": cz - half + depth,
        }
    if face == "east":
        return {
            "min_x": cx + half - depth,
            "max_x": cx + half + apron,
            "min_z": cz - hw,
            "max_z": cz + hw,
        }
    return {
        "min_x": cx - half - apron,
        "max_x": cx - half + depth,
        "min_z": cz - hw,
        "max_z": cz + hw,
    }


def _segments_intersect(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float], d: tuple[float, float]) -> bool:
    def orient(p, q, r) -> float:
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    return orient(a, b, c) * orient(a, b, d) < 0 and orient(c, d, a) * orient(c, d, b) < 0


def _point_in_poly(x: float, z: float, ring: list[tuple[float, float]]) -> bool:
    n = len(ring)
    if n < 3:
        return False
    inside = False
    j = n - 1
    for i in range(n):
        xi, zi = ring[i]
        xj, zj = ring[j]
        if ((zi > z) != (zj > z)) and (x < (xj - xi) * (z - zi) / (zj - zi + 1e-9) + xi):
            inside = not inside
        j = i
    return inside


class HubCollision:
    """Bâtiments + remparts (portes = corridors)."""

    def __init__(
        self,
        buildings_path: Path | None = None,
        props_path: Path | None = None,
        size_mul: float = 1.0,
        enforce_fence: bool | None = None,
    ) -> None:
        self.path = buildings_path or _default_buildings_path()
        self.props_path = props_path or _default_props_path()
        self.size_mul = size_mul if size_mul > 0 else 1.0
        if enforce_fence is None:
            enforce_fence = os.environ.get("LBG_HUB_ENFORCE_FENCE", "1") not in {"0", "false", "False"}
        self.enforce_fence = bool(enforce_fence)
        self.blocks: list[BuildingBlock] = []
        self.fence_ring: list[tuple[float, float]] = []
        self.gate_exits: list[dict[str, Any]] = []
        self.open_fence_segments: set[int] = set()
        self.reload()

    def reload(self) -> None:
        self.blocks.clear()
        self.fence_ring.clear()
        self.gate_exits.clear()
        self.open_fence_segments.clear()
        if self.path.is_file():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                for item in raw.get("buildings") or []:
                    if not isinstance(item, dict):
                        continue
                    if str(item.get("kind", "")) == "city_gate":
                        continue
                    cx = float(item.get("x", 0.0))
                    cz = float(item.get("z", 0.0))
                    size_m = float(item.get("size_m", 32.0))
                    half = size_m * 0.5 * self.size_mul
                    door_raw = item.get("door")
                    door = (
                        _door_corridor(door_raw, cx, cz, half)
                        if isinstance(door_raw, dict)
                        else None
                    )
                    self.blocks.append(
                        BuildingBlock(
                            id=str(item.get("id", item.get("kind", "building"))),
                            min_x=cx - half,
                            max_x=cx + half,
                            min_z=cz - half,
                            max_z=cz + half,
                            door=door,
                        )
                    )
        if self.props_path.is_file():
            props = json.loads(self.props_path.read_text(encoding="utf-8"))
            if isinstance(props, dict):
                gates = props.get("gate_exits") or []
                if isinstance(gates, list):
                    self.gate_exits = [g for g in gates if isinstance(g, dict)]
                    for g in self.gate_exits:
                        for idx in g.get("fence_open_segment_indices") or []:
                            self.open_fence_segments.add(int(idx))
                for item in props.get("paths") or []:
                    if not isinstance(item, dict):
                        continue
                    if str(item.get("id", "")) != "path:lh_perimeter_fence":
                        continue
                    for pt in item.get("points") or []:
                        if isinstance(pt, dict):
                            self.fence_ring.append(
                                (float(pt.get("x", 0.0)), float(pt.get("z", 0.0)))
                            )
                    break

    def _in_gate_corridor(self, x: float, z: float) -> bool:
        for g in self.gate_exits:
            c = g.get("center") or {}
            if not isinstance(c, dict):
                continue
            gx = float(c.get("x", 0.0))
            gz = float(c.get("z", 0.0))
            hw = float(g.get("width_m", 16.0)) * 0.5
            axis = str(g.get("axis", "z")).lower()
            if axis == "x":
                east = float(g.get("depth_east_m", g.get("depth_m", 32.0)))
                west = float(g.get("depth_west_m", g.get("depth_m", 32.0)))
                if abs(z - gz) <= hw and gx - west <= x <= gx + east:
                    return True
            else:
                north = float(g.get("depth_north_m", g.get("depth_m", 32.0)))
                south = float(g.get("depth_south_m", g.get("depth_m", 32.0)))
                if abs(x - gx) <= hw and gz - south <= z <= gz + north:
                    return True
        return False

    def _fence_segment_open(self, seg_index: int) -> bool:
        if seg_index in self.open_fence_segments:
            return True
        n = len(self.fence_ring)
        if n < 2:
            return False
        i = seg_index % n
        j = (i + 1) % n
        mx = (self.fence_ring[i][0] + self.fence_ring[j][0]) * 0.5
        mz = (self.fence_ring[i][1] + self.fence_ring[j][1]) * 0.5
        for g in self.gate_exits:
            c = g.get("center") or {}
            if not isinstance(c, dict):
                continue
            gx = float(c.get("x", 0.0))
            gz = float(c.get("z", 0.0))
            hw = float(g.get("width_m", 16.0)) * 0.55
            if abs(mx - gx) <= hw and abs(mz - gz) <= 55.0:
                return True
        return False

    def _crosses_blocked_fence(self, fx: float, fz: float, tx: float, tz: float) -> bool:
        if not self.enforce_fence or len(self.fence_ring) < 3:
            return False
        # portes : libre
        if self._in_gate_corridor(tx, tz) or self._in_gate_corridor(fx, fz):
            # encore bloquer si on traverse un segment fermé hors corridor
            pass
        a, b = (fx, fz), (tx, tz)
        n = len(self.fence_ring)
        for i in range(n):
            if self._fence_segment_open(i):
                continue
            p1 = self.fence_ring[i]
            p2 = self.fence_ring[(i + 1) % n]
            if _segments_intersect(a, b, p1, p2):
                # autoriser si destination dans corridor de porte
                if self._in_gate_corridor(tx, tz):
                    continue
                return True
        return False

    def allows(self, x: float, z: float) -> bool:
        for b in self.blocks:
            if b.contains(x, z) and not b.in_door(x, z):
                return False
        return True

    def nearest_walkable(self, x: float, z: float, radius: float = 120.0) -> tuple[float, float]:
        if self.allows(x, z):
            return x, z
        best = None
        step = 5.0
        r = 5.0
        while r <= radius:
            for i in range(24):
                ang = (2.0 * math.pi * i) / 24.0
                cx = x + math.cos(ang) * r
                cz = z + math.sin(ang) * r
                if self.allows(cx, cz):
                    d = math.hypot(cx - x, cz - z)
                    if best is None or d < best[0]:
                        best = (d, cx, cz)
            if best is not None:
                return best[1], best[2]
            r += step
        return x, z

    def clamp_move(
        self, from_x: float, from_z: float, to_x: float, to_z: float
    ) -> tuple[float, float]:
        if self._crosses_blocked_fence(from_x, from_z, to_x, to_z):
            # slide
            if not self._crosses_blocked_fence(from_x, from_z, to_x, from_z) and self.allows(
                to_x, from_z
            ):
                return to_x, from_z
            if not self._crosses_blocked_fence(from_x, from_z, from_x, to_z) and self.allows(
                from_x, to_z
            ):
                return from_x, to_z
            return from_x, from_z
        if self.allows(to_x, to_z):
            return to_x, to_z
        if self.allows(to_x, from_z) and not self._crosses_blocked_fence(
            from_x, from_z, to_x, from_z
        ):
            return to_x, from_z
        if self.allows(from_x, to_z) and not self._crosses_blocked_fence(
            from_x, from_z, from_x, to_z
        ):
            return from_x, to_z
        return from_x, from_z

    def find_path(
        self,
        sx: float,
        sz: float,
        tx: float,
        tz: float,
        *,
        cell: float = 12.0,
        max_expand: int = 1200,
    ) -> list[tuple[float, float]]:
        """A* grille AABB — waypoints world (x,z). Vide si impossible."""
        import heapq

        sx, sz = self.nearest_walkable(sx, sz)
        tx, tz = self.nearest_walkable(tx, tz)
        if math.hypot(tx - sx, tz - sz) < cell * 0.5:
            return [(tx, tz)]

        def key(x: float, z: float) -> tuple[int, int]:
            return (int(round(x / cell)), int(round(z / cell)))

        def cell_center(i: int, j: int) -> tuple[float, float]:
            return (i * cell, j * cell)

        start = key(sx, sz)
        goal = key(tx, tz)
        if start == goal:
            return [(tx, tz)]

        open_h: list[tuple[float, int, int]] = []
        heapq.heappush(open_h, (0.0, start[0], start[1]))
        came: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
        gscore: dict[tuple[int, int], float] = {start: 0.0}
        expanded = 0
        found: tuple[int, int] | None = None
        neigh = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))

        while open_h and expanded < max_expand:
            _f, ci, cj = heapq.heappop(open_h)
            cur = (ci, cj)
            expanded += 1
            if cur == goal:
                found = cur
                break
            cx, cz = cell_center(ci, cj)
            for di, dj in neigh:
                ni, nj = ci + di, cj + dj
                nxt = (ni, nj)
                nx, nz = cell_center(ni, nj)
                if not self.allows(nx, nz):
                    continue
                if self._crosses_blocked_fence(cx, cz, nx, nz):
                    continue
                step = cell * (1.414 if di and dj else 1.0)
                ng = gscore[cur] + step
                if ng >= gscore.get(nxt, 1e18):
                    continue
                came[nxt] = cur
                gscore[nxt] = ng
                h = math.hypot(goal[0] - ni, goal[1] - nj) * cell
                heapq.heappush(open_h, (ng + h, ni, nj))

        if found is None:
            # fallback : un seul waypoint walkable vers la cible
            wx, wz = self.nearest_walkable(tx, tz)
            return [(wx, wz)] if abs(wx - sx) + abs(wz - sz) > 1.0 else []

        rev: list[tuple[int, int]] = []
        cur2: tuple[int, int] | None = found
        while cur2 is not None:
            rev.append(cur2)
            cur2 = came.get(cur2)
        rev.reverse()
        # sparsify : garder ~1 point sur 2 + fin exacte
        out: list[tuple[float, float]] = []
        for i, (ii, jj) in enumerate(rev):
            if i == 0:
                continue
            if i == len(rev) - 1 or i % 2 == 0:
                out.append(cell_center(ii, jj))
        if not out or math.hypot(out[-1][0] - tx, out[-1][1] - tz) > 1.0:
            out.append((tx, tz))
        return out

    def detour_waypoint(
        self, x: float, z: float, tx: float, tz: float
    ) -> tuple[float, float] | None:
        steps = 16
        for i in range(1, steps + 1):
            t = i / steps
            px = x + (tx - x) * t
            pz = z + (tz - z) * t
            for b in self.blocks:
                if b.contains(px, pz) and not b.in_door(px, pz):
                    pad = 6.0
                    candidates = [
                        (b.min_x - pad, b.min_z - pad),
                        (b.min_x - pad, b.max_z + pad),
                        (b.max_x + pad, b.min_z - pad),
                        (b.max_x + pad, b.max_z + pad),
                        (b.min_x - pad, (b.min_z + b.max_z) * 0.5),
                        (b.max_x + pad, (b.min_z + b.max_z) * 0.5),
                        ((b.min_x + b.max_x) * 0.5, b.min_z - pad),
                        ((b.min_x + b.max_x) * 0.5, b.max_z + pad),
                    ]
                    best = None
                    best_score = 1e18
                    for cx, cz in candidates:
                        if not self.allows(cx, cz):
                            continue
                        score = math.hypot(cx - x, cz - z) + math.hypot(tx - cx, tz - cz)
                        if score < best_score:
                            best_score = score
                            best = (cx, cz)
                    return best
        # pas de bâtiment sur le segment : pousser vers cible walkable
        wx, wz = self.nearest_walkable(tx, tz)
        if abs(wx - x) + abs(wz - z) > 1.0:
            return wx, wz
        return None


COLLISION = HubCollision()
