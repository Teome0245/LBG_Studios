#!/usr/bin/env python3
"""Smoke chat WS humain↔humain + /v1/say IA (Nix). Run on hub host."""
from __future__ import annotations

import asyncio
import json
import os
import urllib.request

import websockets

PORT = int(os.environ.get("LBG_HUB_RUNTIME_PORT", "8787"))
BASE = f"http://127.0.0.1:{PORT}"
URI = f"ws://127.0.0.1:{PORT}/ws"


def guest(name: str) -> dict:
    req = urllib.request.Request(
        BASE + "/v1/auth/guest",
        data=json.dumps({"player_name": name}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return json.load(urllib.request.urlopen(req, timeout=5))


async def drain(ws, n: int = 10, t: float = 0.35) -> None:
    for _ in range(n):
        try:
            await asyncio.wait_for(ws.recv(), timeout=t)
        except asyncio.TimeoutError:
            break


async def wait_chat(ws, needle: str, n: int = 20):
    for _ in range(n):
        raw = await asyncio.wait_for(ws.recv(), timeout=4)
        msg = json.loads(raw)
        if msg.get("type") == "chat" and needle in str(msg.get("text", "")):
            return msg
    return None


async def main() -> None:
    ga, gb = guest("SmokeChatA"), guest("SmokeChatB")
    assert ga.get("ok") and gb.get("ok"), (ga, gb)
    ta, tb = ga["session_token"], gb["session_token"]

    async with websockets.connect(URI, open_timeout=5) as a, websockets.connect(
        URI, open_timeout=5
    ) as b:
        await a.send(json.dumps({"type": "login", "proto": "lbg-ws/2", "session_token": ta}))
        await b.send(json.dumps({"type": "login", "proto": "lbg-ws/2", "session_token": tb}))
        await asyncio.wait_for(a.recv(), timeout=3)
        await asyncio.wait_for(b.recv(), timeout=3)
        await a.send(json.dumps({"type": "enter_world", "proto": "lbg-ws/2"}))
        await b.send(json.dumps({"type": "enter_world", "proto": "lbg-ws/2"}))
        await asyncio.wait_for(a.recv(), timeout=3)
        await asyncio.wait_for(b.recv(), timeout=3)
        # Nix greet (enter_world) — flotte peut envoyer plusieurs
        greet = await wait_chat(b, "bienvenue")
        assert greet and greet.get("source") == "ia", greet
        print("OK nix greet", greet.get("from"), greet.get("text"))
        # drain other fleet greets
        await drain(a, n=12)
        await drain(b, n=12)
        # humain → humain
        await a.send(json.dumps({"type": "chat", "proto": "lbg-ws/2", "text": "ping hub chat"}))
        peer = await wait_chat(b, "ping hub chat")
        assert peer and peer.get("source") == "human", peer
        print("OK human chat", peer.get("from"), peer.get("text"))
        await drain(a)
        await drain(b)

    # IA via HTTP /v1/say (Lia)
    async with websockets.connect(URI, open_timeout=5) as c:
        await c.send(json.dumps({"type": "login", "proto": "lbg-ws/2", "session_token": ta}))
        await asyncio.wait_for(c.recv(), timeout=3)
        await c.send(json.dumps({"type": "enter_world", "proto": "lbg-ws/2"}))
        await asyncio.wait_for(c.recv(), timeout=3)
        await drain(c, n=12)
        req = urllib.request.Request(
            BASE + "/v1/say",
            data=json.dumps({"player": "Lia", "text": "signal IA hub lia"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        http = json.load(urllib.request.urlopen(req, timeout=5))
        assert http.get("ok"), http
        ia = await wait_chat(c, "signal IA hub lia")
        assert ia and ia.get("source") == "ia" and ia.get("from") == "Lia", ia
        print("OK /v1/say IA", ia.get("from"), ia.get("text"))


if __name__ == "__main__":
    asyncio.run(main())
