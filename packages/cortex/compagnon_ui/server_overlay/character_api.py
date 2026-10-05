"""API Character Compagnon — dials lab + snapshot pack.

Routes :
  GET  /character/
  GET  /character/dials
  PUT  /character/dials
  POST /character/catchphrases
  GET  /character/voice-smoke
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.services.character_layer import (
    DIAL_KEYS,
    character_public_snapshot,
    clamp_dials,
    list_catchphrases,
    load_dials,
    load_pack,
    remember_catchphrase,
    save_dials,
    voice_smoke_cases,
)
from src.services.router_prompts import lab_env_enabled

router = APIRouter(prefix="/character", tags=["character"])


class DialsBody(BaseModel):
    dials: dict[str, float] = Field(default_factory=dict)
    lab: bool | None = None


class CatchphraseBody(BaseModel):
    text: str = ""
    tags: list[str] = Field(default_factory=list)


def _lab_flag(explicit: bool | None) -> bool:
    if explicit is not None:
        return bool(explicit)
    return lab_env_enabled()


@router.get("/")
async def character_root() -> dict[str, Any]:
    return character_public_snapshot(lab=_lab_flag(None))


@router.get("/dials")
async def get_dials(lab: bool | None = None) -> dict[str, Any]:
    lab_on = _lab_flag(lab)
    pack = load_pack()
    return {
        "ok": True,
        "lab": lab_on,
        "keys": list(DIAL_KEYS),
        "dials": load_dials(lab=lab_on),
        "defaults": clamp_dials(None, lab=lab_on, pack=pack),
        "meta": (pack.get("character") or {}).get("dials_meta") or {},
    }


@router.put("/dials")
async def put_dials(body: DialsBody) -> dict[str, Any]:
    lab_on = _lab_flag(body.lab)
    saved = save_dials(body.dials or {}, lab=lab_on)
    return {"ok": True, "lab": lab_on, "dials": saved}


@router.post("/catchphrases")
async def post_catchphrase(body: CatchphraseBody) -> dict[str, Any]:
    ok = remember_catchphrase(body.text, tags=list(body.tags or []))
    return {
        "ok": ok,
        "catchphrases": list_catchphrases(limit=12),
    }


@router.get("/voice-smoke")
async def get_voice_smoke() -> dict[str, Any]:
    return {"ok": True, "cases": voice_smoke_cases()}
