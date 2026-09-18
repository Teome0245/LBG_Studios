"""Bootstrap jeton desktop pour Compagnon (:5174) — LAN only.

Le navigateur peut avoir un vieux jeton localStorage qui ne match plus
``C:\\Agent_IA\\desktop.env``. Ce endpoint renvoie la valeur serveur
(``LBG_DESKTOP_APPROVAL_TOKEN`` dans ``/opt/orchestrateur/.env``), déjà
alignée avec l’agent Windows ``.10``.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["desktop"])

_ENV_CANDIDATES = (
    Path("/opt/orchestrateur/.env"),
    Path("/app/.env"),
)


def _load_token() -> str:
    env = (os.environ.get("LBG_DESKTOP_APPROVAL_TOKEN") or "").strip()
    if env:
        return env
    for p in _ENV_CANDIDATES:
        try:
            if not p.is_file():
                continue
            for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                if line.strip().startswith("LBG_DESKTOP_APPROVAL_TOKEN="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
        except OSError:
            continue
    return ""


def _client_is_lan(request: Request) -> bool:
    host = (request.client.host if request.client else "") or ""
    if host in ("127.0.0.1", "::1", "localhost"):
        return True
    if host.startswith("192.168."):
        return True
    if host.startswith("10."):
        return True
    # docker bridge
    if host.startswith("172."):
        return True
    return False


@router.get("/desktop-approval")
async def desktop_approval_bootstrap(request: Request) -> JSONResponse:
    if not _client_is_lan(request):
        return JSONResponse({"ok": False, "error": "lan_only"}, status_code=403)
    token = _load_token()
    if not token:
        return JSONResponse({"ok": False, "configured": False, "token": ""})
    return JSONResponse(
        {
            "ok": True,
            "configured": True,
            "token": token,
            "source": "server_env",
            "hint": "Aligné avec LBG_DESKTOP_APPROVAL_TOKEN (agent .10)",
        }
    )
