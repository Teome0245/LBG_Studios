"""Agrégation des sous-routeurs Pilot."""

from __future__ import annotations

from fastapi import APIRouter

from . import desktop, gameplay_debug, hunt_yard, intents_route, orch_proxy, orchestrator_proxy, proxy_agents, slack_hitl, status, team, vision
from ._common import LOG, OrchestratorClient, OrchestratorError, httpx

router = APIRouter()
for _mod in (
    status,
    proxy_agents,
    orchestrator_proxy,
    orch_proxy,
    desktop,
    intents_route,
    gameplay_debug,
    hunt_yard,
    team,
    slack_hitl,
    vision,
):
    router.include_router(_mod.router)

__all__ = ["LOG", "OrchestratorClient", "OrchestratorError", "httpx", "router"]
