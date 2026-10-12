"""Objectifs joueur IA — pas de couloirs / patrouilles fixes."""

from __future__ import annotations

import random
from typing import Any

# Coords hub (dupliquées volontairement — évite import circulaire with sim)
_PLAZA = (4749.0, 0.15, -737.0)
_MARKET = (4809.0, 0.15, -932.0)
_STARPORT = (4740.0, 0.15, -820.0)
_CANTINA = (4939.0, 0.15, -802.0)
_MISSION = (4939.0, 0.15, -932.0)
_CLINIC = (4679.0, 0.15, -672.0)
_TRAINING = (4939.0, 0.15, -672.0)
_INN = (4809.0, 0.15, -672.0)
_TOWN_HALL = (4679.0, 0.15, -932.0)
_ARTISAN = (5069.0, 0.15, -802.0)

PLAY_GOALS: list[dict[str, Any]] = [
    {"id": "board", "label": "regarder le board missions", "pos": _MISSION},
    {"id": "market", "label": "fouiller le marché", "pos": _MARKET},
    {"id": "cantina", "label": "passer à La Perle", "pos": _CANTINA},
    {"id": "plaza", "label": "traîner sur la plaza", "pos": _PLAZA},
    {"id": "train", "label": "s'entraîner au hall", "pos": _TRAINING},
    {"id": "clinic", "label": "passer à la clinique", "pos": _CLINIC},
    {"id": "craft", "label": "voir l'atelier", "pos": _ARTISAN},
    {"id": "inn", "label": "reposer à l'auberge", "pos": _INN},
    {"id": "hall", "label": "passer à la mairie", "pos": _TOWN_HALL},
    {"id": "apron", "label": "surveiller l'apron port", "pos": _STARPORT},
]


def pick_goal(*, avoid_id: str | None = None, prefer: list[str] | None = None) -> dict[str, Any]:
    pool = list(PLAY_GOALS)
    if prefer:
        preferred = [g for g in pool if g["id"] in prefer]
        if preferred and random.random() < 0.55:
            pool = preferred
    if avoid_id:
        filtered = [g for g in pool if g["id"] != avoid_id]
        if filtered:
            pool = filtered
    return dict(random.choice(pool))


def linger_seconds() -> float:
    return random.uniform(4.0, 14.0)
