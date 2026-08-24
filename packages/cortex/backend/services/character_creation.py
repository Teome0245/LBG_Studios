"""Service de création de personnage — logique métier de l'Amas."""

from __future__ import annotations

import json
import random
import time
import uuid
from pathlib import Path
from typing import Any

from models.characters import (
    ArchetypeId,
    CharacterCreateRequest,
    CharacterCreateResponse,
    CharacterOrigin,
    CharacterStats,
    CreationMode,
)

CONTENT_DIR = Path(__file__).resolve().parent.parent.parent / "content" / "world"

_cache: dict[str, Any] = {}


def _load_json(name: str) -> Any:
    if name not in _cache:
        _cache[name] = json.loads((CONTENT_DIR / name).read_text(encoding="utf-8"))
    return _cache[name]


def _races_by_id() -> dict[str, dict]:
    data = _load_json("playable_races.json")
    return {r["id"]: r for r in data["races"] if r.get("playable_v1")}


def _archetypes_by_id() -> dict[str, dict]:
    data = _load_json("archetypes.json")
    return {a["id"].split(":")[-1]: a for a in data["archetypes"]}


def _empreintes_by_pnj() -> dict[str, dict]:
    data = _load_json("empreinte_pnj.json")
    return {e["pnj_id"]: e for e in data["empreintes"]}


def _apply_racial_bonus(base: dict[str, int], bonus: dict[str, int]) -> dict[str, int]:
    return {k: max(1, base.get(k, 0) + bonus.get(k, 0)) for k in base}


def _vary_stats(stats: dict[str, int], pct: float = 0.10) -> dict[str, int]:
    out = {}
    for k, v in stats.items():
        if k == "hp":
            out[k] = v
            continue
        delta = max(1, int(v * pct))
        out[k] = max(1, v + random.randint(-delta, delta))
    return out


def _pick_archetype_from_stats(stats: dict[str, int]) -> ArchetypeId:
    """Déduit l'archétype le plus proche à partir de stats dominantes."""
    dominant = sorted(
        [(k, v) for k, v in stats.items() if k not in ("hp",)],
        key=lambda x: x[1],
        reverse=True,
    )
    top = dominant[0][0]
    mapping = {
        "force": ArchetypeId.poing,
        "agilite": ArchetypeId.oeil,
        "intelligence": ArchetypeId.forgeur,
        "endurance": ArchetypeId.traqueur,
        "esprit": ArchetypeId.soigneur,
    }
    return mapping.get(top, ArchetypeId.voix)


class CharacterCreationError(Exception):
    def __init__(self, detail: str, status_code: int = 422):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


_created_names: set[str] = set()
_account_characters: dict[str, list[dict[str, object]]] = {}
_account_noyaux: dict[str, dict[str, str]] = {}
_last_human_create: dict[str, float] = {}

MAX_CHARACTERS_PER_ACCOUNT = 6
CHARACTER_CREATE_COOLDOWN_S = 300


def clear_store() -> None:
    """Reset in-memory store (tests)."""
    _created_names.clear()
    _account_characters.clear()
    _account_noyaux.clear()
    _last_human_create.clear()
    _cache.clear()


def _count_characters(account_id: str) -> int:
    return len(_account_characters.get(account_id, []))


def _ensure_noyau(account_id: str) -> tuple[str, str]:
    existing = _account_noyaux.get(account_id)
    if existing is not None:
        return existing["noyau_id"], existing["particule_seed"]
    noyau_id = f"noyau_{uuid.uuid4().hex[:8]}"
    particule_seed = uuid.uuid4().hex[:8]
    _account_noyaux[account_id] = {
        "noyau_id": noyau_id,
        "particule_seed": particule_seed,
    }
    return noyau_id, particule_seed


def create_character(
    req: CharacterCreateRequest,
    account_id: str = "default",
) -> CharacterCreateResponse:
    name_lower = req.customization.name.strip().lower()
    if name_lower in _created_names:
        raise CharacterCreationError("Nom déjà pris", status_code=409)

    max_chars = MAX_CHARACTERS_PER_ACCOUNT
    current = _count_characters(account_id)
    if current >= max_chars:
        raise CharacterCreationError(
            f"Maximum {max_chars} personnages par compte",
            status_code=403,
        )

    if not req.is_ai:
        last_at = _last_human_create.get(account_id)
        if last_at is not None:
            elapsed = time.time() - last_at
            if elapsed < CHARACTER_CREATE_COOLDOWN_S:
                wait_s = int(CHARACTER_CREATE_COOLDOWN_S - elapsed)
                raise CharacterCreationError(
                    f"Cooldown actif — réessayer dans {wait_s}s",
                    status_code=429,
                )

    races = _races_by_id()
    archetypes = _archetypes_by_id()
    empreintes = _empreintes_by_pnj()

    if req.mode == CreationMode.archetype:
        if req.archetype is None:
            raise CharacterCreationError("archetype requis pour mode=archetype")
        arch = archetypes.get(req.archetype.value)
        if arch is None:
            raise CharacterCreationError(f"Archétype inconnu: {req.archetype}")
        suggested = arch["suggested_races"]
        if req.race_id is not None:
            if req.race_id not in suggested:
                raise CharacterCreationError(
                    f"Race {req.race_id} non compatible avec l'archétype {req.archetype.value}",
                    status_code=422,
                )
            race_id = req.race_id
        else:
            race_id = suggested[0]
        race = races[race_id]
        base = {k: v for k, v in arch["base_stats"].items()}
        stats = _apply_racial_bonus(base, race["stat_bonus"])
        archetype_id = req.archetype
        lore_brief = arch["lore_brief"]

    elif req.mode == CreationMode.empreinte:
        if req.empreinte_pnj_id is None:
            raise CharacterCreationError("empreinte_pnj_id requis pour mode=empreinte")
        emp = empreintes.get(req.empreinte_pnj_id)
        if emp is None:
            raise CharacterCreationError(
                f"PNJ inconnu: {req.empreinte_pnj_id}", status_code=404
            )
        race_id = emp["race_id"]
        race = races[race_id]
        stats = _vary_stats(emp["base_stats"])
        archetype_id = ArchetypeId(emp["implied_archetype"])
        lore_brief = emp["lore_brief"]

    elif req.mode == CreationMode.chaos:
        race_id = random.choice(list(races.keys()))
        race = races[race_id]
        stats_raw = {
            "force": random.randint(25, 80),
            "agilite": random.randint(25, 80),
            "intelligence": random.randint(25, 80),
            "hp": 100,
            "endurance": random.randint(25, 80),
            "esprit": random.randint(25, 80),
        }
        stats = _apply_racial_bonus(stats_raw, race["stat_bonus"])
        archetype_id = _pick_archetype_from_stats(stats)
        lore_brief = "L'Amas a vibré sans guide. Ce qui en est sorti… personne ne s'y attendait."
    else:
        raise CharacterCreationError(f"Mode inconnu: {req.mode}")

    character_id = f"chr_{uuid.uuid4().hex[:8]}"
    noyau_id, particule_seed = _ensure_noyau(account_id)

    _created_names.add(name_lower)
    _account_characters.setdefault(account_id, []).append(
        {"character_id": character_id, "is_ai": req.is_ai}
    )
    if not req.is_ai:
        _last_human_create[account_id] = time.time()

    return CharacterCreateResponse(
        character_id=character_id,
        name=req.customization.name.strip(),
        race=race_id,
        race_display=race["display_name"],
        archetype_starter=archetype_id,
        stats=CharacterStats(**stats),
        origin=CharacterOrigin(
            mode=req.mode,
            archetype=archetype_id if req.mode == CreationMode.archetype else None,
            empreinte_pnj_id=req.empreinte_pnj_id,
            ai_brief=req.ai_brief,
        ),
        is_ai=req.is_ai,
        lore_brief=lore_brief,
        noyau_id=noyau_id,
        particule_seed=particule_seed,
    )
