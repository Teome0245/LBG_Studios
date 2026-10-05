"""Tests mapping affichage Scrapaltai (ADR 0009)."""

from __future__ import annotations

from world_display import enrich_bot_zone_fields, lore_label, zone_display_name


def test_zone_display_tatooine_to_scrapaltai() -> None:
    assert zone_display_name("tatooine") == "Scrapaltai"
    assert zone_display_name("Tatooine") == "Scrapaltai"
    assert zone_display_name("scrapaltai") == "Scrapaltai"


def test_lore_label_mos_eisley() -> None:
    assert "Mos Eisley" not in lore_label("Mos Eisley — tatooine")
    assert "Lost Heaven" in lore_label("Mos Eisley — tatooine")
    assert "Scrapaltai" in lore_label("citoyen Tatooine — starport")


def test_enrich_bot_keeps_engine_id() -> None:
    out = enrich_bot_zone_fields({"id": "lia", "zone": "tatooine", "online": True})
    assert out["zone_engine"] == "tatooine"
    assert out["zone_display"] == "Scrapaltai"
    assert out["zone"] == "Scrapaltai"
