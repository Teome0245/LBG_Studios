"""Test de l'endpoint /v1/pilot/topology (Second Brain & Knowledge Explorer)."""

import pytest
from backend.main import app
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_pilot_topology_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/v1/pilot/topology")
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data
        assert "edges" in data
        assert "broken_links" in data
        assert isinstance(data["nodes"], dict)
        assert isinstance(data["edges"], list)
