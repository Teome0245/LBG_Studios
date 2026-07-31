#!/usr/bin/env python3
"""
Parse World Snapshot Core3 (WSNP / NODE) → objets plats.

Source : snapshot/tatooine.ws extrait des .tre (data_other_00.tre, etc.)
"""
from __future__ import annotations

import math
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SnapshotObject:
    object_id: int
    parent_id: int
    name_id: int
    cell_id: int
    x: float
    y: float  # hauteur Core3
    z: float
    game_object_type: float
    template: str = ""
    heading_deg: float = 0.0
    children: list["SnapshotObject"] = field(default_factory=list)


def _read_chunks(data: bytes, offset: int = 0, end: int | None = None) -> tuple[list[tuple[str, bytes]], int]:
    if end is None:
        end = len(data)
    chunks: list[tuple[str, bytes]] = []
    while offset + 8 <= end:
        tag = data[offset : offset + 4].decode("ascii", errors="replace")
        size = struct.unpack(">I", data[offset + 4 : offset + 8])[0]
        body = data[offset + 8 : offset + 8 + size]
        offset += 8 + size
        chunks.append((tag, body))
    return chunks, offset


def _parse_otnl(data: bytes) -> list[str]:
    if len(data) < 4:
        return []
    count = struct.unpack("<I", data[0:4])[0]
    names: list[str] = []
    off = 4
    for _ in range(count):
        if off >= len(data):
            break
        end = data.find(b"\x00", off)
        if end < 0:
            break
        names.append(data[off:end].decode("utf-8", errors="replace"))
        off = end + 1
    return names


def _parse_node_form(node_body: bytes, templates: list[str]) -> SnapshotObject | None:
    """node_body = contenu après tag NODE (FORM 0000 + DATA + enfants NODE)."""
    chunks, _ = _read_chunks(node_body)
    data_body: bytes | None = None
    child_node_bodies: list[bytes] = []
    for tag, chunk in chunks:
        if tag == "FORM" and len(chunk) >= 4:
            sub = chunk[0:4].decode("ascii", errors="replace")
            if sub == "0000":
                inner, _ = _read_chunks(chunk[4:])
                for it, ib in inner:
                    if it == "DATA":
                        data_body = ib
                    elif it == "FORM" and ib[0:4] == b"NODE":
                        child_node_bodies.append(ib[4:])
            elif sub == "NODE":
                child_node_bodies.append(chunk[4:])
        elif tag == "DATA":
            data_body = chunk
    if data_body is None or len(data_body) < 44:
        return None
    off = 0
    object_id = struct.unpack("<I", data_body[off : off + 4])[0]
    off += 4
    parent_id = struct.unpack("<I", data_body[off : off + 4])[0]
    off += 4
    name_id = struct.unpack("<I", data_body[off : off + 4])[0]
    off += 4
    cell_id = struct.unpack("<I", data_body[off : off + 4])[0]
    off += 4
    qw, qx, qy, qz = struct.unpack("<ffff", data_body[off : off + 16])
    off += 16
    px, pz, py = struct.unpack("<fff", data_body[off : off + 12])
    off += 12
    game_object_type = struct.unpack("<f", data_body[off : off + 4])[0]
    tmpl = templates[name_id] if 0 <= name_id < len(templates) else ""
    heading = math.degrees(math.atan2(2.0 * (qw * qy + qx * qz), 1.0 - 2.0 * (qy * qy + qz * qz)))
    # Core3 : read x,z,y puis initializePosition(getX(), getZ(), getY()) → (worldX, height, worldZ)
    node = SnapshotObject(
        object_id=object_id,
        parent_id=parent_id,
        name_id=name_id,
        cell_id=cell_id,
        x=round(px, 3),
        y=round(pz, 3),
        z=round(py, 3),
        game_object_type=game_object_type,
        template=tmpl,
        heading_deg=round(heading, 1),
    )
    for raw in child_node_bodies:
        child = _parse_node_form(raw, templates)
        if child:
            node.children.append(child)
    return node


def parse_ws_file(path: str | Path) -> tuple[list[SnapshotObject], list[str]]:
    raw = Path(path).read_bytes()
    if raw[0:4] != b"FORM" or raw[8:12] != b"WSNP":
        raise ValueError("Fichier .ws WSNP attendu")
    wsn_inner = raw[12:]
    if wsn_inner[0:4] != b"FORM":
        raise ValueError("FORM 0001 manquant")
    form_size = struct.unpack(">I", wsn_inner[4:8])[0]
    v1_payload = wsn_inner[8 : 8 + form_size]
    if v1_payload[0:4] != b"0001":
        raise ValueError("Version WSNP != 0001")
    templates: list[str] = []
    roots: list[SnapshotObject] = []

    chunks, _ = _read_chunks(v1_payload[4:])
    node_raws: list[bytes] = []
    for t2, c2 in chunks:
        if t2 == "OTNL":
            templates = _parse_otnl(c2)
        elif t2 == "FORM" and c2[0:4] == b"NODS":
            nods_chunks, _ = _read_chunks(c2[4:])
            for t3, c3 in nods_chunks:
                if t3 == "FORM" and c3[0:4] == b"NODE":
                    node_raws.append(c3[4:])
    for raw_node in node_raws:
        node = _parse_node_form(raw_node, templates)
        if node:
            roots.append(node)

    return roots, templates


def flatten_all(nodes: list[SnapshotObject]) -> list[SnapshotObject]:
    flat: list[SnapshotObject] = []

    def walk(n: SnapshotObject) -> None:
        flat.append(n)
        for c in n.children:
            walk(c)

    for r in nodes:
        walk(r)
    return flat


def outdoor_objects(nodes: list[SnapshotObject]) -> list[SnapshotObject]:
    return [o for o in flatten_all(nodes) if o.cell_id == 0]


def to_dict(obj: SnapshotObject) -> dict[str, Any]:
    return {
        "id": obj.object_id,
        "parent_id": obj.parent_id,
        "tmpl": obj.template,
        "x": obj.x,
        "y": obj.y,
        "z": obj.z,
        "cell": obj.cell_id,
        "got": obj.game_object_type,
        "heading_deg": obj.heading_deg,
    }
