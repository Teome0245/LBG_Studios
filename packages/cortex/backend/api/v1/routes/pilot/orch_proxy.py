"""Proxies same-origin vers l'API Orch UI legacy (.100:3000) — plan_pilot_hub_orch_absorb P0."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from ._common import LOG, httpx, orch_ui_api_base, orch_ui_ask_timeout_s
from ._models import OkEnvelope, OrchAskBody, OrchLyraUpdateBody

router = APIRouter(prefix="/orch", tags=["pilot-orch"])


def _disabled() -> dict[str, object]:
    return {
        "ok": False,
        "disabled": True,
        "error": "orch_ui_disabled",
        "detail": "LBG_ORCH_UI_API_URL vide (proxies Orch désactivés).",
    }


def _wrap_ok(data: object) -> dict[str, object]:
    if isinstance(data, dict):
        # Évite double `ok` contradictoire si upstream en a déjà un
        out = {"ok": True, **data}
        out["ok"] = True
        return out
    return {"ok": True, "payload": data}


async def _upstream_get(
    path: str,
    *,
    timeout: float = 8.0,
    params: dict[str, Any] | None = None,
) -> dict[str, object]:
    base = orch_ui_api_base()
    if not base:
        return _disabled()
    url = f"{base}{path}"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(url, params=params)
        if r.status_code != 200:
            return {
                "ok": False,
                "error": f"orch_ui HTTP {r.status_code}",
                "body": r.text[:500],
                "upstream": url,
            }
        return _wrap_ok(r.json())
    except Exception as e:
        LOG.warning("pilot.orch GET %s err=%s", path, e)
        return {"ok": False, "error": str(e), "upstream": url}


async def _upstream_post(
    path: str,
    *,
    json_body: dict[str, object] | None = None,
    timeout: float = 15.0,
) -> dict[str, object]:
    base = orch_ui_api_base()
    if not base:
        return _disabled()
    url = f"{base}{path}"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(url, json=json_body or {})
        if r.status_code != 200:
            return {
                "ok": False,
                "error": f"orch_ui HTTP {r.status_code}",
                "body": r.text[:500],
                "upstream": url,
            }
        return _wrap_ok(r.json())
    except Exception as e:
        LOG.warning("pilot.orch POST %s err=%s", path, e)
        return {"ok": False, "error": str(e), "upstream": url}


async def _upstream_delete(path: str, *, timeout: float = 8.0) -> dict[str, object]:
    base = orch_ui_api_base()
    if not base:
        return _disabled()
    url = f"{base}{path}"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.delete(url)
        if r.status_code not in (200, 204):
            return {
                "ok": False,
                "error": f"orch_ui HTTP {r.status_code}",
                "body": r.text[:500],
                "upstream": url,
            }
        if r.status_code == 204 or not r.content:
            return {"ok": True}
        try:
            return _wrap_ok(r.json())
        except Exception:
            return {"ok": True}
    except Exception as e:
        LOG.warning("pilot.orch DELETE %s err=%s", path, e)
        return {"ok": False, "error": str(e), "upstream": url}


@router.get("/health", response_model=OkEnvelope)
async def pilot_orch_health() -> dict[str, object]:
    """Ping amont Orch UI (`GET /health`) + base configurée."""
    base = orch_ui_api_base()
    if not base:
        return _disabled()
    out = await _upstream_get("/health", timeout=5.0)
    out["upstream_base"] = base
    return out


@router.post("/ask", response_model=OkEnvelope)
async def pilot_orch_ask(payload: OrchAskBody) -> dict[str, object]:
    """Proxy `POST /ask` (chat produit Orch / RouterIA).

    Enrichit le prompt (lookup web Wikipedia/DDG) quand l'intention est une
    recherche culturelle (film, titre…). Si des hits existent : réponse directe
    Cortex (évite le ask_user Orch / interrogatoire).
    """
    body = payload.model_dump(exclude_none=True)
    lookup_meta: dict[str, object] | None = None
    raw_prompt = str(body.get("prompt") or "")
    if raw_prompt.strip():
        try:
            from services.web_lookup import enrich_ask_prompt

            enriched, lookup_meta = await enrich_ask_prompt(raw_prompt)
            if lookup_meta is not None:
                body["prompt"] = enriched
        except Exception as e:
            LOG.warning("pilot.orch ask web_lookup enrich failed: %s", e)
            lookup_meta = {"ok": False, "error": f"{type(e).__name__}: {e}"}

    # Hits fiables → répondre ici (Orch P1 ask_user ignorerait les faits)
    if (
        isinstance(lookup_meta, dict)
        and lookup_meta.get("ok")
        and int(lookup_meta.get("hit_count") or 0) > 0
        and isinstance(lookup_meta.get("direct_reply"), str)
        and str(lookup_meta.get("direct_reply") or "").strip()
    ):
        reply = str(lookup_meta["direct_reply"]).strip()
        step = {
            "kind": "web_lookup",
            "label": "Recherche web",
            "detail": lookup_meta.get("query") or "",
            "status": "ok",
            "ms": lookup_meta.get("ms") or 0,
        }
        # Ne pas exposer hits bruts / direct_reply en double dans le client
        public_meta = {
            k: v
            for k, v in lookup_meta.items()
            if k not in ("hits", "direct_reply")
        }
        return {
            "ok": True,
            "web_lookup": public_meta,
            "timeline": [
                step,
                {
                    "kind": "answer",
                    "label": "Réponse ancrée web",
                    "detail": "cortex_web_lookup",
                    "status": "ok",
                    "ms": 0,
                },
            ],
            "response": {
                "role": "assistant",
                "content": reply,
                "response": reply,
                "source": "web_lookup",
                "model": "web_lookup",
                "model_used": "web_lookup",
                "provider": "cortex",
                "latency": float(lookup_meta.get("ms") or 0) / 1000.0,
                "timeline": [
                    step,
                    {
                        "kind": "answer",
                        "label": "Réponse ancrée web",
                        "status": "ok",
                    },
                ],
            },
        }

    out = await _upstream_post("/ask", json_body=body, timeout=orch_ui_ask_timeout_s())
    if lookup_meta is not None and isinstance(out, dict):
        public_meta = {
            k: v
            for k, v in lookup_meta.items()
            if k not in ("hits", "direct_reply")
        }
        out["web_lookup"] = public_meta
        step = {
            "kind": "web_lookup",
            "label": "Recherche web",
            "detail": lookup_meta.get("query") or "",
            "status": "ok" if lookup_meta.get("ok") else "error",
            "ms": lookup_meta.get("ms") or 0,
        }
        tl = out.get("timeline")
        if isinstance(tl, list):
            out["timeline"] = [step, *tl]
        else:
            resp = out.get("response")
            if isinstance(resp, dict):
                rtl = resp.get("timeline")
                if isinstance(rtl, list):
                    resp["timeline"] = [step, *rtl]
                else:
                    out["timeline"] = [step]
            else:
                out["timeline"] = [step]
    return out


@router.get("/lyra/state", response_model=OkEnvelope)
async def pilot_orch_lyra_state() -> dict[str, object]:
    """Proxy `GET /lyra/state` (LyraEngineV2)."""
    return await _upstream_get("/lyra/state")


@router.post("/lyra/update", response_model=OkEnvelope)
async def pilot_orch_lyra_update(payload: OrchLyraUpdateBody) -> dict[str, object]:
    """Proxy `POST /lyra/update`."""
    return await _upstream_post("/lyra/update", json_body=payload.model_dump(exclude_none=True))


@router.get("/agents/map", response_model=OkEnvelope)
async def pilot_orch_agents_map() -> dict[str, object]:
    """Proxy `GET /agents/map`."""
    return await _upstream_get("/agents/map")


@router.get("/providers/catalog", response_model=OkEnvelope)
async def pilot_orch_providers_catalog() -> dict[str, object]:
    """Proxy `GET /providers/catalog`."""
    return await _upstream_get("/providers/catalog", timeout=20.0)


@router.get("/monitor/cockpit", response_model=OkEnvelope)
async def pilot_orch_monitor_cockpit() -> dict[str, object]:
    """Proxy `GET /monitor/cockpit`."""
    return await _upstream_get("/monitor/cockpit")


@router.get("/monitor/agents", response_model=OkEnvelope)
async def pilot_orch_monitor_agents() -> dict[str, object]:
    """Proxy `GET /monitor/agents`."""
    return await _upstream_get("/monitor/agents")


@router.get("/chat/context/{conversation_id}", response_model=OkEnvelope)
async def pilot_orch_chat_context(conversation_id: str) -> dict[str, object]:
    """Proxy `GET /chat/context/{conversation_id}`."""
    cid = (conversation_id or "").strip()
    if not cid:
        return {"ok": False, "error": "conversation_id required"}
    return await _upstream_get(f"/chat/context/{cid}")


@router.get("/chat/conversations", response_model=OkEnvelope)
async def pilot_orch_chat_conversations(
    limit: int = Query(default=50, ge=1, le=200),
    include_archived: bool = Query(default=False),
) -> dict[str, object]:
    """Proxy `GET /chat/conversations`."""
    return await _upstream_get(
        "/chat/conversations",
        params={"limit": limit, "include_archived": include_archived},
    )


@router.post("/chat/conversations/{conversation_id}/archive", response_model=OkEnvelope)
async def pilot_orch_chat_archive(conversation_id: str) -> dict[str, object]:
    return await _upstream_post(f"/chat/conversations/{conversation_id}/archive")


@router.post("/chat/conversations/{conversation_id}/unarchive", response_model=OkEnvelope)
async def pilot_orch_chat_unarchive(conversation_id: str) -> dict[str, object]:
    return await _upstream_post(f"/chat/conversations/{conversation_id}/unarchive")


@router.delete("/chat/conversations/{conversation_id}", response_model=OkEnvelope)
async def pilot_orch_chat_delete(conversation_id: str) -> dict[str, object]:
    return await _upstream_delete(f"/chat/conversations/{conversation_id}")
