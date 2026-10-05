"""Affichage lore LBG (ADR 0009) — ids moteur Core3 inchangés.

Id zone technique : ``tatooine``
Affichage planète : Scrapaltai
Hub gameplay : Lost Heaven
"""

from __future__ import annotations

from typing import Any

# Clé moteur Core3 / WS — ne jamais renommer côté protocole.
ZONE_ENGINE_DEFAULT = "tatooine"
PLANET_DISPLAY = "Scrapaltai"
HUB_CITY = "Lost Heaven"
CANTINA_DISPLAY = "La Perle de Scrapaltai"

_ZONE_DISPLAY: dict[str, str] = {
    "tatooine": PLANET_DISPLAY,
    "scrapaltai": PLANET_DISPLAY,
}

# Remplacements pour libellés legacy SWG (registry, prompts, UI).
_LABEL_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("Mos Eisley — tatooine", f"{HUB_CITY} — {PLANET_DISPLAY}"),
    ("Mos Eisley — Tatooine", f"{HUB_CITY} — {PLANET_DISPLAY}"),
    ("mos eisley — tatooine", f"{HUB_CITY} — {PLANET_DISPLAY}"),
    ("Mos Eisley - ", f"{HUB_CITY} - "),
    ("Mos Eisley — ", f"{HUB_CITY} — "),
    ("Mos Eisley", HUB_CITY),
    ("mos eisley", "lost heaven"),
    ("citoyen Tatooine", f"citoyen {PLANET_DISPLAY}"),
    ("Civils Tatooine", f"Civils {PLANET_DISPLAY}"),
    ("survie Tatooine", f"survie {PLANET_DISPLAY}"),
    ("planète Tatooine", f"planète {PLANET_DISPLAY}"),
    ("Centre entrainement ME", f"Centre entraînement {HUB_CITY}"),
    ("Centre entraînement ME", f"Centre entraînement {HUB_CITY}"),
    ("Cantina ME", CANTINA_DISPLAY),
    ("cantina Mos Eisley", CANTINA_DISPLAY),
    ("cantina tatooine", CANTINA_DISPLAY),
)


def zone_display_name(zone_id: str | None) -> str:
    """Nom planète affiché pour un id zone moteur (ex. tatooine → Scrapaltai)."""
    raw = str(zone_id or "").strip()
    if not raw:
        return PLANET_DISPLAY
    key = raw.lower()
    if key in _ZONE_DISPLAY:
        return _ZONE_DISPLAY[key]
    # Déjà un libellé lore (Lost Heaven — …) : ne pas écraser.
    if "scrapaltai" in key or "lost heaven" in key:
        return raw
    if key == "tatooine" or raw == ZONE_ENGINE_DEFAULT:
        return PLANET_DISPLAY
    return raw


def lore_label(text: str | None) -> str:
    """Nettoie un libellé user-facing / prompt des fuites SWG."""
    s = str(text or "")
    if not s:
        return s
    out = s
    for old, new in _LABEL_REPLACEMENTS:
        out = out.replace(old, new)
    # Dernier filet : « Tatooine » isolé en prose (pas l'id technique seul).
    if "Tatooine" in out and out.strip().lower() != "tatooine":
        out = out.replace("Tatooine", PLANET_DISPLAY)
    return out


def enrich_bot_zone_fields(bot: dict[str, Any]) -> dict[str, Any]:
    """Ajoute zone_display / zone_engine sur une entrée runtime bot."""
    zone_engine = bot.get("zone")
    zone_eng = str(zone_engine).strip() if zone_engine is not None else ""
    display = zone_display_name(zone_eng or ZONE_ENGINE_DEFAULT)
    out = dict(bot)
    out["zone_engine"] = zone_eng or ZONE_ENGINE_DEFAULT
    out["zone_display"] = display
    # Champ affiché par défaut pour l'UI (chips) — l'id moteur reste zone_engine.
    if zone_eng.lower() == "tatooine" or not zone_eng:
        out["zone"] = display
    return out
