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

        # Vérification de l'intégration Organisme Gladys et MMO dans la vue unifiée
        nodes = data["nodes"]
        assert "gladys_organism" in nodes
        assert "poste_10" in nodes
        assert "lia_avatar" in nodes
        assert "scrapaltai" in nodes
        assert "live_gladys_count" in data

        # Vérification des silos de connaissances et skills Gladys
        assert "domain_compagnon" in nodes
        assert "domain_mmo_prime" in nodes
        assert "domain_infra_lan" in nodes
        assert "domain_showcase_web" in nodes
        assert "skill_nocturnal_audit" in nodes
        assert "skill_deploy_showcase" in nodes
        assert "skill_blender_143" in nodes
        assert "skill_smoke_lan" in nodes
        assert "skill_self_healing" in nodes
        assert nodes["domain_compagnon"]["is_live"] is True
        assert nodes["skill_nocturnal_audit"]["is_live"] is True


@pytest.mark.asyncio
async def test_pilot_topology_domain_filters():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Filtre Gladys
        resp_gladys = await client.get("/v1/pilot/topology?domain=gladys")
        assert resp_gladys.status_code == 200
        data_gladys = resp_gladys.json()
        assert "gladys_organism" in data_gladys["nodes"]
        assert "scrapaltai" not in data_gladys["nodes"]
        assert data_gladys["domain"] == "gladys"

        # Filtre MMO
        resp_mmo = await client.get("/v1/pilot/topology?domain=mmo")
        assert resp_mmo.status_code == 200
        data_mmo = resp_mmo.json()
        assert "scrapaltai" in data_mmo["nodes"]
        assert "gladys_organism" not in data_mmo["nodes"]
        assert data_mmo["domain"] == "mmo"
