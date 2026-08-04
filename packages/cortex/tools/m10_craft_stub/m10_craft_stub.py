#!/usr/bin/env python3
"""M10 craft stub — catalogue schema 3 + inventaire + POST /v1/craft/combine.

Boucle locale (sans Core3) pour P2. Logique partagée : ``m10_craft_runtime``.

Usage :
  python3 packages/cortex/tools/m10_craft_stub/m10_craft_stub.py
  LBG_M10_STUB_PORT=8791 python3 …/m10_craft_stub.py
"""
from __future__ import annotations

import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

TOOLS = Path(__file__).resolve().parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import m10_craft_runtime as runtime  # noqa: E402

HOST = os.environ.get("LBG_M10_STUB_HOST", "127.0.0.1")
PORT = int(os.environ.get("LBG_M10_STUB_PORT", "8791"))
DEFAULT_PLAYER = runtime.DEFAULT_PLAYER


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[m10_stub] {self.address_string()} {fmt % args}")

    def _send(self, code: int, payload: dict[str, Any]) -> None:
        import json

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        import json

        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            return {}
        return data if isinstance(data, dict) else {}

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        qs = parse_qs(parsed.query)
        player = (qs.get("player") or [DEFAULT_PLAYER])[0]
        cat = runtime.ensure_catalog()

        if path in ("/healthz", "/health"):
            self._send(
                200,
                {
                    "ok": True,
                    "service": "m10_craft_stub",
                    "catalog": str(runtime.catalog_path()),
                    "schema_version": cat.get("schema_version"),
                },
            )
            return

        if path in ("/v1/catalog/skills", "/v1/catalog/schematics"):
            skills = [s for s in (cat.get("skills") or []) if isinstance(s, dict)]
            schematics = [sc for sc in (cat.get("schematics") or []) if isinstance(sc, dict)]
            shown = [s for s in skills if s.get("status") != "draft"]
            shown_sc = [sc for sc in schematics if sc.get("status") != "draft"]
            self._send(
                200,
                {
                    "ok": True,
                    "track": cat.get("track", "m10_talents_craft"),
                    "schema_version": cat.get("schema_version"),
                    "fallback": False,
                    "source": "m10_craft_stub",
                    "catalog_path": str(runtime.catalog_path()),
                    "skills": shown,
                    "schematics": shown_sc,
                },
            )
            return

        if path == "/v1/inventory":
            self._send(200, runtime.inventory_payload(player))
            return

        if path == "/v1/player/skills":
            self._send(200, runtime.player_skills_payload(player))
            return

        self._send(404, {"ok": False, "error": "not_found", "path": path})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        body = self._read_json()
        player = str(body.get("player") or DEFAULT_PLAYER)

        if path == "/v1/craft/combine":
            sid = str(body.get("schematic_id") or body.get("schematic") or "")
            if not sid:
                self._send(400, {"ok": False, "error": "schematic_id_required"})
                return
            result = runtime.craft_combine(player, sid)
            self._send(200 if result.get("ok") else 400, result)
            return

        if path == "/v1/inventory/reset":
            state = runtime.reset_player(player)
            self._send(200, {"ok": True, **state})
            return

        self._send(404, {"ok": False, "error": "not_found", "path": path})


def main() -> None:
    if not runtime.catalog_path().is_file():
        raise SystemExit(f"Catalogue introuvable: {runtime.catalog_path()}")
    runtime.load_catalog()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(
        f"[m10_stub] listening http://{HOST}:{PORT} "
        f"catalog={runtime.catalog_path()} schema={runtime.ensure_catalog().get('schema_version')}"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[m10_stub] stop")
        server.server_close()


if __name__ == "__main__":
    main()
