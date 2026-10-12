"""SSE minimal Compagnon (plan 1.2) — framing de POST /ask/stream.

Module autonome (aucune dépendance legacy) : importable et testable hors backend :
``python3 -m unittest packages/cortex/compagnon_ui/server_overlay/tests/test_sse_ask.py``.

Événements :
- ``start`` — émis immédiatement (l'UI sort du blanc dès le 1er octet) ;
- ``ping``  — heartbeat pendant la génération (anti-blanc + anti-buffering proxy) ;
- ``delta`` — fragments du contenu (rendu progressif dans ChatFlow) ;
- ``done``  — réponse complète (source / model / latency / campus_meta …) ;
- ``error`` — échec du dispatch (l'UI bascule sur le message d'erreur).

Le dispatch amont n'est pas token-streamé (provider local en ``stream: false``) :
``stream_ask`` ouvre le flux tout de suite puis égrène le texte final — le gain
perçu est le retrait du « blanc » d'attente, pas la latence de génération.
"""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

PING_INTERVAL_S = 1.0
CHUNK_CHARS = 48
CHUNK_DELAY_S = 0.012

DispatchFn = Callable[[], Awaitable[dict]]


def sse_event(event: str, data: Any) -> bytes:
    """Une frame SSE (``event`` + ``data`` JSON) terminée par une ligne vide."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n".encode("utf-8")


async def stream_ask(
    dispatch: DispatchFn,
    *,
    ping_interval: float = PING_INTERVAL_S,
    chunk_chars: int = CHUNK_CHARS,
    chunk_delay: float = CHUNK_DELAY_S,
) -> AsyncIterator[bytes]:
    """Flux SSE d'un tour ``/ask`` : start → ping* → delta* → done | error."""
    yield sse_event("start", {"ok": True, "ts": time.time()})
    # Commentaire SSE : force le flush ASGI/proxy (premier octet < 1 s).
    yield b": flush\n\n"

    try:
        task: asyncio.Future[dict] = asyncio.ensure_future(dispatch())
    except Exception as exc:  # noqa: BLE001 — on expose l'erreur dans le flux
        yield sse_event("error", {"ok": False, "error": _err(exc)})
        return

    payload: dict | None = None
    try:
        while not task.done():
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=ping_interval)
            except asyncio.TimeoutError:
                yield sse_event("ping", {"ts": time.time()})
        payload = task.result()
    except Exception as exc:  # noqa: BLE001
        task.cancel()
        yield sse_event("error", {"ok": False, "error": _err(exc)})
        return

    payload = payload or {}
    if not isinstance(payload, dict):
        payload = {"content": str(payload), "source": "assistant"}
    text = str(payload.get("content") or payload.get("response") or payload.get("raw") or "")
    # Évite un done « vide » (bulle Terminé sans texte) — contenu minimal de secours.
    if not text.strip():
        err = payload.get("error") or payload.get("detail")
        text = (
            f"Erreur : {err}"
            if err
            else "Réponse vide — réessaie ; vérifie /ask/stream si ça revient."
        )
        payload = {**payload, "content": text}
        if err and not payload.get("source"):
            payload["source"] = "error"
    step = max(1, int(chunk_chars))
    for start in range(0, len(text), step):
        if start:
            await asyncio.sleep(max(0.0, float(chunk_delay)))
        yield sse_event("delta", {"content": text[start : start + step]})

    yield sse_event("done", {"ok": True, "response": payload})


def _err(exc: BaseException) -> str:
    return str(exc) or exc.__class__.__name__
