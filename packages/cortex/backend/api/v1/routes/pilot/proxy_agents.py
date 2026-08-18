"""Proxies same-origin vers agents dialogue/quests/combat et mmo_server."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from config import get_settings

from ._common import httpx, pilot_agent_dialogue_invoke_timeout_s
from ._models import AgentDialogueInvokeBody, OkEnvelope

router = APIRouter()

@router.get("/agent-dialogue/healthz", tags=["pilot"], response_model=OkEnvelope)
async def pilot_proxy_agent_dialogue_healthz() -> OkEnvelope:
    """
    Proxy same-origin vers l’agent dialogue : évite d’exposer 8020 au navigateur (CORS / firewall).
    """
    base = get_settings().lbg_agent_dialogue_url.strip().rstrip("/")
    if not base:
        return {"ok": False, "skipped": True, "detail": "LBG_AGENT_DIALOGUE_URL non défini"}
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{base}/healthz")
        if r.status_code != 200:
            return {"ok": False, "error": f"HTTP {r.status_code}", "body": r.text[:500]}
        try:
            data = r.json()
        except ValueError:
            return {"ok": False, "error": "corps non JSON", "body": r.text[:500]}
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/agent-dialogue/npc-registry", tags=["pilot"])
async def pilot_proxy_agent_dialogue_npc_registry(npc_id: str | None = None) -> dict[str, object]:
    """
    Proxy same-origin vers `GET agent-dialogue /npc-registry`.
    Option : `?npc_id=npc:...` pour filtrer une entrée.
    """
    base = get_settings().lbg_agent_dialogue_url.strip().rstrip("/")
    if not base:
        return {"ok": False, "skipped": True, "detail": "LBG_AGENT_DIALOGUE_URL non défini"}
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{base}/npc-registry", params={"npc_id": npc_id} if npc_id else None)
        if r.status_code != 200:
            return {"ok": False, "error": f"HTTP {r.status_code}", "body": r.text[:800]}
        try:
            data = r.json()
        except ValueError:
            return {"ok": False, "error": "corps non JSON", "body": r.text[:800]}
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/agent-dialogue/world-content", tags=["pilot"])
async def pilot_proxy_agent_dialogue_world_content() -> dict[str, object]:
    """
    Proxy same-origin vers `GET agent-dialogue /world-content` (inventaire races + bestiaire).
    """
    base = get_settings().lbg_agent_dialogue_url.strip().rstrip("/")
    if not base:
        return {"ok": False, "skipped": True, "detail": "LBG_AGENT_DIALOGUE_URL non défini"}
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{base}/world-content")
        if r.status_code != 200:
            return {"ok": False, "error": f"HTTP {r.status_code}", "body": r.text[:800]}
        try:
            data = r.json()
        except ValueError:
            return {"ok": False, "error": "corps non JSON", "body": r.text[:800]}
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}



@router.post("/agent-dialogue/invoke", tags=["pilot"])
async def pilot_proxy_agent_dialogue_invoke(body: AgentDialogueInvokeBody) -> dict[str, object]:
    """
    Proxy same-origin vers `POST {LBG_AGENT_DIALOGUE_URL}/invoke` (LLM dialogue + meta).

    Utile pour le Pilot (ex. proposition `DESKTOP_JSON` → édition humaine → `/v1/pilot/route`).
    Rang2 §5 MVP : enrichit ``session_summary`` depuis sidecar ``/v1/quest-state`` si manquant.
    """
    base = get_settings().lbg_agent_dialogue_url.strip().rstrip("/")
    if not base:
        raise HTTPException(
            status_code=400,
            detail={"error": "bad_request", "hint": "LBG_AGENT_DIALOGUE_URL non défini"},
        )
    url = f"{base}/invoke"
    context = dict(body.context) if isinstance(body.context, dict) else {}
    try:
        from backend.services.session_quest_enrich import merge_quest_into_session_summary

        context = merge_quest_into_session_summary(context, actor_id=body.actor_id)
    except Exception:
        pass
    payload = {"actor_id": body.actor_id, "text": body.text, "context": context}
    try:
        async with httpx.AsyncClient(timeout=pilot_agent_dialogue_invoke_timeout_s()) as client:
            r = await client.post(url, json=payload)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={"error": "upstream_unreachable", "detail": str(e)},
        ) from e
    try:
        data = r.json()
    except ValueError:
        raise HTTPException(
            status_code=502,
            detail={"error": "upstream_non_json", "body": r.text[:800]},
        )
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=data if isinstance(data, dict) else {"body": r.text[:800]})
    return data if isinstance(data, dict) else {"payload": data}


@router.get("/agent-quests/healthz", tags=["pilot"], response_model=OkEnvelope)
async def pilot_proxy_agent_quests_healthz() -> OkEnvelope:
    """Proxy same-origin vers l’agent quests (port 8030 typiquement)."""
    base = get_settings().lbg_agent_quests_url.strip().rstrip("/")
    if not base:
        return {"ok": False, "skipped": True, "detail": "LBG_AGENT_QUESTS_URL non défini"}
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{base}/healthz")
        if r.status_code != 200:
            return {"ok": False, "error": f"HTTP {r.status_code}", "body": r.text[:500]}
        try:
            data = r.json()
        except ValueError:
            return {"ok": False, "error": "corps non JSON", "body": r.text[:500]}
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/agent-combat/healthz", tags=["pilot"], response_model=OkEnvelope)
async def pilot_proxy_agent_combat_healthz() -> OkEnvelope:
    """Proxy same-origin vers l'agent combat (port 8040 typiquement)."""
    base = get_settings().lbg_agent_combat_url.strip().rstrip("/")
    if not base:
        return {"ok": False, "skipped": True, "detail": "LBG_AGENT_COMBAT_URL non défini"}
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{base}/healthz")
        if r.status_code != 200:
            return {"ok": False, "error": f"HTTP {r.status_code}", "body": r.text[:500]}
        try:
            data = r.json()
        except ValueError:
            return {"ok": False, "error": "corps non JSON", "body": r.text[:500]}
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/agent-pm/healthz", tags=["pilot"], response_model=OkEnvelope)
async def pilot_proxy_agent_pm_healthz() -> OkEnvelope:
    """Proxy same-origin vers l’agent chef de projet (port 8055 typiquement)."""
    base = get_settings().lbg_agent_pm_url.strip().rstrip("/")
    if not base:
        return {"ok": False, "skipped": True, "detail": "LBG_AGENT_PM_URL non défini"}
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{base}/healthz")
        if r.status_code != 200:
            return {"ok": False, "error": f"HTTP {r.status_code}", "body": r.text[:500]}
        try:
            data = r.json()
        except ValueError:
            return {"ok": False, "error": "corps non JSON", "body": r.text[:500]}
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/agent-desktop/healthz", tags=["pilot"], response_model=OkEnvelope)
async def pilot_proxy_agent_desktop_healthz() -> OkEnvelope:
    """Proxy same-origin vers l’agent desktop Windows (hybride)."""
    base = get_settings().lbg_agent_desktop_url.strip().rstrip("/")
    if not base:
        return {"ok": False, "skipped": True, "detail": "LBG_AGENT_DESKTOP_URL non défini"}
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{base}/healthz")
        if r.status_code != 200:
            return {"ok": False, "error": f"HTTP {r.status_code}", "body": r.text[:500]}
        try:
            data = r.json()
        except ValueError:
            return {"ok": False, "error": "corps non JSON", "body": r.text[:500]}
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/mmo-server/healthz", tags=["pilot"], response_model=OkEnvelope)
async def pilot_proxy_mmo_server_healthz() -> OkEnvelope:
    """Proxy same-origin vers le serveur MMO HTTP (tick monde + /v1/world/lyra)."""
    base = get_settings().lbg_mmo_server_url.strip().rstrip("/")
    if not base:
        return {"ok": False, "skipped": True, "detail": "LBG_MMO_SERVER_URL non défini"}
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{base}/healthz")
        if r.status_code != 200:
            return {"ok": False, "error": f"HTTP {r.status_code}", "body": r.text[:500]}
        try:
            data = r.json()
        except ValueError:
            return {"ok": False, "error": "corps non JSON", "body": r.text[:500]}
        return {"ok": True, **data} if isinstance(data, dict) else {"ok": True, "payload": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/mmo-server/world-lyra", tags=["pilot"])
async def pilot_proxy_mmo_server_world_lyra(npc_id: str) -> dict[str, object]:
    """Proxy same-origin vers `GET /v1/world/lyra` sur `mmo_server`."""
    base = get_settings().lbg_mmo_server_url.strip().rstrip("/")
    if not base:
        raise HTTPException(status_code=400, detail={"error": "bad_request", "hint": "LBG_MMO_SERVER_URL non défini"})
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{base}/v1/world/lyra", params={"npc_id": npc_id})
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail={"error": "upstream_error", "body": r.text[:500]})
        try:
            data = r.json()
        except ValueError:
            raise HTTPException(status_code=502, detail={"error": "upstream_non_json", "body": r.text[:500]})
        return data if isinstance(data, dict) else {"payload": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail={"error": "upstream_unreachable", "detail": str(e)})
