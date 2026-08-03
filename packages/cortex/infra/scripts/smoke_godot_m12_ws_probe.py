#!/usr/bin/env python3
"""Probe WS M12 — login → select → zone_state/enter_world → move (±1.5 m).

Env :
  WS_URL, TOKEN, CHAR_ID
  LBG_M12_MOVE_TOL_M (défaut 1.5)
  LBG_M12_MOVE_DX / LBG_M12_MOVE_DZ (offset cible, défaut 2 / 1)
"""
from __future__ import annotations

import asyncio
import json
import math
import os
import sys


def _parse_pos(raw):
    if raw is None:
        return None
    if isinstance(raw, dict):
        return float(raw.get("x", 0)), float(raw.get("y", 0)), float(raw.get("z", 0))
    if isinstance(raw, (list, tuple)) and len(raw) >= 3:
        return float(raw[0]), float(raw[1]), float(raw[2])
    return None


def _ids_match(a, b) -> bool:
    if a is None or b is None:
        return False
    if a == b:
        return True
    try:
        return int(a) == int(b)
    except (TypeError, ValueError):
        return str(a) == str(b)


def find_me(msg: dict, cid: int):
    yid = msg.get("your_character_id")
    if _ids_match(yid, cid):
        pos = _parse_pos(msg.get("position"))
        if pos is not None:
            return pos, int(msg.get("cell") or 0), "top"
    for ent in msg.get("entities") or []:
        if not isinstance(ent, dict):
            continue
        eid = ent.get("id") or ent.get("character_id") or ent.get("oid")
        if not _ids_match(eid, cid) and not _ids_match(eid, yid):
            continue
        pos = _parse_pos(ent.get("pos") or ent.get("position"))
        if pos is not None:
            return pos, int(ent.get("cell") or msg.get("cell") or 0), "ent"
    return None, 0, None


async def probe() -> None:
    import websockets

    url = os.environ["WS_URL"]
    token = os.environ["TOKEN"]
    cid = int(os.environ["CHAR_ID"])
    tol = float(os.environ.get("LBG_M12_MOVE_TOL_M", "1.5"))
    dx = float(os.environ.get("LBG_M12_MOVE_DX", "2.0"))
    dz = float(os.environ.get("LBG_M12_MOVE_DZ", "1.0"))

    async with websockets.connect(url, open_timeout=8) as ws:
        await ws.send(json.dumps({"type": "login", "proto": "lbg-ws/2", "session_token": token}))
        raw = await asyncio.wait_for(ws.recv(), timeout=8)
        msg = json.loads(raw)
        if not (msg.get("type") == "login_result" and msg.get("success") is True):
            raise SystemExit(f"login_result fail: {msg}")

        await ws.send(
            json.dumps({"type": "select_character", "proto": "lbg-ws/2", "character_id": cid})
        )

        my_pos = None
        cell = 0
        for _ in range(10):
            raw = await asyncio.wait_for(ws.recv(), timeout=8)
            msg = json.loads(raw)
            if msg.get("type") not in ("enter_world", "zone_state"):
                continue
            pos, cell, src = find_me(msg, cid)
            n_ents = len(msg.get("entities") or [])
            print(
                f"zone ok type={msg.get('type')} your_character_id={msg.get('your_character_id')} "
                f"entities={n_ents} pos={pos} src={src}"
            )
            if pos is not None:
                my_pos = pos
                break
        if my_pos is None:
            raise SystemExit("pas de enter_world/zone_state avec position")

        x, y, z = my_pos
        nx, ny, nz = x + dx, y, z + dz
        move = {
            "type": "move",
            "proto": "lbg-ws/2",
            "pos": [nx, ny, nz],
            "heading": 0.5,
            "cell": int(cell or 0),
            "seq": 1,
        }
        await ws.send(json.dumps(move))
        print(f"move sent target=({nx:.3f},{ny:.3f},{nz:.3f}) seq=1")

        for _ in range(20):
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=3)
            except asyncio.TimeoutError:
                break
            msg = json.loads(raw)
            if msg.get("type") not in ("zone_state", "enter_world", "move_ack"):
                continue
            pos, _, src = find_me(msg, cid)
            if pos is None:
                continue
            dist = math.sqrt((pos[0] - nx) ** 2 + (pos[2] - nz) ** 2)
            print(f"post-move type={msg.get('type')} pos={pos} dist={dist:.3f} src={src}")
            if dist <= tol:
                print(
                    f"OK M12 — login→WS→zone_state→move dist={dist:.3f}m "
                    f"char={cid} entities={len(msg.get('entities') or [])}"
                )
                return
        raise SystemExit(f"move non confirmé (tol={tol}m)")


def main() -> int:
    try:
        asyncio.run(probe())
    except ImportError:
        print("websockets manquant", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"FAIL M12: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
