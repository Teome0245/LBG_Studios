# core3_places.py — Ancres monde Scrapaltai / Lost Heaven (coords Core3 X/Y/Z)
"""Constantes de placement partagées (bots IA, autonomie, économie).

Repère outdoor Tatooine/Scrapaltai : X est, Y nord, Z hauteur (souvent ~5–32).
Hub Lost Heaven : ancre (4749, -737) — même référence que prime-client / retail overlay.
"""
from __future__ import annotations

# Hub Lost Heaven (outdoor plaza)
LH_ANCHOR_X = 4749.0
LH_ANCHOR_Y = -737.0
LH_ANCHOR_Z = 32.0

# Offsets bots autour de la plaza (éviter le même point)
LH_BOT_SPAWNS: dict[str, tuple[float, float, float]] = {
    "lia": (4749.0, -720.0, 32.0),   # plaza nord
    "nix": (4780.0, -760.0, 32.0),   # allée port
    "mira": (4720.0, -780.0, 32.0),  # près marché
    "kael": (4809.0, -700.0, 32.0),  # vers trainers / auberge
}

# Sortie intérieur → outdoor hub (forage / économie)
LH_OUTDOOR = (4749.0, -780.0, 32.0)

# Point « port shuttle » (proche POI hub)
LH_STARPORT = (4809.0, -802.0, 32.0)


def bot_spawn(player_id: str) -> tuple[float, float, float]:
    return LH_BOT_SPAWNS.get(player_id.strip().lower(), (LH_ANCHOR_X, LH_ANCHOR_Y, LH_ANCHOR_Z))


def outdoor_hub() -> tuple[float, float, float]:
    return LH_OUTDOOR
