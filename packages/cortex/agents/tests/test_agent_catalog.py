"""C10 catalog read-only + C11 tick matrix."""

from __future__ import annotations

from fastapi.testclient import TestClient

from lbg_agents import agent_catalog as ac
from lbg_agents.dialogue_http_app import app


def setup_function() -> None:
    ac.reset_cache()


def test_catalog_skills_nonempty() -> None:
    out = ac.catalog("skills")
    assert out["ok"] is True
    assert out["type"] == "skills"
    assert out["count"] >= 1
    assert out["tick_cost"] == "free"
    assert out["requires_tick"] is False
    assert out["context"]["kind"] == "query"
    assert out["context"]["action"] == "catalog"
    ids = {i.get("id") for i in out["items"] if i.get("kind") == "profession"}
    assert "artisan" in ids or "prospecteur" in ids


def test_catalog_recipes_has_schematics() -> None:
    out = ac.catalog("recipes")
    assert out["ok"] is True
    assert out["count"] >= 1
    ids = {i.get("id") for i in out["items"]}
    assert "kit_reparation" in ids


def test_catalog_npcs_summary() -> None:
    out = ac.catalog("npcs")
    assert out["ok"] is True
    assert out["count"] >= 5
    row = out["items"][0]
    assert "id" in row and "name" in row
    assert "goals" not in row  # résumé — pas dump registry complet


def test_catalog_poi_includes_lh_or_stub() -> None:
    out = ac.catalog("poi")
    assert out["ok"] is True
    assert out["count"] >= 1
    ids = {i.get("id") for i in out["items"]}
    assert "poi:player_spawn" in ids or "poi:lh_scrap_pile" in ids


def test_catalog_bad_type() -> None:
    out = ac.catalog("galaxy")
    assert out["ok"] is False
    assert out["error"] == "bad_type"


def test_get_guide_prospecteur() -> None:
    out = ac.get_guide("prospecteur")
    assert out["ok"] is True
    assert out["tick_cost"] == "free"
    g = out["guide"]
    assert g["profession_id"] == "prospecteur"
    assert "survey" in g["loop"] or "survey" in str(g.get("hub_actions"))


def test_classify_query_vs_mutation() -> None:
    q = ac.classify_action("catalog")
    assert q["kind"] == "query" and q["requires_tick"] is False
    m = ac.classify_action("craft/start")
    assert m["kind"] == "mutation" and m["requires_tick"] is True
    assert ac.is_query("quests/board")
    assert ac.is_mutation("talk_npc")


def test_tick_matrix_covers_c11_table() -> None:
    rows = {r["action"]: r for r in ac.tick_matrix_rows()}
    assert "catalog" in rows and rows["catalog"]["tick_cost"] == "free"
    assert "move_to" in rows and rows["move_to"]["requires_tick"] is True
    assert "salvage/loot" in rows


def test_http_catalog_skills() -> None:
    client = TestClient(app)
    r = client.get("/catalog", params={"type": "skills"})
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert j["context"]["tick_cost"] == "free"


def test_http_catalog_bad_type_400() -> None:
    client = TestClient(app)
    r = client.get("/catalog", params={"type": "nope"})
    assert r.status_code == 400


def test_http_guide_and_tick_matrix() -> None:
    client = TestClient(app)
    g = client.get("/guide", params={"playstyle": "artisan"})
    assert g.status_code == 200
    assert g.json()["guide"]["playstyle"] == "artisan"
    t = client.get("/tick-matrix")
    assert t.status_code == 200
    body = t.json()
    assert body["ok"] is True
    assert body["count"] >= 10
    assert "tick_cost" in body["flag_context"]


def test_http_get_dispatch_shared_routes() -> None:
    code, payload = ac.http_get_dispatch("/catalog", {"type": ["npcs"]})  # type: ignore[misc]
    assert code == 200 and payload["ok"] is True and payload["type"] == "npcs"
    code2, payload2 = ac.http_get_dispatch("/v1/guide", {"playstyle": ["scene"]})  # type: ignore[misc]
    assert code2 == 200 and payload2["guide"]["playstyle"] == "scene"
    code3, payload3 = ac.http_get_dispatch("/tick-matrix", {})  # type: ignore[misc]
    assert code3 == 200 and payload3["count"] >= 10
    assert ac.http_get_dispatch("/v1/quest-state", {}) is None
