#!/usr/bin/env python3
"""Client minimal Omarchy — Présence Agents (SSE ou Unix socket).

Usage::

    # SSE
    python presence_agents_client.py --sse http://127.0.0.1:5005/session/stream

    # Socket
    python presence_agents_client.py --socket $XDG_RUNTIME_DIR/lbg-presence-agents.sock
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import urllib.request


def listen_sse(url: str) -> None:
    req = urllib.request.Request(url, headers={"Accept": "text/event-stream"})
    with urllib.request.urlopen(req, timeout=None) as resp:  # noqa: S310 — lab LAN
        buf = ""
        while True:
            chunk = resp.read(256)
            if not chunk:
                break
            buf += chunk.decode("utf-8", errors="replace")
            while "\n\n" in buf:
                block, buf = buf.split("\n\n", 1)
                for line in block.split("\n"):
                    if line.startswith("data: "):
                        print(line[6:], flush=True)


def listen_socket(path: str) -> None:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(path)
    f = sock.makefile("r", encoding="utf-8")
    for line in f:
        line = line.strip()
        if line:
            print(line, flush=True)


def main() -> int:
    p = argparse.ArgumentParser(description="Présence Agents — client minimal")
    p.add_argument("--sse", help="URL SSE (ex. http://127.0.0.1:5005/session/stream)")
    p.add_argument(
        "--socket",
        help="Chemin Unix socket",
        default=os.environ.get("LBG_PRESENCE_AGENTS_SOCK")
        or os.path.join(os.environ.get("XDG_RUNTIME_DIR") or f"/tmp/lbg-{os.getuid()}", "lbg-presence-agents.sock"),
    )
    args = p.parse_args()
    try:
        if args.sse:
            listen_sse(args.sse)
        else:
            listen_socket(args.socket)
    except KeyboardInterrupt:
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
