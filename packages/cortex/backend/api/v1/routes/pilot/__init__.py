"""Agrégation des sous-routeurs Pilot."""

from __future__ import annotations

from fastapi import APIRouter

from . import desktop, gameplay_debug, hunt_yard, intents_route, orchestrator_proxy, proxy_agents, status, team
from ._common import LOG, OrchestratorClient, OrchestratorError, httpx

router = APIRouter()
for _mod in (status, proxy_agents, orchestrator_proxy, desktop, intents_route, gameplay_debug, hunt_yard, team):
    router.include_router(_mod.router)

__all__ = ["LOG", "OrchestratorClient", "OrchestratorError", "httpx", "router"]
