"""Middlewares FastAPI du backend LBG."""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from services import metrics as svc_metrics

LOG = logging.getLogger("backend")


class TraceIdMiddleware(BaseHTTPMiddleware):
    """Injecte un ``X-Request-Id`` dans chaque requête/réponse et log la requête."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        trace_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        request.state.trace_id = trace_id

        t0 = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        response.headers["X-Request-Id"] = trace_id

        path = request.url.path
        if not path.startswith("/pilot/") and path != "/pilot":
            LOG.info(
                "%s %s %d %dms trace=%s",
                request.method,
                path,
                response.status_code,
                elapsed_ms,
                trace_id,
            )
            svc_metrics.inc("http_requests_total")

        return response
