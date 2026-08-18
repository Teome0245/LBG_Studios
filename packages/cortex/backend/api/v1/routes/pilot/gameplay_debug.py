"""Commits gameplay monde (réputation, inventaire, aid) sans LLM."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Header, HTTPException

from config import get_settings
from services.mmmorpg_commit import try_commit_dialogue

from ._common import httpx, require_internal_token
from ._models import AidRequest, OkEnvelope

router = APIRouter()

@router.post("/reputation", tags=["pilot"], response_model=OkEnvelope)
async def pilot_commit_reputation(
    payload: dict[str, object],
    x_lbg_service_token: str | None = Header(default=None, alias="X-LBG-Service-Token"),
) -> dict[str, object]:
    """
    Applique un `reputation_delta` via le serveur WS (HTTP interne), sans passer par le LLM.

    Body (JSON) :
      - npc_id: str (ex. "npc:merchant")
      - delta: int (borné [-100, 100])
    """
    npc_id = (payload.get("npc_id") if isinstance(payload, dict) else None)  # type: ignore[truthy-bool]
    delta = (payload.get("delta") if isinstance(payload, dict) else None)  # type: ignore[truthy-bool]
    if not isinstance(npc_id, str) or not npc_id.strip():
        raise HTTPException(status_code=400, detail={"error": "bad_request", "hint": "npc_id requis"})
    try:
        d = int(delta)  # accepte "11"
    except Exception:
        raise HTTPException(status_code=400, detail={"error": "bad_request", "hint": "delta int requis"})
    if d < -100 or d > 100:
        raise HTTPException(status_code=400, detail={"error": "bad_request", "hint": "delta hors bornes [-100,100]"})

    # Même protection optionnelle que `/v1/pilot/internal/route` (utile si on expose `/pilot/` sur le LAN).
    # Important : après validation du body pour que les erreurs 400 restent observables même si un token est requis.
    require_internal_token(x_lbg_service_token)

    trace_id = uuid.uuid4().hex
    # Réutiliser le canal commit existant (HTTP interne mmmorpg_server) + filtrage backend.
    commit_result = await try_commit_dialogue(trace_id=trace_id, npc_id=npc_id.strip(), flags={"reputation_delta": d})
    if commit_result is None:
        return {"ok": False, "trace_id": trace_id, "attempted": False, "error": "commit_disabled"}

    # Best-effort : garder le fallback `mmo_world` cohérent (si activé).
    mmo_base = get_settings().lbg_mmo_server_url.strip().rstrip("/")
    if mmo_base:
        mmo_token = get_settings().lbg_mmo_internal_token.strip()
        headers = {"X-LBG-Service-Token": mmo_token} if mmo_token else None
        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                await client.post(
                    f"{mmo_base}/internal/v1/npc/{npc_id.strip()}/reputation",
                    json={"delta": d, "trace_id": trace_id},
                    headers=headers,
                )
        except Exception:
            # Ne jamais casser la route pilote si le monde HTTP est indispo.
            pass

    return {"ok": True, "trace_id": trace_id, "commit_result": commit_result}


@router.post("/player-inventory", tags=["pilot"], response_model=OkEnvelope)
async def pilot_commit_player_inventory(
    payload: dict[str, object],
    x_lbg_service_token: str | None = Header(default=None, alias="X-LBG-Service-Token"),
) -> dict[str, object]:
    """
    Applique ``player_item_id`` + ``player_item_qty_delta`` (+ ``player_item_label`` optionnel)
    via le HTTP interne du serveur WS, **sans** LLM.

    Body (JSON) :
      - ``npc_id`` : PNJ « contexte » du commit (même mécanisme que les autres commits dialogue).
      - ``player_id`` : UUID joueur session WS (``welcome.player_id``).
      - ``item_id`` : id d’objet (≤ 64 car. côté serveur jeu).
      - ``qty_delta`` : entier non nul, borné **[-50, 50]** (aligné ``mmmorpg_server``).
      - ``label`` : optionnel (≤ 80 car.), utile quand une nouvelle pile est créée.
    """
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail={"error": "bad_request", "hint": "JSON objet requis"})

    npc_id = payload.get("npc_id")
    player_id = payload.get("player_id")
    item_id = payload.get("item_id")
    qty_raw = payload.get("qty_delta")
    label_raw = payload.get("label")

    if not isinstance(npc_id, str) or not npc_id.strip():
        raise HTTPException(status_code=400, detail={"error": "bad_request", "hint": "npc_id requis"})
    if not isinstance(player_id, str) or not player_id.strip():
        raise HTTPException(status_code=400, detail={"error": "bad_request", "hint": "player_id requis (UUID WS)"})
    if not isinstance(item_id, str) or not item_id.strip():
        raise HTTPException(status_code=400, detail={"error": "bad_request", "hint": "item_id requis"})
    try:
        qd = int(qty_raw)  # type: ignore[arg-type]
    except Exception:
        raise HTTPException(status_code=400, detail={"error": "bad_request", "hint": "qty_delta entier requis"})
    if qd == 0:
        raise HTTPException(status_code=400, detail={"error": "bad_request", "hint": "qty_delta non nul"})
    if qd < -50 or qd > 50:
        raise HTTPException(status_code=400, detail={"error": "bad_request", "hint": "qty_delta hors [-50,50]"})

    iid = item_id.strip()
    if len(iid) > 64:
        raise HTTPException(status_code=400, detail={"error": "bad_request", "hint": "item_id trop long"})

    flags: dict[str, object] = {"player_item_id": iid, "player_item_qty_delta": qd}
    if label_raw is not None and isinstance(label_raw, str):
        lab = label_raw.strip()
        if lab:
            if len(lab) > 80:
                raise HTTPException(status_code=400, detail={"error": "bad_request", "hint": "label trop long"})
            flags["player_item_label"] = lab

    require_internal_token(x_lbg_service_token)

    trace_id = uuid.uuid4().hex
    commit_result = await try_commit_dialogue(
        trace_id=trace_id,
        npc_id=npc_id.strip(),
        flags=flags,
        player_id=player_id.strip(),
    )
    if commit_result is None:
        return {"ok": False, "trace_id": trace_id, "attempted": False, "error": "commit_disabled"}

    return {"ok": True, "trace_id": trace_id, "commit_result": commit_result}


@router.post("/aid", tags=["pilot"], response_model=OkEnvelope)
async def pilot_apply_aid_to_world(
    payload: AidRequest,
    x_lbg_service_token: str | None = Header(default=None, alias="X-LBG-Service-Token"),
) -> dict[str, object]:
    """
    Gameplay v1 (monde) : applique des deltas sur un PNJ via `mmo_server` (LAN).
    Protégé par le même token optionnel que `/v1/pilot/internal/route` (LBG_PILOT_INTERNAL_TOKEN).
    """
    npc_id = (payload.npc_id or "").strip()
    if not npc_id:
        raise HTTPException(status_code=400, detail={"error": "bad_request", "hint": "npc_id requis"})

    # Validation d'inputs avant le gate token pour garder des 400 utiles.
    if payload.reputation_delta < -100 or payload.reputation_delta > 100:
        raise HTTPException(
            status_code=400,
            detail={"error": "bad_request", "hint": "reputation_delta hors bornes [-100,100]"},
        )
    for name in ("hunger_delta", "thirst_delta", "fatigue_delta"):
        v = float(getattr(payload, name))
        if v < -1.0 or v > 1.0:
            raise HTTPException(status_code=400, detail={"error": "bad_request", "hint": f"{name} hors bornes [-1,1]"})

    require_internal_token(x_lbg_service_token)

    base = get_settings().lbg_mmo_server_url.strip().rstrip("/")
    if not base:
        raise HTTPException(status_code=400, detail={"error": "bad_request", "hint": "LBG_MMO_SERVER_URL non défini"})

    trace_id = uuid.uuid4().hex
    mmo_token = get_settings().lbg_mmo_internal_token.strip()
    headers = {"X-LBG-Service-Token": mmo_token} if mmo_token else None
    body = {
        "hunger_delta": float(payload.hunger_delta),
        "thirst_delta": float(payload.thirst_delta),
        "fatigue_delta": float(payload.fatigue_delta),
        "reputation_delta": int(payload.reputation_delta),
        "trace_id": trace_id,
    }
    try:
        async with httpx.AsyncClient(timeout=2.5) as client:
            r = await client.post(
                f"{base}/internal/v1/npc/{npc_id}/aid",
                json=body,
                headers=headers,
            )
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail={"error": "upstream_error", "body": r.text[:500]})
        try:
            data = r.json()
        except ValueError:
            raise HTTPException(status_code=502, detail={"error": "upstream_non_json", "body": r.text[:500]})
        return {"ok": True, "trace_id": trace_id, "world_result": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail={"error": "upstream_unreachable", "detail": str(e)})
