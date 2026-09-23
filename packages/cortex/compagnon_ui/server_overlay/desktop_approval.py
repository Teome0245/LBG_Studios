"""Bootstrap approval Compagnon (:5174) — LAN only.

Modes :
- ``token`` (défaut) : renvoie ``LBG_DESKTOP_APPROVAL_TOKEN`` pour sync localStorage
- ``confirm`` (LAB) : pas de secret dans le navigateur — UI coche « Je confirme »
  → context ``desktop_approval=confirmed`` accepté par agents soft-confirm
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


def _approval_mode() -> str:
    """confirm | token — LAB sécurisé LAN → confirm par défaut si COMPAGNON_LAB."""
    raw = (os.environ.get("LBG_DESKTOP_APPROVAL_MODE") or "").strip().lower()
    if raw in ("confirm", "soft", "lab"):
        return "confirm"
    if raw in ("token", "secret"):
        return "token"
    soft = (os.environ.get("LBG_DESKTOP_SOFT_CONFIRM") or "").strip().lower()
    if soft in ("1", "true", "yes", "on"):
        return "confirm"
    lab = (os.environ.get("LBG_COMPAGNON_LAB") or "").strip().lower()
    if lab in ("1", "true", "yes", "on"):
        return "confirm"
    return "token"


def _client_is_lan(request: Request) -> bool:
    host = (request.client.host if request.client else "") or ""
    if host in ("127.0.0.1", "::1", "localhost"):
        return True
    if host.startswith("192.168."):
        return True
    if host.startswith("10."):
        return True
    if host.startswith("172."):
        return True
    return False


@router.get("/desktop-approval")
async def desktop_approval_bootstrap(request: Request) -> JSONResponse:
    if not _client_is_lan(request):
        return JSONResponse({"ok": False, "error": "lan_only"}, status_code=403)
    mode = _approval_mode()
    if mode == "confirm":
        return JSONResponse(
            {
                "ok": True,
                "configured": True,
                "mode": "confirm",
                "token": "",
                "sentinel": "confirmed",
                "source": "lab_soft_confirm",
                "hint": "LAB : confirmation UI (pas de jeton navigateur)",
            }
        )
    token = _load_token()
    if not token:
        return JSONResponse(
            {"ok": False, "configured": False, "mode": "token", "token": ""}
        )
    return JSONResponse(
        {
            "ok": True,
            "configured": True,
            "mode": "token",
            "token": token,
            "source": "server_env",
            "hint": "Aligné avec LBG_DESKTOP_APPROVAL_TOKEN (agent .10)",
        }
    )
